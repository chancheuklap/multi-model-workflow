#!/usr/bin/env bash
set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "$0")/.." && pwd)"

python3 - "$PLUGIN_DIR" <<'PY'
import sys
from pathlib import Path
import tomllib

root = Path(sys.argv[1])
expected = {
    "pack_executor.toml": ("gpt-5.3-codex", "xhigh"),
    "complex_pack_executor.toml": ("gpt-5.5", "high"),
    "code_explorer.toml": ("gpt-5.3-codex", "xhigh"),
    "complex_code_explorer.toml": ("gpt-5.5", "high"),
    "docs_worker.toml": ("gpt-5.3-codex", "xhigh"),
    "plan_writer.toml": ("gpt-5.5", "xhigh"),
    "root_cause_analyst.toml": ("gpt-5.5", "xhigh"),
}

for name, (model, effort) in expected.items():
    path = root / "agents" / name
    payload = tomllib.loads(path.read_text())
    assert payload["model"] == model, (name, payload["model"], model)
    assert payload["model_reasoning_effort"] == effort, (name, payload["model_reasoning_effort"], effort)
    assert payload["developer_instructions"].strip(), name
    assert payload["sandbox_mode"] in {"workspace-write", "read-only"}, name

for path in (root / "agents").glob("*.toml"):
    text = path.read_text()
    assert "gpt-5.4-mini" not in text, path.name
PY
