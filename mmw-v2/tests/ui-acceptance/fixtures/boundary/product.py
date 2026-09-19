"""Fake consuming-repository product for four-column and cross-component samples.

The outbound call module is the layer that emits outbound calls. The page
holds displayed values, scene, failure copy, and two regions. The interaction
helper finds a control by its data-ui id and does nothing under MMW_NEGATIVE=1.
"""
from __future__ import annotations

import os
from typing import Any, Callable


EXPECTED_CALL = {
    "method": "POST",
    "path": "/api/notes/1",
    "params": {"title": "hello"},
}
MARKED_BODY = "MARKED_BODY"
NEXT_SCENE = "saved"
FAILURE = "toast:NEXT_FAILED_TITLE"
NONE_NEXT = "panel-open"
MARKED_SELECTED = "MARKED_NOTE_42"
CROSS_NEXT = "filtered"


class OutboundCallModule:
    def __init__(self, *, fail: bool = False) -> None:
        self.calls: list[dict[str, Any]] = []
        self.fail = fail

    def call(self, method: str, path: str, params: dict[str, Any]) -> dict[str, Any]:
        self.calls.append({"method": method, "path": path, "params": params})
        if self.fail:
            return {"ok": False, "error": FAILURE}
        return {"ok": True, "body": MARKED_BODY}


class Page:
    def __init__(self, *, fail: bool = False) -> None:
        self.scene = "edit"
        self.displayed: dict[str, str] = {}
        self.failure: str | None = None
        self.title = "hello"
        self.outbound = OutboundCallModule(fail=fail)
        self.regions: dict[str, dict[str, Any]] = {
            "filters": {
                "scene": "idle",
                "controls": {"apply-filter": self._on_apply_filter},
            },
            "list": {
                "selected_id": "note-7",
                "scene": "idle",
            },
        }
        self.controls = {
            "save-note": self._on_save,
            "open-panel": self._on_open_panel,
        }

    def handler_for(self, data_ui: str) -> Callable[[], None]:
        if data_ui in self.controls:
            return self.controls[data_ui]
        for region in self.regions.values():
            handler = region.get("controls", {}).get(data_ui)
            if handler is not None:
                return handler
        raise KeyError(f"no control with data-ui={data_ui}")

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
        other = self.regions["list"]
        self.outbound.call(
            "POST", "/api/filter", {"selected_id": other["selected_id"]}
        )
        other["scene"] = CROSS_NEXT


class InteractionHelper:
    def __init__(self, page: Page) -> None:
        self.page = page

    def click(self, data_ui: str) -> None:
        if os.environ.get("MMW_NEGATIVE") == "1":
            return
        self.page.handler_for(data_ui)()
