#!/usr/bin/env bash
# Plan 005 Pack 5.15: plan-return.json parser.
# Source this file then call:
#   parse_plan_return <path-to-plan-return.json>
#
# Exports bash variables: PLAN_RETURN_VERDICT, PLAN_RETURN_PLAN_ID,
#   PLAN_RETURN_RUN_ID, PLAN_RETURN_DOC_PATCH_PATH, PLAN_RETURN_OPEN_ITEMS_PATH,
#   PLAN_RETURN_COMMITTED_COUNT, PLAN_RETURN_BLOCKED_COUNT, PLAN_RETURN_RAW.
# Returns 0 on success, 2 on validation failure (logs to stderr).

parse_plan_return() {
  local file="$1"

  if [[ -z "$file" ]]; then
    echo "Error: parse_plan_return requires a file path argument" >&2
    return 2
  fi
  if [[ ! -f "$file" ]]; then
    echo "Error: plan-return.json not found at: $file" >&2
    return 2
  fi
  if ! jq empty "$file" 2>/dev/null; then
    echo "Error: plan-return.json is not valid JSON: $file" >&2
    return 2
  fi

  # Required fields (schema_version + run_id + plan_id + verdict + per_pack)
  local schema_version verdict run_id plan_id
  schema_version=$(jq -r '.schema_version // empty' "$file")
  verdict=$(jq -r '.verdict // empty' "$file")
  run_id=$(jq -r '.run_id // empty' "$file")
  plan_id=$(jq -r '.plan_id // empty' "$file")

  if [[ "$schema_version" != "1" ]]; then
    echo "Error: plan-return schema_version expected '1', got '$schema_version'" >&2
    return 2
  fi
  if [[ -z "$run_id" || -z "$plan_id" || -z "$verdict" ]]; then
    echo "Error: plan-return missing required fields (run_id/plan_id/verdict)" >&2
    return 2
  fi

  case "$verdict" in
    pass|partial-pass|blocked|need-fresh-worker|needs-context|needs-plan-revision) ;;
    *) echo "Error: invalid verdict '$verdict' in plan-return.json" >&2; return 2 ;;
  esac

  if ! jq -e '.per_pack | type == "object"' "$file" >/dev/null 2>&1; then
    echo "Error: plan-return missing per_pack object" >&2
    return 2
  fi

  PLAN_RETURN_VERDICT="$verdict"
  PLAN_RETURN_RUN_ID="$run_id"
  PLAN_RETURN_PLAN_ID="$plan_id"
  PLAN_RETURN_DOC_PATCH_PATH=$(jq -r '.doc_patch_path // empty' "$file")
  PLAN_RETURN_OPEN_ITEMS_PATH=$(jq -r '.open_items_path // empty' "$file")
  PLAN_RETURN_COMMITTED_COUNT=$(jq '[.per_pack | to_entries[] | select(.value.status == "committed")] | length' "$file")
  PLAN_RETURN_BLOCKED_COUNT=$(jq '[.per_pack | to_entries[] | select(.value.status == "blocked")] | length' "$file")
  PLAN_RETURN_RAW="$(cat "$file")"

  export PLAN_RETURN_VERDICT PLAN_RETURN_RUN_ID PLAN_RETURN_PLAN_ID
  export PLAN_RETURN_DOC_PATCH_PATH PLAN_RETURN_OPEN_ITEMS_PATH
  export PLAN_RETURN_COMMITTED_COUNT PLAN_RETURN_BLOCKED_COUNT
  export PLAN_RETURN_RAW
  return 0
}
