"""Four-column boundary tests for the App · 任务板 cross-component rows."""

from __future__ import annotations

import json
import re
import unittest
from copy import deepcopy
from pathlib import Path

from playwright.sync_api import sync_playwright

import interact
from story_helper import recorded_requests, story_page


ROOT = Path(__file__).resolve().parents[3]
ZONE = "Asia/Hong_Kong"


def pin_clock(page, iso: str) -> None:
    # 23:39Z is 07:39 in Hong Kong, and 23:12Z is 28 minutes before the example now.
    session = page.context.new_cdp_session(page)
    session.send("Emulation.setTimezoneOverride", {"timezoneId": ZONE})
    page.clock.set_fixed_time(iso)


def open_board(browser, scene: str, responses=None):
    now = board_scene("morning")["now"]
    return story_page(
        browser, "board", scene, responses,
        before_goto=lambda page: pin_clock(page, now),
    )


def settings_scene(name: str = "mine") -> dict:
    source = (ROOT / "prototypes" / "task-board" / "example-data" / "settings.js").read_text(encoding="utf-8")
    match = re.fullmatch(r"window\.SETTINGS_SCENES = (\{.*\});?\n?", source)
    if not match:
        raise AssertionError("cannot read settings scenes")
    return json.loads(match.group(1))[name]


def board_scene(name: str) -> dict:
    source = (ROOT / "prototypes" / "task-board" / "example-data" / f"board-{name}.js").read_text(encoding="utf-8")
    match = re.fullmatch(
        r'\(window\.BOARD_SCENES = window\.BOARD_SCENES \|\| \{\}\)\["[^"]+"\] = (\{.*\});?\n?',
        source,
    )
    if not match:
        raise AssertionError(f"cannot read board scene {name}")
    return json.loads(match.group(1))


class BoardRowsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_board_jump_needs_you(self):
        with open_board(self.browser, "App · 任务板.morning") as page:
            interact.click(page, "顶栏.needs-you")
            detail = page.locator('[data-ui="详情.root"]')
            detail.wait_for(timeout=1000)
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(detail.locator('[data-ui="详情.origin.number"]').inner_text(), "#138")
            self.assertEqual(detail.locator('[data-ui="详情.title"]').inner_text(), "离线时唤醒去向")
            selected = page.locator('[data-ui="画布.ticket-card"].on')
            self.assertEqual(selected.locator('[data-ui="画布.ticket-card.num"]').inner_text(), "#138")

    def test_board_open_settings(self):
        settings = settings_scene()["payload"]
        responses = {"GET /api/settings": {"status": 200, "body": settings}}
        with open_board(self.browser, "App · 任务板.morning", responses) as page:
            interact.click(page, "顶栏.settings")
            sheet = page.locator('[data-ui="本机配置.root"]')
            sheet.wait_for(timeout=1000)
            self.assertEqual(recorded_requests(page), [
                {"method": "GET", "path": "/api/settings", "fields": None},
            ])
            self.assertEqual(sheet.locator('[data-ui="本机配置.runner.select"]').input_value(), "orca")
            self.assertEqual(sheet.locator('[data-ui="本机配置.sheet.title"]').inner_text(),
                             "这台机器上，每个 agent 跑在哪")

        responses = {"GET /api/settings": {
            "status": 503, "body": {"message": "missing config marker"},
        }}
        with open_board(self.browser, "App · 任务板.morning", responses) as page:
            before = page.locator('[data-ui="任务板.root"]').inner_text()
            interact.click(page, "顶栏.settings")
            page.wait_for_timeout(20)
            self.assertEqual(recorded_requests(page), [
                {"method": "GET", "path": "/api/settings", "fields": None},
            ])
            self.assertEqual(page.locator('[data-ui="本机配置.root"]').count(), 0)
            self.assertEqual(page.locator('[data-ui="任务板.root"]').inner_text(), before)
            self.assertNotIn("missing config marker", page.locator("body").inner_text())

    def test_board_refresh_all(self):
        refreshed = deepcopy(board_scene("morning")["payload"])
        refreshed["tasks"][0]["title"] = "刷新后的任务"
        selected = next(ticket for spec in refreshed["tasks"][0]["specs"]
                        for ticket in spec["tickets"] if ticket["n"] == 133)
        selected["title"] = "刷新后的详情"
        responses = {"POST /api/board/refresh": {"status": 200, "body": refreshed}}
        with open_board(self.browser, "App · 任务板.morning", responses) as page:
            interact.click(page, "顶栏.refresh")
            page.locator('[data-ui="详情.title"]', has_text="刷新后的详情").wait_for(timeout=1000)
            self.assertEqual(recorded_requests(page), [
                {"method": "POST", "path": "/api/board/refresh", "fields": None},
            ])
            self.assertEqual(page.locator('[data-ui="任务列表.task.title"]').first.inner_text(),
                             "刷新后的任务")
            self.assertEqual(page.locator('[data-ui="画布.ticket-card"].on '
                                          '[data-ui="画布.ticket-card.title"]').inner_text(),
                             "刷新后的详情")
            self.assertEqual(page.locator('[data-ui="详情.title"]').inner_text(), "刷新后的详情")

        failed = board_scene("bad-data")["payload"]
        responses = {"POST /api/board/refresh": {"status": 200, "body": failed}}
        with open_board(self.browser, "App · 任务板.morning", responses) as page:
            columns = {
                key: page.locator(f'[data-ui="{key}.root"]').inner_text()
                for key in ("任务列表", "画布", "详情")
            }
            interact.click(page, "顶栏.refresh")
            page.locator('[data-ui="顶栏.read-state"]', has_text="读 GitHub 失败").wait_for(timeout=1000)
            self.assertEqual(recorded_requests(page), [
                {"method": "POST", "path": "/api/board/refresh", "fields": None},
            ])
            self.assertEqual(page.locator('[data-ui="顶栏.read-state"]').inner_text(),
                             "读 GitHub 失败 · 下面是 07:12 的数据（28 分钟前）")
            for key, before in columns.items():
                self.assertEqual(page.locator(f'[data-ui="{key}.root"]').inner_text(), before)

        responses = {"POST /api/board/refresh": {
            "status": 403, "body": {"message": "forbidden marker"},
        }}
        with open_board(self.browser, "App · 任务板.morning", responses) as page:
            before = page.locator('[data-ui="任务板.root"]').inner_text()
            interact.click(page, "顶栏.refresh")
            page.wait_for_timeout(20)
            self.assertEqual(recorded_requests(page), [
                {"method": "POST", "path": "/api/board/refresh", "fields": None},
            ])
            self.assertEqual(page.locator('[data-ui="任务板.root"]').inner_text(), before)
            self.assertNotIn("forbidden marker", page.locator("body").inner_text())

    def test_board_pick_task(self):
        with open_board(self.browser, "App · 任务板.morning") as page:
            interact.click(page, "任务列表.task#2")
            page.locator('[data-ui="任务列表.task"].on '
                         '[data-ui="任务列表.task.meta"]', has_text="#77 · map").wait_for(timeout=1000)
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(page.locator('[data-ui="画布.container-card.num"]').first.inner_text(),
                             "#77 · map")
            self.assertEqual(page.locator('[data-ui="画布.root"] .card.on').count(), 0)
            self.assertEqual(page.locator('[data-ui="详情.root"]').count(), 0)

    def test_board_open_ticket(self):
        with open_board(self.browser, "App · 任务板.morning") as page:
            interact.click(page, "画布.ticket-card.open")
            page.locator('[data-ui="详情.origin.number"]', has_text="#132").wait_for(timeout=1000)
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(page.locator('[data-ui="详情.title"]').inner_text(), "中继进程骨架")
            self.assertEqual(page.locator('[data-ui="详情.status.phase"]').inner_text(), "landed")

    def test_board_open_map(self):
        with open_board(self.browser, "App · 任务板.morning") as page:
            interact.click(page, "任务列表.task#2")
            interact.click(page, "画布.container-card.open")
            page.locator('[data-ui="详情.origin.number"]', has_text="#77 · map").wait_for(timeout=1000)
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(page.locator('[data-ui="详情.title"]').inner_text(), "交接包比对")
            self.assertEqual(page.locator('[data-ui="详情.spec-row"]').count(), 1)

    def test_board_open_spec(self):
        with open_board(self.browser, "App · 任务板.morning") as page:
            interact.click(page, "画布.zoom.fit")
            interact.click(page, "画布.container-card.open#2")
            page.locator('[data-ui="详情.origin.number"]', has_text="#123").wait_for(timeout=1000)
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(page.locator('[data-ui="详情.title"]').inner_text(), "事件评论格式")
            self.assertGreater(page.locator('[data-ui="详情.ticket-row"]').count(), 0)

    def test_board_open_decision(self):
        with open_board(self.browser, "App · 任务板.morning") as page:
            interact.click(page, "画布.decision-card.open")
            page.locator('[data-ui="详情.origin.number"]', has_text="#99").wait_for(timeout=1000)
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(page.locator('[data-ui="详情.title"]').inner_text(), "事件格式怎么定")
            self.assertEqual(page.locator('[data-ui="详情.head.eyebrow"]').inner_text(),
                             "DECISION TICKET · GRILLING")

    def test_board_goto_origin(self):
        with open_board(self.browser, "App · 任务板.morning") as page:
            interact.click(page, "详情.origin.link")
            selected = page.locator('[data-ui="画布.container-card"].on')
            selected.wait_for(timeout=1000)
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(selected.locator('[data-ui="画布.container-card.num"]').inner_text(), "#131")
            self.assertEqual(page.locator('[data-ui="详情.title"]').inner_text(), "唤醒回路")

    def test_board_goto_blocker(self):
        with open_board(self.browser, "App · 任务板.morning") as page:
            interact.click(page, "详情.blocker")
            selected = page.locator('[data-ui="画布.ticket-card"].on')
            selected.locator('[data-ui="画布.ticket-card.num"]', has_text="#132").wait_for(timeout=1000)
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(page.locator('[data-ui="详情.title"]').inner_text(), "中继进程骨架")

    def test_board_goto_blocked(self):
        with open_board(self.browser, "App · 任务板.morning") as page:
            interact.click(page, "详情.blocks")
            selected = page.locator('[data-ui="画布.ticket-card"].on')
            selected.locator('[data-ui="画布.ticket-card.num"]', has_text="#135").wait_for(timeout=1000)
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(page.locator('[data-ui="详情.title"]').inner_text(), "投递回执")

    def test_board_goto_spec_row(self):
        with open_board(self.browser, "App · 任务板.morning") as page:
            interact.click(page, "任务列表.task#2")
            interact.click(page, "画布.container-card.open")
            interact.click(page, "详情.spec-row")
            selected = page.locator('[data-ui="画布.container-card"].on')
            selected.locator('[data-ui="画布.container-card.num"]', has_text="#80").wait_for(timeout=1000)
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(page.locator('[data-ui="详情.title"]').inner_text(), "交接包落盘")

    def test_board_goto_decision_row(self):
        with open_board(self.browser, "App · 任务板.morning") as page:
            interact.click(page, "画布.zoom.fit")
            interact.click(page, "画布.container-card.open")
            interact.click(page, "详情.decision-row")
            selected = page.locator('[data-ui="画布.decision-card"].on')
            selected.locator('[data-ui="画布.decision-card.num"]', has_text="#99").wait_for(timeout=1000)
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(page.locator('[data-ui="详情.title"]').inner_text(), "事件格式怎么定")

    def test_board_goto_ticket_row(self):
        with open_board(self.browser, "App · 任务板.morning") as page:
            interact.click(page, "画布.zoom.fit")
            interact.click(page, "画布.container-card.open#2")
            interact.click(page, "详情.ticket-row")
            selected = page.locator('[data-ui="画布.ticket-card"].on')
            selected.locator('[data-ui="画布.ticket-card.num"]', has_text="#124").wait_for(timeout=1000)
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(page.locator('[data-ui="详情.title"]').inner_text(), "事件表与校验")

    def test_board_close_detail(self):
        with open_board(self.browser, "App · 任务板.morning") as page:
            interact.click(page, "详情.head.close")
            page.locator('[data-ui="详情.root"]').wait_for(state="detached", timeout=1000)
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(page.locator('[data-ui="画布.root"] .card.on').count(), 0)
            self.assertEqual(round(page.locator('[data-ui="画布.root"]').bounding_box()["width"]), 1204)

    def test_board_close_settings(self):
        settings = settings_scene()["payload"]
        responses = {"GET /api/settings": {"status": 200, "body": settings}}
        with open_board(self.browser, "App · 任务板.morning", responses) as page:
            interact.click(page, "顶栏.settings")
            page.locator('[data-ui="本机配置.root"]').wait_for(timeout=1000)
            interact.click(page, "本机配置.sheet.close")
            page.locator('[data-ui="本机配置.root"]').wait_for(state="detached", timeout=1000)
            self.assertEqual(recorded_requests(page), [
                {"method": "GET", "path": "/api/settings", "fields": None},
            ])
            self.assertEqual(page.locator('[data-ui="顶栏.settings"]').get_attribute("class"), "iconbtn bare")
            self.assertEqual(page.locator('[data-ui="顶栏.read-state"]').inner_text(), "只读 · 07:39 读取")

    def test_board_cancel_settings(self):
        settings = settings_scene()["payload"]
        responses = {"GET /api/settings": {"status": 200, "body": settings}}
        with open_board(self.browser, "App · 任务板.morning", responses) as page:
            interact.click(page, "顶栏.settings")
            page.locator('[data-ui="本机配置.root"]').wait_for(timeout=1000)
            interact.click(page, "本机配置.sheet.cancel")
            page.locator('[data-ui="本机配置.root"]').wait_for(state="detached", timeout=1000)
            self.assertEqual(recorded_requests(page), [
                {"method": "GET", "path": "/api/settings", "fields": None},
            ])
            self.assertEqual(page.locator('[data-ui="顶栏.settings"]').get_attribute("class"), "iconbtn bare")
            self.assertEqual(page.locator('[data-ui="顶栏.read-state"]').inner_text(), "只读 · 07:39 读取")


if __name__ == "__main__":
    unittest.main()
