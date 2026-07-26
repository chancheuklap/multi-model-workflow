#!/usr/bin/env bash
# Cursor Task investigate fan-out：准备 prompt/账本、打印 DISPATCH、校验 result.json。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"
# shellcheck source=lib/retrieval-candidates.sh
. "$SCRIPT_DIR/lib/retrieval-candidates.sh"

TOPIC_SUBAGENT="${CURSOR_INVESTIGATE_TOPIC_AGENT:-investigate-topic}"
SYNTH_SUBAGENT="${CURSOR_INVESTIGATE_SYNTH_AGENT:-investigate-synthesizer}"
TOPIC_MODEL="${CURSOR_INVESTIGATE_TOPIC_MODEL:-composer-2.5}"
SYNTH_MODEL="${CURSOR_INVESTIGATE_SYNTH_MODEL:-grok-4.5}"
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
  local sd
  sd="$(mmw_state_subdir)"
  case "$staging" in
    */"$sd"/investigate-runs/.*.start.[0-9]*)
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

print_task_dispatch() {
  local subagent="$1" prompt_path="$2" model="$3"
  echo "DISPATCH=Task({subagent_type:\"$subagent\", prompt:\"$prompt_path\", model:\"$model\", background:true})"
}

write_job_meta() {
  local file="$1" kind="$2" subagent="$3" model="$4" cwd="$5" prompt="$6"
  local tmp result_path
  result_path="$(dirname "$prompt")/result.json"
  tmp="$(mktemp "$(dirname "$file")/.meta.XXXXXX")" || return 1
  jq -n --arg kind "$kind" --arg subagent "$subagent" --arg model "$model" \
    --arg cwd "$cwd" --arg prompt "$prompt" --arg result "$result_path" \
    --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{kind:$kind,subagent_type:$subagent,model:$model,cwd:$cwd,prompt_file:$prompt,
      status:"prepared",attempt:1,result_file:$result,validation_error:null,
      backend:"cursor-task",created_at:$at,updated_at:$at}' \
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
  local mode="$1" angle="$2" question="$3" skill="$4" repo="$5" candidates_file="$6" plugin
  plugin="$(mmw_plugin_root)"
  cat <<PROMPT
你只调查一个 topic，只摆证据，不选方案、不改文件。
mode=$mode
angle=$angle
question=$question
skill=${skill:-none}(非 none 时先用 Read 读 ~/.cursor/skills/$skill/SKILL.md；若无则读 $plugin/skills/$skill/SKILL.md。按其指引投查,引用不照抄;文件不存在=缺装,写入 gaps 并注明角度未应用,不凭记忆编方法论)
repoRoot=$repo

上游结构候选(仅候选,不代表本 topic worker 调过工具):
PROMPT
  if [ -s "$candidates_file" ]; then
    printf '```json\n'; jq -c '.' "$candidates_file"; printf '```\n'
    cat <<'PROMPT2'
内部 topic 必须逐 locator 回 repoRoot 用 Read/Grep/Glob 亲验；Serena/graphify 候选来自上游，不代表 Cursor worker 能直接调用那些 MCP。Serena 对装饰器 endpoint 完整调用方、动态 await import() 解构引用存在已知盲区；unsupported/not_available/failed/空结果均须 fallback 到 Grep/Glob/Read 源码检索。summary/gaps 必须区分上游候选、worker 自己实际用的 Read/Grep/Glob/Shell、源码 locator 与 fallback_reason。

内部调查只在 repoRoot 下用 Read/Grep/Glob 取证；定位 bug 根因需要复现时可用 Shell 跑只读诊断、目标测试或复现命令，禁止安装依赖、改文件、commit。执行前后都核对 `git status --short`，发现 tracked 改动立即停止并写入 gaps。每条 locator 必须是 file:line。
PROMPT2
  else
    cat <<'PROMPT2'
内部调查只在 repoRoot 下用 Read/Grep/Glob 取证；定位 bug 根因需要复现时可用 Shell 跑只读诊断、目标测试或复现命令，禁止安装依赖、改文件、commit。执行前后都核对 `git status --short`，发现 tracked 改动立即停止并写入 gaps。每条 locator 必须是 file:line。
PROMPT2
  fi
  if [ "$mode" = external ]; then
    cat <<'PROMPT3'
外部调查用 Shell 只读网络命令或可用 MCP 文档搜索取证，每条 locator 必须是已打开核验的 URL。
PROMPT3
  fi
  cat <<'PROMPT4'
查不清写入 gaps，不得编造。把结果写入本 topic 目录的 result.json（紧凑 JSON 对象，不加 Markdown fence）。主线程 status 会读取该文件。只返回一个紧凑 JSON 对象，不加 Markdown fence 或解释：
{"topic":"<angle>","findings":[{"claim":"<事实>","locator":"<file:line或URL>","confidence":"high|medium|low"}],"summary":"<只陈述现状>","gaps":["<缺口>"]}
PROMPT4
}

