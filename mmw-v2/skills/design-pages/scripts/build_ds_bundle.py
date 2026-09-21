#!/usr/bin/env python3
"""Bundle a design system's components into `_ds_bundle.js`, the file pages mount from.

Usage: build_ds_bundle.py <design-system dir> --namespace <Namespace> [--out <file>]

Every `components/**/<Name>.jsx` (PascalCase stem) is bundled by esbuild into one
classic script that sets `window.<Namespace>.<Name>` for each export, the shape a page
mounts with `<x-import component-from-global-scope="<Namespace>.<Name>">`. The
namespace is the one Claude Design gave the design system: the `window.` name in the
first lines of the placeholder `_ds_bundle.js` a new design system starts with.

React is read from `window.React` when a component renders, not when the bundle
loads: the page runtime loads React after the bundle's `<script>` has run
(measured 2026-09-21 on the live preview, `support.js` 66404 bytes).

The first line is the `@ds-bundle` header Claude Design writes on its own bundles
(format 4), listing the components. esbuild runs through `npx`, pinned below.

Exit 0 prints `bundled <n> components into <file>`; 1 when esbuild fails (its error
follows); 2 on a usage error, a directory with no component, or no `npx`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ESBUILD = "esbuild@0.28.2"
SHIM = """export default new Proxy({}, {get: (_, key) => window.React[key]});
"""


def components(root: Path) -> list[Path]:
    return sorted(p for p in root.glob("components/**/*.jsx") if p.stem[:1].isupper())


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("root")
    parser.add_argument("--namespace", required=True)
    parser.add_argument("--out")
    args = parser.parse_args(argv[1:])
    root = Path(args.root).resolve()
    if not re.fullmatch(r"[A-Za-z_$][\w$]*", args.namespace):
        print(f"--namespace {args.namespace!r} is not a JavaScript identifier", file=sys.stderr)
        return 2
    found = components(root)
    if not found:
        print(f"{root}: no components/**/<Name>.jsx to bundle", file=sys.stderr)
        return 2
    npx = shutil.which("npx")
    if not npx:
        print("npx is not on PATH; install Node.js to bundle components", file=sys.stderr)
        return 2
    out = Path(args.out).resolve() if args.out else root / "_ds_bundle.js"
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        (work / "react-shim.js").write_text(SHIM, encoding="utf-8")
        entry = work / "entry.js"
        entry.write_text("".join(f'export * from "{p.as_posix()}";\n' for p in found), encoding="utf-8")
        built = work / "bundle.js"
        cmd = [npx, "--yes", ESBUILD, str(entry), "--bundle", "--format=iife", "--global-name=__ds",
               "--jsx=transform", "--jsx-factory=React.createElement",
               f"--alias:react={(work / 'react-shim.js').as_posix()}", f"--outfile={built}",
               "--log-level=error"]
        run = subprocess.run(cmd, capture_output=True, text=True, cwd=tmp)
        if run.returncode != 0:
            print(run.stderr.strip() or run.stdout.strip(), file=sys.stderr)
            return 1
        header = {
            "format": 4, "namespace": args.namespace,
            "components": [p.stem for p in found],
            "sourceHashes": {p.stem: hashlib.sha256(p.read_bytes()).hexdigest()[:16] for p in found},
            "inlinedExternals": [], "unexposedExports": [],
        }
        body = built.read_text(encoding="utf-8")
        out.write_text(
            f"/* @ds-bundle: {json.dumps(header, separators=(',', ':'))} */\n{body}"
            f"window.{args.namespace} = Object.assign(window.{args.namespace} || {{}}, __ds);\n",
            encoding="utf-8")
    print(f"bundled {len(found)} components into {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
