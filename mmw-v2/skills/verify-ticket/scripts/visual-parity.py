# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy>=2", "Pillow>=10", "playwright>=1.58"]
# ///
"""Compare an interface against the handoff package it was built from, scene by scene.

`--baseline` names the handoff package: the Claude Design project downloaded into a
leaf directory, holding the component's `.dc.html`, its `styles/`, `data/`,
`support.js`, and a `scenes.json` listing every scene by name. This tool renders each
named scene from that directory offline, opens the same scene on the implementation,
and compares the two by ARIA tree and by pixels at two viewports.

What decides a scene
--------------------
The accessibility tree is the main judge. It is read as the sequence of named nodes —
a button and its name, a heading and its text, a line of copy — in reading order;
unnamed wrappers (`generic`, `group`, `list`, an unnamed `region`) and landmark names
are not part of it, because a product page nests things differently from a component
page without showing anything different. A node missing, added, renamed, or given
another role fails the scene.

Pixels are the second judge, for what a tree cannot carry: colour, spacing, a block
that did not render. Both screenshots are shrunk by `PIXEL_SCALE` (box average) before
they are compared, which removes glyph rendering and sub-`PIXEL_SCALE` offsets; the
share of cells that still differ is compared with `--max-pct`. Measured on ticket
#548 of the chameleon repository (2026-09-02, six scenes, two viewports): with the
tree identical, the residue from font rendering alone was 0.04%–1.52% after shrinking
by 4; scenes whose copy and layout were wrong measured 1.5%–31%, and every one of those
also failed on the tree. The default of 3% leaves the residue a margin of one time
its own size.

How a non-default scene is rendered from the handoff package
-----------------------------------------------------
A scene in Claude Design is a prop on the component, set from the Tweaks panel, not a
URL parameter. This tool writes one wrapper page per scene holding a single
`<dc-import name="<component>" scenario="<scene>">`, and serves it from the handoff
package's own URL space (`support.js` resolves a sibling component as
`./<name>.dc.html`). The wrapper pages exist only in the server's memory; no file in
the handoff package is read as anything but bytes to send.

Measured on 2026-08-30 against `prototypes/code-landing/fixture/baseline`: a hardcoded
`scenario` attribute on `<dc-import>` does switch the component. Rendering
`scenario="default"` printed "5 个任务" and five queue rows; rendering
`scenario="queue-empty"` printed "0 个任务" and the empty-state line "还没有生成任务";
both with an empty console. `support.js` reaches the attribute through `collectProps`
(`kind="dc-import"`) and passes it straight into the component's props, so the
`parseDataProps` route — injecting props through the `data-props` attribute — is not
needed and is not used here.

Usage
-----
    uv run visual-parity.py --baseline <dir> --impl <url> --scenes a,b --out <dir>

An implementation that is not a page on a web server — an Electron application, say —
is compared where it already runs, by connecting to its debugging port:

    uv run visual-parity.py --baseline <dir> --cdp http://127.0.0.1:9229 \
        --impl http://127.0.0.1:5173/ --scenes a,b

`--cdp` says which browser; `--impl` still says where to navigate, because a scene is
reached by its query string: `scene=<name>` plus the scene's props from `scenes.json`.
That browser renders the handoff package too, so both sides come out of one engine with
one set of fonts: two browsers measure a line of text a fraction of a pixel apart, which
is enough to break a line on one side and move everything below it. The application is
left running afterwards. Only what its renderer draws is compared: the size of its
operating-system window is not, so a window minimum is checked by the user, not here.

Exit 0 and one line `PARITY OK <passed>/<total> pixel<=<worst>%` when every scene
matches at every viewport; the number is the largest pixel share any pair had, so a
difference under the threshold is still on record.
Exit 1 with one `DIFF` line per failing pair, each followed by the ARIA tree lines
that differ — the name of the button or the line of copy, as text, which is what a
reader has to change. A pixel failure names the implementation's elements under the
differing area after `around:`, so the reader is sent to a component, not a
coordinate. Exit 2 when the built-in negative control fails, in which case
no parity conclusion is printed at all.

`--out` holds the screenshot, the ARIA tree, and the differing-pixel picture for
every scene and viewport, for the differences an ARIA tree cannot carry: spacing,
colour, alignment. Nothing reads them but the user, and only when the printed lines
are not enough.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import http.server
import json
import re
import socketserver
import sys
import threading
import time
import urllib.parse
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

# A pixel counts as identical while every channel is within this of the other image's.
PIXEL_TOLERANCE = 16
# Both screenshots are shrunk by this factor (box average) before pixels are compared.
PIXEL_SCALE = 4
DEFAULT_MAX_PCT = 3.0
# How many implementation elements a pixel failure names under `around:`.
AROUND_LIMIT = 5

# Roles whose accessible name is dropped: a product page labels its `<main>`, a
# component page does not, and the landmark itself is what matters.
LANDMARKS = {"main", "navigation", "banner", "contentinfo", "region", "complementary"}

# The three scripts `support.js` loads from unpkg. Answered from a local cache so the
# handoff package renders with no network.
CDN_PREFIX = "https://unpkg.com/"

DEFAULT_VIEWPORTS = "1440x900,1180x720"
SETTLE_MS = 1000  # after networkidle, for `support.js`'s own readiness poll

NEGATIVE_CONTROL_SCENE = "__negative_control__"
NEGATIVE_CONTROL_CSS = (
    "#dc-root::before{content:'NEGATIVE CONTROL';position:absolute;top:0;left:0;"
    "right:0;height:120px;background:#ff2d55;color:#fff;font:32px/120px sans-serif;"
    "text-align:center;z-index:2147483647}"
)
NEGATIVE_CONTROL_JS = (
    "(() => { const r = document.querySelector('#dc-root'); if (!r) return;"
    " const b = document.createElement('h1'); b.textContent = 'NEGATIVE CONTROL';"
    " b.setAttribute('style', 'margin:0;padding:24px;background:#ff2d55;color:#fff');"
    " r.insertBefore(b, r.firstChild); })()"
)


# ---------------------------------------------------------------- ARIA
ARIA_LINE = re.compile(
    r'^\s*- (?P<role>[a-zA-Z]+)(?: "(?P<name>(?:[^"\\]|\\.)*)")?'
    r'(?P<attrs>(?: \[[^\]]*\])*)(?::\s*(?P<value>.*))?\s*$')


def normalize_aria(text: str) -> list[str]:
    """The named nodes of a Playwright ARIA snapshot, flat, in reading order.

    Each line is `- <role> "<name>"<attrs>` or `- <role>: <value>`, without indent.
    Kept: every node that carries a name or a value — a control, a heading, a line of
    copy — with its attributes (`[level=2]`, `[checked]`). Dropped: nodes with neither,
    the accessible name of a landmark role, and lines that are not nodes. Nesting is
    dropped with the indent: an app page wraps a component in one more `main` and a
    product page in `list` and `article`, and none of that shows on screen.
    """
    out = []
    for ln in text.splitlines():
        m = ARIA_LINE.match(ln)
        if not m:
            continue
        role, name, attrs, value = (m.group("role"), m.group("name"),
                                    m.group("attrs") or "", m.group("value"))
        if role in LANDMARKS:
            name = None
        if name is None and not value and not attrs.strip():
            continue
        if value:
            out.append(f"- {role}: {value.strip()}")
        elif name is not None:
            out.append(f'- {role} "{name}"{attrs}')
        else:
            out.append(f"- {role}{attrs}")
    return out


def aria_diff(a: str, b: str, out: Path | None = None) -> dict:
    la, lb = normalize_aria(a), normalize_aria(b)
    diff = list(difflib.unified_diff(la, lb, "baseline", "impl", lineterm="", n=1))
    if out is not None:
        out.write_text("\n".join(diff) + ("\n" if diff else ""), encoding="utf-8")
    changed = sum(1 for d in diff if d[:1] in "+-" and not d.startswith(("+++", "---")))
    return {"lines_a": len(la), "lines_b": len(lb), "changed": changed,
            "diff": "\n".join(diff)}


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
        # A washed-out baseline under the red, so the differing cells can be placed
        # on the page they belong to rather than on a black field.
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
    # The implementation's elements with a label and a box, for naming a pixel failure.
    impl_elements: list[dict] = field(default_factory=list)


def around(box: list[int] | None, elements: list[dict], limit: int = AROUND_LIMIT) -> list[str]:
    """The labels of the elements under a differing area, smallest first.

    Smallest first because the page and its main column overlap every box; the
    element a reader has to open is the one that fits the area, not the one that
    contains it. Same label once.
    """
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
    """Why a pair failed, said once in the line a machine reads and once in the line
    a person reads, so the two cannot drift apart."""
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
            "size",
            f"size {c.pixel['size_a']} vs {c.pixel['size_b']}",
            f"两张图尺寸不等，基线 {c.pixel['size_a']}、实现 {c.pixel['size_b']}"))
    if c.aria["changed"]:
        reasons.append(Reason(
            "aria",
            f"aria {c.aria['changed']} changed lines",
            f"ARIA 树差 {c.aria['changed']} 行"))
    if c.pixel["size_equal"] and c.pixel["pct"] > max_pct:
        reasons.append(Reason(
            "pixel",
            f"pixel {c.pixel['pct']}% > {max_pct}%",
            f"像素差 {c.pixel['pct']}%，超过 {max_pct}%"))
    for side, side_zh, msgs in (("baseline", "基线", c.console_baseline),
                                ("impl", "实现", c.console_impl)):
        if len(msgs) > console_limit:
            joined = " | ".join(msgs)
            reasons.append(Reason(
                "console",
                f"{side} console: {joined}",
                f"{side_zh}页控制台有 {len(msgs)} 条 error：{joined}"))
    return reasons


def gate(control: Comparison, comparisons: list[Comparison], max_pct: float,
         console_limit: int) -> tuple[int, list[str]]:
    """Exit code and the lines to print, in order.

    The negative control is constructed once, after every scene of the first viewport
    has run, and its result is applied before any scene's: it is the only thing
    reported when it fails, because a comparison that did not catch a scene known to be
    wrong says nothing about the scenes it passed.
    """
    control_reasons = failures(control, max_pct, console_limit)
    if not control_reasons:
        return 2, ["NEGATIVE CONTROL FAILED: a baseline render with an inserted error "
                   "banner compared equal; this run proves nothing"]
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
    if failed:
        return 1, lines
    return 0, [f"PARITY OK {len(comparisons)}/{len(comparisons)} pixel<={worst}%"]


# ---------------------------------------------------------------- baseline server
def wrapper_page(component: str, props: dict) -> str:
    """One page holding one `dc-import`, pinned to a scene.

    Follows `claude-design-blocks/scripts/mkharness.py`, minus the `<select>`: the
    scene is written into the attribute instead of driven from state.
    """
    attrs = []
    for key, value in props.items():
        literal = value if isinstance(value, str) else "{{ %s }}" % json.dumps(value)
        attrs.append(f'{key}="{_attr(literal)}"')
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8" /><script src="./support.js"></script></head>
<body><x-dc>
<helmet data-dc-atomics><style>html, body {{ margin: 0; height: 100%; }}
#dc-root, #dc-root .sc-host {{ height: 100%; }}</style></helmet>
<dc-import name="{_attr(component)}" {" ".join(attrs)} hint-size="100%,100%"></dc-import>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{}}'>
class Component extends DCLogic {{ renderVals() {{ return {{}}; }} }}
</script></body></html>"""


