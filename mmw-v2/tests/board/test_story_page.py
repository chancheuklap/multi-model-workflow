from __future__ import annotations

import json
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

    def test_topbar_uses_the_complete_scene_name_and_product_root(self):
        with story_page(self.browser, "topbar", "Component · 顶栏.morning") as page:
            root = page.locator('[data-story-root][data-ui="顶栏.root"]')
            self.assertEqual(root.count(), 1)
            self.assertEqual(page.locator('[data-ui="顶栏.needs-you.count"]').inner_text(), "3")
            self.assertEqual(page.locator('[data-ui="顶栏.read-state"]').inner_text(),
                             "只读 · 07:39 读取")

    def test_service_gives_the_adapter_the_contract_scene_input(self):
        def inspect_input(page):
            page.route("**/adapters/detail.mjs", lambda route: route.fulfill(
                content_type="text/javascript",
                body="""export function render(host, data) {
                  const root = document.createElement('main');
                  root.dataset.storyRoot = '';
                  root.dataset.ui = '详情.root';
                  root.dataset.input = JSON.stringify(data);
                  host.replaceChildren(root);
                }""",
            ))

        scene = "Component · 详情.ticket-returned"
        with story_page(self.browser, "detail", scene, before_goto=inspect_input) as page:
            value = json.loads(page.locator("[data-story-root]").get_attribute("data-input"))
            self.assertEqual(value["select"]["node"], 138)
            self.assertEqual(value["payload"]["read_at"], "2026-09-10T23:39:00Z")

    def test_response_table_returns_any_status_and_body_without_fetch(self):
        escaped = []

        def call_api(page):
            page.route("**/api/**", lambda route: (escaped.append(route.request.url), route.abort()))
            page.route("**/adapters/topbar.mjs", lambda route: route.fulfill(
                content_type="text/javascript",
                body="""export async function render(host, data, api) {
                  const root = document.createElement('header');
                  root.dataset.storyRoot = '';
                  root.dataset.ui = '顶栏.root';
                  host.replaceChildren(root);
                  const response = await api.saveSettings({version: 7});
                  root.textContent = `${response.status}:${JSON.stringify(await response.json())}`;
                }""",
            ))

        responses = {"PUT /api/settings": {"status": 422, "body": {
            "errors": [{"cell": "reviewer.model", "reason": "retired"}],
        }}}
        with story_page(self.browser, "topbar", "Component · 顶栏.morning",
                        responses=responses, before_goto=call_api) as page:
            page.locator("[data-story-root]").wait_for()
            self.assertIn('422:{"errors"', page.locator("[data-story-root]").inner_text())
            self.assertEqual(recorded_requests(page), [{
                "method": "PUT", "path": "/api/settings", "fields": {"version": 7},
            }])
            self.assertEqual(escaped, [])

    def test_response_table_can_leave_one_call_pending(self):
        def call_api(page):
            page.route("**/adapters/topbar.mjs", lambda route: route.fulfill(
                content_type="text/javascript",
                body="""export function render(host, data, api) {
                  const root = document.createElement('header');
                  root.dataset.storyRoot = '';
                  root.dataset.ui = '顶栏.root';
                  root.dataset.settled = 'no';
                  host.replaceChildren(root);
                  api.scanSettings({source: 'cli'}).then(() => { root.dataset.settled = 'yes'; });
                }""",
            ))

        responses = {"POST /api/settings/scan": {"never": True}}
        with story_page(self.browser, "topbar", "Component · 顶栏.morning",
                        responses=responses, before_goto=call_api) as page:
            page.wait_for_timeout(50)
            self.assertEqual(page.locator("[data-story-root]").get_attribute("data-settled"), "no")
            self.assertEqual(recorded_requests(page), [{
                "method": "POST", "path": "/api/settings/scan", "fields": {"source": "cli"},
            }])

    def test_adapter_renders_the_product_module(self):
        def replace_product(page):
            page.route("**/product/topbar.mjs", lambda route: route.fulfill(
                content_type="text/javascript",
                body="""export function fromBoard(payload) { return {count: payload.tasks.length}; }
                export function render(host, view) {
                  const root = document.createElement('header');
                  root.dataset.ui = '顶栏.root';
                  root.dataset.screen = 'topbar';
                  root.dataset.productProbe = String(view.count);
                  host.replaceChildren(root);
                  return root;
                }""",
            ))

        with story_page(self.browser, "topbar", "Component · 顶栏.morning",
                        before_goto=replace_product) as page:
            root = page.locator('[data-story-root][data-product-probe="3"]')
            self.assertEqual(root.count(), 1)


if __name__ == "__main__":
    unittest.main()
