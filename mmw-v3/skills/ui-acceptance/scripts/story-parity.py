#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["Pillow>=10", "playwright>=1.58", "psutil>=7", "pyyaml>=6"]
# ///
"""Compare a product story with its design page by `data-ui` element facts.

    uv run story-parity.py --contract efforts/<effort>/screen-contract.yaml --pages <mount,…>

The screen contract names the design package, viewports, pages and scenes. `--pages`
names the `pages.<page>.mount` values this run covers, including `App · ` pages;
`--scenes` narrows that set. `.mmw/target.json`'s `stories` command prints the
origin, and the story URL is
`<origin>/?page=<mount>&scene=<name>&viewport=<WxH>`.

The product side is `[data-story-root]`; the design side is `#dc-root` at the size
the design page renders in the screen-contract viewport. The same reader takes each side's
`data-ui` facts. Pixel difference images are written as evidence and do not decide
the result. Class names, font families, line heights, hover and focus styles are
not compared.

Exit codes
----------
Exit 0 and one line `STORY OK <passed>/<total>` when every pair matches. Exit 1
with one `DIFF` line per differing element fact. Exit 2 when a negative control
fails, the story service does not start, a story page is unreachable or 404, the
requested mount or scene is outside the screen contract, `--pages` is empty, there is no
visible `[data-story-root]`, the screen contract lacks `viewports` or `locale`, the
screen contract still carries a key the oracle no longer executes, the product story
page hosts Claude Design runtime, the design page throws or does not mount, the design
page renders no `data-ui` element, or compare hits an unexpected error.

A `missing` or `extra` line appends the other side's size, parent and quoted text.
A `visible` line appends the first reason that holds: `display:none`,
`visibility:hidden`, `opacity:0`, `size 0`, or `clipped by an ancestor`. Text
values are quoted. Exit 0 and exit 1 also print one `PIXEL` line per compared
scene and viewport, after the verdict. That line does not contain `STORY OK` and
does not change the exit code. Each screenshot is cropped to that side's component
box and only the overlap is compared, so an identical pair is 0%. When the boxes
differ, the line names both sizes.

When the story service exits or stalls before printing origin, its last 15 output
lines are printed and then the refusal. Those lines are not part of the refusal.
A design-page failure names the scene, the design-page file, the URL and the first
error, then refuses. The same four facts are printed on their own lines first, because
the refusal is capped at 256 characters. Console errors with no uncaught exception are
printed and written under `--out`, and the run continues. A design page that renders
no `data-ui` element prints one line with the count 0, the URL and the design
screenshot path, and exits 2.

`--out` holds screenshots, capture evidence and a pixel difference image for every
pair, plus `<scene>-<W>x<H>-elements.json` for each compared pair. `--render-only`
needs no product and writes the design facts to
`--out/values/<mount>/<scene>-<W>x<H>.json`.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import NamedTuple
from urllib.parse import urlencode


def _load(name: str, modname: str):
    here = Path(__file__).resolve().parent / name
    spec = importlib.util.spec_from_file_location(modname, here)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


dr = _load("design_render.py", "design_render")
lease_mod = _load("lease.py", "lease")
tc = _load("target_config.py", "target_config")

pixel_diff = _load("pixel_diff.py", "pixel_diff").pixel_diff
refusal = _load("refusal.py", "refusal").refusal
NEGATIVE_CONTROL_SCENE = "__negative_control__"

STORY_ROOT = "[data-story-root]"
STYLE_KEYS = ("font-size", "font-weight", "color", "background-color",
              "border-radius")
ORIGIN_WAIT_S = 15
_BOOTSTRAP = "MMW_STORY_PARITY_BOOTSTRAPPED"
FONT_CONTROL_JS = """(() => {
  for (const el of document.querySelectorAll('[data-ui]')) {
    el.style.fontSize = (parseFloat(getComputedStyle(el).fontSize) + 7) + 'px';
  }
})()"""
REMOVE_IDS_JS = """(() => {
  for (const el of document.querySelectorAll('[data-ui]')) el.removeAttribute('data-ui');
})()"""
DESIGN_TRACE_JS = """() => {
  if (document.querySelector('.sc-interp')) return 'sc-interp';
  if (document.querySelector('[data-dc-tpl]')) return 'data-dc-tpl';
  if (document.querySelector('[data-dc-script]')) return 'data-dc-script';
  if (document.getElementById('dc-root')) return 'dc-root';
  return null;
}"""
# Same element walk as UI_VALUES_JS. The values record only `visible`; the reason
# stays beside that record so the JSON key set does not change.
HIDDEN_REASON_JS = """(selector) => {
  const root = document.querySelector(selector);
  if (!root) return [];
  const els = [];
  if (root.hasAttribute('data-ui')) els.push(root);
  for (const el of root.querySelectorAll('[data-ui]')) els.push(el);
  const reasonOf = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none') return 'display:none';
    if (cs.visibility === 'hidden') return 'visibility:hidden';
    if (cs.opacity === '0') return 'opacity:0';
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return 'size 0';
    for (let p = el.parentElement; p; p = p.parentElement) {
      const pcs = getComputedStyle(p);
      if (pcs.overflowX === 'visible' && pcs.overflowY === 'visible') continue;
      const pr = p.getBoundingClientRect();
      const ix = Math.min(r.right, pr.right) - Math.max(r.left, pr.left);
      const iy = Math.min(r.bottom, pr.bottom) - Math.max(r.top, pr.top);
      if (ix <= 0 || iy <= 0) return 'clipped by an ancestor';
    }
    return null;
  };
  return els.map(reasonOf);
}"""
# The screenshot is clipped to `selector`. The product selector is the component.
# `#dc-root` is the design viewport, so the component is the first `[data-ui]` in it.
COMPONENT_BOX_JS = """(selector) => {
  const root = document.querySelector(selector);
  if (!root) return null;
  const el = root.hasAttribute('data-ui') ? root
    : (root.querySelector('[data-ui]') || root);
  const r = el.getBoundingClientRect();
  return [r.x, r.y, r.width, r.height];
}"""


class ElementDifference(NamedTuple):
    uid: str
    property: str
    design: str | None = None
    product: str | None = None
    note: str = ""


def _ensure_script_env() -> None:
    """A `CHECK:` of `uv run python story-parity.py` does not read the script's
    dependency block; `uv run --script` does. Re-exec once when the imports are
    missing, so both forms reach Chromium."""
    try:
        import PIL  # noqa: F401
        import playwright.sync_api  # noqa: F401
        import psutil  # noqa: F401
        import yaml  # noqa: F401
    except ImportError:
        if os.environ.get(_BOOTSTRAP) == "1":
            raise SystemExit(
                "story-parity.py is missing Pillow, playwright, psutil or pyyaml "
                "after uv run --script; install those with the script's metadata"
            )
        env = dict(os.environ)
        env[_BOOTSTRAP] = "1"
        os.execvpe("uv", ["uv", "run", "--script", str(Path(__file__).resolve()),
                          *sys.argv[1:]], env)


def parse_origin(text: str) -> str | None:
    """The first origin in `stories` stdout: `origin=…`, a JSON object, or a bare URL."""
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("origin="):
            value = line.split("=", 1)[1].strip()
            return value or None
        if line.startswith("{"):
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and data.get("origin"):
                return str(data["origin"])
        if line.startswith(("http://", "https://")):
            return line
    return None


def product_root() -> Path:
    """Where `.mmw/target.json` lives for this run.

    The criterion is invoked from the product repository (AC1–AC3 `cd` there).
    `repo_root` walks from the working directory to that file, then the git toplevel.
    """
    return tc.repo_root()


def load_stories_config(root: Path) -> dict:
    try:
        cfg = lease_mod.read_target_json(root)
    except lease_mod.TargetJSONError as exc:
        raise SystemExit(refusal(
            str(exc),
            "story-parity.py starts the product story pages with the stories command in that file.",
            "Fix .mmw/target.json so it holds one valid JSON object, then re-run."))
    if cfg is None:
        raise SystemExit(refusal(
            "no .mmw/target.json.",
            "story-parity.py starts the product story pages with the stories command in that file.",
            "Add .mmw/target.json with a stories command, then re-run."))
    if not cfg.get("stories"):
        raise SystemExit(refusal(
            ".mmw/target.json has no `stories` command.",
            "story-parity.py starts the product story page with that command, which prints origin.",
            "Add a stories command to .mmw/target.json, then re-run."))
    return cfg


def story_url(origin: str, mount: str, scene: str, viewport: tuple[int, int]) -> str:
    query = urlencode({
        "page": mount,
        "scene": scene,
        "viewport": f"{viewport[0]}x{viewport[1]}",
    })
    return f"{origin.rstrip('/')}/?{query}"


class Stories:
    """The `stories` command, started for this run alone, stopped when we finish.

    It takes no lease. A story page is the product components rendered
    from scene data, with no backend, no seed and no route behind it, so the one thing
    this service needs is a port, and a port it picks for itself is free of every other
    run on the machine. A lease would instead cost the run one of the machine's product
    slots and hold it for the rest of the ticket.
    """

    def __init__(self, root: Path, cfg: dict):
        self.root = root
        self.cfg = cfg
        self.proc: subprocess.Popen | None = None
        self.origin = ""

    def __enter__(self) -> "Stories":
        command = self.cfg["stories"]
        env = dict(os.environ)
        env["MMW_AUTOMATION"] = "1"
        env["PYTHONUNBUFFERED"] = "1"
        self.proc = subprocess.Popen(
            shlex.split(command), cwd=self.root, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
        collected: list[str] = []
        done = threading.Event()

        def read_stdout():
            assert self.proc is not None and self.proc.stdout is not None
            for line in self.proc.stdout:
                collected.append(line)
                if parse_origin("".join(collected)):
                    break
            done.set()

        reader = threading.Thread(target=read_stdout, daemon=True)
        reader.start()
        done.wait(ORIGIN_WAIT_S)
        origin = parse_origin("".join(collected))
        if origin:
            self.origin = origin
            return self
        code = self.proc.poll()
        detail = "".join(collected).strip().splitlines()
        # The refusal is capped at 256 characters. The log stays outside it, or the
        # real error, which is often not the first line, is the part that is cut.
        for line in detail[-15:]:
            print(line, file=sys.stderr)
        if code is not None:
            raise SystemExit(refusal(
                f"`{command}` exited {code} before printing origin.",
                "The story service must print origin before the oracle can open a page.",
                "Fix the stories command so it prints origin, then re-run."))
        raise SystemExit(refusal(
            f"`{command}` printed no origin within {ORIGIN_WAIT_S}s.",
            "The story service must print origin before the oracle can open a page.",
            "Fix the stories command so it prints origin, then re-run."))

    def __exit__(self, *exc) -> None:
        proc = self.proc
        if proc is None or proc.poll() is not None:
            return
        stop_tree(proc)


def stop_tree(proc: subprocess.Popen, grace_s: float = 5.0) -> None:
    """End the `stories` command and every process under it.

    The server is usually a grandchild (`uv run` → python → pnpm → vite), and a member
    of the chain that dies on SIGTERM without forwarding it leaves the rest reparented
    to init, still holding its port: ten Vite servers were found three days after the
    runs that started them (2026-09-12). The tree is read before anything is signalled,
    because after the first death the survivors can no longer be traced to this run.
    The command stays in this process group, so gate-check's group kill on a timed-out
    `CHECK:` still reaches it.
    """
    import psutil

    try:
        leader = psutil.Process(proc.pid)
        tree = [leader, *leader.children(recursive=True)]
    except psutil.NoSuchProcess:
        tree = []
    for member in tree:
        try:
            member.terminate()
        except psutil.NoSuchProcess:
            pass
    _, alive = psutil.wait_procs(tree, timeout=grace_s)
    for member in alive:
        try:
            member.kill()
        except psutil.NoSuchProcess:
            pass
    psutil.wait_procs(alive, timeout=2)
    proc.poll()


def element_differences(design: list[dict], product: list[dict]
                        ) -> list[ElementDifference]:
    """One structured record per element fact that differs."""
    design, product = _align_repeated_ids(design, product)
    design_by_id = {item["id"]: item for item in design}
    product_by_id = {item["id"]: item for item in product}
    differences = []
    suppressed: set[str] = set()
    for before in design:
        uid = before["id"]
        if uid in suppressed:
            continue
        if uid not in product_by_id:
            differences.append(ElementDifference(
                uid, "missing", note=_other_side_facts(before)))
            continue
        after = product_by_id[uid]
        if not (before["visible"] and after["visible"]):
            if before["visible"] != after["visible"]:
                hidden = before if not before["visible"] else after
                differences.append(ElementDifference(
                    uid, "visible",
                    "yes" if before["visible"] else "no",
                    "yes" if after["visible"] else "no",
                    note=hidden.get("_reason") or ""))
            suppressed.update(_descendant_ids(design, uid))
            suppressed.update(_descendant_ids(product, uid))
            continue
        if before["text"] != after["text"]:
            differences.append(ElementDifference(
                uid, "text", before["text"], after["text"]))
        if any(abs(a - b) > 2 for a, b in zip(before["size"], after["size"])):
            differences.append(ElementDifference(
                uid, "size", f"{before['size'][0]}x{before['size'][1]}",
                f"{after['size'][0]}x{after['size'][1]}"))
        for key in STYLE_KEYS:
            if before["style"][key] != after["style"][key]:
                differences.append(ElementDifference(
                    uid, key, before["style"][key], after["style"][key]))
        if before["ancestor"] != after["ancestor"]:
            differences.append(ElementDifference(
                uid, "parent", before["ancestor"] or "null",
                after["ancestor"] or "null"))
        elif _position_differs(before, after):
            differences.append(ElementDifference(
                uid, "position", _pair(before["offset"]), _pair(after["offset"])))
    for after in product:
        uid = after["id"]
        if uid not in suppressed and uid not in design_by_id:
            differences.append(ElementDifference(
                uid, "extra", note=_other_side_facts(after)))
    return differences


def _quote(value: str) -> str:
    """Quote a text value so a space or ` product=` stays inside the value."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _other_side_facts(item: dict) -> str:
    """Size, parent and quoted text of the side that does have the element."""
    width, height = item["size"]
    parent = item["ancestor"] or "null"
    return f"size={width}x{height} parent={parent} text={_quote(item['text'])}"


