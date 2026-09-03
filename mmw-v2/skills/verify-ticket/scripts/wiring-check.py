#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.48", "pyyaml>=6"]
# ///
"""Check that controls on a running interface do what their screen-contract rows say.

  wiring-check.py --contract <screen-contract.yaml> --rows <id,id> --cdp <url> --impl <url>
                  --backend <url> [--seed "<command>"] [--impl-title <text>]

For each row: reload, open the row's route, trigger the control by role and accessible
name, then read every `observe` line against the backend. Prints `WIRING OK <n>/<n>`
(exit 0) or one `MISS <row> — <reason>` per failing row (exit 1); exit 2 when the run
could not start. The reference beside this script, references/wiring-check.md, is where
the lines are read.
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
import urllib.error
import urllib.request

import yaml

PLACEHOLDER = re.compile(r"\{(\w+)\}")


def api(base: str, method: str, path: str) -> tuple[int, object]:
    req = urllib.request.Request(base.rstrip("/") + path, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        return e.code, None


def evaluate(expr: str, body: object) -> tuple[bool, object]:
    """`.a.b[0] == "x"`, `.a != 1`, `.a contains "x"`, `.a exists`, or a bare `.a` (truthy)."""
    m = re.match(r"^\s*(\.[\w.\[\]]*)\s*(?:(==|!=|contains|exists)\s*(.*))?$", expr)
    if not m:
        raise ValueError(f"cannot read expression {expr!r}")
    value: object = body
    for part in re.findall(r"\.(\w+)|\[(\d+)\]", m.group(1)):
        key, idx = part
        try:
            value = value[key] if key else value[int(idx)]
        except (KeyError, IndexError, TypeError):
            value = None
            break
    op, rhs = m.group(2), (m.group(3) or "").strip()
    if op is None:
        return bool(value), value
    if op == "exists":
        return value is not None, value
    want = json.loads(rhs) if rhs else None
    if op == "==":
        return value == want, value
    if op == "!=":
        return value != want, value
    return (want in value) if isinstance(value, (str, list)) else False, value


def fill(text: str, values: dict[str, str]) -> str:
    def sub(m: re.Match) -> str:
        return values.get(m.group(1), m.group(0))
    return PLACEHOLDER.sub(sub, text)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--contract", required=True)
    p.add_argument("--rows", required=True)
    p.add_argument("--cdp", required=True)
    p.add_argument("--impl", required=True)
    p.add_argument("--backend", required=True)
    p.add_argument("--seed", default=None)
    p.add_argument("--impl-title", default=None)
    args = p.parse_args(argv)

    with open(args.contract, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    by_id = {r["id"]: r for r in doc.get("rows") or []}
    wanted = [s.strip() for s in args.rows.split(",") if s.strip()]
    missing = [w for w in wanted if w not in by_id]
    if missing:
        print(f"rows not in contract: {', '.join(missing)}", file=sys.stderr)
        return 2
    for w in wanted:
        if not by_id[w].get("observe"):
            print(f"row {w} has no observe lines; nothing a machine can check", file=sys.stderr)
            return 2

    values: dict[str, str] = {}
    if args.seed:
        run = subprocess.run(shlex.split(args.seed), capture_output=True, text=True)
        if run.returncode != 0:
            print(f"seed exited {run.returncode}: {run.stderr.strip()}", file=sys.stderr)
            return 2
        for line in run.stdout.splitlines():
            k, _, v = line.partition("=")
            if k.strip() and _:
                values[k.strip()] = v.strip()

    status, _ = api(args.backend, "GET", "/health")
    if status >= 400:
        print(f"no backend answering {args.backend}/health ({status})", file=sys.stderr)
        return 2

    from playwright.sync_api import sync_playwright
    misses: list[str] = []
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.connect_over_cdp(args.cdp, timeout=10000)
        except Exception as exc:  # noqa: BLE001
            print(f"no application on {args.cdp}: {exc}", file=sys.stderr)
            return 2
        pages = [pg for c in browser.contexts for pg in c.pages]
        if args.impl_title:
            pages = [pg for pg in pages if args.impl_title in pg.title()]
        if not pages:
            print("no page to drive over CDP", file=sys.stderr)
            return 2
        page = pages[0]
        home = page.url
        try:
            for rid in wanted:
                row = by_id[rid]
                route = row.get("route") or ""
                page.goto(args.impl.rstrip("/") + "/" + route.lstrip("/"), wait_until="networkidle")
                page.reload(wait_until="networkidle")
                page.wait_for_timeout(500)
                trig = row["trigger"]
                control = page.get_by_role(trig["role"], name=trig["name"], exact=True)
                if control.count() == 0:
                    misses.append(f'MISS {rid} — no control {trig["role"]} "{trig["name"]}"')
                    continue
                control.first.click()
                page.wait_for_timeout(1000)
                for line in row["observe"]:
                    op, _, expr = line.partition("->")
                    method, _, path = op.strip().partition(" ")
                    status, body = api(args.backend, method.upper(), fill(path.strip(), values))
                    if status >= 300:
                        misses.append(f"MISS {rid} — {op.strip()} answered {status}")
                        break
                    ok, got = evaluate(expr.strip(), body)
                    if not ok:
                        misses.append(f"MISS {rid} — {expr.strip()} was {json.dumps(got, ensure_ascii=False)}")
                        break
        finally:
            page.goto(home, wait_until="networkidle")
    for m in misses:
        print(m)
    passed = len(wanted) - len(misses)
    if misses:
        return 1
    print(f"WIRING OK {passed}/{len(wanted)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
