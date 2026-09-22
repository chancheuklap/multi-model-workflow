from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright

import interact
from story_helper import recorded_requests, story_page


ROOT = Path(__file__).resolve().parents[3]
EXAMPLE = ROOT / "prototypes" / "task-board" / "example-data"
HANDOFF = ROOT / "prototypes" / "task-board" / "claude-design"


def board_scene(name: str) -> dict:
    source = (EXAMPLE / f"board-{name}.js").read_text(encoding="utf-8")
    match = re.fullmatch(
        r'\(window\.BOARD_SCENES = window\.BOARD_SCENES \|\| \{\}\)\["[^"]+"\] = (\{.*\});?\n?',
        source,
    )
    if not match:
        raise AssertionError(f"cannot read board scene {name}")
    return json.loads(match.group(1))


def topbar_scene(name: str) -> dict:
    source = (HANDOFF / "data" / "topbar-scenes.js").read_text(encoding="utf-8")
    match = re.search(r"window\.TOPBAR_SCENES = (\{.*\});\s*$", source, re.S)
    if not match:
        raise AssertionError("cannot read topbar scenes")
    return json.loads(match.group(1))[name]


def freeze_clock(page, iso: str) -> None:
    page.add_init_script(
        "(() => {\n"
        f"  const fixed = Date.parse({json.dumps(iso)});\n"
        "  const RealDate = Date;\n"
        "  class FixedDate extends RealDate {\n"
        "    constructor(...args) {\n"
        "      if (args.length === 0) super(fixed);\n"
        "      else super(...args);\n"
        "    }\n"
        "  }\n"
        "  FixedDate.now = () => fixed;\n"
        "  FixedDate.parse = RealDate.parse;\n"
        "  FixedDate.UTC = RealDate.UTC;\n"
        "  window.Date = FixedDate;\n"
        "})();"
    )


def transitions(page):
    return page.evaluate("window.storyTransitions()")


class TopbarRowsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_topbar_refresh(self):
        morning = board_scene("morning")
        shown = topbar_scene("morning")
        responses = {"POST /api/board/refresh": {"status": 200, "body": morning["payload"]}}
        with story_page(self.browser, "topbar", "Component · 顶栏.empty", responses,
                        before_goto=lambda page: freeze_clock(page, morning["now"])) as page:
            interact.click(page, "顶栏.refresh")
            page.wait_for_function("window.storyTransitions().length === 1", timeout=1000)
            self.assertEqual(recorded_requests(page), [
                {"method": "POST", "path": "/api/board/refresh", "fields": None},
            ])
            self.assertEqual(page.locator('[data-ui="顶栏.needs-you.count"]').inner_text(),
                             str(shown["orangeN"]))
            self.assertEqual(page.locator('[data-ui="顶栏.running.count"]').inner_text(),
                             str(shown["greenN"]))
            self.assertEqual(page.locator('[data-ui="顶栏.running.sub"]').inner_text(),
                             f"waiting for a slot {shown['waiting']}")
            self.assertEqual(page.locator('[data-ui="顶栏.queued.count"]').inner_text(),
                             str(shown["hollowN"]))
            self.assertEqual(page.locator('[data-ui="顶栏.done.count"]').inner_text(),
                             str(shown["inkN"]))
            self.assertEqual(page.locator('[data-ui="顶栏.read-state"]').inner_text(),
                             shown["readText"])
            self.assertEqual(transitions(page)[0]["scene"], "Component · 顶栏.morning")

        failed = board_scene("bad-data")
        failed_shown = topbar_scene("bad-data")
        responses = {"POST /api/board/refresh": {"status": 200, "body": failed["payload"]}}
        with story_page(self.browser, "topbar", "Component · 顶栏.bad-data", responses,
                        before_goto=lambda page: freeze_clock(page, failed["now"])) as page:
            before = page.locator('[data-ui="顶栏.root"]').inner_text()
            interact.click(page, "顶栏.refresh")
            page.wait_for_function("window.storyTransitions().length === 1", timeout=1000)
            self.assertEqual(recorded_requests(page), [
                {"method": "POST", "path": "/api/board/refresh", "fields": None},
            ])
            self.assertEqual(page.locator('[data-ui="顶栏.root"]').inner_text(), before)
            self.assertEqual(page.locator('[data-ui="顶栏.read-state"]').inner_text(),
                             failed_shown["readText"])
            self.assertEqual(transitions(page)[0]["scene"], "Component · 顶栏.bad-data")

        responses = {"POST /api/board/refresh": {
            "status": 403, "body": {"message": "forbidden marker"},
        }}
        with story_page(self.browser, "topbar", "Component · 顶栏.morning", responses) as page:
            before = page.locator('[data-ui="顶栏.root"]').inner_text()
            interact.click(page, "顶栏.refresh")
            page.wait_for_timeout(20)
            self.assertEqual(recorded_requests(page), [
                {"method": "POST", "path": "/api/board/refresh", "fields": None},
            ])
            self.assertEqual(page.locator('[data-ui="顶栏.root"]').inner_text(), before)
            self.assertEqual(transitions(page), [])
            self.assertNotIn("forbidden marker", page.locator("body").inner_text())

    def test_topbar_needs_you_jump(self):
        shown = topbar_scene("morning")
        with story_page(self.browser, "topbar", "Component · 顶栏.morning") as page:
            self.assertEqual(page.locator('[data-ui="顶栏.needs-you.count"]').inner_text(),
                             str(shown["orangeN"]))
            interact.click(page, "顶栏.needs-you")
            page.wait_for_function("window.storyTransitions().length === 1", timeout=1000)
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(transitions(page), [{
                "scene": "Component · 详情.ticket-returned",
                "data": None,
            }])

    def test_topbar_open_settings(self):
        settings = {
            "version": 17,
            "runner": "orca",
            "rows": {"worker": {"host": "codex", "model": "gpt-5", "effort": "high"}},
            "hosts": ["codex"],
            "runners": ["orca"],
            "sources": ["cli"],
            "scan": {
                "source": "cli", "scanned_at": "2026-09-21T08:00:00Z", "scanning": False,
                "hosts": [{"host": "codex", "state": "ready", "offered": []}],
            },
        }
        responses = {"GET /api/settings": {"status": 200, "body": settings}}
        with story_page(self.browser, "topbar", "Component · 顶栏.morning", responses) as page:
            interact.click(page, "顶栏.settings")
            page.wait_for_function("window.storyTransitions().length === 1", timeout=1000)
            self.assertEqual(recorded_requests(page), [
                {"method": "GET", "path": "/api/settings", "fields": None},
            ])
            self.assertEqual(transitions(page), [{
                "scene": "Component · 本机配置.mine",
                "data": settings,
            }])

        responses = {"GET /api/settings": {
            "status": 503, "body": {"message": "missing config marker"},
        }}
        with story_page(self.browser, "topbar", "Component · 顶栏.morning", responses) as page:
            before = page.locator('[data-ui="顶栏.root"]').inner_text()
            interact.click(page, "顶栏.settings")
            page.wait_for_timeout(20)
            self.assertEqual(recorded_requests(page), [
                {"method": "GET", "path": "/api/settings", "fields": None},
            ])
            self.assertEqual(page.locator('[data-ui="顶栏.root"]').inner_text(), before)
            self.assertEqual(transitions(page), [])
            self.assertNotIn("missing config marker", page.locator("body").inner_text())


if __name__ == "__main__":
    unittest.main()
