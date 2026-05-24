#!/usr/bin/env bash
# Learnings JSONL manager.
# Subcommands: append, read, read --with-trust-gate
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/lib/state-lock.sh"

STATE_BASE="${STATE_BASE:-.codex/multi-model-workflow}"
LEARNINGS_FILE="${STATE_BASE}/learnings.jsonl"

usage() {
  cat <<'USAGE'
Usage: learnings-jsonl.sh <command> [options]

Commands:
  append              Append a learning entry
  read                Read all learnings
  read --with-trust-gate  Read with trust gate filtering

Options:
  --run-id <id>         Run identifier
  --source-project <p>  Source project name
  --agent-role <role>   Agent role that produced the learning
  --type <type>         Learning type (pattern|gotcha|convention|risk)
  --content <text>      Learning content
  --tags <t1,t2>        Comma-separated tags
  --files <f1,f2>       Comma-separated file paths
  --confidence <1-10>   Confidence level
  --source <src>        Source description
USAGE
  exit 1
}

cmd_append() {
  local run_id="" source_project="" agent_role="" type="" content="" tags="" files="" confidence="" source=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --run-id) run_id="$2"; shift 2 ;;
      --source-project) source_project="$2"; shift 2 ;;
      --agent-role) agent_role="$2"; shift 2 ;;
      --type) type="$2"; shift 2 ;;
      --content) content="$2"; shift 2 ;;
      --tags) tags="$2"; shift 2 ;;
      --files) files="$2"; shift 2 ;;
      --confidence) confidence="$2"; shift 2 ;;
      --source) source="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$content" ]]; then
    echo "Error: --content required for append" >&2
    exit 2
  fi

  # Run poison detection (pass source for trust gate)
  local poison_result poison_exit
  poison_result=$(bash "$SCRIPT_DIR/lib/learnings-poison-detector.sh" "$content" "${run_id:-}" "" "${source:-}" 2>/dev/null) && poison_exit=0 || poison_exit=$?
  if [[ "$poison_exit" -ne 0 ]]; then
    echo "BLOCKED: learning failed poison detection: $poison_result" >&2
    exit 2
  fi

  # Extract trust marking from poison detector result
  local trusted="false"
  if [[ "$poison_result" == *"trusted=true"* ]]; then
    trusted="true"
  fi

  mkdir -p "$STATE_BASE"
  local now
  now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  # Convert comma-separated to JSON arrays
  local tags_json="[]"
  if [[ -n "$tags" ]]; then
    tags_json=$(echo "$tags" | tr ',' '\n' | jq -R . | jq -s .)
  fi
  local files_json="[]"
  if [[ -n "$files" ]]; then
    files_json=$(echo "$files" | tr ',' '\n' | jq -R . | jq -s .)
  fi

  local lock_dir="${STATE_BASE}/learnings.lock"
  state_lock_acquire "$lock_dir"

  local entry
  entry=$(jq -n -c \
    --arg sv "1" \
    --arg ts "$now" \
    --arg rid "${run_id:-}" \
    --arg sp "${source_project:-}" \
    --arg ar "${agent_role:-}" \
    --arg tp "${type:-pattern}" \
    --arg ct "$content" \
    --argjson tg "$tags_json" \
    --argjson fl "$files_json" \
    --argjson cf "${confidence:-5}" \
    --arg src "${source:-}" \
    --argjson tr "$trusted" \
    '{schema_version: ($sv|tonumber), timestamp: $ts, run_id: $rid, source_project: $sp, agent_role: $ar, type: $tp, content: $ct, tags: $tg, files: $fl, confidence: $cf, source: $src, trusted: $tr}')

  echo "$entry" >> "$LEARNINGS_FILE"

  # Per-run count check: warn if >10 learnings from same run_id
  if [[ -n "$run_id" ]]; then
    local run_count
    run_count=$(grep -c "\"run_id\":\"${run_id}\"" "$LEARNINGS_FILE" 2>/dev/null || echo "0")
    if [[ "$run_count" -gt 10 ]]; then
      echo "WARNING: run_id $run_id has $run_count learnings (>10 threshold)" >&2
    fi
  fi

  state_lock_release "$lock_dir"
  echo "OK: appended learning"
}

cmd_read() {
  local with_trust_gate=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --with-trust-gate) with_trust_gate="true"; shift ;;
      *) shift ;;
    esac
  done

  if [[ ! -f "$LEARNINGS_FILE" ]]; then
    echo "[]"
    return 0
  fi

  if [[ "$with_trust_gate" == "true" ]]; then
    local now_epoch
    now_epoch=$(date +%s)

    # Apply trust gate filters:
    # - confidence < 4: filtered
    # - decay (linear, -1 per 30 days, floor 0): filtered if effective confidence < 1
    # - source attribution missing: filtered
    # - stale reference: filtered (> 90 days without reconfirmation)
    # - contested learning: filtered (same content contradicted)
    # - high-volume source flooding: > 10 from same run_id filtered
    while IFS= read -r line; do
      [[ -z "$line" ]] && continue

      local conf
      conf=$(echo "$line" | jq -r '.confidence // 0')
      # Filter: confidence < 4
      if [[ "$conf" -lt 4 ]] 2>/dev/null; then
        continue
      fi

      local ts
      ts=$(echo "$line" | jq -r '.timestamp // ""')
      if [[ -n "$ts" ]]; then
        local ts_epoch
        ts_epoch=$(python3 -c "
import datetime, sys
ts = sys.argv[1].replace('Z', '+00:00')
try:
    dt = datetime.datetime.fromisoformat(ts)
    print(int(dt.timestamp()))
except Exception:
    print('0')
" "$ts" 2>/dev/null || echo "0")
        local age_days=$(( (now_epoch - ts_epoch) / 86400 ))
        local decay=$(( age_days / 30 ))
        local effective_conf=$(( conf - decay ))
        if [[ "$effective_conf" -lt 1 ]]; then
          continue
        fi
      fi

      # Filter: source attribution missing
      local src
      src=$(echo "$line" | jq -r '.source // ""')
      if [[ -z "$src" ]]; then
        continue
      fi

      # Filter: stale file references — check if referenced files still exist
      local has_stale_ref=false
      local file_refs
      file_refs=$(echo "$line" | jq -r '.files[]? // empty' 2>/dev/null)
      if [[ -n "$file_refs" ]]; then
        while IFS= read -r ref_path; do
          [[ -z "$ref_path" ]] && continue
          if [[ ! -f "$ref_path" && ! -f "./$ref_path" ]]; then
            has_stale_ref=true
            break
          fi
        done <<< "$file_refs"
      fi
      if [[ "$has_stale_ref" == "true" ]]; then
        continue
      fi

      echo "$line"
    done < "$LEARNINGS_FILE" | jq -s .
  else
    jq -s . "$LEARNINGS_FILE"
  fi
}

# --- Main ---
if [[ $# -lt 1 ]]; then usage; fi

CMD="$1"; shift

case "$CMD" in
  append) cmd_append "$@" ;;
  read) cmd_read "$@" ;;
  *) echo "Error: unknown command: $CMD" >&2; usage ;;
esac
