"""Write each scene's `{state, vals}` into `scenes.json` by running that page's LOGIC in Node.

Usage: export_scene_data.py <handoff-dir>
Prints `exported <n>/<n> scenes`. Exit 1 if a scene fails (names it and the last
error line); 2 if a scene's props set `standalone`.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

FX = os.environ.get("DC_FX", "FIXTURES")
FX_FILE = os.environ.get("DC_FX_FILE", "data/fixtures.js")
W, H = (int(v) for v in os.environ.get("DC_FRAME", "1440x900").split("x"))
RUNNER_JS = Path(__file__).with_name("export_scene.js")


def page_props(module, scene: dict) -> dict:
    props = {"$preview": {"width": W, "height": H}}
    spec = getattr(module, "PROPS", None) or {}
    if isinstance(spec, dict):
        for key, value in spec.items():
            if isinstance(value, dict) and "default" in value:
                props[key] = value["default"]
    props.update(scene.get("props") or {})
    return props


_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def last_line(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    while lines:
        plain = _ANSI.sub("", lines[-1]).strip()
        if plain.startswith("Node.js v") or plain.startswith("at "):
            lines.pop()
            continue
        return plain
    return "failed"


def run_scene(handoff: Path, scene: dict) -> dict:
    page = scene.get("page") or ""
    src = handoff / "src" / f"{page.removesuffix('.dc.html')}.py"
    if not src.is_file():
        raise RuntimeError(f"no src for {page}: {src}")
    spec = importlib.util.spec_from_file_location("blk", src)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    logic = getattr(module, "LOGIC", "")
    fx_path = handoff / FX_FILE
    if not fx_path.is_file():
        raise RuntimeError(f"no fixtures at {fx_path}")
    proc = subprocess.run(
        ["node", str(RUNNER_JS), str(fx_path), FX, json.dumps(page_props(module, scene))],
        input=logic,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(last_line(proc.stderr or proc.stdout))
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(last_line(proc.stdout or str(exc))) from exc


def main() -> int:
    args = sys.argv[1:]
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
