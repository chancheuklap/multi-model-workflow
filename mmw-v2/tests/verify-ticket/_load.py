"""Load verify-ticket.py as a module; its filename is not a Python identifier.

`event` writes a comment the way the pipeline's scripts post one, for fixtures that stand
for a ticket's history; `checked` writes one run of a ticket's criteria as the
`ticket.checked` event `verify-ticket.py` posts for it.

Every module `load` returns asks nobody which spec a ticket sits under: `ticket_spec` —
the lookup `post_event` makes for an event's `spec` field — answers None, so no test
reaches the tracker through it. A test about that field patches `ticket_spec` itself.
"""

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "verify-ticket" / "scripts" / "verify-ticket.py"
EVENTS = SCRIPT.parent / "events.py"
AT = "2026-09-10T00:00:00Z"


def load():
    spec = importlib.util.spec_from_file_location("verify_ticket", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ticket_spec = lambda number: None
    return module


def load_events():
    spec = importlib.util.spec_from_file_location("mmw_events_for_tests", EVENTS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_events = load_events()
_vt = None


def event(name, text, ticket=77, **fields):
    """`text` posted as event `name`: its first line, the rest of it, then the block."""
    first, _, rest = text.partition("\n")
    return _events.build(name, ticket=ticket, line=first, text=rest.strip("\n"),
                         at=AT, **fields)


def checked(run, ledger, summary=None, ticket=77, commit="0" * 40, **fields):
    """One run of `ledger` (its lines, or its text) as a `ticket.checked` event.

    Each criterion's outcome and the counts are read off the ledger the way the run reads
    its own updated ledger; `summary` is gate-check's summary line, which sets the result
    (`ALL MET` met, `HANDOFF REQUIRED:` handoff, anything else unmet) — left out, the
    result is met exactly when every criterion is. The fingerprint is of these criteria,
    so a ticket body stating the same ones matches it.
    """
    global _vt
    if _vt is None:
        _vt = load()
    lines = ledger.splitlines() if isinstance(ledger, str) else list(ledger)
    lines = [row for block in lines for row in block.splitlines()]
    text = "\n".join(lines)
    criteria = _vt.parse_criteria(text)
    abandons = _vt.parse_abandons(text)
    results = [{"id": c["id"],
                "met": bool(c["ticked"] and c["evidence"] and c["evidence"] != "pending"),
                "evidence": c["evidence"] or "pending"} for c in criteria]
    failed = [r["id"] for r in results if not r["met"]]
    if summary is None:
        result = "unmet" if failed else "met"
    elif summary.startswith("ALL MET"):
        result = "met"
    elif summary.startswith("HANDOFF REQUIRED:"):
        result = "handoff"
    else:
        result = "unmet"
    payload = {"run": run, "commit": commit, "result": result,
               "counts": _vt.tally(criteria, abandons), "criteria": results,
               "failed": failed,
               "shape": _vt.shape_digest([row for row in lines
                                          if not row.startswith("ABANDON:")])}
    payload.update(fields)
    return _events.build("ticket.checked", ticket=ticket,
                         line=f"{run} on {commit[:12]}: {summary or result}", text=text,
                         at=AT, **payload)
