#!/usr/bin/env python3
# A calls=none row whose next is not stay: the click emits no outbound call
# and the page enters that next. The helper does nothing under MMW_NEGATIVE=1.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from product import NONE_NEXT, InteractionHelper, Page

page = Page()
InteractionHelper(page).click("open-panel")
assert page.outbound.calls == [], f"calls: {page.outbound.calls!r}"
assert page.scene == NONE_NEXT, f"next: {page.scene!r} != {NONE_NEXT!r}"
