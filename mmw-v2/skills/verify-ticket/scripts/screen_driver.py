"""The one driver behind both judges of an interface: interface parity and the wiring check.

Everything that is not a judgement lives here — how a product is reached, put into a
state, addressed, released, and read — so that `visual-parity.py` and `wiring-check.py`
are two judgements over one drive and cannot drift apart. `extract_skeleton.py` of the
`align-screens` skill imports the same module for its offline render of a handoff
package, so the trees it commits are produced by the code path the judges read.

Six platform capabilities, one adapter per target kind (`target.kind` in the screen
contract; the reference file each `targets/<kind>.md` names is the human account):

    attach     hand back a page that drives the product, as the identity the seeded state
               belongs to; the adapter decides whether the state is put before or after
    ready      is the product answering — re-checked between scenes, not once at start
    address    turn a contract `route` into what `goto()` accepts
    release    give the product back
    transport  run the contract's `reach` mechanisms through the repository's own script
               (the write half); `transport_off` / `transport_on` break and mend it for
               the wiring check's negative control
    observe    read a persistent surface freshly, on a path the acting view did not
               produce (the read half)

Machine facts — addresses, the reach script, how to break the transport — are never in
the contract. They come from `.mmw/target.json` at the repository root:

    {"start": "<command that brings the product up and returns when it answers>",
     "discover": "<command printing one JSON object of addresses>",
     "reach": "<command prefix; mechanism names are appended>",
     "transport_off": "<command>", "transport_on": "<command>"}

Nobody starts the product by hand for a run: when `ready` says it is not answering, the
driver runs `start` once and asks again. A repository that declares no `start` gets a
run that stops on the first scene with the words to add it.

`discover` prints, per kind: electron `cdp`, `impl`, `backend`, optional `title`;
web-server-rendered / web-spa `origin`, optional `ready` (a path answering 2xx when up,
default `/health`); chrome-extension `extension_dir`, and the popup page under
`popup` (default `popup.html`). The reach command prints `KEY=VALUE` lines; every
`{key}` in a route, an `open` value, or an `observe` line is filled from them, and a web
target's `attach` takes its session cookie from the `cookie` key (`name=value`).
"""

from __future__ import annotations

import hashlib
import http.server
import json
import os
import re
import shlex
import socketserver
import subprocess
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from lease import leased_environment  # noqa: E402
from refusal import refusal  # noqa: E402

# ---------------------------------------------------------------- constants
# The three scripts `support.js` loads from unpkg. Answered from the handoff package's
# own `vendor/` directory when the handoff stored them, else from a local cache, else
# fetched once; a render never depends on the network twice.
CDN_PREFIX = "https://unpkg.com/"
VENDOR_DIR = "vendor"
DEFAULT_CACHE = Path.home() / ".cache" / "mmw" / "visual-parity"

# Virtual milliseconds the controlled clock is run after a navigation: `support.js`
# polls readiness every 50 ms and each component first renders on that poll, and a
# `requestAnimationFrame` focus effect rides the same clock. Far below the handoff
# package's own timers (an 1800 ms auto-advance, a 2600 ms auto-recover, a 2400 ms toast).
SETTLE_VIRTUAL_MS = 200
# Further virtual time the driver may spend, in `SETTLE_STEP_MS` steps, waiting for the
# mount element to appear. Kept under the shortest auto-advance in any handoff package
# seen so far, so a scene is never captured one step past itself.
SETTLE_BUDGET_MS = 1400
SETTLE_STEP_MS = 100
# Wall-clock bound on one click or fill. The page's clock is paused, so an element that
# is not enabled now stays so; the bound only keeps a wrong step from hanging the run.
ACTION_TIMEOUT_MS = 2000
# Every scene starts the fake clock here and moves it forward only; `pause_at` refuses
# to go back, and a page reached over CDP keeps one clock for the whole run.
CLOCK_EPOCH_MS = 1_700_000_000_000

# Roles whose accessible name is dropped: a product page labels its `<main>`, a
# component page does not, and the landmark itself is what matters.
LANDMARKS = {"main", "navigation", "banner", "contentinfo", "region", "complementary"}
# `open` steps on these roles carry a value to type instead of a click.
INPUT_ROLES = {"textbox", "combobox", "spinbutton", "searchbox"}
# Classes the Claude Design runtime adds around interpolated text and hosts; a product
# never carries them, and they are not part of the design.
RUNTIME_CLASS_PREFIXES = ("sc-", "dc-")

DATA_SCREEN = "data-screen"
PLACEHOLDER = re.compile(r"\{(\w+)\}")
VIEWPORT_RE = re.compile(r"^(\d+)x(\d+)$")


# ---------------------------------------------------------------- the contract
@dataclass
class Scene:
    """One screen declaration of the contract, joined with its `scenes.json` entry."""
    name: str
    page: str
    mount: str
    route: str
    reach: list[str]
    open: list[dict]
    props: dict
    # Virtual milliseconds the controlled clock is run after `open`, before capture:
    # the one place elapsed time enters, for a state the design itself defines by time
    # (a notice that dismisses after its toast timer).
    clock: int = 0


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
                             f"step 2 to declare the screen axis")
    return doc


def mechanisms_of(doc: dict) -> dict[str, dict]:
    """The mechanism table as a mapping, whichever shape the file wrote it in."""
    raw = doc.get("mechanisms") or {}
    if isinstance(raw, list):
        return {str(m): {} for m in raw}
    return {str(k): (v or {}) for k, v in raw.items()}


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


