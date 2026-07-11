#!/usr/bin/env bash
# release-flow.sh -- 通用 release-flow 引擎(确定层:操作 release-state.json)。
#
#   init        --manifest <path> [--max-rounds N]
#   where       报当前 stage+run / SUCCESS / PAUSED / NO-STAGES / CORRUPT
#   stage       done|fail  (fail 归 Pack 1.3)
#   round next  轮账;到 max_rounds 自动 surface 熔断
#   surface|resume|close|exit-check
#   receipt     从 attempt_ledger 渲染已试动作
#   dispatch    --stage <n> --findings <p>  收敛护栏 + 按 tier 派修(P2 derive/P1 fix/P0 停)
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/host.sh
. "$SCRIPT_DIR/lib/host.sh"
STATE_NAME="release-state.json"
RF_MAX_SAME_FINGERPRINT="${RF_MAX_SAME_FINGERPRINT:-2}"

die() { echo "ERROR: $*" >&2; exit 1; }
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }

state_file() {
  local top sd
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "不在 git 仓库内"
  sd="$(mmw_resolve_state_subdir "$top")"
  echo "$top/$sd/$STATE_NAME"
}

need_state() {
  local f
  f="$(state_file)"
  [ -f "$f" ] || die "无 release-state(先 release init)"
  echo "$f"
}

# 原子写 + fail-closed:验非空且合法 JSON 才 mv,否则保留原文件退非零。
write() {
  local f="$1" tmp dir
  dir="$(dirname "$f")"
  tmp="$(mktemp "$dir/.tmpXXXXXX")"
  cat > "$tmp"
  if [ ! -s "$tmp" ] || ! jq -e . "$tmp" >/dev/null 2>&1; then
    rm -f "$tmp"
    echo "ERROR: 拒绝写入空/非法 JSON 到 $f;原文件保留" >&2
    return 1
  fi
  mv "$tmp" "$f"
}

edit() {
  local f="$1"
  shift
  jq "$@" "$f" | write "$f"
}

# $1=state $2=stage $3=action_kind $4=outcome $5=fingerprint $6=findings_ref
append_attempt() {
  local f="$1" stage="$2" kind="$3" outcome="$4" fp="$5" ref="$6" aid
  aid="a$(jq -r '.attempt_ledger|length' "$f")-$stage"
  edit "$f" --arg aid "$aid" --arg st "$stage" --arg k "$kind" --arg o "$outcome" \
    --arg fp "$fp" --arg ref "$ref" --arg t "$(now)" \
    '.attempt_ledger += [{attempt_id:$aid, stage:$st, action_kind:$k, outcome:$o,
        root_cause_fingerprint:(if $fp=="" then null else $fp end),
        command:null, started_at:$t, finished_at:$t,
        changed_paths:[], blocked_paths:[], gate_results:[],
        artifact_refs:(if $ref=="" then [] else [$ref] end), log_refs:[], worker_ref:null}]
     | .budget.attempts += 1'
}

_repo_top() { git rev-parse --show-toplevel 2>/dev/null || die "不在 git 仓库内"; }

iso_to_epoch() {
  date -u -d "$1" +%s 2>/dev/null || date -j -u -f "%Y-%m-%dT%H:%M:%SZ" "$1" +%s 2>/dev/null || echo 0
}

_convergence_guard() {
  local f="$1" cls="$2" stage="$3" fp cnt
  while IFS= read -r fp; do
    [ -n "$fp" ] || continue
    cnt="$(jq -r --arg fp "$fp" '[.fingerprint_ledger[]|select(.fingerprint==$fp)][0].count // 0' "$f")"
    if [ "$cnt" -ge "$RF_MAX_SAME_FINGERPRINT" ]; then
      edit "$f" --arg s "$stage" --arg fp "$fp" --argjson n "$RF_MAX_SAME_FINGERPRINT" \
        '.pause={at_stage:$s, kind:"surface", reason:"needs-redirection",
                 question:("同根因("+$fp+")重复达阈值 "+($n|tostring)+" 次仍未收敛,引擎熔断交人")}'
      emit_event "$f" "paused" "$stage" "" "$fp" ""
      echo "CIRCUIT-BREAK:fingerprint=$fp ×$cnt(>=$RF_MAX_SAME_FINGERPRINT),熔断交人"
      return 1
    fi
  done < <(printf '%s' "$cls" | jq -r '.failing[].root_cause_fingerprint')

  local att max
  att="$(jq -r '.budget.attempts // 0' "$f")"
  max="$(jq -r '.budget.max_attempts // 0' "$f")"
  if [ "$max" -gt 0 ] && [ "$att" -ge "$max" ]; then
    edit "$f" --arg s "$stage" --argjson a "$att" --argjson m "$max" \
      '.pause={at_stage:$s, kind:"surface", reason:"needs-redirection",
               question:("尝试预算越界(attempts="+($a|tostring)+">=max="+($m|tostring)+"),引擎熔断交人")}'
    emit_event "$f" "paused" "$stage" "" "" ""
    echo "BUDGET-EXCEEDED:attempts=$att>=max=$max,熔断交人"
    return 1
  fi

  local started wallmax elapsed
  started="$(jq -r '.budget.started_at // ""' "$f")"
  wallmax="$(jq -r '.budget.max_wall_clock_seconds // 0' "$f")"
  if [ -n "$started" ] && [ "$wallmax" -gt 0 ]; then
    elapsed=$(( $(date -u +%s) - $(iso_to_epoch "$started") ))
    if [ "$elapsed" -ge "$wallmax" ]; then
      edit "$f" --arg s "$stage" --argjson e "$elapsed" --argjson w "$wallmax" \
        '.pause={at_stage:$s, kind:"surface", reason:"needs-redirection",
                 question:("墙钟预算越界(elapsed="+($e|tostring)+"s>=max="+($w|tostring)+"s),引擎熔断交人")}'
      emit_event "$f" "paused" "$stage" "" "" ""
      echo "BUDGET-EXCEEDED:wallclock=${elapsed}s>=${wallmax}s,熔断交人"
      return 1
    fi
  fi
  return 0
}

