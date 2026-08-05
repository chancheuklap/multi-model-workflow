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

SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# 状态落点从目标仓库的 .mmw.json 读。旧宿主这里读的是一个写死的常量，那份常量
# 属于已经不存在的阶段引擎；除此之外整个引擎不认识任何宿主。
# shellcheck source=../cli/lib/config.sh
. "$SCRIPT_DIR/../cli/lib/config.sh"
STATE_NAME="release-state.json"
# 同根因阈值 3 = 给两次修复机会:第 1 次失败(count=1)派修,修不好第 2 次失败(count=2)再派一次,
# 第 3 次观测(count=3)才熔断。2 意味着任何修复只有一次机会,正常迭代会被误熔断。
RF_MAX_SAME_FINGERPRINT="${RF_MAX_SAME_FINGERPRINT:-3}"

die() { echo "ERROR: $*" >&2; exit 1; }
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }

state_file() {
  local top sd
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "不在 git 仓库内"
  sd="$(mmw_path_field release)"
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

  # 预算按「修复轮次」记账,不按动作数:一轮正常修复(stage run+classify+fix+gate+全量重跑)
  # 会产生 ~9 条 attempt 账目,若按动作数熔断,第二个不同根因必然在修复前被误熔断。
  # attempt_ledger 保留全动作审计,熔断只看 fix_rounds。
  local fr max
  fr="$(jq -r '.budget.fix_rounds // 0' "$f")"
  max="$(jq -r '.budget.max_fix_rounds // 0' "$f")"
  if [ "$max" -gt 0 ] && [ "$fr" -ge "$max" ]; then
    edit "$f" --arg s "$stage" --argjson a "$fr" --argjson m "$max" \
      '.pause={at_stage:$s, kind:"surface", reason:"needs-redirection",
               question:("修复轮次预算越界(fix_rounds="+($a|tostring)+">=max="+($m|tostring)+"),引擎熔断交人")}'
    emit_event "$f" "paused" "$stage" "" "" ""
    echo "BUDGET-EXCEEDED:fix_rounds=$fr>=max=$max,熔断交人"
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
    # shellcheck disable=SC2053 # $g 是 release_protection 配置的 glob，不是字面字符串。
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
  local f="$1" mode="${2:-fix}" mp path matcher
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
    # P2 derive:引擎从真相源单向重生消费方派生物,derive.regenerate 自身已把输出约束在派生目录;
    # 派生物刻意不入 P1 的 editable_paths(否则 P1 fix_executor 能直改派生物,破坏「derive 唯一 writer」)。
    # 设计意图是 derive 只过 P0 保护路径 hard-deny,不施 P1 的 editable 白名单;否则 P2 无感自愈对真钥匙失效。
    if [ "$mode" = "derive" ]; then
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

  if ! _path_gate "$f" "$mode"; then
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
  edit "$f" '.budget.fix_rounds += 1'
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
  # sink 要按 ReleaseLoopEvent 合同 model_validate 后再落地,得先拿到本引擎正在用的那份
  # release_contracts.py。它恒是 release-flow.sh 的同目录兄弟($SCRIPT_DIR/release_contracts.py,
  # 见上方 validate-event),已安装扁平 cache 与源仓库 plugin/scripts/ 两种布局都成立。把这个权威
  # 路径交给 sink,两端加载同一份合同、不靠 sink 自己猜 plugin 根下的子路径(那条假设只在源仓库
  # 布局成立、已安装 cache 无 plugin/ 中间层,是 event 落地长期失败的根因)。
  printf '%s\n' "$ev" | MMW_PLUGIN_DIR="$SCRIPT_DIR" "${sink_argv[@]}" || echo "WARN: event_sink 落地失败: $event" >&2
}

