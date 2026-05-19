#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=0
ROOT_ARG=""

usage() {
  cat <<'EOF'
Usage:
  bash codex/hooks/cleanup-run-state.sh [--dry-run|--apply] [--root PATH]

Removes multi-model-workflow runtime state before publishing:
  .codex/multi-model-workflow/

The directory contains temporary scope, budget, review prompt, review result,
and dispatch ledger files. Formal design, plan, issue, report, code, and test
artifacts live outside this directory and are not removed.

Default mode is --apply.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --apply)
      DRY_RUN=0
      shift
      ;;
    --root)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --root requires a path" >&2
        exit 2
      fi
      ROOT_ARG="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ -n "$ROOT_ARG" ]; then
  if [ ! -d "$ROOT_ARG" ]; then
    echo "ERROR: --root is not a directory: $ROOT_ARG" >&2
    exit 2
  fi
  ROOT_DIR="$(cd "$ROOT_ARG" && (git rev-parse --show-toplevel 2>/dev/null || pwd))"
else
  ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi
ROOT_DIR="$(cd "$ROOT_DIR" && pwd)"
RUN_DIR="$ROOT_DIR/.codex/multi-model-workflow"

case "$RUN_DIR" in
  "$ROOT_DIR/.codex/multi-model-workflow") ;;
  *)
    echo "ERROR: refusing to clean unexpected path: $RUN_DIR" >&2
    exit 2
    ;;
esac

if [ ! -e "$RUN_DIR" ]; then
  echo "[multi-model-workflow] No runtime state directory to clean: $RUN_DIR"
  exit 0
fi

if [ -L "$RUN_DIR" ]; then
  echo "ERROR: refusing to remove symlinked runtime state directory: $RUN_DIR" >&2
  exit 2
fi

if [ ! -d "$RUN_DIR" ]; then
  echo "ERROR: runtime state path exists but is not a directory: $RUN_DIR" >&2
  exit 2
fi

count="$(find "$RUN_DIR" -mindepth 1 -print | wc -l | tr -d ' ')"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "[multi-model-workflow] Would remove $count runtime state entries under $RUN_DIR"
  find "$RUN_DIR" -mindepth 1 -maxdepth 3 -print | sort
  exit 0
fi

rm -rf "$RUN_DIR"
echo "[multi-model-workflow] Removed $count runtime state entries under $RUN_DIR"
