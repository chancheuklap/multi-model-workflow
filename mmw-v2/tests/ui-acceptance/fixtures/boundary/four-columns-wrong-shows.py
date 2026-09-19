#!/usr/bin/env python3
# Same four-column assertions as the honest sample; the shows expected value is wrong.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from product import EXPECTED_CALL, FAILURE, NEXT_SCENE, InteractionHelper, Page

page = Page()
InteractionHelper(page).click("save-note")
assert page.outbound.calls, "calls: no outbound call"
assert page.outbound.calls[-1] == EXPECTED_CALL, (
    f"calls: {page.outbound.calls[-1]!r} != {EXPECTED_CALL!r}"
)
assert page.displayed.get("body") == "WRONG_BODY", (
    f"shows: {page.displayed.get('body')!r} != 'WRONG_BODY'"
)
assert page.scene == NEXT_SCENE, f"next: {page.scene!r} != {NEXT_SCENE!r}"

failed = Page(fail=True)
InteractionHelper(failed).click("save-note")
assert failed.failure == FAILURE, f"on_failure: {failed.failure!r} != {FAILURE!r}"
