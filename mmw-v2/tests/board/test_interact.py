from __future__ import annotations

import os
import unittest
from unittest import mock

from playwright.sync_api import sync_playwright

import interact


class InteractTest(unittest.TestCase):
    def test_helper_does_nothing_under_negative(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content('<button type="button" onclick="window.clicks += 1">保存</button>'
                             '<script>window.clicks = 0</script>')
            interact.click(page, "button", "保存")
            self.assertEqual(page.evaluate("window.clicks"), 1)
            with mock.patch.dict(os.environ, {"MMW_NEGATIVE": "1"}):
                interact.click(page, "button", "保存")
            self.assertEqual(page.evaluate("window.clicks"), 1)
            browser.close()


if __name__ == "__main__":
    unittest.main()
