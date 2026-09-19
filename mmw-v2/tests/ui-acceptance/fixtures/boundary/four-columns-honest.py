#!/usr/bin/env python3
# Asserts calls, shows, next and on_failure of one row, plus a calls=none
# row whose next is not stay. The helper does nothing under MMW_NEGATIVE=1.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from product import four_columns

four_columns()
