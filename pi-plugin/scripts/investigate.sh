#!/usr/bin/env bash
# pi 原生 investigate fan-out 准备 + schema 校验 + synthesis 汇编(pi-subagents 原生)。
# 脚本不启动工人:start 准备每 topic 的 prompt 与账本并打印派发指令,协调者在会话内
# 用 Agent 工具并行派 investigate-topic;工人最终消息(一个紧凑 JSON)由协调者经
# submit 交回,当场过 schema 闸。全部 topic 过闸后 status 备好 synthesis prompt,
# 协调者派 investigate-synthesizer,结果同样 submit 交回并汇编 result.json。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"

TOPIC_AGENT="${PI_INVESTIGATE_AGENT:-investigate-topic}"
SYNTH_AGENT="${PI_INVESTIGATE_SYNTH_AGENT:-investigate-synthesizer}"
MMW_INVESTIGATE_RUN_LOCK=""
MMW_INVESTIGATE_START_LOCK=""
MMW_INVESTIGATE_STAGING=""

die() { echo "ERROR: $*" >&2; exit 2; }

repo_top() {
  git rev-parse --show-toplevel 2>/dev/null || die "不在 git 仓库内"
}

run_root() {
  local run="$1" top sd
  [[ "$run" =~ ^[A-Za-z0-9._-]+$ ]] || die "--run 只能含字母、数字、点、下划线和横线"
  top="$(repo_top)"
  sd="$(mmw_resolve_state_subdir "$top")"
  printf '%s/%s/investigate-runs/%s' "$top" "$sd" "$run"
}

cleanup_investigate_locks() {
  local lock staging="${MMW_INVESTIGATE_STAGING:-}"
  for lock in "${MMW_INVESTIGATE_RUN_LOCK:-}" "${MMW_INVESTIGATE_START_LOCK:-}"; do
    [ -n "$lock" ] || continue
    rm -f "$lock"
  done
  case "$staging" in
    */.pi/multi-model-workflow/investigate-runs/.*.start.[0-9]*)
      [ -d "$staging" ] && rm -rf "$staging"
      ;;
  esac
}

acquire_lock_path() {
  local lock="$1" owner=""
  if ! (set -o noclobber; printf '%s\n' "$$" >"$lock") 2>/dev/null; then
    owner="$(cat "$lock" 2>/dev/null || true)"
    [ -n "$owner" ] || die "investigate 锁正在初始化，请稍后重跑:$lock"
    if [ -n "$owner" ] && kill -0 "$owner" 2>/dev/null; then
      die "investigate run 正被另一个 status/submit 更新:$owner"
    fi
    die "investigate 锁的 owner 已退出；确认没有同 run 进程后删除锁再重跑:$lock"
  fi
  trap cleanup_investigate_locks EXIT
}

acquire_run_lock() {
  local root="$1"
  acquire_lock_path "$root/.run-lock"
  MMW_INVESTIGATE_RUN_LOCK="$root/.run-lock"
}

release_start_lock() {
  local lock="${MMW_INVESTIGATE_START_LOCK:-}"
  [ -n "$lock" ] || return 0
  rm -f "$lock"
  MMW_INVESTIGATE_START_LOCK=""
}

release_run_lock() {
  local lock="${MMW_INVESTIGATE_RUN_LOCK:-}"
  [ -n "$lock" ] || return 0
  rm -f "$lock"
  MMW_INVESTIGATE_RUN_LOCK=""
}

write_job_meta() {
  local file="$1" kind="$2" agent="$3" prompt="$4"
  local tmp
  tmp="$(mktemp "$(dirname "$file")/.meta.XXXXXX")" || return 1
  jq -n --arg kind "$kind" --arg agent "$agent" --arg prompt "$prompt" \
    --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{kind:$kind,agent:$agent,prompt_file:$prompt,status:"dispatched",attempt:1,
      result_file:null,validation_error:null,created_at:$at,updated_at:$at}' \
    >"$tmp" && mv "$tmp" "$file"
}