cmd_init() {
  # 墙钟默认 4h:单产品一次真实 Windows 构建(Nuitka+electron-builder+NSIS)就要 20-60 分钟,
  # 预算必须容纳「一次失败构建 + 一轮修复 + 一次重跑」;1h 会在正常修复路径上误熔断。
  local manifest="" max_rounds=6 max_wall_clock=14400
  while [ $# -gt 0 ]; do
    case "$1" in
      --manifest) manifest="$2"; shift 2 ;;
      --max-rounds) max_rounds="$2"; shift 2 ;;
      --max-wall-clock) max_wall_clock="$2"; shift 2 ;;
      *) die "未知参数 $1" ;;
    esac
  done
  [ -n "$manifest" ] || die "--manifest 必填"
  [ -f "$manifest" ] || die "manifest 文件不存在: $manifest"
  case "$max_rounds" in ''|*[!0-9]*) die "--max-rounds 必须是非负整数" ;; esac
  case "$max_wall_clock" in ''|*[!0-9]*) die "--max-wall-clock 必须是非负整数(秒)" ;; esac

  local canon
  canon="$(uv run --quiet "$SCRIPT_DIR/release_contracts.py" validate-manifest "$manifest")" \
    || die "manifest 不合规(引擎载入 fail-loud，请人改 manifest)"

  local f top sd mp source_commit
  top="$(git rev-parse --show-toplevel)"
  source_commit="$(git -C "$top" rev-parse HEAD)"
  sd="$(mmw_path_field release)"
  f="$top/$sd/$STATE_NAME"
  [ -f "$f" ] && die "已有未收束 release loop;先 release close 或复用"
  mkdir -p "$top/$sd"
  mp="$(cd "$(dirname "$manifest")" && pwd)/$(basename "$manifest")"
  printf '%s' "$canon" | jq --arg mp "$mp" --arg sc "$source_commit" --argjson mr "$max_rounds" --argjson wall "$max_wall_clock" --arg ts "$(now)" \
    '{schema_version:"1", product:.product, manifest_path:$mp, source_commit:$sc,
      stages:[.stages[]|{name:.name, run:.run, status:"pending"}],
      current_stage:(.stages[0].name // null),
      round:1, max_rounds:$mr, fingerprint_ledger:[],
      budget:{attempts:0, fix_rounds:0, max_fix_rounds:$mr, started_at:$ts, max_wall_clock_seconds:$wall},
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
  # running 优先于 failed/pending:进程在「已标 running、未写终态」间中断后,该 stage 必须重跑。
  # 不认 running 会让 where 指向下一个 pending(stage run 二次防线 die)甚至误报 SUCCESS。
  local interrupted
  interrupted="$(jq -r '[.stages[]|select(.status=="running")][0].name // ""' "$f")"
  if [ -n "$interrupted" ]; then
    jq -r --arg c "$interrupted" '"RETRY-STAGE:"+$c+" RUN:"+([.stages[]|select(.name==$c)][0].run|join(" "))' "$f"
    return 0
  fi
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

# 远端是 Windows OpenSSH,DefaultShell 默认 cmd.exe:一切 PowerShell 语法必须显式经
# powershell -Command 执行,否则 New-Item/Test-Path 之类 cmdlet 在 cmd 下直接 not recognized。
_ssh_ps() {
  local remote_host="$1" ps_command="$2"
  ssh "$remote_host" "powershell -NoProfile -NonInteractive -Command \"$ps_command\""
}

# 生成远端构建 wrapper。忠实复刻本仓现役、已实测能出三个产品包的 build-pc-installers.sh 里的
# run-detached.ps1 成熟脱附模式,不再自造:扁平 $ErrorActionPreference='Continue' + `& powershell -File`
# 子进程 + `*>` 原生流重定向到日志 + Set-Content 写退出码。曾自造的 `*>&1 | Out-File`/try-catch/finally
# 是错的——脱附 schtasks 会话里 `| Out-File` 管道根本不落地(build-run.log 从不创建、diagnose 无据),
# 而 `*>` 原生重定向与 Set-Content 在脱附会话可靠(现役旧路径长年验证)。exitcode 由 Set-Content 单独
# 落地,不与日志重定向同一语句,故日志写没写都不影响退出码落地、轮询不空转。
_write_remote_wrapper() {
  local wrapper="$1"
  cat > "$wrapper" <<'PS1'
param([Parameter(Mandatory=$true)][string]$InputRoot)
$ErrorActionPreference = 'Continue'
$log = Join-Path $InputRoot 'build-run.log'
$rel = Join-Path $InputRoot 'release.ps1'
$ctx = Join-Path $InputRoot 'release-context.json'
# Source already extracted to $InputRoot/source by the harness ssh step. Run release.ps1 as a child
# process and redirect all its streams to the log with `*>` (native, reliable in a detached schtasks
# session; `*>&1 | Out-File` never lands there). $LASTEXITCODE is the child's real exit code.
& powershell -NoProfile -ExecutionPolicy Bypass -File $rel -ReleaseContextPath $ctx *> $log
$code = $LASTEXITCODE
# `*>` writes UTF-16LE on Windows PS 5.1; re-encode the log to UTF-8 with Set-Content (reliable when
# detached) so diagnose's ASCII failure-pattern matching is not broken by interleaved null bytes.
# Best-effort: a re-encode failure must not swallow the exit code.
try { $t = Get-Content -LiteralPath $log -Raw -ErrorAction Stop; if ($null -ne $t) { Set-Content -LiteralPath $log -Value $t -Encoding utf8 } } catch { }
Set-Content -Path (Join-Path $InputRoot 'build-run.exitcode') -Value $code -Encoding ascii
PS1
}

_run_remote_build() {
  local top="$1" source_commit="$2" stage_dir="$3"
  shift 3
  local script="" context="" remote_host remote_root remote_input remote_input_win archive commit_file remote_context wrapper cmd_file runner_cmd_win task_name product installer_glob
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

  # 引号合同:远端命令跨三种解析器(cmd.exe / PowerShell 语言 / powershell.exe native CLI),
  # 单引号只在 PowerShell 语言里是定界符,cmd 与 native CLI 都按字面收——路径/任务名一旦需要
  # 引号就没有统一合同。唯一稳定做法:远端根收紧为字符白名单(盘符开头,只允许字母数字与
  # ._-/\),空格/引号/美元符/反引号/分号等一律拒,所有 schtasks 参数裸传不加引号。
  if ! printf '%s' "$remote_root" | grep -Eq '^[A-Za-z]:[/\\][A-Za-z0-9._/\\-]*$'; then
    echo "ERROR: RELEASE_REMOTE_ROOT 必须是安全字符的 Windows 绝对路径(盘符开头,仅字母数字._-/\\): $remote_root" >&2
    return 64
  fi
  # 远端构建目录按 <短commit>-<product> 命名:
  # (1) 带 product:同一个 commit 出多个产品时(三产品共用一份源码树),若只按 commit 命名,后一个产品
  #     构建一开始的 Remove-Item + 重解压会把前一个产品已产出的安装包整片冲掉。product 取自已校验的
  #     context,收紧为安全字符白名单(字母数字._-)裸拼进路径。
  # (2) 只取 12 字符短 commit(与 task_name 同):Windows makensis 不开长路径,electron-builder 的 NSIS
  #     include 埋在极深的 pnpm 依赖哈希目录里,叠加 40 字符全 commit 目录名会让 !include 路径越过 MAX_PATH
  #     260 而「could not open file」失败。短 commit 省 28 字符把最深路径拉回 260 内。SOURCE_COMMIT.txt
  #     仍记全 commit 供溯源,只有目录名收短。
  product="$(jq -r '.product // empty' "$context" 2>/dev/null)"
  case "$product" in
    '' | *[!A-Za-z0-9._-]*)
      echo "ERROR: remote build context.product 缺失或含非法字符: '$product'" >&2
      return 64
      ;;
  esac
  remote_input="${remote_root%/}/${source_commit:0:12}-${product}"
  # 成品安装包在源码树里的落点(仓库相对 glob),供出包成功后收拢到统一交付目录;缺省则不收拢。
  installer_glob="$(jq -r '.build_target.installer_glob // empty' "$context" 2>/dev/null)"
  archive="$stage_dir/source.zip"
  commit_file="$stage_dir/SOURCE_COMMIT.txt"
  remote_context="$stage_dir/release-context.remote.json"
  wrapper="$stage_dir/run-release.ps1"
  git -C "$top" archive --format=zip --output "$archive" HEAD || return $?
  printf '%s\n' "$source_commit" > "$commit_file"
  jq --arg root "$remote_input/source" '.repo_root = $root' "$context" > "$remote_context" || return $?
  _write_remote_wrapper "$wrapper"

  _ssh_ps "$remote_host" "New-Item -ItemType Directory -Force -Path '$remote_input' | Out-Null" || return $?
  scp "$archive" "$remote_host:$remote_input/source.zip" || return $?
  scp "$commit_file" "$remote_host:$remote_input/SOURCE_COMMIT.txt" || return $?
  scp "$script" "$remote_host:$remote_input/release.ps1" || return $?
  scp "$remote_context" "$remote_host:$remote_input/release-context.json" || return $?
  scp "$wrapper" "$remote_host:$remote_input/run-release.ps1" || return $?

  # 忠实复刻现役 build-pc-installers.sh:schtasks /tr 指向一个 .cmd,由 .cmd 再调 run-release.ps1。
  # .cmd 单路径无空格无嵌套引号,规避 schtasks /tr 跨 cmd/PowerShell/native CLI 三解析器的引号地雷。
  # remote_input 已被上面字符白名单收紧(无空格),win 路径用反斜杠;-InputRoot 烘进 .cmd,不用 %~dp0
  # (末尾反斜杠+引号在 cmd→powershell 参数解析里会转义掉引号)。
  remote_input_win="$(printf '%s' "$remote_input" | tr '/' '\\')"
  cmd_file="$stage_dir/run-release.cmd"
  printf '@echo off\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%s\\run-release.ps1" -InputRoot "%s"\r\n' "$remote_input_win" "$remote_input_win" > "$cmd_file"
  scp "$cmd_file" "$remote_host:$remote_input/run-release.cmd" || return $?
  runner_cmd_win="${remote_input_win}\\run-release.cmd"

  # 源码解压:在 harness 独立 ssh 会话里同步做完(~60s、断 ssh 无碍),失败必 fail-loud 不进构建。
  # (现役旧路径是在脱附会话内的 build ps1 里解压,同样可靠;此处前置做只是让解压失败在 Mac 侧即时可见。)
  # 先删旧 source 避免跨轮残留半解压文件;解压后校验目录非空,空即判失败。
  if ! _ssh_ps "$remote_host" "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue '$remote_input/source'; Expand-Archive -Force '$remote_input/source.zip' '$remote_input/source'; if (-not (Test-Path '$remote_input/source') -or -not (Get-ChildItem -Force '$remote_input/source')) { exit 1 }"; then
    echo "ERROR: 远端源码解压失败或产出为空(构建任务前置准备): $remote_input/source" >&2
    return 71
  fi

  # 清掉上一轮遗留的构建产物并验证清干净:remote_input 只按 commit 命名,resume / 重跑同 commit
  # 时若不清,首次轮询就会读到过期 exitcode(如上轮的 "0")而把仍在跑或已失败的本轮误判成功——
  # 清除失败必须 fail-loud,不能静默继续。
  if ! _ssh_ps "$remote_host" "Remove-Item -Force -ErrorAction SilentlyContinue '$remote_input/build-run.log','$remote_input/build-run.exitcode'; if ((Test-Path '$remote_input/build-run.exitcode') -or (Test-Path '$remote_input/build-run.log')) { exit 1 }"; then
    echo "ERROR: 无法清除远端上一轮构建产物(旧 exitcode 会把本轮误判成功): $remote_input" >&2
    return 70
  fi

  task_name="mmw-release-${source_commit:0:12}-${RANDOM}"
  # schtasks 忠实复刻现役 build-pc-installers.sh 的成熟做法(已实测能出三产品包):
  # - /tr 指向上面上传的 .cmd(无空格裸传,charset 白名单保证),不直接串 powershell + 多参数;
  # - /sc weekly /d SUN 而非 /sc once:过期的 once 任务会被 Task Scheduler 判「不再运行」而在
  #   create→run 之间自动删除(旧路径注释记 build5 踩过此竞态);weekly 任务永不过期,/run 强制立即跑;
  # - 不加 /it /rl HIGHEST:构建机是已登录交互工作机,默认就在登录用户会话跑,旧路径长年长构建无需 /it。
  # 先删同名残留任务再建,避免上轮崩溃遗留条目。三条 schtasks 各一次 ssh:PC 默认 shell 是 PowerShell,
  # `&`/`;` 串联在 PS5.1 非法或变后台 job,没有顺序语义。
  ssh "$remote_host" "schtasks /delete /tn $task_name /f" >/dev/null 2>&1 || true
  ssh "$remote_host" "schtasks /create /tn $task_name /tr $runner_cmd_win /sc weekly /d SUN /st 23:59 /f" || return $?
  # 任务一旦 /create 成功,此后所有出口(/run 起不来、轮询超时、exitcode 损坏、正常结束)都必须
  # 结束可能仍在跑的构建 + 删计划任务:超时那类会有孤儿构建抢写下次同 commit 的 exitcode,其余虽只在
  # Task Scheduler 堆无害死条目也一并清。用子函数跑「/run + 轮询」拿 rc,函数尾部统一清理一次,不在每个
  # return 前重复 cleanup(避免上轮只补超时分支、漏掉 /run 失败与 exitcode 非法两个出口那类遗漏)。
  local rc=0
  _remote_run_and_poll "$remote_host" "$remote_input" "$task_name" "$stage_dir" || rc=$?
  # 清理经 _ssh_ps 的 PowerShell 分号顺序执行(/end 失败不挡 /delete):cmd 的 `&` 在
  # PowerShell 5.1 解析失败、PS6+ 变后台 job,跨默认 shell 没有顺序语义。任务名与创建端
  # 同样裸传(无空格无引号,PowerShell 原样传给 schtasks native)。清理失败不改变构建判定,
  # 但必须留痕(残留任务会在下轮同 commit 抢写产物)。
  if ! _ssh_ps "$remote_host" "schtasks /end /tn $task_name; schtasks /delete /tn $task_name /f" >/dev/null 2>&1; then
    echo "WARN: 远端计划任务清理失败(task=$task_name),残留条目需手动 schtasks /delete" >&2
  fi
  # 构建成功且钥匙声明了安装包落点:把安装包从 commit 哈希构建目录收拢到统一交付目录
  # $RELEASE_DELIVERY_ROOT/<product>/(缺省 D:\agentflow-releases),按产品分子目录、覆盖同名(每产品各占各的,
  # 不同产品不互删——覆盖问题在构建目录命名处已解;交付目录同产品新包盖旧包是预期)。排除 electron-builder
  # 的卸载器(*__*)与 .blockmap(-File + 扩展名 .exe + 非 __)。交付失败只 loud WARN 不改判定:包已在
  # 构建目录产出,交付是收拢便利,不该让一次拷贝故障把成功的构建标成失败——但必须留痕并指出源路径。
  if [ "$rc" -eq 0 ] && [ -n "$installer_glob" ]; then
    local delivery_root glob_win dest_win src_glob_win deliver_ps deliver_out
    delivery_root="${RELEASE_DELIVERY_ROOT:-D:\\agentflow-releases}"
    glob_win="$(printf '%s' "$installer_glob" | tr '/' '\\')"
    dest_win="${delivery_root%\\}\\${product}"
    src_glob_win="${remote_input_win}\\source\\${glob_win}"
    # 参数化 .ps1 写文件 scp 跑:inline 拼 PowerShell $变量经 bash 双引号/ssh 会被吃空,写成 -File 脚本
    # 用 -Dest/-SrcGlob 传参最稳(与 run-release.ps1 同一可靠模式)。纯 ASCII heredoc,无 BOM 也不会 GBK 误解析。
    deliver_ps="$stage_dir/deliver-installer.ps1"
    cat > "$deliver_ps" <<'DELIVER_PS1'
param([Parameter(Mandatory=$true)][string]$Dest, [Parameter(Mandatory=$true)][string]$SrcGlob)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
$items = @(Get-ChildItem -Path $SrcGlob -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -eq '.exe' -and $_.Name -notlike '*__*' })
if ($items.Count -eq 0) { Write-Error "no installer matched: $SrcGlob"; exit 3 }
foreach ($it in $items) { Copy-Item -LiteralPath $it.FullName -Destination $Dest -Force; Write-Output ("DELIVERED " + (Join-Path $Dest $it.Name)) }
DELIVER_PS1
    if scp "$deliver_ps" "$remote_host:$remote_input/deliver-installer.ps1" >/dev/null 2>&1 &&
      deliver_out="$(ssh "$remote_host" "powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File '$remote_input_win\\deliver-installer.ps1' -Dest '$dest_win' -SrcGlob '$src_glob_win'" 2>&1)"; then
      printf '%s\n' "$deliver_out" | grep '^DELIVERED ' >&2 || true
    else
      echo "WARN: 安装包交付到 $dest_win 失败(构建已成功,安装包仍在 $src_glob_win):$deliver_out" >&2
    fi
  fi
  return "$rc"
}

