#!/usr/bin/env python3
"""Serve component stories on a port of their own and print their origin.

The port is whatever the machine hands out (`127.0.0.1:0`), because a story page renders
presentational components from scene data and has no backend, no seed and no route
behind it: nothing here has to be reachable at an address anyone agreed in advance, and
a port picked this way collides with no other run. Taking one from the lease instead
would spend one of the product's `instance.max` slots for the length of a ticket.
"""

from __future__ import annotations

import http.server
import json
import os
import re
import subprocess
import sys
import urllib.parse
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PAGE = ROOT / "mmw-v2" / "board" / "page"
HANDOFF = Path(os.environ.get(
    "MMW_STORY_HANDOFF",
    ROOT / "prototypes" / "task-board" / "claude-design",
))
SCENES = HANDOFF / "scenes.json"
CONTRACT = Path(os.environ.get(
    "MMW_STORY_CONTRACT",
    ROOT / "docs" / "specs" / "task-board" / "screen-contract.yaml",
))
ADAPTERS = HERE / "adapters"


class BurstServer(http.server.ThreadingHTTPServer):
    request_queue_size = 128


def scene_inputs() -> dict[str, dict]:
    """Read the bounded scene-input shape from the screen contract."""
    inputs: dict[str, dict] = {}
    current: str | None = None
    in_scenes = False
    for line in CONTRACT.read_text(encoding="utf-8").splitlines():
        if line == "scenes:":
            in_scenes = True
            continue
        if in_scenes and line and not line.startswith(" "):
            break
        if not in_scenes:
            continue
        scene_match = re.match(r"^  (\S.*):$", line)
        if scene_match:
            current = scene_match.group(1)
            inputs[current] = {}
            continue
        if current is None:
            continue
        field_match = re.match(r"^      (file|value): (.+)$", line)
        if field_match:
            inputs[current][field_match.group(1)] = field_match.group(2)
            continue
        with_match = re.match(r"^      with: \{select: \{node: (null|\d+)}}$", line)
        if with_match:
            raw = with_match.group(1)
            inputs[current]["with"] = {"select": {"node": None if raw == "null" else int(raw)}}
    return inputs


SCENE_INPUTS = scene_inputs()


def merge(base, overlay):
    if not isinstance(base, dict) or not isinstance(overlay, dict):
        return deepcopy(overlay)
    result = deepcopy(base)
    for key, value in overlay.items():
        result[key] = merge(result.get(key), value) if key in result else deepcopy(value)
    return result


JAVASCRIPT_EXPORTS = r"""
const fs = require("node:fs");
const vm = require("node:vm");
const path = process.argv[1];
const sandbox = {window: {}};
vm.runInNewContext(fs.readFileSync(path, "utf8"), sandbox, {filename: path, timeout: 1000});
process.stdout.write(JSON.stringify(sandbox.window));
"""


