from __future__ import annotations

import os
import sys

from playwright.sync_api import sync_playwright


def choose_another_model(row):
    select = row.locator('[data-ui="本机配置.role.model"]')
    current = select.input_value()
    choices = select.locator("option:not(:disabled)").evaluate_all(
        "options => options.map(option => option.value)"
    )
    alternative = next((choice for choice in choices if choice and choice != current), None)
    if alternative is None:
        raise AssertionError(f"reviewer.model has no legal alternative to {current!r}")
    select.select_option(alternative)
    return alternative


def main() -> int:
    origin = os.environ["ORIGIN"].rstrip("/")
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
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
            browser.close()
    except Exception as exc:
        print(f"settings-save failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