def _with_reasons(values: list[dict], reasons: list) -> list[dict]:
    """Copies that carry the hidden reason beside the recorded facts.

    The reason is not a field of the values JSON. Alignment copies each dict, so
    the reason stays with its element when a lone id gains `#1`.
    """
    annotated = []
    for index, item in enumerate(values):
        copied = dict(item)
        copied["_reason"] = reasons[index] if index < len(reasons) else None
        annotated.append(copied)
    return annotated


def format_element_difference(mount: str, scene: str, viewport: str,
                              difference: ElementDifference) -> str:
    """The one public line for a structured element difference."""
    prefix = f"DIFF {mount} {scene} {viewport} {difference.uid} {difference.property}"
    if difference.design is None and difference.product is None:
        line = prefix
    else:
        design = difference.design
        product = difference.product
        if difference.property == "text":
            design = _quote(design)
            product = _quote(product)
        line = f"{prefix} design={design} product={product}"
    if difference.note:
        return f"{line} {difference.note}"
    return line


def _align_repeated_ids(design: list[dict], product: list[dict]
                        ) -> tuple[list[dict], list[dict]]:
    """Give a lone occurrence `#1` when the other side repeats that raw id."""
    suffix = re.compile(r"^(.*)#([1-9][0-9]*)$")
    numbered: dict[str, set[int]] = {}
    for item in [*design, *product]:
        match = suffix.match(item["id"])
        if match:
            numbered.setdefault(match.group(1), set()).add(int(match.group(2)))
    repeated = {base for base, occurrences in numbered.items()
                if 1 in occurrences and any(n > 1 for n in occurrences)}

    def aligned(values: list[dict]) -> list[dict]:
        out = []
        for original in values:
            item = dict(original)
            if item["id"] in repeated:
                item["id"] += "#1"
            for key in ("ancestor", "previous"):
                if item.get(key) in repeated:
                    item[key] += "#1"
            out.append(item)
        return out

    return aligned(design), aligned(product)


