#!/usr/bin/env python3
# Cross-component row: apply-filter lives on the filters region; the request
# carries the list region's marked selected_id, and that region enters filtered.
# The helper does nothing under MMW_NEGATIVE=1.
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
assert page.outbound.calls, "calls: no outbound call"
assert page.outbound.calls[-1] == expected, (
    f"calls: {page.outbound.calls[-1]!r} != {expected!r}"
)
assert page.regions["list"]["scene"] == CROSS_NEXT, (
    f"next: {page.regions['list']['scene']!r} != {CROSS_NEXT!r}"
)
