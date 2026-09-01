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
STATE_NAME="release-state.json"

# 状态落点。名字固定,目标仓库把 .release/ 写进 .gitignore 就够了——出包是这台机器上的
# 事实,不是仓库历史。可配置会让这两件事对不上:改了名字而 .gitignore 没跟着改,状态就进了 git。
RELEASE_SUBDIR=".release"

# Git 共享根。在 linked worktree 里跑时指回创建这些 worktree 的主检出；交付记录落那里，
# 因为它要比对跨任务、跨会话的几次出包，而任务 worktree 收尾就删。
main_root() {
  local common
  common="$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || return 1
  dirname "$common"
}
# 同根因阈值 3 = 给两次修复机会:第 1 次失败(count=1)派修,修不好第 2 次失败(count=2)再派一次,
# 第 3 次观测(count=3)才熔断。2 意味着任何修复只有一次机会,正常迭代会被误熔断。
RF_MAX_SAME_FINGERPRINT="${RF_MAX_SAME_FINGERPRINT:-3}"

die() { echo "ERROR: $*" >&2; exit 1; }
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }

usage_release() {
  cat >&2 <<'EOF'
release-flow.sh init --manifest <path> [--max-rounds N]
release-flow.sh where
release-flow.sh stage run|done|fail
release-flow.sh round next
release-flow.sh surface|resume|close|exit-check
release-flow.sh receipt
release-flow.sh dispatch --stage <n> --findings <path>

Examples:
  bash <absolute path to this script> where
  bash <absolute path to this script> init --manifest path/to/product.release-adapter.json
  bash <absolute path to this script> receipt
EOF
  return 2
}

state_file() {
  local top
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "not inside a git repository"
  echo "$top/$RELEASE_SUBDIR/$STATE_NAME"
}

need_state() {
  local f
  f="$(state_file)"
  [ -f "$f" ] || die "no release-state (run release init first)"
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
    echo "ERROR: refusing to write empty/invalid JSON to $f; original kept" >&2
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

_repo_top() { git rev-parse --show-toplevel 2>/dev/null || die "not inside a git repository"; }

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
                 question:("the same root cause ("+$fp+") reached the threshold of "+($n|tostring)+" observations without converging; the engine stops and hands it to a human")}'
      emit_event "$f" "paused" "$stage" "" "$fp" ""
      echo "CIRCUIT-BREAK:fingerprint=$fp x$cnt(>=$RF_MAX_SAME_FINGERPRINT), same cause keeps coming back; hand to a person"
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
               question:("fix round budget exceeded (fix_rounds="+($a|tostring)+">=max="+($m|tostring)+"); the engine stops and hands it to a human")}'
    emit_event "$f" "paused" "$stage" "" "" ""
    echo "BUDGET-EXCEEDED:fix_rounds=$fr>=max=$max; hand to a person"
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
                 question:("wall clock budget exceeded (elapsed="+($e|tostring)+"s>=max="+($w|tostring)+"s); the engine stops and hands it to a human")}'
      emit_event "$f" "paused" "$stage" "" "" ""
      echo "BUDGET-EXCEEDED:wallclock=${elapsed}s>=${wallmax}s; hand to a person"
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

# 不管产品声明了什么，自动修复永远不许碰这几类路径。产品的 protection_source 加在它之上，
# 不是取代它——一把新钥匙什么都还没写的时候，闸门不该是整个开着的。
# 匹配用 bash 的 [[ == ]]，其中 * 也跨 /，所以 *foo 等于「任意深度下的 foo」。
_SKILL_HARD_DENY=(
  '.env' '.env.*' '*/.env' '*/.env.*'
  '*.pem' '*.key' '*.p12' '*.pfx' '*id_rsa' '*id_ed25519' '*id_ecdsa'
  '.git' '.git/*'
  '*.lock' '*package-lock.json' '*pnpm-lock.yaml' '*yarn.lock'
  '*.release-adapter.json'
)

