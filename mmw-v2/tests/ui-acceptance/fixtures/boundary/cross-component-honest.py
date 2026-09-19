#!/usr/bin/env python3
# Cross-component row: the request carries the other region's state, and that
# region enters the named scene. The helper does nothing under MMW_NEGATIVE=1.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from product import cross_component

cross_component()