def negative_control_gate(design_differences: list[ElementDifference],
                          missing_differences: list[ElementDifference]
                          ) -> tuple[int, list[str]]:
    """The two controls prove this run can see a changed style and absent ids."""
    if not design_differences:
        return 2, [refusal(
            "NEGATIVE CONTROL FAILED: changing every design font-size reported no difference.",
            "The oracle could not prove that it can observe element differences.",
            "Confirm the design page and product story carry corresponding data-ui ids, then re-run.")]
    if not any(diff.property == "missing" for diff in missing_differences):
        return 2, [refusal(
            "NEGATIVE CONTROL FAILED: removing every product data-ui id reported no missing element.",
            "The design page carries no data-ui id this oracle can compare.",
            "Give the design page's elements data-ui ids in Claude Design and pull again, "
            "put the same ids on the product story's elements, then re-run.")]
    return 0, []


def _descendant_ids(values: list[dict], ancestor: str) -> set[str]:
    by_id = {item["id"]: item for item in values}
    descendants = set()
    for item in values:
        current = item.get("ancestor")
        while current is not None:
            if current == ancestor:
                descendants.add(item["id"])
                break
            parent = by_id.get(current)
            current = parent.get("ancestor") if parent else None
    return descendants


def _pair(value: list[int] | None) -> str:
    return "null" if value is None else f"{value[0]},{value[1]}"


