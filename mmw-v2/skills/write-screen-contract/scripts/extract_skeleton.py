# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.58", "pyyaml>=6"]
# ///
"""Render the handoff package's declared scenes and write its row inventory.

Usage: uv run python extract_skeleton.py <handoff dir> <out.json> --contract <yaml> [--tools <dir>]

Every scene in `scenes.json` is rendered at every viewport declared by the contract,
with the contract locale, through the same `design_render.py` the story judge uses.
The output has one entry per (design page, `data-ui` id). Each entry says which
declared scenes show that element, whether it is clickable or editable, the displayed
text values, and its accessible names as explanation rather than identity.

Needs Chromium installed for Playwright. Playwright and PyYAML come from the dependency
block above: `uv run --script` reads it, and a `uv run python` invocation, which does not,
re-execs once through `uv run --script` when either import is missing. The three CDN
scripts `support.js` loads are answered from the package's `vendor/` directory, else a
local cache, else fetched once.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
# The ui-acceptance skill sits beside this one under `skills/`; `--tools` overrides that.
SIBLING_UA = HERE.parents[1] / "ui-acceptance" / "scripts"
TOOLS: list[Path] = []


def tools_dirs() -> list[Path]:
    return TOOLS or [SIBLING_UA]


def load_driver():
    looked = tools_dirs()
    path = None
    for directory in looked:
        candidate = directory / "design_render.py"
        if candidate.is_file():
            path = candidate
            break
    if path is None:
        paths = ", ".join(str(d) for d in looked)
        if TOOLS:
            raise SystemExit(
                f"no design_render.py in any --tools directory ({paths}). "
                "That file belongs to the ui-acceptance skill. "
                "Pass --tools <the ui-acceptance skill's scripts directory>."
            )
        raise SystemExit(
            f"no design_render.py in the sibling ui-acceptance skill ({paths}). "
            "Pass --tools <the ui-acceptance skill's scripts directory>."
        )
    spec = importlib.util.spec_from_file_location("design_render", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["design_render"] = mod
    spec.loader.exec_module(mod)
    return mod


def load_refusal():
    """Load the ui-acceptance skill's refusal formatter from the resolved tools."""
    for directory in tools_dirs():
        path = directory / "refusal.py"
        if not path.is_file():
            continue
        spec = importlib.util.spec_from_file_location("_extract_skeleton_refusal", path)
        if spec is None or spec.loader is None:
            break
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        return mod
    paths = ", ".join(str(directory / "refusal.py") for directory in tools_dirs())
    raise SystemExit(f"no refusal.py in the resolved ui-acceptance scripts ({paths})")


def load_conditions(dr, refusal, contract: Path) -> tuple[str, list[tuple[int, int]]]:
    """The two rendering conditions this command reads from the contract."""
    doc = dr.load_yaml(contract)
    locale = doc.get("locale")
    if not isinstance(locale, str) or not locale.strip():
        raise SystemExit(refusal.refusal(
            f"Top-level `locale` is missing from {contract.name}.",
            "extract_skeleton.py does not invent the product language.",
            "Add `locale` to the screen contract, then rerun."
        ))
    try:
        viewports = dr.parse_viewports(doc.get("viewports"))
    except (TypeError, ValueError) as exc:
        raise SystemExit(refusal.refusal(
            f"{contract.name} has invalid top-level `viewports` ({exc}).",
            "Every scene must be rendered at the contract's declared sizes.",
            "Add `viewports` as WIDTHxHEIGHT values, then rerun."
        )) from None
    return locale.strip(), viewports


def append_unique(values: list[str], value: str) -> None:
    if value and value not in values:
        values.append(value)


def accessible_name(dr, locator) -> str:
    """The first named or valued node in one element's accessibility snapshot."""
    snapshot = dr.accessibility_snapshot(locator)
    for raw in snapshot.splitlines():
        match = dr.ARIA_LINE.match(dr.unquote_key(raw))
        if not match:
            continue
        if match.group("name") is not None:
            return match.group("name")
        if match.group("value"):
            return match.group("value").strip()
    return ""


