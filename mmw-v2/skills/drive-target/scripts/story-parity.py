#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy>=2", "Pillow>=10", "playwright>=1.58", "pyyaml>=6"]
# ///
"""Compare a product story page with the design page it was built from, scene by scene.

    uv run story-parity.py --contract docs/specs/<effort>/screen-contract.yaml --pages <mount,…>

The screen contract names the handoff package (`baselines.look`), the sizes
(`viewports`), and which design page each scene is on (`pages`, `scenes`). `--pages`
names the `pages.<page>.mount` values this run covers — the non-`App · ` design pages.
`--scenes` narrows that to a subset. Addresses come from `.mmw/target.json`'s `stories`
command, which prints `origin`; the story URL is
`<origin>/?page=<mount>&scene=<name>&viewport=<WxH>`.

The product side is the story page, captured at `[data-story-root]`. The design side is
the existing baseline server and wrapper page, with `#dc-root` pinned to the box that
root measured (`frame_box`). The two judges are the normalised accessibility tree and
pixels after sub-cell alignment. Class names are not compared. No paused clock is
installed on the story page; the design side uses `navigate`'s 200 ms of virtual time.

Exit codes
----------
Exit 0 and one line `STORY OK <passed>/<total> pixel<=<worst>%` when every scene matches
at every viewport. Exit 1 with one `DIFF` line per failing pair, each followed by the
tree lines that differ. Exit 2 when the negative control fails, when the stories
command does not come up, when a story page is 404, or when `--pages` names a mount
the contract does not declare.

`--out` holds the screenshot, the tree and the differing-pixel picture for every scene
and viewport. `--render-only` renders the design side of the selected scenes into
`--out` and stops, needing no product.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shlex
import subprocess
import sys
import threading
from pathlib import Path
from urllib.parse import urlencode


def _load(name: str, modname: str):
    here = Path(__file__).resolve().parent / name
    spec = importlib.util.spec_from_file_location(modname, here)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


vp = _load("visual-parity.py", "visual_parity")
sd = vp.sd

# Reused from visual-parity.py: do not copy.
diff_images = vp.diff_images
around = vp.around
change_lines = vp.change_lines
pixel_diff = vp.pixel_diff
failures = vp.failures
Comparison = vp.Comparison
NEGATIVE_CONTROL_HEAD = vp.NEGATIVE_CONTROL_HEAD
NEGATIVE_CONTROL_SCENE = vp.NEGATIVE_CONTROL_SCENE
DEFAULT_MAX_PCT = vp.DEFAULT_MAX_PCT
render_only = vp.render_only

STORY_ROOT = "[data-story-root]"
ORIGIN_WAIT_S = 15
_BOOTSTRAP = "MMW_STORY_PARITY_BOOTSTRAPPED"
# Tree, pixels, and a size mismatch. Not the class set, not console errors.
JUDGED = {"aria", "pixel", "size"}


def _ensure_script_env() -> None:
    """A `CHECK:` of `uv run python story-parity.py` does not read the script's
    dependency block; `uv run --script` does. Re-exec once when the imports are
    missing, so both forms reach Chromium."""
    try:
        import numpy  # noqa: F401
        import PIL  # noqa: F401
        import playwright.sync_api  # noqa: F401
        import yaml  # noqa: F401
    except ImportError:
        if os.environ.get(_BOOTSTRAP) == "1":
            raise SystemExit(
                "story-parity.py is missing numpy, Pillow, playwright or pyyaml "
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

    The criterion is invoked from the product repository (AC1–AC3 `cd` there). If that
    directory holds the file, it is the product. Otherwise the git toplevel — the same
    anchor `sd.repo_root()` uses.
    """
    cwd = Path.cwd().resolve()
    if (cwd / ".mmw" / "target.json").exists():
        return cwd
    return sd.repo_root()


def load_stories_config(root: Path) -> dict:
    path = root / ".mmw" / "target.json"
    if not path.exists():
        raise SystemExit(
            f"no {path}: the repository has not said how its story pages are served"
        )
    cfg = json.loads(path.read_text(encoding="utf-8"))
    if not cfg.get("stories"):
        raise SystemExit(
            f"{path} has no `stories` command; story-parity.py starts the product "
            f"story page with that command, which prints origin"
        )
    return cfg


def story_url(origin: str, mount: str, scene: str, viewport: tuple[int, int]) -> str:
    query = urlencode({
        "page": mount,
        "scene": scene,
        "viewport": f"{viewport[0]}x{viewport[1]}",
    })
    return f"{origin.rstrip('/')}/?{query}"


