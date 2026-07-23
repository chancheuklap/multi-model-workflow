#!/usr/bin/env bash
# prototype.sh —— design 阶段内的可恢复 prototype 迭代账本。
# 只有两个动作：start 首次登记/接管；checkpoint 记录一轮并继续、接受或废止。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"
# shellcheck source=lib/prototype-state.sh
. "$SCRIPT_DIR/lib/prototype-state.sh"

MANIFEST_NAME="task.json"
MMW="bash \"$SCRIPT_DIR/mmw.sh\""

die() { echo "ERROR: $*" >&2; exit 1; }
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }

manifest_path() {
  local top man
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "不在 git 仓库内"
  man="$(mmw_prototype_manifest_from_top "$top")" || die "无法解析状态目录"
  [ -f "$man" ] || die "当前不是在管任务(无 $MANIFEST_NAME)"
  printf '%s' "$man"
}

write_manifest() {
  local man="$1" tmp stamped
  tmp="$(mktemp "$(dirname "$man")/.prototype-manifest.XXXXXX")" || return 1
  cat >"$tmp"
  if [ ! -s "$tmp" ] || ! jq -e . "$tmp" >/dev/null 2>&1; then
    rm -f "$tmp"; echo "ERROR: prototype 状态写入为空或不是合法 JSON，原 manifest 保留" >&2; return 1
  fi
  stamped="$(mktemp "$(dirname "$man")/.prototype-stamped.XXXXXX")" || { rm -f "$tmp"; return 1; }
  if jq --arg at "$(now)" '.updated_at=$at' "$tmp" >"$stamped" && [ -s "$stamped" ] && jq -e . "$stamped" >/dev/null 2>&1; then
    mv "$stamped" "$man"; rm -f "$tmp"
  else
    rm -f "$tmp" "$stamped"; return 1
  fi
}

require_design_phase() {
  local man="$1" scenario phase status gate
  scenario="$(jq -r '.scenario // empty' "$man")"
  phase="$(jq -r '.phase // empty' "$man")"
  status="$(jq -r '.status // empty' "$man")"
  gate="$(jq -r '.gate // empty' "$man")"
  [ "$scenario" = develop ] || die "prototype 迭代只属于 develop 设计路(当前 scenario=$scenario)"
  [ "$phase" = design ] || die "prototype 只能在 design 阶段运行(当前 phase=$phase)"
  [ "$status" = active ] || die "任务不是 active(当前 status=$status)，先按 mmw where 恢复"
  [ -z "$gate" ] || die "design 当前处于 gate=$gate，不能改 prototype"
}

require_single_line() {
  local label="$1" value="$2"
  [ -n "$value" ] || die "$label 必填"
  if mmw_prototype_has_newline "$value"; then die "$label 必须是单行文本"; fi
  return 0
}

array_json() {
  if [ "$#" -eq 0 ]; then printf '[]'; else printf '%s\n' "$@" | jq -R . | jq -s 'unique'; fi
}

array_contains() {
  local needle="$1"; shift
  local item
  for item in "$@"; do [ "$item" = "$needle" ] && return 0; done
  return 1
}

validate_artifacts() {
  local top="$1" man="$2" rel
  shift 2
  for rel in "$@"; do mmw_prototype_validate_artifact "$top" "$man" "$rel" || exit 1; done
}

payload_hash() {
  git hash-object --stdin
}

ensure_log_parent() {
  local log="$1"
  mkdir -p "$(dirname "$log")/runs"
  if [ ! -f "$log" ]; then
    cat >"$log" <<'EOF'
# Prototype

> 本文件由 `mmw prototype` 维护。源码在原路径持续演进，历史版本由 Git 保存。
EOF
  fi
  [ ! -L "$log" ] || die "prototype 日志不得是软链:$log"
}

