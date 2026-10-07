from __future__ import annotations

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def first_line(exc: BaseException) -> str:
    text = str(exc).strip()
    return text.splitlines()[0] if text else type(exc).__name__


def write_evidence(page, context, console_errors: list[str], failed_requests: list[str]) -> None:
    """Write the four failure files while the page is still open.

    A capture that fails is absent from the directory. The other files are still written.
    """
    raw = os.environ.get("MMW_EVIDENCE_DIR")
    if not raw:
        return
    dest = Path(raw)
    dest.mkdir(parents=True, exist_ok=True)
    if page is not None:
        try:
            page.screenshot(path=str(dest / "screenshot.png"))
        except Exception:
            pass
    if context is not None:
        try:
            context.tracing.stop(path=str(dest / "trace.zip"))
        except Exception:
            pass
    console_text = "\n".join(console_errors)
    request_text = "\n".join(failed_requests)
    (dest / "console.txt").write_text(
        console_text + ("\n" if console_text else ""), encoding="utf-8")
    (dest / "requests.txt").write_text(
        request_text + ("\n" if request_text else ""), encoding="utf-8")


def watch(page, console_errors: list[str], failed_requests: list[str]) -> None:
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    page.on(
        "response",
        lambda response: failed_requests.append(
            f"{response.status} {response.request.method} {response.url}"
        ) if response.status >= 400 else None,
    )
    page.on(
        "requestfailed",
        lambda request: failed_requests.append(
            f"failed {request.method} {request.url} {request.failure or ''}".rstrip()
        ),
    )


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
        write_evidence(page, context, console_errors, failed_requests)
        print(first_line(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
