#!/usr/bin/env python3
"""Emit one opaque context marker and record only probe-owned event fields."""

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
    with Path(log).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record) + "\n")
    if in_mmw:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": event, "additionalContext":
            f"Probe context marker: {marker}; MMW_ROLE={record['MMW_ROLE']}"}}))


if __name__ == "__main__":
    main()
