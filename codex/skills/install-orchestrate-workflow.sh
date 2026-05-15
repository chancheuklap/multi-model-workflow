#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SOURCE_DIR="$ROOT_DIR/.agents/skills/orchestrate-workflow"
MODE=""
TARGET_REPO=""
APPLY=0

usage() {
  cat <<'EOF'
Usage:
  codex/skills/install-orchestrate-workflow.sh --target-repo /path/to/repo [--dry-run|--apply]
  codex/skills/install-orchestrate-workflow.sh --user [--dry-run|--apply]

Installs the repo-authored orchestrate-workflow skill into a Codex-visible
location. Default mode is --dry-run.

Modes:
  --target-repo PATH  Copy into PATH/.agents/skills/orchestrate-workflow.
  --user              Copy into ${AGENTS_HOME:-$HOME/.agents}/skills/orchestrate-workflow.

Safety:
  Existing different targets are moved to *.bak-YYYYmmddHHMMSS before copying.
  The script never edits Codex config files.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target-repo)
      MODE="target"
      TARGET_REPO="${2:-}"
      if [ -z "$TARGET_REPO" ]; then
        echo "ERROR: --target-repo requires a path" >&2
        exit 2
      fi
      shift 2
      ;;
    --user)
      MODE="user"
      shift
      ;;
    --apply)
      APPLY=1
      shift
      ;;
    --dry-run)
      APPLY=0
      shift
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

if [ ! -f "$SOURCE_DIR/SKILL.md" ]; then
  echo "ERROR: source skill is missing: $SOURCE_DIR" >&2
  exit 1
fi

if [ "$MODE" = "target" ]; then
  TARGET_REPO="$(cd "$TARGET_REPO" && pwd)"
  DEST_DIR="$TARGET_REPO/.agents/skills/orchestrate-workflow"
elif [ "$MODE" = "user" ]; then
  DEST_DIR="${AGENTS_HOME:-$HOME/.agents}/skills/orchestrate-workflow"
else
  echo "ERROR: choose --target-repo PATH or --user" >&2
  usage >&2
  exit 2
fi

if [ "$SOURCE_DIR" = "$DEST_DIR" ]; then
  echo "Source and destination are identical; nothing to install."
  exit 0
fi

echo "Source:      $SOURCE_DIR"
echo "Destination: $DEST_DIR"

if [ "$APPLY" -ne 1 ]; then
  echo "Dry run only. Re-run with --apply to install."
  exit 0
fi

mkdir -p "$(dirname "$DEST_DIR")"

if [ -e "$DEST_DIR" ]; then
  if diff -qr "$SOURCE_DIR" "$DEST_DIR" >/dev/null 2>&1; then
    echo "Destination already matches source."
    exit 0
  fi

  STAMP="$(date +%Y%m%d%H%M%S)"
  BACKUP_DIR="$DEST_DIR.bak-$STAMP"
  mv "$DEST_DIR" "$BACKUP_DIR"
  echo "Backed up existing destination to $BACKUP_DIR"
fi

cp -R "$SOURCE_DIR" "$DEST_DIR"
find "$DEST_DIR" -name '.DS_Store' -type f -delete
echo "Installed orchestrate-workflow skill."
