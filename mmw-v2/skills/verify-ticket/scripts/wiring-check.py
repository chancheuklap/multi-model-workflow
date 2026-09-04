#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.58", "pyyaml>=6"]
# ///
"""Check that controls on a running interface do what their screen-contract rows say.

    wiring-check.py --contract <screen-contract.yaml> --rows <id,id> [--negative]

For each row: put the product into the row's `reach` state through the repository's
own reach script, open the row's `route`, reload, trigger the control by role and
accessible name, then read every `observe` line through the target's read surface.
Prints `WIRING OK <n>/<n>` (exit 0) or one `MISS <row> — <reason>` per failing row
(exit 1); exit 2 when the run could not start. Addresses, the reach script and the way
to reach the product come from `.mmw/target.json` through `screen_driver.py` beside
this script; nothing about the machine is on the command line.

An `observe` line reads a persistent surface freshly, on a path the acting view did not
produce, after the action completed. On a target with a JSON read surface it is
`METHOD /path -> <jq-style expression>`. On a server-rendered target without one it is
`GET /path -> node <role> "<name>" exists`, read from a second tab in the same session
and normalised the way interface parity normalises a tree. The reference beside this
script, references/wiring-check.md, is where the lines are read.

`--negative` is the wiring check's own control: the repository's `transport_off`
command breaks the state transport, every row is run once more, and every one of them
must fail on an `observe` assertion — a specific `MISS <row> — … was …`, not a run that
could not attach. It proves the thing that matters: an `observe` line cannot go green
without something having been persisted. Prints `WIRING NEGATIVE OK <n>/<n>`; a row that
still passed, or a run that failed before any `observe` was evaluated, is exit 1 or 2.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


def _load_driver():
    here = Path(__file__).resolve().parent / "screen_driver.py"
    spec = importlib.util.spec_from_file_location("screen_driver", here)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["screen_driver"] = mod
    spec.loader.exec_module(mod)
    return mod


sd = _load_driver()

# Re-exported for the tests.
evaluate = sd.evaluate
evaluate_tree = sd.evaluate_tree
fill = sd.fill


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="wiring-check.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--contract", required=True, metavar="FILE")
    p.add_argument("--rows", required=True, metavar="IDS")
    p.add_argument("--negative", action="store_true",
                   help="break the state transport and require every row to MISS on an "
                        "observe assertion")
    return p


def run_rows(adapter, pw, wanted: list[str], by_id: dict[str, dict],
             viewport: tuple[int, int]) -> tuple[list[str], list[str]]:
    """`(misses, observed)`: the `MISS` lines, and the ids of rows whose observe lines
    were evaluated at all (so a negative run can tell a miss from a run that never got
    that far)."""
    misses: list[str] = []
    observed: list[str] = []
    page = None
    try:
        for rid in wanted:
            row = by_id[rid]
            ok, why = adapter.ready()
            if not ok:
                misses.append(f"MISS {rid} — not ready: {why}")
                continue
            reach = [str(row["reach"])] if row.get("reach") else []
            values = adapter.transport(reach, {})
            if page is None or adapter.reach_before_attach:
                if page is not None:
                    adapter.release()
                page = adapter.attach(pw, values)
            sd.resize(page, viewport, adapter.over_cdp)
            sd.navigate(page, adapter.address(row.get("route") or "", values), reload=True)
            trig = row["trigger"]
            control = page.get_by_role(trig["role"], name=trig["name"], exact=True)
            if control.count() == 0:
                misses.append(f'MISS {rid} — no control {trig["role"]} "{trig["name"]}"')
                continue
            control.first.click()
            sd.run_clock(page, sd.SETTLE_VIRTUAL_MS)
            # The action's own request has to leave the page before the read is fresh.
            page.wait_for_load_state("networkidle")
            observed.append(rid)
            for line in row["observe"]:
                ok, got, why = adapter.observe(str(line), values)
                if not ok:
                    misses.append(f"MISS {rid} — {why}")
                    break
    finally:
        adapter.release()
    return misses, observed


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = sd.repo_root()
    doc = sd.load_contract(Path(args.contract))
    by_id = sd.rows_by_id(doc)
    wanted = [s.strip() for s in args.rows.split(",") if s.strip()]
    missing = [w for w in wanted if w not in by_id]
    if missing:
        print(f"rows not in contract: {', '.join(missing)}", file=sys.stderr)
        return 2
    for w in wanted:
        if not by_id[w].get("observe"):
            print(f"row {w} has no observe lines; nothing a machine can check", file=sys.stderr)
            return 2
    adapter = sd.adapter_for(doc, root)
    viewport = sd.parse_viewports(doc["viewports"])[0]

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        if not args.negative:
            misses, _ = run_rows(adapter, pw, wanted, by_id, viewport)
            for m in misses:
                print(m)
            if misses:
                return 1
            print(f"WIRING OK {len(wanted)}/{len(wanted)}")
            return 0
        adapter.transport_off()
        try:
            misses, observed = run_rows(adapter, pw, wanted, by_id, viewport)
        finally:
            adapter.transport_on()
    missed = {m.split(" ", 2)[1] for m in misses}
    not_observed = [w for w in wanted if w not in observed]
    if not_observed:
        print(f"negative control proved nothing: no observe line was evaluated for "
              f"{', '.join(not_observed)} (the run failed before it read anything)",
              file=sys.stderr)
        for m in misses:
            print(m, file=sys.stderr)
        return 2
    still_green = [w for w in wanted if w not in missed]
    if still_green:
        for w in still_green:
            print(f"GREEN WITHOUT TRANSPORT {w} — its observe lines held with the state "
                  f"transport broken; the read surface is not fed from persisted state")
        return 1
    for m in misses:
        print(m)
    print(f"WIRING NEGATIVE OK {len(wanted)}/{len(wanted)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