archive_job_attempt() {
  local meta="$1" dir attempt archive result
  dir="$(dirname "$meta")"
  attempt="$(jq -r '.attempt // 1' "$meta")"
  printf -v archive '%s/attempts/%03d' "$dir" "$attempt"
  mkdir -p "$archive"
  cp "$meta" "$archive/meta.json"
  result="$(jq -r '.result_file // empty' "$meta")"
  if [ -n "$result" ] && [ -f "$result" ]; then mv "$result" "$archive/result.json"; fi
  return 0
}

topic_prompt() {
  local mode="$1" angle="$2" question="$3" skill="$4" repo="$5"
  cat <<PROMPT
你只调查一个 topic，只摆证据，不选方案、不改文件。
mode=$mode
angle=$angle
question=$question
skill=${skill:-none}
repoRoot=$repo

内部调查只在 repoRoot 下用 read/grep/find/ls 取证；定位 bug 根因需要复现时可用 bash 跑只读诊断、目标测试或复现命令，禁止安装依赖、改文件、commit。执行前后都核对 \`git status --short\`，发现 tracked 改动立即停止并写入 gaps。每条 locator 必须是 file:line。
外部调查不读仓库，经 bash 用 \`curl\` 等只读网络命令取证，每条 locator 必须是已打开核验的 URL。
查不清写入 gaps，不得编造。只返回一个紧凑 JSON 对象，不加 Markdown fence 或解释：
{"topic":"<angle>","findings":[{"claim":"<事实>","locator":"<file:line或URL>","confidence":"high|medium|low"}],"summary":"<只陈述现状>","gaps":["<缺口>"]}
PROMPT
}

# 工人最终消息由协调者 submit 交回;要求它整体就是一个 JSON 对象。
validate_topic() {
  local meta="$1" out="$2" result tmp
  result="$(jq -r '.result_file // empty' "$meta")"
  [ -s "$result" ] || return 1
  tmp="$(mktemp "$(dirname "$out")/.topic.XXXXXX")" || return 1
  if ! jq -e '
      type=="object"
      and (.topic|type=="string")
      and (.summary|type=="string")
      and (.findings|type=="array")
      and (all(.findings[]; type=="object"
        and ((keys_unsorted | sort)==(["claim","confidence","locator"] | sort))
        and (.claim|type=="string")
        and (.locator|type=="string")
        and (.confidence=="high" or .confidence=="medium" or .confidence=="low")))
      and (.gaps|type=="array")
      and (all(.gaps[]; type=="string"))
      and ((keys_unsorted | sort)==(["findings","gaps","summary","topic"] | sort))
    ' "$result" >/dev/null 2>&1; then
    rm -f "$tmp"
    return 1
  fi
  jq --arg mode "$(jq -r '.mode' "$meta")" '
    def locator_ok:
      if $mode=="internal"
      then test("^.+:[0-9]+(-[0-9]+)?$")
      else test("^https?://")
      end;
    . as $topic
    | .findings |= map(select((.locator|locator_ok) and .confidence!="low"))
    | . + {mode:$mode,dropped: ($topic.findings
        | map(select((.locator|locator_ok|not) or .confidence=="low")))}
  ' "$result" >"$tmp" 2>/dev/null \
    && jq -e . "$tmp" >/dev/null 2>&1 \
    && mv "$tmp" "$out" \
    || { rm -f "$tmp"; return 1; }
}

validate_report() {
  local meta="$1" out="$2" result tmp
  result="$(jq -r '.result_file // empty' "$meta")"
  [ -s "$result" ] || return 1
  tmp="$(mktemp "$(dirname "$out")/.report.XXXXXX")" || return 1
  if ! jq -e '
      type=="object"
      and (.markdown|type=="string" and length>0)
      and (.open_questions|type=="array")
      and (all(.open_questions[]; type=="string"))
      and (.spinoff_candidates|type=="array")
      and (all(.spinoff_candidates[]; type=="object"
        and ((keys_unsorted | sort)==(["finding","tag"] | sort))
        and (.tag=="bug" or .tag=="optimize" or .tag=="out-of-scope" or .tag=="needs-evaluation")
        and (.finding|type=="string")))
      and ((keys_unsorted | sort)==(["markdown","open_questions","spinoff_candidates"] | sort))
    ' "$result" >/dev/null 2>&1; then
    rm -f "$tmp"
    return 1
  fi
  jq '.' "$result" >"$tmp" 2>/dev/null \
    && mv "$tmp" "$out" \
    || { rm -f "$tmp"; return 1; }
}

build_synth_prompt() {
  local evidence="$1" prompt="$2"
  cat >"$prompt" <<PROMPT
把下面各 topic 已通过机器校验的证据综合成一份报告。跨 topic 去重，保留出处，只陈述现状，不替 design 选方案。只返回一个紧凑 JSON 对象，不加 Markdown fence 或解释：
{"markdown":"<带引用的 Markdown 现状报告>","open_questions":["<缺口>"],"spinoff_candidates":[{"tag":"bug|optimize|out-of-scope|needs-evaluation","finding":"<旁路线索>"}]}

证据：
$(cat "$evidence")
PROMPT
}

print_topic_dispatch() {
  local root="$1" run="$2" count="$3" i angle prompt
  echo "DISPATCH=单条消息并行派 $count 个 Agent(subagent_type=$TOPIC_AGENT,run_in_background=true),每个 prompt=对应 PROMPT_FILE 全文;工人最终消息是一个紧凑 JSON,原样存临时文件后逐个 submit 交回过闸。"
  for ((i=0; i<count; i++)); do
    angle="$(jq -r ".[$i].angle" "$root/topics.json")"
    printf -v prompt '%s/topics/%03d/prompt.md' "$root" "$i"
    echo "TOPIC=$i ANGLE=$angle PROMPT_FILE=$prompt"
  done
  echo "SUBMIT=mmw investigate submit --run $run --topic <i> --file <工人 JSON 文件>"
  echo "NEXT=全部 submit 后跑 mmw investigate status --run $run"
}

cmd_start() {
  local direction="" topics="" run="" top root staging start_lock normalized i count
  local parent
  while [ $# -gt 0 ]; do
    case "$1" in
      --direction) direction="$2"; shift 2 ;;
      --topics) topics="$2"; shift 2 ;;
      --run) run="$2"; shift 2 ;;
      *) die "未知参数:$1" ;;
    esac
  done
  case "$direction" in internal|external|both) ;; *) die "--direction 只能 internal|external|both" ;; esac
  [ -f "$topics" ] || die "--topics JSON 文件不存在:$topics"
  [ -n "$run" ] || die "--run 必填"
  jq -e 'type=="array" and length>0 and all(.[];
    type=="object" and (.angle|type=="string" and length>0)
    and (.question|type=="string" and length>0)
    and ((.skill // "")|type=="string")
    and ((.mode // "")|type=="string"))' "$topics" >/dev/null \
    || die "topics 必须是非空 [{angle,question,skill?,mode?}]"
  if [ "$direction" = both ]; then
    jq -e 'all(.[]; .mode=="internal" or .mode=="external")' "$topics" >/dev/null \
      || die "direction=both 时每个 topic 必须给 mode"
  fi

  top="$(repo_top)"
  root="$(run_root "$run")"
  parent="$(dirname "$root")"
  mkdir -p "$parent"
  start_lock="$parent/.${run}.start-lock"
  acquire_lock_path "$start_lock"
  MMW_INVESTIGATE_START_LOCK="$start_lock"
  [ ! -e "$root" ] || die "investigate run 已存在:$run"
  staging="$parent/.${run}.start.$$"
  mkdir "$staging"
  MMW_INVESTIGATE_STAGING="$staging"
  mkdir "$staging/topics"

  normalized="$staging/topics.json"
  if [ "$direction" = both ]; then
    jq '.' "$topics" >"$normalized"
  else
    jq --arg mode "$direction" 'map(.mode=$mode)' "$topics" >"$normalized"
  fi

  jq -n --arg run "$run" --arg direction "$direction" --arg topics "$root/topics.json" \
    --arg topic_agent "$TOPIC_AGENT" --arg synth_agent "$SYNTH_AGENT" \
    --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{run:$run,direction:$direction,topics_file:$topics,status:"running",
      topic_agent:$topic_agent,synth_agent:$synth_agent,
      report_file:null,created_at:$at,updated_at:$at}' >"$staging/run.json"

  count="$(jq 'length' "$normalized")"
  for ((i=0; i<count; i++)); do
    local dir mode angle question skill prompt meta final_prompt
    printf -v dir '%s/topics/%03d' "$staging" "$i"
    mkdir -p "$dir"
    mode="$(jq -r ".[$i].mode" "$normalized")"
    angle="$(jq -r ".[$i].angle" "$normalized")"
    question="$(jq -r ".[$i].question" "$normalized")"
    skill="$(jq -r ".[$i].skill // empty" "$normalized")"
    prompt="$dir/prompt.md"
    meta="$dir/meta.json"
    printf -v final_prompt '%s/topics/%03d/prompt.md' "$root" "$i"
    topic_prompt "$mode" "$angle" "$question" "$skill" "$top" >"$prompt"
    write_job_meta "$meta" topic "$TOPIC_AGENT" "$final_prompt"
    jq --arg mode "$mode" --arg angle "$angle" --arg question "$question" \
      '. + {mode:$mode,angle:$angle,question:$question}' \
      "$meta" >"$meta.tmp" && mv "$meta.tmp" "$meta"
  done
  mv "$staging" "$root"
  MMW_INVESTIGATE_STAGING=""
  release_start_lock
  echo "INVESTIGATE_STARTED run=$run topics=$count"
  print_topic_dispatch "$root" "$run" "$count"
}

cmd_submit() {
  local run="" topic="" synthesis=0 file="" root meta dir out
  while [ $# -gt 0 ]; do case "$1" in
    --run) run="$2"; shift 2 ;;
    --topic) topic="$2"; shift 2 ;;
    --synthesis) synthesis=1; shift ;;
    --file) file="$2"; shift 2 ;;
    *) die "未知参数:$1" ;;
  esac; done
  [ -n "$run" ] || die "--run 必填"
  [ -f "$file" ] || die "--file 不存在:$file"
  root="$(run_root "$run")"
  [ -f "$root/run.json" ] || die "investigate run 不存在:$run"
  acquire_run_lock "$root"
  if [ "$synthesis" = 1 ]; then
    dir="$root/synthesis"
    meta="$dir/meta.json"
    [ -f "$meta" ] || die "synthesis 尚未派发;先跑 investigate status"
  else
    [[ "$topic" =~ ^[0-9]+$ ]] || die "--topic 必须是编号"
    printf -v dir '%s/topics/%03d' "$root" "$topic"
    meta="$dir/meta.json"
    [ -f "$meta" ] || die "topic 不存在:$topic"
  fi
  cp "$file" "$dir/result.json"
  mmw_atomic_update "$meta" --arg result "$dir/result.json" \
    --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '.result_file=$result | .updated_at=$at' || die "无法登记结果文件"
  if [ "$synthesis" = 1 ]; then
    echo "SUBMIT=synthesis 已收;跑 mmw investigate status --run $run 校验并汇编"
  else
    if validate_topic "$meta" "$dir/validated.json"; then
      mmw_atomic_update "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        '.status="validated" | .validation_error=null | .updated_at=$at'
      echo "SUBMIT=topic $topic VALIDATED"
    else
      mmw_atomic_update "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        '.status="failed" | .validation_error="topic result schema invalid" | .updated_at=$at'
      echo "SUBMIT=topic $topic INVALID(schema 未过);修 prompt 或重派后经 resume 重交" >&2
      release_run_lock
      return 1
    fi
  fi
  release_run_lock
}

prepare_synthesis() {
  local root="$1" run="$2" synth_dir evidence prompt meta
  synth_dir="$root/synthesis"
  mkdir -p "$synth_dir"
  evidence="$synth_dir/evidence.json"
  jq -s '.' "$root"/topics/*/validated.json >"$evidence"
  prompt="$synth_dir/prompt.md"
  build_synth_prompt "$evidence" "$prompt"
  meta="$synth_dir/meta.json"
  write_job_meta "$meta" synthesis "$SYNTH_AGENT" "$prompt"
  mmw_atomic_update "$root/run.json" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '.status="synthesizing" | .updated_at=$at'
  echo "DISPATCH=派 1 个 Agent(subagent_type=$SYNTH_AGENT,run_in_background=true,prompt=$prompt 全文);最终消息是一个紧凑 JSON,存临时文件后 submit --synthesis 交回。"
  echo "SUBMIT=mmw investigate submit --run $run --synthesis --file <JSON 文件>"
}

cmd_status() {
  local run="" root meta pending=0 failed=0 validated=0 total=0 i
  while [ $# -gt 0 ]; do case "$1" in --run) run="$2"; shift 2 ;; *) die "未知参数:$1" ;; esac; done
  [ -n "$run" ] || die "--run 必填"
  root="$(run_root "$run")"
  [ -f "$root/run.json" ] || die "investigate run 不存在:$run"
  acquire_run_lock "$root"

  total="$(jq 'length' "$root/topics.json")"
  for ((i=0; i<total; i++)); do
    printf -v meta '%s/topics/%03d/meta.json' "$root" "$i"
    if [ ! -f "$meta" ]; then
      failed=$((failed+1))
      continue
    fi
    case "$(jq -r '.status' "$meta")" in
      validated) validated=$((validated+1)) ;;
      failed) failed=$((failed+1)) ;;
      *) pending=$((pending+1)) ;;
    esac
  done

  if [ "$failed" -gt 0 ]; then
    mmw_atomic_update "$root/run.json" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '.status="failed" | .updated_at=$at'
    echo "INVESTIGATE_STATUS=FAILED validated=$validated failed=$failed pending=$pending total=$total"
    echo "NEXT=mmw investigate resume --run $run"
    release_run_lock
    return 1
  fi
  if [ "$pending" -gt 0 ]; then
    echo "INVESTIGATE_STATUS=PENDING validated=$validated pending=$pending total=$total"
    echo "NEXT=等在飞工人回执后 submit;缺派发的 topic 按 start 打印的 PROMPT_FILE 派"
    release_run_lock
    return 0
  fi

  local synth_meta="$root/synthesis/meta.json" report="$root/result.json"
  local synth_report="$root/synthesis/report.json" tmp
  if [ -f "$report" ]; then
    mmw_atomic_update "$root/run.json" --arg report "$report" \
      --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '.status="completed" | .report_file=$report | .updated_at=$at'
    echo "INVESTIGATE_STATUS=COMPLETED"
    echo "REPORT_FILE=$report"
    release_run_lock
    return 0
  fi
  if [ ! -f "$synth_meta" ]; then
    prepare_synthesis "$root" "$run"
    echo "INVESTIGATE_STATUS=SYNTHESIZING"
    release_run_lock
    return 0
  fi
  if [ "$(jq -r '.result_file // empty' "$synth_meta")" = "" ]; then
    echo "INVESTIGATE_STATUS=SYNTHESIZING"
    echo "NEXT=synthesis 工人回执后 submit --synthesis 交回"
    release_run_lock
    return 0
  fi

  if validate_report "$synth_meta" "$synth_report"; then
    tmp="$(mktemp "$root/.result.XXXXXX")" || die "无法创建 investigate result"
    jq -n --slurpfile topics "$root/synthesis/evidence.json" \
      --slurpfile report "$synth_report" \
      '{topics:$topics[0],report:$report[0]}' >"$tmp" \
      && jq -e . "$tmp" >/dev/null 2>&1 \
      && mv "$tmp" "$report" \
      || { rm -f "$tmp"; die "无法组装 investigate result"; }
    mmw_atomic_update "$root/run.json" --arg report "$report" \
      --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '.status="completed" | .report_file=$report | .updated_at=$at'
    echo "INVESTIGATE_STATUS=COMPLETED"
    echo "REPORT_FILE=$report"
    release_run_lock
    return 0
  fi
  mmw_atomic_update "$synth_meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '.status="failed" | .validation_error="report result schema invalid" | .updated_at=$at'
  mmw_atomic_update "$root/run.json" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '.status="failed" | .updated_at=$at'
  echo "INVESTIGATE_STATUS=FAILED synthesis"
  echo "NEXT=mmw investigate resume --run $run"
  release_run_lock
  return 1
}

cmd_resume() {
  local run="" root meta retried=0 i total angle prompt
  while [ $# -gt 0 ]; do case "$1" in --run) run="$2"; shift 2 ;; *) die "未知参数:$1" ;; esac; done
  [ -n "$run" ] || die "--run 必填"
  root="$(run_root "$run")"
  [ -f "$root/run.json" ] || die "investigate run 不存在:$run"
  acquire_run_lock "$root"

  total="$(jq 'length' "$root/topics.json")"
  for ((i=0; i<total; i++)); do
    printf -v meta '%s/topics/%03d/meta.json' "$root" "$i"
    [ -f "$meta" ] || continue
    [ -f "$(dirname "$meta")/validated.json" ] && continue
    [ "$(jq -r '.status' "$meta")" = failed ] || continue
    archive_job_attempt "$meta"
    mmw_atomic_update "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '.status="dispatched" | .result_file=null
       | .validation_error=null | .attempt=((.attempt // 1)+1) | .updated_at=$at'
    angle="$(jq -r '.angle' "$meta")"
    prompt="$(jq -r '.prompt_file' "$meta")"
    echo "REDISPATCH=topic $i ANGLE=$angle:Agent(subagent_type=$TOPIC_AGENT,run_in_background=true,prompt=$prompt 全文);回执 JSON 经 submit --topic $i 交回"
    retried=$((retried+1))
  done

  meta="$root/synthesis/meta.json"
  if [ "$retried" -eq 0 ] && [ -f "$meta" ] && [ ! -f "$root/result.json" ]; then
    archive_job_attempt "$meta"
    mmw_atomic_update "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '.status="dispatched" | .result_file=null
       | .validation_error=null | .attempt=((.attempt // 1)+1) | .updated_at=$at'
    echo "REDISPATCH=synthesis:Agent(subagent_type=$SYNTH_AGENT,run_in_background=true,prompt=$root/synthesis/prompt.md 全文);回执 JSON 经 submit --synthesis 交回"
    retried=1
  fi
  [ "$retried" -gt 0 ] || die "没有可恢复的失败 job"
  mmw_atomic_update "$root/run.json" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '.status="running" | .updated_at=$at'
  echo "INVESTIGATE_RESUMED jobs=$retried"
  echo "NEXT=重派后回执经 submit 交回,再跑 mmw investigate status --run $run"
}

cmd_result() {
  local run="" root
  while [ $# -gt 0 ]; do case "$1" in --run) run="$2"; shift 2 ;; *) die "未知参数:$1" ;; esac; done
  [ -n "$run" ] || die "--run 必填"
  root="$(run_root "$run")"
  [ -f "$root/result.json" ] || die "报告尚未完成，先 investigate status"
  jq -r '.report.markdown' "$root/result.json"
}

case "${1:-}" in
  start) shift; cmd_start "$@" ;;
  submit) shift; cmd_submit "$@" ;;
  status) shift; cmd_status "$@" ;;
  resume) shift; cmd_resume "$@" ;;
  result) shift; cmd_result "$@" ;;
  *) die "用法: investigate.sh start|submit|status|resume|result ..." ;;
esac
