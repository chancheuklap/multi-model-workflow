"""Open one offline component story and expose its recorded API requests."""

from __future__ import annotations

import contextlib
import os
import socket
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SERVER = ROOT / ".mmw" / "stories" / "serve.py"


def free_base() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1] - 1


@contextlib.contextmanager
def story_page(browser, mount: str, scene: str):
    env = os.environ.copy()
    env["MMW_PORT_BASE"] = str(free_base())
    process = subprocess.Popen(["python3", "-u", str(SERVER)], cwd=ROOT, env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        line = process.stdout.readline().strip()
        if not line.startswith("origin="):
            raise RuntimeError(process.stderr.read() or f"story server said {line!r}")
        origin = line.removeprefix("origin=")
        page = browser.new_page()
        page.goto(f"{origin}/?page={mount}&scene={scene}&viewport=1440x900",
                  wait_until="networkidle")
        yield page
        page.close()
    finally:
        process.terminate()
        process.wait(timeout=5)
        process.stdout.close()
        process.stderr.close()


def recorded_requests(page):
    return page.evaluate("window.storyApi.calls()")