# 起远程计划任务并轮询到本轮 exitcode。构建退 0 返 0、退非零返其码;/run 起不来返 ssh 退出码;
# 轮询超时或 exitcode 非法返 70。拿到合法 exitcode(含构建失败)即设全局 REMOTE_LOG_REF 供调用方引日志,
# 并把 build-run.log 回传到 stage_dir(设 REMOTE_LOG_LOCAL):失败根因只存在于构建机日志,不回传
# 则 Mac 侧 diagnose 永远翻译不出 finding,自愈闭环断裂。
# 计划任务的 /end + /delete 清理由调用方 _run_remote_build 统一在尾部做,本函数只管 run+poll+判定。
_remote_run_and_poll() {
  local remote_host="$1" remote_input="$2" task_name="$3" stage_dir="$4"

  # 启动确认(复刻现役 build-pc-installers.sh):schtasks /run 偶发「返回 0 但任务没起来」,
  # 静默失败会让下面的 exitcode 轮询干等到墙钟超时。/run 后最多等 ~40s 看 build-run.log 或 exitcode
  # 出现(证明 wrapper 真跑起来了);没起来重试一次 /run,再不起 fail-loud,不进长轮询。
  local launched=0 attempt probe
  for attempt in 1 2; do
    ssh "$remote_host" "schtasks /run /tn $task_name" || return $?
    local _
    for _ in 1 2 3 4 5 6 7 8; do
      probe="$(_ssh_ps "$remote_host" "if ((Test-Path '$remote_input/build-run.log') -or (Test-Path '$remote_input/build-run.exitcode')) { 'Y' } else { 'N' }" 2>/dev/null || true)"
      probe="${probe%%[$'\r\n']*}"
      if [ "$probe" = "Y" ]; then launched=1; break; fi
      sleep 5
    done
    [ "$launched" = "1" ] && break
    echo "WARN: detached 构建任务未启动,重试 schtasks /run(第 ${attempt} 次)" >&2
  done
  if [ "$launched" != "1" ]; then
    echo "ERROR: detached 构建任务在 $remote_host 启动失败(build-run.log/exitcode 一直未出现,task=$task_name)" >&2
    return 70
  fi

  # 真实 Windows 构建耗时分钟级:轮询「本轮 exitcode 文件出现」而非日志出现,带间隔、有上限,
  # running 不当 fail。间隔/上限可经 env 调,测试用 fake ssh 首轮即有 exitcode、不进 sleep。
  local poll_seconds="${RELEASE_REMOTE_BUILD_POLL_SECONDS:-15}"
  local max_seconds="${RELEASE_REMOTE_BUILD_TIMEOUT_SECONDS:-7200}"
  local start_ts seen="" exit_code="" rc=0
  start_ts="$(date +%s)"
  while :; do
    seen="$(_ssh_ps "$remote_host" "if (Test-Path '$remote_input/build-run.exitcode') { 'Y' } else { 'N' }" 2>/dev/null || true)"
    seen="${seen%%[$'\r\n']*}"
    if [ "$seen" = "Y" ]; then
      exit_code="$(_ssh_ps "$remote_host" "Get-Content '$remote_input/build-run.exitcode'" 2>/dev/null || true)"
      exit_code="${exit_code%%[$'\r\n']*}"
      [ -n "$exit_code" ] && break
    fi
    # 超时按真实墙钟判(不累加 poll_seconds):即使 poll=0(测试用的快轮询)也不会因 waited 恒为 0 而永不超时。
    if [ "$(( $(date +%s) - start_ts ))" -ge "$max_seconds" ]; then
      echo "ERROR: remote build 超时 ${max_seconds}s 未产出 exitcode(task=$task_name)" >&2
      _fetch_remote_build_log "$remote_host" "$remote_input" "$stage_dir"
      return 70
    fi
    sleep "$poll_seconds"
  done
  _fetch_remote_build_log "$remote_host" "$remote_input" "$stage_dir"
  case "$exit_code" in
    ''|*[!0-9-]*) echo "ERROR: remote build exit-code 非法: $exit_code" >&2; return 70 ;;
  esac
  REMOTE_LOG_REF="pc:$remote_input/build-run.log"
  [ "$exit_code" = "0" ] || return "$exit_code"
}

