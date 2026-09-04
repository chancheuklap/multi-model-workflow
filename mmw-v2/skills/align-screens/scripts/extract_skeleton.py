"""Render every scene of a handoff package once, offline, and write what the rest of the
pipeline reads from that render.

Usage: uv run python extract_skeleton.py <handoff dir> <out.json> [--targets <dir> [--contract <yaml>]]

One render per scene in `scenes.json`, through the same driver interface parity uses
(`verify-ticket/scripts/screen_driver.py`, installed beside this skill), so what comes
out here is what the judge will read. Three things come out:

- `<out.json>`, the skeleton: every interactive control keyed by (page, role,
  accessible name) with the scenes it is visible in — the row inventory the contract
  is linted against — plus, per scene, its normalised tree and its class set.
- With `--targets <dir>`: one `<page>.aria` and one `<page>.classes` file per design
  page under that directory, holding every scene of the page. These are the handoff
  package's behavioural counterpart — the half of it a worker and the judge read
  directly — and a derived view: the package is the baseline, and each file carries the
  sha256 of `scenes.json` and of its page so the lint can tell when it has gone stale.
- With `--contract <yaml>` beside `--targets`: the contract's `retired_ids` triggers are
  hidden before the tree is read, as the judge hides them.

Needs Playwright with Chromium. The three CDN scripts `support.js` loads are answered
from the package's `vendor/` directory, else a local cache, else fetched once.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

INTERACTIVE = {"button", "textbox", "checkbox", "combobox", "link", "tab", "radio",
               "switch", "slider", "menuitem", "searchbox", "spinbutton"}
LINE = re.compile(r'^\s*-\s+(\w+)(?:\s+"((?:[^"\\]|\\.)*)")?')
TARGET_HEADER = "# target trees of the handoff package page: "
CLASSES_HEADER = "# class sets of the handoff package page: "
DERIVED_LINE = ("# derived by align-screens extract_skeleton.py — the handoff package is the "
                "baseline and this file is its readable view; the lint fails when the hashes "
                "below no longer match the package")


def load_driver():
    here = Path(__file__).resolve()
    candidates = [here.parents[2] / "verify-ticket/scripts/screen_driver.py"]
    for base in (Path.home() / ".agents/skills", Path.home() / ".claude/skills"):
        candidates.append(base / "verify-ticket/scripts/screen_driver.py")
    for p in candidates:
        if p.exists():
            spec = importlib.util.spec_from_file_location("screen_driver", p)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["screen_driver"] = mod
            spec.loader.exec_module(mod)
            return mod
    raise SystemExit("screen_driver.py not found; install the verify-ticket skill")


def controls(aria: str) -> list[tuple[str, str]]:
    found = []
    for raw in aria.splitlines():
        m = LINE.match(raw)
        if m and m.group(1) in INTERACTIVE:
            found.append((m.group(1), m.group(2) or ""))
    return found


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def page_stem(page: str) -> str:
    return re.sub(r"\.dc\.html$", "", page)


def target_files(targets: Path, page: str) -> tuple[Path, Path]:
    stem = page_stem(page)
    return targets / f"{stem}.aria", targets / f"{stem}.classes"


def write_targets(targets: Path, handoff: Path, scenes: list[dict], trees: dict[str, list[str]],
                  classes: dict[str, list[str]]) -> list[Path]:
    targets.mkdir(parents=True, exist_ok=True)
    scenes_hash = sha256_of(handoff / "scenes.json")
    written = []
    by_page: dict[str, list[dict]] = {}
    for s in scenes:
        by_page.setdefault(s["page"], []).append(s)
    for page, entries in sorted(by_page.items()):
        page_hash = sha256_of(handoff / page)
        aria_file, classes_file = target_files(targets, page)
        head = [f"# scenes.json sha256={scenes_hash}", f"# page sha256={page_hash}"]
        lines = [TARGET_HEADER + page, DERIVED_LINE, *head, ""]
        for s in entries:
            lines.append(f"## scene {s['name']}")
            lines.extend(trees[s["name"]])
            lines.append("")
        aria_file.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")
        lines = [CLASSES_HEADER + page, DERIVED_LINE, *head, ""]
        for s in entries:
            lines.append(f"## scene {s['name']}")
            lines.extend(classes[s["name"]])
            lines.append("")
        classes_file.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")
        written += [aria_file, classes_file]
    return written


def read_target_hashes(path: Path) -> dict[str, str]:
    """`{"scenes.json": sha, "page": sha}` from a target file's header, `{}` if absent."""
    out = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines()[:6]:
        m = re.match(r"^# (scenes\.json|page) sha256=([0-9a-f]{64})$", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def main(handoff: Path, out: Path, targets: Path | None, contract: Path | None) -> None:
    sd = load_driver()
    scenes = json.loads((handoff / "scenes.json").read_text(encoding="utf-8"))
    pages = {sd.wrapper_path(s["name"]): sd.wrapper_page(sd.component_of(s["page"]),
                                                          s.get("props") or {})
             for s in scenes}
    server, port = sd.serve_baseline(handoff, pages)
    origin = f"http://127.0.0.1:{port}"
    route = sd.baseline_router(origin, handoff, sd.DEFAULT_CACHE)
    hide_js = None
    if contract is not None:
        import yaml
        doc = yaml.safe_load(contract.read_text(encoding="utf-8")) or {}
        retired = sd.retired_triggers(doc)
        hide_js = sd.hide_retired_js(retired) if retired else None

    from playwright.sync_api import sync_playwright
    rows: dict[tuple[str, str, str], dict] = {}
    per_scene: dict[str, int] = {}
    trees: dict[str, list[str]] = {}
    classes: dict[str, list[str]] = {}
    tmp = Path(tempfile.mkdtemp())
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1,
                                  reduced_motion="reduce", locale="zh-CN")
        ctx.route("**/*", route)
        page = ctx.new_page()
        for s in scenes:
            sd.navigate(page, f"{origin}{sd.wrapper_path(s['name'])}")
            sd.wait_for_mount(page, "#dc-root")
            shot = sd.capture(page, tmp / f"{s['name']}.png", selector="#dc-root",
                              extra_js=hide_js)
            found = controls(shot.aria)
            per_scene[s["name"]] = len(found)
            trees[s["name"]] = sd.normalize_aria(shot.aria)
            classes[s["name"]] = sorted(shot.classes)
            for role, name in found:
                row = rows.setdefault((s["page"], role, name),
                                      {"page": s["page"], "role": role, "name": name, "scenes": []})
                if s["name"] not in row["scenes"]:
                    row["scenes"].append(s["name"])
        browser.close()
    server.shutdown()
    result = {"handoff": str(handoff), "scenes": len(scenes),
              "scene_x_control": sum(per_scene.values()), "rows": len(rows),
              "per_scene": per_scene,
              "scene_pages": {s["name"]: s["page"] for s in scenes},
              "trees": trees, "classes": classes,
              "table": sorted(rows.values(), key=lambda r: (r["page"], r["role"], r["name"]))}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"scenes={result['scenes']} scene_x_control={result['scene_x_control']} "
          f"rows={result['rows']} -> {out}")
    if targets is not None:
        written = write_targets(targets, handoff, scenes, trees, classes)
        print(f"targets: {len(written)} files under {targets}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("handoff", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--targets", type=Path, default=None,
                   help="write one .aria and one .classes file per design page here")
    p.add_argument("--contract", type=Path, default=None,
                   help="hide this contract's retired_ids triggers before reading the tree")
    return p.parse_args(argv)


if __name__ == "__main__":
    a = parse_args(sys.argv[1:])
    main(a.handoff.resolve(), a.out.resolve(),
         a.targets.resolve() if a.targets else None,
         a.contract.resolve() if a.contract else None)