def _position_differs(design: dict, product: dict) -> bool:
    """Whether an element itself moved, excluding movement inherited from the
    preceding element's changed size."""
    before = design["offset"]
    after = product["offset"]
    if before is None or after is None:
        return False
    for axis in (0, 1):
        if abs(before[axis] - after[axis]) <= 2:
            continue
        if (design["previous"] is None
                or design["previous"] != product["previous"]):
            return True
        before_gap = design["gap"]
        after_gap = product["gap"]
        if (before_gap is not None and after_gap is not None
                and abs(before_gap[axis] - after_gap[axis]) > 2):
            return True
    return False


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="story-parity.py",
        usage="story-parity.py --contract FILE --pages ID[,ID] [options]",
        description="Compare a product story page with its design page by data-ui id.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--contract", required=True, metavar="FILE",
                   help="the screen contract; it names the design package, the viewports "
                        "and every scene's page and mount")
    p.add_argument("--pages", required=True, metavar="IDS",
                   help="comma-separated pages.mount values; every "
                        "scene declaring one of them is compared")
    p.add_argument("--scenes", metavar="NAMES", default=None,
                   help="a subset of the scenes --pages derives")
    p.add_argument("--out", metavar="DIR", default=None,
                   help="where screenshots, element facts and pixel evidence are written")
    p.add_argument("--cdn", metavar="DIR", default=None,
                   help="cache for the scripts support.js loads, when the design package "
                        "carries no vendor/ copy")
    p.add_argument("--render-only", action="store_true",
                   help="render the design side of the selected scenes into --out "
                        "(screenshots and values/<mount>/<scene>-<WxH>.json) and stop; "
                        "no product is needed")
    return p


