# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy>=2", "Pillow>=10", "playwright>=1.58", "pyyaml>=6"]
# ///
"""Compare an interface against the handoff package it was built from, scene by scene.

    uv run visual-parity.py --contract docs/specs/<effort>/screen-contract.yaml --mount <id,id>

The screen contract says everything a run needs: where the handoff package is
(`baselines.look`), the sizes to compare at (`viewports`), which design page each scene
is on and where the product shows it (`pages`, `scenes`: `mount`, `route`, `reach`,
`open`), and what kind of product it is (`target.kind`). Addresses come from the
repository's `.mmw/target.json` through the driver beside this script,
`screen_driver.py`; no address is ever written on a criterion.

`--mount` names the product elements — `data-screen` attribute values — whose scenes
this run covers; every scene of the contract that declares one of them is compared.
`--scenes` narrows that to a subset, which is how one design page's scenes are split
between two tickets. A name outside the mounts is refused.

Two-level model
---------------
An `App · *` scene compares the whole surface — which components are on it, and what
box the layout gives each. A `Component · *` scene compares the block the product gives
that one component. That split rests on the `App · ` / `Component · ` page prefix the
`claude-design-blocks` skill enforces, not on anything the product does; a handoff
package that holds only whole-page designs makes every scene whole-surface, and the
model degrades to that without breaking.

Measure the box, declare no size
--------------------------------
The mount element is never pinned. The viewport is (the adapter pushes a device-metrics
override for every entry of `viewports`), the product lays the element out as it will,
and its box — `getBoundingClientRect()` after the override — is what the design's
`#dc-root` is pinned to for that scene. The two come out the same size by construction,
and no number appears in the contract. This rests on the porting convention that a
ported component fills its container (`#dc-root > * { height:100% }`). On a responsive
target the measured width may land in a media query other than the design's default,
and that is correct: the design is rendered at the width the product actually gives.

Two judges, two ranges — a written decision, not a default
----------------------------------------------------------
The accessibility tree is the main judge: the sequence of named nodes in reading order,
each with its nearest named ancestor, over the whole subtree under the mount, below the
fold included. Pixels are the second judge — colour, spacing, a block that did not
render — and see only the mount element's box intersected with the viewport, the
baseline being pinned to that same intersection. What is below the fold is judged by
the tree alone. The third judge is the class set of the subtree: the stylesheets are
copied byte for byte, so a wrong colour or gap on the right element can only be the
wrong class, which the tree cannot see and a pixel share cannot name.

Pixels: both screenshots are shrunk by `PIXEL_SCALE` (box average) before they are
compared, which removes glyph rendering and sub-`PIXEL_SCALE` offsets; the share of cells
that still differ is compared with `--max-pct`. Measured on ticket #548 of the chameleon
repository (2026-09-02, six scenes, two viewports): with the tree identical, the residue
from font rendering alone was 0.04%–1.52% after shrinking by 4; scenes whose copy and
layout were wrong measured 1.5%–31%, and every one of those also failed on the tree.

Controlled clock
----------------
Every page runs under a paused fake clock the driver moves forward in small steps: the
readiness poll of `support.js` fires, a focus effect fires, and none of the handoff
package's own timers (auto-advance, auto-recover, toast) ever does. Animations are off
through reduced motion on both sides.

Negative control across both sides
----------------------------------
After the first scene at the first viewport, the baseline server is made to serve, at
that scene's own address, the same scene with an error banner in the bytes it sends;
the implementation is captured again and compared with that render. The two must
differ. If they compare equal, the two capture chains have collapsed into one — the
implementation side is reading the design's server — and the run stops with exit 2,
because nothing it would go on to say could be trusted.

Exit codes
----------
Exit 0 and one line `PARITY OK <passed>/<total> pixel<=<worst>%` when every scene
matches at every viewport. Exit 1 with one `DIFF` line per failing pair, each followed
by the tree lines that differ and the class names one side lacks. Exit 2 when the
negative control fails, when the product is not ready, or when a scene cannot be
reached; then no parity conclusion is printed.

`--out` holds the screenshot, the tree and the differing-pixel picture for every scene
and viewport, for the user's eyes. `--render-only` renders the baseline side of the
selected scenes into `--out` and stops, needing no product — what a worker opens to see
what it is building. `--shows-perturbation` reseeds every scene with values other than
`data/fixtures.js` and requires each scene whose rows declare `shows` to read differently.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path


def _load_driver():
    here = Path(__file__).resolve().parent / "screen_driver.py"
    spec = importlib.util.spec_from_file_location("screen_driver", here)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["screen_driver"] = mod
    spec.loader.exec_module(mod)
    return mod


sd = _load_driver()

# A pixel counts as identical while every channel is within this of the other image's.
PIXEL_TOLERANCE = 16
# Both screenshots are shrunk by this factor (box average) before pixels are compared.
PIXEL_SCALE = 4
DEFAULT_MAX_PCT = 3.0
# How many implementation elements a pixel failure names under `around:`.
AROUND_LIMIT = 5
# How many class names a class failure prints per side.
CLASS_LIMIT = 8

NEGATIVE_CONTROL_SCENE = "__negative_control__"
NEGATIVE_CONTROL_HEAD = """<style>#dc-root::before{content:'NEGATIVE CONTROL';position:absolute;top:0;left:0;right:0;height:120px;background:#ff2d55;color:#fff;font:32px/120px sans-serif;text-align:center;z-index:2147483647}</style>
<script>(function(){var t=setInterval(function(){var r=document.querySelector('#dc-root');if(!r||!r.firstChild)return;clearInterval(t);var b=document.createElement('h1');b.textContent='NEGATIVE CONTROL';b.setAttribute('style','margin:0;padding:24px;background:#ff2d55;color:#fff');r.insertBefore(b,r.firstChild);},50);})();</script>"""

# Re-exported for the tests and for `extract_skeleton.py`, which read the tree through
# this module's name.
normalize_aria = sd.normalize_aria
aria_diff = sd.aria_diff
resize = sd.resize
impl_page_over_cdp = sd.page_by_title
wrapper_page = sd.wrapper_page
serve_baseline = sd.serve_baseline
cdn_path = sd.cdn_path
CDN_PREFIX = sd.CDN_PREFIX
frame_box = sd.frame_box
parse_viewports = sd.parse_viewports


# ---------------------------------------------------------------- pixels
def diff_images(ia, ib, out: Path | None = None, scale: int = PIXEL_SCALE) -> dict:
    """Two renders of the same scene, already loaded as RGB images.

    Images of unequal size are a failure on the spot: a scene that renders taller on
    one side is a difference, and scaling one to the other would hide it.

    Equal-sized images are shrunk by `scale` (each cell the average of a
    `scale`×`scale` block) and compared cell by cell. `pct` is the share of differing
    cells; `count` and `total` count cells; `box` is in the coordinates of the
    original image, so it can be placed on the screenshot.
    """
    if ia.size != ib.size:
        return {"size_equal": False, "pct": 100.0, "count": None, "total": None,
                "box": None, "size_a": tuple(ia.size), "size_b": tuple(ib.size)}
    import numpy as np
    from PIL import Image

    small = (max(1, ia.width // scale), max(1, ia.height // scale))
    na = np.asarray(ia.resize(small, Image.BOX), dtype=np.int16)
    nb = np.asarray(ib.resize(small, Image.BOX), dtype=np.int16)
    mask = (np.abs(na - nb) > PIXEL_TOLERANCE).any(axis=2)
    count, total = int(mask.sum()), int(mask.size)
    box = None
    if count:
        ys, xs = np.nonzero(mask)
        box = [int(xs.min()) * scale, int(ys.min()) * scale,
               (int(xs.max()) + 1) * scale - 1, (int(ys.max()) + 1) * scale - 1]
    if out is not None:
        full = np.asarray(ia, dtype=np.int16)
        vis = (full * 0.22 + 196).astype(np.uint8)
        big = np.kron(mask, np.ones((scale, scale), dtype=bool))
        vis[:big.shape[0], :big.shape[1]][big[:vis.shape[0], :vis.shape[1]]] = (230, 20, 60)
        Image.fromarray(vis).save(out)
    return {"size_equal": True, "pct": round(100 * count / total, 3), "count": count,
            "total": total, "box": box,
            "size_a": tuple(ia.size), "size_b": tuple(ib.size)}


def pixel_diff(a: Path, b: Path, out: Path | None = None) -> dict:
    from PIL import Image

    return diff_images(Image.open(a).convert("RGB"), Image.open(b).convert("RGB"), out)


# ---------------------------------------------------------------- the decision
@dataclass
class Comparison:
    scene: str
    viewport: str
    pixel: dict
    aria: dict
    console_baseline: list[str] = field(default_factory=list)
    console_impl: list[str] = field(default_factory=list)
    impl_elements: list[dict] = field(default_factory=list)
    classes: dict = field(default_factory=lambda: {"only_in_baseline": [], "only_in_impl": [],
                                                   "changed": 0})


def around(box: list[int] | None, elements: list[dict], limit: int = AROUND_LIMIT) -> list[str]:
    """The labels of the elements under a differing area, smallest first."""
    if not box or not elements:
        return []
    x0, y0, x1, y1 = box
    hits = []
    for e in elements:
        ex0, ey0 = e["x"], e["y"]
        ex1, ey1 = ex0 + e["w"], ey0 + e["h"]
        if e["w"] <= 0 or e["h"] <= 0 or ex1 < x0 or ex0 > x1 or ey1 < y0 or ey0 > y1:
            continue
        hits.append((e["w"] * e["h"], e["label"]))
    out: list[str] = []
    for _, label in sorted(hits, key=lambda h: h[0]):
        if label not in out:
            out.append(label)
        if len(out) == limit:
            break
    return out


@dataclass
class Reason:
    kind: str
    en: str
    zh: str

    def __str__(self) -> str:
        return self.en


def failures(c: Comparison, max_pct: float, console_limit: int) -> list[Reason]:
    """Every reason this pair fails. An empty list is a pass."""
    reasons = []
    if not c.pixel["size_equal"]:
        reasons.append(Reason(
            "size", f"size {c.pixel['size_a']} vs {c.pixel['size_b']}",
            f"两张图尺寸不等，基线 {c.pixel['size_a']}、实现 {c.pixel['size_b']}"))
    if c.aria["changed"]:
        reasons.append(Reason(
            "aria", f"aria {c.aria['changed']} changed lines",
            f"元素树差 {c.aria['changed']} 行"))
    if c.classes.get("changed"):
        reasons.append(Reason(
            "classes", f"classes {c.classes['changed']} differ",
            f"类名集合差 {c.classes['changed']} 个"))
    if c.pixel["size_equal"] and c.pixel["pct"] > max_pct:
        reasons.append(Reason(
            "pixel", f"pixel {c.pixel['pct']}% > {max_pct}%",
            f"像素差 {c.pixel['pct']}%，超过 {max_pct}%"))
    for side, side_zh, msgs in (("baseline", "基线", c.console_baseline),
                                ("impl", "实现", c.console_impl)):
        if len(msgs) > console_limit:
            joined = " | ".join(msgs)
            reasons.append(Reason(
                "console", f"{side} console: {joined}",
                f"{side_zh}页控制台有 {len(msgs)} 条 error：{joined}"))
    return reasons


def class_lines(classes: dict, limit: int = CLASS_LIMIT) -> list[str]:
    out = []
    for cls, el in classes.get("only_in_baseline", [])[:limit]:
        out.append(f"  class only in baseline  {cls}  (on {el})")
    for cls, el in classes.get("only_in_impl", [])[:limit]:
        out.append(f"  class only in impl      {cls}  (on {el})")
    return out


def gate(control: Comparison, comparisons: list[Comparison], max_pct: float,
         console_limit: int) -> tuple[int, list[str]]:
    """Exit code and the lines to print, in order. The negative control is judged
    before any scene: a comparison that did not catch a pair known to differ says
    nothing about the scenes it passed."""
    control_reasons = failures(control, max_pct, console_limit)
    if not control_reasons:
        return 2, ["NEGATIVE CONTROL FAILED: the implementation compared equal to a "
                   "baseline render served with an error banner; the two capture chains "
                   "have collapsed into one and this run proves nothing"]
    lines = []
    failed = 0
    worst = 0.0
    for c in comparisons:
        reasons = failures(c, max_pct, console_limit)
        if c.pixel["size_equal"]:
            worst = max(worst, c.pixel["pct"])
        if reasons:
            failed += 1
            box = c.pixel["box"]
            line = (f"DIFF {c.scene} {c.viewport} {c.pixel['pct']}% box={box} "
                    f"— {'; '.join(r.en for r in reasons)}")
            if any(r.kind == "pixel" for r in reasons):
                names = around(box, c.impl_elements)
                if names:
                    line += " around: " + ", ".join(names)
            lines.append(line)
            lines.extend(change_lines(c.aria["diff"]))
            lines.extend(class_lines(c.classes))
    if failed:
        return 1, lines
    return 0, [f"PARITY OK {len(comparisons)}/{len(comparisons)} pixel<={worst}%"]


# ---------------------------------------------------------------- reading the diff
def _split_ancestor(line: str) -> str:
    return line.split(" < ", 1)[0]


def text_changes(diff: str) -> list[dict]:
    """Say what changed in words, out of the tree's own unified diff."""
    removed, added, changes = [], [], []

    def flush():
        for i in range(max(len(removed), len(added))):
            before = removed[i] if i < len(removed) else None
            after = added[i] if i < len(added) else None
            if before and after and before["role"] == after["role"]:
                changes.append({"kind": "changed", "role": before["role"],
                                "before": before["text"], "after": after["text"]})
            elif before and after:
                changes.append({"kind": "replaced", "role": after["role"],
                                "before": f'{before["role"]} {before["text"]}'.strip(),
                                "after": f'{after["role"]} {after["text"]}'.strip()})
            elif before:
                changes.append({"kind": "removed", "role": before["role"],
                                "before": before["text"], "after": None})
            else:
                changes.append({"kind": "added", "role": after["role"],
                                "before": None, "after": after["text"]})
        removed.clear()
        added.clear()

    for line in diff.splitlines():
        if line.startswith(("+++", "---", "@@")):
            continue
        sign, rest = (line[:1], line[1:]) if line[:1] in "+- " else (" ", line)
        parsed = sd.ARIA_LINE.match(_split_ancestor(rest))
        if sign == " " or not parsed:
            flush()
            continue
        text = (parsed.group("name") or parsed.group("value") or "").strip()
        ancestor = rest.split(" < ", 1)[1] if " < " in rest else ""
        if ancestor:
            text = f"{text} (in {ancestor})"
        entry = {"role": parsed.group("role"), "text": text}
        (removed if sign == "-" else added).append(entry)
        if sign == "-" and added:
            flush()
            removed.append(entry)
    flush()
    return changes


