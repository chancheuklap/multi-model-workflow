#!/usr/bin/env python3
# Same four-column assertions as the honest sample; the shows expected value is wrong.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from product import four_columns

four_columns(wrong="shows")
