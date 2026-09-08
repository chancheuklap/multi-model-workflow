#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy>=2", "Pillow>=10", "playwright>=1.58", "pyyaml>=6"]
# ///
"""Pixel and tree helpers the story judge imports.

`story-parity.py` compares a product story page with the design page it was built
from. The comparison primitives live here so both that judge and its tests share one
implementation: `diff_images`, `pixel_diff`, `around`, `change_lines`, `text_changes`,
`failures`, `gate`, `Comparison`, `Reason`, plus `render_only` for the design side
with no product. Invoking this file as a command exits 2 and names `story-parity.py`.
"""

from __future__ import annotations

import importlib.util
import sys
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
# 5%, not 3%: pinning the design side to the box the product measured lands half a
# pixel off whenever the component's height is not a whole number, and that alone
# costs a tall component about 2% before it has drawn anything wrong (agentflow #710,
# 2026-09-08: a 1440×632 card differed by 1.8–2.1%, and 4087 of its 4417 differing
# pixels were the outermost one-pixel ring). A budget the framing eats two thirds of
# is not a budget.
DEFAULT_MAX_PCT = 5.0
# How many implementation elements a pixel failure names under `around:`.
AROUND_LIMIT = 5

NEGATIVE_CONTROL_SCENE = "__negative_control__"
NEGATIVE_CONTROL_HEAD = """<style>#dc-root::before{content:'NEGATIVE CONTROL';position:absolute;top:0;left:0;right:0;height:120px;background:#ff2d55;color:#fff;font:32px/120px sans-serif;text-align:center;z-index:2147483647}</style>
<script>(function(){var t=setInterval(function(){var r=document.querySelector('#dc-root');if(!r||!r.firstChild)return;clearInterval(t);var b=document.createElement('h1');b.textContent='NEGATIVE CONTROL';b.setAttribute('style','margin:0;padding:24px;background:#ff2d55;color:#fff');r.insertBefore(b,r.firstChild);},50);})();</script>"""

# Re-exported for the tests and for `extract_skeleton.py`, which read the tree through
# this module's name.
normalize_aria = sd.normalize_aria
aria_diff = sd.aria_diff
resize = sd.resize
wrapper_page = sd.wrapper_page
serve_baseline = sd.serve_baseline
cdn_path = sd.cdn_path
CDN_PREFIX = sd.CDN_PREFIX
frame_box = sd.frame_box
parse_viewports = sd.parse_viewports