def change_lines(diff: str) -> list[str]:
    out = []
    for change in text_changes(diff):
        role, before, after = change["role"], change["before"], change["after"]
        if change["kind"] == "changed":
            out.append(f"  baseline  {role} {before}")
            out.append(f"  impl      {role} {after}")
        elif change["kind"] == "removed":
            out.append(f"  only in baseline  {role} {before}")
        elif change["kind"] == "added":
            out.append(f"  only in impl      {role} {after}")
        else:
            out.append(f"  baseline  {before}")
            out.append(f"  impl      {after}")
    return out


# ---------------------------------------------------------------- arguments
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="visual-parity.py",
        usage="visual-parity.py --contract FILE --mount ID[,ID] [options]",
        description="Compare an interface with the handoff package it was built from, "
                    "scene by scene, by accessibility tree, class set and pixels.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--contract", required=True, metavar="FILE",
                   help="the screen contract; it names the handoff package, the viewports, "
                        "the target kind and every scene's mount, route, reach and open")
    p.add_argument("--mount", required=True, metavar="IDS",
                   help="comma-separated data-screen values; every scene declaring one of "
                        "them is compared")
    p.add_argument("--scenes", metavar="NAMES", default=None,
                   help="a subset of the scenes --mount derives, when a page's scenes are "
                        "split between tickets")
    p.add_argument("--max-pct", type=float, default=DEFAULT_MAX_PCT, metavar="PCT",
                   help=f"largest share of differing cells a scene may have, after both "
                        f"screenshots are shrunk by {PIXEL_SCALE} (default {DEFAULT_MAX_PCT})")
    p.add_argument("--out", metavar="DIR", default=None,
                   help="where the screenshots and trees are written")
    p.add_argument("--console-errors", type=int, default=0, metavar="N",
                   help="how many console errors a page may log")
    p.add_argument("--cdn", metavar="DIR", default=None,
                   help="cache for the scripts `support.js` loads, when the handoff package "
                        "carries no vendor/ copy")
    p.add_argument("--addressing", action="store_true",
                   help="the addressing self-check: for every selected scene, run its reach, "
                        "fill its route, navigate, and assert the mount element is there; no "
                        "open, no baseline, no comparison")
    p.add_argument("--render-only", action="store_true",
                   help="render the baseline side of the selected scenes into --out and "
                        "stop; no product is needed")
    p.add_argument("--shows-perturbation", action="store_true",
                   help="reseed every scene with values other than data/fixtures.js and "
                        "require each scene whose rows declare `shows` to read differently")
    return p


