from __future__ import annotations

import unittest

from playwright.sync_api import sync_playwright

import interact
from story_helper import recorded_requests, story_page

EDITED = {
    "junior-worker": {"host": "grok", "model": "grok 4.6", "effort": "high"},
    "senior-worker": {"host": "claude", "model": "opus 5", "effort": "high"},
    "reviewer": {"host": "claude", "model": "opus 5", "effort": "high"},
    "verifier": {"host": "claude", "model": "sonnet 5", "effort": "high"},
    "advisor": {"host": "claude", "model": "fable 5.1", "effort": "medium"},
}


class SettingsCallsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_save_puts_the_whole_config(self):
        with story_page(self.browser, "settings", "edited") as page:
            interact.click(page, "button", "保存")
            self.assertEqual(recorded_requests(page), [
                {"method": "PUT", "path": "/api/settings", "fields": {
                    "version": 1, "runner": "orca", "rows": EDITED,
                }},
            ])

    def test_rescan_posts_the_source(self):
        with story_page(self.browser, "settings", "mine") as page:
            interact.click(page, "button", "重新扫描")
            self.assertEqual(recorded_requests(page), [
                {"method": "POST", "path": "/api/settings/scan", "fields": {"source": "cli"}},
            ])

    def test_reread_gets_the_settings(self):
        with story_page(self.browser, "settings", "refused") as page:
            interact.click(page, "button", "重新读取")
            self.assertEqual(recorded_requests(page), [
                {"method": "GET", "path": "/api/settings", "fields": None},
            ])

    def test_runner_to_paseo_rescans(self):
        with story_page(self.browser, "settings", "mine") as page:
            interact.select(page, "combobox", "runner", "paseo")
            self.assertEqual(recorded_requests(page), [
                {"method": "POST", "path": "/api/settings/scan", "fields": {"source": "paseo"}},
            ])


if __name__ == "__main__":
    unittest.main()
