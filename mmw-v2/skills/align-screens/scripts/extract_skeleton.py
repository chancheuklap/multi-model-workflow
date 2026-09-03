"""Build the screen-contract row skeleton from a handoff package, offline.

Renders every scene in the package's scenes.json the way visual-parity.py does,
reads the accessibility tree of each, and keeps every interactive control keyed by
(page, role, accessible name) with the scenes it is visible in.

Usage: uv run python extract_skeleton.py <handoff dir> <out.json>
Needs: the verify-ticket skill installed beside this one (its visual-parity.py is
reused for the offline render), and Playwright with Chromium.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
import urllib.request
from pathlib import Path

INTERACTIVE = {"button", "textbox", "checkbox", "combobox", "link", "tab", "radio",
               "switch", "slider", "menuitem", "searchbox", "spinbutton"}
LINE = re.compile(r'^\s*-\s+(\w+)(?:\s+"((?:[^"\\]|\\.)*)")?')


def load_parity():
    here = Path(__file__).resolve()
    candidates = [here.parents[2] / "verify-ticket/scripts/visual-parity.py"]
    for base in (Path.home() / ".claude/skills", Path.home() / ".agents/skills"):
        candidates.append(base / "verify-ticket/scripts/visual-parity.py")
    for p in candidates:
        if p.exists():
            spec = importlib.util.spec_from_file_location("visual_parity", p)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["visual_parity"] = mod
            spec.loader.exec_module(mod)
            return mod
    raise SystemExit("visual-parity.py not found; install the verify-ticket skill")


def controls(aria: str) -> list[tuple[str, str]]:
    found = []
    for raw in aria.splitlines():
        m = LINE.match(raw)
        if m and m.group(1) in INTERACTIVE:
            found.append((m.group(1), m.group(2) or ""))
    return found


def main(handoff: Path, out: Path) -> None:
    vp = load_parity()
    scenes = json.loads((handoff / "scenes.json").read_text(encoding="utf-8"))
    pages = {f"/__parity-{s['name']}.dc.html": vp.wrapper_page(re.sub(r"\.dc\.html$", "", s["page"]),
                                                              s.get("props") or {}) for s in scenes}
    server, port = vp.serve_baseline(handoff, pages)
    origin = f"http://127.0.0.1:{port}"
    cache = Path.home() / ".cache/mmw/visual-parity"
    cache.mkdir(parents=True, exist_ok=True)

    def route(r, req):
        if req.url.startswith(origin):
            r.continue_()
        elif req.url.startswith(vp.CDN_PREFIX):
            t = vp.cdn_path(cache, req.url)
            if not t.exists():
                try:
                    urllib.request.urlretrieve(req.url, t)
                except Exception:
                    r.abort()
                    return
            r.fulfill(path=str(t), content_type="application/javascript")
        else:
            r.abort()

    from playwright.sync_api import sync_playwright
    rows: dict[tuple[str, str, str], dict] = {}
    per_scene: dict[str, int] = {}
    tmp = Path(tempfile.mkdtemp())
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1,
                                  reduced_motion="reduce", locale="zh-CN")
        ctx.route("**/*", route)
        page = ctx.new_page()
        for s in scenes:
            shot = vp.capture(page, f"{origin}/__parity-{s['name']}.dc.html", None, (1440, 900),
                              tmp / f"{s['name']}.png")
            found = controls(shot.aria)
            per_scene[s["name"]] = len(found)
            for role, name in found:
                row = rows.setdefault((s["page"], role, name),
                                      {"page": s["page"], "role": role, "name": name, "scenes": []})
                if s["name"] not in row["scenes"]:
                    row["scenes"].append(s["name"])
        browser.close()
    server.shutdown()
    result = {"handoff": str(handoff), "scenes": len(scenes), "scene_x_control": sum(per_scene.values()),
              "rows": len(rows), "per_scene": per_scene,
              "table": sorted(rows.values(), key=lambda r: (r["page"], r["role"], r["name"]))}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"scenes={result['scenes']} scene_x_control={result['scene_x_control']} rows={result['rows']} -> {out}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
