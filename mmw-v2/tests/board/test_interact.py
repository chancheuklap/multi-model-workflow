from __future__ import annotations

import os
import unittest
from unittest import mock

from playwright.sync_api import sync_playwright

import interact


class InteractTest(unittest.TestCase):
    def test_helpers_find_controls_by_data_ui(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(
                '<button data-ui="panel.save" onclick="window.clicks += 1">保存</button>'
                '<input data-ui="panel.name">'
                '<select data-ui="panel.host"><option value="codex">Codex</option></select>'
                '<script>window.clicks = 0</script>'
            )
            interact.click(page, "panel.save")
            interact.fill(page, "panel.name", "MMW")
            interact.select(page, "panel.host", "codex")
            self.assertEqual(page.evaluate("window.clicks"), 1)
            self.assertEqual(page.locator('[data-ui="panel.name"]').input_value(), "MMW")
            self.assertEqual(page.locator('[data-ui="panel.host"]').input_value(), "codex")

            page.set_content(
                '<button aria-label="旧名字" data-ui="panel.save" '
                'onclick="window.clicks += 1">新名字</button>'
                '<script>window.clicks = 0</script>'
            )
            interact.click(page, "panel.save")
            self.assertEqual(page.evaluate("window.clicks"), 1)
            browser.close()

    def test_helpers_do_nothing_under_negative(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(
                '<button data-ui="panel.save" onclick="window.clicks += 1">保存</button>'
                '<input data-ui="panel.name" value="before">'
                '<select data-ui="panel.host"><option value="a">A</option>'
                '<option value="b">B</option></select>'
                '<script>window.clicks = 0</script>'
            )
            with mock.patch.dict(os.environ, {"MMW_NEGATIVE": "1"}):
                interact.click(page, "panel.save")
                interact.fill(page, "panel.name", "after")
                interact.select(page, "panel.host", "b")
            self.assertEqual(page.evaluate("window.clicks"), 0)
            self.assertEqual(page.locator('[data-ui="panel.name"]').input_value(), "before")
            self.assertEqual(page.locator('[data-ui="panel.host"]').input_value(), "a")
            browser.close()


if __name__ == "__main__":
    unittest.main()
