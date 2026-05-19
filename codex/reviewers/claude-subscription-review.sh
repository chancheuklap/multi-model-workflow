#!/usr/bin/env bash
set -euo pipefail

MODEL="claude-opus-4-7"
EFFORT="high"
TOOLS="${CLAUDE_SUBSCRIPTION_REVIEW_TOOLS:-Read,Grep,Glob}"
PROMPT_FILE=""
OUTPUT_FILE=""
REVIEW_NAME="${MULTI_MODEL_WORKFLOW_REVIEW_NAME:-claude-subscription-review}"

usage() {
  cat <<'EOF'
Usage:
  bash codex/reviewers/claude-subscription-review.sh [--prompt-file PATH] [--output PATH] [--tools TOOLS] [--review-name NAME]
  cat prompt.md | bash codex/reviewers/claude-subscription-review.sh

Runs an external Claude Code reviewer from Codex without `claude -p`.

This wrapper intentionally calls ordinary `claude` with prompt text on stdin.
It avoids the `-p/--print` and Agent SDK path. Use it for the Codex -> Claude
cross-model review lane intended to draw from normal interactive Claude Code
subscription usage.

Defaults:
  model: claude-opus-4-7
  effort: high
  tools: Read,Grep,Glob

The wrapper is reviewer-only. It does not enable Edit, Write, or Bash by
default. Parent prompts must be self-contained and include the same review mode,
source artifacts, pass condition, finding shape, and return contract used for
Codex code_reviewer dispatches.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --prompt-file)
      PROMPT_FILE="${2:-}"
      if [ -z "$PROMPT_FILE" ]; then
        echo "ERROR: --prompt-file requires a path" >&2
        exit 2
      fi
      shift 2
      ;;
    --output)
      OUTPUT_FILE="${2:-}"
      if [ -z "$OUTPUT_FILE" ]; then
        echo "ERROR: --output requires a path" >&2
        exit 2
      fi
      shift 2
      ;;
    --model|--effort)
      echo "ERROR: Claude review model and effort are fixed: --model claude-opus-4-7 --effort high" >&2
      exit 2
      ;;
    --tools)
      TOOLS="${2:-}"
      shift 2
      ;;
    --review-name)
      REVIEW_NAME="${2:-}"
      if [ -z "$REVIEW_NAME" ]; then
        echo "ERROR: --review-name requires a value" >&2
        exit 2
      fi
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

if ! command -v claude >/dev/null 2>&1; then
  echo "ERROR: claude CLI not found on PATH" >&2
  exit 127
fi

TMP_PROMPT="$(mktemp)"
trap 'rm -f "$TMP_PROMPT"' EXIT

cat > "$TMP_PROMPT" <<'EOF'
You are an external Claude Code reviewer invoked from Codex through ordinary interactive Claude Code CLI usage.

Role:
- Review only. Do not edit files, do not run write commands, do not commit, do not push, do not open PRs.
- Do not expand scope beyond the parent prompt.
- Do not trust upstream summaries. Independently inspect the provided artifacts and, when tools are available, read only the files needed to verify claims.
- Findings must be actionable and fit the parent return contract.
- If essential context is missing, return `needs context` instead of guessing.

EOF

if [ -n "$PROMPT_FILE" ]; then
  cat "$PROMPT_FILE" >> "$TMP_PROMPT"
else
  cat >> "$TMP_PROMPT"
fi

cmd=(
  claude
  --model "$MODEL"
  --effort "$EFFORT"
  --no-session-persistence
  --permission-mode dontAsk
  --tools "$TOOLS"
)

if [ -n "$OUTPUT_FILE" ]; then
  mkdir -p "$(dirname "$OUTPUT_FILE")"
  "${cmd[@]}" < "$TMP_PROMPT" | tee "$OUTPUT_FILE"
else
  "${cmd[@]}" < "$TMP_PROMPT"
fi

if [ -x "codex/hooks/track-review-budget.sh" ]; then
  MULTI_MODEL_WORKFLOW_REVIEW_LANE="external-claude-subscription" \
  MULTI_MODEL_WORKFLOW_REVIEW_NAME="$REVIEW_NAME" \
    bash codex/hooks/track-review-budget.sh
fi
