#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["Pillow>=10", "playwright>=1.58", "psutil>=7", "pyyaml>=6"]
# ///
"""Compare a product story with its design page by `data-ui` element facts.

    uv run story-parity.py --contract docs/specs/<effort>/screen-contract.yaml --pages <mount,…>

The screen contract names the design package, viewports, pages and scenes. `--pages`
names the `pages.<page>.mount` values this run covers, including `App · ` pages;
`--scenes` narrows that set. `.mmw/target.json`'s `stories` command prints the
origin, and the story URL is
`<origin>/?page=<mount>&scene=<name>&viewport=<WxH>`.

The product side is `[data-story-root]`; the design side is `#dc-root` at the size
the design page renders in the contract viewport. The same reader takes each side's
`data-ui` facts. Pixel difference images are written as evidence and do not decide
the result. Class names, font families, line heights, hover and focus styles are
not compared.

Exit codes
----------
Exit 0 and one line `STORY OK <passed>/<total>` when every pair matches. Exit 1
with one `DIFF` line per differing element fact. Exit 2 when a negative control
fails, the story service does not start, a story page is unreachable or 404, the
requested mount or scene is outside the contract, `--pages` is empty, there is no
visible `[data-story-root]`, the contract lacks `viewports` or `locale`, the
contract still carries a key the judge no longer executes, or the product story
page hosts Claude Design runtime.

`--out` holds screenshots, capture evidence and a pixel difference image for every
pair. `--render-only` needs no product and writes the design facts to
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


class ElementDifference(NamedTuple):
    uid: str
    property: str
    design: str | None = None
    product: str | None = None


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
    path = root / ".mmw" / "target.json"
    if not path.exists():
        raise SystemExit(refusal(
            "no .mmw/target.json.",
            "story-parity.py starts the product story pages with the stories command in that file.",
            "Add .mmw/target.json with a stories command, then rerun."))
    cfg = json.loads(path.read_text(encoding="utf-8"))
    if not cfg.get("stories"):
        raise SystemExit(refusal(
            ".mmw/target.json has no `stories` command.",
            "story-parity.py starts the product story page with that command, which prints origin.",
            "Add a stories command to .mmw/target.json, then rerun."))
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
    run on the machine. A lease would instead cost the run one of the product's
    `instance.max` slots — the count of how many copies of a product whose ports cannot
    move may run at once — and hold it for the rest of the ticket, which is how
    agentflow spent a night with two interface tickets in acceptance and six free slots.
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
        first = detail[0] if detail else "(no output)"
        if code is not None:
            raise SystemExit(refusal(
                f"`{command}` exited {code} before printing origin: {first}",
                "The story service must print origin before the judge can open a page.",
                "Fix the stories command so it prints origin, then rerun."))
        raise SystemExit(refusal(
            f"`{command}` printed no origin within {ORIGIN_WAIT_S}s: {first}",
            "The story service must print origin before the judge can open a page.",
            "Fix the stories command so it prints origin, then rerun."))

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
            differences.append(ElementDifference(uid, "missing"))
            continue
        after = product_by_id[uid]
        if not (before["visible"] and after["visible"]):
            if before["visible"] != after["visible"]:
                differences.append(ElementDifference(
                    uid, "visible",
                    "yes" if before["visible"] else "no",
                    "yes" if after["visible"] else "no"))
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
            differences.append(ElementDifference(uid, "extra"))
    return differences


def format_element_difference(mount: str, scene: str, viewport: str,
                              difference: ElementDifference) -> str:
    """The one public line for a structured element difference."""
    prefix = f"DIFF {mount} {scene} {viewport} {difference.uid} {difference.property}"
    if difference.design is None and difference.product is None:
        return prefix
    return f"{prefix} design={difference.design} product={difference.product}"


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
            "The judge could not prove that it can observe element differences.",
            "Confirm the design page and product story carry corresponding data-ui ids, then rerun.")]
    if not any(diff.property == "missing" for diff in missing_differences):
        return 2, [refusal(
            "NEGATIVE CONTROL FAILED: removing every product data-ui id reported no missing element.",
            "The design page carries no data-ui id this judge can compare.",
            "Give the design page's elements data-ui ids in Claude Design and pull again, "
            "put the same ids on the product story's elements, then rerun.")]
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
    """Why `--pages` cannot run, or None. Exit 2 for a mount the contract does not declare."""
    declared = {s.mount for s in dr.scenes_of(doc, catalogue).values()}
    missing = [m for m in mounts if m not in declared]
    if missing:
        return refusal(
            f"--pages names mount(s) the contract does not declare: {', '.join(missing)}.",
            "Every mount must be a pages.mount value in the screen contract.",
            "Pass a declared --pages mount, then rerun.")
    return None


def refuse_story_inputs(doc: dict, contract: str) -> str | None:
    """Why this contract cannot be judged, or None. Exit 2, refusal.py three parts."""
    if doc.get("viewports") in (None, [], ""):
        return refusal(
            f"{contract} has no top-level `viewports`.",
            "Both browser windows are one contract viewport; the judge does not invent a size.",
            "Add `viewports` as references/story-parity.md says, then rerun.")
    locale = doc.get("locale")
    if not isinstance(locale, str) or not locale.strip():
        return refusal(
            f"{contract} has no top-level `locale`.",
            "story-parity.py reads locale from the contract and does not fall back to zh-CN.",
            "Add `locale` as references/story-parity.md says, then rerun.")
    if doc.get("volatile_values"):
        return refusal(
            f"{contract} has a non-empty `volatile_values`.",
            "The screen-contract format has no such key, and the judge would ignore it.",
            "Delete `volatile_values` from the contract, then rerun.")
    for entry in doc.get("retired_ids") or []:
        if isinstance(entry, dict) and entry.get("trigger"):
            return refusal(
                f"{contract} has a `retired_ids` entry with `trigger`.",
                "A `retired_ids` entry holds only `id` and `note`, and the judge would ignore `trigger`.",
                "Delete `trigger` from that entry, then rerun.")
    return None


def refuse_design_trace(scene: str, named: str) -> str:
    """The product story page still hosts Claude Design runtime."""
    return refusal(
        f"product story page for scene {scene} carries {named}.",
        "A story page hosting Claude Design runtime is serving the design page.",
        f"Remove {named} from the product story page, then rerun.")


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
            "The judge needs at least one pages.mount value.",
            "Pass --pages with a declared mount, then rerun."), file=sys.stderr)
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
                        "The judge could not reach the stories service.",
                        "Fix the stories command so it stays up and prints origin, then rerun."
                    )) from exc
                status = response.status if response is not None else 0
                if status == 404:
                    raise SystemExit(refusal(
                        f"story page 404: {url}",
                        "The stories service has no page for this mount and scene.",
                        "Serve that scene or drop it from --scenes, then rerun."))
                if status >= 400 or status == 0:
                    raise SystemExit(refusal(
                        f"story page {url} answered {status}.",
                        "The stories service did not return a usable page.",
                        "Fix the stories command so that URL returns 200, then rerun."))
                try:
                    story_page.locator(STORY_ROOT).first.wait_for(
                        state="visible", timeout=8000)
                except PlaywrightError as exc:
                    raise SystemExit(refusal(
                        f"no visible {STORY_ROOT} at {url}: {exc}",
                        "The product story page must put [data-story-root] on the component root.",
                        "Put [data-story-root] on the product component root, then rerun."
                    )) from exc
                if not negative_control:
                    named = story_page.evaluate(DESIGN_TRACE_JS)
                    if named:
                        raise SystemExit(refuse_design_trace(scene.name, named))
                box = dr.visible_box(story_page, STORY_ROOT, viewport)
                return dr.capture(story_page, png, selector=STORY_ROOT, clip=box,
                                  extra_js=extra_js)

            def capture_design(scene, viewport, png, extra_js=None):
                dr.resize(design_page, viewport)
                dr.navigate(design_page, f"{design_origin}{dr.wrapper_path(scene.name)}")
                dr.wait_for_mount(design_page, "#dc-root")
                return dr.capture(
                    design_page, png, selector="#dc-root", extra_js=extra_js)

            for scene in plan:
                for viewport in scene.viewports or viewports:
                    tag = f"{viewport[0]}x{viewport[1]}"
                    impl = capture_story(
                        scene, viewport, media / f"{scene.name}-{tag}-impl.png")
                    base = capture_design(
                        scene, viewport,
                        media / f"{scene.name}-{tag}-baseline.png")
                    pair_count += 1
                    pixel_diff(base.png, impl.png,
                               media / f"{scene.name}-{tag}-diff.png")
                    element_lines.extend(
                        format_element_difference(scene.mount, scene.name, tag, difference)
                        for difference in element_differences(base.values, impl.values))
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
        finally:
            browser.close()

    assert controls is not None
    control_code, control_lines = negative_control_gate(*controls)
    if control_code == 2:
        code, lines = control_code, control_lines
    elif element_lines:
        code, lines = 1, element_lines
    else:
        code, lines = 0, [f"STORY OK {pair_count}/{pair_count}"]
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