append_start_log() {
  local log="$1" token="$2" kind="$3" question="$4" run="$5" adopted="$6"
  local marker="<!-- mmw-prototype-session:$token -->"
  ensure_log_parent "$log"
  grep -qF "$marker" "$log" && return 0
  cat >>"$log" <<EOF

$marker
## 验证问题

- 类型：$kind
- 问题：$question
- 运行命令：\`$run\`
- 起点：$adopted

## 迭代记录
EOF
}

append_round_log() {
  local log="$1" round="$2" feedback="$3" change="$4" result="$5" verdict="$6"
  local evidence_json="$7" selected_json="$8" payload hash marker hash_marker
  payload="$(printf '%s\n%s\n%s\n%s\n%s\n%s\n' "$feedback" "$change" "$result" "$verdict" "$evidence_json" "$selected_json")"
  hash="$(printf '%s' "$payload" | payload_hash)"
  marker="<!-- mmw-prototype-round:$round -->"
  hash_marker="<!-- mmw-prototype-payload:$hash -->"
  if grep -qF "$marker" "$log"; then
    grep -qF "$hash_marker" "$log" || die "第 $round 轮日志已存在但内容不同，拒绝覆盖；先读 $log 对齐"
    return 0
  fi
  {
    printf '\n%s\n%s\n### 第 %s 轮\n\n' "$marker" "$hash_marker" "$round"
    printf '**反馈或假设**\n\n%s\n\n' "$feedback"
    printf '**实际改动**\n\n%s\n\n' "$change"
    printf '**验证结果**\n\n%s\n\n' "$result"
    printf '**证据**\n\n'
    if [ "$(jq -r 'length' <<<"$evidence_json")" -eq 0 ]; then printf -- '- 无独立证据文件\n'; else jq -r '.[] | "- `\(.)`"' <<<"$evidence_json"; fi
    printf '\n**结论**\n\n- verdict：`%s`\n' "$verdict"
    if [ "$(jq -r 'length' <<<"$selected_json")" -gt 0 ]; then jq -r '.[] | "- selected：`\(.)`"' <<<"$selected_json"; fi
  } >>"$log"
}

append_reopen_log() {
  local log="$1" round="$2" feedback="$3" hash marker
  hash="$(printf '%s' "$feedback" | payload_hash)"
  marker="<!-- mmw-prototype-reopen:$round:$hash -->"
  grep -qF "$marker" "$log" && return 0
  cat >>"$log" <<EOF

$marker
### 第 $round 轮重新打开

**新反馈**

$feedback
EOF
}

print_state() {
  local man="$1"
  echo "prototype_status=$(jq -r '.prototype.status' "$man")"
  echo "prototype_iteration=$(jq -r '.prototype.iteration' "$man")"
  echo "prototype_log=$(jq -r '.prototype.log' "$man")"
  echo "prototype_artifacts=$(jq -c '.prototype.artifacts' "$man")"
  echo "prototype_selected=$(jq -c '.prototype.selected' "$man")"
}

cmd_start() {
  local kind="" question="" run="" adopt=false
  local -a artifacts=()
  while [ $# -gt 0 ]; do
    case "$1" in
      --kind) kind="$2"; shift 2 ;;
      --question) question="$2"; shift 2 ;;
      --run) run="$2"; shift 2 ;;
      --artifact) artifacts+=("$2"); shift 2 ;;
      --adopt) adopt=true; shift ;;
      *) die "未知参数:$1" ;;
    esac
  done
  case "$kind" in logic|ui|mixed) ;; *) die "--kind 只能 logic|ui|mixed" ;; esac
  require_single_line "--question" "$question"
  require_single_line "--run" "$run"

  local man top current_status previous_token log_rel log_abs artifacts_json token untracked rel
  man="$(manifest_path)"; require_design_phase "$man"
  top="$(git rev-parse --show-toplevel)"
  current_status="$(jq -r 'if .prototype == null then "" else (.prototype.status // "BROKEN") end' "$man")"
  case "$current_status" in
    active)
      echo "prototype 已在第 $(jq -r '.prototype.iteration' "$man") 轮，拒绝重建" >&2
      echo "NEXT=先读 $(jq -r '.prototype.log' "$man") 与现有 artifacts，在原产物上修改；验证后运行 $MMW prototype checkpoint" >&2
      exit 1 ;;
    accepted)
      echo "prototype 已 accepted，拒绝重新 start" >&2
      echo "NEXT=收到新反馈时运行 $MMW prototype checkpoint --feedback '<新反馈>' --verdict continue 重新打开" >&2
      exit 1 ;;
    BROKEN) die "task.json.prototype 非 null 但缺合法 status，先修复损坏状态" ;;
    ""|superseded) ;;
    *) die "未知 prototype status:$current_status" ;;
  esac

  if $adopt; then
    [ -z "$current_status" ] || die "--adopt 只接管缺状态的旧任务；当前 prototype=$current_status"
    [ "${#artifacts[@]}" -gt 0 ] || die "--adopt 必须至少带一个 --artifact"
  elif [ "${#artifacts[@]}" -gt 0 ]; then
    die "fresh start 不接收 --artifact；已有产物使用 --adopt"
  fi

  untracked="$(mmw_prototype_untracked_paths "$top" "$man")"
  if [ -z "$current_status" ] && [ -n "$untracked" ]; then
    if ! $adopt; then
      echo "已有未登记 prototype/mockup，拒绝 fresh start:" >&2
      printf '%s\n' "$untracked" | sed 's/^/  - /' >&2
      echo "NEXT=$MMW prototype start --adopt --kind <logic|ui|mixed> --question '<问题>' --run '<命令>' $(printf '%s\n' "$untracked" | sed 's/.*/--artifact "&"/' | tr '\n' ' ')" >&2
      exit 1
    fi
    while IFS= read -r rel; do
      [ -n "$rel" ] || continue
      array_contains "$rel" ${artifacts[@]+"${artifacts[@]}"} || die "--adopt 必须显式登记全部已有文件，缺:$rel"
    done <<<"$untracked"
  fi

  validate_artifacts "$top" "$man" ${artifacts[@]+"${artifacts[@]}"}
  artifacts_json="$(array_json ${artifacts[@]+"${artifacts[@]}"})"
  log_rel="$(mmw_prototype_log_rel "$man")" || die "manifest.docs.design 缺失"
  log_abs="$top/$log_rel"
  previous_token="$(jq -r '.prototype.updated_at // "initial"' "$man")"
  token="$(printf '%s\n%s\n%s\n%s\n' "$previous_token" "$kind" "$question" "$run" | payload_hash)"
  append_start_log "$log_abs" "$token" "$kind" "$question" "$run" "$($adopt && printf '接管已有产物' || printf '全新原型')"

  jq --arg kind "$kind" --arg question "$question" --arg run "$run" --arg log "$log_rel" \
    --arg at "$(now)" --argjson artifacts "$artifacts_json" \
    '.prototype={status:"active",kind:$kind,question:$question,iteration:1,run_command:$run,
      artifacts:$artifacts,selected:[],log:$log,updated_at:$at}' "$man" | write_manifest "$man" \
    || die "prototype start 状态写入失败；日志已保留，原命令可安全重跑"

  if $adopt; then echo "PROTOTYPE_ADOPTED"; else echo "PROTOTYPE_STARTED"; fi
  print_state "$man"
  echo "NEXT=先读 $log_rel 与 prototype-mockup.md；制作或运行现有原型，只在原产物上迭代，验证后运行 $MMW prototype checkpoint"
}

cmd_checkpoint() {
  local feedback="" change="" result="" verdict=""
  local -a artifacts=() evidence=() selected=()
  while [ $# -gt 0 ]; do
    case "$1" in
      --feedback) feedback="$2"; shift 2 ;;
      --change) change="$2"; shift 2 ;;
      --result) result="$2"; shift 2 ;;
      --verdict) verdict="$2"; shift 2 ;;
      --artifact) artifacts+=("$2"); shift 2 ;;
      --evidence) evidence+=("$2"); shift 2 ;;
      --selected) selected+=("$2"); shift 2 ;;
      *) die "未知参数:$1" ;;
    esac
  done
  case "$verdict" in continue|accepted|superseded) ;; *) die "--verdict 只能 continue|accepted|superseded" ;; esac
  require_single_line "--feedback" "$feedback"

  local man top status iteration new_iteration log_rel log_abs
  man="$(manifest_path)"; require_design_phase "$man"
  top="$(git rev-parse --show-toplevel)"
  status="$(jq -r '.prototype.status // empty' "$man")"
  [ -n "$status" ] || die "尚未 start prototype"
  iteration="$(jq -r '.prototype.iteration // 0' "$man")"
  [ "$iteration" -ge 1 ] 2>/dev/null || die "prototype.iteration 损坏:$iteration"
  log_rel="$(jq -r '.prototype.log // empty' "$man")"
  [ -n "$log_rel" ] && [ -f "$top/$log_rel" ] || die "prototype 日志缺失:$log_rel"
  log_abs="$top/$log_rel"

  # accepted 后的新反馈先重新打开；本动作不伪造尚未发生的改动和验证结果。
  if [ "$status" = accepted ]; then
    [ "$verdict" = continue ] || die "accepted prototype 只能用 --verdict continue 重新打开"
    [ -z "$change" ] && [ -z "$result" ] || die "重新打开时只登记 --feedback，不填写尚未发生的 change/result"
    [ "${#artifacts[@]}" -eq 0 ] && [ "${#evidence[@]}" -eq 0 ] && [ "${#selected[@]}" -eq 0 ] \
      || die "重新打开时不改产物；进入 active 后完成下一轮 checkpoint"
    new_iteration=$(( iteration + 1 ))
    append_reopen_log "$log_abs" "$new_iteration" "$feedback"
    jq --argjson n "$new_iteration" --arg at "$(now)" \
      '.prototype.status="active" | .prototype.iteration=$n | .prototype.selected=[] | .prototype.updated_at=$at' \
      "$man" | write_manifest "$man" || die "prototype 重新打开写入失败；原命令可安全重跑"
    echo "PROTOTYPE_REOPENED"
    print_state "$man"
    echo "NEXT=先读 $log_rel 与现有 artifacts，按新反馈修改并运行原型；完成后运行 $MMW prototype checkpoint"
    return 0
  fi

  [ "$status" = active ] || die "prototype status=$status，不能 checkpoint；按 mmw where 指路"
  require_single_line "--change" "$change"
  require_single_line "--result" "$result"
  [ "$verdict" != accepted ] || [ "${#selected[@]}" -gt 0 ] || die "accepted 必须至少带一个 --selected"
  [ "$verdict" = accepted ] || [ "${#selected[@]}" -eq 0 ] || die "--selected 只用于 accepted"

  local rel
  if [ "${#artifacts[@]}" -eq 0 ]; then
    while IFS= read -r rel; do [ -n "$rel" ] && artifacts+=("$rel"); done < <(jq -r '.prototype.artifacts[]?' "$man")
  fi
  validate_artifacts "$top" "$man" ${artifacts[@]+"${artifacts[@]}"}
  validate_artifacts "$top" "$man" ${selected[@]+"${selected[@]}"}
  for rel in ${selected[@]+"${selected[@]}"}; do array_contains "$rel" ${artifacts[@]+"${artifacts[@]}"} || artifacts+=("$rel"); done
  if [ "$verdict" != superseded ] && [ "${#artifacts[@]}" -eq 0 ]; then
    die "$verdict checkpoint 必须有至少一个真实 artifact"
  fi
  for rel in ${evidence[@]+"${evidence[@]}"}; do mmw_prototype_validate_evidence "$top" "$man" "$rel" "$iteration" || exit 1; done

  local artifacts_json evidence_json selected_json next_status
  artifacts_json="$(array_json ${artifacts[@]+"${artifacts[@]}"})"
  evidence_json="$(array_json ${evidence[@]+"${evidence[@]}"})"
  selected_json="$(array_json ${selected[@]+"${selected[@]}"})"
  append_round_log "$log_abs" "$iteration" "$feedback" "$change" "$result" "$verdict" "$evidence_json" "$selected_json"

  case "$verdict" in
    continue) next_status=active; new_iteration=$(( iteration + 1 )); selected_json='[]' ;;
    accepted) next_status=accepted; new_iteration="$iteration" ;;
    superseded) next_status=superseded; new_iteration="$iteration"; selected_json='[]' ;;
  esac
  jq --arg status "$next_status" --argjson iteration "$new_iteration" --argjson artifacts "$artifacts_json" \
    --argjson selected "$selected_json" --arg at "$(now)" \
    '.prototype.status=$status | .prototype.iteration=$iteration | .prototype.artifacts=$artifacts |
      .prototype.selected=$selected | .prototype.updated_at=$at' "$man" | write_manifest "$man" \
    || die "prototype checkpoint 状态写入失败；日志已幂等落盘，原命令可安全重跑"

  echo "PROTOTYPE_CHECKPOINTED verdict=$verdict"
  print_state "$man"
  case "$verdict" in
    continue) echo "NEXT=先读 $log_rel 与现有 artifacts，在原产物上完成第 $new_iteration 轮；验证后再次运行 $MMW prototype checkpoint" ;;
    accepted) echo "NEXT=把 selected 的状态模型、交互和结论回填主设计文档，完成 design self-check 与设计预审，再请用户 /approve-design" ;;
    superseded) echo "NEXT=$MMW handoff --conclusion needs-redirection --to-phase propose" ;;
  esac
}

case "${1:-}" in
  start) shift; cmd_start "$@" ;;
  checkpoint) shift; cmd_checkpoint "$@" ;;
  *) die "用法: prototype start|checkpoint ..." ;;
esac