cmd_dispatch_p2() {
  local f="$1" name="$2" fp="$3" mp
  mp="$(jq -r '.manifest_path' "$f")"
  local derive_argv=() a
  while IFS= read -r a; do derive_argv+=("$a"); done < <(jq -r '.derive[]' "$mp")
  [ ${#derive_argv[@]} -gt 0 ] || die "manifest.derive 为空(引擎载入应已挡,防御)"
  local rc=0 dcmd
  dcmd="${derive_argv[*]}"
  ( cd "$(_repo_top)" && "${derive_argv[@]}" ) || rc=$?
  if [ "$rc" -eq 0 ]; then
    append_attempt "$f" "$name" "derive" "done" "$fp" ""
    edit "$f" --arg c "$dcmd" '.attempt_ledger[-1].command=$c'
    edit "$f" --arg n "$name" \
      '(.stages |= map(if .name==$n then .status="pending" else . end))
       | .current_stage=([.stages[]|select(.status=="pending")][0].name // null)'
    emit_event "$f" "classified" "$name" "P2" "$fp" "$(jq -r '.attempt_ledger[-1].attempt_id' "$f")"
    echo "DERIVED:$name(消费方重生,待重跑)"
  else
    append_attempt "$f" "$name" "derive" "fail" "$fp" ""
    edit "$f" --arg c "$dcmd" '.attempt_ledger[-1].command=$c'
    edit "$f" --arg n "$name" --arg mp "$mp" \
      '.pause={at_stage:$n, kind:"surface", reason:"needs-context",
               question:("derive 失败("+$mp+"),真相源可能损坏,交人(agent 不碰真相源本体)")}'
    emit_event "$f" "paused" "$name" "" "$fp" "$(jq -r '.attempt_ledger[-1].attempt_id' "$f")"
    echo "DERIVE-FAILED:$name(escalate PAUSE)"
  fi
}

_match_any() {
  local path="$1" g
  shift
  for g in "$@"; do
    [[ "$path" == $g ]] && return 0
  done
  return 1
}

_json_array() {
  if [ "$#" -eq 0 ]; then echo "[]"; return; fi
  printf '%s\n' "$@" | jq -R . | jq -s -c .
}

_json_changed_paths() {
  if [ ${#CHANGED_PATHS[@]} -eq 0 ]; then _json_array; else _json_array "${CHANGED_PATHS[@]}"; fi
}

patch_last_attempt() {
  local f="$1" cp="$2" bp="$3" gr="$4" wr="$5" cmd="${6:-}"
  edit "$f" --argjson cp "$cp" --argjson bp "$bp" --argjson gr "$gr" --arg wr "$wr" --arg c "$cmd" \
    '.attempt_ledger[-1].changed_paths=$cp
     | .attempt_ledger[-1].blocked_paths=$bp
     | .attempt_ledger[-1].gate_results=$gr
     | .attempt_ledger[-1].worker_ref=(if $wr=="" then null else $wr end)
     | .attempt_ledger[-1].command=(if $c=="" then null else $c end)'
}

_run_fix_in_staging() {
  local f="$1" findings="$2" mp main basep reff p a
  mp="$(jq -r '.manifest_path' "$f")"
  main="$(_repo_top)"
  STAGING="$(mktemp -d)/rf-staging"
  git worktree add -q --detach "$STAGING" HEAD || die "建 staging worktree 失败"

  # ponytail: 只重放 tracked diff;untracked 不进 fix-only base,避免把测试产物带进修复 diff。
  basep="$(mktemp)"
  git -C "$main" diff HEAD > "$basep" 2>/dev/null || true
  if [ -s "$basep" ]; then git -C "$STAGING" apply "$basep" || die "重放主树改动到 staging 失败"; fi
  rm -f "$basep"
  git -C "$STAGING" add -A >/dev/null 2>&1 || true
  git -C "$STAGING" commit -q --allow-empty -m rf-base

  reff="$(mktemp)"
  : > "$reff"
  local before_status after_status new_status before_patch after_patch dirty_line dirty_path
  before_status="$(mktemp)"
  after_status="$(mktemp)"
  new_status="$(mktemp)"
  before_patch="$(mktemp)"
  after_patch="$(mktemp)"
  git -C "$main" status --porcelain=v1 --untracked-files=all | LC_ALL=C sort > "$before_status"
  git -C "$main" diff --binary HEAD > "$before_patch" 2>/dev/null || true
  RF_MAIN_TREE_DIRTY=0
  RF_MAIN_DIRTY_PATHS=""
  local fix_argv=()
  while IFS= read -r a; do fix_argv+=("$a"); done < <(jq -r '.fix_executor[]' "$mp")
  [ ${#fix_argv[@]} -gt 0 ] || die "manifest.fix_executor 为空(引擎载入应已挡,防御)"
  RF_FIX_CMD="${fix_argv[*]}"
  (
    cd "$STAGING"
    RELEASE_FIX_STAGING="$STAGING" RELEASE_FIX_FINDINGS="$findings" RELEASE_FIX_WORKER_REF_FILE="$reff" \
      "${fix_argv[@]}"
  ) >&2 || echo "WARN: fix_executor 退非零(仍走 path-gate 审它改了什么)" >&2

  git -C "$main" status --porcelain=v1 --untracked-files=all | LC_ALL=C sort > "$after_status"
  if ! cmp -s "$before_status" "$after_status"; then
    RF_MAIN_TREE_DIRTY=1
    comm -13 "$before_status" "$after_status" > "$new_status" || true
    git -C "$main" diff --binary HEAD > "$after_patch" 2>/dev/null || true
    if [ -s "$after_patch" ]; then git -C "$main" apply -R "$after_patch" >/dev/null 2>&1 || true; fi
    if [ -s "$before_patch" ]; then git -C "$main" apply "$before_patch" >/dev/null 2>&1 || true; fi
    while IFS= read -r dirty_line; do
      [ -n "$dirty_line" ] || continue
      dirty_path="${dirty_line#???}"
      case "$dirty_line" in
        '?? '*) rm -rf -- "$main/${dirty_line#?? }" ;;
      esac
      [ -n "$dirty_path" ] && RF_MAIN_DIRTY_PATHS="${RF_MAIN_DIRTY_PATHS}${dirty_path}"$'\n'
    done < "$new_status"
  fi
  rm -f "$before_status" "$after_status" "$new_status" "$before_patch" "$after_patch"

  git -C "$STAGING" add -A >/dev/null 2>&1 || true
  CHANGED_PATHS=()
  while IFS= read -r p; do [ -n "$p" ] && CHANGED_PATHS+=("$p"); done \
    < <(git -C "$STAGING" diff --cached --name-only HEAD)
  RF_WORKER_REF="$(head -1 "$reff" 2>/dev/null || true)"
  rm -f "$reff"
}

_path_gate() {
  local f="$1" mp p g
  mp="$(jq -r '.manifest_path' "$f")"
  local editable=() p0=()
  while IFS= read -r g; do [ -n "$g" ] && editable+=("$g"); done < <(jq -r '.editable_paths[]' "$mp")
  while IFS= read -r g; do [ -n "$g" ] && p0+=("$g"); done < <(jq -r '.p0_paths[]' "$mp")
  BLOCKED_PATHS=()
  if [ ${#CHANGED_PATHS[@]} -gt 0 ]; then
    for p in "${CHANGED_PATHS[@]}"; do
      if [ ${#p0[@]} -gt 0 ] && _match_any "$p" "${p0[@]}"; then
        BLOCKED_PATHS+=("$p")
        continue
      fi
      if [ ${#editable[@]} -eq 0 ] || ! _match_any "$p" "${editable[@]}"; then
        BLOCKED_PATHS+=("$p")
      fi
    done
  fi
}

_apply_staging_to_main() {
  local staging="$1" main st p
  main="$(_repo_top)"
  while IFS=$'\t' read -r st p; do
    [ -n "$p" ] || continue
    case "$st" in
      D*) rm -f "$main/$p" ;;
      *)
        mkdir -p "$main/$(dirname "$p")"
        [ -L "$main/$p" ] && rm -f "$main/$p"
        cp "$staging/$p" "$main/$p"
        ;;
    esac
  done < <(git -C "$staging" diff --cached --name-status HEAD)
}

_discard_staging() {
  local s="$1" parent
  parent="$(dirname "$s")"
  git worktree remove --force "$s" 2>/dev/null || rm -rf "$s"
  rmdir "$parent" 2>/dev/null || true
}

_post_fix_gate() {
  local f="$1" name="$2" mp a rc=0 gate_out
  mp="$(jq -r '.manifest_path' "$f")"
  local gate_argv=()
  while IFS= read -r a; do gate_argv+=("$a"); done < <(jq -r '.post_fix_gate[]' "$mp")
  [ ${#gate_argv[@]} -gt 0 ] || die "manifest.post_fix_gate 为空(引擎载入应已挡,防御)"
  gate_out="$( cd "$(_repo_top)" && "${gate_argv[@]}" 2>&1 )" || rc=$?

  append_attempt "$f" "$name" "post_fix_gate" "$( [ "$rc" -eq 0 ] && echo pass || echo fail )" "" ""
  local gate_cmd
  gate_cmd="$(jq -r '.post_fix_gate|join(" ")' "$mp")"
  patch_last_attempt "$f" "[]" "[]" \
    "$(jq -nc --argjson rc "$rc" --arg cmd "$gate_cmd" \
        --arg out "$(printf '%s' "$gate_out" | head -c 400)" '[{gate:$cmd, rc:$rc, output:$out}]')" "" "$gate_cmd"

  if [ "$rc" -eq 0 ]; then
    emit_event "$f" "classified" "$name" "P1" "" "$(jq -r '.attempt_ledger[-1].attempt_id' "$f")"
    edit "$f" --arg n "$name" \
      '(.stages |= map(if .name==$n then .status="pending" else . end))
       | .current_stage=([.stages[]|select(.status=="pending")][0].name // null)'
    echo "POST-FIX-GATE-PASS:$name(架构闸绿,待重跑)"
    return 0
  fi

  local diag_argv=() findings_tmp
  if [ "$(jq -r '.post_fix_diagnose != null' "$mp")" = "true" ]; then
    while IFS= read -r a; do diag_argv+=("$a"); done < <(jq -r '.post_fix_diagnose[]' "$mp")
  else
    while IFS= read -r a; do diag_argv+=("$a"); done < <(jq -r '.diagnose[]' "$mp")
  fi
  findings_tmp="$(mktemp)"
  ( cd "$(_repo_top)" && "${diag_argv[@]}" ) > "$findings_tmp" 2>/dev/null || true
  echo "POST-FIX-GATE-FAIL:$name(架构闸红,重分级)"
  cmd_stage_fail --stage "$name" --findings "$findings_tmp"
  rm -f "$findings_tmp"
}

cmd_dispatch_p1() {
  local f="$1" name="$2" fp="$3" findings="$4" staging
  _run_fix_in_staging "$f" "$findings"
  staging="$STAGING"
  _path_gate "$f"
  if [ "${RF_MAIN_TREE_DIRTY:-0}" = "1" ]; then
    while IFS= read -r p; do
      [ -n "$p" ] && BLOCKED_PATHS+=("main:$p")
    done <<< "${RF_MAIN_DIRTY_PATHS:-main-worktree}"
  fi
  if [ ${#BLOCKED_PATHS[@]} -gt 0 ]; then
    _discard_staging "$staging"
    append_attempt "$f" "$name" "path_gate" "rejected" "$fp" ""
    patch_last_attempt "$f" "$(_json_changed_paths)" "$(_json_array "${BLOCKED_PATHS[@]}")" "[]" "" "$RF_FIX_CMD"
    edit "$f" --arg n "$name" --arg bp "$(printf '%s ' "${BLOCKED_PATHS[@]}")" \
      '.pause={at_stage:$n, kind:"surface", reason:"needs-redirection",
               question:("P1 修复 diff 越界(触 p0_paths 或出 editable_paths): "+($bp|rtrimstr(" "))+";已弃 diff、主树复原干净,停交人")}'
    emit_event "$f" "paused" "$name" "P0" "$fp" "$(jq -r '.attempt_ledger[-1].attempt_id' "$f")"
    echo "PATH-GATE-REJECT:$name 越界=[${BLOCKED_PATHS[*]}](弃 diff+主树干净+PAUSE)"
    return 0
  fi

  _apply_staging_to_main "$staging"
  _discard_staging "$staging"
  append_attempt "$f" "$name" "fix" "applied" "$fp" ""
  patch_last_attempt "$f" "$(_json_changed_paths)" "[]" "[]" "$RF_WORKER_REF" "$RF_FIX_CMD"
  emit_event "$f" "classified" "$name" "P1" "$fp" "$(jq -r '.attempt_ledger[-1].attempt_id' "$f")"
  local changed_text=""
  if [ ${#CHANGED_PATHS[@]} -gt 0 ]; then changed_text="$(printf '%s ' "${CHANGED_PATHS[@]}")"; changed_text="${changed_text% }"; fi
  echo "FIX-APPLIED:$name changed=[$changed_text]"
  _post_fix_gate "$f" "$name"
}

# $1=state $2=event $3=stage $4=tier $5=fingerprint $6=attempt_ref
emit_event() {
  local f="$1" event="$2" stage="$3" tier="$4" fp="$5" aref="$6"
  local mp
  mp="$(jq -r '.manifest_path' "$f")"
  [ -f "$mp" ] || { echo "WARN: manifest 已清($mp),跳过 event 落地: $event" >&2; return 0; }

  local product round trace ev
  product="$(jq -r '.product' "$f")"
  round="$(jq -r '.round' "$f")"
  trace="${RELEASE_TRACE_ID:-rel-$(date -u +%s)-$$}"
  ev="$(jq -nc --arg e "$event" --arg p "$product" --arg s "$stage" --arg tier "$tier" \
        --arg fp "$fp" --argjson r "$round" --arg tr "$trace" --arg ar "$aref" --arg ts "$(now)" \
        '{schema_version:"1", event:$e, product:$p,
          stage:(if $s=="" then null else $s end),
          tier:(if $tier=="" then null else $tier end),
          fingerprint:(if $fp=="" then null else $fp end),
          round:$r, trace_id:$tr,
          attempt_ref:(if $ar=="" then null else $ar end), timestamp:$ts}')"
  printf '%s' "$ev" | uv run --quiet "$SCRIPT_DIR/release_contracts.py" validate-event - \
    || { echo "ERROR: 引擎产出非法 ReleaseLoopEvent: $ev" >&2; return 0; }

  local sink_argv=()
  while IFS= read -r arg; do
    sink_argv+=("$arg")
  done < <(jq -r '.event_sink[]' "$mp")
  printf '%s\n' "$ev" | "${sink_argv[@]}" || echo "WARN: event_sink 落地失败: $event" >&2
}

cmd_init() {
  local manifest="" max_rounds=6
  while [ $# -gt 0 ]; do
    case "$1" in
      --manifest) manifest="$2"; shift 2 ;;
      --max-rounds) max_rounds="$2"; shift 2 ;;
      *) die "未知参数 $1" ;;
    esac
  done
  [ -n "$manifest" ] || die "--manifest 必填"
  [ -f "$manifest" ] || die "manifest 文件不存在: $manifest"
  case "$max_rounds" in ''|*[!0-9]*) die "--max-rounds 必须是非负整数" ;; esac

  local canon
  canon="$(uv run --quiet "$SCRIPT_DIR/release_contracts.py" validate-manifest "$manifest")" \
    || die "manifest 不合规(引擎载入 fail-loud，请人改 manifest)"

  local f top sd mp source_commit
  top="$(git rev-parse --show-toplevel)"
  source_commit="$(git -C "$top" rev-parse HEAD)"
  sd="$(mmw_resolve_state_subdir "$top")"
  f="$top/$sd/$STATE_NAME"
  [ -f "$f" ] && die "已有未收束 release loop;先 release close 或复用"
  mkdir -p "$top/$sd"
  mp="$(cd "$(dirname "$manifest")" && pwd)/$(basename "$manifest")"
  printf '%s' "$canon" | jq --arg mp "$mp" --arg sc "$source_commit" --argjson mr "$max_rounds" --arg ts "$(now)" \
    '{schema_version:"1", product:.product, manifest_path:$mp, source_commit:$sc,
      stages:[.stages[]|{name:.name, run:.run, status:"pending"}],
      current_stage:(.stages[0].name // null),
      round:1, max_rounds:$mr, fingerprint_ledger:[],
      budget:{attempts:0, max_attempts:$mr, started_at:$ts, max_wall_clock_seconds:3600},
      attempt_ledger:[], pause:null}' | write "$f"
  echo "INIT product=$(printf '%s' "$canon" | jq -r .product) stages=$(printf '%s' "$canon" | jq -r '.stages|length') max_rounds=$max_rounds"
}

cmd_where() {
  local f
  f="$(need_state)"
  jq -e . "$f" >/dev/null 2>&1 || { echo "CORRUPT:release-state 空/非法 JSON"; return 0; }
  if [ "$(jq -r '.pause // "null"' "$f")" != "null" ]; then
    echo "PAUSED:$(jq -r '.pause.reason' "$f")"
    return 0
  fi
  local n
  n="$(jq -r '.stages|length' "$f")"
  [ "$n" -gt 0 ] || { echo "NO-STAGES:manifest 合规但无阶段可跑(请人改 manifest)"; return 0; }
  local failed
  failed="$(jq -r '[.stages[]|select(.status=="failed")][0].name // ""' "$f")"
  if [ -n "$failed" ]; then
    jq -r --arg c "$failed" '"RETRY-STAGE:"+$c+" RUN:"+([.stages[]|select(.name==$c)][0].run|join(" "))' "$f"
    return 0
  fi
  local cur
  cur="$(jq -r '[.stages[]|select(.status=="pending")][0].name // ""' "$f")"
  if [ -z "$cur" ]; then
    local failed
    failed="$(jq -r '[.stages[]|select(.status=="failed")|.name]|join(",")' "$f")"
    [ -z "$failed" ] && echo "SUCCESS:all stages done" || echo "FAILED-STAGE:$failed"
    return 0
  fi
  jq -r --arg c "$cur" '"STAGE:"+$c+" RUN:"+([.stages[]|select(.name==$c)][0].run|join(" "))' "$f"
}

cmd_stage() {
  local verb="${1:-}"
  shift || true
  case "$verb" in
    done) cmd_stage_done "$@" ;;
    fail) cmd_stage_fail "$@" ;;
    run) cmd_stage_run "$@" ;;
    *) die "用法 stage run|done|fail" ;;
  esac
}

_run_remote_build() {
  local top="$1" source_commit="$2" stage_dir="$3"
  shift 3
  local script="" context="" remote_host remote_root remote_input archive commit_file remote_context task_name
  while [ $# -gt 0 ]; do
    case "$1" in
      --script) script="${2:-}"; shift 2 ;;
      --context) context="${2:-}"; shift 2 ;;
      *) echo "ERROR: mmw-release-remote-build 未知参数 $1" >&2; return 64 ;;
    esac
  done
  case "$script" in /*) ;; *) echo "ERROR: remote build --script 必须是绝对路径" >&2; return 64 ;; esac
  case "$context" in /*) ;; *) echo "ERROR: remote build --context 必须是绝对路径" >&2; return 64 ;; esac
  [ -f "$script" ] || { echo "ERROR: remote build script 不存在: $script" >&2; return 64; }
  [ -f "$context" ] || { echo "ERROR: remote build context 不存在: $context" >&2; return 64; }
  remote_host="${RELEASE_REMOTE_HOST:-}"
  remote_root="${RELEASE_REMOTE_ROOT:-}"
  [ -n "$remote_host" ] || { echo "ERROR: remote build 缺 RELEASE_REMOTE_HOST" >&2; return 64; }
  [ -n "$remote_root" ] || { echo "ERROR: remote build 缺 RELEASE_REMOTE_ROOT" >&2; return 64; }

  remote_input="${remote_root%/}/$source_commit"
  archive="$stage_dir/source.zip"
  commit_file="$stage_dir/SOURCE_COMMIT.txt"
  remote_context="$stage_dir/release-context.remote.json"
  git -C "$top" archive --format=zip --output "$archive" HEAD || return $?
  printf '%s\n' "$source_commit" > "$commit_file"
  jq --arg root "$remote_input/source" '.repo_root = $root' "$context" > "$remote_context" || return $?

  ssh "$remote_host" "New-Item -ItemType Directory -Force -Path '$remote_input' | Out-Null" || return $?
  scp "$archive" "$remote_host:$remote_input/source.zip" || return $?
  scp "$commit_file" "$remote_host:$remote_input/SOURCE_COMMIT.txt" || return $?
  scp "$script" "$remote_host:$remote_input/release.ps1" || return $?
  scp "$remote_context" "$remote_host:$remote_input/release-context.json" || return $?

  task_name="mmw-release-${source_commit:0:12}-${RANDOM}"
  ssh "$remote_host" "schtasks /create /tn '$task_name' /tr \"powershell -NoProfile -ExecutionPolicy Bypass -Command \\\"Expand-Archive -Force '$remote_input/source.zip' '$remote_input/source'; & '$remote_input/release.ps1' *>> '$remote_input/build-run.log'; \\\$LASTEXITCODE | Set-Content '$remote_input/build-run.exitcode'\\\"\" /sc once /st 00:00 /f" || return $?
  ssh "$remote_host" "schtasks /run /tn '$task_name'" || return $?

  local poll seen="" exit_code="" attempt
  for attempt in 1 2 3; do
    seen="$(ssh "$remote_host" "if (Test-Path '$remote_input/build-run.log') { 'Y' } else { 'N' }" 2>/dev/null || true)"
    if [ "$seen" = "Y" ]; then
      exit_code="$(ssh "$remote_host" "Get-Content '$remote_input/build-run.exitcode'" 2>/dev/null || true)"
      [ -n "$exit_code" ] && break
    fi
  done
  [ "$seen" = "Y" ] || { echo "ERROR: remote build 未出现 build-run.log" >&2; return 70; }
  case "$exit_code" in
    ''|*[!0-9-]*) echo "ERROR: remote build exit-code 非法: $exit_code" >&2; return 70 ;;
  esac
  REMOTE_LOG_REF="pc:$remote_input/build-run.log"
  ssh "$remote_host" "schtasks /delete /tn '$task_name' /f" >/dev/null 2>&1 || true
  [ "$exit_code" = "0" ] || return "$exit_code"
}

cmd_stage_run() {
  local requested="" f name top source_commit attempt_id stage_dir log_file raw expanded rc=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --stage) requested="$2"; shift 2 ;;
      *) die "未知参数 $1" ;;
    esac
  done

  f="$(need_state)"
  jq -e . "$f" >/dev/null 2>&1 || die "release-state 损坏，拒绝执行 stage"
  name="$(jq -r '[.stages[] | select(.status == "pending" or .status == "failed" or .status == "running")][0].name // ""' "$f")"
  [ -n "$name" ] || die "没有可执行的 stage"
  if [ -n "$requested" ] && [ "$requested" != "$name" ]; then
    die "只能执行最早未完成 stage: $name"
  fi

  top="$(_repo_top)"
  source_commit="$(git -C "$top" rev-parse HEAD)"
  attempt_id="a$(jq -r '.attempt_ledger | length' "$f")-$name"
  stage_dir="$(dirname "$f")/release-artifacts/$attempt_id"
  log_file="$stage_dir/$name.log"
  mkdir -p "$stage_dir"

  local argv=()
  while IFS= read -r raw; do
    expanded="${raw//\$\{RELEASE_STAGE_DIR\}/$stage_dir}"
    expanded="${expanded//\$\{RELEASE_PLUGIN_DIR\}/$SCRIPT_DIR}"
    argv+=("$expanded")
  done < <(jq -r --arg n "$name" '.stages[] | select(.name == $n) | .run[]' "$f")
  [ ${#argv[@]} -gt 0 ] || die "stage $name 的 argv 为空"

  edit "$f" --arg n "$name" '(.stages |= map(if .name == $n then .status = "running" else . end)) | .current_stage = $n'
  append_attempt "$f" "$name" "stage_run" "running" "" ""
  local remote_log_ref=""
  if [ "$name" = "build" ] && [ "${argv[0]}" = "mmw-release-remote-build" ]; then
    if _run_remote_build "$top" "$source_commit" "$stage_dir" "${argv[@]:1}" >"$log_file" 2>&1; then
      remote_log_ref="${REMOTE_LOG_REF:-}"
      rc=0
    else
      rc=$?
      remote_log_ref="${REMOTE_LOG_REF:-}"
    fi
  elif (
    cd "$top"
    RELEASE_REPO_ROOT="$top" \
    RELEASE_STATE_FILE="$f" \
    RELEASE_STAGE_NAME="$name" \
    RELEASE_SOURCE_COMMIT="$source_commit" \
    RELEASE_STAGE_DIR="$stage_dir" \
    "${argv[@]}"
  ) >"$log_file" 2>&1; then
    rc=0
  else
    rc=$?
  fi

  if [ "$rc" -eq 0 ]; then
    edit "$f" --arg n "$name" --arg log "file:$log_file" --arg remote "$remote_log_ref" \
      '(.stages |= map(if .name == $n then .status = "done" else . end))
       | .current_stage = ([.stages[] | select(.status == "pending")][0].name // null)
       | .attempt_ledger[-1].outcome = "done"
       | .attempt_ledger[-1].log_refs = (if $remote == "" then [$log] else [$log, $remote] end)'
    echo "STAGE-RUN-DONE $name"
    return 0
  fi

  edit "$f" --arg n "$name" --arg log "file:$log_file" --arg remote "$remote_log_ref" \
    '(.stages |= map(if .name == $n then .status = "failed" else . end))
     | .current_stage = $n
     | .attempt_ledger[-1].outcome = "fail"
     | .attempt_ledger[-1].log_refs = (if $remote == "" then [$log] else [$log, $remote] end)'
  local mp findings_file diag_arg
  mp="$(jq -r '.manifest_path' "$f")"
  findings_file="$stage_dir/$name.findings.json"
  local diagnose_argv=()
  while IFS= read -r diag_arg; do
    diagnose_argv+=("$diag_arg")
  done < <(jq -r '.diagnose[]' "$mp")
  [ ${#diagnose_argv[@]} -gt 0 ] || die "manifest.diagnose 为空"
  ( cd "$top" && "${diagnose_argv[@]}" ) > "$findings_file" 2>&1 || true
  echo "STAGE-RUN-FAILED $name rc=$rc; 进入 diagnose 分级" >&2
  cmd_stage_fail --stage "$name" --findings "$findings_file"
}

cmd_stage_done() {
  local name=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --stage) name="$2"; shift 2 ;;
      *) die "未知参数 $1" ;;
    esac
  done
  [ -n "$name" ] || die "--stage 必填"
  local f
  f="$(need_state)"
  jq -e --arg n "$name" 'any(.stages[]; .name==$n)' "$f" >/dev/null || die "无此 stage: $name"
  append_attempt "$f" "$name" "stage" "done" "" ""
  edit "$f" --arg n "$name" \
    '(.stages |= map(if .name==$n then .status="done" else . end))
     | .current_stage=([.stages[]|select(.status=="pending")][0].name // null)'
  echo "STAGE-DONE $name"
}

cmd_stage_fail() {
  local name="" findings=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --stage) name="$2"; shift 2 ;;
      --findings) findings="$2"; shift 2 ;;
      *) die "未知参数 $1" ;;
    esac
  done
  [ -n "$name" ] || die "--stage 必填"
  [ -n "$findings" ] || die "--findings 必填"
  [ -f "$findings" ] || die "findings 文件不存在: $findings"

  local f
  f="$(need_state)"
  jq -e --arg n "$name" 'any(.stages[]; .name==$n)' "$f" >/dev/null || die "无此 stage: $name"

  local cls
  if ! cls="$(uv run --quiet "$SCRIPT_DIR/release_contracts.py" classify-findings "$findings")"; then
    append_attempt "$f" "$name" "stage" "unclassifiable" "" "$findings"
    edit "$f" --arg n "$name" --arg fd "$findings" \
      '(.stages |= map(if .name==$n then .status="failed" else . end))
       | .current_stage=$n
       | .pause={at_stage:$n, kind:"surface", reason:"needs-context",
                 question:("stage "+$n+" 的 diagnose 产不出合规 Finding("+$fd+"),无法分级,交人")}'
    emit_event "$f" "stage.failed" "$name" "" "" ""
    echo "UNCLASSIFIABLE:$name(escalate PAUSE)"
    return 0
  fi

  if [ "$(printf '%s' "$cls" | jq -r '.failing|length')" -eq 0 ]; then
    append_attempt "$f" "$name" "stage" "unclassifiable" "" "$findings"
    edit "$f" --arg n "$name" --arg fd "$findings" \
      '(.stages |= map(if .name==$n then .status="failed" else . end))
       | .current_stage=$n
       | .pause={at_stage:$n, kind:"surface", reason:"needs-context",
                 question:("stage "+$n+" 的 diagnose 未产出 fail Finding("+$fd+"),无法诊断,交人")}'
    emit_event "$f" "stage.failed" "$name" "" "" "$(jq -r '.attempt_ledger[-1].attempt_id' "$f")"
    echo "UNCLASSIFIABLE:$name(empty findings escalate PAUSE)"
    return 0
  fi

  local tier fp aref
  tier="$(printf '%s' "$cls" | jq -r '.highest_tier // ""')"
  fp="$(printf '%s' "$cls" | jq -r '.failing[0].root_cause_fingerprint // ""')"
  append_attempt "$f" "$name" "stage" "fail" "$fp" "$findings"
  aref="$(jq -r '.attempt_ledger[-1].attempt_id' "$f")"

  while IFS= read -r one; do
    [ -n "$one" ] || continue
    edit "$f" --arg fp "$one" \
      'if any(.fingerprint_ledger[]; .fingerprint==$fp)
       then .fingerprint_ledger |= map(if .fingerprint==$fp then .count+=1 else . end)
       else .fingerprint_ledger += [{fingerprint:$fp, count:1}] end'
  done < <(printf '%s' "$cls" | jq -r '.failing[].root_cause_fingerprint')

  edit "$f" --arg n "$name" \
    '(.stages |= map(if .name==$n then .status="failed" else . end))
     | .current_stage=$n'
  if [ "$tier" = "P0" ]; then
    edit "$f" --arg n "$name" --arg fp "$fp" \
      '.pause={at_stage:$n, kind:"surface", reason:"needs-redirection",
               question:("stage "+$n+" P0 硬约束失败("+$fp+"),触人工门禁,停")}'
    emit_event "$f" "paused" "$name" "P0" "$fp" "$aref"
    echo "CLASSIFY=P0 $name -> PAUSE(交人)"
    return 0
  fi

  emit_event "$f" "classified" "$name" "$tier" "$fp" "$aref"
  echo "CLASSIFY=$tier $name(待 fix-dispatch,归 002)"
}

cmd_dispatch() {
  local name="" findings=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --stage) name="$2"; shift 2 ;;
      --findings) findings="$2"; shift 2 ;;
      *) die "未知参数 $1" ;;
    esac
  done
  [ -n "$name" ] || die "--stage 必填"
  [ -n "$findings" ] || die "--findings 必填"
  [ -f "$findings" ] || die "findings 文件不存在: $findings"

  local f cls
  f="$(need_state)"
  jq -e --arg n "$name" 'any(.stages[]; .name==$n)' "$f" >/dev/null || die "无此 stage: $name"

  if ! cls="$(uv run --quiet "$SCRIPT_DIR/release_contracts.py" classify-findings "$findings")"; then
    edit "$f" --arg n "$name" --arg fd "$findings" \
      '.pause={at_stage:$n, kind:"surface", reason:"needs-context",
               question:("dispatch 时 findings("+$fd+")产不出合规 Finding,无法分级,交人")}'
    echo "UNCLASSIFIABLE:$name(dispatch escalate)"
    return 0
  fi

  local tier fp
  tier="$(printf '%s' "$cls" | jq -r '.highest_tier // ""')"
  fp="$(printf '%s' "$cls" | jq -r '.failing[0].root_cause_fingerprint // ""')"
  [ -n "$tier" ] || { echo "NOTHING-TO-DISPATCH:$name 无 failing finding"; return 0; }
  if ! _convergence_guard "$f" "$cls" "$name"; then return 0; fi

  case "$tier" in
    P0)
      append_attempt "$f" "$name" "dispatch" "fail" "$fp" "$findings"
      local aref
      aref="$(jq -r '.attempt_ledger[-1].attempt_id' "$f")"
      edit "$f" --arg n "$name" --arg fp "$fp" \
        '(.stages |= map(if .name==$n then .status="failed" else . end))
         | .current_stage=$n
         | .pause={at_stage:$n, kind:"surface", reason:"needs-redirection",
                  question:("dispatch "+$n+" P0 硬约束("+$fp+"),触人工门禁,停")}'
      emit_event "$f" "paused" "$name" "P0" "$fp" "$aref"
      echo "P0:$name P0 硬约束($fp),交人(已 PAUSE)"
      ;;
    P2) cmd_dispatch_p2 "$f" "$name" "$fp" ;;
    P1) cmd_dispatch_p1 "$f" "$name" "$fp" "$findings" ;;
    *) die "未知 tier: $tier" ;;
  esac
}

cmd_round() {
  local verb="${1:-}"
  shift || true
  [ "$verb" = "next" ] || die "用法 round next"
  local f max cur new
  f="$(need_state)"
  max="$(jq -r '.max_rounds // 0' "$f")"
  cur="$(jq -r '.round // 1' "$f")"
  new=$(( cur + 1 ))
  if [ "$max" -gt 0 ] && [ "$new" -gt "$max" ]; then
    edit "$f" --arg q "跑满 $max 轮未收敛，引擎熔断交人(防无限打转)" \
      '.pause={at_stage:(.current_stage // ""), kind:"surface", reason:"needs-redirection", question:$q}'
    echo "ROUND-CAP:max=$max(已自动 surface 交人)"
    return 0
  fi
  edit "$f" --argjson r "$new" '.round=$r'
  echo "ROUND=$new/$max"
}

cmd_surface() {
  local kind="" q="" at=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --kind) kind="$2"; shift 2 ;;
      --question) q="$2"; shift 2 ;;
      --at-stage) at="$2"; shift 2 ;;
      *) die "未知参数 $1" ;;
    esac
  done
  case "$kind" in needs-context|needs-redirection) ;; *) die "--kind 只能 needs-context|needs-redirection" ;; esac
  [ -n "$q" ] || die "--question 必填"
  edit "$(need_state)" --arg at "$at" --arg k "$kind" --arg q "$q" \
    '.pause={at_stage:$at, kind:"surface", reason:$k, question:$q}'
  echo "SURFACED $kind"
}

cmd_resume() {
  local f live saved start
  f="$(need_state)"
  jq -e . "$f" >/dev/null 2>&1 || die "release-state 损坏，拒绝 resume"
  live="$(git -C "$(_repo_top)" rev-parse HEAD)"
  saved="$(jq -r '.source_commit // ""' "$f")"
  if [ "$saved" != "$live" ]; then
    edit "$f" --arg sc "$live" \
      '(.stages |= map(.status = "pending"))
       | .source_commit = $sc
       | .current_stage = (.stages[0].name // null)
       | .pause = null'
    echo "RESUMED:HEAD-CHANGED 重验全部 stages"
    return 0
  fi

  start="$(jq -r '[.stages | to_entries[] | select(.value.status == "failed" or .value.status == "running") | .key][0] // ""' "$f")"
  if [ -n "$start" ]; then
    edit "$f" --argjson start "$start" \
      '(.stages |= (to_entries | map(if .key >= $start then .value.status = "pending" else . end) | map(.value)))
       | .current_stage = .stages[$start].name
       | .pause = null'
    echo "RESUMED:stage=$start"
    return 0
  fi

  edit "$f" '.pause = null'
  echo "RESUMED"
}

cmd_close() {
  local top sd
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "NO-GIT"; return 0; }
  sd="$(mmw_resolve_state_subdir "$top")"
  rm -f "$top/$sd/$STATE_NAME"
  echo "CLOSED"
}

cmd_exit_check() {
  local f
  f="$(need_state)"
  jq -e . "$f" >/dev/null 2>&1 || { echo "CORRUPT:release-state 空/非法 JSON"; return 0; }
  if [ "$(jq -r '.pause // "null"' "$f")" != "null" ]; then
    echo "PAUSED:$(jq -r '.pause.reason' "$f")"
    return 0
  fi
  local n
  n="$(jq -r '.stages|length' "$f")"
  [ "$n" -gt 0 ] || { echo "NOT-DONE:stages=EMPTY(manifest 无阶段)"; return 0; }
  local rem
  rem="$(jq -r '[.stages[]|select(.status=="failed")|.name]|join(",")' "$f")"
  [ -n "$rem" ] || rem="$(jq -r '[.stages[]|select(.status!="done")|.name]|join(",")' "$f")"
  [ -z "$rem" ] && echo "DONE" || echo "NOT-DONE:stages=$rem"
}

cmd_receipt() {
  local f
  f="$(need_state)"
  jq -e . "$f" >/dev/null 2>&1 || { echo "CORRUPT:release-state 空/非法 JSON"; return 0; }
  echo "# Release 回执 - product=$(jq -r .product "$f")"
  if [ "$(jq -r '.pause // "null"' "$f")" != "null" ]; then
    echo "## 停在 stage=$(jq -r '.pause.at_stage' "$f") 原因=$(jq -r '.pause.reason' "$f")"
    jq -r '.pause.question' "$f"
  fi
  echo "## 已试 attempt:"
  jq -r '.attempt_ledger[] | "- ["+.action_kind+"] stage="+.stage+" outcome="+.outcome+(if .root_cause_fingerprint then " fp="+.root_cause_fingerprint else "" end)+(if (.artifact_refs|length)>0 then " findings="+(.artifact_refs|join(",")) else "" end)' "$f"
  echo "## fingerprint 累计:"
  jq -r '.fingerprint_ledger[] | "- "+.fingerprint+" x"+(.count|tostring)' "$f"
}

case "${1:-}" in
  init)       shift; cmd_init "$@" ;;
  where)      shift; cmd_where "$@" ;;
  stage)      shift; cmd_stage "$@" ;;
  round)      shift; cmd_round "$@" ;;
  surface)    shift; cmd_surface "$@" ;;
  resume)     shift; cmd_resume "$@" ;;
  close)      shift; cmd_close "$@" ;;
  exit-check) shift; cmd_exit_check "$@" ;;
  receipt)    shift; cmd_receipt "$@" ;;
  dispatch)   shift; cmd_dispatch "$@" ;;
  *) die "用法: release-flow.sh init|where|stage|round|surface|resume|close|exit-check|receipt|dispatch ..." ;;
esac