validate_topic_payload() {
  local mode="$1" payload="$2" out="$3" tmp
  tmp="$(mktemp "$(dirname "$out")/.topic.XXXXXX")" || return 1
  if ! jq -n -e --argjson payload "$payload" '
      $payload
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
    ' >/dev/null 2>&1; then
    rm -f "$tmp"
    return 1
  fi
  jq -n --arg mode "$mode" --argjson payload "$payload" '
    def locator_ok:
      if $mode=="internal"
      then test("^.+:[0-9]+(-[0-9]+)?$")
      else test("^https?://")
      end;
    $payload
    | . as $topic
    | .findings |= map(select((.locator|locator_ok) and .confidence!="low"))
    | . + {mode:$mode,dropped: ($topic.findings
        | map(select((.locator|locator_ok|not) or .confidence=="low")))}
  ' >"$tmp" \
    && jq -e . "$tmp" >/dev/null 2>&1 \
    && mv "$tmp" "$out" \
    || { rm -f "$tmp"; return 1; }
}

validate_topic() {
  local meta="$1" out="$2" mode result payload dir
  dir="$(dirname "$meta")"
  mode="$(jq -r '.mode' "$meta")"
  result="$dir/result.json"
  [ -s "$result" ] || return 1
  if ! payload="$(jq -c . "$result" 2>/dev/null)"; then
    return 1
  fi
  validate_topic_payload "$mode" "$payload" "$out"
}

validate_report_payload() {
  local payload="$1" out="$2" tmp
  tmp="$(mktemp "$(dirname "$out")/.report.XXXXXX")" || return 1
  if ! jq -n -e --argjson payload "$payload" '
      $payload
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
    ' >/dev/null 2>&1; then
    rm -f "$tmp"
    return 1
  fi
  jq -n --argjson payload "$payload" '$payload' >"$tmp" \
    && mv "$tmp" "$out" \
    || { rm -f "$tmp"; return 1; }
}

validate_report() {
  local meta="$1" out="$2" result payload dir
  dir="$(dirname "$meta")"
  result="$dir/result.json"
  [ -s "$result" ] || return 1
  payload="$(jq -c . "$result" 2>/dev/null)" || return 1
  validate_report_payload "$payload" "$out"
}

build_synth_prompt() {
  local evidence="$1" prompt="$2" result_path="$3"
  cat >"$prompt" <<PROMPT
把下面各 topic 已通过机器校验的证据综合成一份报告。跨 topic 去重，保留出处，只陈述现状，不替 design 选方案。把结果写入 ${result_path}（紧凑 JSON，不加 Markdown fence）。主线程 status 会读取该文件。只返回一个紧凑 JSON 对象，不加 Markdown fence 或解释：
{"markdown":"<带引用的 Markdown 现状报告>","open_questions":["<缺口>"],"spinoff_candidates":[{"tag":"bug|optimize|out-of-scope|needs-evaluation","finding":"<旁路线索>"}]}

证据：
$(cat "$evidence")
PROMPT
}

