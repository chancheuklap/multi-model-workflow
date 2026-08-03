#!/usr/bin/env bash
# shellcheck shell=bash

mmw_write_attendance() {
  local manifest="$1" mode="$2" policy="$3"
  case "$mode" in
    attended|afk) [ "$policy" = "null" ] || return 1 ;;
    unattended) jq -e 'type == "object"' <<<"$policy" >/dev/null 2>&1 || return 1 ;;
    *) return 1 ;;
  esac

  local loop_file tmp loop_tmp
  loop_file="$(dirname "$manifest")/loop-state.json"
  jq -e . "$manifest" >/dev/null 2>&1 || return 1
  if [ -f "$loop_file" ]; then
    jq -e . "$loop_file" >/dev/null 2>&1 || return 1
  fi

  tmp="$(mktemp "$(dirname "$manifest")/.task.json.attendance.XXXXXX")" || return 1
  jq --arg mode "$mode" --argjson policy "$policy" \
    '.attendance=$mode | .unattended_policy=$policy' "$manifest" >"$tmp" \
    || { rm -f "$tmp"; return 1; }
  [ -s "$tmp" ] && jq -e . "$tmp" >/dev/null 2>&1 \
    || { rm -f "$tmp"; return 1; }

  if [ -f "$loop_file" ]; then
    loop_tmp="$(mktemp "$(dirname "$loop_file")/.loop-state.attendance.XXXXXX")" \
      || { rm -f "$tmp"; return 1; }
    jq --arg mode "$mode" '.attendance=$mode' "$loop_file" >"$loop_tmp" \
      || { rm -f "$tmp" "$loop_tmp"; return 1; }
    [ -s "$loop_tmp" ] && jq -e . "$loop_tmp" >/dev/null 2>&1 \
      || { rm -f "$tmp" "$loop_tmp"; return 1; }
  else
    loop_tmp=""
  fi

  mv "$tmp" "$manifest" || { rm -f "$tmp" "$loop_tmp"; return 1; }
  if [ -n "$loop_tmp" ]; then
    mv "$loop_tmp" "$loop_file" || return 1
  fi
}
