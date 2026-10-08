from __future__ import annotations

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from evidence import first_line, watch, write_evidence  # noqa: E402


def main() -> int:
    origin = os.environ["ORIGIN"]
    expected_token = os.environ["INSTANCE_TOKEN"]
    page = None
    context = None
    console_errors: list[str] = []
    failed_requests: list[str] = []
    try:
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(headless=True)
                context = browser.new_context()
                context.tracing.start(screenshots=True, snapshots=True)
                page = context.new_page()
                watch(page, console_errors, failed_requests)
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
                context.tracing.stop()
                browser.close()
            except Exception as exc:
                write_evidence(page, context, console_errors, failed_requests)
                print(first_line(exc), file=sys.stderr)
                return 1
    except Exception as exc:
        print(first_line(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
