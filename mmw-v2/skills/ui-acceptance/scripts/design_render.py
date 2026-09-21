#!/usr/bin/env python3
"""Offline rendering of a handoff package's design side.

Nothing here judges. `story-parity.py` and `extract_skeleton.py` import the baseline
server, the wrapper page, capture, and the `[data-ui]` reader.
"""

from __future__ import annotations

import hashlib
import http.server
import importlib.util
import json
import re
import socketserver
import subprocess
import sys
import threading
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------- constants
# The three scripts `support.js` loads from unpkg. Answered from the handoff package's
# own `vendor/` directory when the handoff stored them, else from a local cache, else
# fetched once; a render never depends on the network twice.
CDN_PREFIX = "https://unpkg.com/"
VENDOR_DIR = "vendor"
DEFAULT_CACHE = Path.home() / ".cache" / "mmw" / "pixel-diff"

# Virtual milliseconds the design page's clock is run after a navigation: `support.js`
# polls readiness every 50 ms and each component first renders on that poll, and a
# `requestAnimationFrame` focus effect rides the same clock. Far below the handoff
# package's own timers (an 1800 ms auto-advance, a 2600 ms auto-recover, a 2400 ms toast).
SETTLE_VIRTUAL_MS = 200
FRAME_MS = 16
# Every design page starts the fake clock here and moves it forward only; `pause_at`
# refuses to go back.
CLOCK_EPOCH_MS = 1_700_000_000_000

VIEWPORT_RE = re.compile(r"^(\d+)x(\d+)$")


# ---------------------------------------------------------------- the contract
@dataclass
class Scene:
    """One screen declaration of the contract, joined with its `scenes.json` entry."""
    name: str
    page: str
    mount: str
    props: dict
    # The page's own `pages.<page>.viewports`; empty means the top-level list.
    viewports: tuple = ()


def _refusal(what: str, why: str, next_step: str) -> str:
    name = "_mmw_refusal"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            name, Path(__file__).resolve().parent / "refusal.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name].refusal(what, why, next_step)


def load_yaml(path: Path) -> dict:
    """`pyyaml` when the interpreter has it (the scripts declare it); else through `uv`,
    which every criterion of this pipeline already relies on."""
    try:
        import yaml
    except ImportError:
        out = subprocess.run(
            ["uv", "run", "--with", "pyyaml", "python", "-c",
             "import json,sys,yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1], "
             "encoding='utf-8')) or {}))", str(path)],
            capture_output=True, text=True)
        if out.returncode != 0:
            raise SystemExit(f"cannot read {path}: pyyaml is not importable and uv failed: "
                             f"{out.stderr.strip()}")
        return json.loads(out.stdout)
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def load_contract(path: Path, doc: dict | None = None) -> dict:
    """Read the contract, or reuse a dict already loaded from `path`."""
    if doc is None:
        doc = load_yaml(Path(path))
    for key in ("pages", "scenes"):
        if key not in doc:
            raise SystemExit(f"{path}: contract has no top-level `{key}`; run write-screen-contract "
                             f"step 2 to declare pages")
    return doc



def parse_viewports(raw) -> list[tuple[int, int]]:
    items = raw if isinstance(raw, list) else str(raw).split(",")
    out = []
    for chunk in items:
        chunk = str(chunk).strip()
        if not chunk:
            continue
        m = VIEWPORT_RE.match(chunk)
        if not m:
            raise ValueError(f"viewport must be WIDTHxHEIGHT, got {chunk!r}")
        out.append((int(m.group(1)), int(m.group(2))))
    if not out:
        raise ValueError("no viewport given")
    return out



def page_viewports(doc: dict) -> dict[str, list[tuple[int, int]]]:
    """`pages.<page>.viewports` for every page that declares its own sizes.

    A page drawn at one size is compared at that size only; the top-level
    `viewports` list is the size of every page that declares none."""
    out = {}
    for page, decl in (doc.get("pages") or {}).items():
        if isinstance(decl, dict) and decl.get("viewports") not in (None, [], ""):
            out[str(page)] = parse_viewports(decl["viewports"])
    return out


def viewports_for(page: str, own: dict[str, list[tuple[int, int]]],
                  default: list[tuple[int, int]]) -> list[tuple[int, int]]:
    return own.get(page) or default


