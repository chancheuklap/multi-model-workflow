"""Playwright interactions addressed by the screen contract's data-ui ids."""

from __future__ import annotations

import json
import os


def _control(page, data_ui: str):
    selector = f"[data-ui={json.dumps(data_ui, ensure_ascii=False)}]"
    return page.locator(selector).first


def click(page, data_ui: str) -> None:
    if os.environ.get("MMW_NEGATIVE") == "1":
        return
    _control(page, data_ui).click()


def fill(page, data_ui: str, value: str) -> None:
    if os.environ.get("MMW_NEGATIVE") == "1":
        return
    _control(page, data_ui).fill(value)


def select(page, data_ui: str, value: str) -> None:
    if os.environ.get("MMW_NEGATIVE") == "1":
        return
    _control(page, data_ui).select_option(value)
