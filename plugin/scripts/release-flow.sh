#!/usr/bin/env bash
# release-flow.sh -- 通用 release-flow 引擎(确定层:操作 release-state.json)。
#
#   init        --manifest <path> [--max-rounds N]
#   where       报当前 stage+run / SUCCESS / PAUSED / NO-STAGES / CORRUPT
#   stage       run|done|fail
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

_file_sha256() {
  shasum -a 256 "$1" | awk '{print $1}'
}

_snapshot_baseline_untracked() {
  local top="$1" f="${2:-}" path
  BASELINE_UNTRACKED_PATHS=()
  BASELINE_UNTRACKED_HASHES=()
  while IFS= read -r path; do
    [ -n "$path" ] || continue
    BASELINE_UNTRACKED_PATHS+=("$path")
    BASELINE_UNTRACKED_HASHES+=("$(_file_sha256 "$top/$path")")
  done < <(git -C "$top" ls-files --others --exclude-standard)
  # P0:被 gitignore 的受保护文件(如已有 .env)也纳入 baseline(带原始 hash),让「自愈修复改写
  # 已有受保护文件」走 baseline_untracked_changed 的诚实 PAUSE、保留原文件,而不是被当成本轮
  # 新建候选、在 reject cleanup 时误 rm 掉(会丢失原 secret)。
  if [ -n "$f" ] && _load_path_hard_deny "$f" 2>/dev/null; then
    while IFS= read -r path; do
      [ -n "$path" ] || continue
      _match_any "$path" "${PROTECTION_MATCHERS[@]-}" || continue
      _is_baseline_untracked "$path" && continue
      BASELINE_UNTRACKED_PATHS+=("$path")
      BASELINE_UNTRACKED_HASHES+=("$(_file_sha256 "$top/$path")")
    done < <(git -C "$top" ls-files --others --ignored --exclude-standard)
  fi
}

_is_baseline_untracked() {
  local candidate="$1" path
  for path in "${BASELINE_UNTRACKED_PATHS[@]-}"; do
    [ "$candidate" = "$path" ] && return 0
  done
  return 1
}

