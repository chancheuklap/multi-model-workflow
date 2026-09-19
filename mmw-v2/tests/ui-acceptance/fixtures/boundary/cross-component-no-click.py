#!/usr/bin/env python3
# Writes the expected request and the list region's scene after the click, so
# the assertions stay true when the helper does nothing.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from product import CROSS_NEXT, MARKED_SELECTED, InteractionHelper, Page

expected = {
    "method": "POST",
    "path": "/api/filter",
    "params": {"selected_id": MARKED_SELECTED},
}

page = Page()
page.regions["list"]["selected_id"] = MARKED_SELECTED
InteractionHelper(page).click("apply-filter")
page.outbound.calls = [dict(expected)]
page.regions["list"]["scene"] = CROSS_NEXT
assert page.outbound.calls, "calls: no outbound call"
assert page.outbound.calls[-1] == expected, (
    f"calls: {page.outbound.calls[-1]!r} != {expected!r}"
)
assert page.regions["list"]["scene"] == CROSS_NEXT, (
    f"next: {page.regions['list']['scene']!r} != {CROSS_NEXT!r}"
)
