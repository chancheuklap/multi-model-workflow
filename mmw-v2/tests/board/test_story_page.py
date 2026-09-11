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
                box = root.bounding_box()
                self.assertIsNotNone(box)
                self.assertGreater(box["width"], 0)
                self.assertGreater(box["height"], 0)
                self.assertEqual(root.get_attribute("data-screen"), mount)

    def test_story_api_records_requests(self):
        escaped = []

        def install_probe(page):
            page.route("**/api/**", lambda route: (
                escaped.append(route.request.url), route.abort()
            ))
            page.route("**/adapters/topbar.mjs", lambda route: route.fulfill(
                content_type="text/javascript",
                body="""export function render(host, data, api) {
                  const root = document.createElement('header');
                  root.dataset.storyRoot = '';
                  root.dataset.screen = 'topbar';
                  root.style.height = '52px';
                  host.replaceChildren(root);
                  api.saveSettings({version: 7});
                }""",
            ))

        with story_page(self.browser, "topbar", "顶栏.morning", install_probe) as page:
            self.assertEqual(recorded_requests(page), [{
                "method": "PUT", "path": "/api/settings", "fields": {"version": 7}
            }])
            self.assertEqual(escaped, [])

    def test_adapter_renders_the_product_module(self):
        def replace_product(page):
            page.route("**/product/topbar.mjs", lambda route: route.fulfill(
                content_type="text/javascript",
                body="""export function render(host) {
                  const root = document.createElement('header');
                  root.dataset.screen = 'topbar';
                  root.dataset.productProbe = 'rendered';
                  host.replaceChildren(root);
                  return root;
                }""",
            ))

        with story_page(self.browser, "topbar", "顶栏.morning", replace_product) as page:
            root = page.locator('[data-story-root][data-product-probe="rendered"]')
            self.assertEqual(root.count(), 1)


if __name__ == "__main__":
    unittest.main()
