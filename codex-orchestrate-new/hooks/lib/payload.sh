#!/usr/bin/env bash
# Safe helpers for Codex hook payloads.

payload_jq() {
  local payload="$1"
  local filter="$2"
  local default="${3:-}"
  local value

  value=$(printf '%s' "$payload" | jq -er "$filter" 2>/dev/null) || {
    printf '%s\n' "$default"
    return 0
  }

  printf '%s\n' "$value"
}

payload_tool_command() {
  local payload="$1"

  payload_jq "$payload" '
    if (.tool_input? | type) == "object" then
      (.tool_input.command // .tool_input.cmd // "")
    elif (.tool_input? | type) == "string" then
      .tool_input
    else
      ""
    end
  ' ""
}

payload_tool_exit_code() {
  local payload="$1"

  payload_jq "$payload" '
    if (.tool_response? | type) == "object" then
      (.tool_response.exit_code // .tool_response.status_code // 0)
    elif (.tool_response? | type) == "number" then
      .tool_response
    else
      0
    end
  ' "0"
}

payload_file_path() {
  local payload="$1"

  payload_jq "$payload" '
    if (.tool_input? | type) == "object" then
      (.tool_input.file_path // .tool_input.path // "")
    else
      ""
    end
  ' ""
}

payload_touches_docs() {
  local payload="$1"
  local file_path
  file_path="$(payload_file_path "$payload")"

  if [[ "$file_path" =~ (^|/)docs/ ]]; then
    return 0
  fi

  local raw_input
  raw_input="$(payload_jq "$payload" 'if (.tool_input? | type) == "string" then .tool_input else "" end' "")"
  if printf '%s\n' "$raw_input" | grep -qE '^\*\*\* (Add|Update|Delete) File: (.*[/])?docs/'; then
    return 0
  fi

  return 1
}

mmw_payload_command() {
  payload_tool_command "$1"
}

mmw_payload_exit_code() {
  payload_tool_exit_code "$1"
}

mmw_payload_file_path() {
  payload_file_path "$1"
}