# best-effort 回传远端构建日志到 stage_dir;成功设 REMOTE_LOG_LOCAL。回传失败不改变构建判定,
# 但 stderr 留痕(丢日志必须可见,不静默)。
_fetch_remote_build_log() {
  local remote_host="$1" remote_input="$2" stage_dir="$3"
  REMOTE_LOG_LOCAL=""
  if scp "$remote_host:$remote_input/build-run.log" "$stage_dir/build-run.log" 2>/dev/null; then
    REMOTE_LOG_LOCAL="$stage_dir/build-run.log"
  else
    echo "WARN: 无法回传远端构建日志 $remote_input/build-run.log" >&2
  fi
}

cmd_stage_run() {
  local requested="" f name top source_commit attempt_id stage_dir loop_dir log_file raw expanded rc=0
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
  # 跨 stage 产物交接目录:整轮固定(不随 attempt 序号变)。${RELEASE_STAGE_DIR} 是每-attempt 目录
  # (a0-verify_key / a1-assemble / a2-build ...),只存本 stage 自己的日志与临时输入;它无法在
  # stage 之间传产物——assemble 写进 a1、build 从 a2 读同名文件永远错开。真正的 stage 交接产物
  # (拼脚本器产出的 release.ps1 / release-context.json 供 build 消费)必须落这个整轮固定目录。
  loop_dir="$(dirname "$f")/release-artifacts/_loop"
  log_file="$stage_dir/$name.log"
  mkdir -p "$stage_dir" "$loop_dir"

  local argv=()
  while IFS= read -r raw; do
    expanded="${raw//\$\{RELEASE_STAGE_DIR\}/$stage_dir}"
    expanded="${expanded//\$\{RELEASE_LOOP_DIR\}/$loop_dir}"
    expanded="${expanded//\$\{RELEASE_PLUGIN_DIR\}/$SCRIPT_DIR}"
    argv+=("$expanded")
  done < <(jq -r --arg n "$name" '.stages[] | select(.name == $n) | .run[]' "$f")
  [ ${#argv[@]} -gt 0 ] || die "stage $name 的 argv 为空"

  edit "$f" --arg n "$name" '(.stages |= map(if .name == $n then .status = "running" else . end)) | .current_stage = $n'
  append_attempt "$f" "$name" "stage_run" "running" "" ""
  local remote_log_ref="" remote_log_local=""
  if [ "$name" = "build" ] && [ "${argv[0]}" = "mmw-release-remote-build" ]; then
    REMOTE_LOG_REF=""
    REMOTE_LOG_LOCAL=""
    if _run_remote_build "$top" "$source_commit" "$stage_dir" "${argv[@]:1}" >"$log_file" 2>&1; then
      remote_log_ref="${REMOTE_LOG_REF:-}"
      remote_log_local="${REMOTE_LOG_LOCAL:-}"
      rc=0
    else
      rc=$?
      remote_log_ref="${REMOTE_LOG_REF:-}"
      remote_log_local="${REMOTE_LOG_LOCAL:-}"
    fi
  elif (
    cd "$top"
    RELEASE_REPO_ROOT="$top" \
    RELEASE_STATE_FILE="$f" \
    RELEASE_STAGE_NAME="$name" \
    RELEASE_SOURCE_COMMIT="$source_commit" \
    RELEASE_STAGE_DIR="$stage_dir" \
    RELEASE_LOOP_DIR="$loop_dir" \
    "${argv[@]}"
  ) >"$log_file" 2>&1; then
    rc=0
  else
    rc=$?
  fi

  if [ "$rc" -eq 0 ]; then
    edit "$f" --arg n "$name" --arg log "file:$log_file" --arg remote "$remote_log_ref" --arg local_log "$remote_log_local" \
      '(.stages |= map(if .name == $n then .status = "done" else . end))
       | .current_stage = ([.stages[] | select(.status == "pending")][0].name // null)
       | .attempt_ledger[-1].outcome = "done"
       | .attempt_ledger[-1].log_refs = ([$log, (if $remote == "" then empty else $remote end), (if $local_log == "" then empty else "file:" + $local_log end)])'
    echo "STAGE-RUN-DONE $name"
    return 0
  fi

  edit "$f" --arg n "$name" --arg log "file:$log_file" --arg remote "$remote_log_ref" --arg local_log "$remote_log_local" \
    '(.stages |= map(if .name == $n then .status = "failed" else . end))
     | .current_stage = $n
     | .attempt_ledger[-1].outcome = "fail"
     | .attempt_ledger[-1].log_refs = ([$log, (if $remote == "" then empty else $remote end), (if $local_log == "" then empty else "file:" + $local_log end)])'
  local mp findings_file diag_arg
  mp="$(jq -r '.manifest_path' "$f")"
  findings_file="$stage_dir/$name.findings.json"
  local diagnose_argv=()
  while IFS= read -r diag_arg; do
    diagnose_argv+=("$diag_arg")
  done < <(jq -r '.diagnose[]' "$mp")
  [ ${#diagnose_argv[@]} -gt 0 ] || die "manifest.diagnose 为空"
  # 把失败现场交给 diagnose:RELEASE_BUILD_LOG 是回传的远端构建日志(仅远程 build 失败时有),
  # RELEASE_STAGE_LOG 是本 stage 的引擎侧日志。diagnose 据此把真实失败翻译成带 tier+fingerprint
  # 的 finding,而不是只看 Mac 本地状态、把远程失败降级成「无法分类交人」。
  (
    cd "$top"
    RELEASE_FAILED_STAGE="$name" \
    RELEASE_STAGE_LOG="$log_file" \
    RELEASE_BUILD_LOG="$remote_log_local" \
    "${diagnose_argv[@]}"
  ) > "$findings_file" 2>&1 || true
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
  local f earliest
  f="$(need_state)"
  jq -e --arg n "$name" 'any(.stages[]; .name==$n)' "$f" >/dev/null || die "无此 stage: $name"
  # stage run 是唯一执行器;stage done 只是人工确认位,只能确认最早未完成 stage,否则可把从未
  # 执行的 build 直接标 done、让 exit-check 在没有安装包的情况下报 DONE。
  earliest="$(jq -r '[.stages[] | select(.status == "pending" or .status == "failed" or .status == "running")][0].name // ""' "$f")"
  [ -n "$earliest" ] || die "没有未完成 stage 可确认"
  [ "$name" = "$earliest" ] || die "只能确认最早未完成 stage: $earliest(拒绝跳步标 done)"
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
               question:("stage "+$n+" P0 硬约束失败("+$fp+"),触发人工审批关卡,停")}'
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

  # 瞬态失败(fingerprint 前缀 transient:,如构建机网络抖动)没有可修的代码——正确处置是直接
  # 重跑该 stage,不派 fix executor。同指纹熔断(RF_MAX_SAME_FINGERPRINT)兜底防无限重试。
  local non_transient
  non_transient="$(printf '%s' "$cls" | jq -r '[.failing[] | select((.root_cause_fingerprint // "") | startswith("transient:") | not)] | length')"
  if [ "$non_transient" -eq 0 ]; then
    append_attempt "$f" "$name" "transient_retry" "retry" "$fp" "$findings"
    edit "$f" --arg n "$name" \
      '(.stages |= map(if .name==$n then .status="pending" else . end))
       | .current_stage=$n'
    emit_event "$f" "classified" "$name" "$tier" "$fp" "$(jq -r '.attempt_ledger[-1].attempt_id' "$f")"
    echo "TRANSIENT-RETRY:$name($fp,直接重跑不派修)"
    return 0
  fi

  case "$tier" in
    P0)
      append_attempt "$f" "$name" "dispatch" "fail" "$fp" "$findings"
      local aref
      aref="$(jq -r '.attempt_ledger[-1].attempt_id' "$f")"
      edit "$f" --arg n "$name" --arg fp "$fp" \
        '(.stages |= map(if .name==$n then .status="failed" else . end))
         | .current_stage=$n
         | .pause={at_stage:$n, kind:"surface", reason:"needs-redirection",
                  question:("dispatch "+$n+" P0 硬约束("+$fp+"),触发人工审批关卡,停")}'
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
  local top sd f main product commit
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "NO-GIT"; return 0; }
  sd="$(mmw_path_field release)"
  f="$top/$sd/$STATE_NAME"
  # 收束时留一份交付记录再删状态。一次改动影响多个产品时,后一个产品的自愈修复会
  # 产生新提交推进 HEAD,早前那个产品的包就已经不是最终代码了——把几个包混着发出去,
  # 客户装到的是两份不同的东西。这几份记录是发出去之前唯一能发现这件事的地方。
  # 只记 product 与 commit 两个事实,判断「要不要重出」是技能的事,不在引擎里。
  #
  # 活状态跟着当前树走,交付记录落主仓库根:它要比对的是几次出包之间的 commit,
  # 跨任务、跨会话才成立,而任务 worktree 收尾就删,记录跟着一起没。两边都在
  # .gitignore 里,不进 git——出包是这台机器上的事实,不是仓库历史的一部分。
  if [ -f "$f" ]; then
    product="$(jq -r '.product // empty' "$f" 2>/dev/null || true)"
    commit="$(jq -r '.source_commit // empty' "$f" 2>/dev/null || true)"
    if [ -n "$product" ] && [ -n "$commit" ]; then
      main="$(mmw_main_root)"
      mkdir -p "$main/$sd/delivered"
      jq -n --arg p "$product" --arg c "$commit" --arg at "$(now)" \
        '{product:$p, source_commit:$c, closed_at:$at}' > "$main/$sd/delivered/$product.json"
    fi
    rm -f "$f"
  fi
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
  # log_refs 必须进回执:PAUSED:needs-context 的自主处置政策(drive-loop.md)第一步就是从
  # 回执拿日志 locator(file:/pc:),漏印 = 驱动 Agent 只能翻裸 state 文件猜路径。
  jq -r '.attempt_ledger[] | "- ["+.action_kind+"] stage="+.stage+" outcome="+.outcome+(if .root_cause_fingerprint then " fp="+.root_cause_fingerprint else "" end)+(if (.artifact_refs|length)>0 then " findings="+(.artifact_refs|join(",")) else "" end)+(if (.log_refs//[]|length)>0 then " logs="+(.log_refs|join(",")) else "" end)' "$f"
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
  *) die "用法: mmw release init|where|stage|round|surface|resume|close|exit-check|receipt|dispatch ..." ;;
esac
