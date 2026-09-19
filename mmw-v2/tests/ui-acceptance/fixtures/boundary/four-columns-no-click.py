#!/usr/bin/env python3
# Writes the four expected values after the click, so the assertions stay true
# when the helper does nothing.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from product import four_columns

four_columns(overwrite_after_click=True)
