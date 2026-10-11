"""Playwright interactions addressed by the screen contract's data-ui ids."""

from __future__ import annotations

import json
import os
import re


def _control(page, data_ui: str):
    repeated = re.fullmatch(r"(.+)#([1-9][0-9]*)", data_ui)
    control_id = repeated.group(1) if repeated else data_ui
    index = int(repeated.group(2)) - 1 if repeated else 0
    selector = f"[data-ui={json.dumps(control_id, ensure_ascii=False)}]"
    return page.locator(selector).nth(index)


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
