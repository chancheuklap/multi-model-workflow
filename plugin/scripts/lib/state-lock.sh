#!/usr/bin/env bash
# Shared state lock primitives.
# Extracted from state.sh for reuse by review-effectiveness.sh and other scripts.
set -euo pipefail

STATE_LOCK_TTL="${STATE_LOCK_TTL:-60}"

state_lock_acquire() {
  local lock_dir="$1"
  local attempts=0

  while ! mkdir "$lock_dir" 2>/dev/null; do
    if [[ -f "$lock_dir/ts" ]]; then
      local ts
      ts=$(cat "$lock_dir/ts")
      local now
      now=$(date +%s)
      if (( now - ts > STATE_LOCK_TTL )); then
        echo "Cleaning stale lock (age=$((now - ts))s)" >&2
        rm -rf "$lock_dir"
        continue
      fi
    fi
    attempts=$((attempts + 1))
    if (( attempts > 50 )); then
      echo "Error: could not acquire lock after 50 attempts" >&2
      return 2
    fi
    sleep 0.1
  done

  echo $$ > "$lock_dir/pid"
  date +%s > "$lock_dir/ts"
}

state_lock_release() {
  local lock_dir="$1"
  rm -rf "$lock_dir"
}

state_lock_check_stale() {
  local lock_dir="$1"
  local ttl_seconds="${2:-$STATE_LOCK_TTL}"

  if [[ ! -d "$lock_dir" ]]; then
    echo "no_lock"
    return 0
  fi

  if [[ -f "$lock_dir/ts" ]]; then
    local ts
    ts=$(cat "$lock_dir/ts")
    local now
    now=$(date +%s)
    if (( now - ts > ttl_seconds )); then
      echo "stale"
      return 0
    fi
  fi

  echo "active"
  return 0
}