# ---------------------------------------------------------------- run
def run(args) -> int:
    root = sd.repo_root()
    contract_path = Path(args.contract)
    doc = sd.load_contract(contract_path)
    baseline = (root / doc["baselines"]["look"]).resolve()
    catalogue = sd.load_catalogue(baseline)
    viewports = sd.parse_viewports(doc["viewports"])
    mounts = [m.strip() for m in args.mount.split(",") if m.strip()]
    explicit = [s.strip() for s in args.scenes.split(",") if s.strip()] if args.scenes else None
    plan = sd.scene_plan(doc, catalogue, mounts, explicit)
    rows = sd.rows_by_id(doc)
    out = Path(args.out).resolve() if args.out else Path("./parity-shots").resolve()
    media = out / "media"
    media.mkdir(parents=True, exist_ok=True)
    cache = Path(args.cdn).expanduser() if args.cdn else sd.DEFAULT_CACHE

    pages = {sd.wrapper_path(s.name): sd.wrapper_page(sd.component_of(s.page), s.props)
             for s in plan}
    server, port = sd.serve_baseline(baseline, pages)
    origin = f"http://127.0.0.1:{port}"
    route_baseline = sd.baseline_router(origin, baseline, cache)
    hide_js = {s.name: sd.hide_js_for(doc, s.page) for s in plan}

    from playwright.sync_api import sync_playwright

    try:
        if args.render_only:
            return render_only(plan, viewports, media, origin, route_baseline, hide_js)
        adapter = sd.adapter_for(doc, root)
        if args.addressing:
            return addressing(adapter, plan, viewports[0])
        if args.shows_perturbation:
            return shows_perturbation(adapter, plan, viewports[0], rows, media)
        return parity(adapter, plan, viewports, rows, media, origin, pages, route_baseline,
                      hide_js, args)
    finally:
        server.shutdown()
        server.server_close()


