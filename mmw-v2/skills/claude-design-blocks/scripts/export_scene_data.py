"""Write each scene's `{state, vals}` into `scenes.json` by running that page's LOGIC in Node.

Usage: export_scene_data.py <handoff-dir>
Prints `exported <n>/<n> scenes`. Exit 1 if a scene fails (names it and the last
error line); 2 if a scene's props set `standalone`.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

FX = os.environ.get("DC_FX", "FIXTURES")
FX_FILE = os.environ.get("DC_FX_FILE", "data/fixtures.js")

RUNNER = r"""
const fs = require("fs");
const [fxPath, fxName, propsJson] = process.argv.slice(2);
const logic = fs.readFileSync(0, "utf8");
const props = JSON.parse(propsJson);

const window = {
  addEventListener() {},
  removeEventListener() {},
  querySelector() { return null; },
};
const document = {
  addEventListener() {},
  removeEventListener() {},
  querySelector() { return null; },
};
function setTimeout() {}
function clearTimeout() {}
globalThis.window = window;
globalThis.document = document;
globalThis.setTimeout = setTimeout;
globalThis.clearTimeout = clearTimeout;

const fxSource = fs.readFileSync(fxPath, "utf8");
(0, eval)(fxSource);
if (window[fxName] == null && globalThis[fxName] != null) {
  window[fxName] = globalThis[fxName];
}

class DCLogic {
  constructor(props) {
    this.props = props;
    this.state = Object.assign({ fx: false, toast: "" }, this.init(props));
  }
  setState(partial, cb) {
    this.state = Object.assign({}, this.state, partial);
    if (typeof cb === "function") cb();
  }
  fx() { return window[fxName] || {}; }
  emit() {}
  toast() {}
  init() { return {}; }
  onReady() {}
  afterUpdate() {}
  cleanup() {}
  renderVals() { return {}; }
}

const Component = new Function(
  "DCLogic",
  `return class Component extends DCLogic {\n${logic}\n}`,
)(DCLogic);
const inst = new Component(props);
if (typeof inst.onReady === "function") inst.onReady();
const vals = typeof inst.renderVals === "function" ? inst.renderVals() : {};
process.stdout.write(JSON.stringify({
  state: JSON.parse(JSON.stringify(inst.state)),
  vals: JSON.parse(JSON.stringify(vals)),
}));
"""


def load_page(src: Path):
    spec = importlib.util.spec_from_file_location("blk", src)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def src_for(handoff: Path, page: str) -> Path:
    name = page.removesuffix(".dc.html")
    return handoff / "src" / f"{name}.py"


def last_line(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    while lines and (lines[-1].startswith("Node.js v") or lines[-1].startswith("at ")):
        lines.pop()
    return lines[-1] if lines else "failed"


def run_scene(handoff: Path, scene: dict) -> dict:
    page = scene.get("page") or ""
    src = src_for(handoff, page)
    if not src.is_file():
        raise RuntimeError(f"no src for {page}: {src}")
    module = load_page(src)
    logic = getattr(module, "LOGIC", "")
    fx_path = handoff / FX_FILE
    if not fx_path.is_file():
        raise RuntimeError(f"no fixtures at {fx_path}")
    with tempfile.TemporaryDirectory() as tmp:
        runner = Path(tmp) / "export_scene.js"
        runner.write_text(RUNNER, encoding="utf-8")
        proc = subprocess.run(
            ["node", str(runner), str(fx_path), FX, json.dumps(scene.get("props") or {})],
            input=logic,
            capture_output=True,
            text=True,
        )
    if proc.returncode != 0:
        raise RuntimeError(last_line(proc.stderr or proc.stdout))
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(last_line(proc.stdout or str(exc))) from exc
    if not isinstance(data, dict) or "vals" not in data:
        raise RuntimeError("Node wrote no {state, vals}")
    return data


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        sys.stderr.write("usage: export_scene_data.py <handoff-dir>\n")
        return 2
    handoff = Path(args[0])
    scenes_path = handoff / "scenes.json"
    try:
        scenes = json.loads(scenes_path.read_text(encoding="utf-8"))
    except OSError as exc:
        sys.stderr.write(f"{scenes_path}: {exc}\n")
        return 1
    if not isinstance(scenes, list):
        sys.stderr.write(f"{scenes_path}: expected a list of scenes\n")
        return 1
    for scene in scenes:
        props = scene.get("props") or {}
        if props.get("standalone"):
            name = scene.get("name") or "?"
            sys.stderr.write(f"{name}: standalone\n")
            return 2
    for scene in scenes:
        name = scene.get("name") or "?"
        try:
            scene["data"] = run_scene(handoff, scene)
        except Exception as exc:
            sys.stderr.write(f"{name}: {last_line(str(exc))}\n")
            return 1
    scenes_path.write_text(
        json.dumps(scenes, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    n = len(scenes)
    sys.stdout.write(f"exported {n}/{n} scenes\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
