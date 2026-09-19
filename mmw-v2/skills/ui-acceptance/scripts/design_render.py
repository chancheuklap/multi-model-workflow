#!/usr/bin/env python3
"""Offline rendering of a handoff package's design side.

Nothing here judges. `story-parity.py` and `extract_skeleton.py` import the baseline
server, the wrapper page, capture, the `[data-ui]` reader, and the accessibility-tree
normaliser. The contract lint loads `volatile_triggers` and `count_volatile_hits` from
this file.
"""

from __future__ import annotations

import hashlib
import http.server
import json
import re
import socketserver
import subprocess
import sys
import threading
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

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

# Roles whose accessible name is dropped: a product page labels its `<main>`, a
# component page does not, and the landmark itself is what matters.
LANDMARKS = {"main", "navigation", "banner", "contentinfo", "region", "complementary"}
# Roles the *comparison* keeps even with no accessible name: a dialog is on screen, so a
# product that stopped drawing one has to fail, and until this list existed an unnamed
# dialog was dropped and no judge could see it. This is a statement about what counts as
# structure on screen, and it is the only place a role is named — **locating** a control
# uses the whole ancestor chain and needs no list, so a product built from `nav`, `table`
# or a repeated `article` needs nothing added here.
COMPARED_UNNAMED = {"dialog", "alertdialog"}
# Classes the Claude Design runtime adds around interpolated text and hosts; a product
# never carries them, and they are not part of the design.
RUNTIME_CLASS_PREFIXES = ("sc-", "dc-")

VIEWPORT_RE = re.compile(r"^(\d+)x(\d+)$")
# Scene marker `extract_skeleton.py` writes into target trees; `count_volatile_hits`
# splits on the same string.
SCENE_HEADER = "## scene "


# ---------------------------------------------------------------- the contract
@dataclass
class Scene:
    """One screen declaration of the contract, joined with its `scenes.json` entry."""
    name: str
    page: str
    mount: str
    props: dict


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