def render_only(plan, viewports, media, origin, route_baseline, hide_js) -> int:
    from playwright.sync_api import sync_playwright

    vp = viewports[0]
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": vp[0], "height": vp[1]},
                                  device_scale_factor=1, reduced_motion="reduce",
                                  locale="zh-CN")
        ctx.route("**/*", route_baseline)
        page = ctx.new_page()
        for scene in plan:
            sd.navigate(page, f"{origin}{sd.wrapper_path(scene.name)}")
            sd.wait_for_mount(page, "#dc-root")
            sd.capture(page, media / f"{scene.name}-baseline.png", selector="#dc-root",
                       extra_js=hide_js[scene.name])
            print(f"rendered {scene.name} -> {media / (scene.name + '-baseline.png')}")
        browser.close()
    return 0


def addressing(adapter, plan, vp) -> int:
    """The contract ticket's check that needs no interface: the whole addressing model
    — the state can be put, the placeholders fill, the route is reachable, the mount is
    where the contract says — proved against an empty surface. Prints `ADDRESSING OK
    <n>/<n>` or one `UNREACHABLE <scene> — <why>` per scene that failed."""
    from playwright.sync_api import sync_playwright

    failed = []
    with sync_playwright() as pw:
        page = None
        try:
            for scene in plan:
                ok, why = adapter.ready()
                if not ok:
                    print(why, file=sys.stderr)
                    return 2
                try:
                    values = adapter.transport(scene.reach, {})
                    if page is None or adapter.reach_before_attach:
                        if page is not None:
                            adapter.release()
                        page = adapter.attach(pw, values)
                    sd.resize(page, vp, adapter.over_cdp)
                    sd.navigate(page, adapter.address(scene.route, values), reload=True)
                    sd.wait_for_mount(page, sd.mount_selector(scene.mount))
                except SystemExit as exc:
                    failed.append(f"UNREACHABLE {scene.name} — {exc}")
        finally:
            adapter.release()
    for line in failed:
        print(line)
    if failed:
        return 1
    print(f"ADDRESSING OK {len(plan)}/{len(plan)}")
    return 0


