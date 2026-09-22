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

    def test_tasks_uses_the_complete_scene_name_and_product_root(self):
        with story_page(self.browser, "tasks", "Component · 任务列表.morning") as page:
            root = page.locator('[data-story-root][data-ui="任务列表.root"]')
            self.assertEqual(root.count(), 1)
            self.assertEqual(page.locator('[data-ui="任务列表.eyebrow.count"]').inner_text(), "3")
            self.assertEqual(page.locator('[data-ui="任务列表.task.title"]').first.inner_text(),
                             "落地流水线改造")

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
            self.assertEqual(value["num"], "#138")
            self.assertEqual(value["title"], "离线时唤醒去向")
            self.assertEqual(value["phase"], "verify")

    def test_scene_input_is_read_by_running_the_data_file(self):
        def inspect_input(page):
            page.route("**/adapters/tasks.mjs", lambda route: route.fulfill(
                content_type="text/javascript",
                body="""export function render(host, data) {
                  const root = document.createElement('nav');
                  root.dataset.storyRoot = '';
                  root.dataset.ui = '任务列表.root';
                  root.dataset.input = JSON.stringify(data);
                  host.replaceChildren(root);
                }""",
            ))

        scene = "Component · 任务列表.morning"
        with story_page(self.browser, "tasks", scene, before_goto=inspect_input) as page:
            root = page.locator("[data-story-root]")
            root.wait_for(state="attached")
            value = json.loads(root.get_attribute("data-input"))
            self.assertEqual(value["selected"], 98)
            self.assertEqual(value["rows"][0], {
                "n": 98,
                "kind": "map",
                "title": "落地流水线改造",
                "lamp": "orange",
                "done": 6,
                "total": 18,
            })

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
            page.route("**/product/tasks.mjs", lambda route: route.fulfill(
                content_type="text/javascript",
                body="""export function render(host, data) {
                  const root = document.createElement('nav');
                  root.dataset.ui = '任务列表.root';
                  root.dataset.screen = 'tasks';
                  root.dataset.productProbe = String(data.view.count);
                  host.replaceChildren(root);
                  return root;
                }""",
            ))

        with story_page(self.browser, "tasks", "Component · 任务列表.morning",
                        before_goto=replace_product) as page:
            root = page.locator('[data-story-root][data-product-probe="3"]')
            self.assertEqual(root.count(), 1)


if __name__ == "__main__":
    unittest.main()
