#!/usr/bin/env bash
# Droid 原生 investigate fan-out + schema 校验 + synthesis。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"
# shellcheck source=lib/droid-exec.sh
. "$SCRIPT_DIR/lib/droid-exec.sh"

TOPIC_MODEL="${DROID_INVESTIGATE_MODEL:-custom:GPT-5.6-Sol-[Codex]-0}"
TOPIC_EFFORT="${DROID_INVESTIGATE_EFFORT:-medium}"
SYNTH_MODEL="${DROID_INVESTIGATE_SYNTH_MODEL:-custom:GPT-5.6-Terra-[Codex]-0}"
SYNTH_EFFORT="${DROID_INVESTIGATE_SYNTH_EFFORT:-high}"
ALLOW_INTERNAL="read-cli,grep_tool_cli,glob-search-cli,ls-cli,execute-cli,skill"
ALLOW_EXTERNAL="web_search,fetch_url,mcp_context7_query-docs,mcp_context7_resolve-library-id,skill"
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
    */.factory/multi-model-workflow/investigate-runs/.*.start.[0-9]*)
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
      die "investigate run 正被另一个 status/resume 更新:$owner"
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
  local file="$1" kind="$2" model="$3" effort="$4" cwd="$5" prompt="$6" system="$7"
  local tmp
  tmp="$(mktemp "$(dirname "$file")/.meta.XXXXXX")" || return 1
  jq -n --arg kind "$kind" --arg model "$model" --arg effort "$effort" \
    --arg cwd "$cwd" --arg prompt "$prompt" --arg system "$system" \
    --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{kind:$kind,model:$model,reasoning_effort:$effort,cwd:$cwd,prompt_file:$prompt,
      system_prompt_file:$system,status:"prepared",attempt:1,pid:null,session_id:null,
      result_file:null,log_file:null,validation_error:null,created_at:$at,updated_at:$at}' \
    >"$tmp" && mv "$tmp" "$file"
}

archive_job_attempt() {
  local meta="$1" dir attempt archive result log
  dir="$(dirname "$meta")"
  attempt="$(jq -r '.attempt // 1' "$meta")"
  printf -v archive '%s/attempts/%03d' "$dir" "$attempt"
  mkdir -p "$archive"
  cp "$meta" "$archive/meta.json"
  result="$(jq -r '.result_file // empty' "$meta")"
  log="$(jq -r '.log_file // empty' "$meta")"
  if [ -n "$result" ] && [ -f "$result" ]; then mv "$result" "$archive/result.json"; fi
  if [ -n "$log" ] && [ -f "$log" ]; then mv "$log" "$archive/run.log"; fi
  return 0
}

launch_job() {
  local meta="$1" disabled="$2"
  mmw_droid_launch "$meta" \
    "$(jq -r .prompt_file "$meta")" \
    "$(jq -r .cwd "$meta")" \
    "$(jq -r .model "$meta")" \
    "$(jq -r .reasoning_effort "$meta")" \
    "$(jq -r .system_prompt_file "$meta")" \
    "" low "$disabled" || die "Droid investigate job 启动失败:$meta"
}

topic_prompt() {
  local mode="$1" angle="$2" question="$3" skill="$4" repo="$5"
  cat <<PROMPT
你只调查一个 topic，只摆证据，不选方案、不改文件。
mode=$mode
angle=$angle
question=$question
skill=${skill:-none}(非 none 时先用 Read 读 ~/.factory/skills/$skill/SKILL.md 按其指引投查,引用不照抄;文件不存在=缺装,写入 gaps 并注明角度未应用,不凭记忆编方法论)
repoRoot=$repo

内部调查只在 repoRoot 下用 Read/Grep/Glob/LS 取证；定位 bug 根因需要复现时可用 Execute 跑只读诊断、目标测试或复现命令，禁止安装依赖、改文件、commit。执行前后都核对 `git status --short`，发现 tracked 改动立即停止并写入 gaps。每条 locator 必须是 file:line。
外部调查用 WebSearch/FetchUrl/Context7 取证，每条 locator 必须是已打开核验的 URL。
查不清写入 gaps，不得编造。只返回一个紧凑 JSON 对象，不加 Markdown fence 或解释：
{"topic":"<angle>","findings":[{"claim":"<事实>","locator":"<file:line或URL>","confidence":"high|medium|low"}],"summary":"<只陈述现状>","gaps":["<缺口>"]}
PROMPT
}

