"""Write a FastAPI application's OpenAPI document to a file, for repositories whose own
exporter does not cover the product.

Usage: uv run python dump_openapi.py <module>:<factory> <out.json>
       e.g. dump_openapi.py chameleon.runtime:create_app scratch/openapi.json
Run it from the repository root so the module imports.
"""
import importlib
import json
import sys
from pathlib import Path


def main(target: str, out: Path) -> None:
    module_name, _, factory_name = target.partition(":")
    if not factory_name:
        raise SystemExit("target must be <module>:<factory>")
    app = getattr(importlib.import_module(module_name), factory_name)()
    document = app.openapi()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(document, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{out}: {len(document.get('paths', {}))} paths")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], Path(sys.argv[2]).resolve())