def refuse_pages(mounts: list[str], doc: dict, catalogue: dict) -> str | None:
    """Why `--pages` cannot run, or None. Exit 2 for a mount the screen contract does not declare."""
    declared = {s.mount for s in dr.scenes_of(doc, catalogue).values()}
    missing = [m for m in mounts if m not in declared]
    if missing:
        return refusal(
            f"--pages names mount(s) the screen contract does not declare: {', '.join(missing)}.",
            "Every mount must be a pages.mount value in the screen contract.",
            "Pass a declared --pages mount, then re-run.")
    return None


def refuse_story_inputs(doc: dict, contract: str) -> str | None:
    """Why this screen contract cannot be judged, or None. Exit 2, refusal.py three parts."""
    if doc.get("viewports") in (None, [], ""):
        return refusal(
            f"{contract} has no top-level `viewports`.",
            "Both browser windows are one screen-contract viewport; the oracle does not invent a size.",
            "Add `viewports` as the write-screen-contract skill's references/screen-contract-format.md says, then re-run.")
    locale = doc.get("locale")
    if not isinstance(locale, str) or not locale.strip():
        return refusal(
            f"{contract} has no top-level `locale`.",
            "story-parity.py reads locale from the screen contract and does not fall back to zh-CN.",
            "Add `locale` as the write-screen-contract skill's references/screen-contract-format.md says, then re-run.")
    return None


def refuse_design_trace(scene: str, named: str) -> str:
    """The product story page still hosts Claude Design runtime."""
    return refusal(
        f"product story page for scene {scene} carries {named}.",
        "A story page hosting Claude Design runtime is serving the design page.",
        f"Remove {named} from the product story page, then re-run.")


def refuse_design_page(scene: str, page: str, url: str, error: str) -> str:
    """The design page threw or did not mount. The product was not compared.

    The four facts are printed in full first. `refusal` keeps the next step and
    trims the tail of what happened, so a long URL would otherwise take the error with it.
    """
    print(f"scene {scene}", file=sys.stderr)
    print(f"file {page}", file=sys.stderr)
    print(f"url {url}", file=sys.stderr)
    print(f"error {error}", file=sys.stderr)
    return refusal(
        f"{error} scene {scene} file {page} url {url}",
        "The design page failed, so the product was not compared.",
        "Run verify-ticket.py <n> --sub-issue contract <file>.")