_baseline_untracked_changed() {
  local top="$1" index path actual
  BASELINE_CHANGED_PATHS=()
  for index in "${!BASELINE_UNTRACKED_PATHS[@]}"; do
    path="${BASELINE_UNTRACKED_PATHS[$index]}"
    if [ ! -e "$top/$path" ] && [ ! -L "$top/$path" ]; then
      BASELINE_CHANGED_PATHS+=("$path")
      continue
    fi
    actual="$(_file_sha256 "$top/$path")"
    [ "$actual" = "${BASELINE_UNTRACKED_HASHES[$index]}" ] || BASELINE_CHANGED_PATHS+=("$path")
  done
  [ ${#BASELINE_CHANGED_PATHS[@]} -eq 0 ]
}

_collect_candidate_paths() {
  local top="$1" f="$2" path
  TRACKED_PATHS=()
  NEW_UNTRACKED_PATHS=()
  CHANGED_PATHS=()
  while IFS= read -r path; do
    [ -n "$path" ] && TRACKED_PATHS+=("$path")
  done < <(git -C "$top" diff --name-only HEAD)
  while IFS= read -r path; do
    [ -n "$path" ] || continue
    _is_baseline_untracked "$path" || NEW_UNTRACKED_PATHS+=("$path")
  done < <(git -C "$top" ls-files --others --exclude-standard)
  # P0 安全:一般候选集用 --exclude-standard 排除 gitignored,曾致自愈修复新建的 gitignored
  # 受保护文件(如 .env/secret)看不见,流程误判「无改动」直接放过、不进 path-gate、不拦不存 patch。
  # 这里额外扫 gitignored 未跟踪文件,只把匹配 hard-deny 的纳入候选(缓存等不匹配的不受影响)。
  if [ -n "${f:-}" ] && _load_path_hard_deny "$f" 2>/dev/null; then
    while IFS= read -r path; do
      [ -n "$path" ] || continue
      _is_baseline_untracked "$path" && continue
      _match_any "$path" "${PROTECTION_MATCHERS[@]-}" && NEW_UNTRACKED_PATHS+=("$path")
    done < <(git -C "$top" ls-files --others --ignored --exclude-standard)
  fi
  if [ ${#TRACKED_PATHS[@]} -gt 0 ]; then
    CHANGED_PATHS+=("${TRACKED_PATHS[@]}")
  fi
  if [ ${#NEW_UNTRACKED_PATHS[@]} -gt 0 ]; then
    CHANGED_PATHS+=("${NEW_UNTRACKED_PATHS[@]}")
  fi
}

_load_path_hard_deny() {
  local f="$1" top mp source_rel source_file matchers path
  # P0:本轮 dispatch 若已在跑修复前冻结过 hard-deny 快照,后续一律用冻结值,不再从可能被修复
  # 改坏的 protection_source 重读——否则「改写 release_protection.json 本身」会让规则源读不出、
  # 把 P0 受保护路径违规降级成 needs-context「规则源不可读」,等于破坏被保护物就能关掉它自己的闸。
  if [ "${PROTECTION_FROZEN:-0}" = "1" ]; then
    [ ${#PROTECTION_MATCHERS[@]} -gt 0 ] && return 0
    PATH_GATE_ERROR="protection_source 冻结快照为空"
    return 1
  fi
  top="$(_repo_top)"
  mp="$(jq -r '.manifest_path' "$f")"
  source_rel="$(jq -er '.protection_source' "$mp" 2>/dev/null)" || {
    PATH_GATE_ERROR="manifest.protection_source 不可读"
    return 1
  }
  case "$source_rel" in
    /*|..|../*|*/../*) PATH_GATE_ERROR="protection_source 必须是仓库内相对路径: $source_rel"; return 1 ;;
  esac
  source_file="$top/$source_rel"
  [ -f "$source_file" ] || { PATH_GATE_ERROR="protection_source 不存在: $source_rel"; return 1; }
  matchers="$(mktemp)"
  if ! jq -er '.rules
    | if type == "array" then . else error("rules must be array") end
    | [ .[]
        | select(.kind == "path_hard_deny")
        | .matcher
        | if type == "string" and length > 0 then . else error("hard-deny matcher must be non-empty string") end
      ]
    | if length > 0 then .[] else error("no path_hard_deny matcher") end' "$source_file" > "$matchers"; then
    rm -f "$matchers"
    PATH_GATE_ERROR="protection_source 不合规: $source_rel"
    return 1
  fi
  PROTECTION_MATCHERS=()
  while IFS= read -r path; do
    [ -n "$path" ] && PROTECTION_MATCHERS+=("$path")
  done < "$matchers"
  rm -f "$matchers"
  [ ${#PROTECTION_MATCHERS[@]} -gt 0 ] || {
    PATH_GATE_ERROR="protection_source 没有 path_hard_deny matcher"
    return 1
  }
}

_path_gate() {
  local f="$1" mp path matcher
  _load_path_hard_deny "$f" || return 1
  mp="$(jq -r '.manifest_path' "$f")"
  EDITABLE_MATCHERS=()
  while IFS= read -r matcher; do
    [ -n "$matcher" ] && EDITABLE_MATCHERS+=("$matcher")
  done < <(jq -r '.editable_paths[]' "$mp")
  BLOCKED_PATHS=()
  for path in "${CHANGED_PATHS[@]-}"; do
    [ -n "$path" ] || continue
    if _match_any "$path" "${PROTECTION_MATCHERS[@]-}"; then
      BLOCKED_PATHS+=("$path")
      continue
    fi
    if [ ${#EDITABLE_MATCHERS[@]} -eq 0 ] || ! _match_any "$path" "${EDITABLE_MATCHERS[@]-}"; then
      BLOCKED_PATHS+=("$path")
    fi
  done
}

_write_path_gate_patch() {
  local f="$1" name="$2" top="$3" attempt_id artifact path rc
  attempt_id="a$(jq -r '.attempt_ledger | length' "$f")-$name"
  artifact="$(dirname "$f")/release-artifacts/$attempt_id-path-gate.patch"
  mkdir -p "$(dirname "$artifact")" || return 1
  git -C "$top" diff --binary HEAD > "$artifact" || return 1
  for path in "${NEW_UNTRACKED_PATHS[@]-}"; do
    [ -n "$path" ] || continue
    rc=0
    git -C "$top" diff --no-index --binary /dev/null -- "$path" >> "$artifact" || rc=$?
    [ "$rc" -eq 1 ] || [ "$rc" -eq 0 ] || return "$rc"
  done
  PATH_GATE_ARTIFACT="file:$artifact"
}

_restore_rejected_candidates() {
  local top="$1" path
  if [ ${#TRACKED_PATHS[@]} -gt 0 ]; then
    git -C "$top" restore --source=HEAD --staged --worktree -- "${TRACKED_PATHS[@]-}" || return 1
  fi
  for path in "${NEW_UNTRACKED_PATHS[@]-}"; do
    [ -n "$path" ] || continue
    rm -f -- "$top/$path" || return 1
  done
}

_record_pause() {
  local f="$1" name="$2" action="$3" outcome="$4" fp="$5" ref="$6" reason="$7" question="$8"
  local changed="$9" blocked="${10}" worker="${11}" command="${12}" tier="${13}" attempt_id
  append_attempt "$f" "$name" "$action" "$outcome" "$fp" "$ref"
  patch_last_attempt "$f" "$changed" "$blocked" "[]" "$worker" "$command"
  attempt_id="$(jq -r '.attempt_ledger[-1].attempt_id' "$f")"
  edit "$f" --arg n "$name" --arg r "$reason" --arg q "$question" \
    '.pause={at_stage:$n, kind:"surface", reason:$r, question:$q}'
  emit_event "$f" "paused" "$name" "$tier" "$fp" "$attempt_id"
}

_invalidate_all_stages() {
  local f="$1" source_commit="$2"
  edit "$f" --arg sc "$source_commit" \
    '(.stages |= map(.status="pending"))
     | .source_commit=$sc
     | .current_stage=(.stages[0].name // null)
     | .pause=null'
}

_run_direct_action() {
  local f="$1" mode="$2" findings="$3" top mp key arg ref_file
  top="$(_repo_top)"
  mp="$(jq -r '.manifest_path' "$f")"
  case "$mode" in
    fix) key="fix_executor" ;;
    derive) key="derive" ;;
    *) die "未知 direct action: $mode" ;;
  esac
  ACTION_ARGV=()
  while IFS= read -r arg; do ACTION_ARGV+=("$arg"); done < <(jq -r --arg key "$key" '.[$key][]' "$mp")
  [ ${#ACTION_ARGV[@]} -gt 0 ] || die "manifest.$key 为空(引擎载入应已挡,防御)"
  ACTION_COMMAND="${ACTION_ARGV[*]}"
  ACTION_RC=0
  RF_WORKER_REF=""
  if [ "$mode" = "fix" ]; then
    ref_file="$(mktemp)"
    : > "$ref_file"
    (
      cd "$top"
      unset RELEASE_FIX_STAGING
      RELEASE_FIX_FINDINGS="$findings" RELEASE_FIX_WORKER_REF_FILE="$ref_file" "${ACTION_ARGV[@]-}"
    ) || ACTION_RC=$?
    RF_WORKER_REF="$(head -1 "$ref_file" 2>/dev/null || true)"
    rm -f "$ref_file"
    return 0
  fi
  (
    cd "$top"
    unset RELEASE_FIX_STAGING
    "${ACTION_ARGV[@]-}"
  ) || ACTION_RC=$?
}

_post_fix_gate() {
  local f="$1" name="$2" fp="$3" repair_sha="$4" mp a rc=0 gate_out
  mp="$(jq -r '.manifest_path' "$f")"
  local gate_argv=()
  while IFS= read -r a; do gate_argv+=("$a"); done < <(jq -r '.post_fix_gate[]' "$mp")
  [ ${#gate_argv[@]} -gt 0 ] || die "manifest.post_fix_gate 为空(引擎载入应已挡,防御)"
  gate_out="$( cd "$(_repo_top)" && "${gate_argv[@]}" 2>&1 )" || rc=$?

  local gate_cmd
  gate_cmd="$(jq -r '.post_fix_gate|join(" ")' "$mp")"
  local gate_result
  gate_result="$(jq -nc --argjson rc "$rc" --arg cmd "$gate_cmd" \
    --arg out "$(printf '%s' "$gate_out" | head -c 400)" '[{gate:$cmd, rc:$rc, output:$out}]')"

  if [ "$rc" -eq 0 ]; then
    append_attempt "$f" "$name" "post_fix_gate" "pass" "$fp" "git-commit:$repair_sha"
    patch_last_attempt "$f" "[]" "[]" "$gate_result" "" "$gate_cmd"
    _invalidate_all_stages "$f" "$repair_sha"
    emit_event "$f" "classified" "$name" "P1" "$fp" "$(jq -r '.attempt_ledger[-1].attempt_id' "$f")"
    echo "POST-FIX-GATE-PASS:$name(架构闸绿,待重跑)"
    return 0
  fi

  local top revert_sha diag_argv=() findings_tmp
  top="$(_repo_top)"
  if ! git -C "$top" revert --no-edit "$repair_sha" >/dev/null; then
    _record_pause "$f" "$name" "post_fix_gate" "revert_failed" "$fp" "git-commit:$repair_sha" \
      "needs-context" "post-fix-gate 红后无法撤回 repair commit，停下交人" "[]" "[]" "" "$gate_cmd" "P1"
    echo "POST-FIX-GATE-REVERT-FAILED:$name"
    return 0
  fi
  revert_sha="$(git -C "$top" rev-parse HEAD)"
  append_attempt "$f" "$name" "post_fix_gate" "fail" "$fp" "git-revert:$revert_sha"
  patch_last_attempt "$f" "[]" "[]" "$gate_result" "" "$gate_cmd"
  edit "$f" --arg sc "$revert_sha" '.source_commit=$sc'
  while IFS= read -r a; do diag_argv+=("$a"); done < <(jq -r '.diagnose[]' "$mp")
  findings_tmp="$(mktemp)"
  ( cd "$top" && "${diag_argv[@]}" ) > "$findings_tmp" 2>/dev/null || true
  echo "FIX-REVERTED:$repair_sha commit=$revert_sha"
  echo "POST-FIX-GATE-FAIL:$name(架构闸红,重分级)"
  cmd_stage_fail --stage "$name" --findings "$findings_tmp"
  rm -f "$findings_tmp"
}

cmd_dispatch_direct() {
  local f="$1" name="$2" fp="$3" findings="$4" mode="$5" top commit_sha message
  local changed_json blocked_json artifact_ref="" action_kind
  top="$(_repo_top)"
  action_kind="$mode"
  if ! git -C "$top" diff --quiet HEAD; then
    _record_pause "$f" "$name" "preflight" "tracked_dirty" "$fp" "" \
      "needs-context" "功能分支已有未提交 tracked 改动，不能混入自动修复提交" "[]" "[]" "" "git diff --quiet HEAD" ""
    echo "DISPATCH-PAUSED:$name(pre-existing tracked diff)"
    return 0
  fi

  # P0:跑修复前先加载并冻结 protection hard-deny 快照;后续 baseline/candidate/path-gate 都用它,
  # 使「自愈修复改写 protection_source 本身」仍被判 P0 受保护路径违规,而非降级成「规则源不可读」。
  PROTECTION_FROZEN=0
  if ! _load_path_hard_deny "$f"; then
    _record_pause "$f" "$name" "preflight" "protection_source_unreadable" "$fp" "" \
      "needs-context" "protection_source 在自动修复前已不可用($PATH_GATE_ERROR)，保留现场交人" "[]" "[]" "" "" ""
    echo "DISPATCH-PAUSED:$name(protection source unreadable)"
    return 0
  fi
  PROTECTION_FROZEN=1

  _snapshot_baseline_untracked "$top" "$f"
  _run_direct_action "$f" "$mode" "$findings"
  _collect_candidate_paths "$top" "$f"
  changed_json="$(_json_changed_paths)"

  if ! _baseline_untracked_changed "$top"; then
    _record_pause "$f" "$name" "$action_kind" "baseline_untracked_changed" "$fp" "" \
      "needs-context" "自动修复改写了本轮前已存在的未跟踪文件，保留现场交人" \
      "$(_json_array "${BASELINE_CHANGED_PATHS[@]-}")" "[]" "$RF_WORKER_REF" "$ACTION_COMMAND" ""
    echo "DISPATCH-PAUSED:$name(baseline untracked changed)"
    return 0
  fi

  if [ "$ACTION_RC" -ne 0 ]; then
    _record_pause "$f" "$name" "$action_kind" "action_failed" "$fp" "" \
      "needs-context" "$mode 执行非零退出，保留现场交人" "$changed_json" "[]" "$RF_WORKER_REF" "$ACTION_COMMAND" ""
    echo "DISPATCH-PAUSED:$name($mode rc=$ACTION_RC)"
    return 0
  fi

  if [ ${#CHANGED_PATHS[@]} -eq 0 ]; then
    _record_pause "$f" "$name" "$action_kind" "no_change" "$fp" "" \
      "needs-context" "$mode 未产生任何可提交改动，不能伪装为已修复" "[]" "[]" "$RF_WORKER_REF" "$ACTION_COMMAND" ""
    echo "DISPATCH-PAUSED:$name(no change)"
    return 0
  fi

  if ! _path_gate "$f"; then
    BLOCKED_PATHS=("${CHANGED_PATHS[@]-}")
    if ! _write_path_gate_patch "$f" "$name" "$top" || ! _restore_rejected_candidates "$top"; then
      _record_pause "$f" "$name" "path_gate" "cleanup_failed" "$fp" "" \
        "needs-context" "protection_source 不可用且无法完整保存或复原本轮改动，保留现场交人" \
        "$changed_json" "$(_json_array "${BLOCKED_PATHS[@]-}")" "$RF_WORKER_REF" "$ACTION_COMMAND" ""
      echo "PATH-GATE-PAUSED:$name($PATH_GATE_ERROR)"
      return 0
    fi
    artifact_ref="$PATH_GATE_ARTIFACT"
    blocked_json="$(_json_array "${BLOCKED_PATHS[@]-}")"
    _record_pause "$f" "$name" "path_gate" "rejected" "$fp" "$artifact_ref" \
      "needs-context" "protection_source 无法作为路径闸真相源($PATH_GATE_ERROR)，已保存 patch 并停下交人" \
      "$changed_json" "$blocked_json" "$RF_WORKER_REF" "$ACTION_COMMAND" ""
    echo "PATH-GATE-REJECT:$name protection_source=[$PATH_GATE_ERROR]"
    return 0
  fi

  if [ ${#BLOCKED_PATHS[@]} -gt 0 ]; then
    if ! _write_path_gate_patch "$f" "$name" "$top" || ! _restore_rejected_candidates "$top"; then
      _record_pause "$f" "$name" "path_gate" "cleanup_failed" "$fp" "" \
        "needs-context" "路径闸拒绝后无法完整保存或复原本轮改动，保留现场交人" \
        "$changed_json" "$(_json_array "${BLOCKED_PATHS[@]-}")" "$RF_WORKER_REF" "$ACTION_COMMAND" "P0"
      echo "PATH-GATE-PAUSED:$name(cleanup failed)"
      return 0
    fi
    artifact_ref="$PATH_GATE_ARTIFACT"
    blocked_json="$(_json_array "${BLOCKED_PATHS[@]-}")"
    _record_pause "$f" "$name" "path_gate" "rejected" "$fp" "$artifact_ref" \
      "needs-redirection" "自动修复触及受保护路径或超出 editable_paths，已保存 patch、复原改动，停下请负责人拍板" \
      "$changed_json" "$blocked_json" "$RF_WORKER_REF" "$ACTION_COMMAND" "P0"
    echo "PATH-GATE-REJECT:$name 越界=[${BLOCKED_PATHS[*]}]"
    return 0
  fi

  if ! git -C "$top" add -- "${CHANGED_PATHS[@]-}"; then
    _record_pause "$f" "$name" "$action_kind" "add_failed" "$fp" "" \
      "needs-context" "自动修复通过路径闸后无法暂存改动，保留现场交人" "$changed_json" "[]" "$RF_WORKER_REF" "$ACTION_COMMAND" ""
    echo "DISPATCH-PAUSED:$name(git add failed)"
    return 0
  fi
  case "$mode" in
    fix) message="fix(release): $fp" ;;
    derive) message="chore(release): regenerate $fp" ;;
  esac
  if ! git -C "$top" commit -m "$message" >/dev/null; then
    _record_pause "$f" "$name" "$action_kind" "commit_failed" "$fp" "" \
      "needs-context" "自动修复通过路径闸后无法创建功能分支提交，保留现场交人" "$changed_json" "[]" "$RF_WORKER_REF" "$ACTION_COMMAND" ""
    echo "DISPATCH-PAUSED:$name(git commit failed)"
    return 0
  fi
  commit_sha="$(git -C "$top" rev-parse HEAD)"
  append_attempt "$f" "$name" "$action_kind" "applied" "$fp" "git-commit:$commit_sha"
  patch_last_attempt "$f" "$changed_json" "[]" "[]" "$RF_WORKER_REF" "$ACTION_COMMAND"
  emit_event "$f" "classified" "$name" "$( [ "$mode" = fix ] && echo P1 || echo P2 )" "$fp" "$(jq -r '.attempt_ledger[-1].attempt_id' "$f")"
  if [ "$mode" = "derive" ]; then
    _invalidate_all_stages "$f" "$commit_sha"
    echo "DERIVED-COMMITTED:$name commit=$commit_sha"
    return 0
  fi
  echo "FIX-COMMITTED:$name commit=$commit_sha"
  _post_fix_gate "$f" "$name" "$fp" "$commit_sha"
}

cmd_dispatch_p1() {
  cmd_dispatch_direct "$1" "$2" "$3" "$4" "fix"
}

cmd_dispatch_p2() {
  cmd_dispatch_direct "$1" "$2" "$3" "$4" "derive"
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

  local f cls
  f="$(need_state)"
  # 驱动器经 stage run 失败时,diagnose findings 已由 cmd_stage_fail 记进最近一条 attempt 的 artifact_refs;
  # 省略 --findings 即从 state 读回,驱动器无须复制引擎的内部 findings 路径。
  if [ -z "$findings" ]; then
    findings="$(jq -r '.attempt_ledger[-1].artifact_refs[0] // ""' "$f")"
  fi
  [ -n "$findings" ] || die "--findings 未给且 ledger 无可用 findings 引用"
  [ -f "$findings" ] || die "findings 文件不存在: $findings"
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
    P2) cmd_dispatch_p2 "$f" "$name" "$fp" "$findings" ;;
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
