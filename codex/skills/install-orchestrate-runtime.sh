#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SOURCE_ROOT="$ROOT_DIR/.agents/skills"
SKILL_NAMES=(
  "orchestrate-discovery"
  "orchestrate-workflow"
  "orchestrate-plan-writing"
  "orchestrate-execution"
  "orchestrate-final-review"
  "orchestrate-multi-pr-merge"
)
MODE=""
TARGET_REPO=""
APPLY=0

usage() {
  cat <<'EOF'
Usage:
  bash codex/skills/install-orchestrate-runtime.sh --target-repo /path/to/repo [--dry-run|--apply]
  bash codex/skills/install-orchestrate-runtime.sh --user [--dry-run|--apply]

Installs the repo-authored Codex Orchestrate skill bundle into a Codex-visible
location. Default mode is --dry-run.

Modes:
  --target-repo PATH  Copy into PATH/.agents/skills/<skill-name>.
  --user              Copy into ${AGENTS_HOME:-$HOME/.agents}/skills/<skill-name>.

The installer replaces only the six Orchestrate skill directories listed above.
It does not edit Codex config files.
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

for skill_name in "${SKILL_NAMES[@]}"; do
  if [ ! -f "$SOURCE_ROOT/$skill_name/SKILL.md" ]; then
    echo "ERROR: source skill is missing: $SOURCE_ROOT/$skill_name" >&2
    exit 1
  fi
done

if [ "$MODE" = "target" ]; then
  TARGET_REPO="$(cd "$TARGET_REPO" && pwd)"
  DEST_ROOT="$TARGET_REPO/.agents/skills"
elif [ "$MODE" = "user" ]; then
  DEST_ROOT="${AGENTS_HOME:-$HOME/.agents}/skills"
else
  echo "ERROR: choose --target-repo PATH or --user" >&2
  usage >&2
  exit 2
fi

if [ "$SOURCE_ROOT" = "$DEST_ROOT" ]; then
  echo "Source and destination roots are identical; nothing to install."
  exit 0
fi

echo "Source root:      $SOURCE_ROOT"
echo "Destination root: $DEST_ROOT"
echo "Skills:           ${SKILL_NAMES[*]}"

if [ "$APPLY" -ne 1 ]; then
  echo "Dry run only. Re-run with --apply to install."
  exit 0
fi

mkdir -p "$DEST_ROOT"

installed=0
for skill_name in "${SKILL_NAMES[@]}"; do
  source_dir="$SOURCE_ROOT/$skill_name"
  dest_dir="$DEST_ROOT/$skill_name"

  if [ -e "$dest_dir" ]; then
    if diff -qr "$source_dir" "$dest_dir" >/dev/null 2>&1; then
      echo "$skill_name already matches source."
      continue
    fi

    rm -rf "$dest_dir"
    echo "Removed existing destination before install: $dest_dir"
  fi

  cp -R "$source_dir" "$dest_dir"
  find "$dest_dir" -name '.DS_Store' -type f -delete
  echo "Installed $skill_name."
  installed=1
done

if [ "$installed" -eq 0 ]; then
  echo "All destination skills already match source."
fi
