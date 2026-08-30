# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy>=2", "Pillow>=10", "playwright>=1.58"]
# ///
"""Compare a UI implementation against a Claude Design baseline, scene by scene.

The baseline is the Claude Design project downloaded into a leaf directory: the
component's `.dc.html`, its `styles/`, `data/`, `support.js`, and a `scenes.json`
listing every scene by name. This tool renders each named scene from that directory
offline, opens the same scene on the implementation, and compares the two by ARIA tree
and by pixels at two viewports.

How a non-default scene is rendered from the baseline
-----------------------------------------------------
A scene in Claude Design is a prop on the component, set from the Tweaks panel, not a
URL parameter. This tool writes one wrapper page per scene holding a single
`<dc-import name="<component>" scenario="<scene>">`, and serves it from the baseline
directory's own URL space (the runtime resolves a sibling component as
`./<name>.dc.html`). The wrapper pages exist only in the server's memory; no file in
the baseline directory is read as anything but bytes to send.

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
    uv run visual-parity.py --baseline <dir> --impl <url> --scenes a,b --max-pct 1 \
        --out <dir>

Exit 0 and one line `PARITY OK n/n` when every scene matches at every viewport.
Exit 1 with one `DIFF` line per failing pair, each followed by the ARIA tree lines
that differ — the name of the button or the line of copy, as text, which is what a
reader has to change. Exit 2 when the built-in negative control fails, in which case
no parity conclusion is printed at all.

`--out` holds the screenshot, the ARIA tree, and the differing-pixel picture for
every scene and viewport, for the differences an ARIA tree cannot carry: spacing,
colour, alignment. Nothing reads them but a person, and only when the printed lines
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
from dataclasses import dataclass, field
from pathlib import Path

# A pixel counts as identical while every channel is within this of the other image's.
PIXEL_TOLERANCE = 16

# What the Claude Design runtime wraps a component in that no product page has.
ARIA_NOISE = re.compile(r"^\s*- (generic|group)\s*$")
LANDMARK_NAME = re.compile(
    r'^(\s*- (?:main|navigation|banner|contentinfo|region|complementary)) "[^"]*"(:?)\s*$'
)

# The three scripts the Claude Design runtime loads from unpkg. Answered from a local
# cache so the baseline renders with no network.
CDN_PREFIX = "https://unpkg.com/"

DEFAULT_VIEWPORTS = "1440x900,1180x720"
SETTLE_MS = 1000  # after networkidle, for the runtime's own readiness poll

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
def normalize_aria(text: str) -> list[str]:
    """Drop what the runtime adds and what carries no structure.

    1. blank lines and bare ``- generic`` / ``- group`` lines;
    2. the accessible name on landmark roles — a product page labels its ``<main>``,
       a component page does not, and the landmark itself is what matters;
    3. one inner ``- main:`` nested inside another ``main``, whose children come up
       one level.
    """
    lines = []
    for ln in text.splitlines():
        if not ln.strip() or ARIA_NOISE.match(ln):
            continue
        lines.append(LANDMARK_NAME.sub(r"\1\2", ln.rstrip()))
    return hoist_nested_main(lines)


def hoist_nested_main(lines: list[str]) -> list[str]:
    """Remove a ``main`` nested inside another ``main`` and dedent its children.

    A Claude Design app page wraps every ``dc-import`` in its own ``<main>``; when the
    imported component's own root is a ``main`` too, both trees have to put the same
    content at the same level before they can be compared.
    """
    out: list[str] = []
    main_depths: list[int] = []  # indents of open main landmarks
    hoist: list[int] = []  # indents of removed nested mains still in scope
    for ln in lines:
        ind = len(ln) - len(ln.lstrip())
        while main_depths and ind <= main_depths[-1]:
            main_depths.pop()
        while hoist and ind <= hoist[-1]:
            hoist.pop()
        if ln.strip() == "- main:" and main_depths:
            hoist.append(ind)
            continue
        dedent = 2 * len(hoist)
        out.append(ln[dedent:] if dedent and ln.startswith(" " * dedent) else ln)
        if ln.strip() == "- main:":
            main_depths.append(ind - dedent)
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
def diff_images(ia, ib, out: Path | None = None) -> dict:
    """Two renders of the same scene, already loaded as RGB images.

    Images of unequal size are a failure on the spot: a scene that renders taller on
    one side is a difference, and scaling one to the other would hide it.
    """
    if ia.size != ib.size:
        return {"size_equal": False, "pct": 100.0, "count": None, "total": None,
                "box": None, "size_a": tuple(ia.size), "size_b": tuple(ib.size)}
    import numpy as np
    from PIL import Image

    na = np.asarray(ia, dtype=np.int16)
    nb = np.asarray(ib, dtype=np.int16)
    mask = (np.abs(na - nb) > PIXEL_TOLERANCE).any(axis=2)
    count, total = int(mask.sum()), int(mask.size)
    box = None
    if count:
        ys, xs = np.nonzero(mask)
        box = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    if out is not None:
        # A washed-out baseline under the red, so the differing pixels can be placed
        # on the page they belong to rather than on a black field.
        vis = (na * 0.22 + 196).astype(np.uint8)
        vis[mask] = (230, 20, 60)
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
    has run, and its verdict is applied before any scene's: it is the only thing
    reported when it fails, because a check that did not catch a scene known to be
    wrong says nothing about the scenes it passed.
    """
    control_reasons = failures(control, max_pct, console_limit)
    if not control_reasons:
        return 2, ["NEGATIVE CONTROL FAILED: a baseline render with an inserted error "
                   "banner compared equal; this run proves nothing"]
    lines = []
    failed = 0
    for c in comparisons:
        reasons = failures(c, max_pct, console_limit)
        if reasons:
            failed += 1
            box = c.pixel["box"]
            lines.append(f"DIFF {c.scene} {c.viewport} {c.pixel['pct']}% box={box} "
                         f"— {'; '.join(r.en for r in reasons)}")
            lines.extend(change_lines(c.aria["diff"]))
    if failed:
        return 1, lines
    return 0, [f"PARITY OK {len(comparisons)}/{len(comparisons)}"]


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