def scenes_of(doc: dict, catalogue: dict[str, dict]) -> dict[str, Scene]:
    """Every screen declaration, with page-level `mount` filled in."""
    pages = doc.get("pages") or {}
    own = page_viewports(doc)
    out = {}
    for name, decl in (doc.get("scenes") or {}).items():
        decl = decl or {}
        page = decl.get("page") or catalogue.get(name, {}).get("page") or ""
        page_decl = pages.get(page) or {}
        out[name] = Scene(
            name=name, page=page,
            mount=str(page_decl.get("mount") or ""),
            props=catalogue.get(name, {}).get("props") or {},
            viewports=tuple(own.get(page) or ()))
    return out


def load_catalogue(baseline: Path) -> dict[str, dict]:
    path = baseline / "scenes.json"
    if not path.exists():
        raise SystemExit(f"no scenes.json in {baseline}")
    return {s["name"]: s for s in json.loads(path.read_text(encoding="utf-8"))}


def scene_plan(doc: dict, catalogue: dict[str, dict], mounts: list[str],
               explicit: list[str] | None) -> list[Scene]:
    """The scenes a run covers: every scene whose `mount` is one of `mounts`, narrowed to
    `explicit` when given — which must be a subset, because a page's scenes are split
    between two tickets only this way and a scene outside the mount is another ticket's.
    An empty `explicit` keeps every derived scene."""
    scenes = scenes_of(doc, catalogue)
    derived = [s for s in scenes.values() if s.mount in mounts]
    if not derived:
        raise SystemExit(_refusal(
            f"no scene declares mount {', '.join(mounts)}.",
            "Every --pages value must be a pages.mount that at least one scene uses.",
            "Pass a declared --pages mount, then rerun."))
    if not explicit:
        return derived
    by_name = {s.name: s for s in derived}
    outside = [n for n in explicit if n not in by_name]
    if outside:
        raise SystemExit(_refusal(
            f"--scenes names scenes outside mount {', '.join(mounts)}: "
            f"{', '.join(outside)}.",
            "A --scenes name must belong to one of the --pages mounts.",
            "Pass a scene of those mounts, then rerun."))
    return [by_name[n] for n in explicit]


# ---------------------------------------------------------------- the tree
ARIA_LINE = re.compile(
    r'^(?P<indent>\s*)- (?P<role>[a-zA-Z]+)(?: "(?P<name>(?:[^"\\]|\\.)*)")?'
    r'(?P<attrs>(?: \[[^\]]*\])*)(?::\s*(?P<value>.*))?\s*$')
# Playwright writes a node's key — `role "name" [attrs]` — in single quotes, doubling
# any quote inside, whenever the key would not read as plain YAML: a name holding " #" or
# ": " is enough. The quotes are YAML's, not the tree's; the line is a node like any other.
QUOTED_KEY = re.compile(r"^(?P<indent>\s*- )'(?P<key>(?:[^']|'')*)'(?P<rest>:.*)?$")


def unquote_key(line: str) -> str:
    """A snapshot line with its key's YAML quoting taken off; any other line unchanged."""
    m = QUOTED_KEY.match(line)
    if not m:
        return line
    return m.group("indent") + m.group("key").replace("''", "'") + (m.group("rest") or "")


def accessibility_snapshot(locator) -> str:
    """The Playwright accessibility snapshot for one locator."""
    return locator.aria_snapshot()


# An `<option>`'s accessible name is computed from its own child text nodes alone. The
# Claude Design runtime wraps every `{{ }}` hole in a `span.sc-interp`, which takes the
# text out of those nodes, so a handoff package reports its options unnamed while any
# implementation that writes the same text plainly reports them named. Both sides read
# the name off the DOM instead, and the comparison is of the copy the reader sees.
OPTION_TEXT_JS = """(root) => [...root.querySelectorAll('option')]
  .map(o => (o.textContent || '').trim().replace(/\\s+/g, ' '))"""

OPTION_LINE = re.compile(r'^(\s*- option)(?: "(?:[^"\\]|\\.)*")?(.*)$')


def name_options_from_dom(aria: str, texts: list[str]) -> str:
    remaining = list(texts)
    out = []
    for line in aria.splitlines():
        m = OPTION_LINE.match(unquote_key(line))
        if not m or not remaining:
            out.append(line)
            continue
        text = remaining.pop(0)
        head, attrs = m.group(1), m.group(2)
        out.append(f'{head} "{text}"{attrs}' if text else f"{head}{attrs}")
    return "\n".join(out)


