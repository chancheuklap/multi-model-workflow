from __future__ import annotations

import copy
import json
import re
import unittest
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

import interact
from story_helper import recorded_requests, story_page


ROOT = Path(__file__).resolve().parents[3]
SETTINGS_SOURCE = ROOT / "prototypes" / "task-board" / "claude-design" / "data" / "settings.js"


def settings_scenes() -> dict:
    source = SETTINGS_SOURCE.read_text(encoding="utf-8")
    match = re.fullmatch(r"window\.SETTINGS_SCENES = (\{.*\});?\n?", source)
    if not match:
        raise AssertionError("cannot read settings scene input")
    return json.loads(match.group(1))


SCENES = settings_scenes()


def transitions(page) -> list[dict]:
    return page.evaluate("window.storyTransitions()")


def transition_names(page) -> list[str]:
    return [item["scene"] for item in transitions(page)]


def one_request(page, method: str, path: str, fields=None) -> None:
    assert recorded_requests(page) == [{"method": method, "path": path, "fields": fields}]


def selected(page, data_ui: str, nth: int = 0) -> str:
    return page.locator(f'[data-ui="{data_ui}"]').nth(nth).input_value()


def local_hhmm(value: str) -> str:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone().strftime("%H:%M")


def scan_answer(source: str = "cli") -> dict:
    answer = copy.deepcopy(SCENES["mine"]["payload"]["scan"])
    answer["source"] = source
    answer["scanned_at"] = "2026-09-21T09:17:00Z"
    answer["scanning"] = False
    answer["hosts"]["cursor"]["offered"] = [{"model": "only-now", "efforts": ["high"]}]
    return answer


class SettingsRowsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_settings_rescan(self):
        answer = scan_answer()
        responses = {"POST /api/settings/scan": {"status": 200, "body": answer}}
        with story_page(self.browser, "settings", "Component · 本机配置.mine", responses) as page:
            interact.click(page, "本机配置.scan.rescan")
            page.wait_for_function("window.storyTransitions().length >= 1")
            one_request(page, "POST", "/api/settings/scan", {"source": "cli"})
            self.assertIn("Component · 本机配置.scanning", transition_names(page))
            self.assertIn(f"{local_hhmm(answer['scanned_at'])} 问各 host 的 CLI",
                          page.locator('[data-ui="本机配置.scan"]').inner_text())
            self.assertIn("1 个 model", page.locator('[data-ui="本机配置.host"]').first.inner_text())

        for status, marker in [(500, "scan failed marker"), (403, "forbidden marker")]:
            responses = {"POST /api/settings/scan": {"status": status, "body": {"message": marker}}}
            with story_page(self.browser, "settings", "Component · 本机配置.mine", responses) as page:
                before = page.locator('[data-ui="本机配置.root"]').inner_text()
                interact.click(page, "本机配置.scan.rescan")
                page.wait_for_function("window.storyCalls().length === 1")
                page.wait_for_timeout(20)
                one_request(page, "POST", "/api/settings/scan", {"source": "cli"})
                self.assertEqual(page.locator('[data-ui="本机配置.root"]').inner_text(), before)
                self.assertNotIn(marker, page.locator("body").inner_text())

    def test_settings_runner_pick(self):
        with story_page(self.browser, "settings", "Component · 本机配置.mine") as page:
            interact.select(page, "本机配置.runner.select", "herdr")
            page.wait_for_function("window.storyTransitions().length === 1")
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(selected(page, "本机配置.runner.select"), "herdr")
            self.assertEqual(transition_names(page), ["Component · 本机配置.edited"])

    def test_settings_runner_rescan(self):
        answer = scan_answer("paseo")
        responses = {"POST /api/settings/scan": {"status": 200, "body": answer}}
        with story_page(self.browser, "settings", "Component · 本机配置.mine", responses) as page:
            interact.select(page, "本机配置.runner.select", "paseo")
            page.wait_for_function("window.storyTransitions().length >= 1")
            one_request(page, "POST", "/api/settings/scan", {"source": "paseo"})
            self.assertIn("Component · 本机配置.scanning", transition_names(page))
            self.assertIn(f"{local_hhmm(answer['scanned_at'])} 问 Paseo",
                          page.locator('[data-ui="本机配置.scan"]').inner_text())
            self.assertIn("1 个 model", page.locator('[data-ui="本机配置.host"]').first.inner_text())

        for status, marker in [(500, "scan failed marker"), (403, "forbidden marker")]:
            responses = {"POST /api/settings/scan": {"status": status, "body": {"message": marker}}}
            with story_page(self.browser, "settings", "Component · 本机配置.mine", responses) as page:
                interact.select(page, "本机配置.runner.select", "paseo")
                page.wait_for_function("window.storyCalls().length === 1")
                page.wait_for_timeout(20)
                one_request(page, "POST", "/api/settings/scan", {"source": "paseo"})
                self.assertIn("07:02 问各 host 的 CLI", page.locator('[data-ui="本机配置.scan"]').inner_text())
                self.assertIn("9 个 model", page.locator('[data-ui="本机配置.host"]').first.inner_text())
                self.assertEqual(page.locator(".spin").count(), 0)
                self.assertNotIn(marker, page.locator("body").inner_text())

    def test_settings_host_pick_keeps_model(self):
        with story_page(self.browser, "settings", "Component · 本机配置.mine") as page:
            interact.select(page, "本机配置.role.host", "cursor")
            page.wait_for_function("window.storyTransitions().length === 1")
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(selected(page, "本机配置.role.host"), "cursor")
            self.assertEqual(selected(page, "本机配置.role.model"), "grok 4.6")
            self.assertEqual(transition_names(page), ["Component · 本机配置.edited"])

    def test_settings_host_pick_clears_model(self):
        with story_page(self.browser, "settings", "Component · 本机配置.mine") as page:
            interact.select(page, "本机配置.role.host", "claude")
            page.wait_for_function("window.storyTransitions().length === 1")
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(selected(page, "本机配置.role.host"), "claude")
            self.assertEqual(selected(page, "本机配置.role.model"), "")
            self.assertEqual(transition_names(page), ["Component · 本机配置.incomplete"])

    def test_settings_model_pick(self):
        with story_page(self.browser, "settings", "Component · 本机配置.mine") as page:
            interact.select(page, "本机配置.role.model", "grok 4.5")
            page.wait_for_function("window.storyTransitions().length === 1")
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(selected(page, "本机配置.role.model"), "grok 4.5")
            self.assertEqual(transition_names(page), ["Component · 本机配置.edited"])

    def test_settings_effort_pick(self):
        with story_page(self.browser, "settings", "Component · 本机配置.mine") as page:
            interact.select(page, "本机配置.role.effort", "xhigh")
            page.wait_for_function("window.storyTransitions().length === 1")
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(selected(page, "本机配置.role.effort"), "xhigh")
            self.assertEqual(transition_names(page), ["Component · 本机配置.edited"])

    def test_settings_save(self):
        responses = {"PUT /api/settings": [
            {"status": 200, "body": {"version": 99, "saved_at": "2026-09-21T09:23:00Z"}},
            {"status": 200, "body": {"version": 100, "saved_at": "2026-09-21T09:24:00Z"}},
        ]}
        with story_page(self.browser, "settings", "Component · 本机配置.edited", responses) as page:
            interact.click(page, "本机配置.sheet.save")
            page.wait_for_function("window.storyTransitions().length >= 1")
            first = recorded_requests(page)[0]
            self.assertEqual(first["method"], "PUT")
            self.assertEqual(first["path"], "/api/settings")
            self.assertEqual(first["fields"]["version"], 12)
            self.assertEqual(first["fields"]["rows"]["senior-worker"], {
                "host": "claude", "model": "opus 5", "effort": "high",
            })
            self.assertIn(f"已保存 · {local_hhmm('2026-09-21T09:23:00Z')}",
                          page.locator('[data-ui="本机配置.sheet.status"]').inner_text())
            self.assertEqual(transition_names(page)[0], "Component · 本机配置.saved")
            interact.select(page, "本机配置.role.effort", "xhigh")
            interact.click(page, "本机配置.sheet.save")
            page.wait_for_function("window.storyCalls().length === 2")
            self.assertEqual(recorded_requests(page)[1]["fields"]["version"], 99)

        responses = {"PUT /api/settings": {
            "status": 409, "body": {"modified_at": "2026-09-21T09:31:00Z"},
        }}
        with story_page(self.browser, "settings", "Component · 本机配置.edited", responses) as page:
            interact.click(page, "本机配置.sheet.save")
            page.wait_for_function("window.storyTransitions().length === 1")
            self.assertEqual(transition_names(page), ["Component · 本机配置.changed"])
            self.assertIn(f"{local_hhmm('2026-09-21T09:31:00Z')} 被别处改过",
                          page.locator('[data-ui="本机配置.refused.text"]').inner_text())
            self.assertEqual(page.locator('[data-ui="本机配置.refused.reread"]').inner_text(), "重新读取")

        responses = {"PUT /api/settings": {"status": 422, "body": {"errors": [{
            "cell": "senior-worker.model", "reason": "model refused marker",
        }]}}}
        with story_page(self.browser, "settings", "Component · 本机配置.edited", responses) as page:
            interact.click(page, "本机配置.sheet.save")
            page.wait_for_function("window.storyTransitions().length === 1")
            self.assertEqual(transition_names(page), ["Component · 本机配置.refused"])
            self.assertIn("model refused marker", page.locator('[data-ui="本机配置.role.problem.item"]').inner_text())
            background = page.locator('[data-ui="本机配置.role.model"]').nth(1).evaluate(
                "node => getComputedStyle(node).backgroundImage"
            )
            self.assertIn("repeating-linear-gradient", background)

        for status, marker in [(423, "lock holder marker"), (403, "forbidden marker")]:
            responses = {"PUT /api/settings": {"status": status, "body": {"message": marker}}}
            with story_page(self.browser, "settings", "Component · 本机配置.edited", responses) as page:
                before = page.locator('[data-ui="本机配置.root"]').inner_text()
                interact.click(page, "本机配置.sheet.save")
                page.wait_for_function("window.storyCalls().length === 1")
                page.wait_for_timeout(20)
                self.assertEqual(page.locator('[data-ui="本机配置.root"]').inner_text(), before)
                self.assertEqual(transition_names(page), [])
                self.assertNotIn(marker, page.locator("body").inner_text())

    def test_settings_reread(self):
        body = copy.deepcopy(SCENES["mine"]["payload"])
        body["version"] = 44
        body["runner"] = "herdr"
        body["scan"]["scanned_at"] = "2026-09-21T09:42:00Z"
        responses = {
            "GET /api/settings": {"status": 200, "body": body},
            "PUT /api/settings": {"status": 200, "body": {"version": 45, "saved_at": "2026-09-21T09:43:00Z"}},
        }
        with story_page(self.browser, "settings", "Component · 本机配置.changed", responses) as page:
            interact.click(page, "本机配置.refused.reread")
            page.wait_for_function("window.storyTransitions().length === 1")
            self.assertEqual(recorded_requests(page), [
                {"method": "GET", "path": "/api/settings", "fields": None},
            ])
            self.assertEqual(transition_names(page), ["Component · 本机配置.mine"])
            self.assertEqual(selected(page, "本机配置.runner.select"), "herdr")
            self.assertIn(local_hhmm(body["scan"]["scanned_at"]),
                          page.locator('[data-ui="本机配置.scan"]').inner_text())
            self.assertEqual(page.locator('[data-ui="本机配置.refused"]').count(), 0)
            interact.select(page, "本机配置.role.effort", "xhigh")
            interact.click(page, "本机配置.sheet.save")
            page.wait_for_function("window.storyCalls().length === 2")
            self.assertEqual(recorded_requests(page)[1]["fields"]["version"], 44)

        responses = {"GET /api/settings": {"status": 500, "body": {"message": "read failed marker"}}}
        with story_page(self.browser, "settings", "Component · 本机配置.changed", responses) as page:
            before = page.locator('[data-ui="本机配置.refused"]').inner_text()
            interact.click(page, "本机配置.refused.reread")
            page.wait_for_function("window.storyCalls().length === 1")
            page.wait_for_timeout(20)
            self.assertEqual(page.locator('[data-ui="本机配置.refused"]').inner_text(), before)
            self.assertEqual(transition_names(page), [])
            self.assertNotIn("read failed marker", page.locator("body").inner_text())

    def test_settings_close(self):
        with story_page(self.browser, "settings", "Component · 本机配置.mine") as page:
            interact.click(page, "本机配置.sheet.close")
            page.wait_for_function("window.storyTransitions().length === 1")
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(transition_names(page), ["settings-closed"])
            self.assertEqual(page.locator('[data-ui="本机配置.root"]').count(), 0)

    def test_settings_close_unchanged(self):
        with story_page(self.browser, "settings", "Component · 本机配置.mine") as page:
            interact.click(page, "本机配置.sheet.cancel")
            page.wait_for_function("window.storyTransitions().length === 1")
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(transition_names(page), ["settings-closed"])
            self.assertEqual(page.locator('[data-ui="本机配置.root"]').count(), 0)

    def test_settings_cancel(self):
        with story_page(self.browser, "settings", "Component · 本机配置.edited") as page:
            interact.click(page, "本机配置.sheet.cancel")
            page.wait_for_function("window.storyTransitions().length === 1")
            self.assertEqual(recorded_requests(page), [])
            self.assertEqual(transition_names(page), ["settings-closed"])
            self.assertEqual(page.locator('[data-ui="本机配置.root"]').count(), 0)


if __name__ == "__main__":
    unittest.main()
