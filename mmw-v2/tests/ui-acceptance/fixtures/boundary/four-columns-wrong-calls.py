#!/usr/bin/env python3
# Same four-column assertions as the honest sample; the calls expected value is wrong.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from product import FAILURE, MARKED_BODY, NEXT_SCENE, InteractionHelper, Page

wrong_call = {
    "method": "POST",
    "path": "/api/wrong",
    "params": {"title": "hello"},
}

page = Page()
InteractionHelper(page).click("save-note")
assert page.outbound.calls, "calls: no outbound call"
assert page.outbound.calls[-1] == wrong_call, (
    f"calls: {page.outbound.calls[-1]!r} != {wrong_call!r}"
)
assert page.displayed.get("body") == MARKED_BODY, (
    f"shows: {page.displayed.get('body')!r} != {MARKED_BODY!r}"
)
assert page.scene == NEXT_SCENE, f"next: {page.scene!r} != {NEXT_SCENE!r}"

failed = Page(fail=True)
InteractionHelper(failed).click("save-note")
assert failed.failure == FAILURE, f"on_failure: {failed.failure!r} != {FAILURE!r}"