# ---------------------------------------------------------------- baseline server
def wrapper_page(component: str, props: dict, inline_head: str = "") -> str:
    """One page holding one `dc-import`, pinned to a scene.

    One `dc-import` with the scene written into the attribute, rather than driven
    from state by a `<select>`. `inline_head` is
    served as part of the page, which is what the negative control needs: an error that
    is in the bytes the server sends, not injected by the client.
    """
    attrs = []
    for key, value in props.items():
        literal = value if isinstance(value, str) else "{{ %s }}" % json.dumps(value)
        attrs.append(f'{key}="{_attr(literal)}"')
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8" /><script src="./support.js"></script>{inline_head}</head>
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


def component_of(page: str) -> str:
    return re.sub(r"\.dc\.html$", "", page)


def wrapper_path(scene: str) -> str:
    return f"/__parity-{scene}.dc.html"


class _Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True
    # A page opens a burst of connections at once (stylesheets, scripts, data). The
    # standard library's listen backlog of 5 lets a busy machine reset the rest, and
    # the page renders empty (measured 2026-09-21: 6 parallel story runs, resets on
    # every round at 5, none in 24 runs at 128).
    request_queue_size = 128


def serve_baseline(root: Path, pages: dict[str, str]) -> tuple[_Server, int]:
    """Serve `root` read-only, with the wrapper pages answered from memory. `pages` is
    read on every request, so a caller may swap an entry while the server runs."""

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


def vendor_path(baseline: Path, url: str) -> Path | None:
    """The copy of a CDN script the handoff package carries under `vendor/`, by the
    script's own file name, when the handoff stored one."""
    name = url.rsplit("/", 1)[-1].split("?", 1)[0]
    candidate = baseline / VENDOR_DIR / name
    return candidate if candidate.exists() else None


def baseline_router(origin: str, baseline: Path, cache: Path):
    """A Playwright route handler: the baseline origin passes, a CDN script is answered
    from `vendor/`, then the cache, then one fetch; everything else is refused."""
    cache.mkdir(parents=True, exist_ok=True)

    def route_baseline(route, request):
        if request.url.startswith(origin):
            route.continue_()
        elif request.url.startswith(CDN_PREFIX):
            target = vendor_path(baseline, request.url) or cdn_path(cache, request.url)
            if not target.exists():
                try:
                    urllib.request.urlretrieve(request.url, target)
                except Exception:
                    route.abort()
                    return
            route.fulfill(path=str(target), content_type="application/javascript")
        else:
            route.abort()

    return route_baseline


# ---------------------------------------------------------------- capture
@dataclass
class Shot:
    png: Path
    aria: str
    box: tuple[int, int, int, int]  # x, y, w, h in viewport CSS pixels
    values: list[dict]


# Facts of every `[data-ui]` element under a root, document order. Visibility, box and
# computed style follow Quixote `src/q_element.js` (`getComputedStyle`,
# `getBoundingClientRect`). Text is the element's own character data plus descendants
# that do not themselves carry `data-ui` — so a `span.sc-interp` counts and a nested
# `[data-ui]` child does not. The walk is DOM-only, so a product story page can run it
# on `[data-story-root]`.
UI_VALUES_JS = """(root) => {
  const els = [];
  if (root.hasAttribute('data-ui')) els.push(root);
  for (const el of root.querySelectorAll('[data-ui]')) els.push(el);
  const counts = {};
  for (const el of els) {
    const id = el.getAttribute('data-ui');
    counts[id] = (counts[id] || 0) + 1;
  }
  const seen = {};
  const qualified = new Map();
  for (const el of els) {
    const id = el.getAttribute('data-ui');
    if (counts[id] === 1) {
      qualified.set(el, id);
    } else {
      seen[id] = (seen[id] || 0) + 1;
      qualified.set(el, id + '#' + seen[id]);
    }
  }
  const nearest = (el) => {
    for (let p = el.parentElement; p; p = p.parentElement) {
      if (p.hasAttribute('data-ui')) return p;
      if (p === root) return null;
    }
    return null;
  };
  const ownText = (el) => {
    const parts = [];
    const walk = (node) => {
      for (const child of node.childNodes) {
        if (child.nodeType === 3) parts.push(child.nodeValue);
        else if (child.nodeType === 1 && !child.hasAttribute('data-ui')) walk(child);
      }
    };
    walk(el);
    return parts.join('').replace(/\\s+/g, ' ').trim();
  };
  const lastByAncestor = new Map();
  const out = [];
  for (const el of els) {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    const anc = nearest(el);
    const prev = lastByAncestor.has(anc) ? lastByAncestor.get(anc) : null;
    const pr = prev ? prev.getBoundingClientRect() : null;
    const ar = anc ? anc.getBoundingClientRect() : null;
    out.push({
      id: qualified.get(el),
      interactive: el.matches('button,input,select,textarea,a[href],[role="button"],'
        + '[role="textbox"],[role="checkbox"],[role="combobox"],[role="link"],'
        + '[role="tab"],[role="radio"],[role="switch"],[role="slider"],'
        + '[role="menuitem"],[role="searchbox"],[role="spinbutton"],'
        + '[contenteditable="true"]'),
      disabled: el.matches(':disabled') || el.getAttribute('aria-disabled') === 'true',
      visible: cs.display !== 'none' && cs.visibility !== 'hidden' && cs.opacity !== '0'
        && r.width !== 0 && r.height !== 0,
      text: ownText(el),
      size: [Math.round(r.width), Math.round(r.height)],
      ancestor: anc ? qualified.get(anc) : null,
      offset: ar ? [Math.round(r.left - ar.left), Math.round(r.top - ar.top)] : null,
      previous: prev ? qualified.get(prev) : null,
      gap: pr ? [Math.round(r.left - pr.right), Math.round(r.top - pr.bottom)] : null,
      style: {
        'font-size': cs.getPropertyValue('font-size'),
        'font-weight': cs.getPropertyValue('font-weight'),
        'color': cs.getPropertyValue('color'),
        'background-color': cs.getPropertyValue('background-color'),
        'border-radius': cs.getPropertyValue('border-radius'),
      },
    });
    lastByAncestor.set(anc, el);
  }
  return out;
}"""