def capture(page, url: str, selector: str | None, viewport: tuple[int, int], png: Path,
            extra_css: str | None = None, extra_js: str | None = None) -> Shot:
    console: list[str] = []
    page.on("console", lambda m: console.append(f"{m.type}: {m.text}")
            if m.type == "error" else None)
    page.on("pageerror", lambda e: console.append(f"pageerror: {e}"))
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    page.goto(url, wait_until="networkidle")
    if extra_css:
        page.add_style_tag(content=extra_css)
    page.wait_for_timeout(SETTLE_MS)
    if extra_js:
        page.evaluate(extra_js)
        page.wait_for_timeout(200)
    target = page.locator(selector or "body").first
    target.wait_for(state="visible", timeout=15000)
    if selector:
        target.screenshot(path=str(png))
    else:
        page.screenshot(path=str(png))
    aria = target.aria_snapshot()
    aria_path(png).write_text(aria, encoding="utf-8")
    return Shot(png, aria, console)


def aria_path(png: Path) -> Path:
    """The ARIA snapshot saved beside a screenshot, under the same name."""
    return png.with_name(png.name.removesuffix(".png") + ".aria.yml")


def frame_css(viewport: tuple[int, int]) -> str:
    """The `.dc.html` helmet pins `#dc-root` to the size the component was drawn at;
    one rule resizes it to the viewport under comparison without touching the file."""
    return (f"#dc-root{{width:{viewport[0]}px !important;"
            f"height:{viewport[1]}px !important;margin:0 !important}}")


def impl_url(base: str, props: dict) -> str:
    parts = urllib.parse.urlsplit(base)
    query = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
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
        description="Compare an implementation with a Claude Design baseline, "
                    "scene by scene, by ARIA tree and by pixels.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--baseline", required=True, metavar="DIR",
                   help="downloaded Claude Design leaf directory, holding scenes.json")
    p.add_argument("--impl", required=True, metavar="URL",
                   help="the running implementation page")
    p.add_argument("--scenes", required=True, metavar="NAMES",
                   help="comma-separated scene names, each one named in scenes.json")
    p.add_argument("--max-pct", type=float, default=1.0, metavar="PCT",
                   help="largest share of differing pixels a scene may have")
    p.add_argument("--viewports", default=DEFAULT_VIEWPORTS, metavar="LIST",
                   help="comma-separated WIDTHxHEIGHT window sizes to compare at")
    p.add_argument("--out", metavar="DIR", default=None,
                   help="where the screenshots and ARIA trees are written")
    p.add_argument("--console-errors", type=int, default=0, metavar="N",
                   help="how many console errors a page may log")
    p.add_argument("--cdn", metavar="DIR", default=None,
                   help="cache for the runtime scripts, so a render needs no network")
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
            browser = pw.chromium.launch()
            for vp in viewports:
                tag_vp = f"{vp[0]}x{vp[1]}"
                base_ctx = browser.new_context(
                    viewport={"width": vp[0], "height": vp[1]}, device_scale_factor=1,
                    reduced_motion="reduce", locale="zh-CN")
                base_ctx.route("**/*", route_baseline)
                impl_ctx = browser.new_context(
                    viewport={"width": vp[0], "height": vp[1]}, device_scale_factor=1,
                    reduced_motion="reduce", locale="zh-CN")
                first_baseline: Shot | None = None
                for scene in scenes:
                    name = scene["name"]
                    page = base_ctx.new_page()
                    base_shot = capture(
                        page, f"{origin}/__parity-{name}.dc.html", "#dc-root", vp,
                        media / f"{name}-{tag_vp}-baseline.png", frame_css(vp))
                    page.close()
                    if first_baseline is None:
                        first_baseline = base_shot
                    page = impl_ctx.new_page()
                    impl_shot = capture(
                        page, impl_url(args.impl, scene.get("props") or {}), None, vp,
                        media / f"{name}-{tag_vp}-impl.png")
                    page.close()
                    comparisons.append(Comparison(
                        name, tag_vp,
                        pixel_diff(base_shot.png, impl_shot.png,
                                   media / f"{name}-{tag_vp}-diff.png"),
                        aria_diff(base_shot.aria, impl_shot.aria,
                                  media / f"{name}-{tag_vp}.aria.diff"),
                        base_shot.console, impl_shot.console))
                if control is None:
                    scene = scenes[0]
                    page = base_ctx.new_page()
                    wrong = capture(
                        page, f"{origin}/__parity-{scene['name']}.dc.html", "#dc-root",
                        vp, media / f"{NEGATIVE_CONTROL_SCENE}-{tag_vp}-impl.png",
                        frame_css(vp) + NEGATIVE_CONTROL_CSS, NEGATIVE_CONTROL_JS)
                    page.close()
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
                base_ctx.close()
                impl_ctx.close()
            browser.close()
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
ARIA_LINE = re.compile(
    r'^\s*- (?P<role>[a-zA-Z]+)(?: "(?P<name>.*?)")?(?::(?:\s*(?P<value>.*))?)?\s*$')


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