validate_topic() {
  local meta="$1" out="$2" result tmp
  result="$(jq -r '.result_file // empty' "$meta")"
  [ -s "$result" ] || return 1
  tmp="$(mktemp "$(dirname "$out")/.topic.XXXXXX")" || return 1
  if ! jq -e '
      .result | fromjson
      | type=="object"
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
    .result | fromjson
    | . as $topic
    | .findings |= map(select((.locator|locator_ok) and .confidence!="low"))
    | . + {mode:$mode,dropped: ($topic.findings
        | map(select((.locator|locator_ok|not) or .confidence=="low")))}
  ' "$result" >"$tmp" \
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
      .result | fromjson
      | type=="object"
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
  jq '.result | fromjson' "$result" >"$tmp" \
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

cmd_start() {
  local direction="" topics="" run="" top root staging start_lock plugin topic_system disabled normalized i count
  local topic_inventory synth_inventory parent
  local internal_disabled external_disabled synth_disabled
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
  plugin="$(mmw_plugin_root)"
  topic_inventory="$staging/topic-tool-inventory.json"
  synth_inventory="$staging/synthesis-tool-inventory.json"
  mmw_droid_load_tool_inventory "$topic_inventory" "$TOPIC_MODEL" \
    || die "无法读取 topic Droid tool inventory"
  mmw_droid_load_tool_inventory "$synth_inventory" "$SYNTH_MODEL" \
    || die "无法读取 synthesis Droid tool inventory"
  internal_disabled="$(mmw_droid_disable_all_except "$ALLOW_INTERNAL" "$topic_inventory")"
  external_disabled="$(mmw_droid_disable_all_except "$ALLOW_EXTERNAL" "$topic_inventory")"
  synth_disabled="$(mmw_droid_disable_all_except "" "$synth_inventory")"
  topic_system="$staging/topic-system.md"
  mmw_droid_render_prompt "$plugin/droids/investigate-topic.md" "$topic_system" \
    || die "investigate-topic droid prompt 无效"

  normalized="$staging/topics.json"
  if [ "$direction" = both ]; then
    jq '.' "$topics" >"$normalized"
  else
    jq --arg mode "$direction" 'map(.mode=$mode)' "$topics" >"$normalized"
  fi

  jq -n --arg run "$run" --arg direction "$direction" --arg topics "$root/topics.json" \
    --arg internal_disabled "$internal_disabled" --arg external_disabled "$external_disabled" \
    --arg synth_disabled "$synth_disabled" \
    --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{run:$run,direction:$direction,topics_file:$topics,status:"running",
      internal_disabled_tools:$internal_disabled,external_disabled_tools:$external_disabled,
      synthesis_disabled_tools:$synth_disabled,
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
    write_job_meta "$meta" topic "$TOPIC_MODEL" "$TOPIC_EFFORT" "$top" \
      "$final_prompt" "$root/topic-system.md"
    if [ "$mode" = internal ]; then disabled="$internal_disabled"; else disabled="$external_disabled"; fi
    jq --arg mode "$mode" --arg angle "$angle" --arg question "$question" \
      --arg disabled "$disabled" \
      '. + {mode:$mode,angle:$angle,question:$question,disabled_tools:$disabled}' \
      "$meta" >"$meta.tmp" && mv "$meta.tmp" "$meta"
  done
  printf '%s\n' "$$" >"$staging/.run-lock"
  mv "$staging" "$root"
  MMW_INVESTIGATE_STAGING=""
  MMW_INVESTIGATE_RUN_LOCK="$root/.run-lock"
  release_start_lock
  for ((i=0; i<count; i++)); do
    printf -v meta '%s/topics/%03d/meta.json' "$root" "$i"
    launch_job "$meta" "$(jq -r .disabled_tools "$meta")"
  done
  release_run_lock
  echo "INVESTIGATE_STARTED run=$run topics=$count"
  echo "NEXT=mmw investigate status --run $run"
}

launch_synthesis() {
  local root="$1" top plugin synth_dir evidence prompt system meta
  top="$(repo_top)"
  plugin="$(mmw_plugin_root)"
  synth_dir="$root/synthesis"
  mkdir -p "$synth_dir"
  evidence="$synth_dir/evidence.json"
  jq -s '.' "$root"/topics/*/validated.json >"$evidence"
  prompt="$synth_dir/prompt.md"
  build_synth_prompt "$evidence" "$prompt"
  system="$synth_dir/system-prompt.md"
  mmw_droid_render_prompt "$plugin/droids/investigate-synthesizer.md" "$system" \
    || die "investigate-synthesizer droid prompt 无效"
  meta="$synth_dir/meta.json"
  write_job_meta "$meta" synthesis "$SYNTH_MODEL" "$SYNTH_EFFORT" "$top" "$prompt" "$system"
  launch_job "$meta" "$(jq -r .synthesis_disabled_tools "$root/run.json")"
  mmw_droid_atomic_update "$root/run.json" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '.status="synthesizing" | .updated_at=$at'
}

cmd_status() {
  local run="" root meta state running=0 failed=0 validated=0 total=0 i
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
    if [ -f "$(dirname "$meta")/validated.json" ]; then
      validated=$((validated+1))
      continue
    fi
    state="$(mmw_droid_refresh "$meta" 2>/dev/null || true)"
    case "$state" in
      RUNNING) running=$((running+1)) ;;
      COMPLETED)
        if validate_topic "$meta" "$(dirname "$meta")/validated.json"; then
          mmw_droid_atomic_update "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
            '.status="validated" | .validation_error=null | .updated_at=$at'
          validated=$((validated+1))
        else
          mmw_droid_atomic_update "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
            '.status="failed" | .validation_error="topic result schema invalid" | .updated_at=$at'
          failed=$((failed+1))
        fi
        ;;
      *) failed=$((failed+1)) ;;
    esac
  done

  if [ "$running" -gt 0 ]; then
    echo "INVESTIGATE_STATUS=RUNNING validated=$validated running=$running failed=$failed total=$total"
    return 0
  fi
  if [ "$failed" -gt 0 ] || [ "$validated" -ne "$total" ]; then
    mmw_droid_atomic_update "$root/run.json" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '.status="failed" | .updated_at=$at'
    echo "INVESTIGATE_STATUS=FAILED validated=$validated failed=$failed total=$total"
    echo "NEXT=mmw investigate resume --run $run"
    return 1
  fi

  local synth_meta="$root/synthesis/meta.json" report="$root/result.json"
  local synth_report="$root/synthesis/report.json" tmp
  if [ -f "$report" ]; then
    mmw_droid_atomic_update "$root/run.json" --arg report "$report" \
      --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '.status="completed" | .report_file=$report | .updated_at=$at'
    echo "INVESTIGATE_STATUS=COMPLETED"
    echo "REPORT_FILE=$report"
    return 0
  fi
  if [ ! -f "$synth_meta" ]; then
    launch_synthesis "$root"
    echo "INVESTIGATE_STATUS=SYNTHESIZING"
    echo "NEXT=mmw investigate status --run $run"
    return 0
  fi

  state="$(mmw_droid_refresh "$synth_meta" 2>/dev/null || true)"
  case "$state" in
    RUNNING)
      echo "INVESTIGATE_STATUS=SYNTHESIZING"
      return 0
      ;;
    COMPLETED)
      if validate_report "$synth_meta" "$synth_report"; then
        tmp="$(mktemp "$root/.result.XXXXXX")" || die "无法创建 investigate result"
        jq -n --slurpfile topics "$root/synthesis/evidence.json" \
          --slurpfile report "$synth_report" \
          '{topics:$topics[0],report:$report[0]}' >"$tmp" \
          && jq -e . "$tmp" >/dev/null 2>&1 \
          && mv "$tmp" "$report" \
          || { rm -f "$tmp"; die "无法组装 investigate result"; }
        mmw_droid_atomic_update "$root/run.json" --arg report "$report" \
          --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
          '.status="completed" | .report_file=$report | .updated_at=$at'
        echo "INVESTIGATE_STATUS=COMPLETED"
        echo "REPORT_FILE=$report"
        return 0
      fi
      ;;
  esac
  if [ "$state" = COMPLETED ]; then
    mmw_droid_atomic_update "$synth_meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '.status="failed" | .validation_error="report result schema invalid" | .updated_at=$at'
  fi
  mmw_droid_atomic_update "$root/run.json" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '.status="failed" | .updated_at=$at'
  echo "INVESTIGATE_STATUS=FAILED synthesis"
  echo "NEXT=mmw investigate resume --run $run"
  return 1
}

cmd_resume() {
  local run="" root meta state retried=0
  while [ $# -gt 0 ]; do case "$1" in --run) run="$2"; shift 2 ;; *) die "未知参数:$1" ;; esac; done
  [ -n "$run" ] || die "--run 必填"
  root="$(run_root "$run")"
  [ -f "$root/run.json" ] || die "investigate run 不存在:$run"
  acquire_run_lock "$root"

  for meta in "$root"/topics/*/meta.json; do
    [ -f "$meta" ] || continue
    [ -f "$(dirname "$meta")/validated.json" ] && continue
    state="$(mmw_droid_refresh "$meta" 2>/dev/null || true)"
    [ "$state" = RUNNING ] && continue
    archive_job_attempt "$meta"
    mmw_droid_atomic_update "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '.status="prepared" | .pid=null | .result_file=null | .log_file=null
       | .validation_error=null | .attempt=((.attempt // 1)+1) | .updated_at=$at'
    launch_job "$meta" "$(jq -r .disabled_tools "$meta")"
    retried=$((retried+1))
  done

  meta="$root/synthesis/meta.json"
  if [ "$retried" -eq 0 ] && [ -f "$meta" ] && [ ! -f "$root/result.json" ]; then
    state="$(mmw_droid_refresh "$meta" 2>/dev/null || true)"
    [ "$state" = RUNNING ] || {
      archive_job_attempt "$meta"
      mmw_droid_atomic_update "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        '.status="prepared" | .pid=null | .result_file=null | .log_file=null
         | .validation_error=null | .attempt=((.attempt // 1)+1) | .updated_at=$at'
      launch_job "$meta" "$(jq -r .synthesis_disabled_tools "$root/run.json")"
      retried=1
    }
  fi
  [ "$retried" -gt 0 ] || die "没有可恢复的失败 job"
  mmw_droid_atomic_update "$root/run.json" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '.status="running" | .updated_at=$at'
  echo "INVESTIGATE_RESUMED jobs=$retried"
  echo "NEXT=mmw investigate status --run $run"
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
  status) shift; cmd_status "$@" ;;
  resume) shift; cmd_resume "$@" ;;
  result) shift; cmd_result "$@" ;;
  *) die "用法: investigate.sh start|status|resume|result ..." ;;
esac