_CLOCK_PAGES: set[int] = set()


def resize(page, viewport: tuple[int, int]) -> None:
    """Put the page in a window of this size."""
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})


def install_clock(page) -> None:
    """Install a paused fake clock once per page, so `support.js`'s readiness poll
    fires only when `run_clock` moves time, and never further than that."""
    if id(page) in _CLOCK_PAGES:
        return
    page.clock.install(time=CLOCK_EPOCH_MS)
    page.clock.pause_at(CLOCK_EPOCH_MS)
    _CLOCK_PAGES.add(id(page))


def run_clock(page, ms: int) -> None:
    install_clock(page)
    page.clock.run_for(ms)


def navigate(page, url: str, reload: bool = False) -> None:
    """Open `url` on a paused clock and let the design page settle 200 ms of virtual
    time. `reload` is for a hash-routed document that would otherwise stay put."""
    install_clock(page)
    page.goto(url, wait_until="networkidle")
    if reload:
        page.reload(wait_until="networkidle")
    run_clock(page, SETTLE_VIRTUAL_MS)


def wait_for_mount(page, selector: str) -> None:
    """Wait for the mount element to be on screen, in virtual time only."""
    if mount_rect(page, selector) is not None:
        return
    for _ in range(max(1, SETTLE_VIRTUAL_MS // FRAME_MS)):
        run_clock(page, FRAME_MS)
        if mount_rect(page, selector) is not None:
            return
    raise SystemExit(f"no visible element matches {selector}")


def capture(page, png: Path, *, selector: str, clip: tuple[int, int, int, int] | None = None,
            extra_js: str | None = None) -> Shot:
    """Screenshot, accessibility tree and `[data-ui]` values under `selector`, on a
    page that has already been navigated and settled.

    `clip` is the screenshot rectangle in viewport coordinates. The tree and values
    walk the whole subtree. `extra_js` applies a negative-control mutation before
    capture.
    """
    if extra_js:
        page.evaluate(extra_js)
    target = page.locator(selector).first
    rect = mount_rect(page, selector)
    if rect is None:
        raise SystemExit(f"{selector} is not on screen at capture time")
    if clip is None:
        clip = (int(round(rect["x"])), int(round(rect["y"])),
                int(round(rect["width"])), int(round(rect["height"])))
    x, y, w, h = clip
    page.screenshot(path=str(png), scale="css",
                    clip={"x": x, "y": y, "width": max(1, w), "height": max(1, h)})
    aria = name_options_from_dom(target.aria_snapshot(),
                                 target.evaluate(OPTION_TEXT_JS))
    values = read_ui_values(page, selector)
    aria_path(png).write_text(aria, encoding="utf-8")
    return Shot(png, aria, (x, y, w, h), values)


def read_ui_values(page, selector: str) -> list[dict]:
    """Every `[data-ui]` element under `selector`, document order, as one dict each."""
    return page.locator(selector).first.evaluate(UI_VALUES_JS)


def plain_ui_id(qualified: str) -> str:
    """Remove the occurrence suffix the shared reader adds to repeated ids."""
    return re.sub(r"#\d+$", "", qualified)


def nest_ui_values(values: list[dict]) -> dict:
    """Visible `[data-ui]` text as the scene-data tree.

    A leaf is its displayed text. A node with visible `[data-ui]` children is an
    object keyed by those children's ids and carries its own direct text under
    `_text`. Repeated ids under one parent become a document-order list. The reader
    qualifies repeated ids as `id#1`, `id#2`; this function removes only that suffix.
    """
    visible = [row for row in values if row.get("visible")]
    by_id = {str(row.get("id")): row for row in visible if row.get("id")}
    children: dict[str | None, list[dict]] = {}
    for row in visible:
        ancestor = row.get("ancestor")
        if ancestor not in by_id:
            ancestor = None
        children.setdefault(ancestor, []).append(row)

    def add(target: dict, key: str, value) -> None:
        if key not in target:
            target[key] = value
        elif isinstance(target[key], list):
            target[key].append(value)
        else:
            target[key] = [target[key], value]

    def value_of(row: dict):
        own = str(row.get("text") or "")
        descendants = children.get(str(row.get("id")), [])
        if not descendants:
            return own
        out = {}
        if own:
            out["_text"] = own
        for child in descendants:
            add(out, plain_ui_id(str(child["id"])), value_of(child))
        return out

    out = {}
    for row in children.get(None, []):
        add(out, plain_ui_id(str(row["id"])), value_of(row))
    return out


def values_path(out: Path, mount: str, scene: str, viewport: tuple[int, int]) -> Path:
    """`--out/values/<mount>/<scene>-<W>x<H>.json`."""
    w, h = viewport
    return Path(out) / "values" / mount / f"{scene}-{w}x{h}.json"


def write_values(path: Path, values: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(values, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def visible_box(page, selector: str, viewport: tuple[int, int]) -> tuple[int, int, int, int]:
    """The mount element's layout box intersected with the viewport, in viewport CSS
    pixels. `getBoundingClientRect()` gives the layout box — a 3000 px table is 3000 px
    tall, not "what is visible" — and the intersection is what the pixel judge compares;
    the rest is the tree's."""
    rect = mount_rect(page, selector)
    if rect is None:
        raise SystemExit(f"{selector} has no box")
    x0, y0 = max(0.0, rect["x"]), max(0.0, rect["y"])
    x1 = min(rect["x"] + rect["width"], float(viewport[0]))
    y1 = min(rect["y"] + rect["height"], float(viewport[1]))
    return (int(round(x0)), int(round(y0)), max(1, int(round(x1 - x0))),
            max(1, int(round(y1 - y0))))



MOUNT_RECT_JS = """
(selector) => {
  const el = document.querySelector(selector);
  if (!el) return null;
  const shown = (e) => {
    const cs = getComputedStyle(e);
    return cs.display !== 'none' && cs.visibility !== 'hidden' && cs.opacity !== '0';
  };
  const own = el.getBoundingClientRect();
  if (shown(el) && own.width > 0 && own.height > 0) {
    return {x: own.x, y: own.y, width: own.width, height: own.height};
  }
  // A mount that is a box-less wrapper — a dialog layer whose children are positioned
  // out of flow — takes the union of its shown descendants' boxes.
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity, any = false;
  for (const d of el.querySelectorAll('*')) {
    if (!shown(d)) continue;
    const r = d.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    any = true;
    x0 = Math.min(x0, r.x); y0 = Math.min(y0, r.y);
    x1 = Math.max(x1, r.right); y1 = Math.max(y1, r.bottom);
  }
  return any ? {x: x0, y: y0, width: x1 - x0, height: y1 - y0} : null;
}
"""


def mount_rect(page, selector: str) -> dict | None:
    """The mount element's layout box, or `None` while it is not on screen. An element
    with a box of its own gives that box; a wrapper without one (a dialog layer whose
    children are positioned out of flow) gives the union of its shown descendants."""
    return page.evaluate(MOUNT_RECT_JS, selector)


def aria_path(png: Path) -> Path:
    """The ARIA snapshot saved beside a screenshot, under the same name."""
    return png.with_name(png.name.removesuffix(".png") + ".aria.yml")
