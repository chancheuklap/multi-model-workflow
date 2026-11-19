from __future__ import annotations

import unittest

from playwright.sync_api import sync_playwright

import interact
from story_helper import recorded_requests, story_page


def transitions(page):
    return page.evaluate("window.storyTransitions()")


class TasksRowsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_tasks_pick(self):
        with story_page(self.browser, "tasks", "Component · 任务列表.morning") as page:
            rows = page.locator('[data-ui="任务列表.task"]')
            self.assertEqual(rows.nth(0).get_attribute("class"), "task on")
            self.assertEqual(rows.nth(1).get_attribute("class"), "task")

            interact.click(page, "任务列表.task#2")

            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(rows.nth(0).get_attribute("class"), "task")
            self.assertEqual(rows.nth(1).get_attribute("class"), "task on")
            self.assertEqual(
                rows.nth(1).locator('[data-ui="任务列表.task.meta"]').inner_text(),
                "#77 · map",
            )
            self.assertEqual(
                rows.nth(1).locator('[data-ui="任务列表.task.title"]').inner_text(),
                "交接包比对",
            )
            self.assertEqual(
                rows.nth(1).locator('[data-ui="任务列表.task.lamp"]').get_attribute("class"),
                "lamp ink",
            )
            self.assertEqual(
                rows.nth(1).locator('[data-ui="任务列表.task.count"]').inner_text(),
                "3/3 landed",
            )
            self.assertEqual(transitions(page), [{
                "scene": "Component · 任务列表.morning",
                "data": {"task": 77},
            }])


if __name__ == "__main__":
    unittest.main()
