"""Open one offline component story and expose its recorded API requests."""

from __future__ import annotations

import contextlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SERVER = ROOT / ".mmw" / "stories" / "serve.py"
VIEWPORTS = {
    "topbar": "1440x52",
    "tasks": "236x848",
    "canvas": "864x848",
    "detail": "340x848",
    "settings": "1440x900",
    "board": "1440x900",
}


@contextlib.contextmanager
def story_page(browser, mount: str, scene: str, responses=None, before_goto=None):
    # The story server takes a port of the machine's choosing and prints it; the origin
    # read back below is the only place its address comes from.
    env = os.environ.copy()
    process = subprocess.Popen(["python3", "-u", str(SERVER)], cwd=ROOT, env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        line = process.stdout.readline().strip()
        if not line.startswith("origin="):
            raise RuntimeError(process.stderr.read() or f"story server said {line!r}")
        origin = line.removeprefix("origin=")
        page = browser.new_page()
        page.add_init_script(
            f"window.__STORY_ANSWERS__ = {json.dumps(responses or {}, ensure_ascii=False)};"
        )
        if before_goto:
            before_goto(page)
        viewport = VIEWPORTS[mount]
        page.goto(f"{origin}/?page={mount}&scene={scene}&viewport={viewport}",
                  wait_until="networkidle")
        yield page
        page.close()
    finally:
        process.terminate()
        process.wait(timeout=5)
        process.stdout.close()
        process.stderr.close()


def recorded_requests(page):
    return page.evaluate("window.storyCalls()")
