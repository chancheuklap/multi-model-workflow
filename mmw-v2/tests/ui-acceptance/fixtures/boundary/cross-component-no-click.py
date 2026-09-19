#!/usr/bin/env python3
# Writes the expected request and the other region's scene after the click, so
# the assertions stay true when the helper does nothing.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from product import cross_component

cross_component(overwrite_after_click=True)