def load_contract(path: Path) -> dict:
    doc = load_yaml(Path(path))
    for key in ("target", "pages", "scenes", "viewports"):
        if key not in doc:
            raise SystemExit(f"{path}: contract has no top-level `{key}`; run align-screens "
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



def scenes_of(doc: dict, catalogue: dict[str, dict]) -> dict[str, Scene]:
    """Every screen declaration, with page-level `mount` filled in."""
    pages = doc.get("pages") or {}
    out = {}
    for name, decl in (doc.get("scenes") or {}).items():
        decl = decl or {}
        page = decl.get("page") or catalogue.get(name, {}).get("page") or ""
        page_decl = pages.get(page) or {}
        out[name] = Scene(
            name=name, page=page,
            mount=str(page_decl.get("mount") or ""),
            props=catalogue.get(name, {}).get("props") or {})
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
        raise SystemExit(f"no scene declares mount {', '.join(mounts)}")
    if not explicit:
        return derived
    by_name = {s.name: s for s in derived}
    outside = [n for n in explicit if n not in by_name]
    if outside:
        raise SystemExit(f"--scenes names scenes outside mount {', '.join(mounts)}: "
                         f"{', '.join(outside)}")
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


def normalize_aria(text: str) -> list[str]:
    """The named nodes of a Playwright ARIA snapshot, in reading order, each with its
    nearest named ancestor.

    Each line is `- <role> "<name>"<attrs>` or `- <role>: <value>`, followed by
    ` < <role> "<name>"` naming the closest ancestor that itself carries a name or a
    value. Kept: every node that carries a name or a value — a control, a heading, a line
    of copy — with its attributes (`[level=2]`, `[checked]`). Dropped: nodes with
    neither, the accessible name of a landmark role, and lines that are not nodes. An
    unnamed wrapper is not an ancestor: an app page wraps a component in one more `main`
    and a product page in `list` and `article`, and none of that shows on screen. A
    button that moved out of its dialog does show, and its ancestor line says so.
    """
    out = []
    # (indent, rendered node) for every named node on the path from the root.
    stack: list[tuple[int, str]] = []
    for ln in text.splitlines():
        m = ARIA_LINE.match(unquote_key(ln))
        if not m:
            continue
        indent = len(m.group("indent").expandtabs(2))
        while stack and stack[-1][0] >= indent:
            stack.pop()
        role, name, attrs, value = (m.group("role"), m.group("name"),
                                    m.group("attrs") or "", m.group("value"))
        if role in LANDMARKS:
            name = None
        if name is None and not value and not attrs.strip() and role not in COMPARED_UNNAMED:
            continue
        if value:
            node = f"- {role}: {value.strip()}"
        elif name is not None:
            node = f'- {role} "{name}"{attrs}'
        else:
            node = f"- {role}{attrs}"
        parent = stack[-1][1] if stack else None
        out.append(f"{node} < {parent[2:]}" if parent else node)
        if name is not None or value or role in COMPARED_UNNAMED:
            stack.append((indent, node))
    return out


def aria_diff(a: str, b: str, out: Path | None = None,
              volatile: list[VolatileTrigger] | None = None) -> dict:
    import difflib

    la, lb = normalize_aria(a), normalize_aria(b)
    if volatile:
        la, lb = mask_volatile(la, volatile), mask_volatile(lb, volatile)
    diff = list(difflib.unified_diff(la, lb, "baseline", "impl", lineterm="", n=1))
    if out is not None:
        out.write_text("\n".join(diff) + ("\n" if diff else ""), encoding="utf-8")
    changed = sum(1 for d in diff if d[:1] in "+-" and not d.startswith(("+++", "---")))
    return {"lines_a": len(la), "lines_b": len(lb), "changed": changed,
            "diff": "\n".join(diff)}


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


# ---------------------------------------------------------------- class sets
CLASSES_JS = """(root) => {
  const out = {};
  for (const el of root.querySelectorAll('*')) {
    const raw = typeof el.className === 'string' ? el.className : (el.className.baseVal || '');
    const label = ((el.getAttribute('aria-label') || el.innerText || '').trim()
      .replace(/\\s+/g, ' ').slice(0, 30));
    for (const c of raw.split(/\\s+/).filter(Boolean)) {
      if (!(c in out)) out[c] = el.tagName.toLowerCase() + (label ? ' "' + label + '"' : '');
    }
  }
  return out;
}"""


def class_set(page, selector: str) -> dict[str, str]:
    """Every class name in the subtree, each with the first element that wears it."""
    found = page.locator(selector).first.evaluate(CLASSES_JS)
    return {c: label for c, label in found.items()
            if not c.startswith(RUNTIME_CLASS_PREFIXES)}


def class_diff(a: dict[str, str], b: dict[str, str]) -> dict:
    only_a = sorted(set(a) - set(b))
    only_b = sorted(set(b) - set(a))
    return {"only_in_baseline": [(c, a[c]) for c in only_a],
            "only_in_impl": [(c, b[c]) for c in only_b],
            "changed": len(only_a) + len(only_b)}


# ---------------------------------------------------------------- baseline server
def wrapper_page(component: str, props: dict, inline_head: str = "") -> str:
    """One page holding one `dc-import`, pinned to a scene.

    Follows `claude-design-blocks/scripts/mkharness.py`, minus the `<select>`: the
    scene is written into the attribute instead of driven from state. `inline_head` is
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


def frame_box(size: tuple[int, int]) -> str:
    """Pin `#dc-root` to the box the implementation's mount element measured. The
    `.dc.html` helmet pins it to the size the component was drawn at; the component
    fills its container (`#dc-root > * { height:100% }`), so the design renders at
    whatever box the product gives that component, and no size is declared anywhere."""
    return (f"#dc-root{{width:{size[0]}px !important;height:{size[1]}px !important;"
            f"margin:0 !important}}")


def hide_retired_js(triggers: list[tuple[str, str]]) -> str:
    """Hide every retired control on the baseline side — not merely drop it from the
    tree: it takes up room, and a tree-only exclusion leaves a pixel difference and a
    shift of everything below."""
    wanted = json.dumps([{"role": r, "name": n} for r, n in triggers], ensure_ascii=False)
    return """(() => {
  const wanted = %s;
  const name = el => (el.getAttribute('aria-label') || el.textContent || '').trim().replace(/\\s+/g, ' ');
  const roleOf = el => el.getAttribute('role') || ({button: 'button', a: 'link', input: 'textbox',
    select: 'combobox', textarea: 'textbox'}[el.tagName.toLowerCase()] || '');
  for (const el of document.querySelectorAll('button, a, input, select, textarea, [role]')) {
    for (const w of wanted) {
      if (roleOf(el) === w.role && name(el) === w.name) { el.style.display = 'none'; }
    }
  }
})()""" % wanted


# A display value the seed must not write (a wallet balance belonging to an external
# account). Both judges replace it with one token before they compare, so the two
# sides may show different numbers and still match. The trigger is the handoff's
# role and accessible name; a product node matches when its role is the same and the
# non-digit stem of the name is the same. An optional `after` (the previous named
# node) splits siblings that share that stem, and row triggers that share role
# and name.
VOLATILE_TOKEN = "<volatile>"
VOLATILE_FILL = "#00E5FF"
VOLATILE_DIGITS = re.compile(r"[\d,]+")
# HTML implicit roles the pixel paint uses when the element has no `role`
# attribute. `TD`/`TH` are `cell` so a balance in a table cell is painted;
# static-text tags (`P`, `SPAN`, `DIV`, `SMALL`, `B`, `CODE`) are `text`.
VOLATILE_IMPLICIT_ROLES = {
    "BUTTON": "button", "A": "link", "P": "text", "SPAN": "text", "DIV": "text",
    "STATUS": "status", "STRONG": "strong", "EM": "em", "LABEL": "label",
    "LI": "listitem", "H1": "heading", "H2": "heading", "H3": "heading",
    "H4": "heading", "H5": "heading", "H6": "heading",
    "TD": "cell", "TH": "cell", "TIME": "time", "SMALL": "text", "B": "text",
    "CODE": "text", "CAPTION": "caption", "DD": "definition", "DT": "term",
}
# A `text` trigger also paints these computed roles: a `<td>` snapshots as
# `cell` in the tree, and the paint has to find the same node in the DOM.
VOLATILE_TEXT_LIKE = (
    "text", "generic", "cell", "columnheader", "rowheader", "definition",
    "term", "caption", "time", "code", "",
)


def volatile_stem(name: str) -> str:
    return VOLATILE_DIGITS.sub("", name).strip()


class VolatileTrigger(NamedTuple):
    """A `volatile_values` entry: role, accessible name, and optional `after`
    (the previous named node) when that pair is not unique on the scene."""
    role: str
    name: str
    after: tuple[str, str] | None = None


def volatile_name_matches(role: str, name: str, wanted_role: str, wanted_name: str) -> bool:
    """Role and non-digit stem. A `text` trigger also matches the computed roles
    a static string snapshots as (`cell`, `generic`, …), the same set the pixel
    paint already used, so lint and the two judges name one node."""
    if role != wanted_role and not (wanted_role == "text" and role in VOLATILE_TEXT_LIKE):
        return False
    if name == wanted_name:
        return True
    stem = volatile_stem(wanted_name)
    return bool(stem) and volatile_stem(name) == stem


def after_of(entry: dict) -> tuple[str, str] | None:
    """`after` on a `volatile_values` entry: the previous named node, or None."""
    raw = entry.get("after")
    if isinstance(raw, dict) and raw.get("role") and raw.get("name"):
        return (str(raw.get("role")), str(raw.get("name")))
    return None





def named_nodes(lines: list[str], chains: list[tuple[tuple[str, str], ...]] | None = None):
    """Yield `(role, name, previous, ancestor)` in reading order; yield `None` at a
    `## scene` boundary so a consumer can take the maximum per scene.
    Accessible name wins when a node carries both a name and a value, matching
    `get_by_role(..., exact=True)`.

    `ancestor` is the node the line already names after ` < `. It was parsed off and
    thrown away here, so the one fact that tells a dialog's confirm button from the page
    button that opened it reached the tree comparison and nothing else — a trigger could
    not be pinned by it because the matcher never saw it."""
    previous: tuple[str, str] | None = None
    i = -1
    for raw in lines:
        line = raw.rstrip("\n")
        i += 1
        if line.startswith(SCENE_HEADER):
            previous = None
            yield None
            continue
        own, sep, ancestor = line.partition(" < ")
        parsed = _own_role_name(own)
        if parsed is None:
            continue
        # The whole chain when the caller has it, else the one ancestor the line carries.
        # A stored comparison line keeps only that one, which is why the offline readers
        # take their lines from the snapshot beside it.
        if chains is not None and i < len(chains):
            chain = chains[i]
        else:
            under = _own_role_name(f"- {ancestor}") if sep else None
            chain = (under,) if under else ()
        yield parsed[0], parsed[1], previous, chain
        if parsed[1]:
            previous = parsed






def matches_volatile(role: str, name: str, triggers: list[VolatileTrigger],
                     previous: tuple[str, str] | None = None,
                     chain: tuple[tuple[str, str], ...] = ()) -> bool:
    for trigger in triggers:
        if not volatile_name_matches(role, name, trigger.role, trigger.name):
            continue
        if trigger.after is None:
            return True
        if previous is not None and volatile_name_matches(
                previous[0], previous[1], trigger.after[0], trigger.after[1]):
            return True
    return False


def _own_role_name(own: str) -> tuple[str, str] | None:
    m = ARIA_LINE.match(own)
    if not m:
        return None
    name, value = m.group("name"), m.group("value")
    if name is not None:
        label = name
    elif value:
        label = value.strip()
    else:
        label = ""
    return m.group("role"), label


def _mask_label(own: str) -> str:
    m = ARIA_LINE.match(own)
    if not m:
        return own
    role, name, attrs, value = (m.group("role"), m.group("name"),
                                m.group("attrs") or "", m.group("value"))
    if value:
        return f"- {role}: {VOLATILE_TOKEN}"
    if name is not None:
        return f'- {role} "{VOLATILE_TOKEN}"{attrs}'
    return own


def mask_volatile(lines: list[str], triggers: list[VolatileTrigger]) -> list[str]:
    """Replace matching nodes' names (and the same names on ancestor suffixes) with
    `VOLATILE_TOKEN`, so two trees that differ only in those values compare equal."""
    out = []
    previous: tuple[str, str] | None = None
    masked: dict[str, str] = {}
    for line in lines:
        own, sep, ancestor = line.partition(" < ")
        parsed = _own_role_name(own)
        if parsed and matches_volatile(parsed[0], parsed[1], triggers, previous):
            masked_own = _mask_label(own)
            if own.startswith("- "):
                masked[own[2:]] = masked_own[2:]
            own = masked_own
        if sep:
            ancestor = masked.get(ancestor, ancestor)
            out.append(f"{own} < {ancestor}")
        else:
            out.append(own)
        if parsed and parsed[1]:
            previous = parsed
    return out


def count_volatile_hits(lines: list[str], triggers: list[VolatileTrigger],
                        chains=None) -> int:
    """Most named nodes that match `triggers` in any one scene. A `## scene` line
    starts a new scene; a file with none is one scene. The matcher is
    `matches_volatile`, walked in reading order so `after` sees the previous
    named node."""
    best = 0
    current = 0
    for item in named_nodes(lines, chains):
        if item is None:
            best = max(best, current)
            current = 0
            continue
        role, name, previous, chain = item
        if matches_volatile(role, name, triggers, previous, chain):
            current += 1
    return max(best, current)


def volatile_paint_js(triggers: list[VolatileTrigger]) -> str:
    """Put the trigger's digits into every matching node, then paint its box one
    solid colour, on both sides. The digits come first because a box is as wide as
    the string in it: `0 鸭豆` painted over is narrower than `3,220 鸭豆` painted
    over, and everything after it on the line moves; a scene where the design itself
    shows another number (`鸭豆余额 20` on the debt scene, `12,480` elsewhere) has the
    same problem on its own side. With the trigger's digits in the first digit-bearing
    text node on both sides the two boxes are one width by construction, and the
    paint hides them. A node named by aria-label keeps its text.

    Matching is the same as `matches_volatile`: role and non-digit stem, plus
    `after` as the previous named node from a document-order walk of `nameOf`."""
    wanted_list = []
    for t in triggers:
        item: dict = {"role": t.role, "name": t.name, "after": None}
        if t.after:
            item["after"] = {"role": t.after[0], "name": t.after[1]}
        wanted_list.append(item)
    wanted = json.dumps(wanted_list, ensure_ascii=False)
    fill = json.dumps(VOLATILE_FILL)
    implicit = ", ".join(f"{tag}: {json.dumps(role)}"
                         for tag, role in VOLATILE_IMPLICIT_ROLES.items())
    text_like = json.dumps(list(VOLATILE_TEXT_LIKE))
    return """(() => {
  const wanted = %s;
  const fill = %s;
  const implicit = {%s};
  const textLike = new Set(%s);
  const stem = s => s.replace(/[\\d,]+/g, '').trim();
  const nameOf = el => (el.getAttribute('aria-label') || el.textContent || '')
    .trim().replace(/\\s+/g, ' ');
  const roleOf = el => el.getAttribute('role') || implicit[el.tagName] || el.tagName.toLowerCase();
  const nameOk = (nm, wanted) => nm === wanted || (Boolean(stem(wanted)) && stem(nm) === stem(wanted));
  const roleOk = (role, wanted) => role === wanted || (wanted === 'text' && textLike.has(role));
  const hit = (role, nm, w, prev) => {
    if (!nameOk(nm, w.name) || !roleOk(role, w.role)) return false;
    if (!w.after) return true;
    if (!prev) return false;
    return nameOk(prev.nm, w.after.name) && roleOk(prev.role, w.after.role);
  };
  const digitsOf = s => (s.match(/[\\d,]+/) || [null])[0];
  const retext = (el, w) => {
    // The design's digits go into the first text node that carries digits, on both
    // sides, so the box is one width whatever number each side showed.
    const target = digitsOf(w.name);
    if (!target || el.getAttribute('aria-label')) return;
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      if (/[\\d,]+/.test(node.nodeValue)) {
        node.nodeValue = node.nodeValue.replace(/[\\d,]+/, target);
        return;
      }
    }
  };
  const paint = (el, w) => {
    retext(el, w);
    el.style.backgroundColor = fill;
    el.style.color = fill;
    el.style.borderColor = fill;
    el.style.caretColor = fill;
    el.style.boxShadow = 'none';
    el.style.outline = 'none';
    for (const child of el.querySelectorAll('*')) {
      child.style.backgroundColor = fill;
      child.style.color = fill;
      child.style.borderColor = fill;
    }
  };
  let prev = null;
  for (const el of document.querySelectorAll('*')) {
    const nm = nameOf(el);
    if (!nm) continue;
    const role = roleOf(el);
    for (const w of wanted) {
      if (hit(role, nm, w, prev)) { paint(el, w); break; }
    }
    prev = {role, nm};
  }
})()""" % (wanted, fill, implicit, text_like)


# ---------------------------------------------------------------- capture
@dataclass
class Shot:
    png: Path
    aria: str
    console: list[str] = field(default_factory=list)
    elements: list[dict] = field(default_factory=list)
    classes: dict[str, str] = field(default_factory=dict)
    box: tuple[int, int, int, int] = (0, 0, 0, 0)  # x, y, w, h in viewport CSS pixels
    values: list[dict] = field(default_factory=list)


# Facts of every `[data-ui]` element under a root, document order. Visibility, box and
# computed style follow Quixote `src/q_element.js` (`getComputedStyle`,
# `getBoundingClientRect`). Text is the element's own character data plus descendants
# that do not themselves carry `data-ui` — so a `span.sc-interp` counts and a nested
# `[data-ui]` child does not. The walk is DOM-only, so a product story page can run it
# on `[data-story-root]`.
UI_VALUES_JS = """(root) => {
  const els = [];
  if (root && root.hasAttribute && root.hasAttribute('data-ui')) els.push(root);
  if (root && root.querySelectorAll) {
    for (const el of root.querySelectorAll('[data-ui]')) els.push(el);
  }
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
  const ancestors = new Map();
  for (const el of els) ancestors.set(el, nearest(el));
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
  const visible = (el) => {
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    if (cs.display === 'none' || cs.visibility === 'hidden' || cs.opacity === '0') {
      return false;
    }
    if (r.width === 0 || r.height === 0) return false;
    return true;
  };
  const out = [];
  for (const el of els) {
    const r = el.getBoundingClientRect();
    const anc = ancestors.get(el);
    let prev = null;
    for (const other of els) {
      if (other === el) break;
      if (ancestors.get(other) === anc) prev = other;
    }
    const cs = getComputedStyle(el);
    const pr = prev ? prev.getBoundingClientRect() : null;
    const ar = anc ? anc.getBoundingClientRect() : null;
    out.push({
      id: qualified.get(el),
      visible: visible(el),
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
  }
  return out;
}"""


# Every element a reader could be sent to, with the name it goes by: its `aria-label`,
# else its own text, else its `alt`. Boxes are viewport CSS pixels.
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
            extra_css: str | None = None, extra_js: str | None = None) -> Shot:
    """Screenshot, tree, elements and class set of the subtree under `selector`, on a
    page that has already been navigated and settled.

    The pixel judge sees `clip` — the mount element's box intersected with the
    viewport, in viewport coordinates; the tree and the class set walk the whole
    subtree, below the fold included. Both sides accept `extra_css` and `extra_js`: the
    baseline side takes its frame and the retired controls' hiding through them; both
    sides take the `volatile_values` paint through `extra_js`.
    """
    console: list[str] = []

    def on_console(message):
        if message.type == "error":
            console.append(f"{message.type}: {message.text}")

    def on_pageerror(error):
        console.append(f"pageerror: {error}")

    page.on("console", on_console)
    page.on("pageerror", on_pageerror)
    try:
        if extra_css:
            page.add_style_tag(content=extra_css)
        if extra_js:
            page.evaluate(extra_js)
        # Pinning the design frame (and hiding retired controls, which rides with
        # that extra_css) needs a clock step so the layout settles. Painting a
        # volatile box is an inline style and must not move the page's clock past
        # `scenes.<name>.clock` — that field is the one place elapsed time enters.
        if extra_css:
            run_clock(page, SETTLE_VIRTUAL_MS)
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
        elements = page.evaluate(ELEMENTS_JS)
        for e in elements:
            e["x"] -= x
            e["y"] -= y
        classes = class_set(page, selector)
        values = read_ui_values(page, selector)
    finally:
        page.remove_listener("console", on_console)
        page.remove_listener("pageerror", on_pageerror)
    aria_path(png).write_text(aria, encoding="utf-8")
    return Shot(png, aria, console, elements, classes, (x, y, w, h), values)


def read_ui_values(page, selector: str) -> list[dict]:
    """Every `[data-ui]` element under `selector`, document order, as one dict each."""
    return page.locator(selector).first.evaluate(UI_VALUES_JS)


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


def _scoped_entries(doc: dict, key: str, page: str | None = None):
    """Entries of `doc[key]` whose `page` applies, or that name no page.

    A control's role and name are not unique across pages (a retired 查看 on one
    page, a live 查看 on another). An entry that names its `page` applies there
    only.
    """
    for entry in doc.get(key) or []:
        if not (isinstance(entry, dict) and isinstance(entry.get("trigger"), dict)):
            continue
        scope = entry.get("page")
        if page is not None and scope and scope != page:
            continue
        yield entry


def _triggers(doc: dict, key: str, page: str | None = None) -> list[tuple[str, str]]:
    """`(role, name)` pairs from `doc[key]`, scoped to `page` when an entry names one."""
    out = []
    for entry in _scoped_entries(doc, key, page):
        t = entry["trigger"]
        out.append((str(t.get("role")), str(t.get("name"))))
    return out


def retired_triggers(doc: dict, page: str | None = None) -> list[tuple[str, str]]:
    """The retired controls to hide on the design side — for one design page when
    `page` is given."""
    return _triggers(doc, "retired_ids", page)


def hide_js_for(doc: dict, page: str) -> str | None:
    triggers = retired_triggers(doc, page)
    return hide_retired_js(triggers) if triggers else None


def volatile_triggers(doc: dict, page: str | None = None
                      ) -> list[VolatileTrigger]:
    """The display values not compared, for one design page when `page` is given.
    Each item is a `VolatileTrigger`; `after` is the previous named node, or
    None."""
    out: list[VolatileTrigger] = []
    for entry in _scoped_entries(doc, "volatile_values", page):
        t = entry["trigger"]
        out.append(VolatileTrigger(str(t.get("role")), str(t.get("name")),
                                   after_of(entry)))
    return out
