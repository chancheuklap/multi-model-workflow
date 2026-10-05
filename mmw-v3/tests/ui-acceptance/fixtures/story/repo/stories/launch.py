#!/usr/bin/env python3
"""Start serve.py as a child and stay in front of it, the shape of a real `stories`
command (`uv run` → python → pnpm → vite), where the server is a grandchild.

Writes the child's pid to the file STORY_CHILD_PID names. A SIGTERM ends this process
alone: nothing is forwarded, so a caller that stops only its direct child leaves
serve.py running with its port.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

child = subprocess.Popen([sys.executable, "-u", str(Path(__file__).with_name("serve.py"))])
Path(os.environ["STORY_CHILD_PID"]).write_text(str(child.pid), encoding="utf-8")
sys.exit(child.wait())
