#!/usr/bin/env bash
set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "$0")/.." && pwd)"

forbidden='SendMessage|Agent tool|Agent\(\{|Skill\(\{|\.claude/multi-model-workflow|CLAUDE_PLUGIN_ROOT|run_in_background|agentId|codex-companion\.mjs|CODEX_SCRIPT|Opus|Sonnet|sonnet|claude-opus|~/.claude|claude-review-companion|--lane claude|claude-cli-default|claude -p'

if rg -n "$forbidden" \
  "$PLUGIN_DIR/.codex-plugin" \
  "$PLUGIN_DIR/agents" \
  "$PLUGIN_DIR/hooks" \
  "$PLUGIN_DIR/scripts" \
  "$PLUGIN_DIR/skills" \
  "$PLUGIN_DIR/build" \
  "$PLUGIN_DIR/state-schema" \
  "$PLUGIN_DIR/README.md" \
  "$PLUGIN_DIR/architecture-draft.md"; then
  echo "stale Claude host primitive found in Codex runtime source" >&2
  exit 1
fi

if rg -n 'send_input\(\{\s*agent_id|resume_agent\(\{\s*agent_id|use the installed `' \
  "$PLUGIN_DIR/agents" \
  "$PLUGIN_DIR/skills" \
  "$PLUGIN_DIR/build"; then
  echo "non-native Codex multi-agent or skill invocation schema found" >&2
  exit 1
fi

python3 - "$PLUGIN_DIR" <<'PY'
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
bad = []
for base in ["skills", "build"]:
    for path in (root / base).rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"spawn_agent\(\{.*?\n\}\)", text, re.S):
            block = match.group(0)
            if re.search(r"^\s*(description|prompt):", block, re.M):
                bad.append(f"{path}:{text[:match.start()].count(chr(10)) + 1}")

if bad:
    print("spawn_agent blocks must use Codex native fields only:", file=sys.stderr)
    for item in bad:
        print(item, file=sys.stderr)
    sys.exit(1)
PY
