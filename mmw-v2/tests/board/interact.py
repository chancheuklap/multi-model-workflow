"""Accessible Playwright interactions shared by board boundary tests."""

from __future__ import annotations

import os


def _control(page, role: str, name: str):
    return page.get_by_role(role, name=name, exact=True)


def click(page, role: str, name: str) -> None:
    if os.environ.get("MMW_NEGATIVE") == "1":
        return
    _control(page, role, name).click()


def fill(page, role: str, name: str, value: str) -> None:
    if os.environ.get("MMW_NEGATIVE") == "1":
        return
    _control(page, role, name).fill(value)


def select(page, role: str, name: str, value: str) -> None:
    if os.environ.get("MMW_NEGATIVE") == "1":
        return
    _control(page, role, name).select_option(value)
