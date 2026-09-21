from __future__ import annotations

import os
import sys

from playwright.sync_api import sync_playwright

origin = os.environ["ORIGIN"]
expected_token = os.environ["INSTANCE_TOKEN"]
try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(origin, wait_until="networkidle", timeout=10_000)
        root = page.locator("[data-board-root]")
        token = page.locator('meta[name="mmw-page-token"]').get_attribute("content")
        board_response = page.request.get(origin + "/api/board")
        board = board_response.json()
        if root.count() != 1 or not root.is_visible():
            raise AssertionError("the answering page has no visible board root")
        if token != expected_token:
            raise AssertionError("the answering page token does not match this start")
        if "read_failed" in board:
            raise AssertionError(f"the board read failed: {board['read_failed']['message']}")
        if not board.get("tasks"):
            raise AssertionError("the board has no fixture task")
        browser.close()
except Exception as exc:
    print(f"smoke failed: {exc}", file=sys.stderr)
    sys.exit(1)
