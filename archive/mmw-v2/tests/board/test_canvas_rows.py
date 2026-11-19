"""Four-column boundary tests for the canvas screen-contract rows."""

from __future__ import annotations

import unittest

from playwright.sync_api import sync_playwright

import interact
from story_helper import recorded_requests, story_page


def transitions(page):
    return page.evaluate("window.storyTransitions()")


def text(page, data_ui: str) -> str:
    return page.locator(f'[data-ui="{data_ui}"]').first.inner_text()


class CanvasRowsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_canvas_open_ticket(self):
        with story_page(self.browser, "canvas", "Component · 画布.morning") as page:
            interact.click(page, "画布.ticket-card.open")
            page.wait_for_function("window.storyTransitions().length === 1", timeout=1000)
            selected = page.locator('[data-ui="画布.ticket-card"].on')
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(selected.locator('[data-ui="画布.ticket-card.num"]').inner_text(), "#132")
            self.assertEqual(selected.locator('[data-ui="画布.ticket-card.title"]').inner_text(), "中继进程骨架")
            self.assertEqual(selected.locator('[data-ui="画布.ticket-card.lamp"]').get_attribute("title"), "done")
            self.assertEqual(selected.locator('[data-ui="画布.ticket-card.phase"]').inner_text(), "landed")
            self.assertEqual(selected.locator('[data-ui="画布.ticket-card.run"]').inner_text(),
                             "claude · opus 5 · high")
            self.assertEqual(transitions(page)[-1]["scene"], "Component · 画布.morning")

    def test_canvas_open_container(self):
        with story_page(self.browser, "canvas", "Component · 画布.morning") as page:
            interact.click(page, "画布.container-card.open")
            page.wait_for_function("window.storyTransitions().length === 1", timeout=1000)
            selected = page.locator('[data-ui="画布.container-card"].on')
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(selected.locator('[data-ui="画布.container-card.num"]').inner_text(),
                             "#98 · map")
            self.assertEqual(selected.locator('[data-ui="画布.container-card.title"]').inner_text(),
                             "落地流水线改造")
            self.assertEqual(selected.locator('[data-ui="画布.container-card.lamp"]').get_attribute("title"),
                             "needs you")
            self.assertEqual(selected.locator('[data-ui="画布.container-card.count"]').inner_text(), "6/18")
            self.assertEqual(transitions(page)[-1]["scene"], "Component · 画布.morning")

    def test_canvas_expand_container(self):
        with story_page(self.browser, "canvas", "Component · 画布.morning") as page:
            decisions = page.locator('[data-ui="画布.decision-card"]')
            self.assertGreater(decisions.count(), 0)
            interact.click(page, "画布.container-card.expand")
            page.wait_for_function(
                'document.querySelectorAll(\'[data-ui="画布.decision-card"]\').length === 0',
                timeout=1000,
            )
            interact.click(page, "画布.container-card.expand")
            page.wait_for_function(
                'document.querySelectorAll(\'[data-ui="画布.decision-card"]\').length > 0',
                timeout=1000,
            )
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(text(page, "画布.decision-card.num"), "#99")
            self.assertEqual(transitions(page)[-1]["scene"], "container-expanded")

    def test_canvas_collapse_container(self):
        with story_page(self.browser, "canvas", "Component · 画布.morning") as page:
            self.assertGreater(page.locator('[data-ui="画布.decision-card"]').count(), 0)
            interact.click(page, "画布.container-card.expand")
            page.wait_for_function(
                'document.querySelectorAll(\'[data-ui="画布.decision-card"]\').length === 0',
                timeout=1000,
            )
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(transitions(page)[-1]["scene"], "container-collapsed")

    def test_canvas_open_decision(self):
        with story_page(self.browser, "canvas", "Component · 画布.morning") as page:
            interact.click(page, "画布.decision-card.open")
            page.wait_for_function("window.storyTransitions().length === 1", timeout=1000)
            selected = page.locator('[data-ui="画布.decision-card"].on')
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(selected.locator('[data-ui="画布.decision-card.num"]').inner_text(), "#99")
            self.assertEqual(selected.locator('[data-ui="画布.decision-card.title"]').inner_text(),
                             "事件格式怎么定")
            self.assertEqual(selected.locator('[data-ui="画布.decision-card.kind"]').inner_text(), "grilling")
            self.assertEqual(transitions(page)[-1]["scene"], "Component · 画布.morning")

    def test_canvas_zoom_in(self):
        with story_page(self.browser, "canvas", "Component · 画布.morning") as page:
            before = text(page, "画布.zoom.level")
            interact.click(page, "画布.zoom.in")
            page.wait_for_function("window.storyTransitions().length === 1", timeout=1000)
            self.assertEqual(recorded_requests(page), [])
            self.assertGreater(int(text(page, "画布.zoom.level").rstrip("%")),
                               int(before.rstrip("%")))
            self.assertEqual(transitions(page)[-1]["scene"], "canvas-zoomed")

    def test_canvas_zoom_out(self):
        with story_page(self.browser, "canvas", "Component · 画布.morning") as page:
            before = text(page, "画布.zoom.level")
            interact.click(page, "画布.zoom.out")
            page.wait_for_function("window.storyTransitions().length === 1", timeout=1000)
            self.assertEqual(recorded_requests(page), [])
            self.assertLess(int(text(page, "画布.zoom.level").rstrip("%")),
                            int(before.rstrip("%")))
            self.assertEqual(transitions(page)[-1]["scene"], "canvas-zoomed")

    def test_canvas_fit(self):
        with story_page(self.browser, "canvas", "Component · 画布.morning") as page:
            interact.click(page, "画布.zoom.in")
            page.wait_for_function("window.storyTransitions().length === 1", timeout=1000)
            zoomed = text(page, "画布.zoom.level")
            interact.click(page, "画布.zoom.fit")
            page.wait_for_function("window.storyTransitions().length === 2", timeout=1000)
            self.assertEqual(recorded_requests(page), [])
            self.assertNotEqual(text(page, "画布.zoom.level"), zoomed)
            self.assertEqual(transitions(page)[-1]["scene"], "canvas-fitted")


if __name__ == "__main__":
    unittest.main()
