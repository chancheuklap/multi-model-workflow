"""Write each scene's `{state, vals}` into `scenes.json` by running its page in Node.

The input is the downloaded page itself — the `.dc.html` in the package, which is the
baseline the implementation is held to. A page's source under `src/` is what `mk.py`
built it from; it is not read here, because not every page has one (an app page is
written by hand, and a page written inside Claude Design has no source at all) and
because a source can drift from the page that came down.

Usage: export_scene_data.py <handoff-dir>
Prints `exported <n>/<n> scenes`. Exit 1 if a scene fails (names it and the last
error line); 2 if a scene's props set `standalone`.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

RUNNER_JS = Path(__file__).with_name("export_scene.js")
RUNTIME = "support.js"


class _Page(HTMLParser):
    """The three things a scene needs from a downloaded page: the `data-props` prop
    declarations, the `src` of every script the page loads, and the body of its
    `<script data-dc-script>`."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.props: dict = {}
        self.sources: list[str] = []
        self.script = ""
        self._in_logic = False

    def handle_starttag(self, tag, attrs):
        if tag != "script":
            return
        attr = {k: v for k, v in attrs}
        if "src" in attr and attr["src"]:
            self.sources.append(attr["src"])
        if "data-dc-script" not in attr:
            return
        self._in_logic = True
        raw = attr.get("data-props")
        if raw:
            self.props = json.loads(raw)

    def handle_data(self, data):
        if self._in_logic:
            self.script += data

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_logic = False


def page_props(declared: dict, scene: dict) -> dict:
    """The props the page opens with: each declaration's `default`, then the scene's
    own props over them. `$preview` is a value, not a declaration."""
    props = {}
    if isinstance(declared, dict):
        for key, value in declared.items():
            if key == "$preview":
                props[key] = value
            elif isinstance(value, dict) and "default" in value:
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
    name = scene.get("page") or ""
    page = handoff / name
    if not page.is_file():
        raise RuntimeError(f"no page in the package: {page}")
    parsed = _Page()
    parsed.feed(page.read_text(encoding="utf-8"))
    if not parsed.script.strip():
        raise RuntimeError(f"{name}: no <script data-dc-script>")
    fixtures = []
    for src in parsed.sources:
        if "://" in src or src.rsplit("/", 1)[-1] == RUNTIME:
            continue
        path = handoff / re.sub(r"^\./", "", src)
        if not path.is_file():
            raise RuntimeError(f"{name} loads {src}, which the package does not have")
        fixtures.append(str(path))
    proc = subprocess.run(
        ["node", str(RUNNER_JS), json.dumps(page_props(parsed.props, scene)), *fixtures],
        input=parsed.script,
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