def main(handoff: Path, out: Path, contract: Path) -> None:
    dr = load_driver()
    locale, viewports = load_conditions(dr, load_refusal(), contract)
    scenes = json.loads((handoff / "scenes.json").read_text(encoding="utf-8"))
    pages = {
        dr.wrapper_path(scene["name"]): dr.wrapper_page(
            dr.component_of(scene["page"]), scene.get("props") or {})
        for scene in scenes
    }
    server, port = dr.serve_baseline(handoff, pages)
    origin = f"http://127.0.0.1:{port}"
    route = dr.baseline_router(origin, handoff, dr.DEFAULT_CACHE)

    from playwright.sync_api import sync_playwright
    rows: dict[tuple[str, str], dict] = {}
    per_scene: dict[str, set[tuple[str, str]]] = {scene["name"]: set() for scene in scenes}
    render_count = 0
    try:
        with tempfile.TemporaryDirectory(prefix="mmw-skeleton-") as tmp_name:
            tmp = Path(tmp_name)
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                try:
                    context = browser.new_context(
                        device_scale_factor=1, reduced_motion="reduce", locale=locale)
                    context.route("**/*", route)
                    page = context.new_page()
                    for scene in scenes:
                        for viewport in viewports:
                            dr.resize(page, viewport)
                            dr.navigate(page, f"{origin}{dr.wrapper_path(scene['name'])}")
                            dr.wait_for_mount(page, "#dc-root")
                            width, height = viewport
                            shot = dr.capture(
                                page, tmp / f"{scene['name']}-{width}x{height}.png",
                                selector="#dc-root")
                            locators = page.locator(
                                "#dc-root[data-ui], #dc-root [data-ui]")
                            for index, value in enumerate(shot.values):
                                if not value.get("visible"):
                                    continue
                                text = str(value.get("text") or "")
                                interactive = bool(value.get("interactive"))
                                if not interactive and not text:
                                    continue
                                data_ui = dr.plain_ui_id(str(value.get("id") or ""))
                                if not data_ui:
                                    continue
                                key = (scene["page"], data_ui)
                                row = rows.setdefault(key, {
                                    "page": scene["page"],
                                    "id": data_ui,
                                    "scenes": [],
                                    "interactive": False,
                                    "text": [],
                                    "names": [],
                                })
                                if scene["name"] not in row["scenes"]:
                                    row["scenes"].append(scene["name"])
                                row["interactive"] = row["interactive"] or interactive
                                name = accessible_name(dr, locators.nth(index))
                                append_unique(row["text"], text)
                                append_unique(row["names"], name)
                                per_scene[scene["name"]].add(key)
                            render_count += 1
                finally:
                    browser.close()
    finally:
        server.shutdown()
        server.server_close()

    table = sorted(rows.values(), key=lambda row: (row["page"], row["id"]))
    result = {
        "handoff": str(handoff),
        "locale": locale,
        "viewports": [f"{width}x{height}" for width, height in viewports],
        "scenes": len(scenes),
        "renders": render_count,
        "scene_x_element": sum(len(entries) for entries in per_scene.values()),
        "rows": len(table),
        "per_scene": {name: len(entries) for name, entries in per_scene.items()},
        "scene_pages": {scene["name"]: scene["page"] for scene in scenes},
        "table": table,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"scenes={result['scenes']} renders={render_count} "
          f"scene_x_element={result['scene_x_element']} rows={result['rows']} -> {out}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("handoff", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--contract", type=Path, required=True,
                        help="read locale and viewports from this screen contract")
    parser.add_argument("--tools", action="append", type=Path, default=[], metavar="DIR",
                        help="the ui-acceptance skill's scripts/; overrides the sibling lookup")
    return parser.parse_args(argv)


_BOOTSTRAP = "MMW_EXTRACT_SKELETON_BOOTSTRAPPED"


def _ensure_script_env() -> None:
    """Re-exec through the PEP 723 block when the caller used `uv run python`."""
    try:
        import playwright.sync_api  # noqa: F401
        import yaml  # noqa: F401
    except ImportError:
        if os.environ.get(_BOOTSTRAP) == "1":
            raise SystemExit("extract_skeleton.py is missing playwright or pyyaml after "
                             "uv run --script; install those with the script's metadata")
        env = dict(os.environ)
        env[_BOOTSTRAP] = "1"
        os.execvpe("uv", ["uv", "run", "--script", str(Path(__file__).resolve()),
                          *sys.argv[1:]], env)


if __name__ == "__main__":
    _ensure_script_env()
    args = parse_args(sys.argv[1:])
    TOOLS[:] = [directory.resolve() for directory in args.tools]
    main(args.handoff.resolve(), args.out.resolve(), args.contract.resolve())
