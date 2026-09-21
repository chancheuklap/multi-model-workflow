from __future__ import annotations

import unittest

from playwright.sync_api import sync_playwright

import interact
from story_helper import recorded_requests, story_page


def transitions(page):
    return page.evaluate("window.storyTransitions()")


class DetailRowsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def assert_transition(self, page, scene: str) -> None:
        page.wait_for_function("window.storyTransitions().length > 0", timeout=1000)
        self.assertEqual(transitions(page)[-1]["scene"], scene)
        self.assertEqual(recorded_requests(page), [])

    def test_detail_close(self):
        with story_page(self.browser, "detail", "Component · 详情.morning") as page:
            interact.click(page, "详情.head.close")
            self.assert_transition(page, "Component · 详情.nothing-selected")
            self.assertEqual(page.locator('[data-ui="详情.empty.title"]').inner_text(), "点一张卡")

    def test_detail_goto_origin_spec(self):
        with story_page(self.browser, "detail", "Component · 详情.morning") as page:
            interact.click(page, "详情.origin.link")
            self.assert_transition(page, "Component · 详情.spec")
            self.assertEqual(page.locator('[data-ui="详情.origin.number"]').inner_text(), "#131")
            self.assertEqual(page.locator('[data-ui="详情.title"]').inner_text(), "唤醒回路")

    def test_detail_goto_origin_map(self):
        with story_page(self.browser, "detail", "Component · 详情.spec") as page:
            interact.click(page, "详情.origin.link")
            self.assert_transition(page, "Component · 详情.map")
            self.assertEqual(page.locator('[data-ui="详情.origin.number"]').inner_text(), "#98 · map")
            self.assertEqual(page.locator('[data-ui="详情.title"]').inner_text(), "落地流水线改造")

    def test_detail_goto_blocker(self):
        with story_page(self.browser, "detail", "Component · 详情.morning") as page:
            interact.click(page, "详情.blocker")
            self.assert_transition(page, "Component · 详情.morning")
            self.assertEqual(page.locator('[data-ui="详情.origin.number"]').inner_text(), "#132")
            self.assertEqual(page.locator('[data-ui="详情.title"]').inner_text(), "中继进程骨架")

    def test_detail_goto_decision_blocker(self):
        with story_page(self.browser, "detail", "Component · 详情.decision") as page:
            interact.click(page, "详情.blocker")
            self.assert_transition(page, "Component · 详情.decision")
            self.assertEqual(page.locator('[data-ui="详情.origin.number"]').inner_text(), "#105")
            self.assertEqual(page.locator('[data-ui="详情.title"]').inner_text(), "槽位推到哪一步")

    def test_detail_goto_blocked(self):
        with story_page(self.browser, "detail", "Component · 详情.morning") as page:
            interact.click(page, "详情.blocks")
            self.assert_transition(page, "Component · 详情.morning")
            self.assertEqual(page.locator('[data-ui="详情.origin.number"]').inner_text(), "#135")
            self.assertEqual(page.locator('[data-ui="详情.title"]').inner_text(), "投递回执")

    def test_detail_goto_spec_row(self):
        with story_page(self.browser, "detail", "Component · 详情.map") as page:
            interact.click(page, "详情.spec-row")
            self.assert_transition(page, "Component · 详情.spec")
            self.assertEqual(page.locator('[data-ui="详情.origin.number"]').inner_text(), "#123")
            self.assertEqual(page.locator('[data-ui="详情.title"]').inner_text(), "事件评论格式")

    def test_detail_goto_decision_row(self):
        with story_page(self.browser, "detail", "Component · 详情.map") as page:
            interact.click(page, "详情.decision-row")
            self.assert_transition(page, "Component · 详情.decision")
            self.assertEqual(page.locator('[data-ui="详情.origin.number"]').inner_text(), "#99")
            self.assertEqual(page.locator('[data-ui="详情.title"]').inner_text(), "事件格式怎么定")

    def test_detail_goto_ticket_row(self):
        with story_page(self.browser, "detail", "Component · 详情.spec") as page:
            interact.click(page, "详情.ticket-row")
            self.assert_transition(page, "Component · 详情.morning")
            self.assertEqual(page.locator('[data-ui="详情.origin.number"]').inner_text(), "#132")
            self.assertEqual(page.locator('[data-ui="详情.title"]').inner_text(), "中继进程骨架")

    def test_detail_open_event_block(self):
        with story_page(self.browser, "detail", "Component · 详情.ticket-landed") as page:
            before = page.locator('[data-ui="详情.event"]').count()
            interact.click(page, "详情.event-block.toggle")
            self.assert_transition(page, "event-block-open")
            self.assertGreater(page.locator('[data-ui="详情.event"]').count(), before)
            self.assertEqual(page.locator('[data-ui="详情.event-block.chev"]').first.inner_text(), "▾")

    def test_detail_close_event_block(self):
        with story_page(self.browser, "detail", "Component · 详情.morning") as page:
            self.assertGreater(page.locator('[data-ui="详情.event"]').count(), 0)
            interact.click(page, "详情.event-block.toggle")
            self.assert_transition(page, "event-block-closed")
            self.assertEqual(page.locator('[data-ui="详情.event"]').count(), 0)
            self.assertEqual(page.locator('[data-ui="详情.event-block.chev"]').inner_text(), "▸")

    def test_detail_open_event(self):
        with story_page(self.browser, "detail", "Component · 详情.morning") as page:
            interact.click(page, "详情.event")
            self.assert_transition(page, "event-detail-open")
            detail = page.locator('[data-ui="详情.event.detail"]')
            self.assertEqual(detail.count(), 1)
            self.assertIn("host", detail.inner_text())
            self.assertIn("grok", detail.inner_text())

    def test_detail_close_event(self):
        with story_page(self.browser, "detail", "Component · 详情.morning") as page:
            interact.click(page, "详情.event")
            self.assertEqual(page.locator('[data-ui="详情.event.detail"]').count(), 1)
            interact.click(page, "详情.event")
            self.assert_transition(page, "event-detail-closed")
            self.assertEqual(page.locator('[data-ui="详情.event.detail"]').count(), 0)


if __name__ == "__main__":
    unittest.main()
