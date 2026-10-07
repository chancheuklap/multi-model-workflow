from __future__ import annotations

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def enabled_values(select):
    return select.locator("option:not(:disabled)").evaluate_all(
        "options => options.map(option => option.value)"
    )


def choose_another_model(row):
    select = row.locator('[data-ui="本机配置.role.model"]')
    current = select.input_value()
    alternative = next(
        (choice for choice in enabled_values(select) if choice and choice != current),
        None,
    )
    if alternative is None:
        raise AssertionError(f"reviewer.model has no legal alternative to {current!r}")
    select.select_option(alternative)
    return alternative


def choose_effort_when_the_model_cleared_it(row, model: str) -> None:
    """A model that does not offer the current effort, and offers more than one, clears it."""
    effort = row.locator('[data-ui="本机配置.role.effort"]')
    if effort.input_value():
        return
    picked = next((choice for choice in enabled_values(effort) if choice), None)
    if picked is None:
        raise AssertionError(
            f"reviewer.effort has no legal value after selecting {model!r}"
        )
    effort.select_option(picked)


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
    origin = os.environ["ORIGIN"].rstrip("/")
    page = None
    context = None
    console_errors: list[str] = []
    failed_requests: list[str] = []
    try:
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(headless=True)
                context = browser.new_context(viewport={"width": 1440, "height": 900})
                context.tracing.start(screenshots=True, snapshots=True)
                page = context.new_page()
                watch(page, console_errors, failed_requests)
                settings_reads = []
                page.on(
                    "request",
                    lambda request: settings_reads.append(request.url)
                    if request.method == "GET" and request.url == origin + "/api/settings"
                    else None,
                )

                page.goto(origin, wait_until="networkidle", timeout=30_000)
                page.locator('[data-ui="顶栏.settings"]').click()
                sheet = page.locator('[data-ui="本机配置.root"]')
                sheet.wait_for(state="visible", timeout=10_000)
                reviewer = sheet.locator('[data-ui="本机配置.role"]').filter(has_text="reviewer")
                expected = choose_another_model(reviewer)
                choose_effort_when_the_model_cleared_it(reviewer, expected)

                save = sheet.locator('[data-ui="本机配置.sheet.save"]')
                if save.is_disabled():
                    raise AssertionError("save stayed disabled after selecting a legal reviewer.model")
                with page.expect_response(
                    lambda response: response.request.method == "PUT"
                    and response.url == origin + "/api/settings",
                    timeout=10_000,
                ):
                    save.click()
                sheet.locator('[data-ui="本机配置.sheet.close"]').click()
                sheet.wait_for(state="detached", timeout=10_000)

                page.locator('[data-ui="顶栏.settings"]').click()
                reopened = page.locator('[data-ui="本机配置.root"]')
                reopened.wait_for(state="visible", timeout=10_000)
                read_back = (
                    reopened.locator('[data-ui="本机配置.role"]')
                    .filter(has_text="reviewer")
                    .locator('[data-ui="本机配置.role.model"]')
                    .input_value()
                )
                if len(settings_reads) != 2:
                    raise AssertionError(
                        f"opening settings twice made {len(settings_reads)} GET /api/settings requests"
                    )
                if read_back != expected:
                    raise AssertionError(
                        f"saved reviewer.model read back {read_back!r}, expected {expected!r}"
                    )
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
