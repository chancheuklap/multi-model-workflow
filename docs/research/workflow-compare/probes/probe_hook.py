#!/usr/bin/env python3
"""Emit opaque context markers and record probe-owned event fields.

2026-09-30: Grok 1.0.45's UserPromptSubmit payload contains prompt,
observed via Herdr 0.9.0 U-9.
Only U9_ probe prompts are retained; ordinary prompt text is not logged.
"""

import json
import os
from pathlib import Path
import sys
import uuid


def main() -> None:
    event, marker, log = sys.argv[1:]
    marker += "_" + uuid.uuid4().hex
    payload = json.load(sys.stdin)
    cwd = Path(payload.get("cwd") or os.getcwd())
    in_mmw = (cwd / ".mmw").is_dir()
    record = {"event": event, "marker": marker, "in_mmw": in_mmw,
              "source": payload.get("source", ""),
              "MMW_ROLE": os.environ.get("MMW_ROLE", "absent")}
    if event == "UserPromptSubmit" and "U9_" in payload.get("prompt", ""):
        record["probe_prompt"] = payload["prompt"]
    with Path(log).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record) + "\n")
    if in_mmw and event in ("SessionStart", "SubagentStart", "UserPromptSubmit"):
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": event, "additionalContext":
            f"Probe context marker: {marker}; MMW_ROLE={record['MMW_ROLE']}"}}))


if __name__ == "__main__":
    main()
