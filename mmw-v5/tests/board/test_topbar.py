from __future__ import annotations

import os
import tempfile
import unittest

from playwright.sync_api import expect, sync_playwright

from board_process import RunningBoard
from test_board_data import FAKE_BIN


class TopbarRepositoryTest(unittest.TestCase):
    def test_topbar_names_its_repository_without_inventing_an_identity(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                for repo in ["sample/alpha", "other/beta", None]:
                    with self.subTest(repo=repo), tempfile.TemporaryDirectory() as home:
                        environment = {
                            "PATH": str(FAKE_BIN) + os.pathsep + os.environ.get("PATH", ""),
                            "MMW_HOME": home,
                        }
                        fixture = {"repo": repo, "maps": [], "specs": [], "fail_all": repo is None}
                        with RunningBoard(environment=environment, fixture=fixture) as board:
                            page = browser.new_page()
                            try:
                                page.goto(board.origin, wait_until="networkidle")
                                if repo is None:
                                    expect(page.get_by_text("读 GitHub 失败", exact=True)).to_be_visible()
                                expect(page.locator('[data-ui="顶栏.brand.repo"]')).to_have_text(repo or "")
                                expect(page.locator('[data-ui="顶栏.brand.mark"]')).to_have_text("MMW")
                            finally:
                                page.close()
            finally:
                browser.close()


if __name__ == "__main__":
    unittest.main()