def _attr(value: str) -> str:
    return value.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


class _Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def serve_baseline(root: Path, pages: dict[str, str]) -> tuple[_Server, int]:
    """Serve `root` read-only, with the wrapper pages answered from memory."""

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(root), **k)

        def log_message(self, *a):
            pass

        def do_GET(self):
            path = urllib.parse.unquote(self.path.split("?", 1)[0])
            body = pages.get(path)
            if body is None:
                super().do_GET()
                return
            raw = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    srv = _Server(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def cdn_path(cache: Path, url: str) -> Path:
    name = url.rsplit("/", 1)[-1].split("?", 1)[0] or "asset.js"
    return cache / f"{hashlib.sha256(url.encode()).hexdigest()[:12]}-{name}"


# ---------------------------------------------------------------- capture
@dataclass
class Shot:
    png: Path
    aria: str
    console: list[str] = field(default_factory=list)
    elements: list[dict] = field(default_factory=list)


# Every element a reader could be sent to, with the name it goes by: its `aria-label`,
# else its own text, else its `alt`. Boxes are viewport CSS pixels, the screenshot's.
ELEMENTS_JS = """(() => {
  const sel = 'button, a, input, select, textarea, label, img, h1, h2, h3, h4, h5, h6, ' +
              'p, li, strong, em, [role], [aria-label]';
  const out = [];
  for (const el of document.querySelectorAll(sel)) {
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    const role = el.getAttribute('role') || el.tagName.toLowerCase();
    const text = (el.getAttribute('aria-label') || el.innerText || el.getAttribute('alt') || '')
      .trim().replace(/\\s+/g, ' ').slice(0, 40);
    if (!text) continue;
    out.push({label: role + ' "' + text + '"', x: r.left, y: r.top, w: r.width, h: r.height});
  }
  return out;
})()"""


def resize(page, viewport: tuple[int, int], over_cdp: bool) -> None:
    """Put the page in a window of this size, however it was reached.

    A context this program launched was given its viewport and its device pixel ratio
    when it was created. A page reached over CDP belongs to the application, whose
    context was created by somebody else and cannot be given either — so the size and
    the ratio are pushed down as a device-metrics override instead. The ratio has to be
    said out loud there: on a high-resolution screen the application renders at two
    device pixels per CSS pixel, and a screenshot twice the size of the baseline's is a
    failure before anything is compared.
    """
    if over_cdp:
        page.context.new_cdp_session(page).send(
            "Emulation.setDeviceMetricsOverride",
            {"width": viewport[0], "height": viewport[1],
             "deviceScaleFactor": 1, "mobile": False})
        page.emulate_media(reduced_motion="reduce")
    else:
        page.set_viewport_size({"width": viewport[0], "height": viewport[1]})


def capture(page, url: str, selector: str | None, viewport: tuple[int, int], png: Path,
            extra_css: str | None = None, extra_js: str | None = None,
            over_cdp: bool = False) -> Shot:
    console: list[str] = []

    def on_console(message):
        if message.type == "error":
            console.append(f"{message.type}: {message.text}")

    def on_pageerror(error):
        console.append(f"pageerror: {error}")

    # Removed again at the end: a page reached over CDP is the application's own and is
    # used for every scene, so listeners left behind would go on appending to the list
    # of a scene already recorded.
    page.on("console", on_console)
    page.on("pageerror", on_pageerror)
    try:
        resize(page, viewport, over_cdp)
        page.goto(url, wait_until="networkidle")
        if extra_css:
            page.add_style_tag(content=extra_css)
        page.wait_for_timeout(SETTLE_MS)
        if extra_js:
            page.evaluate(extra_js)
            page.wait_for_timeout(200)
        target = page.locator(selector or "body").first
        target.wait_for(state="visible", timeout=15000)
        shot_at = {"path": str(png), "scale": "css"}
        if selector:
            target.screenshot(**shot_at)
        else:
            page.screenshot(**shot_at)
        aria = name_options_from_dom(target.aria_snapshot(),
                                     target.evaluate(OPTION_TEXT_JS))
        elements = page.evaluate(ELEMENTS_JS)
    finally:
        page.remove_listener("console", on_console)
        page.remove_listener("pageerror", on_pageerror)
    aria_path(png).write_text(aria, encoding="utf-8")
    return Shot(png, aria, console, elements)


def impl_page_over_cdp(browser, title_includes: str | None, timeout_seconds: int = 15):
    """The application's own page, out of a browser this program connected to.

    Picked by a substring of the window title rather than of the URL: a development
    server takes whichever port is free at startup, so the URL is not the same twice.
    With no substring given the first page is taken, which is what an application with
    one window has.
    """
    deadline = time.monotonic() + timeout_seconds
    seen: list[str] = []
    while True:
        seen = []
        for context in browser.contexts:
            for page in context.pages:
                title = page.title() or ""
                seen.append(f"{title!r} @ {page.url}")
                if not title_includes or title_includes in title:
                    return page
        # Looked at once before the clock is read, so that however short the wait is,
        # the refusal below can still say which windows were there.
        if time.monotonic() >= deadline:
            break
        time.sleep(0.5)
    raise SystemExit(
        f"no page whose title holds {title_includes!r} within {timeout_seconds}s. "
        f"Pages found: {seen or 'none'}")


def aria_path(png: Path) -> Path:
    """The ARIA snapshot saved beside a screenshot, under the same name."""
    return png.with_name(png.name.removesuffix(".png") + ".aria.yml")


# An `<option>`'s accessible name is computed from its own child text nodes alone. The
# Claude Design runtime wraps every `{{ }}` hole in a `span.sc-interp`, which takes the
# text out of those nodes, so a handoff package reports its options unnamed while any
# implementation that writes the same text plainly reports them named. Both sides read
# the name off the DOM instead, and the comparison is of the copy the reader sees.
OPTION_TEXT_JS = """(root) => [...root.querySelectorAll('option')]
  .map(o => (o.textContent || '').trim().replace(/\\s+/g, ' '))"""

OPTION_LINE = re.compile(r'^(\s*- option)(?: "(?:[^"\\]|\\.)*")?(.*)$')


def name_options_from_dom(aria: str, texts: list[str]) -> str:
    """The ARIA snapshot with every `option` line renamed from the DOM, in tree order.

    Both listings are in document order — the snapshot's nodes and
    `querySelectorAll('option')` — so the nth line takes the nth text.
    """
    remaining = list(texts)
    out = []
    for line in aria.splitlines():
        m = OPTION_LINE.match(line)
        if not m or not remaining:
            out.append(line)
            continue
        text = remaining.pop(0)
        head, attrs = m.group(1), m.group(2)
        out.append(f'{head} "{text}"{attrs}' if text else f"{head}{attrs}")
    return "\n".join(out)


def frame_css(viewport: tuple[int, int]) -> str:
    """The `.dc.html` helmet pins `#dc-root` to the size the component was drawn at;
    one rule resizes it to the viewport under comparison without touching the file."""
    return (f"#dc-root{{width:{viewport[0]}px !important;"
            f"height:{viewport[1]}px !important;margin:0 !important}}")


def impl_url(base: str, scene: str, props: dict) -> str:
    """The implementation's address for one scene.

    The query carries `scene=<name>` — the scene's name from `scenes.json`, which is
    unique — and every scene prop as its own parameter. Several scenes of one handoff
    package can share the same props (a shell header and a library page both in
    `scenario=ready`), so an implementation that keys on `scene` reaches exactly one;
    one that only knows the props still works.
    """
    parts = urllib.parse.urlsplit(base)
    query = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
    query.append(("scene", scene))
    query += [(k, v if isinstance(v, str) else json.dumps(v)) for k, v in props.items()]
    return urllib.parse.urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urllib.parse.urlencode(query),
         parts.fragment))


