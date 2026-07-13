#!/usr/bin/env bash
# shellcheck shell=bash

mmw_droid_atomic_update() {
  local file="$1"; shift
  local tmp
  tmp="$(mktemp "$(dirname "$file")/.droid-meta.XXXXXX")" || return 1
  jq "$@" "$file" >"$tmp" \
    && jq -e . "$tmp" >/dev/null 2>&1 \
    && mv "$tmp" "$file" \
    || { rm -f "$tmp"; return 1; }
}

mmw_droid_render_prompt() {
  local source="$1" target="$2"
  awk 'BEGIN{n=0} /^---[[:space:]]*$/{n++; next} n>=2{print}' "$source" >"$target"
  [ -s "$target" ]
}

mmw_droid_load_tool_inventory() {
  local file="$1" model="$2" tmp
  tmp="$(mktemp "$(dirname "$file")/.tools.XXXXXX")" || return 1
  droid exec --model "$model" --list-tools --output-format json >"$tmp" \
    && jq -e 'type=="array" and all(.[]; .id|type=="string")' "$tmp" >/dev/null 2>&1 \
    && mv "$tmp" "$file" \
    || { rm -f "$tmp"; return 1; }
}

mmw_droid_disable_all_except() {
  local allowed="$1" inventory="$2"
  jq -r --arg allowed "$allowed" '
    ($allowed | if .=="" then [] else split(",") end) as $kept
    | [.[] | .id | select(. as $id | $kept | index($id) | not)] | join(",")
  ' "$inventory"
}

mmw_droid_launch() {
  local meta="$1" prompt="$2" cwd="$3" model="$4" effort="$5" system_prompt="$6"
  local session_id="${7:-}" auto="${8:-high}" disabled_tools="${9:-}"
  command -v droid >/dev/null 2>&1 || return 1

  local dir result log pid
  dir="$(dirname "$meta")"
  result="$dir/result.json"
  log="$dir/run.log"
  rm -f "$result" "$log"

  local -a cmd=(droid exec --output-format json --auto "$auto" --cwd "$cwd"
    --model "$model" --reasoning-effort "$effort"
    --append-system-prompt-file "$system_prompt")
  [ -n "$disabled_tools" ] && cmd+=(--disabled-tools "$disabled_tools")
  [ -n "$session_id" ] && cmd+=(--session-id "$session_id")
  cmd+=(--file "$prompt")

  nohup "${cmd[@]}" >"$result" 2>"$log" </dev/null &
  pid=$!
  if ! mmw_droid_atomic_update "$meta" \
    --argjson pid "$pid" --arg result "$result" --arg log "$log" \
    --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '.status="running" | .pid=$pid | .result_file=$result | .log_file=$log | .updated_at=$at'; then
    kill "$pid" 2>/dev/null || true
    return 1
  fi

  MMW_DROID_PID="$pid"
  MMW_DROID_RESULT_FILE="$result"
  MMW_DROID_LOG_FILE="$log"
}

mmw_droid_refresh() {
  local meta="$1" pid result status subtype session
  [ -f "$meta" ] || return 2
  pid="$(jq -r '.pid // empty' "$meta")"
  result="$(jq -r '.result_file // empty' "$meta")"
  status="$(jq -r '.status // "prepared"' "$meta")"

  if [ -z "$result" ] || [ ! -s "$result" ] || ! jq -e . "$result" >/dev/null 2>&1; then
    if [ "$status" = running ] && [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      echo RUNNING
      return 0
    fi
    mmw_droid_atomic_update "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '.status="failed" | .updated_at=$at' || return 2
    echo FAILED
    return 1
  fi

  subtype="$(jq -r '.subtype // empty' "$result")"
  session="$(jq -r '.session_id // empty' "$result")"
  if [ "$subtype" = success ] \
    && [ "$(jq -r '.is_error // false' "$result")" = false ] \
    && [ -n "$session" ]; then
    mmw_droid_atomic_update "$meta" --arg session "$session" \
      --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '.status="completed" | .session_id=$session | .updated_at=$at' || return 2
    echo COMPLETED
    return 0
  fi

  mmw_droid_atomic_update "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '.status="failed" | .updated_at=$at' \
    || return 2
  echo FAILED
  return 1
}