def open_steps(raw) -> list[dict]:
    steps = []
    for step in raw or []:
        if isinstance(step, str):
            steps.append({"row": step, "value": None})
        else:
            steps.append({"row": str(step.get("row")), "value": step.get("value")})
    return steps


def scenes_of(doc: dict, catalogue: dict[str, dict]) -> dict[str, Scene]:
    """Every screen declaration, with page-level `mount` and `route` filled in."""
    pages = doc.get("pages") or {}
    out = {}
    for name, decl in (doc.get("scenes") or {}).items():
        decl = decl or {}
        page = decl.get("page") or catalogue.get(name, {}).get("page") or ""
        page_decl = pages.get(page) or {}
        out[name] = Scene(
            name=name, page=page,
            mount=str(decl.get("mount") or page_decl.get("mount") or ""),
            route=str(decl.get("route") or page_decl.get("route") or ""),
            reach=[str(r) for r in (decl.get("reach") or [])],
            open=open_steps(decl.get("open")),
            props=catalogue.get(name, {}).get("props") or {},
            clock=int(decl.get("clock") or 0))
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
    `["all"]` means every mount the contract declares (the addressing self-check)."""
    scenes = scenes_of(doc, catalogue)
    if mounts == ["all"]:
        mounts = sorted({s.mount for s in scenes.values()})
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


def scene_for_row(row: dict, scenes: dict[str, Scene]) -> Scene | None:
    """The scene the wiring check drives a row on: the row's `drive.scene` when it names
    one, else the first of the row's `scenes` the contract declares. Its `reach` and
    `open` put the control on screen; a row whose control sits in a dialog is reached
    the way the scene is."""
    drive = row.get("drive") or {}
    chosen = drive.get("scene")
    if chosen:
        if chosen not in scenes:
            raise SystemExit(f"row {row.get('id')}: drive.scene {chosen!r} is not a declared scene")
        return scenes[chosen]
    for name in row.get("scenes") or []:
        if name in scenes:
            return scenes[name]
    return None


def drive_of(row: dict) -> tuple[list[str], list[dict]]:
    """A row's own way to a state its scenes never show actionable: extra `reach`
    mechanisms run after the scene's, and `open` steps performed after the scene's
    chain and before the trigger (typing a name, picking a file)."""
    drive = row.get("drive") or {}
    reach = [str(m) for m in drive.get("reach") or []]
    steps = []
    for step in drive.get("open") or []:
        steps.append({"row": step, "value": None} if isinstance(step, str)
                     else {"row": str(step.get("row")), "value": step.get("value")})
    return reach, steps


def fill(text: str, values: dict[str, str]) -> str:
    return PLACEHOLDER.sub(lambda m: values.get(m.group(1), m.group(0)), text)


# ---------------------------------------------------------------- repository config
def repo_root(start: Path | None = None) -> Path:
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=start or Path.cwd(),
                             capture_output=True, text=True, check=True).stdout.strip()
        return Path(out)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return (start or Path.cwd()).resolve()


def target_config(root: Path) -> dict:
    path = root / ".mmw" / "target.json"
    if not path.exists():
        raise SystemExit(f"no {path}: the repository has not said how its product is "
                         f"reached (see verify-ticket/references/targets/README.md)")
    cfg = json.loads(path.read_text(encoding="utf-8"))
    for key in ("discover", "reach"):
        if not cfg.get(key):
            raise SystemExit(f"{path} has no `{key}` command")
    return cfg


def command_env(cwd: Path) -> dict[str, str]:
    """This process's environment plus this run's lease.

    Every command `.mmw/target.json` declares is run through here, so a repository is
    told which run it is in rather than having to work it out — and never has to invent
    an allocation of its own. Inventing one is how a machine ended up with five worktrees
    sharing three fixed ports (2026-09-05): the contract's seven questions were all in
    the singular, so nobody was ever asked.

    The variables reach the declared command and stop there. A repository translates
    them at the moment it starts a process, never into the session or the test
    environment: a suite that asserts its product's registered port number is right to,
    and a derived port leaking into it turns a correct suite red.
    """
    env = dict(os.environ)
    env.update(leased_environment(Path(cwd)))
    return env


def run_command(command: str, cwd: Path, extra: list[str] | None = None) -> str:
    proc = subprocess.run(shlex.split(command) + (extra or []), cwd=cwd,
                          capture_output=True, text=True, env=command_env(cwd))
    if proc.returncode != 0:
        raise SystemExit(f"`{command}{' ' + ' '.join(extra) if extra else ''}` exited "
                         f"{proc.returncode}: {proc.stderr.strip() or proc.stdout.strip()}")
    return proc.stdout


def discover(cfg: dict, root: Path) -> dict:
    out = run_command(cfg["discover"], root).strip()
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"discover printed no JSON object: {out[:200]!r} ({exc})")
    if not isinstance(data, dict):
        raise SystemExit("discover must print one JSON object")
    return data


def key_values(text: str) -> dict[str, str]:
    values = {}
    for line in text.splitlines():
        k, sep, v = line.partition("=")
        if sep and k.strip():
            values[k.strip()] = v.strip()
    return values


# ---------------------------------------------------------------- HTTP read surface
def http_get(url: str, headers: dict | None = None, timeout: int = 15):
    """`(status, content_type, body_bytes)`; a 4xx/5xx is returned, not raised."""
    req = urllib.request.Request(url, method="GET", headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", "") if e.headers else "", b""
    except (urllib.error.URLError, OSError) as e:
        return 0, "", str(e).encode()


def http_call(base: str, method: str, path: str, headers: dict | None = None):
    req = urllib.request.Request(base.rstrip("/") + path, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        return e.code, None
    except (urllib.error.URLError, OSError):
        return 0, None


SIMPLE_EXPR = re.compile(r"^\s*(\.[\w.\[\]]*)\s*(?:(==|!=|contains|exists)\s*(.*))?$")
JQ_VAR = re.compile(r"\$([A-Za-z_]\w*)")


def evaluate(expr: str, body: object, values: dict[str, str] | None = None) -> tuple[bool, object]:
    """An observe expression against a JSON body. The built-in grammar covers
    `.a.b[0] == "x"`, `.a != 1`, `.a contains "x"`, `.a exists`, and a bare `.a` (truthy);
    anything else is a jq program, run by the `jq` on PATH with every value the reach
    script printed or an `open` step typed bound as a `$variable`. A `$variable` nothing
    supplies is a contract defect and stops the run by name."""
    expr = re.sub(r"\s+#.*$", "", expr.strip())  # a trailing `# note` is for the reader
    m = SIMPLE_EXPR.match(expr)
    if not m or "$" in expr:
        return evaluate_jq(expr, body, values or {})
    value: object = body
    for part in re.findall(r"\.(\w+)|\[(\d+)\]", m.group(1)):
        key, idx = part
        try:
            value = value[key] if key else value[int(idx)]
        except (KeyError, IndexError, TypeError):
            value = None
            break
    op, rhs = m.group(2), (m.group(3) or "").strip()
    if op is None:
        return bool(value), value
    if op == "exists":
        return value is not None, value
    want = json.loads(rhs) if rhs else None
    if op == "==":
        return value == want, value
    if op == "!=":
        return value != want, value
    return (want in value) if isinstance(value, (str, list)) else False, value


def evaluate_jq(expr: str, body: object, values: dict[str, str]) -> tuple[bool, object]:
    """`jq -e <expr>` over the body: exit 0 is true, 1 is false or null; the last output
    line is what was seen. Values bind as `--argjson` when they read as JSON scalars
    (numbers, booleans, null) and as `--arg` strings otherwise."""
    unbound = sorted({v for v in JQ_VAR.findall(expr) if v not in values})
    if unbound:
        raise SystemExit(f"observe expression uses ${', $'.join(unbound)}, which neither the "
                         f"reach script's KEY=VALUE lines nor a typed open step supplies: {expr}")
    args = ["jq", "-e", "-c"]
    for key, value in values.items():
        if f"${key}" not in expr:
            continue
        try:
            parsed = json.loads(value)
        except (ValueError, TypeError):
            parsed = None
        if isinstance(parsed, (int, float, bool)) or parsed is None and value == "null":
            args += ["--argjson", key, value]
        else:
            args += ["--arg", key, value]
    args.append(expr)
    try:
        run = subprocess.run(args, input=json.dumps(body, ensure_ascii=False), capture_output=True,
                             text=True, timeout=30)
    except FileNotFoundError as exc:
        raise SystemExit("observe expression needs jq on PATH: " + expr) from exc
    if run.returncode not in (0, 1):
        raise SystemExit(f"jq could not run the observe expression {expr!r}: "
                         f"{run.stderr.strip() or run.returncode}")
    lines = [line for line in run.stdout.splitlines() if line.strip()]
    got: object = None
    if lines:
        try:
            got = json.loads(lines[-1])
        except ValueError:
            got = lines[-1]
    return run.returncode == 0, got


NODE_EXPR = re.compile(r'^\s*node\s+(?P<role>[a-zA-Z]+)(?:\s+"(?P<name>(?:[^"\\]|\\.)*)")?'
                       r'\s+(?P<op>exists|absent)\s*$')


def evaluate_tree(expr: str, tree_lines: list[str]) -> tuple[bool, object]:
    """`node <role> "<name>" exists` (or `absent`) against a normalised tree."""
    m = NODE_EXPR.match(expr)
    if not m:
        raise ValueError(f"cannot read tree expression {expr!r}")
    role, name, op = m.group("role"), m.group("name"), m.group("op")
    wanted = f'- {role} "{name}"' if name is not None else f"- {role}"
    hits = [ln for ln in tree_lines if ln.split(" < ")[0].startswith(wanted)]
    found = bool(hits)
    return (found if op == "exists" else not found), hits[:3]


# ---------------------------------------------------------------- the tree
ARIA_LINE = re.compile(
    r'^(?P<indent>\s*)- (?P<role>[a-zA-Z]+)(?: "(?P<name>(?:[^"\\]|\\.)*)")?'
    r'(?P<attrs>(?: \[[^\]]*\])*)(?::\s*(?P<value>.*))?\s*$')


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
        m = ARIA_LINE.match(ln)
        if not m:
            continue
        indent = len(m.group("indent").expandtabs(2))
        while stack and stack[-1][0] >= indent:
            stack.pop()
        role, name, attrs, value = (m.group("role"), m.group("name"),
                                    m.group("attrs") or "", m.group("value"))
        if role in LANDMARKS:
            name = None
        if name is None and not value and not attrs.strip():
            continue
        if value:
            node = f"- {role}: {value.strip()}"
        elif name is not None:
            node = f'- {role} "{name}"{attrs}'
        else:
            node = f"- {role}{attrs}"
        parent = stack[-1][1] if stack else None
        out.append(f"{node} < {parent[2:]}" if parent else node)
        if name is not None or value:
            stack.append((indent, node))
    return out


def aria_diff(a: str, b: str, out: Path | None = None,
              volatile: list[tuple[str, str]] | None = None) -> dict:
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
        m = OPTION_LINE.match(line)
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
# non-digit stem of the name is the same.
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


def matches_volatile(role: str, name: str, triggers: list[tuple[str, str]]) -> bool:
    for wanted_role, wanted_name in triggers:
        if role != wanted_role:
            continue
        if name == wanted_name:
            return True
        stem = volatile_stem(wanted_name)
        if stem and volatile_stem(name) == stem:
            return True
    return False


def _mask_own(own: str, triggers: list[tuple[str, str]]) -> str:
    m = ARIA_LINE.match(own)
    if not m:
        return own
    role, name, attrs, value = (m.group("role"), m.group("name"),
                                m.group("attrs") or "", m.group("value"))
    label = value.strip() if value else (name or "")
    if not matches_volatile(role, label, triggers):
        return own
    if value:
        return f"- {role}: {VOLATILE_TOKEN}"
    if name is not None:
        return f'- {role} "{VOLATILE_TOKEN}"{attrs}'
    return own


def mask_volatile(lines: list[str], triggers: list[tuple[str, str]]) -> list[str]:
    """Replace matching nodes' names (and the same names on ancestor suffixes) with
    `VOLATILE_TOKEN`, so two trees that differ only in those values compare equal."""
    out = []
    for line in lines:
        own, sep, ancestor = line.partition(" < ")
        own = _mask_own(own, triggers)
        if sep:
            out.append(f"{own} < {_mask_own('- ' + ancestor, triggers)[2:]}")
        else:
            out.append(own)
    return out


def volatile_paint_js(triggers: list[tuple[str, str]]) -> str:
    """Put the trigger's digits into every matching node, then paint its box one
    solid colour, on both sides. The digits come first because a box is as wide as
    the string in it: `0 鸭豆` painted over is narrower than `3,220 鸭豆` painted
    over, and everything after it on the line moves; a scene where the design itself
    shows another number (`鸭豆余额 20` on the debt scene, `12,480` elsewhere) has the
    same problem on its own side. With the trigger's digits in the first digit-bearing
    text node on both sides the two boxes are one width by construction, and the
    paint hides them. A node named by aria-label keeps its text."""
    wanted = json.dumps([{"role": r, "name": n} for r, n in triggers], ensure_ascii=False)
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
  const hit = (role, nm, w) => {
    const nameOk = nm === w.name || (Boolean(stem(w.name)) && stem(nm) === stem(w.name));
    if (!nameOk) return false;
    if (role === w.role) return true;
    return w.role === 'text' && textLike.has(role);
  };
  const digitsOf = s => (s.match(/[\d,]+/) || [null])[0];
  const retext = (el, w) => {
    // The design's digits go into the first text node that carries digits, on both
    // sides, so the box is one width whatever number each side showed.
    const target = digitsOf(w.name);
    if (!target || el.getAttribute('aria-label')) return;
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      if (/[\d,]+/.test(node.nodeValue)) {
        node.nodeValue = node.nodeValue.replace(/[\d,]+/, target);
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
  for (const el of document.querySelectorAll('*')) {
    const nm = nameOf(el);
    if (!nm) continue;
    const role = roleOf(el);
    for (const w of wanted) {
      if (hit(role, nm, w)) { paint(el, w); break; }
    }
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


# One session per page for the whole run. An emulation override belongs to the session
# that set it, so a second session cannot clear it and a first session left attached
# goes on applying it.
_CDP_SESSIONS: dict[int, object] = {}
_CLOCKED: dict[int, int] = {}


def cdp_session(page):
    session = _CDP_SESSIONS.get(id(page))
    if session is None:
        session = page.context.new_cdp_session(page)
        _CDP_SESSIONS[id(page)] = session
    return session


def resize(page, viewport: tuple[int, int], over_cdp: bool) -> None:
    """Put the page in a window of this size, however it was reached.

    A context this program launched was given its viewport and its device pixel ratio
    when it was created. A page reached over CDP belongs to the application, whose
    context was created by somebody else and cannot be given either — so the size and
    the ratio are pushed down as a device-metrics override instead. The ratio has to be
    said out loud there: on a high-resolution screen the application renders at two
    device pixels per CSS pixel, and a screenshot twice the size of the baseline's is a
    failure before anything is compared. This layer stays whatever the target: an
    extension's popup opened as a plain tab has no 400 px constraint of its own.
    """
    if over_cdp:
        cdp_session(page).send(
            "Emulation.setDeviceMetricsOverride",
            {"width": viewport[0], "height": viewport[1],
             "deviceScaleFactor": 1, "mobile": False})
        page.emulate_media(reduced_motion="reduce")
    else:
        page.set_viewport_size({"width": viewport[0], "height": viewport[1]})


def restore(page, home: str) -> None:
    """Give the application's window back to the user: its own size, its own clock, and
    its own page. The override `resize` pushes down holds until the session that set it
    clears it; a paused clock would leave every timer of the application dead."""
    session = _CDP_SESSIONS.pop(id(page), None)
    try:
        if _CLOCKED.pop(id(page), None) is not None:
            page.clock.resume()
        if session is not None:
            session.send("Emulation.clearDeviceMetricsOverride")
            page.emulate_media(reduced_motion="no-preference")
            session.detach()
        if home:
            page.goto(home, wait_until="domcontentloaded")
    except Exception:
        pass


def install_clock(page) -> None:
    """A controlled clock, installed once per page and moved forward only. Time is
    paused before the navigation, so nothing the page schedules fires until the driver
    runs it, and never further than the driver runs it."""
    now = _CLOCKED.get(id(page))
    if now is None:
        page.clock.install(time=CLOCK_EPOCH_MS)
        now = CLOCK_EPOCH_MS
    page.clock.pause_at(now)
    _CLOCKED[id(page)] = now


def run_clock(page, ms: int) -> None:
    page.clock.run_for(ms)
    _CLOCKED[id(page)] = _CLOCKED.get(id(page), CLOCK_EPOCH_MS) + ms


def navigate(page, url: str, reload: bool = False) -> None:
    """Open `url` under the controlled clock and let it settle. `reload` is for a
    hash-routed application: a same-document fragment jump returns from `networkidle`
    before the view has re-rendered, and a reload is what makes it a fresh document."""
    install_clock(page)
    page.goto(url, wait_until="networkidle")
    if reload:
        page.reload(wait_until="networkidle")
    run_clock(page, SETTLE_VIRTUAL_MS)


def wait_for_mount(page, selector: str) -> None:
    """Run the clock in steps until the mount element is on screen, within the budget."""
    spent = 0
    while mount_rect(page, selector) is None:
        if spent >= SETTLE_BUDGET_MS:
            raise SystemExit(f"no visible element matches {selector} after "
                             f"{SETTLE_VIRTUAL_MS + spent} ms of controlled time")
        run_clock(page, SETTLE_STEP_MS)
        spent += SETTLE_STEP_MS


def perform(page, steps: list[dict], rows: dict[str, dict], values: dict[str, str]) -> None:
    """Walk a scene's `open` chain: each step names a contract row, whose trigger is
    clicked — or filled, for an input role, with the step's value. A control the
    previous step is still bringing on screen is waited for in clock steps, within the
    same budget the mount gets; the mount itself is waited for after the chain."""
    PlaywrightError = _playwright_error()
    for step in steps:
        row = rows.get(step["row"])
        if row is None:
            raise SystemExit(f"open step names no contract row: {step['row']}")
        trig = row["trigger"]
        control = page.get_by_role(trig["role"], name=trig["name"], exact=True)
        spent = 0
        while control.count() == 0:
            if spent >= SETTLE_BUDGET_MS:
                raise SystemExit(f'open step {step["row"]}: no control {trig["role"]} '
                                 f'"{trig["name"]}" on the page after '
                                 f"{SETTLE_VIRTUAL_MS + spent} ms of controlled time")
            run_clock(page, SETTLE_STEP_MS)
            spent += SETTLE_STEP_MS
        try:
            if trig["role"] in INPUT_ROLES:
                typed = fill(str(step.get("value") or ""), values)
                control.first.fill(typed, timeout=ACTION_TIMEOUT_MS)
                # What was typed is a value from here on: `$typed` is the latest, and
                # `$typed_<field>` keeps each row's, named by the row id's last segment.
                values["typed"] = typed
                values["typed_" + step["row"].rsplit(".", 1)[-1].replace("-", "_")] = typed
            else:
                control.first.click(timeout=ACTION_TIMEOUT_MS)
        except PlaywrightError as exc:
            # Under a paused clock nothing changes with wall time: a control that is not
            # enabled or visible now will not become so by waiting.
            reason = str(exc).splitlines()[0] if str(exc) else exc.__class__.__name__
            state = _control_state(control.first)
            raise SystemExit(f'open step {step["row"]}: {trig["role"]} "{trig["name"]}" '
                             f"could not be acted on ({state}): {reason}") from exc
        run_clock(page, SETTLE_VIRTUAL_MS)


def _playwright_error() -> type[Exception]:
    """Playwright's error class, imported when first needed: the driver's own tests run
    a fake page without the package installed."""
    try:
        from playwright.sync_api import Error
    except ImportError:
        return Exception
    return Error


def _control_state(locator) -> str:
    PlaywrightError = _playwright_error()
    try:
        if not locator.is_visible():
            return "not visible"
        if not locator.is_enabled():
            return "disabled"
        return "visible and enabled"
    except PlaywrightError:
        return "state unknown"


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
    finally:
        page.remove_listener("console", on_console)
        page.remove_listener("pageerror", on_pageerror)
    aria_path(png).write_text(aria, encoding="utf-8")
    return Shot(png, aria, console, elements, classes, (x, y, w, h))


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


def mount_selector(mount: str) -> str:
    return f'[{DATA_SCREEN}="{mount}"]'


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


def page_by_title(browser, title_includes: str | None, timeout_seconds: int = 15):
    """The application's own page, out of a browser this program connected to.

    Picked by a substring of the window title rather than of the URL: a development
    server takes whichever port is free at startup, so the URL is not the same twice.
    With no substring given the first page is taken, which is what an application with
    one window has.
    """
    import time

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
        if time.monotonic() >= deadline:
            break
        time.sleep(0.5)
    raise SystemExit(
        f"no page whose title holds {title_includes!r} within {timeout_seconds}s. "
        f"Pages found: {seen or 'none'}")


# ---------------------------------------------------------------- adapters
class Adapter:
    """The six capabilities for one target kind. Subclasses fill the blanks; the order
    of `transport` and `attach` is theirs too (`reach_before_attach`)."""

    kind = ""
    over_cdp = False
    reach_before_attach = False
    # Which read surface `observe` lines are held to: `json` (a JSON read surface plus a
    # jq-style expression) or `tree` (an HTML page read in a second tab, `node … exists`).
    read_surface = "json"

    def __init__(self, cfg: dict, addresses: dict, root: Path):
        self.cfg, self.addresses, self.root = cfg, addresses, root
        self.pw = None
        self.browser = None
        self.page = None
        self.home = ""

    def need(self, key: str):
        if key not in self.addresses:
            raise SystemExit(f"discover printed no `{key}` for target kind {self.kind}")
        return self.addresses[key]

    # -- write half
    def transport(self, mechanisms: list[str], values: dict[str, str],
                  perturb: bool = False) -> dict[str, str]:
        if not mechanisms:
            return values
        extra = list(mechanisms) + (["--perturb"] if perturb else [])
        out = run_command(self.cfg["reach"], self.root, extra)
        merged = dict(values)
        merged.update(key_values(out))
        return merged

    def transport_off(self) -> None:
        cmd = self.cfg.get("transport_off")
        if not cmd:
            raise SystemExit(".mmw/target.json has no `transport_off`; the negative "
                             "control of the wiring check cannot break the transport")
        run_command(cmd, self.root)

    def transport_on(self) -> None:
        cmd = self.cfg.get("transport_on")
        if cmd:
            run_command(cmd, self.root)

    # -- the driven page
    def attach(self, pw, values: dict[str, str]):
        raise NotImplementedError

    def ready(self) -> tuple[bool, str]:
        raise NotImplementedError

    def instance_ok(self) -> tuple[bool, str]:
        """Whether the product answering these addresses is the one this run brought up.

        Liveness is not identity. `ready` used to ask only whether *a* product answered,
        and on a machine running several worktrees that difference is the whole of the
        risk: a driver that accepts any answer judges another run's code and reports the
        verdict as this ticket's. Worse, the answer also skips `start`, so a repository's
        own "another checkout holds these ports" guard never runs.

        `discover` names the check as one `observe` line in this target's own read
        surface, so every adapter gets it without new machinery, and it is asked again
        between scenes rather than once at start-up — an application replaced mid-run is
        exactly what a start-up gate cannot see (2026-09-05: one worktree's application
        was ended from outside and another's took its ports one second later).

        A target that declares no check is unchanged.
        """
        line = self.addresses.get("instance_check")
        if not line:
            return True, ""
        name = self.addresses.get("instance") or "this run"
        try:
            ok, _got, why = self.observe(line, {})
        except Exception as exc:  # noqa: BLE001 - any failure here means "cannot tell"
            return False, refusal(
                f"The instance check `{line}` could not be read: {exc}.",
                "Without it there is no telling whose product is answering.",
                "Bring your own up with the `start` command in .mmw/target.json; if it "
                "will not come up, report the ticket blocked and stop.",
            )
        if ok:
            return True, ""
        return False, refusal(
            f"The product on these addresses is not the one {name} started ({why or line}).",
            "Another run holds them, so anything measured here is that run's code.",
            "Bring your own up with the `start` command in .mmw/target.json; if the "
            "addresses stay held, report the ticket blocked and stop.",
        )

    def address(self, route: str, values: dict[str, str]) -> str:
        raise NotImplementedError

    def release(self) -> None:
        raise NotImplementedError

    def new_context(self, viewport: tuple[int, int]):
        """A context of this program's own for the baseline side, when the driven page
        cannot host it (a launched browser); `None` when the driven page is reused."""
        return None

    # -- read half
    def observe(self, line: str, values: dict[str, str]) -> tuple[bool, object, str]:
        """`(ok, got, why)` for one `METHOD /path -> <expression>` line."""
        raise NotImplementedError


class ElectronAdapter(Adapter):
    """An application that already runs: reached over its debugging port, put into a
    state by its local backend, read through that backend's JSON surface."""

    kind = "electron"
    over_cdp = True
    reach_before_attach = False
    read_surface = "json"

    def attach(self, pw, values):
        self.pw = pw
        try:
            self.browser = pw.chromium.connect_over_cdp(self.need("cdp"), timeout=10000)
        except Exception as exc:  # noqa: BLE001
            raise SystemExit(f"no application on {self.addresses['cdp']}: {exc}")
        self.page = page_by_title(self.browser, self.addresses.get("title"))
        self.home = self.need("impl")
        return self.page

    def ready(self):
        status, _ = http_call(self.need("backend"), "GET", "/health")
        if status >= 400 or status == 0:
            return False, f"no backend answering {self.addresses['backend']}/health ({status})"
        if self.page is not None and self.page.is_closed():
            return False, "the application's page is gone"
        return self.instance_ok()

    def address(self, route, values):
        return self.need("impl").rstrip("/") + "/" + fill(route, values).lstrip("/")

    def release(self):
        if self.page is not None:
            restore(self.page, self.home)
        if self.browser is not None:
            self.browser.close()  # disconnects; the application goes on running

    def observe(self, line, values):
        op, _, expr = line.partition("->")
        method, _, path = op.strip().partition(" ")
        if NODE_EXPR.match(expr):
            return False, None, ("this target has a JSON read surface; an observe line "
                                 "reads it with a jq-style expression, not the tree")
        status, body = http_call(self.need("backend"), method.upper(),
                                 fill(path.strip(), values))
        if status >= 300 or status == 0:
            return False, status, f"{op.strip()} answered {status}"
        ok, got = evaluate(expr.strip(), body, values)
        return ok, got, "" if ok else f"{expr.strip()} was {json.dumps(got, ensure_ascii=False)}"


class WebAdapter(Adapter):
    """A page on a web server, server-rendered or a single-page application: the state
    is put first (a user has to exist before anyone can be that user), then a browser
    of this program's own is launched and given the session the reach script printed."""

    kind = "web-server-rendered"
    over_cdp = False
    reach_before_attach = True
    read_surface = "tree"

    def __init__(self, cfg, addresses, root):
        super().__init__(cfg, addresses, root)
        self.context = None
        self.cookie_header = ""

    def _cookies(self, values):
        raw = values.get("cookie", "")
        origin = urllib.parse.urlsplit(self.need("origin"))
        cookies = []
        for part in filter(None, (p.strip() for p in raw.split(";"))):
            name, _, value = part.partition("=")
            cookies.append({"name": name, "value": value, "domain": origin.hostname,
                            "path": "/"})
        self.cookie_header = raw
        return cookies

    def attach(self, pw, values):
        self.pw = pw
        self.browser = pw.chromium.launch()
        self.context = self.browser.new_context(device_scale_factor=1,
                                                reduced_motion="reduce", locale="zh-CN")
        cookies = self._cookies(values)
        if cookies:
            self.context.add_cookies(cookies)
        self.page = self.context.new_page()
        self.home = self.need("origin")
        return self.page

    def ready(self):
        path = self.addresses.get("ready", "/health")
        status, _, _ = http_get(self.need("origin").rstrip("/") + path)
        if status == 0 or status >= 400:
            return False, f"{self.addresses['origin']}{path} answered {status}"
        return self.instance_ok()

    def address(self, route, values):
        return self.need("origin").rstrip("/") + "/" + fill(route, values).lstrip("/")

    def release(self):
        if self.browser is not None:
            self.browser.close()

    def new_context(self, viewport):
        return self.browser.new_context(
            viewport={"width": viewport[0], "height": viewport[1]},
            device_scale_factor=1, reduced_motion="reduce", locale="zh-CN")

    def observe(self, line, values):
        op, _, expr = line.partition("->")
        method, _, path = op.strip().partition(" ")
        url = self.need("origin").rstrip("/") + fill(path.strip(), values)
        headers = {"Cookie": self.cookie_header} if self.cookie_header else {}
        if NODE_EXPR.match(expr):
            if method.upper() != "GET":
                return False, None, "a tree observe line reads with GET"
            # A second tab, in the same session: the driven page stays where the action
            # left it, and the read is a fresh document the action's view did not paint.
            reader = self.context.new_page()
            try:
                reader.goto(url, wait_until="networkidle")
                tree = normalize_aria(reader.locator("body").aria_snapshot())
            finally:
                reader.close()
            ok, got = evaluate_tree(expr.strip(), tree)
            return ok, got, "" if ok else f"{expr.strip()} was {json.dumps(got, ensure_ascii=False)}"
        status, ctype, raw = http_get(url, headers) if method.upper() == "GET" else (0, "", b"")
        if method.upper() != "GET":
            status, body = http_call(self.need("origin"), method.upper(),
                                     fill(path.strip(), values), headers)
        else:
            if status >= 300 or status == 0:
                return False, status, f"{op.strip()} answered {status}"
            if "json" not in ctype:
                return False, None, (f"{op.strip()} answered {ctype or 'no content type'}; a "
                                     f"jq-style expression needs a JSON read surface — on an "
                                     f"HTML surface write `node <role> \"<name>\" exists`")
            body = json.loads(raw) if raw else None
        if status >= 300 or status == 0:
            return False, status, f"{op.strip()} answered {status}"
        ok, got = evaluate(expr.strip(), body, values)
        return ok, got, "" if ok else f"{expr.strip()} was {json.dumps(got, ensure_ascii=False)}"


class WebSpaAdapter(WebAdapter):
    kind = "web-spa"
    read_surface = "json"


class ChromeExtensionAdapter(WebAdapter):
    """Designed from the platform's rules, not measured on a product: no repository
    holds one yet. The popup is opened as a plain tab (a popup closes on blur), so
    attach and address take the web shape and the fixed popup size is one `viewports`
    entry; the extension id is derived at load time, so `discover` prints it."""

    kind = "chrome-extension"
    read_surface = "json"

    def attach(self, pw, values):
        self.pw = pw
        ext = self.need("extension_dir")
        self.context = pw.chromium.launch_persistent_context(
            "", headless=False, device_scale_factor=1, reduced_motion="reduce",
            args=[f"--disable-extensions-except={ext}", f"--load-extension={ext}"])
        self.browser = self.context.browser
        self.page = self.context.new_page()
        self.home = ""
        return self.page

    def ready(self):
        # A service worker is recycled after about thirty seconds idle; whether it is
        # there is asked again before every scene, which is the point of `ready`.
        workers = [w for w in self.context.service_workers]
        return self.instance_ok() if workers else (False, "no service worker is alive")

    def address(self, route, values):
        ext_id = self.need("extension_id")
        page = self.addresses.get("popup", "popup.html")
        return f"chrome-extension://{ext_id}/{page}" + fill(route, values)

    def release(self):
        if self.context is not None:
            self.context.close()

    def new_context(self, viewport):
        return self.context


ADAPTERS = {a.kind: a for a in (ElectronAdapter, WebAdapter, WebSpaAdapter,
                                ChromeExtensionAdapter)}


START_TIMEOUT_S = 600


def adapter_for(doc: dict, root: Path) -> Adapter:
    kind = str((doc.get("target") or {}).get("kind") or "")
    cls = ADAPTERS.get(kind)
    if cls is None:
        raise SystemExit(f"target.kind {kind!r} has no adapter; one of {sorted(ADAPTERS)}")
    cfg = target_config(root)
    adapter = cls(cfg, discover(cfg, root), root)
    bring_up(adapter)
    return adapter


def bring_up(adapter: Adapter) -> None:
    """The product answering before the first scene. `ready` is asked; when it says no,
    `.mmw/target.json`'s `start` is run once — the repository's own way of bringing its
    product up, with whatever it needs found or chosen inside that command — and
    `discover` and `ready` are asked again. Nothing here is told how the product
    starts, and nobody is expected to have started it by hand."""
    ok, why = adapter.ready()
    start = adapter.cfg.get("start")
    if ok and not start:
        return
    if not start:
        raise SystemExit(f"{why}; .mmw/target.json declares no `start`, so the run cannot "
                         f"bring the product up itself. Declare `start` (a command that "
                         f"brings it up and returns once it answers; see "
                         f"verify-ticket/references/targets/README.md)")
    # 每次都跑，不只在没人应答的时候。`start` 按契约是幂等的，对已在应答的产品原样保留
    # ——但只有它知道那个产品是不是本工作树此刻的代码。跳过它，一个仍在应答的旧产品就
    # 永远不会被换掉，判据在旧代码上得出的结论没人会发现（2026-09-05 实测两次）。
    print(f"running start ({'answering' if ok else why}): {start}", file=sys.stderr)
    try:
        proc = subprocess.run(shlex.split(start), cwd=adapter.root, capture_output=True,
                              text=True, timeout=START_TIMEOUT_S,
                              env=command_env(adapter.root))
    except subprocess.TimeoutExpired as exc:
        raise SystemExit(f"`{start}` did not return within {START_TIMEOUT_S}s") from exc
    if proc.returncode != 0:
        raise SystemExit(f"`{start}` exited {proc.returncode}: "
                         f"{proc.stderr.strip() or proc.stdout.strip()}")
    adapter.addresses = discover(adapter.cfg, adapter.root)
    ok, why = adapter.ready()
    if not ok:
        raise SystemExit(f"`{start}` returned 0 but the product is still not answering: {why}")


def skill_root() -> Path:
    """The directory `verify-ticket/` and the other skills are installed under, resolved
    from this file's own location so it is right on every host and every checkout."""
    return Path(__file__).resolve().parents[2]


def retired_triggers(doc: dict, page: str | None = None) -> list[tuple[str, str]]:
    """The retired controls to hide on the design side — for one design page when
    `page` is given. A retired entry that names its `page` is hidden there only: a
    control's role and name are not unique across pages (a retired 查看 on one page, a
    live 查看 on another), and hiding by name alone would blind the judge to the live one."""
    out = []
    for entry in doc.get("retired_ids") or []:
        if not (isinstance(entry, dict) and isinstance(entry.get("trigger"), dict)):
            continue
        scope = entry.get("page")
        if page is not None and scope and scope != page:
            continue
        t = entry["trigger"]
        out.append((str(t.get("role")), str(t.get("name"))))
    return out


def hide_js_for(doc: dict, page: str) -> str | None:
    triggers = retired_triggers(doc, page)
    return hide_retired_js(triggers) if triggers else None


def volatile_triggers(doc: dict, page: str | None = None) -> list[tuple[str, str]]:
    """The display values not compared, for one design page when `page` is given.
    Same scoping as `retired_triggers`: an entry that names its `page` applies there
    only, because a role and name are not unique across pages."""
    out = []
    for entry in doc.get("volatile_values") or []:
        if not (isinstance(entry, dict) and isinstance(entry.get("trigger"), dict)):
            continue
        scope = entry.get("page")
        if page is not None and scope and scope != page:
            continue
        t = entry["trigger"]
        out.append((str(t.get("role")), str(t.get("name"))))
    return out


def volatile_js_for(doc: dict, page: str) -> str | None:
    triggers = volatile_triggers(doc, page)
    return volatile_paint_js(triggers) if triggers else None


def rows_by_id(doc: dict) -> dict[str, dict]:
    return {str(r["id"]): r for r in doc.get("rows") or []}
