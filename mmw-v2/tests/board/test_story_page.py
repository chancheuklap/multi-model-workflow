from __future__ import annotations

import unittest

from playwright.sync_api import sync_playwright

from story_helper import recorded_requests, story_page


class StoryPageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_every_mount_has_a_story_root(self):
        first_scenes = {
            "topbar": "顶栏.morning",
            "tasks": "任务列表.morning",
            "canvas": "画布.morning",
            "detail": "详情.morning",
            "settings": "mine",
        }
        for mount, scene in first_scenes.items():
            with self.subTest(mount=mount), story_page(self.browser, mount, scene) as page:
                root = page.locator("[data-story-root]")
                self.assertEqual(root.count(), 1)
                self.assertTrue(root.is_visible())
                self.assertEqual(root.get_attribute("data-screen"), mount)

    def test_story_api_records_requests(self):
        with story_page(self.browser, "topbar", "顶栏.morning") as page:
            escaped = []
            page.on("request", lambda request: escaped.append(request.url)
                    if "/api/should-not-leave" in request.url else None)
            page.evaluate("window.storyApi.request('PUT', '/api/should-not-leave', {version: 7})")
            self.assertEqual(recorded_requests(page), [{
                "method": "PUT", "path": "/api/should-not-leave", "fields": {"version": 7}
            }])
            self.assertEqual(escaped, [])


if __name__ == "__main__":
    unittest.main()