# ---------------------------------------------------------------- arguments
def parse_viewports(raw: str) -> list[tuple[int, int]]:
    out = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        m = re.fullmatch(r"(\d+)x(\d+)", chunk)
        if not m:
            raise ValueError(f"viewport must be WIDTHxHEIGHT, got {chunk!r}")
        out.append((int(m.group(1)), int(m.group(2))))
    if not out:
        raise ValueError("no viewport given")
    return out


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="visual-parity.py",
        usage="visual-parity.py [options]",
        description="Compare an interface with the handoff package it was built from, "
                    "scene by scene, by ARIA tree and by pixels.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--baseline", required=True, metavar="DIR",
                   help="the handoff package: a downloaded Claude Design leaf directory "
                        "holding scenes.json")
    p.add_argument("--impl", required=True, metavar="URL",
                   help="the address the implementation is opened at, scene by scene")
    p.add_argument("--cdp", metavar="URL", default=None,
                   help="a browser already running, to compare instead of a fresh one: "
                        "an Electron application's debugging port, say. --impl still "
                        "says where to navigate")
    p.add_argument("--impl-title", metavar="TEXT", default=None,
                   help="with --cdp, a substring of the window title to pick, when the "
                        "application has more than one")
    p.add_argument("--scenes", required=True, metavar="NAMES",
                   help="comma-separated scene names, each one named in scenes.json")
    p.add_argument("--max-pct", type=float, default=DEFAULT_MAX_PCT, metavar="PCT",
                   help=f"largest share of differing cells a scene may have, after both "
                        f"screenshots are shrunk by {PIXEL_SCALE} (default "
                        f"{DEFAULT_MAX_PCT})")
    p.add_argument("--viewports", default=DEFAULT_VIEWPORTS, metavar="LIST",
                   help="comma-separated WIDTHxHEIGHT window sizes to compare at")
    p.add_argument("--out", metavar="DIR", default=None,
                   help="where the screenshots and ARIA trees are written")
    p.add_argument("--console-errors", type=int, default=0, metavar="N",
                   help="how many console errors a page may log")
    p.add_argument("--cdn", metavar="DIR", default=None,
                   help="cache for the scripts `support.js` loads, so a render needs no "
                        "network")
    return p


