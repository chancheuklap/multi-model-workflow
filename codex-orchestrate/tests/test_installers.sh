#!/usr/bin/env bash
set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "$0")/.." && pwd)"

bash "$PLUGIN_DIR/installers/install.sh" --user --dry-run >/dev/null
bash "$PLUGIN_DIR/installers/uninstall.sh" --user --dry-run >/dev/null

tmp="$(mktemp -d)"
printf '[agents]\nmax_threads = 6\nmax_depth = 1\n' > "$tmp/config.toml"
python3 "$PLUGIN_DIR/installers/sync-agent-config.py" install \
  --config-file "$tmp/config.toml" \
  --source-agents-dir "$PLUGIN_DIR/agents" \
  --target-agents-dir "$tmp/agents"
python3 "$PLUGIN_DIR/installers/sync-agent-config.py" verify \
  --config-file "$tmp/config.toml" \
  --source-agents-dir "$PLUGIN_DIR/agents" \
  --target-agents-dir "$tmp/agents"
python3 "$PLUGIN_DIR/installers/sync-agent-config.py" remove \
  --config-file "$tmp/config.toml"
python3 - "$tmp/config.toml" <<'PY'
import pathlib
import sys
import tomllib

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
tomllib.loads(text)
assert "codex-orchestrate managed agents" not in text
PY
