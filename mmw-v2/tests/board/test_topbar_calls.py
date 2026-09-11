from __future__ import annotations

import unittest

from playwright.sync_api import sync_playwright

import interact
from story_helper import recorded_requests, story_page


def request_line(page, method, path):
    calls = recorded_requests(page)
    return [{key: call[key] for key in ("method", "path")} for call in calls] == [
        {"method": method, "path": path},
    ]


class TopbarCallsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_refresh_after_a_good_read(self):
        with story_page(self.browser, "topbar", "顶栏.morning") as page:
            interact.click(page, "button", "立刻重读 GitHub")
            self.assertTrue(request_line(page, "POST", "/api/board/refresh"), recorded_requests(page))

    def test_refresh_after_a_failed_read(self):
        with story_page(self.browser, "topbar", "顶栏.bad-data") as page:
            interact.click(page, "button", "立刻重读 GitHub")
            self.assertTrue(request_line(page, "POST", "/api/board/refresh"), recorded_requests(page))

    def test_gear_reads_the_settings(self):
        with story_page(self.browser, "topbar", "顶栏.morning") as page:
            interact.click(page, "button", "本机配置")
            self.assertTrue(request_line(page, "GET", "/api/settings"), recorded_requests(page))


if __name__ == "__main__":
    unittest.main()
