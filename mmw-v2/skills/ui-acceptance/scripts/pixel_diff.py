#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["Pillow>=10"]
# ///
"""Write the pixel difference image kept as story-parity evidence.

Element facts decide story parity. This module produces an image for a person to
inspect and makes no pass/fail decision. Invoking it as a command exits 2 and names
the judge that uses it.
"""

from __future__ import annotations

import sys
from pathlib import Path


def pixel_diff(design: Path, product: Path, out: Path) -> Path:
    """Write the absolute RGB difference of two renders on their combined canvas."""
    from PIL import Image, ImageChops

    with Image.open(design) as opened:
        left = opened.convert("RGB")
    with Image.open(product) as opened:
        right = opened.convert("RGB")
    size = (max(left.width, right.width), max(left.height, right.height))
    left_canvas = Image.new("RGB", size, "black")
    right_canvas = Image.new("RGB", size, "black")
    left_canvas.paste(left, (0, 0))
    right_canvas.paste(right, (0, 0))
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    ImageChops.difference(left_canvas, right_canvas).save(out)
    return out


def main(argv: list[str] | None = None) -> int:
    print("pixel_diff.py only writes evidence; "
          "run story-parity.py --contract FILE --pages ID[,ID]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