cmd_start() {
  local direction="" topics="" run="" top root staging start_lock parent normalized i count
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
    and ((.mode // "")|type=="string")
    and ((.retrieval_candidates // []) | type=="array" and all(.[];
      type=="object"
      and ((keys | sort)==["fallback_reason","locators","query","status","summary","tool"])
      and (.tool=="serena" or .tool=="graphify")
      and (.query|type=="string")
      and (.status=="used" or .status=="not_available" or .status=="unsupported" or .status=="failed")
      and (.locators|type=="array") and all(.locators[]; type=="string")
      and (.summary|type=="string") and (.fallback_reason|type=="string"))))' "$topics" >/dev/null \
    || die "topics 必须是非空 [{angle,question,skill?,mode?,retrieval_candidates?}]，候选严格六字段"
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
    jq 'map(.retrieval_candidates //= [])' "$topics" >"$normalized"
  else
    jq --arg mode "$direction" 'map(.mode=$mode | .retrieval_candidates //= [])' "$topics" >"$normalized"
  fi

  jq -n --arg run "$run" --arg direction "$direction" --arg topics "$root/topics.json" \
    --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{run:$run,direction:$direction,topics_file:$topics,status:"running",
      backend:"cursor-task",report_file:null,created_at:$at,updated_at:$at}' >"$staging/run.json"

  count="$(jq 'length' "$normalized")"
  for ((i=0; i<count; i++)); do
    local dir mode angle question skill retrieval_candidates candidates_file prompt meta final_prompt
    printf -v dir '%s/topics/%03d' "$staging" "$i"
    mkdir -p "$dir"
    mode="$(jq -r ".[$i].mode" "$normalized")"
    angle="$(jq -r ".[$i].angle" "$normalized")"
    question="$(jq -r ".[$i].question" "$normalized")"
    skill="$(jq -r ".[$i].skill // empty" "$normalized")"
    retrieval_candidates="$(jq -c ".[$i].retrieval_candidates" "$normalized")"
    candidates_file="$dir/retrieval-candidates.json"
    printf '%s\n' "$retrieval_candidates" >"$candidates_file"
    prompt="$dir/prompt.md"
    meta="$dir/meta.json"
    printf -v final_prompt '%s/topics/%03d/prompt.md' "$root" "$i"
    topic_prompt "$mode" "$angle" "$question" "$skill" "$top" "$candidates_file" >"$prompt"
    write_job_meta "$meta" topic "$TOPIC_SUBAGENT" "$TOPIC_MODEL" "$top" "$final_prompt"
    jq --arg mode "$mode" --arg angle "$angle" --arg question "$question" \
      --argjson retrieval_candidates "$retrieval_candidates" \
      '. + {mode:$mode,angle:$angle,question:$question,retrieval_candidates:$retrieval_candidates}' \
      "$meta" >"$meta.tmp" && mv "$meta.tmp" "$meta"
  done

  mv "$staging" "$root"
  MMW_INVESTIGATE_STAGING=""
  release_start_lock

  echo "INVESTIGATE_STARTED run=$run topics=$count backend=cursor-task"
  for ((i=0; i<count; i++)); do
    printf -v meta '%s/topics/%03d/meta.json' "$root" "$i"
    print_task_dispatch "$TOPIC_SUBAGENT" "$(jq -r .prompt_file "$meta")" "$TOPIC_MODEL"
  done
  echo "NEXT=主线程派发上述 Task 后跑: mmw investigate status --run $run"
}

prepare_synthesis() {
  local root="$1" top synth_dir evidence prompt meta result_path
  top="$(repo_top)"
  synth_dir="$root/synthesis"
  mkdir -p "$synth_dir"
  evidence="$synth_dir/evidence.json"
  jq -s '.' "$root"/topics/*/validated.json >"$evidence"
  prompt="$synth_dir/prompt.md"
  result_path="$synth_dir/result.json"
  build_synth_prompt "$evidence" "$prompt" "$result_path"
  meta="$synth_dir/meta.json"
  write_job_meta "$meta" synthesis "$SYNTH_SUBAGENT" "$SYNTH_MODEL" "$top" "$prompt"
  mmw_atomic_update "$root/run.json" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '.status="synthesizing" | .updated_at=$at' \
    || die "无法更新 run 账本"
  print_task_dispatch "$SYNTH_SUBAGENT" "$prompt" "$SYNTH_MODEL"
}

refresh_topic_meta() {
  local meta="$1" dir status validated_out
  dir="$(dirname "$meta")"
  validated_out="$dir/validated.json"
  if [ -f "$validated_out" ]; then
    printf '%s' validated
    return 0
  fi
  status="$(jq -r '.status // "prepared"' "$meta")"
  if [ -s "$dir/result.json" ]; then
    if validate_topic "$meta" "$validated_out"; then
      mmw_atomic_update "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        '.status="validated" | .validation_error=null | .updated_at=$at' \
        || die "无法更新 topic meta:$meta"
      printf '%s' validated
      return 0
    fi
    mmw_atomic_update "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '.status="failed" | .validation_error="topic result schema invalid" | .updated_at=$at' \
      || die "无法更新 topic meta:$meta"
    printf '%s' failed
    return 0
  fi
  case "$status" in
    running|dispatched) printf '%s' running ;;
    failed) printf '%s' failed ;;
    *) printf '%s' prepared ;;
  esac
}

assemble_final_result() {
  local root="$1" report="$2" tmp
  tmp="$(mktemp "$root/.result.XXXXXX")" || die "无法创建 investigate result"
  jq -n --slurpfile topics "$root/synthesis/evidence.json" \
    --slurpfile report "$report" \
    '{topics:$topics[0],report:$report[0]}' >"$tmp" \
    && jq -e . "$tmp" >/dev/null 2>&1 \
    && mv "$tmp" "$root/result.json" \
    || { rm -f "$tmp"; die "无法组装 investigate result"; }
}

cmd_status() {
  local run="" root meta state running=0 failed=0 validated=0 prepared=0 total=0 i angle
  while [ $# -gt 0 ]; do case "$1" in --run) run="$2"; shift 2 ;; *) die "未知参数:$1" ;; esac; done
  [ -n "$run" ] || die "--run 必填"
  root="$(run_root "$run")"
  [ -f "$root/run.json" ] || die "investigate run 不存在:$run"
  acquire_run_lock "$root"

  total="$(jq 'length' "$root/topics.json")"
  for ((i=0; i<total; i++)); do
    printf -v meta '%s/topics/%03d/meta.json' "$root" "$i"
    angle="$(jq -r '.angle // empty' "$meta" 2>/dev/null || true)"
    if [ ! -f "$meta" ]; then
      failed=$((failed+1))
      echo "TOPIC[$i] angle=? status=missing"
      continue
    fi
    state="$(refresh_topic_meta "$meta")"
    case "$state" in
      validated) validated=$((validated+1)) ;;
      running) running=$((running+1)) ;;
      failed) failed=$((failed+1)) ;;
      *) prepared=$((prepared+1)) ;;
    esac
    echo "TOPIC[$i] angle=$angle status=$state"
  done

  if [ "$running" -gt 0 ] || [ "$prepared" -gt 0 ]; then
    release_run_lock
    echo "INVESTIGATE_STATUS=RUNNING validated=$validated prepared=$prepared running=$running failed=$failed total=$total"
    echo "NEXT=完成 topic Task 并写入各 topics/*/result.json 后重跑: mmw investigate status --run $run"
    return 0
  fi
  if [ "$failed" -gt 0 ] || [ "$validated" -ne "$total" ]; then
    mmw_atomic_update "$root/run.json" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '.status="failed" | .updated_at=$at' || die "无法更新 run 账本"
    release_run_lock
    echo "INVESTIGATE_STATUS=FAILED validated=$validated failed=$failed total=$total"
    echo "NEXT=mmw investigate resume --run $run"
    return 1
  fi

  local synth_meta="$root/synthesis/meta.json" report="$root/result.json"
  local synth_report="$root/synthesis/report.json" synth_state
  if [ -f "$report" ]; then
    mmw_atomic_update "$root/run.json" --arg report "$report" \
      --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '.status="completed" | .report_file=$report | .updated_at=$at' \
      || die "无法更新 run 账本"
    release_run_lock
    echo "INVESTIGATE_STATUS=COMPLETED"
    echo "REPORT_FILE=$report"
    return 0
  fi

  if [ ! -f "$synth_meta" ]; then
    prepare_synthesis "$root"
    release_run_lock
    echo "INVESTIGATE_STATUS=SYNTHESIZING"
    echo "NEXT=派发 synthesis DISPATCH 后重跑: mmw investigate status --run $run"
    return 0
  fi

  if [ -f "$root/synthesis/result.json" ]; then
    if validate_report "$synth_meta" "$synth_report"; then
      assemble_final_result "$root" "$synth_report"
      mmw_atomic_update "$root/run.json" --arg report "$root/result.json" \
        --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        '.status="completed" | .report_file=$report | .updated_at=$at' \
        || die "无法更新 run 账本"
      mmw_atomic_update "$synth_meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        '.status="validated" | .validation_error=null | .updated_at=$at' \
        || die "无法更新 synthesis meta"
      release_run_lock
      echo "INVESTIGATE_STATUS=COMPLETED"
      echo "REPORT_FILE=$root/result.json"
      return 0
    fi
    mmw_atomic_update "$synth_meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '.status="failed" | .validation_error="report result schema invalid" | .updated_at=$at' \
      || die "无法更新 synthesis meta"
  else
    synth_state="$(jq -r '.status // prepared' "$synth_meta")"
    if [ "$synth_state" = prepared ]; then
      release_run_lock
      echo "INVESTIGATE_STATUS=SYNTHESIZING"
      print_task_dispatch "$SYNTH_SUBAGENT" "$root/synthesis/prompt.md" "$SYNTH_MODEL"
      echo "NEXT=写入 $root/synthesis/result.json 后重跑: mmw investigate status --run $run"
      return 0
    fi
  fi

  mmw_atomic_update "$root/run.json" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '.status="failed" | .updated_at=$at' || die "无法更新 run 账本"
  release_run_lock
  echo "INVESTIGATE_STATUS=FAILED synthesis"
  echo "NEXT=mmw investigate resume --run $run"
  return 1
}

cmd_resume() {
  local run="" root meta state retried=0 dir
  while [ $# -gt 0 ]; do case "$1" in --run) run="$2"; shift 2 ;; *) die "未知参数:$1" ;; esac; done
  [ -n "$run" ] || die "--run 必填"
  root="$(run_root "$run")"
  [ -f "$root/run.json" ] || die "investigate run 不存在:$run"
  acquire_run_lock "$root"

  for meta in "$root"/topics/*/meta.json; do
    [ -f "$meta" ] || continue
    dir="$(dirname "$meta")"
    [ -f "$dir/validated.json" ] && continue
    state="$(jq -r '.status // prepared' "$meta")"
    case "$state" in
      running|dispatched) continue ;;
    esac
    archive_job_attempt "$meta"
    mmw_atomic_update "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '.status="prepared" | .validation_error=null | .attempt=((.attempt // 1)+1) | .updated_at=$at' \
      || die "无法更新 topic meta:$meta"
    print_task_dispatch "$TOPIC_SUBAGENT" "$(jq -r .prompt_file "$meta")" "$TOPIC_MODEL"
    retried=$((retried+1))
  done

  meta="$root/synthesis/meta.json"
  if [ -f "$meta" ] && [ ! -f "$root/result.json" ]; then
    state="$(jq -r '.status // prepared' "$meta")"
    if [ "$state" != running ] && [ "$state" != dispatched ]; then
      if [ ! -f "$root/synthesis/report.json" ]; then
        archive_job_attempt "$meta"
        mmw_atomic_update "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
          '.status="prepared" | .validation_error=null | .attempt=((.attempt // 1)+1) | .updated_at=$at' \
          || die "无法更新 synthesis meta"
        print_task_dispatch "$SYNTH_SUBAGENT" "$root/synthesis/prompt.md" "$SYNTH_MODEL"
        retried=$((retried+1))
      fi
    fi
  fi

  release_run_lock
  [ "$retried" -gt 0 ] || die "没有可恢复的失败 job"
  mmw_atomic_update "$root/run.json" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '.status="running" | .updated_at=$at' || die "无法更新 run 账本"
  echo "INVESTIGATE_RESUMED jobs=$retried"
  echo "NEXT=mmw investigate status --run $run"
}

cmd_result() {
  local run="" root report
  while [ $# -gt 0 ]; do case "$1" in --run) run="$2"; shift 2 ;; *) die "未知参数:$1" ;; esac; done
  [ -n "$run" ] || die "--run 必填"
  root="$(run_root "$run")"
  report="$root/result.json"
  if [ -f "$report" ]; then
    echo "$report"
    return 0
  fi
  if [ -f "$root/synthesis/report.json" ]; then
    echo "$root/synthesis/report.json"
    return 0
  fi
  echo "报告尚未完成。先派发 topic/synthesis Task，在各目录写入 result.json，再跑 mmw investigate status --run $run" >&2
  exit 2
}

case "${1:-}" in
  start) shift; cmd_start "$@" ;;
  status) shift; cmd_status "$@" ;;
  resume) shift; cmd_resume "$@" ;;
  result) shift; cmd_result "$@" ;;
  *) die "用法: investigate.sh start|status|resume|result ..." ;;
esac