def shows_perturbation(adapter, plan, vp, rows, media) -> int:
    """Every scene twice: seeded from `data/fixtures.js`, then with other values. A
    scene whose rows declare `shows` must read differently, or a shown value is hard
    coded or fed from the wrong field."""
    from playwright.sync_api import sync_playwright

    failed = []
    with sync_playwright() as pw:
        page = None
        try:
            for scene in plan:
                ok, why = adapter.ready()
                if not ok:
                    print(why, file=sys.stderr)
                    return 2
                shows_rows = [rid for rid, r in rows.items()
                              if scene.name in (r.get("scenes") or []) and r.get("shows")]
                if not shows_rows:
                    continue
                trees = []
                for perturb in (False, True):
                    values = adapter.transport(scene.reach, {}, perturb=perturb)
                    if page is None or adapter.reach_before_attach:
                        page = adapter.attach(pw, values)
                    sd.resize(page, vp, adapter.over_cdp)
                    sd.navigate(page, adapter.address(scene.route, values), reload=True)
                    sel = sd.mount_selector(scene.mount)
                    sd.wait_for_mount(page, sel)
                    sd.perform(page, scene.open, rows, values)
                    if scene.clock:
                        sd.run_clock(page, scene.clock)
                    shot = sd.capture(page, media / f"{scene.name}-{'perturbed' if perturb else 'seeded'}.png",
                                      selector=sel)
                    trees.append(sd.normalize_aria(shot.aria))
                if trees[0] == trees[1]:
                    failed.append(f"SHOWS-STATIC {scene.name} — reads the same under perturbed "
                                  f"seed values; rows: {', '.join(shows_rows)}")
            # Leave the product seeded the way every other run expects.
            if plan:
                adapter.transport(plan[-1].reach, {}, perturb=False)
        finally:
            adapter.release()
    for line in failed:
        print(line)
    if failed:
        return 1
    print(f"SHOWS OK {len(plan)}/{len(plan)}")
    return 0