def handoff_values(path: Path) -> dict:
    """Run one trusted handoff data file and return the values it writes to window."""
    try:
        completed = subprocess.run(
            ["node", "-e", JAVASCRIPT_EXPORTS, str(path)],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError(f"scene input timed out: {path}") from exc
    if completed.returncode != 0:
        reason = completed.stderr.strip() or f"node exited {completed.returncode}"
        raise ValueError(f"scene input failed: {path}: {reason}")
    try:
        values = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError(f"scene input did not produce JSON values: {path}") from exc
    if not isinstance(values, dict):
        raise ValueError(f"scene input did not produce a window object: {path}")
    return values


def resolve_scene_input(name: str):
    declaration = SCENE_INPUTS.get(name)
    if not declaration or "file" not in declaration or "value" not in declaration:
        raise ValueError(f"scene has no complete input declaration: {name}")
    values = handoff_values(HANDOFF / declaration["file"])
    reference = declaration["value"]
    try:
        namespace, key = reference.split(".", 1)
        value = values[namespace][key]
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError(f"scene input value was not found: {reference}") from exc
    return merge(value, declaration.get("with", {}))


def declared_input_files() -> set[str]:
    return {item["file"] for item in SCENE_INPUTS.values() if item.get("file")}


def window_keys(file: str, keys: list[str]) -> dict:
    """Return named window bindings from a handoff file the contract already loads.

    A scene input is one value (`APP_SCENES.morning`). The design page also reads
    the bindings beside it in that same file (`APP_TREES`, `APP_DETAILS`). The
    file has to be one a scene input already names, and each key has to be a
    window binding that file writes.
    """
    if file not in declared_input_files() or ".." in Path(file).parts:
        raise ValueError(f"file is not a scene input: {file}")
    if not keys or any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key) for key in keys):
        raise ValueError("window key was not named")
    values = handoff_values(HANDOFF / file)
    missing = [key for key in keys if key not in values]
    if missing:
        raise ValueError(f"window key was not found: {', '.join(missing)}")
    return {key: values[key] for key in keys}


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        path = urllib.parse.unquote(parsed.path)
        if path in ("/", "/index.html"):
            query = urllib.parse.parse_qs(parsed.query)
            page = (query.get("page") or [""])[0]
            if page and not (ADAPTERS / f"{page}.mjs").is_file():
                self.send_error(404)
                return
            return self.send_file(HERE / "index.html", "text/html; charset=utf-8")
        if path == "/story.mjs":
            return self.send_file(HERE / "story.mjs", "text/javascript; charset=utf-8")
        if path == "/scenes.json":
            return self.send_file(SCENES, "application/json")
        if path == "/scene-input.json":
            query = urllib.parse.parse_qs(parsed.query)
            scene = (query.get("scene") or [""])[0]
            try:
                body = (json.dumps(resolve_scene_input(scene), ensure_ascii=False) + "\n").encode()
            except (ValueError, FileNotFoundError) as exc:
                message = (
                    f"scene input unavailable for {scene}: {exc}. "
                    "Check the contract input.file/input.value and that Node.js is on PATH.\n"
                )
                return self.send_bytes(
                    message.encode(), "text/plain; charset=utf-8", status=404
                )
            return self.send_bytes(body, "application/json; charset=utf-8")
        if path == "/window-keys.json":
            query = urllib.parse.parse_qs(parsed.query)
            file = (query.get("file") or [""])[0]
            keys = query.get("key") or []
            try:
                body = (json.dumps(window_keys(file, keys), ensure_ascii=False) + "\n").encode()
            except (ValueError, FileNotFoundError) as exc:
                message = f"window keys unavailable for {file}: {exc}\n"
                return self.send_bytes(
                    message.encode(), "text/plain; charset=utf-8", status=404
                )
            return self.send_bytes(body, "application/json; charset=utf-8")
        if path.startswith("/adapters/"):
            target = (HERE / path.removeprefix("/")).resolve()
            if target.parent == ADAPTERS.resolve():
                return self.send_file(target, "text/javascript; charset=utf-8")
        if path.startswith("/product/"):
            target = (PAGE / path.removeprefix("/product/")).resolve()
            if target.parent == PAGE.resolve():
                return self.send_file(target, "text/javascript; charset=utf-8")
        if path.startswith("/styles/"):
            target = (PAGE / path.removeprefix("/")).resolve()
            styles = (PAGE / "styles").resolve()
            if target.is_relative_to(styles):
                content_type = (
                    "font/woff2" if target.suffix == ".woff2"
                    else "text/css; charset=utf-8"
                )
                return self.send_file(target, content_type)
        self.send_error(404)

    def send_file(self, path: Path, content_type: str):
        try:
            body = path.read_bytes()
        except FileNotFoundError:
            self.send_error(404)
            return
        self.send_bytes(body, content_type)

    def send_bytes(self, body: bytes, content_type: str, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    server = BurstServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    print(f"origin=http://127.0.0.1:{port}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
