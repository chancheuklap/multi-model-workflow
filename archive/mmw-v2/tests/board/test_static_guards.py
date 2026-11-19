from __future__ import annotations

import contextlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from urllib.parse import urlencode

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[3]
PAGE_MODULES = ROOT / "mmw-v2" / "board" / "page"
CONTRACT = ROOT / "docs" / "specs" / "task-board" / "screen-contract.yaml"
HANDOFF = ROOT / "prototypes" / "task-board" / "claude-design"
STORY_SERVER = ROOT / ".mmw" / "stories" / "serve.py"
VIEWPORTS = {
    "board": (1440, 900),
    "topbar": (1440, 52),
    "tasks": (236, 848),
    "canvas": (864, 848),
    "detail": (340, 848),
    "settings": (1440, 900),
}


def load_design_render():
    path = ROOT / "mmw-v2" / "skills" / "ui-acceptance" / "scripts" / "design_render.py"
    spec = importlib.util.spec_from_file_location("static_guard_design_render", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


DESIGN_RENDER = load_design_render()


def contract_scenes() -> list[tuple[str, str, str]]:
    pages: dict[str, str] = {}
    scenes: list[tuple[str, str]] = []
    section = ""
    current = ""
    for line in CONTRACT.read_text(encoding="utf-8").splitlines():
        if line in ("pages:", "scenes:"):
            section = line[:-1]
            current = ""
            continue
        if section and line and not line.startswith(" "):
            section = ""
            current = ""
            continue
        heading = re.fullmatch(r"  ([^ ].*):", line)
        if heading:
            current = heading.group(1)
            if section == "scenes":
                scenes.append((current, ""))
            continue
        if section == "pages" and current:
            mount = re.fullmatch(r"    mount: (\S+)", line)
            if mount:
                pages[current] = mount.group(1)
        elif section == "scenes" and current:
            page = re.fullmatch(r"    page: (.+)", line)
            if page:
                scenes[-1] = (current, page.group(1))
    missing = [page for _, page in scenes if page not in pages]
    if missing:
        raise AssertionError(f"contract scenes name pages without mounts: {missing}")
    return [(name, page, pages[page]) for name, page in scenes]


@contextlib.contextmanager
def story_service():
    process = subprocess.Popen(
        ["python3", "-u", str(STORY_SERVER)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        line = process.stdout.readline().strip()
        if not line.startswith("origin="):
            raise RuntimeError(process.stderr.read() or f"story server said {line!r}")
        yield line.removeprefix("origin=")
    finally:
        process.terminate()
        process.wait(timeout=5)
        process.stdout.close()
        process.stderr.close()


def story_url(origin: str, mount: str, scene: str) -> str:
    width, height = VIEWPORTS[mount]
    query = urlencode({"page": mount, "scene": scene, "viewport": f"{width}x{height}"})
    return f"{origin}/?{query}"


def raw_counts(values) -> Counter:
    return Counter(re.sub(r"#\d+$", "", value["id"]) for value in values)


@contextlib.contextmanager
def rendered_sides(browser):
    catalogue = DESIGN_RENDER.load_catalogue(HANDOFF)
    wrappers = {
        DESIGN_RENDER.wrapper_path(name): DESIGN_RENDER.wrapper_page(
            DESIGN_RENDER.component_of(item["page"]), item.get("props") or {}
        )
        for name, item in catalogue.items()
    }
    baseline_server, baseline_port = DESIGN_RENDER.serve_baseline(HANDOFF, wrappers)
    baseline_origin = f"http://127.0.0.1:{baseline_port}"
    with tempfile.TemporaryDirectory() as cache, story_service() as product_origin:
        product_page = browser.new_page(locale="zh-CN")
        design_page = browser.new_page(locale="zh-CN")
        design_page.route(
            "**/*",
            DESIGN_RENDER.baseline_router(baseline_origin, HANDOFF, Path(cache)),
        )
        try:
            yield product_page, design_page, product_origin, baseline_origin
        finally:
            product_page.close()
            design_page.close()
            baseline_server.shutdown()
            baseline_server.server_close()


def render_scene(product_page, design_page, product_origin, design_origin, name, mount):
    width, height = VIEWPORTS[mount]
    product_page.set_viewport_size({"width": width, "height": height})
    product_page.goto(story_url(product_origin, mount, name), wait_until="networkidle")
    design_page.set_viewport_size({"width": width, "height": height})
    DESIGN_RENDER.navigate(design_page, f"{design_origin}{DESIGN_RENDER.wrapper_path(name)}")
    DESIGN_RENDER.wait_for_mount(design_page, "#dc-root")
    product_values = DESIGN_RENDER.read_ui_values(product_page, "[data-story-root]")
    design_values = DESIGN_RENDER.read_ui_values(design_page, "#dc-root")
    return product_values, design_values


class StaticGuardsTest(unittest.TestCase):
    def test_no_product_module_reads_scene_data(self):
        forbidden = ("fromScene", "scenes.json", "BOARD_SCENES", "SETTINGS_SCENES", "prototypes/")
        found = []
        for path in sorted(PAGE_MODULES.rglob("*.mjs")):
            source = path.read_text(encoding="utf-8")
            for marker in forbidden:
                if marker in source:
                    found.append(f"{path.relative_to(ROOT)}: {marker}")
        self.assertEqual(found, [], "product modules read story-only inputs:\n" + "\n".join(found))

    def test_one_story_root_per_render(self):
        scenes = contract_scenes()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            with rendered_sides(browser) as sides:
                for name, _page, mount in scenes:
                    with self.subTest(scene=name, mount=mount):
                        product_values, design_values = render_scene(*sides, name, mount)
                        visible_roots = sides[0].locator("[data-story-root]").evaluate_all(
                            "roots => roots.filter(root => {"
                            "const style = getComputedStyle(root); const box = root.getBoundingClientRect();"
                            "return style.display !== 'none' && style.visibility !== 'hidden' "
                            "&& style.opacity !== '0' && box.width > 0 && box.height > 0; }).length"
                        )
                        self.assertEqual(visible_roots, 1)
                        if mount == "board":
                            product_root_ids = Counter({
                                key: count for key, count in raw_counts(product_values).items()
                                if key.endswith(".root")
                            })
                            design_root_ids = Counter({
                                key: count for key, count in raw_counts(design_values).items()
                                if key.endswith(".root")
                            })
                            self.assertTrue(all(count == 1 for count in design_root_ids.values()))
                            self.assertEqual(product_root_ids, design_root_ids)
            browser.close()

    def test_data_ui_ids_repeat_only_in_lists(self):
        scenes = contract_scenes()
        offenders = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            with rendered_sides(browser) as sides:
                for name, _page, mount in scenes:
                    product_values, design_values = render_scene(*sides, name, mount)
                    product_counts = raw_counts(product_values)
                    design_counts = raw_counts(design_values)
                    for data_ui, count in product_counts.items():
                        if count > 1 and design_counts[data_ui] <= 1:
                            offenders.append(
                                f"{name}: {data_ui} repeats {count} times in product, "
                                f"{design_counts[data_ui]} times in design"
                            )
            browser.close()
        self.assertEqual(offenders, [], "data-ui ids repeat outside design lists:\n" + "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()