class Stories:
    """The `stories` command, started under this run's lease, stopped when we finish."""

    def __init__(self, root: Path, cfg: dict):
        self.root = root
        self.cfg = cfg
        self.proc: subprocess.Popen | None = None
        self.origin = ""

    def __enter__(self) -> "Stories":
        command = self.cfg["stories"]
        env = sd.command_env(self.root)
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
            raise SystemExit(
                f"`{command}` exited {code} before printing origin: {first}"
            )
        raise SystemExit(
            f"`{command}` printed no origin within {ORIGIN_WAIT_S}s: {first}"
        )

    def __exit__(self, *exc) -> None:
        proc = self.proc
        if proc is None or proc.poll() is not None:
            return
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)


def negative_control(scene, vp, pages, capture_impl, capture_baseline, media) -> Comparison:
    """The baseline server answers this scene's own address with the scene plus an
    error banner in the served bytes; the story page is captured again. If the two
    compare equal, the story capture went through the baseline server."""
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


def story_gate(control: Comparison, comparisons: list, max_pct: float,
               console_limit: int = 0) -> tuple[int, list[str]]:
    """Exit code and the lines to print. The negative control is judged first.

    Scene failures are the tree and the pixels (and a size mismatch). Class-set and
    console reasons from the shared `failures()` are dropped: this judge does not
    compare those. The control still uses every reason `failures()` returns, so a
    collapsed capture is caught even when only a class or a console error differs.
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
        reasons = [r for r in failures(c, max_pct, console_limit) if r.kind in JUDGED]
        if c.pixel["size_equal"]:
            worst = max(worst, c.pixel["pct"])
        if reasons:
            failed += 1
            unaligned = c.pixel.get("pct_unaligned", c.pixel["pct"])
            line = (f"DIFF {c.scene} {c.viewport} {c.pixel['pct']}% "
                    f"(unaligned {unaligned}%) — {'; '.join(r.en for r in reasons)}")
            if any(r.kind == "pixel" for r in reasons):
                names = around(c.pixel, c.impl_elements)
                if names:
                    line += " around: " + ", ".join(names)
            lines.append(line)
            lines.extend(change_lines(c.aria["diff"]))
    if failed:
        return 1, lines
    return 0, [f"STORY OK {len(comparisons)}/{len(comparisons)} pixel<={worst}%"]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="story-parity.py",
        usage="story-parity.py --contract FILE --pages ID[,ID] [options]",
        description="Compare a product story page with the design page it was built from, "
                    "scene by scene, by accessibility tree and pixels.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--contract", required=True, metavar="FILE",
                   help="the screen contract; it names the handoff package, the viewports "
                        "and every scene's page and mount")
    p.add_argument("--pages", required=True, metavar="IDS",
                   help="comma-separated pages.mount values (non-App design pages); every "
                        "scene declaring one of them is compared")
    p.add_argument("--scenes", metavar="NAMES", default=None,
                   help="a subset of the scenes --pages derives")
    p.add_argument("--max-pct", type=float, default=DEFAULT_MAX_PCT, metavar="PCT",
                   help=f"largest share of differing cells a scene may have, after both "
                        f"screenshots are shrunk by {vp.PIXEL_SCALE} "
                        f"(default {DEFAULT_MAX_PCT})")
    p.add_argument("--out", metavar="DIR", default=None,
                   help="where the screenshots and trees are written")
    p.add_argument("--cdn", metavar="DIR", default=None,
                   help="cache for the scripts support.js loads, when the handoff package "
                        "carries no vendor/ copy")
    p.add_argument("--render-only", action="store_true",
                   help="render the design side of the selected scenes into --out and "
                        "stop; no product is needed")
    return p


def refuse_pages(mounts: list[str], doc: dict, catalogue: dict) -> str | None:
    """Why `--pages` cannot run, or None. Exit 2 for a mount the contract does not declare."""
    declared = {s.mount for s in sd.scenes_of(doc, catalogue).values()}
    missing = [m for m in mounts if m not in declared]
    if missing:
        return (f"--pages names mount(s) the contract does not declare: "
                f"{', '.join(missing)}")
    return None


def run(args) -> int:
    contract_path = Path(args.contract).resolve()
    doc = sd.load_contract(contract_path)
    look = doc["baselines"]["look"]
    if args.render_only:
        root = Path.cwd().resolve()
        if not (root / look).exists():
            root = sd.repo_root()
    else:
        root = product_root()
    baseline = (root / look).resolve()
    catalogue = sd.load_catalogue(baseline)
    viewports = sd.parse_viewports(doc["viewports"])
    mounts = [m.strip() for m in args.pages.split(",") if m.strip()]
    if not mounts:
        print("--pages is empty", file=sys.stderr)
        return 2
    why = refuse_pages(mounts, doc, catalogue)
    if why:
        print(why, file=sys.stderr)
        return 2
    explicit = [s.strip() for s in args.scenes.split(",") if s.strip()] if args.scenes else None
    plan = sd.scene_plan(doc, catalogue, mounts, explicit)
    out = Path(args.out).resolve() if args.out else Path("./story-shots").resolve()
    media = out / "media"
    media.mkdir(parents=True, exist_ok=True)
    cache = Path(args.cdn).expanduser() if args.cdn else sd.DEFAULT_CACHE
    cfg = None if args.render_only else load_stories_config(root)

    pages = {sd.wrapper_path(s.name): sd.wrapper_page(sd.component_of(s.page), s.props)
             for s in plan}
    server, port = sd.serve_baseline(baseline, pages)
    origin = f"http://127.0.0.1:{port}"
    route_baseline = sd.baseline_router(origin, baseline, cache)
    hide_js = {s.name: sd.hide_js_for(doc, s.page) for s in plan}
    volatile = {s.name: sd.volatile_triggers(doc, s.page) for s in plan}

    try:
        if args.render_only:
            return render_only(plan, viewports, media, origin, route_baseline, hide_js)
        assert cfg is not None
        with Stories(root, cfg) as stories:
            return compare(plan=plan, viewports=viewports, media=media,
                           design_origin=origin, pages=pages,
                           route_baseline=route_baseline, hide_js=hide_js,
                           volatile=volatile, story_origin=stories.origin,
                           args=args)
    finally:
        server.shutdown()
        server.server_close()


def compare(*, plan, viewports, media, design_origin, pages, route_baseline,
            hide_js, volatile, story_origin, args) -> int:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    comparisons: list = []
    control = None
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        story_ctx = browser.new_context(device_scale_factor=1, reduced_motion="reduce",
                                        locale="zh-CN")
        design_ctx = browser.new_context(device_scale_factor=1, reduced_motion="reduce",
                                         locale="zh-CN")
        design_ctx.route("**/*", route_baseline)
        story_page = story_ctx.new_page()
        design_page = design_ctx.new_page()
        try:
            def capture_story(scene, viewport, png):
                sd.resize(story_page, viewport)
                url = story_url(story_origin, scene.mount, scene.name, viewport)
                try:
                    response = story_page.goto(url, wait_until="domcontentloaded")
                except PlaywrightError as exc:
                    raise SystemExit(
                        f"story page {url} could not be opened: {exc}"
                    ) from exc
                status = response.status if response is not None else 0
                if status == 404:
                    raise SystemExit(f"story page 404: {url}")
                if status >= 400 or status == 0:
                    raise SystemExit(f"story page {url} answered {status}")
                try:
                    story_page.locator(STORY_ROOT).first.wait_for(
                        state="visible", timeout=8000)
                except PlaywrightError as exc:
                    raise SystemExit(
                        f"no visible {STORY_ROOT} at {url}: {exc}"
                    ) from exc
                box = sd.visible_box(story_page, STORY_ROOT, viewport)
                paint = (sd.volatile_paint_js(volatile[scene.name])
                         if volatile[scene.name] else None)
                return sd.capture(story_page, png, selector=STORY_ROOT, clip=box,
                                  extra_js=paint)

            def capture_design(scene, viewport, box, png):
                w, h = box[2], box[3]
                sd.resize(design_page, viewport)
                sd.navigate(design_page, f"{design_origin}{sd.wrapper_path(scene.name)}")
                sd.wait_for_mount(design_page, "#dc-root")
                paint = (sd.volatile_paint_js(volatile[scene.name])
                         if volatile[scene.name] else None)
                return sd.capture(
                    design_page, png, selector="#dc-root", clip=(0, 0, w, h),
                    extra_css=sd.frame_box((w, h)),
                    extra_js=vp._join_js(hide_js[scene.name], paint))

            for scene in plan:
                for viewport in viewports:
                    tag = f"{viewport[0]}x{viewport[1]}"
                    impl = capture_story(
                        scene, viewport, media / f"{scene.name}-{tag}-impl.png")
                    base = capture_design(
                        scene, viewport, impl.box,
                        media / f"{scene.name}-{tag}-baseline.png")
                    comparisons.append(Comparison(
                        scene.name, tag,
                        pixel_diff(base.png, impl.png,
                                   media / f"{scene.name}-{tag}-diff.png"),
                        sd.aria_diff(base.aria, impl.aria,
                                     media / f"{scene.name}-{tag}.aria.diff",
                                     volatile=volatile[scene.name] or None),
                        [], [], impl.elements))
                    if control is None:
                        control = negative_control(
                            scene, viewport, pages, capture_story, capture_design, media)
        finally:
            browser.close()

    code, lines = story_gate(control, comparisons, args.max_pct)
    for line in lines:
        print(line)
    if code:
        print(f"screenshots and trees: {media}", file=sys.stderr)
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
