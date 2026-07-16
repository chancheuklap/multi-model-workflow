#!/usr/bin/env bash
# shellcheck shell=bash
# pi headless 工人后端:渲染角色提示词、后台启动 pi -p、按 exit_code/进程存活刷新派发账本。

mmw_pi_atomic_update() {
  local file="$1"; shift
  local tmp
  tmp="$(mktemp "$(dirname "$file")/.pi-meta.XXXXXX")" || return 1
  jq "$@" "$file" >"$tmp" \
    && jq -e . "$tmp" >/dev/null 2>&1 \
    && mv "$tmp" "$file" \
    || { rm -f "$tmp"; return 1; }
}

# headless-agent.md 去掉 HTML 注释与空白后仍有正文才算可注入(占位文件只含注释)。
mmw_pi_headless_ready() {
  local file="$1"
  [ -f "$file" ] || return 1
  python3 - "$file" <<'PY'
import re
import sys

text = open(sys.argv[1], encoding="utf-8").read()
text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
sys.exit(0 if text.strip() else 1)
PY
}

# 渲染角色系统提示词:去 frontmatter 取正文;GPT 角色(roster frontmatter model 以
# openai-codex/ 开头)追加 headless-agent.md 正文。占位未填时不注入,并经
# MMW_PI_RENDER_NOTE 留一行日志文本,launch 时写进 run.log。
mmw_pi_render_prompt() {
  local source="$1" target="$2"
  local roster_model headless
  MMW_PI_RENDER_NOTE=""
  awk 'BEGIN{n=0} /^---[[:space:]]*$/{n++; next} n>=2{print}' "$source" >"$target"
  [ -s "$target" ] || return 1
  roster_model="$(awk 'BEGIN{n=0} /^---[[:space:]]*$/{n++; next} n<2 && /^model:[[:space:]]*/{sub(/^model:[[:space:]]*/,""); print; exit}' "$source")"
  case "$roster_model" in
    openai-codex/*)
      headless="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/prompts-runtime/headless-agent.md"
      if mmw_pi_headless_ready "$headless"; then
        { printf '\n'; cat "$headless"; } >>"$target"
      else
        MMW_PI_RENDER_NOTE="headless-agent prompt: placeholder, not injected"
      fi
      ;;
  esac
}

# 后台启动 pi headless 工人。$7 续接 session id(空则自铸);$8 工具白名单(逗号分隔,
# 空则不加 -t;审者传 read,grep,find,ls,bash 达成只读约束)。
mmw_pi_launch() {
  local meta="$1" prompt="$2" cwd="$3" model="$4" effort="$5" system_prompt="$6"
  local session_id="${7:-}" allowed_tools="${8:-}"
  local pi_bin="${PI_BIN:-pi}"
  local dir result log exit_file sid pid
  dir="$(dirname "$meta")"
  result="$dir/result.log"
  log="$dir/run.log"
  exit_file="$dir/exit_code"
  rm -f "$result" "$log" "$exit_file"

  if [ -n "$session_id" ]; then
    sid="$session_id"
  else
    sid="$(uuidgen)" || return 1
  fi
  [ -z "${MMW_PI_RENDER_NOTE:-}" ] || printf '%s\n' "$MMW_PI_RENDER_NOTE" >>"$log"

  local -a cmd=("$pi_bin" -p -a --model "$model" --thinking "$effort"
    --session-id "$sid" --append-system-prompt "$system_prompt")
  [ -n "$allowed_tools" ] && cmd+=(-t "$allowed_tools")

  (
    cd "$cwd" || { echo 127 >"$exit_file"; exit 127; }
    nohup "${cmd[@]}" "$(cat "$prompt")" >"$result" 2>>"$log" </dev/null
    echo $? >"$exit_file"
  ) &
  pid=$!

  if ! mmw_pi_atomic_update "$meta" \
    --argjson pid "$pid" --arg result "$result" --arg log "$log" \
    --arg session "$sid" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '.status="running" | .pid=$pid | .result_file=$result | .log_file=$log | .session_id=$session | .updated_at=$at'; then
    kill "$pid" 2>/dev/null || true
    return 1
  fi

  MMW_PI_PID="$pid"
  MMW_PI_RESULT_FILE="$result"
  MMW_PI_LOG_FILE="$log"
  MMW_PI_SESSION_ID="$sid"
}

mmw_pi_refresh() {
  local meta="$1" pid code exit_file
  [ -f "$meta" ] || return 2
  pid="$(jq -r '.pid // empty' "$meta")"
  exit_file="$(dirname "$meta")/exit_code"

  if [ -f "$exit_file" ]; then
    code="$(cat "$exit_file" 2>/dev/null)"
    if [ "$code" = "0" ]; then
      mmw_pi_atomic_update "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        '.status="completed" | .updated_at=$at' || return 2
      echo COMPLETED
      return 0
    fi
    mmw_pi_atomic_update "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '.status="failed" | .updated_at=$at' || return 2
    echo FAILED
    return 1
  fi

  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    echo RUNNING
    return 0
  fi
  mmw_pi_atomic_update "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '.status="failed" | .updated_at=$at' || return 2
  echo FAILED
  return 1
}