def write_element_facts(media: Path, scene: str, tag: str,
                        design: list, product: list) -> None:
    """Both sides' element facts, beside the screenshots for this pair."""
    path = media / f"{scene}-{tag}-elements.json"
    path.write_text(
        json.dumps({"design": design, "product": product},
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")


def console_error_is_uncaught(text: str) -> bool:
    """A thrown Error the paused clock reports as a console message.

    Measured 2026-10-08: a `setTimeout` throw under Playwright's paused clock
    arrives as a console error whose text is `Error: …` plus stack frames, and
    `pageerror` does not fire. A one-line `console.error` string does not.
    """
    lines = text.splitlines()
    if not lines:
        return False
    if lines[0].startswith("Uncaught"):
        return True
    return len(lines) > 1 and any(line.lstrip().startswith("at ") for line in lines[1:])


def hidden_reasons(page, selector: str) -> list:
    """One hidden reason per `[data-ui]` element, in the values reader's order."""
    return page.evaluate(HIDDEN_REASON_JS, selector)


def component_box(page, selector: str, shot_box: tuple[int, int, int, int]
                  ) -> tuple[int, int, int, int]:
    """The component's box inside the screenshot, in CSS pixels."""
    raw = page.evaluate(COMPONENT_BOX_JS, selector)
    vx, vy, vw, vh = raw
    sx, sy, _, _ = shot_box
    return (int(round(vx - sx)), int(round(vy - sy)),
            int(round(vw)), int(round(vh)))


def _crop_png(png: Path, box: tuple[int, int, int, int]) -> Path:
    from PIL import Image

    x, y, w, h = box
    with Image.open(png) as image:
        x = max(0, x)
        y = max(0, y)
        right = min(image.width, x + max(0, w))
        lower = min(image.height, y + max(0, h))
        cropped = image.crop((x, y, right, lower))
        handle = tempfile.NamedTemporaryFile(
            prefix="mmw-crop-", suffix=".png", delete=False)
        handle.close()
        cropped.save(handle.name)
        return Path(handle.name)


def _png_size(path: Path) -> tuple[int, int]:
    from PIL import Image

    with Image.open(path) as image:
        return image.width, image.height


def _diff_facts(path: Path) -> tuple[str, str]:
    """The integer percent of overlap pixels that differ, and their bounding box.

    0 means no pixel differs. A difference smaller than half a percent is still
    1, so a real difference is never reported as 0.
    """
    from PIL import Image

    with Image.open(path) as image:
        rgb = image.convert("RGB")
        box = rgb.getbbox()
        if box is None:
            return "0", ""
        raw = rgb.tobytes()
        differ = sum(1 for i in range(0, len(raw), 3)
                     if raw[i] or raw[i + 1] or raw[i + 2])
        total = rgb.width * rgb.height
        percent = round(100 * differ / total) if total else 0
        if differ and percent == 0:
            percent = 1
        x0, y0, x1, y1 = box
        return str(percent), f"{x0},{y0},{x1 - x0},{y1 - y0}"


def pixel_report(scene: str, design_png: Path, product_png: Path,
                 design_box: tuple[int, int, int, int],
                 product_box: tuple[int, int, int, int],
                 diff_png: Path) -> str:
    """Crop each side to its component box, compare the overlap, return the PIXEL line.

    Measured 2026-10-08: padding the smaller screenshot with black made an identical
    pair look about half different. The crop is here. `pixel_diff` still pads when
    a caller hands it two unequal images directly.
    """
    crops: list[Path] = []
    try:
        design_crop = _crop_png(design_png, design_box)
        crops.append(design_crop)
        product_crop = _crop_png(product_png, product_box)
        crops.append(product_crop)
        design_size = _png_size(design_crop)
        product_size = _png_size(product_crop)
        overlap = (min(design_size[0], product_size[0]),
                   min(design_size[1], product_size[1]))
        left = _crop_png(design_crop, (0, 0, overlap[0], overlap[1]))
        crops.append(left)
        right = _crop_png(product_crop, (0, 0, overlap[0], overlap[1]))
        crops.append(right)
        pixel_diff(left, right, diff_png)
        percent, bbox = _diff_facts(diff_png)
    finally:
        for path in crops:
            path.unlink(missing_ok=True)
    if design_size == product_size:
        size = f"{design_size[0]}x{design_size[1]}"
    else:
        size = (f"{design_size[0]}x{design_size[1]} "
                f"{product_size[0]}x{product_size[1]}")
    return f"PIXEL {scene} {size} {percent}% bbox={bbox}"


def write_console_errors(media: Path, scene: str, tag: str, errors: list[str]) -> None:
    """Console errors from the design page. They do not change the verdict."""
    path = media / f"{scene}-{tag}-console.txt"
    path.write_text("\n".join(errors) + "\n", encoding="utf-8")
    for line in errors:
        print(line, file=sys.stderr)


def run(args) -> int:
    contract_path = Path(args.contract).resolve()
    doc = dr.load_yaml(contract_path)
    why = refuse_story_inputs(doc, args.contract)
    if why:
        print(why, file=sys.stderr)
        return 2
    doc = dr.load_contract(contract_path, doc)
    look = doc["baselines"]["look"]
    if args.render_only:
        root = Path.cwd().resolve()
        if not (root / look).exists():
            root = tc.repo_root()
    else:
        root = product_root()
    baseline = (root / look).resolve()
    catalogue = dr.load_catalogue(baseline)
    viewports = dr.parse_viewports(doc["viewports"])
    locale = doc["locale"].strip()
    mounts = [m.strip() for m in args.pages.split(",") if m.strip()]
    if not mounts:
        print(refusal(
            "--pages is empty.",
            "The oracle needs at least one pages.mount value.",
            "Pass --pages with a declared mount, then re-run."), file=sys.stderr)
        return 2
    why = refuse_pages(mounts, doc, catalogue)
    if why:
        print(why, file=sys.stderr)
        return 2
    explicit = [s.strip() for s in args.scenes.split(",") if s.strip()] if args.scenes else None
    plan = dr.scene_plan(doc, catalogue, mounts, explicit)
    out = Path(args.out).resolve() if args.out else Path("./story-shots").resolve()
    media = out / "media"
    media.mkdir(parents=True, exist_ok=True)
    cache = Path(args.cdn).expanduser() if args.cdn else dr.DEFAULT_CACHE
    cfg = None if args.render_only else load_stories_config(root)

    pages = {dr.wrapper_path(s.name): dr.wrapper_page(dr.component_of(s.page), s.props,
                                                      lang=locale)
             for s in plan}
    server, port = dr.serve_baseline(baseline, pages)
    origin = f"http://127.0.0.1:{port}"
    route_baseline = dr.baseline_router(origin, baseline, cache)
    try:
        if args.render_only:
            return render_only(plan, viewports, out, media, origin, route_baseline,
                               locale)
        assert cfg is not None
        with Stories(root, cfg) as stories:
            return compare(plan=plan, viewports=viewports, media=media,
                           design_origin=origin,
                           route_baseline=route_baseline,
                           story_origin=stories.origin,
                           locale=locale)
    finally:
        server.mmw_stop = True
        server.shutdown()
        server.server_close()


def render_only(plan, viewports, out, media, origin, route_baseline, locale) -> int:
    """Design side only: screenshots under `media`, values under `out/values`.

    No product, and `.mmw/target.json` is not read. Each scene at each viewport is
    one render; the values file is taken from that same capture. `run()` creates
    `media`.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(device_scale_factor=1, reduced_motion="reduce",
                                  locale=locale)
        ctx.route("**/*", route_baseline)
        page = ctx.new_page()
        try:
            for scene in plan:
                for viewport in scene.viewports or viewports:
                    dr.resize(page, viewport)
                    dr.navigate(page, f"{origin}{dr.wrapper_path(scene.name)}")
                    dr.wait_for_mount(page, "#dc-root")
                    tag = f"{viewport[0]}x{viewport[1]}"
                    shot = dr.capture(
                        page, media / f"{scene.name}-{tag}-baseline.png",
                        selector="#dc-root")
                    dr.write_values(
                        dr.values_path(out, scene.mount, scene.name, viewport),
                        shot.values)
                    print(f"rendered {scene.name} {tag} -> {shot.png}")
        finally:
            browser.close()
    return 0


def compare(*, plan, viewports, media, design_origin, route_baseline,
            story_origin, locale) -> int:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    pair_count = 0
    element_lines: list[str] = []
    pixel_lines: list[str] = []
    controls: tuple[list[ElementDifference], list[ElementDifference]] | None = None
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        story_ctx = browser.new_context(device_scale_factor=1, reduced_motion="reduce",
                                        locale=locale)
        design_ctx = browser.new_context(device_scale_factor=1, reduced_motion="reduce",
                                         locale=locale)
        design_ctx.route("**/*", route_baseline)
        story_page = story_ctx.new_page()
        design_page = design_ctx.new_page()
        # Playwright's navigation timeout is 30s. A test sets this so a hung
        # design request fails in this run without waiting that long.
        nav_ms = os.environ.get("MMW_NAV_TIMEOUT_MS")
        if nav_ms:
            for watched in (story_page, design_page):
                watched.set_default_navigation_timeout(int(nav_ms))
                watched.set_default_timeout(int(nav_ms))
        page_errors: list[str] = []
        console_errors: list[str] = []

        def on_pageerror(error) -> None:
            page_errors.append(str(error))

        def on_console(message) -> None:
            if message.type != "error":
                return
            text = message.text
            if console_error_is_uncaught(text):
                page_errors.append(text.splitlines()[0])
            else:
                console_errors.append(text)

        design_page.on("pageerror", on_pageerror)
        design_page.on("console", on_console)
        current_scene = None
        try:
            def capture_story(scene, viewport, png, extra_js=None,
                              *, negative_control=False):
                dr.resize(story_page, viewport)
                url = story_url(story_origin, scene.mount, scene.name, viewport)
                try:
                    response = story_page.goto(url, wait_until="domcontentloaded")
                except PlaywrightError as exc:
                    raise SystemExit(refusal(
                        f"story page {url} could not be opened: {exc}",
                        "The oracle could not reach the stories service.",
                        "Fix the stories command so it stays up and prints origin, then re-run."
                    )) from exc
                status = response.status if response is not None else 0
                if status == 404:
                    raise SystemExit(refusal(
                        f"story page 404: {url}",
                        "The stories service has no page for this mount and scene.",
                        "Serve that scene or drop it from --scenes, then re-run."))
                if status >= 400 or status == 0:
                    raise SystemExit(refusal(
                        f"story page {url} answered {status}.",
                        "The stories service did not return a usable page.",
                        "Fix the stories command so that URL returns 200, then re-run."))
                try:
                    story_page.locator(STORY_ROOT).first.wait_for(
                        state="visible", timeout=8000)
                except PlaywrightError as exc:
                    raise SystemExit(refusal(
                        f"no visible {STORY_ROOT} at {url}: {exc}",
                        "The product story page must put [data-story-root] on the component root.",
                        "Put [data-story-root] on the product component root, then re-run."
                    )) from exc
                if not negative_control:
                    named = story_page.evaluate(DESIGN_TRACE_JS)
                    if named:
                        raise SystemExit(refuse_design_trace(scene.name, named))
                box = dr.visible_box(story_page, STORY_ROOT, viewport)
                return dr.capture(story_page, png, selector=STORY_ROOT, clip=box,
                                  extra_js=extra_js)

            def design_page_url(scene) -> str:
                return f"{design_origin}{dr.wrapper_path(scene.name)}"

            def fail_design_page(scene, error: str) -> None:
                raise SystemExit(refuse_design_page(
                    scene.name, scene.page, design_page_url(scene), error))

            def capture_design(scene, viewport, png, extra_js=None):
                page_errors.clear()
                console_errors.clear()
                dr.resize(design_page, viewport)
                dr.navigate(design_page, design_page_url(scene))
                if page_errors:
                    fail_design_page(scene, page_errors[0])
                try:
                    dr.wait_for_mount(design_page, "#dc-root")
                    shot = dr.capture(
                        design_page, png, selector="#dc-root", extra_js=extra_js)
                except SystemExit as exc:
                    if page_errors:
                        fail_design_page(scene, page_errors[0])
                    message = exc.code if isinstance(exc.code, str) else str(exc.code)
                    fail_design_page(scene, message)
                if page_errors:
                    fail_design_page(scene, page_errors[0])
                return shot

            for scene in plan:
                current_scene = scene
                for viewport in scene.viewports or viewports:
                    tag = f"{viewport[0]}x{viewport[1]}"
                    impl = capture_story(
                        scene, viewport, media / f"{scene.name}-{tag}-impl.png")
                    base = capture_design(
                        scene, viewport,
                        media / f"{scene.name}-{tag}-baseline.png")
                    seen_console = list(console_errors)
                    write_element_facts(
                        media, scene.name, tag, base.values, impl.values)
                    if seen_console:
                        write_console_errors(media, scene.name, tag, seen_console)
                    if not base.values:
                        print(f"read 0 data-ui elements at {design_page_url(scene)} "
                              f"screenshot {base.png}")
                        print(f"story evidence: {media}", file=sys.stderr)
                        return 2
                    pair_count += 1
                    design_reasons = hidden_reasons(design_page, "#dc-root")
                    product_reasons = hidden_reasons(story_page, STORY_ROOT)
                    pixel_lines.append(pixel_report(
                        scene.name, base.png, impl.png,
                        component_box(design_page, "#dc-root", base.box),
                        component_box(story_page, STORY_ROOT, impl.box),
                        media / f"{scene.name}-{tag}-diff.png"))
                    element_lines.extend(
                        format_element_difference(scene.mount, scene.name, tag, difference)
                        for difference in element_differences(
                            _with_reasons(base.values, design_reasons),
                            _with_reasons(impl.values, product_reasons)))
                    if controls is None:
                        font_design = capture_design(
                            scene, viewport,
                            media / f"{NEGATIVE_CONTROL_SCENE}-{tag}-font-design.png",
                            FONT_CONTROL_JS)
                        no_ids = capture_story(
                            scene, viewport,
                            media / f"{NEGATIVE_CONTROL_SCENE}-{tag}-no-ids-product.png",
                            REMOVE_IDS_JS, negative_control=True)
                        controls = (
                            element_differences(font_design.values, impl.values),
                            element_differences(base.values, no_ids.values),
                        )
        except Exception as exc:
            # SystemExit is the refusal path and must keep propagating. Anything else
            # used to become exit 1, which is reserved for a real DIFF line.
            text = str(exc)
            print(text, file=sys.stderr)
            where = (f" while comparing scene {current_scene.name}"
                     if current_scene is not None else "")
            first = text.splitlines()[0] if text else type(exc).__name__
            print(refusal(
                f"{type(exc).__name__}{where}: {first}",
                "An unexpected failure is not an element difference.",
                "Fix the cause named above, then re-run."), file=sys.stderr)
            return 2
        finally:
            browser.close()

    assert controls is not None
    control_code, control_lines = negative_control_gate(*controls)
    if control_code == 2:
        code, lines = control_code, control_lines
    elif element_lines:
        code, lines = 1, [*element_lines, *pixel_lines]
    else:
        code, lines = 0, [f"STORY OK {pair_count}/{pair_count}", *pixel_lines]
    for line in lines:
        print(line)
    if code:
        print(f"story evidence: {media}", file=sys.stderr)
    return code


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _ensure_script_env()
    try:
        return run(args)
    except SystemExit as exc:
        if isinstance(exc.code, int):
            return exc.code
        print(exc.code, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