# ---------------------------------------------------------------- pixels
def _shifted_cells(img, scale: int, cells: tuple[int, int], offset: tuple[int, int]):
    """`img` as `scale`x`scale` box averages whose grid starts `offset` pixels in.

    The grid keeps an unshifted grid's origin and is at most `cells` wide and tall: a
    shift eats up to one cell off the right and the bottom, and those cells are left with
    the unshifted comparison. `None` when the shift leaves less than one whole cell."""
    import numpy as np
    from PIL import Image
    ox, oy = offset
    w = min(cells[0], max(0, (img.width - ox) // scale))
    h = min(cells[1], max(0, (img.height - oy) // scale))
    if w < 1 or h < 1:
        return None
    crop = img.crop((ox, oy, ox + w * scale, oy + h * scale))
    return np.asarray(crop.resize((w, h), Image.BOX), dtype=np.int16)


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
        return {"size_equal": False, "pct": 100.0, "pct_unaligned": 100.0, "count": None,
                "total": None, "box": None, "mask": None,
                "size_a": tuple(ia.size), "size_b": tuple(ib.size)}
    import numpy as np
    from PIL import Image

    small = (max(1, ia.width // scale), max(1, ia.height // scale))
    na = np.asarray(ia.resize(small, Image.BOX), dtype=np.int16)
    nb = np.asarray(ib.resize(small, Image.BOX), dtype=np.int16)
    unaligned = np.abs(na - nb).max(axis=2)
    best = unaligned.copy()
    for oy in range(scale):
        for ox in range(scale):
            if not ox and not oy:
                continue
            for shifted, fixed in ((_shifted_cells(ib, scale, small, (ox, oy)), na),
                                   (_shifted_cells(ia, scale, small, (ox, oy)), nb)):
                if shifted is None:
                    continue
                h, w = shifted.shape[0], shifted.shape[1]
                here = np.abs(fixed[:h, :w] - shifted).max(axis=2)
                np.minimum(best[:h, :w], here, out=best[:h, :w])
    mask = best > PIXEL_TOLERANCE
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
    return {"size_equal": True, "pct": round(100 * count / total, 3),
            "pct_unaligned": round(100 * int((unaligned > PIXEL_TOLERANCE).sum()) / total, 3),
            "count": count, "total": total, "box": box, "mask": mask, "scale": scale,
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


def around(pixel: dict, elements: list[dict], limit: int = AROUND_LIMIT) -> list[str]:
    """The labels of the elements the differing cells actually fall in, most first.

    Ranked by how many differing cells sit inside each element's own box, ties going to
    the smaller element. Ranking by the bounding box of every differing cell — which is
    what this did — answers a different question: on a difference that spans a card, that
    box *is* the card, so the list came back as the card's five smallest labels wherever
    the difference happened to be. On agentflow#640 an agent read such a list as the
    place to look and spent hours on elements the difference was not in."""
    mask = pixel.get("mask")
    if mask is None or not elements:
        return []
    scale = pixel.get("scale") or PIXEL_SCALE
    hits: list[tuple[int, int, str]] = []
    for e in elements:
        if e["w"] <= 0 or e["h"] <= 0:
            continue
        y0, x0 = max(0, int(e["y"]) // scale), max(0, int(e["x"]) // scale)
        y1, x1 = int(e["y"] + e["h"] - 1) // scale, int(e["x"] + e["w"] - 1) // scale
        inside = int(mask[y0:y1 + 1, x0:x1 + 1].sum())
        if inside:
            hits.append((-inside, e["w"] * e["h"], e["label"]))
    out: list[str] = []
    for _, _, label in sorted(hits):
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
            "pixel",
            f"pixel {c.pixel['pct']}% > {max_pct}% "
            f"(unaligned {c.pixel.get('pct_unaligned', c.pixel['pct'])}%)",
            f"像素差 {c.pixel['pct']}%，超过 {max_pct}%"
            f"（未对齐口径 {c.pixel.get('pct_unaligned', c.pixel['pct'])}%）"))
    for side, side_zh, msgs in (("baseline", "基线", c.console_baseline),
                                ("impl", "实现", c.console_impl)):
        if len(msgs) > console_limit:
            joined = " | ".join(msgs)
            reasons.append(Reason(
                "console", f"{side} console: {joined}",
                f"{side_zh}页控制台有 {len(msgs)} 条 error：{joined}"))
    return reasons


def gate(control: Comparison, comparisons: list[Comparison], max_pct: float,
         console_limit: int, *,
         kinds: set[str] | None = None,
         ok_label: str = "PARITY OK",
         unaligned_on_diff: bool = False) -> tuple[int, list[str]]:
    """Exit code and the lines to print, in order. The negative control is judged
    before any scene: a comparison that did not catch a pair known to differ says
    nothing about the scenes it passed.

    `kinds` keeps only those reason kinds on each scene (the control still uses
    every reason `failures()` returns). `ok_label` is the success-line prefix.
    `unaligned_on_diff` puts the unaligned share on the `DIFF` prefix.
    """
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
        if kinds is not None:
            reasons = [r for r in reasons if r.kind in kinds]
        if c.pixel["size_equal"]:
            worst = max(worst, c.pixel["pct"])
        if reasons:
            failed += 1
            prefix = f"DIFF {c.scene} {c.viewport} {c.pixel['pct']}%"
            if unaligned_on_diff:
                unaligned = c.pixel.get("pct_unaligned", c.pixel["pct"])
                prefix += f" (unaligned {unaligned}%)"
            line = f"{prefix} — {'; '.join(r.en for r in reasons)}"
            if any(r.kind == "pixel" for r in reasons):
                names = around(c.pixel, c.impl_elements)
                if names:
                    line += " around: " + ", ".join(names)
            lines.append(line)
            lines.extend(change_lines(c.aria["diff"]))
    if failed:
        return 1, lines
    return 0, [f"{ok_label} {len(comparisons)}/{len(comparisons)} pixel<={worst}%"]


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

# ---------------------------------------------------------------- library helpers used by story-parity.py

def _join_js(*parts: str | None) -> str | None:
    """One script out of several, each of which is a complete expression.

    Every part here is an IIFE — `(() => { … })()`. Joined by a newline alone they
    are one expression, not two statements: JavaScript inserts no semicolon before
    `(`, so the second IIFE reads as a call on what the first returned, and the page
    fails with `is not a function`. The pages that carry both a `retired_ids` hide
    and a `volatile_values` paint are the ones that hit it.
    """
    bits = [p.strip() for p in parts if p]
    return ";\n".join(bits) if bits else None


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



def main(argv: list[str] | None = None) -> int:
    print("visual-parity.py is a library, not a command; "
          "run story-parity.py --contract FILE --pages ID[,ID]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
