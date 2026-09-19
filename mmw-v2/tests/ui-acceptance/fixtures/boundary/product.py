"""Fake consuming-repository product for four-column and cross-component samples.

The outbound call module is the layer that emits outbound calls. The page
holds displayed values, scene, failure copy, and two regions. The interaction
helper finds a control by its data-ui id and does nothing under MMW_NEGATIVE=1.
"""
from __future__ import annotations

import os
from typing import Any


EXPECTED_CALL = {
    "method": "POST",
    "path": "/api/notes/1",
    "params": {"title": "hello"},
}
MARKED_BODY = "MARKED_BODY"
NEXT_SCENE = "saved"
FAILURE = "toast:NEXT_FAILED_TITLE"
NONE_NEXT = "panel-open"

CROSS_CALL = {
    "method": "POST",
    "path": "/api/filter",
    "params": {"selected_id": "note-7"},
}
CROSS_NEXT = "filtered"


class OutboundCallModule:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self._mode = "success"
        self.success_payload = {"body": MARKED_BODY}
        self.failure_payload = {"error": FAILURE}

    def fail_next(self) -> None:
        self._mode = "failure"

    def call(self, method: str, path: str, params: dict[str, Any]) -> dict[str, Any]:
        self.calls.append({"method": method, "path": path, "params": params})
        if self._mode == "failure":
            return {"ok": False, **self.failure_payload}
        return {"ok": True, **self.success_payload}


class Page:
    def __init__(self) -> None:
        self.scene = "edit"
        self.displayed: dict[str, str] = {}
        self.failure: str | None = None
        self.title = "hello"
        self.regions = {
            "list": {"selected_id": "note-7", "scene": "idle"},
            "detail": {"scene": "idle"},
        }
        self.outbound = OutboundCallModule()
        self.controls = {
            "save-note": self._on_save,
            "open-panel": self._on_open_panel,
            "apply-filter": self._on_apply_filter,
        }

    def _on_save(self) -> None:
        result = self.outbound.call("POST", "/api/notes/1", {"title": self.title})
        if result["ok"]:
            self.displayed["body"] = result["body"]
            self.scene = NEXT_SCENE
            self.failure = None
        else:
            self.failure = result["error"]

    def _on_open_panel(self) -> None:
        self.scene = NONE_NEXT

    def _on_apply_filter(self) -> None:
        selected = self.regions["list"]["selected_id"]
        result = self.outbound.call(
            "POST", "/api/filter", {"selected_id": selected}
        )
        if result["ok"]:
            self.regions["detail"]["scene"] = CROSS_NEXT
            self.displayed["body"] = result["body"]
            self.scene = CROSS_NEXT
            self.failure = None
        else:
            self.failure = result["error"]


class InteractionHelper:
    def __init__(self, page: Page) -> None:
        self.page = page

    def click(self, data_ui: str) -> None:
        if os.environ.get("MMW_NEGATIVE") == "1":
            return
        handler = self.page.controls.get(data_ui)
        if handler is None:
            raise KeyError(f"no control with data-ui={data_ui}")
        handler()


def four_columns(*, wrong: str | None = None,
                 overwrite_after_click: bool = False) -> None:
    expected_call: dict[str, Any] = dict(EXPECTED_CALL)
    expected_shows = MARKED_BODY
    expected_next = NEXT_SCENE
    expected_failure = FAILURE
    if wrong == "calls":
        expected_call = {**expected_call, "path": "/api/wrong"}
    elif wrong == "shows":
        expected_shows = "WRONG_BODY"
    elif wrong == "next":
        expected_next = "wrong-scene"
    elif wrong == "on_failure":
        expected_failure = "wrong-failure"
    elif wrong is not None:
        raise ValueError(wrong)

    page = Page()
    InteractionHelper(page).click("save-note")
    if overwrite_after_click:
        page.outbound.calls = [dict(EXPECTED_CALL)]
        page.displayed["body"] = MARKED_BODY
        page.scene = NEXT_SCENE

    assert page.outbound.calls, "calls: no outbound call"
    got_call = page.outbound.calls[-1]
    assert got_call == expected_call, f"calls: {got_call!r} != {expected_call!r}"
    got_shows = page.displayed.get("body")
    assert got_shows == expected_shows, f"shows: {got_shows!r} != {expected_shows!r}"
    assert page.scene == expected_next, f"next: {page.scene!r} != {expected_next!r}"

    failed = Page()
    failed.outbound.fail_next()
    InteractionHelper(failed).click("save-note")
    if overwrite_after_click:
        failed.failure = FAILURE
    assert failed.failure == expected_failure, (
        f"on_failure: {failed.failure!r} != {expected_failure!r}"
    )

    if wrong is None and not overwrite_after_click:
        none_page = Page()
        InteractionHelper(none_page).click("open-panel")
        assert none_page.outbound.calls == [], (
            f"calls none: {none_page.outbound.calls!r}"
        )
        assert none_page.scene == NONE_NEXT, (
            f"next: {none_page.scene!r} != {NONE_NEXT!r}"
        )


def cross_component(*, overwrite_after_click: bool = False) -> None:
    page = Page()
    InteractionHelper(page).click("apply-filter")
    if overwrite_after_click:
        page.outbound.calls = [dict(CROSS_CALL)]
        page.regions["detail"]["scene"] = CROSS_NEXT

    assert page.outbound.calls, "calls: no outbound call"
    got_call = page.outbound.calls[-1]
    assert got_call == CROSS_CALL, f"calls: {got_call!r} != {CROSS_CALL!r}"
    got_scene = page.regions["detail"]["scene"]
    assert got_scene == CROSS_NEXT, f"next: {got_scene!r} != {CROSS_NEXT!r}"