_load_path_hard_deny() {
  local f="$1" top mp source_rel source_file matchers path
  # P0:本轮 dispatch 若已在跑修复前冻结过 hard-deny 快照,后续一律用冻结值,不再从可能被修复
  # 改坏的 protection_source 重读——否则「改写 release_protection.json 本身」会让规则源读不出、
  # 把 P0 受保护路径违规降级成 needs-context「规则源不可读」,等于破坏被保护物就能关掉它自己的闸。
  if [ "${PROTECTION_FROZEN:-0}" = "1" ]; then
    [ ${#PROTECTION_MATCHERS[@]} -gt 0 ] && return 0
    PATH_GATE_ERROR="the frozen protection_source snapshot is empty"
    return 1
  fi
  top="$(_repo_top)"
  mp="$(jq -r '.manifest_path' "$f")"
  PROTECTION_MATCHERS=("${_SKILL_HARD_DENY[@]}")
  # 钥匙没有自己的保护规则，就只有技能这份底线——这不是缺陷，是一把还没长出自愈装备的钥匙。
  if [ "$(jq -r 'has("protection_source") and (.protection_source != null)' "$mp")" != "true" ]; then
    return 0
  fi
  source_rel="$(jq -er '.protection_source' "$mp" 2>/dev/null)" || {
    PATH_GATE_ERROR="manifest.protection_source cannot be read"
    return 1
  }
  case "$source_rel" in
    /*|..|../*|*/../*) PATH_GATE_ERROR="protection_source must be a path relative to the repo root: $source_rel"; return 1 ;;
  esac
  source_file="$top/$source_rel"
  [ -f "$source_file" ] || { PATH_GATE_ERROR="protection_source does not exist: $source_rel"; return 1; }
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
    PATH_GATE_ERROR="protection_source is not valid: $source_rel"
    return 1
  fi
  while IFS= read -r path; do
    [ -n "$path" ] && PROTECTION_MATCHERS+=("$path")
  done < "$matchers"
  # 规则源自己也不许被自动修复改：改得掉它，就等于能关掉自己头上的闸。
  PROTECTION_MATCHERS+=("$source_rel")
  rm -f "$matchers"
  [ ${#PROTECTION_MATCHERS[@]} -gt 0 ] || {
    PATH_GATE_ERROR="protection_source declares no path_hard_deny matcher"
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
    # P2 derive:引擎从唯一事实来源单向重生消费方派生物,derive.regenerate 自身已把输出约束在派生目录;
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

# 钥匙里的 argv 可以指向技能自己带的脚本，路径写 ${RELEASE_PLUGIN_DIR}——技能装在哪由宿主决定，
# 钥匙不该知道。${RELEASE_STAGE_DIR}/${RELEASE_LOOP_DIR} 只在 stage 里有意义，其余场合传空。
_expand_argv_token() {
  local raw="$1" stage_dir="${2:-}" loop_dir="${3:-}" out
  # 每-attempt 目录与整轮目录只在 stage 里存在。diagnose 之外的字段（fix_executor / post_fix_gate /
  # event_sink）没有它们，此时用了就直接停——展开成空字符串会变成一条指向根目录的路径，
  # 那种失败要到跑起来才看得见，而且看不出是这里丢的。
  case "$raw" in
    *'${RELEASE_STAGE_DIR}'*) [ -n "$stage_dir" ] || die "\${RELEASE_STAGE_DIR} has no meaning in this field: $raw" ;;
  esac
  case "$raw" in
    *'${RELEASE_LOOP_DIR}'*) [ -n "$loop_dir" ] || die "\${RELEASE_LOOP_DIR} has no meaning in this field: $raw" ;;
  esac
  out="${raw//\$\{RELEASE_STAGE_DIR\}/$stage_dir}"
  out="${out//\$\{RELEASE_LOOP_DIR\}/$loop_dir}"
  out="${out//\$\{RELEASE_PLUGIN_DIR\}/$SCRIPT_DIR}"
  printf '%s' "$out"
}

# 钥匙没声明 diagnose 时用技能自己的诊断器。这一段在每把钥匙里逐字相同，只有 --adapter
# 后面的路径不同——而那条路径引擎手里就有。抄的东西一旦有四份，其中一份迟早抄错。
_diagnose_argv_source() {
  local mp="$1"
  if [ "$(jq -r '(.diagnose // []) | length' "$mp")" -gt 0 ]; then
    jq -r '.diagnose[]' "$mp"
    return 0
  fi
  printf '%s\n' uv run --with 'pydantic>=2' python \
    '${RELEASE_PLUGIN_DIR}/diagnose_core.py' --adapter "$mp"
}

_run_direct_action() {
  local f="$1" mode="$2" findings="$3" top mp key arg ref_file
  top="$(_repo_top)"
  mp="$(jq -r '.manifest_path' "$f")"
  case "$mode" in
    fix) key="fix_executor" ;;
    derive) key="derive" ;;
    *) die "unknown direct action: $mode" ;;
  esac
  ACTION_ARGV=()
  while IFS= read -r arg; do ACTION_ARGV+=("$(_expand_argv_token "$arg")"); done \
    < <(jq -r --arg key "$key" '(.[$key] // [])[]' "$mp")
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
  # 没有这一关，跟「跑了并通过」在回执里必须分得开。
  if [ "$(jq -r '(.post_fix_gate // []) | length' "$mp")" -eq 0 ]; then
    append_attempt "$f" "$name" "post_fix_gate" "skipped" "$fp" "git-commit:$repair_sha"
    echo "POST-FIX-GATE-SKIPPED:$name (the key declares no post_fix_gate)"
    return 0
  fi
  local gate_argv=()
  while IFS= read -r a; do gate_argv+=("$(_expand_argv_token "$a")"); done < <(jq -r '.post_fix_gate[]' "$mp")
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
    echo "POST-FIX-GATE-PASS:$name (gate green, rerun the stage)"
    return 0
  fi

  local top revert_sha diag_argv=() findings_tmp
  top="$(_repo_top)"
  if ! git -C "$top" revert --no-edit "$repair_sha" >/dev/null; then
    _record_pause "$f" "$name" "post_fix_gate" "revert_failed" "$fp" "git-commit:$repair_sha" \
      "needs-context" "the post-fix gate went red and the repair commit could not be rolled back; stopping for a human" "[]" "[]" "" "$gate_cmd" "P1"
    echo "POST-FIX-GATE-REVERT-FAILED:$name"
    return 0
  fi
  revert_sha="$(git -C "$top" rev-parse HEAD)"
  append_attempt "$f" "$name" "post_fix_gate" "fail" "$fp" "git-revert:$revert_sha"
  patch_last_attempt "$f" "[]" "[]" "$gate_result" "" "$gate_cmd"
  edit "$f" --arg sc "$revert_sha" '.source_commit=$sc'
  while IFS= read -r a; do diag_argv+=("$(_expand_argv_token "$a")"); done < <(_diagnose_argv_source "$mp")
  findings_tmp="$(mktemp)"
  ( cd "$top" && "${diag_argv[@]}" ) > "$findings_tmp" 2>/dev/null || true
  echo "FIX-REVERTED:$repair_sha commit=$revert_sha"
  echo "POST-FIX-GATE-FAIL:$name (gate red, classify again)"
  cmd_stage_fail --stage "$name" --findings "$findings_tmp"
  rm -f "$findings_tmp"
}

cmd_dispatch_direct() {
  local f="$1" name="$2" fp="$3" findings="$4" mode="$5" top mp commit_sha message
  local changed_json blocked_json artifact_ref="" action_kind
  top="$(_repo_top)"
  mp="$(jq -r '.manifest_path' "$f")"
  action_kind="$mode"
  if ! git -C "$top" diff --quiet HEAD; then
    _record_pause "$f" "$name" "preflight" "tracked_dirty" "$fp" "" \
      "needs-context" "the feature branch already holds uncommitted tracked changes; they must not be mixed into an automatic fix commit" "[]" "[]" "" "git diff --quiet HEAD" ""
    echo "DISPATCH-PAUSED:$name(pre-existing tracked diff)"
    return 0
  fi

  # P0:跑修复前先加载并冻结 protection hard-deny 快照;后续 baseline/candidate/path-gate 都用它,
  # 使「自愈修复改写 protection_source 本身」仍被判 P0 受保护路径违规,而非降级成「规则源不可读」。
  PROTECTION_FROZEN=0
  if ! _load_path_hard_deny "$f"; then
    _record_pause "$f" "$name" "preflight" "protection_source_unreadable" "$fp" "" \
      "needs-context" "protection_source was already unusable before the automatic fix ($PATH_GATE_ERROR); keeping the state for a human" "[]" "[]" "" "" ""
    echo "DISPATCH-PAUSED:$name(protection source unreadable)"
    return 0
  fi
  PROTECTION_FROZEN=1

  # 钥匙没配这一件自愈装备，就没有这一步。说成引擎坏了，下一个人会去查引擎。
  if [ "$(jq -r --arg k "$( [ "$mode" = fix ] && echo fix_executor || echo derive )" \
        '(.[$k] // []) | length' "$mp")" -eq 0 ]; then
    _record_pause "$f" "$name" "preflight" "no_${mode}_executor" "$fp" "" \
      "needs-context" "the key declares no $( [ "$mode" = fix ] && echo fix_executor || echo derive ); this class of failure has no automatic path, hand it to a person" \
      "[]" "[]" "" "" ""
    echo "DISPATCH-PAUSED:$name(no $mode executor in the key)"
    return 0
  fi

  _snapshot_baseline_untracked "$top" "$f"
  _run_direct_action "$f" "$mode" "$findings"
  _collect_candidate_paths "$top" "$f"
  changed_json="$(_json_changed_paths)"

  if ! _baseline_untracked_changed "$top"; then
    _record_pause "$f" "$name" "$action_kind" "baseline_untracked_changed" "$fp" "" \
      "needs-context" "the automatic fix rewrote an untracked file that existed before this round; keeping the state for a human" \
      "$(_json_array "${BASELINE_CHANGED_PATHS[@]-}")" "[]" "$RF_WORKER_REF" "$ACTION_COMMAND" ""
    echo "DISPATCH-PAUSED:$name(baseline untracked changed)"
    return 0
  fi

  if [ "$ACTION_RC" -ne 0 ]; then
    _record_pause "$f" "$name" "$action_kind" "action_failed" "$fp" "" \
      "needs-context" "$mode exited non-zero; keeping the state for a human" "$changed_json" "[]" "$RF_WORKER_REF" "$ACTION_COMMAND" ""
    echo "DISPATCH-PAUSED:$name($mode rc=$ACTION_RC)"
    return 0
  fi

  if [ ${#CHANGED_PATHS[@]} -eq 0 ]; then
    _record_pause "$f" "$name" "$action_kind" "no_change" "$fp" "" \
      "needs-context" "$mode produced no committable change; this must not pass as fixed" "[]" "[]" "$RF_WORKER_REF" "$ACTION_COMMAND" ""
    echo "DISPATCH-PAUSED:$name(no change)"
    return 0
  fi

  if ! _path_gate "$f" "$mode"; then
    BLOCKED_PATHS=("${CHANGED_PATHS[@]-}")
    if ! _write_path_gate_patch "$f" "$name" "$top" || ! _restore_rejected_candidates "$top"; then
      _record_pause "$f" "$name" "path_gate" "cleanup_failed" "$fp" "" \
        "needs-context" "protection_source is unusable and this round's changes could not be fully saved or restored; keeping the state for a human" \
        "$changed_json" "$(_json_array "${BLOCKED_PATHS[@]-}")" "$RF_WORKER_REF" "$ACTION_COMMAND" ""
      echo "PATH-GATE-PAUSED:$name($PATH_GATE_ERROR)"
      return 0
    fi
    artifact_ref="$PATH_GATE_ARTIFACT"
    blocked_json="$(_json_array "${BLOCKED_PATHS[@]-}")"
    _record_pause "$f" "$name" "path_gate" "rejected" "$fp" "$artifact_ref" \
      "needs-context" "protection_source cannot serve as the path gate's single source of truth ($PATH_GATE_ERROR); the patch is saved and this stops for a human" \
      "$changed_json" "$blocked_json" "$RF_WORKER_REF" "$ACTION_COMMAND" ""
    echo "PATH-GATE-REJECT:$name protection_source=[$PATH_GATE_ERROR]"
    return 0
  fi

  if [ ${#BLOCKED_PATHS[@]} -gt 0 ]; then
    if ! _write_path_gate_patch "$f" "$name" "$top" || ! _restore_rejected_candidates "$top"; then
      _record_pause "$f" "$name" "path_gate" "cleanup_failed" "$fp" "" \
        "needs-context" "the path gate rejected the changes and they could not be fully saved or restored; keeping the state for a human" \
        "$changed_json" "$(_json_array "${BLOCKED_PATHS[@]-}")" "$RF_WORKER_REF" "$ACTION_COMMAND" "P0"
      echo "PATH-GATE-PAUSED:$name(cleanup failed)"
      return 0
    fi
    artifact_ref="$PATH_GATE_ARTIFACT"
    blocked_json="$(_json_array "${BLOCKED_PATHS[@]-}")"
    _record_pause "$f" "$name" "path_gate" "rejected" "$fp" "$artifact_ref" \
      "needs-redirection" "the automatic fix touched a protected path or reached outside editable_paths; the patch is saved, the changes are restored, and this stops for the owner to decide" \
      "$changed_json" "$blocked_json" "$RF_WORKER_REF" "$ACTION_COMMAND" "P0"
    echo "PATH-GATE-REJECT:$name out-of-bounds=[${BLOCKED_PATHS[*]}]"
    return 0
  fi

  if ! git -C "$top" add -- "${CHANGED_PATHS[@]-}"; then
    _record_pause "$f" "$name" "$action_kind" "add_failed" "$fp" "" \
      "needs-context" "the automatic fix passed the path gate but the changes could not be staged; keeping the state for a human" "$changed_json" "[]" "$RF_WORKER_REF" "$ACTION_COMMAND" ""
    echo "DISPATCH-PAUSED:$name(git add failed)"
    return 0
  fi
  case "$mode" in
    fix) message="fix(release): $fp" ;;
    derive) message="chore(release): regenerate $fp" ;;
  esac
  if ! git -C "$top" commit -m "$message" >/dev/null; then
    _record_pause "$f" "$name" "$action_kind" "commit_failed" "$fp" "" \
      "needs-context" "the automatic fix passed the path gate but the feature branch commit could not be created; keeping the state for a human" "$changed_json" "[]" "$RF_WORKER_REF" "$ACTION_COMMAND" ""
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
  local f="$1" event="$2" stage="$3" tier="$4" fp="$5" aref="$6" mp
  local mp
  mp="$(jq -r '.manifest_path' "$f")"
  [ -f "$mp" ] || { echo "WARN: the manifest is gone ($mp), not recording event: $event" >&2; return 0; }

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
    || { echo "ERROR: the engine produced an invalid ReleaseLoopEvent: $ev" >&2; return 0; }

  # 没接日志系统的产品，事件到此为止：验过合同就够了，不凭空造一个落地点。
  [ "$(jq -r '(.event_sink // []) | length' "$mp")" -gt 0 ] || return 0
  local sink_argv=()
  while IFS= read -r arg; do
    sink_argv+=("$(_expand_argv_token "$arg")")
  done < <(jq -r '.event_sink[]' "$mp")
  # sink 要按 ReleaseLoopEvent 合同 model_validate 后再落地,得先拿到本引擎正在用的那份
  # release_contracts.py。它恒是 release-flow.sh 的同目录兄弟($SCRIPT_DIR/release_contracts.py,
  # 见上方 validate-event),已安装扁平 cache 与源仓库 plugin/scripts/ 两种布局都成立。把这个权威
  # 路径交给 sink,两端加载同一份合同、不靠 sink 自己猜 plugin 根下的子路径(那条假设只在源仓库
  # 布局成立、已安装 cache 无 plugin/ 中间层,是 event 落地长期失败的根因)。
  printf '%s\n' "$ev" | MMW_PLUGIN_DIR="$SCRIPT_DIR" "${sink_argv[@]}" || echo "WARN: event_sink did not record: $event" >&2
}

# 生成脚本这件事的输入不止钥匙，还有技能自己。技能改了而产品仓库 HEAD 没动时，引擎原本
# 看不见——于是 build 拿着上一次装配出来的脚本去构建机跑，日志里每一步都对，只是跑的不是
# 你刚改的那一份。指纹存在状态里，build 前对一次。
_skill_fingerprint() {
  find "$SCRIPT_DIR" -type f \( -name '*.py' -o -name '*.tmpl' -o -name '*.sh' \) \
    ! -path '*/__pycache__/*' -print0 | sort -z | xargs -0 shasum | shasum | cut -d' ' -f1
}

# 标准流水线：验钥匙 → 装配 → 远端构建。每把钥匙的这三段曾经逐字相同，只有钥匙路径不同，
# 于是它是抄的——而 v2 钥匙指着 v1 钥匙那个 bug 正是这么抄出来的，日志里每一步还都是绿的。
# 钥匙自己的 stages 排在这一份**前面**：产品在出发前要跑的检查（版本号没重、仓库现状跟钥匙
# 还对得上）是它自己的事，而后面这三段每把钥匙都一样。
# 这三个名字是保留字，钥匙用不了（合同挡在 init 之前）。曾经允许钥匙用同名接管整条，
# 于是抄来的一句 assemble 就把引擎的验钥匙整段关掉了，而日志每一步都是绿的。
_standard_stages() {
  jq -nc --arg mp "$1" '[
    {name:"verify_key", run:["uv","run","--with","pydantic>=2","python",
      "${RELEASE_PLUGIN_DIR}/verify_key.py","--adapter",$mp,"--repo-root","."]},
    {name:"assemble", run:["uv","run","--with","pydantic>=2","python",
      "${RELEASE_PLUGIN_DIR}/release_script_assembler.py","assemble",
      "--adapter",$mp,"--repo-root",".",
      "--output","${RELEASE_LOOP_DIR}/release.ps1",
      "--context-output","${RELEASE_LOOP_DIR}/release-context.json"]},
    {name:"build", run:["mmw-release-remote-build",
      "--script","${RELEASE_LOOP_DIR}/release.ps1",
      "--context","${RELEASE_LOOP_DIR}/release-context.json"]}
  ]'
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
      -h|--help)
        if usage_release; then :; fi
        exit 0
        ;;
      *) die "unknown argument $1" ;;
    esac
  done
  [ -n "$manifest" ] || die "--manifest is required"
  [ -f "$manifest" ] || die "no such manifest file: $manifest"
  case "$max_rounds" in ''|*[!0-9]*) die "--max-rounds must be a non-negative integer" ;; esac
  case "$max_wall_clock" in ''|*[!0-9]*) die "--max-wall-clock must be a non-negative integer (seconds)" ;; esac

  local canon
  canon="$(uv run --quiet "$SCRIPT_DIR/release_contracts.py" validate-manifest "$manifest")" \
    || die "the manifest does not satisfy the contract; a person has to fix the key"

  local f top mp source_commit
  top="$(git rev-parse --show-toplevel)"
  source_commit="$(git -C "$top" rev-parse HEAD)"
  f="$top/$RELEASE_SUBDIR/$STATE_NAME"
  [ -f "$f" ] && die "a release loop is already open; close it or continue it"
  # 上一轮的 attempt 目录不能留:attempt 号从 a0 重新数,旧目录跟本轮同名对撞,于是
  # 「本轮的 a4-verify_key」读到的是上一个产品的结果,而没有任何一步报错。
  rm -rf "$top/$RELEASE_SUBDIR/release-artifacts"
  mkdir -p "$top/$RELEASE_SUBDIR"
  mp="$(cd "$(dirname "$manifest")" && pwd)/$(basename "$manifest")"
  local standard
  standard="$(_standard_stages "$mp")"
  printf '%s' "$canon" | jq --arg mp "$mp" --arg sc "$source_commit" --argjson mr "$max_rounds" --argjson wall "$max_wall_clock" --arg ts "$(now)" --argjson std "$standard" \
    '{schema_version:"1", product:.product, manifest_path:$mp, source_commit:$sc,
      stages:[(.stages + $std)[] | {name:.name, run:.run, status:"pending"}],
      current_stage:(.stages[0].name // $std[0].name // null),
      round:1, max_rounds:$mr, fingerprint_ledger:[],
      budget:{attempts:0, fix_rounds:0, max_fix_rounds:$mr, started_at:$ts, max_wall_clock_seconds:$wall},
      attempt_ledger:[], pause:null}' | write "$f"
  echo "INIT product=$(printf '%s' "$canon" | jq -r .product) stages=$(jq -r '.stages|length' "$f") max_rounds=$max_rounds"
}

cmd_where() {
  local f
  f="$(need_state)"
  jq -e . "$f" >/dev/null 2>&1 || { echo "CORRUPT:release-state is empty or not valid JSON"; return 0; }
  if [ "$(jq -r '.pause // "null"' "$f")" != "null" ]; then
    echo "PAUSED:$(jq -r '.pause.reason' "$f")"
    return 0
  fi
  local n
  n="$(jq -r '.stages|length' "$f")"
  [ "$n" -gt 0 ] || { echo "NO-STAGES:the manifest is valid but has no stage to run; a person has to fix the key"; return 0; }
  # running 优先于 failed/pending:进程在「已标 running、未写终态」间中断后,该 stage 必须重跑。
  # 不认 running 会让 where 指向下一个 pending(stage run 二次防线 die)甚至误报 SUCCESS。
  local interrupted
  interrupted="$(jq -r '[.stages[]|select(.status=="running")][0].name // ""' "$f")"
  if [ -n "$interrupted" ]; then
    jq -r --arg c "$interrupted" '"RETRY-STAGE:"+$c+" RUN:"+([.stages[]|select(.name==$c)][0].run|join(" "))' "$f"
    return 0
  fi
  # 管线是有序的,所以下一步就是**第一个还没 done 的阶段**——按位置,不按状态。曾经这里先挑
  # failed 再挑 pending,于是失效守卫把靠前的 assemble 打回 pending 之后,where 还指着靠后
  # 那个 failed 的 build:引擎要求先重装配,where 却让人重跑构建,驱动在这里原地打转。
  local cur status
  cur="$(jq -r '[.stages[]|select(.status!="done")][0].name // ""' "$f")"
  if [ -z "$cur" ]; then
    echo "SUCCESS:all stages done"
    return 0
  fi
  status="$(jq -r --arg c "$cur" '[.stages[]|select(.name==$c)][0].status' "$f")"
  local verb="STAGE"
  [ "$status" = "failed" ] && verb="RETRY-STAGE"
  jq -r --arg c "$cur" --arg v "$verb" '$v+":"+$c+" RUN:"+([.stages[]|select(.name==$c)][0].run|join(" "))' "$f"
}

cmd_stage() {
  local verb="${1:-}"
  shift || true
  case "$verb" in
    done) cmd_stage_done "$@" ;;
    fail) cmd_stage_fail "$@" ;;
    run) cmd_stage_run "$@" ;;
    *) die "usage: stage run|done|fail" ;;
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
# 这一层读子进程的输出。构建机是中文 Windows，不设的话按 GBK(cp936) 解——而下面那个子进程
# 里的一切（release.ps1 自己的报错、Python 钩子的日志）都是 UTF-8。解错了整段中文变乱码，
# 而这份日志是出包失败之后唯一的现场，人和自愈链读到的都是它。
try { [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false) } catch { }
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
  local script="" context="" build_env remote_host remote_root remote_conf manifest_path remote_input remote_input_win archive commit_file remote_context wrapper cmd_file runner_cmd_win task_name product installer_glob
  while [ $# -gt 0 ]; do
    case "$1" in
      --script) script="${2:-}"; shift 2 ;;
      --context) context="${2:-}"; shift 2 ;;
      *) echo "ERROR: mmw-release-remote-build got an unknown argument $1" >&2; return 64 ;;
    esac
  done
  case "$script" in /*) ;; *) echo "ERROR: remote build --script must be an absolute path" >&2; return 64 ;; esac
  case "$context" in /*) ;; *) echo "ERROR: remote build --context must be an absolute path" >&2; return 64 ;; esac
  [ -f "$script" ] || { echo "ERROR: no such remote build script: $script" >&2; return 64; }
  [ -f "$context" ] || { echo "ERROR: no such remote build context: $context" >&2; return 64; }
  remote_host="${RELEASE_REMOTE_HOST:-}"
  remote_root="${RELEASE_REMOTE_ROOT:-}"
  # 环境变量为空时回落到 remote-build.json：跟 *.release-adapter.json 同一个目录，
  # 一台构建机一份，不用每把钥匙抄一遍。落成文件是为了没有人需要记住这两个值——
  # 只活在人的记忆里，出包就会走到这一步停下来等人补。
  # 环境变量仍然优先：临时换一次构建机、以及测试灌假值，都只能走它。
  remote_conf=""
  manifest_path="$(jq -r '.manifest_path // empty' "$(state_file)" 2>/dev/null || true)"
  if [ -n "$manifest_path" ] && [ -f "$(dirname "$manifest_path")/remote-build.json" ]; then
    remote_conf="$(dirname "$manifest_path")/remote-build.json"
    [ -n "$remote_host" ] || remote_host="$(jq -r '.host // empty' "$remote_conf" 2>/dev/null || true)"
    [ -n "$remote_root" ] || remote_root="$(jq -r '.root // empty' "$remote_conf" 2>/dev/null || true)"
  fi
  # 这两行报错文字是产品仓库 diagnose 的匹配面，改它等于改掉那边的根因指纹。补充说明另起一行。
  if [ -z "$remote_host" ]; then
    echo "ERROR: remote build has no RELEASE_REMOTE_HOST" >&2
    echo "HINT: export it, or put remote-build.json next to the key: {\"host\": \"...\", \"root\": \"...\"}" >&2
    return 64
  fi
  if [ -z "$remote_root" ]; then
    echo "ERROR: remote build has no RELEASE_REMOTE_ROOT" >&2
    echo "HINT: export it, or put remote-build.json next to the key: {\"host\": \"...\", \"root\": \"...\"}" >&2
    return 64
  fi

  # 引号合同:远端命令跨三种解析器(cmd.exe / PowerShell 语言 / powershell.exe native CLI),
  # 单引号只在 PowerShell 语言里是定界符,cmd 与 native CLI 都按字面收——路径/任务名一旦需要
  # 引号就没有统一合同。唯一稳定做法:远端根收紧为字符白名单(盘符开头,只允许字母数字与
  # ._-/\),空格/引号/美元符/反引号/分号等一律拒,所有 schtasks 参数裸传不加引号。
  if ! printf '%s' "$remote_root" | grep -Eq '^[A-Za-z]:[/\\][A-Za-z0-9._/\\-]*$'; then
    echo "ERROR: RELEASE_REMOTE_ROOT must be an absolute Windows path in safe characters (drive letter, then letters/digits/._-/\\): $remote_root" >&2
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
      echo "ERROR: remote build context.product is missing or has illegal characters: '$product'" >&2
      return 64
      ;;
  esac
  remote_input="${remote_root%/}/${source_commit:0:12}-${product}"
  remote_input_win="$(printf '%s' "$remote_input" | tr '/' '\\')"
  # 成品安装包在源码树里的落点(仓库相对 glob),供出包成功后收拢到统一交付目录;缺省则不收拢。
  installer_glob="$(jq -r '.build_target.installer_glob // empty' "$context" 2>/dev/null)"

  # ── 断线重连 ────────────────────────────────────────────────────────────────
  #
  # 构建跑在那台机器的计划任务里,跟这一侧断不断没有关系;这一侧只是在看 exitcode 出没出现。
  # 看的人被杀掉(进程被停、网络断、会话结束),构建照样跑完、照样产出安装包,而这边什么都不知道:
  # 收拢没跑、状态停在「构建中」。真发生过一次,代价是一轮四十分钟的编译要靠人手工收尾。
  #
  # 所以传源码之前先问一句:这一轮(同 commit、同产品,也就是同一个远端目录)是不是还在跑?
  # 是就接上去轮询,不重传、不再建一个任务——重传会 Remove-Item 掉正在被读写的源码树,
  # 把一次快要跑完的编译毁掉,那比白等更贵。
  #
  # 判据是「有日志、没有 exitcode、而且日志刚刚还在长」。跑完的那一轮不在这条判据里:
  # 它留下的 exitcode 可能属于上一次失败,重跑才是重试该有的语义。
  local attached=0 live_probe
  live_probe="$(_ssh_ps "$remote_host" "if ((Test-Path '$remote_input/build-run.log') -and -not (Test-Path '$remote_input/build-run.exitcode') -and (((Get-Date) - (Get-Item '$remote_input/build-run.log').LastWriteTime).TotalMinutes -lt 10)) { 'LIVE' } else { 'NONE' }" 2>/dev/null || true)"
  live_probe="${live_probe%%[$'\r\n']*}"
  if [ "$live_probe" = "LIVE" ]; then
    attached=1
    # 任务名是建任务那一步写下的。读不回来也继续接:轮询与收拢都不需要它,
    # 只有尾部的清理需要,那一步自己会说清楚它没清掉什么。
    task_name="$(_ssh_ps "$remote_host" "Get-Content -LiteralPath '$remote_input/build-run.task' -ErrorAction SilentlyContinue" 2>/dev/null || true)"
    task_name="${task_name%%[$'\r\n']*}"
    echo "NOTE: a build for this commit is still running on $remote_host ($remote_input); attaching to it instead of starting a second one" >&2
  fi
  # 接上去的那一轮,源码、脚本、计划任务在远端都已经就位,这一整段跳过。
  if [ "$attached" != "1" ]; then
    archive="$stage_dir/source.zip"
    commit_file="$stage_dir/SOURCE_COMMIT.txt"
    remote_context="$stage_dir/release-context.remote.json"
    wrapper="$stage_dir/run-release.ps1"
    git -C "$top" archive --format=zip --output "$archive" HEAD || return $?
    printf '%s\n' "$source_commit" > "$commit_file"
    # 构建机自己的事实（镜像地址、ccache 装在哪）跟着 context 上去，模板在第一步就应用它们。
    # 它们不属于任何一把钥匙：换一台构建机，这些全变，而钥匙一个字都不用改。
    build_env='{}'
    if [ -n "$remote_conf" ]; then
      build_env="$(jq -c '.build_env // {}' "$remote_conf" 2>/dev/null || echo '{}')"
    fi
    # 工具链缓存放哪。不设的话 uv / Nuitka / pnpm / Electron 全都落在 %LOCALAPPDATA%,
    # 也就是系统盘——构建目录在 D 盘上跑得好好的,系统盘却被这几个缓存慢慢填满,直到某一轮
    # 磁盘闸把出包拦下来。缓存必须跨轮活着(那是它存在的理由),所以放在构建输入根**旁边**,
    # 不放在会被删掉的构建目录里面。命名跟 <根>-delivered 一致。
    local cache_root
    cache_root="${RELEASE_CACHE_ROOT:-}"
    if [ -z "$cache_root" ] && [ -n "$remote_conf" ]; then
      cache_root="$(jq -r '.cache_root // empty' "$remote_conf" 2>/dev/null || true)"
    fi
    [ -n "$cache_root" ] || cache_root="${remote_root%/}-cache"
    jq --arg root "$remote_input/source" --argjson be "$build_env" --arg cr "$cache_root" \
      '.repo_root = $root | .build_env = $be | .cache_root = $cr' "$context" > "$remote_context" || return $?
    _write_remote_wrapper "$wrapper"

    _ssh_ps "$remote_host" "New-Item -ItemType Directory -Force -Path '$remote_input' | Out-Null" || return $?
    # 失败的构建目录是现场,留着;但只留最近两个。再往前的没有人会读,而一个就是几个 GB。
    # 只动 <短commit>-<本产品> 这种目录名,交付目录与别的产品都不在范围内。
    # 用 -Property/-Like 而不是 `Where-Object { $_.Name ... }`:这条命令要穿过 bash 双引号、
    # 远端默认 shell(PowerShell)与 powershell.exe 三层,$_ 会在到达 powershell.exe 之前就被
    # 当成变量吃掉,于是筛选条件恒空、什么也不匹配,而且一声不响。
    if ! _ssh_ps "$remote_host" "Get-ChildItem -LiteralPath '${remote_root%/}' -Directory -ErrorAction SilentlyContinue | Where-Object -Property Name -Like '*-$product' | Where-Object -Property Name -NE '${source_commit:0:12}-$product' | Sort-Object LastWriteTime -Descending | Select-Object -Skip 2 | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"; then
      echo "WARN: could not prune old remote build dirs (this round is unaffected); take a look by hand: $remote_root" >&2
    fi
    scp "$archive" "$remote_host:$remote_input/source.zip" || return $?
    # 传完即删:这份 zip 是 `git archive $(cat SOURCE_COMMIT.txt)` 一字不差重生得出来的,
    # 不是记录,只是每一次尝试在 Mac 上多占的几百 MB。
    rm -f "$archive"
    scp "$commit_file" "$remote_host:$remote_input/SOURCE_COMMIT.txt" || return $?
    scp "$script" "$remote_host:$remote_input/release.ps1" || return $?
    scp "$remote_context" "$remote_host:$remote_input/release-context.json" || return $?
    scp "$wrapper" "$remote_host:$remote_input/run-release.ps1" || return $?

    # 忠实复刻现役 build-pc-installers.sh:schtasks /tr 指向一个 .cmd,由 .cmd 再调 run-release.ps1。
    # .cmd 单路径无空格无嵌套引号,规避 schtasks /tr 跨 cmd/PowerShell/native CLI 三解析器的引号地雷。
    # remote_input 已被上面字符白名单收紧(无空格),win 路径用反斜杠;-InputRoot 烘进 .cmd,不用 %~dp0
    # (末尾反斜杠+引号在 cmd→powershell 参数解析里会转义掉引号)。
    cmd_file="$stage_dir/run-release.cmd"
    printf '@echo off\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%s\\run-release.ps1" -InputRoot "%s"\r\n' "$remote_input_win" "$remote_input_win" > "$cmd_file"
    scp "$cmd_file" "$remote_host:$remote_input/run-release.cmd" || return $?
    runner_cmd_win="${remote_input_win}\\run-release.cmd"

    # 源码解压:在 harness 独立 ssh 会话里同步做完(~60s、断 ssh 无碍),失败必 fail-loud 不进构建。
    # (现役旧路径是在脱附会话内的 build ps1 里解压,同样可靠;此处前置做只是让解压失败在 Mac 侧即时可见。)
    # 先删旧 source 避免跨轮残留半解压文件;解压后校验目录非空,空即判失败。
    if ! _ssh_ps "$remote_host" "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue '$remote_input/source'; Expand-Archive -Force '$remote_input/source.zip' '$remote_input/source'; if (-not (Test-Path '$remote_input/source') -or -not (Get-ChildItem -Force '$remote_input/source')) { exit 1 }; Remove-Item -Force -ErrorAction SilentlyContinue '$remote_input/source.zip'"; then
      echo "ERROR: source did not expand on the build machine, or expanded to nothing: $remote_input/source" >&2
      return 71
    fi

    # 清掉上一轮遗留的构建产物并验证清干净:remote_input 只按 commit 命名,resume / 重跑同 commit
    # 时若不清,首次轮询就会读到过期 exitcode(如上轮的 "0")而把仍在跑或已失败的本轮误判成功——
    # 清除失败必须 fail-loud,不能静默继续。
    if ! _ssh_ps "$remote_host" "Remove-Item -Force -ErrorAction SilentlyContinue '$remote_input/build-run.log','$remote_input/build-run.exitcode'; if ((Test-Path '$remote_input/build-run.exitcode') -or (Test-Path '$remote_input/build-run.log')) { exit 1 }"; then
      echo "ERROR: could not clear the previous round on the build machine; a stale exitcode would read as this round succeeding: $remote_input" >&2
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
    # 任务名留在远端:这一侧断掉之后再来接,尾部的清理要靠它才知道该结束哪个任务。
    # 写不下去不挡构建——它只影响清理,而清理失败本来就是 WARN 不是失败。
    _ssh_ps "$remote_host" "Set-Content -LiteralPath '$remote_input/build-run.task' -Value '$task_name' -Encoding Ascii" >/dev/null 2>&1 ||
      echo "WARN: could not record the task name on $remote_host; a later attach will not be able to clean it up" >&2
  fi
  # 任务一旦 /create 成功,此后所有出口(/run 起不来、轮询超时、exitcode 损坏、正常结束)都必须
  # 结束可能仍在跑的构建 + 删计划任务:超时那类会有孤儿构建抢写下次同 commit 的 exitcode,其余虽只在
  # Task Scheduler 堆无害死条目也一并清。用子函数跑「/run + 轮询」拿 rc,函数尾部统一清理一次,不在每个
  # return 前重复 cleanup(避免上轮只补超时分支、漏掉 /run 失败与 exitcode 非法两个出口那类遗漏)。
  local rc=0 delivered=0
  _remote_run_and_poll "$remote_host" "$remote_input" "$task_name" "$stage_dir" "$attached" || rc=$?
  # 清理经 _ssh_ps 的 PowerShell 分号顺序执行(/end 失败不挡 /delete):cmd 的 `&` 在
  # PowerShell 5.1 解析失败、PS6+ 变后台 job,跨默认 shell 没有顺序语义。任务名与创建端
  # 同样裸传(无空格无引号,PowerShell 原样传给 schtasks native)。清理失败不改变构建判定,
  # 但必须留痕(残留任务会在下轮同 commit 抢写产物)。
  if [ -z "$task_name" ]; then
    # 接上来的那一轮没读回任务名(建任务时没写下,或文件丢了)。构建判定不受影响,
    # 但残留的任务会在下一轮同 commit 抢写产物,所以必须留痕、指出手工清的办法。
    echo "WARN: this round attached to a running build and could not learn its task name; look for a leftover mmw-release-* task on $remote_host and delete it by hand" >&2
  elif ! _ssh_ps "$remote_host" "schtasks /end /tn $task_name; schtasks /delete /tn $task_name /f" >/dev/null 2>&1; then
    echo "WARN: could not delete the scheduled task (task=$task_name); remove it by hand with schtasks /delete" >&2
  fi
  # 构建成功且钥匙声明了安装包落点:把安装包从 commit 哈希构建目录收拢到统一交付目录
  # $RELEASE_DELIVERY_ROOT/<product>/(缺省 D:\agentflow-releases),按产品分子目录、覆盖同名(每产品各占各的,
  # 不同产品不互删——覆盖问题在构建目录命名处已解;交付目录同产品新包盖旧包是预期)。排除 electron-builder
  # 的卸载器(*__*)与 .blockmap(-File + 扩展名 .exe + 非 __)。交付失败只 loud WARN 不改判定:包已在
  # 构建目录产出,交付是收拢便利,不该让一次拷贝故障把成功的构建标成失败——但必须留痕并指出源路径。
  if [ "$rc" -eq 0 ] && [ -n "$installer_glob" ]; then
    local delivery_root glob_win dest_win src_glob_win deliver_ps deliver_out
    # 交付目录是构建机的事实，不是技能的常量：先看环境变量，再看钥匙旁边的
    # remote-build.json，最后从构建输入根推一个同级目录出来。
    delivery_root="${RELEASE_DELIVERY_ROOT:-}"
    if [ -z "$delivery_root" ] && [ -n "$remote_conf" ]; then
      delivery_root="$(jq -r '.delivery_root // empty' "$remote_conf" 2>/dev/null || true)"
    fi
    [ -n "$delivery_root" ] || delivery_root="$(printf '%s' "${remote_root%/}" | tr '/' '\\')-delivered"
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
      printf '%s\n' "$deliver_out" | grep '^DELIVERED ' >&2 && delivered=1 || true
    else
      echo "WARN: could not gather the installer into $dest_win (the build did succeed; the installer is still at $src_glob_win): $deliver_out" >&2
    fi
  fi
  # 构建目录是过程,不是记录。安装包已经收进交付目录、日志已经回传到 stage_dir 之后,
  # 剩下的源码树、node_modules 与中间产物(一轮几个 GB)再没有人会读。
  # **失败的整个留着**:根因只存在于那台机器上的那个目录里。
  if [ "$rc" -eq 0 ] && [ "$delivered" -eq 1 ]; then
    if _ssh_ps "$remote_host" "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue '$remote_input'"; then
      REMOTE_LOG_REF=""
    else
      echo "WARN: could not remove the remote build dir; delete it by hand: $remote_input" >&2
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
  local remote_host="$1" remote_input="$2" task_name="$3" stage_dir="$4" attach="${5:-0}"

  # 接上一轮已经在跑的构建:任务早就起来了,这里只剩轮询。再 /run 一次会在同一个目录里
  # 起第二个构建,两个进程抢写同一份 exitcode 与同一棵源码树。
  if [ "$attach" = "1" ]; then
    _remote_poll_exitcode "$remote_host" "$remote_input" "$task_name" "$stage_dir"
    return $?
  fi

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
    echo "WARN: the detached build task did not start; retrying schtasks /run (attempt ${attempt})" >&2
  done
  if [ "$launched" != "1" ]; then
    echo "ERROR: the detached build task never started on $remote_host (no build-run.log and no exitcode ever appeared, task=$task_name)" >&2
    return 70
  fi

  _remote_poll_exitcode "$remote_host" "$remote_input" "$task_name" "$stage_dir"
}

# 轮询到本轮 exitcode 出现为止。起任务的那条路与接上去的那条路共用它——两边等的是同一件事,
# 分成两份写,改了一边忘另一边就是超时判定与日志回传各行其是。
_remote_poll_exitcode() {
  local remote_host="$1" remote_input="$2" task_name="$3" stage_dir="$4"

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
      echo "ERROR: remote build produced no exitcode within ${max_seconds}s (task=$task_name)" >&2
      _fetch_remote_build_log "$remote_host" "$remote_input" "$stage_dir"
      return 70
    fi
    sleep "$poll_seconds"
  done
  _fetch_remote_build_log "$remote_host" "$remote_input" "$stage_dir"
  case "$exit_code" in
    ''|*[!0-9-]*) echo "ERROR: remote build returned an illegal exit code: $exit_code" >&2; return 70 ;;
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
    echo "WARN: could not fetch the build log back from $remote_input/build-run.log" >&2
  fi
}

cmd_stage_run() {
  local requested="" f name top mp source_commit attempt_id stage_dir loop_dir log_file raw expanded rc=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --stage) requested="$2"; shift 2 ;;
      *) die "unknown argument $1" ;;
    esac
  done

  f="$(need_state)"
  jq -e . "$f" >/dev/null 2>&1 || die "release-state is corrupt; refusing to run a stage"
  name="$(jq -r '[.stages[] | select(.status == "pending" or .status == "failed" or .status == "running")][0].name // ""' "$f")"
  [ -n "$name" ] || die "no stage left to run"
  if [ -n "$requested" ] && [ "$requested" != "$name" ]; then
    die "only the earliest unfinished stage may run: $name"
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
    argv+=("$(_expand_argv_token "$raw" "$stage_dir" "$loop_dir")")
  done < <(jq -r --arg n "$name" '.stages[] | select(.name == $n) | .run[]' "$f")
  [ ${#argv[@]} -gt 0 ] || die "stage $name has an empty argv"

  # 装配之后技能自己改了，$loop_dir 里那份脚本就过期了。拿它去构建机跑，每一步都对，
  # 只是跑的不是刚改的那一份——这一类失败在日志里完全看不出来。
  if [ "$name" = "build" ] && [ "${argv[0]}" = "mmw-release-remote-build" ]; then
    local recorded current
    recorded="$(jq -r '.skill_fingerprint // ""' "$f")"
    current="$(_skill_fingerprint)"
    if [ -n "$recorded" ] && [ "$recorded" != "$current" ]; then
      edit "$f" '(.stages |= map(if .name == "assemble" then .status = "pending" else . end))
                 | .current_stage = "assemble"'
      echo "STALE-SCRIPT: the skill changed after assemble; rerun assemble, then build" >&2
      return 1
    fi
  fi

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
    [ "$name" = "assemble" ] && edit "$f" --arg fp "$(_skill_fingerprint)" '.skill_fingerprint = $fp'
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
    diagnose_argv+=("$(_expand_argv_token "$diag_arg" "$stage_dir" "$loop_dir")")
  done < <(_diagnose_argv_source "$mp")
  [ ${#diagnose_argv[@]} -gt 0 ] || die "manifest.diagnose is empty"
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
  echo "STAGE-RUN-FAILED $name rc=$rc; going to diagnose and classify" >&2
  cmd_stage_fail --stage "$name" --findings "$findings_file"
}

cmd_stage_done() {
  local name=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --stage) name="$2"; shift 2 ;;
      *) die "unknown argument $1" ;;
    esac
  done
  [ -n "$name" ] || die "--stage is required"
  local f earliest
  f="$(need_state)"
  jq -e --arg n "$name" 'any(.stages[]; .name==$n)' "$f" >/dev/null || die "no such stage: $name"
  # stage run 是唯一执行器;stage done 只是人工确认位,只能确认最早未完成 stage,否则可把从未
  # 执行的 build 直接标 done、让 exit-check 在没有安装包的情况下报 DONE。
  earliest="$(jq -r '[.stages[] | select(.status == "pending" or .status == "failed" or .status == "running")][0].name // ""' "$f")"
  [ -n "$earliest" ] || die "no unfinished stage to confirm"
  [ "$name" = "$earliest" ] || die "only the earliest unfinished stage may be confirmed: $earliest"
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
      *) die "unknown argument $1" ;;
    esac
  done
  [ -n "$name" ] || die "--stage is required"
  [ -n "$findings" ] || die "--findings is required"
  [ -f "$findings" ] || die "no such findings file: $findings"

  local f
  f="$(need_state)"
  jq -e --arg n "$name" 'any(.stages[]; .name==$n)' "$f" >/dev/null || die "no such stage: $name"

  local cls
  if ! cls="$(uv run --quiet "$SCRIPT_DIR/release_contracts.py" classify-findings "$findings")"; then
    append_attempt "$f" "$name" "stage" "unclassifiable" "" "$findings"
    edit "$f" --arg n "$name" --arg fd "$findings" \
      '(.stages |= map(if .name==$n then .status="failed" else . end))
       | .current_stage=$n
       | .pause={at_stage:$n, kind:"surface", reason:"needs-context",
                 question:("diagnose for stage "+$n+" produced no valid Finding ("+$fd+"); it cannot be classified, so it goes to a human")}'
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
                 question:("diagnose for stage "+$n+" produced no fail Finding ("+$fd+"); there is nothing to diagnose, so it goes to a human")}'
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
               question:("stage "+$n+" broke a P0 hard constraint ("+$fp+"); this needs human approval and stops here")}'
    emit_event "$f" "paused" "$name" "P0" "$fp" "$aref"
    echo "CLASSIFY=P0 $name -> PAUSE (hand to a person)"
    return 0
  fi

  emit_event "$f" "classified" "$name" "$tier" "$fp" "$aref"
  echo "CLASSIFY=$tier $name (waiting for fix-dispatch)"
}

cmd_dispatch() {
  local name="" findings=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --stage) name="$2"; shift 2 ;;
      --findings) findings="$2"; shift 2 ;;
      *) die "unknown argument $1" ;;
    esac
  done
  [ -n "$name" ] || die "--stage is required"

  local f cls
  f="$(need_state)"
  # 驱动器经 stage run 失败时,diagnose findings 已由 cmd_stage_fail 记进最近一条 attempt 的 artifact_refs;
  # 省略 --findings 即从 state 读回,驱动器无须复制引擎的内部 findings 路径。
  if [ -z "$findings" ]; then
    findings="$(jq -r '.attempt_ledger[-1].artifact_refs[0] // ""' "$f")"
  fi
  [ -n "$findings" ] || die "--findings not given and the ledger holds no usable findings reference"
  [ -f "$findings" ] || die "no such findings file: $findings"
  jq -e --arg n "$name" 'any(.stages[]; .name==$n)' "$f" >/dev/null || die "no such stage: $name"

  if ! cls="$(uv run --quiet "$SCRIPT_DIR/release_contracts.py" classify-findings "$findings")"; then
    edit "$f" --arg n "$name" --arg fd "$findings" \
      '.pause={at_stage:$n, kind:"surface", reason:"needs-context",
               question:("the findings at dispatch ("+$fd+") produced no valid Finding; they cannot be classified, so this goes to a human")}'
    echo "UNCLASSIFIABLE:$name(dispatch escalate)"
    return 0
  fi

  local tier fp
  tier="$(printf '%s' "$cls" | jq -r '.highest_tier // ""')"
  fp="$(printf '%s' "$cls" | jq -r '.failing[0].root_cause_fingerprint // ""')"
  [ -n "$tier" ] || { echo "NOTHING-TO-DISPATCH:$name has no failing finding"; return 0; }
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
    echo "TRANSIENT-RETRY:$name ($fp, rerun as-is, no fix dispatched)"
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
                  question:("dispatch "+$n+" broke a P0 hard constraint ("+$fp+"); this needs human approval and stops here")}'
      emit_event "$f" "paused" "$name" "P0" "$fp" "$aref"
      echo "P0:$name hard constraint ($fp), handed to a person (PAUSED)"
      ;;
    P2) cmd_dispatch_p2 "$f" "$name" "$fp" "$findings" ;;
    P1) cmd_dispatch_p1 "$f" "$name" "$fp" "$findings" ;;
    *) die "unknown tier: $tier" ;;
  esac
}

cmd_round() {
  local verb="${1:-}"
  shift || true
  [ "$verb" = "next" ] || die "usage: round next"
  local f max cur new
  f="$(need_state)"
  max="$(jq -r '.max_rounds // 0' "$f")"
  cur="$(jq -r '.round // 1' "$f")"
  new=$(( cur + 1 ))
  if [ "$max" -gt 0 ] && [ "$new" -gt "$max" ]; then
    edit "$f" --arg q "ran the full $max rounds without converging; the engine stops and hands it to a human (loop guard)" \
      '.pause={at_stage:(.current_stage // ""), kind:"surface", reason:"needs-redirection", question:$q}'
    echo "ROUND-CAP:max=$max (surfaced to a person)"
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
      *) die "unknown argument $1" ;;
    esac
  done
  case "$kind" in needs-context|needs-redirection) ;; *) die "--kind must be needs-context or needs-redirection" ;; esac
  [ -n "$q" ] || die "--question is required"
  edit "$(need_state)" --arg at "$at" --arg k "$kind" --arg q "$q" \
    '.pause={at_stage:$at, kind:"surface", reason:$k, question:$q}'
  echo "SURFACED $kind"
}

cmd_resume() {
  local f live saved start
  f="$(need_state)"
  jq -e . "$f" >/dev/null 2>&1 || die "release-state is corrupt; refusing to resume"
  live="$(git -C "$(_repo_top)" rev-parse HEAD)"
  saved="$(jq -r '.source_commit // ""' "$f")"
  if [ "$saved" != "$live" ]; then
    edit "$f" --arg sc "$live" \
      '(.stages |= map(.status = "pending"))
       | .source_commit = $sc
       | .current_stage = (.stages[0].name // null)
       | .pause = null'
    echo "RESUMED:HEAD-CHANGED every stage will run again"
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
  local top f main product commit
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "NO-GIT"; return 0; }
  f="$top/$RELEASE_SUBDIR/$STATE_NAME"
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
      main="$(main_root)"
      mkdir -p "$main/$RELEASE_SUBDIR/delivered"
      jq -n --arg p "$product" --arg c "$commit" --arg at "$(now)" \
        '{product:$p, source_commit:$c, closed_at:$at}' > "$main/$RELEASE_SUBDIR/delivered/$product.json"
    fi
    rm -f "$f"
  fi
  echo "CLOSED"
}

# 放弃这一轮:删活状态,**不写交付记录**。
#
# close 无条件写那份记录,它说的是「这个产品在这个 commit 上出过包」。中途换产品、
# 放弃重来时用 close,就等于写下一个根本不存在的包,而且盖掉上一次真实的记录——
# 第 4 步的同 commit 校验读的正是它,假记录会让那道校验失效。
#
# 现场留着:release-artifacts/ 下的日志与 findings 是这一轮唯一的记录,活状态也另存一份,
# 出了事还能翻。真正要清掉的只是「有一轮正在进行」这个事实。
cmd_abort() {
  local top f keep
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "NO-GIT"; return 0; }
  f="$top/$RELEASE_SUBDIR/$STATE_NAME"
  if [ ! -f "$f" ]; then
    echo "NO-LOOP"
    return 0
  fi
  keep="$top/$RELEASE_SUBDIR/release-artifacts/aborted-$(jq -r '.product // "unknown"' "$f" 2>/dev/null || echo unknown)-$(date +%Y%m%d-%H%M%S).json"
  mkdir -p "$(dirname "$keep")"
  mv "$f" "$keep"
  echo "ABORTED:no delivery record written; the state of this round is kept at $keep"
}

cmd_exit_check() {
  local f
  f="$(need_state)"
  jq -e . "$f" >/dev/null 2>&1 || { echo "CORRUPT:release-state is empty or not valid JSON"; return 0; }
  if [ "$(jq -r '.pause // "null"' "$f")" != "null" ]; then
    echo "PAUSED:$(jq -r '.pause.reason' "$f")"
    return 0
  fi
  local n
  n="$(jq -r '.stages|length' "$f")"
  [ "$n" -gt 0 ] || { echo "NOT-DONE:stages=EMPTY (the manifest has no stages)"; return 0; }
  local rem
  rem="$(jq -r '[.stages[]|select(.status=="failed")|.name]|join(",")' "$f")"
  [ -n "$rem" ] || rem="$(jq -r '[.stages[]|select(.status!="done")|.name]|join(",")' "$f")"
  [ -z "$rem" ] && echo "DONE" || echo "NOT-DONE:stages=$rem"
}

cmd_receipt() {
  local f
  f="$(need_state)"
  jq -e . "$f" >/dev/null 2>&1 || { echo "CORRUPT:release-state is empty or not valid JSON"; return 0; }
  echo "# release receipt - product=$(jq -r .product "$f")"
  if [ "$(jq -r '.pause // "null"' "$f")" != "null" ]; then
    echo "## paused at stage=$(jq -r '.pause.at_stage' "$f") reason=$(jq -r '.pause.reason' "$f")"
    jq -r '.pause.question' "$f"
  fi
  echo "## attempts so far:"
  # log_refs 必须进入 receipt：PAUSED:needs-context 的自主处置政策
  # 在 driving.md 第一步从该命令读取日志 locator(file:/pc:)，漏印会迫使主 agent 翻 state 文件猜路径。
  jq -r '.attempt_ledger[] | "- ["+.action_kind+"] stage="+.stage+" outcome="+.outcome+(if .root_cause_fingerprint then " fp="+.root_cause_fingerprint else "" end)+(if (.artifact_refs|length)>0 then " findings="+(.artifact_refs|join(",")) else "" end)+(if (.log_refs//[]|length)>0 then " logs="+(.log_refs|join(",")) else "" end)' "$f"
  echo "## fingerprints seen:"
  jq -r '.fingerprint_ledger[] | "- "+.fingerprint+" x"+(.count|tostring)' "$f"
}

case "${1:-}" in
  -h|--help)
    if usage_release; then :; fi
    exit 0
    ;;
  init)       shift; cmd_init "$@" ;;
  where)      shift; cmd_where "$@" ;;
  stage)      shift; cmd_stage "$@" ;;
  round)      shift; cmd_round "$@" ;;
  surface)    shift; cmd_surface "$@" ;;
  resume)     shift; cmd_resume "$@" ;;
  close)      shift; cmd_close "$@" ;;
  abort)      shift; cmd_abort "$@" ;;
  exit-check) shift; cmd_exit_check "$@" ;;
  receipt)    shift; cmd_receipt "$@" ;;
  dispatch)   shift; cmd_dispatch "$@" ;;
  *) usage_release ;;
esac