def load_scenes(baseline: Path, wanted: list[str]) -> list[dict]:
    path = baseline / "scenes.json"
    if not path.exists():
        raise SystemExit(f"no scenes.json in {baseline}")
    catalogue = {s["name"]: s for s in json.loads(path.read_text(encoding="utf-8"))}
    missing = [n for n in wanted if n not in catalogue]
    if missing:
        raise SystemExit(f"scenes.json has no scene named: {', '.join(missing)}")
    return [catalogue[n] for n in wanted]


# ---------------------------------------------------------------- run
def run(args) -> int:
    baseline = Path(args.baseline).resolve()
    scene_names = [s.strip() for s in args.scenes.split(",") if s.strip()]
    scenes = load_scenes(baseline, scene_names)
    viewports = parse_viewports(args.viewports)
    out = Path(args.out).resolve() if args.out else Path("./parity-shots").resolve()
    media = out / "media"
    media.mkdir(parents=True, exist_ok=True)
    cache = Path(args.cdn).expanduser() if args.cdn else (
        Path.home() / ".cache" / "mmw" / "visual-parity")
    cache.mkdir(parents=True, exist_ok=True)

    pages = {}
    for scene in scenes:
        component = re.sub(r"\.dc\.html$", "", scene["page"])
        pages[f"/__parity-{scene['name']}.dc.html"] = wrapper_page(
            component, scene.get("props") or {})
    server, port = serve_baseline(baseline, pages)
    origin = f"http://127.0.0.1:{port}"

    from playwright.sync_api import sync_playwright

    def route_baseline(route, request):
        if request.url.startswith(origin):
            route.continue_()
        elif request.url.startswith(CDN_PREFIX):
            target = cdn_path(cache, request.url)
            if not target.exists():
                try:
                    urllib.request.urlretrieve(request.url, target)
                except Exception:
                    route.abort()
                    return
            route.fulfill(path=str(target), content_type="application/javascript")
        else:
            route.abort()

    comparisons: list[Comparison] = []
    control: Comparison | None = None
    try:
        with sync_playwright() as pw:
            # One browser renders both sides. With `--cdp` that is the application's own,
            # so the two screenshots come out of the same engine, the same fonts and the
            # same device pixel ratio, and the only difference left between them is
            # whether the implementation followed the design. Two browsers differ by
            # fractions of a pixel in how they measure a line of text, which is enough to
            # break a line one side and not the other and move everything below it.
            impl_browser = (pw.chromium.connect_over_cdp(args.cdp, timeout=10000)
                            if args.cdp else None)
            impl_page = (impl_page_over_cdp(impl_browser, args.impl_title)
                         if impl_browser else None)
            browser = pw.chromium.launch() if impl_page is None else None

            @contextmanager
            def baseline_page():
                """A page for the handoff package side, with only its own origin and the
                CDN cache reachable. The application's page is routed for the render and
                unrouted after, so the implementation side still reaches its own server.
                """
                if impl_page is None:
                    page = base_ctx.new_page()
                    try:
                        yield page, False
                    finally:
                        page.close()
                else:
                    impl_page.route("**/*", route_baseline)
                    try:
                        yield impl_page, True
                    finally:
                        impl_page.unroute("**/*", route_baseline)

            for vp in viewports:
                tag_vp = f"{vp[0]}x{vp[1]}"
                base_ctx = impl_ctx = None
                if impl_page is None:
                    base_ctx = browser.new_context(
                        viewport={"width": vp[0], "height": vp[1]},
                        device_scale_factor=1, reduced_motion="reduce", locale="zh-CN")
                    base_ctx.route("**/*", route_baseline)
                    impl_ctx = browser.new_context(
                        viewport={"width": vp[0], "height": vp[1]},
                        device_scale_factor=1, reduced_motion="reduce", locale="zh-CN")
                first_baseline: Shot | None = None
                for scene in scenes:
                    name = scene["name"]
                    with baseline_page() as (page, over_cdp):
                        base_shot = capture(
                            page, f"{origin}/__parity-{name}.dc.html", "#dc-root", vp,
                            media / f"{name}-{tag_vp}-baseline.png", frame_css(vp),
                            over_cdp=over_cdp)
                    if first_baseline is None:
                        first_baseline = base_shot
                    page = impl_page or impl_ctx.new_page()
                    impl_shot = capture(
                        page, impl_url(args.impl, name, scene.get("props") or {}), None, vp,
                        media / f"{name}-{tag_vp}-impl.png",
                        over_cdp=impl_page is not None)
                    if impl_page is None:
                        page.close()
                    comparisons.append(Comparison(
                        name, tag_vp,
                        pixel_diff(base_shot.png, impl_shot.png,
                                   media / f"{name}-{tag_vp}-diff.png"),
                        aria_diff(base_shot.aria, impl_shot.aria,
                                  media / f"{name}-{tag_vp}.aria.diff"),
                        base_shot.console, impl_shot.console, impl_shot.elements))
                if control is None:
                    scene = scenes[0]
                    with baseline_page() as (page, over_cdp):
                        wrong = capture(
                            page, f"{origin}/__parity-{scene['name']}.dc.html", "#dc-root",
                            vp, media / f"{NEGATIVE_CONTROL_SCENE}-{tag_vp}-impl.png",
                            frame_css(vp) + NEGATIVE_CONTROL_CSS, NEGATIVE_CONTROL_JS,
                            over_cdp=over_cdp)
                    stem = media / f"{NEGATIVE_CONTROL_SCENE}-{tag_vp}"
                    control = Comparison(
                        NEGATIVE_CONTROL_SCENE, tag_vp,
                        pixel_diff(first_baseline.png, wrong.png,
                                   Path(f"{stem}-diff.png")),
                        aria_diff(first_baseline.aria, wrong.aria,
                                  Path(f"{stem}.aria.diff")),
                        [], [])
                    _copy(first_baseline.png, Path(f"{stem}-baseline.png"))
                    aria_path(Path(f"{stem}-baseline.png")).write_text(
                        first_baseline.aria, encoding="utf-8")
                if base_ctx is not None:
                    base_ctx.close()
                if impl_ctx is not None:
                    impl_ctx.close()
            if browser is not None:
                browser.close()
            if impl_browser is not None:
                # Disconnects; the application it belongs to goes on running.
                impl_browser.close()
    finally:
        server.shutdown()
        server.server_close()

    code, lines = gate(control, comparisons, args.max_pct, args.console_errors)
    for line in lines:
        print(line)
    if code:
        print(f"screenshots and ARIA trees: {media}", file=sys.stderr)
    return code


def _copy(src: Path, dst: Path) -> None:
    dst.write_bytes(src.read_bytes())


# ---------------------------------------------------------------- reading the diff
def text_changes(diff: str) -> list[dict]:
    """Say what changed in words, out of the ARIA tree's own unified diff.

    Whoever reads a failing run asks "what is different" before "how many pixels".
    The tree carries the answer as text — a button's name, a line of copy — so the
    failure can say it instead of printing coordinates and leaving the reader to open
    two screenshots and compare them by eye.
    """
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
        parsed = ARIA_LINE.match(rest)
        if sign == " " or not parsed:
            flush()
            continue
        entry = {"role": parsed.group("role"),
                 "text": (parsed.group("name") or parsed.group("value") or "").strip()}
        (removed if sign == "-" else added).append(entry)
        if sign == "-" and added:
            flush()
            removed.append(entry)
    flush()
    return changes


def change_lines(diff: str) -> list[str]:
    """The `text_changes` of one scene, as the lines printed under its `DIFF`."""
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


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
