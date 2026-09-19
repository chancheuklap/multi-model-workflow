#!/usr/bin/env python3
# Asserts calls, shows, next and on_failure of one row. The helper does
# nothing under MMW_NEGATIVE=1.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from product import (
    EXPECTED_CALL,
    FAILURE,
    MARKED_BODY,
    NEXT_SCENE,
    InteractionHelper,
    Page,
)

page = Page()
InteractionHelper(page).click("save-note")
assert page.outbound.calls, "calls: no outbound call"
assert page.outbound.calls[-1] == EXPECTED_CALL, (
    f"calls: {page.outbound.calls[-1]!r} != {EXPECTED_CALL!r}"
)
assert page.displayed.get("body") == MARKED_BODY, (
    f"shows: {page.displayed.get('body')!r} != {MARKED_BODY!r}"
)
assert page.scene == NEXT_SCENE, f"next: {page.scene!r} != {NEXT_SCENE!r}"

failed = Page(fail=True)
InteractionHelper(failed).click("save-note")
assert failed.failure == FAILURE, f"on_failure: {failed.failure!r} != {FAILURE!r}"