def parity(adapter, plan, viewports, rows, media, origin, pages, route_baseline, hide_js,
           args) -> int:
    from playwright.sync_api import sync_playwright

    comparisons: list[Comparison] = []
    control: Comparison | None = None
    with sync_playwright() as pw:
        page = None
        try:
            @contextmanager
            def baseline_page(vp):
                """A page for the handoff package side. Over CDP the application's own
                page is routed for the render and unrouted after; otherwise a context of
                this program's own."""
                ctx = adapter.new_context(vp)
                if ctx is None:
                    page.route("**/*", route_baseline)
                    try:
                        yield page
                    finally:
                        page.unroute("**/*", route_baseline)
                else:
                    ctx.route("**/*", route_baseline)
                    bp = ctx.new_page()
                    try:
                        yield bp
                    finally:
                        bp.close()
                        ctx.unroute("**/*", route_baseline)

            def capture_baseline(scene, vp, box, png, inline: bool = False):
                w, h = box[2], box[3]
                with baseline_page(vp) as bp:
                    sd.resize(bp, vp, adapter.over_cdp)
                    sd.navigate(bp, f"{origin}{sd.wrapper_path(scene.name)}")
                    sd.wait_for_mount(bp, "#dc-root")
                    return sd.capture(bp, png, selector="#dc-root", clip=(0, 0, w, h),
                                      extra_css=sd.frame_box((w, h)), extra_js=hide_js[scene.name])

            def capture_impl(scene, vp, png):
                sel = sd.mount_selector(scene.mount)
                sd.resize(page, vp, adapter.over_cdp)
                sd.navigate(page, adapter.address(scene.route, values), reload=True)
                sd.wait_for_mount(page, sel)
                sd.perform(page, scene.open, rows, values)
                if scene.clock:
                    sd.run_clock(page, scene.clock)
                box = sd.visible_box(page, sel, vp)
                return sd.capture(page, png, selector=sel, clip=box)

            for scene in plan:
                ok, why = adapter.ready()
                if not ok:
                    print(why, file=sys.stderr)
                    return 2
                values = adapter.transport(scene.reach, {})
                if page is None or adapter.reach_before_attach:
                    if page is not None:
                        adapter.release()
                    page = adapter.attach(pw, values)
                for vp in viewports:
                    tag_vp = f"{vp[0]}x{vp[1]}"
                    impl_shot = capture_impl(scene, vp, media / f"{scene.name}-{tag_vp}-impl.png")
                    base_shot = capture_baseline(scene, vp, impl_shot.box,
                                                 media / f"{scene.name}-{tag_vp}-baseline.png")
                    comparisons.append(Comparison(
                        scene.name, tag_vp,
                        pixel_diff(base_shot.png, impl_shot.png,
                                   media / f"{scene.name}-{tag_vp}-diff.png"),
                        sd.aria_diff(base_shot.aria, impl_shot.aria,
                                     media / f"{scene.name}-{tag_vp}.aria.diff"),
                        base_shot.console, impl_shot.console, impl_shot.elements,
                        sd.class_diff(base_shot.classes, impl_shot.classes)))
                    if control is None:
                        control = negative_control(scene, vp, pages, capture_impl,
                                                   capture_baseline, media)
        finally:
            adapter.release()

    code, lines = gate(control, comparisons, args.max_pct, args.console_errors)
    for line in lines:
        print(line)
    if code:
        print(f"screenshots and trees: {media}", file=sys.stderr)
    return code


def negative_control(scene, vp, pages, capture_impl, capture_baseline, media) -> Comparison:
    """The baseline server is made to answer this scene's own address with the scene
    plus an error banner in the served bytes; the implementation is captured again. If
    the two compare equal, the implementation capture went through the baseline
    server, and the run is worthless."""
    path = sd.wrapper_path(scene.name)
    saved = pages[path]
    pages[path] = sd.wrapper_page(sd.component_of(scene.page), scene.props,
                                  NEGATIVE_CONTROL_HEAD)
    tag_vp = f"{vp[0]}x{vp[1]}"
    stem = media / f"{NEGATIVE_CONTROL_SCENE}-{tag_vp}"
    try:
        impl = capture_impl(scene, vp, Path(f"{stem}-impl.png"))
        wrong = capture_baseline(scene, vp, impl.box, Path(f"{stem}-baseline.png"))
    finally:
        pages[path] = saved
    return Comparison(
        NEGATIVE_CONTROL_SCENE, tag_vp,
        pixel_diff(wrong.png, impl.png, Path(f"{stem}-diff.png")),
        sd.aria_diff(wrong.aria, impl.aria, Path(f"{stem}.aria.diff")),
        [], [], impl.elements, sd.class_diff(wrong.classes, impl.classes))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
