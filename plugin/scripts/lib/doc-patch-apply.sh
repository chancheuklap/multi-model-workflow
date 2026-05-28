#!/usr/bin/env bash
# Plan 005 Pack 5.15: doc-patch.diff applier.
# Source then call:
#   apply_doc_patch <path-to-doc-patch.diff>
#
# Behavior:
#   - git apply --check first (cleanly applies)
#   - if check fails, prints conflict context to stderr and returns 2
#   - on success, runs git apply followed by git add of touched plan files
#   - never commits — caller (Coordinator) controls commit boundary
#     (Decision 6: doc-patch apply only after Plan Implementation Review pass)
#
# Returns 0 on success, 2 on validation/apply failure.

apply_doc_patch() {
  local patch="$1"

  if [[ -z "$patch" ]]; then
    echo "Error: apply_doc_patch requires a patch file path" >&2
    return 2
  fi
  if [[ ! -f "$patch" ]]; then
    echo "Error: doc-patch.diff not found at: $patch" >&2
    return 2
  fi

  # Empty patch is a no-op (legitimate when Worker has no checkbox changes)
  if [[ ! -s "$patch" ]]; then
    echo "Note: doc-patch.diff is empty; no-op" >&2
    return 0
  fi

  if ! git apply --check "$patch" 2>/tmp/doc-patch-conflict.log; then
    echo "Error: doc-patch.diff cannot be applied cleanly. Conflict:" >&2
    cat /tmp/doc-patch-conflict.log >&2
    rm -f /tmp/doc-patch-conflict.log
    return 2
  fi
  rm -f /tmp/doc-patch-conflict.log

  if ! git apply "$patch" 2>&1; then
    echo "Error: git apply failed after --check passed (unexpected race)" >&2
    return 2
  fi

  # Stage touched files (always plan docs; guard-plan-doc-patch.sh ensures shape)
  local touched
  touched=$(git diff --name-only)
  if [[ -n "$touched" ]]; then
    echo "$touched" | xargs -r git add
  fi

  return 0
}
