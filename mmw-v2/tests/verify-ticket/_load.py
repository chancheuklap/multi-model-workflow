"""Load the shared criteria engine and build independent tracker-history fixtures.

Every loaded engine stubs ticket_spec to return None, so event fixtures never reach
GitHub. The mmw suite reuses these fixtures while directly importing ticket_state.
"""

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "verify-ticket" / "scripts" / "verify-ticket.py"
EVENTS = SCRIPT.parents[2] / "mmw" / "scripts" / "events.py"
UI_ACCEPTANCE = SCRIPT.parents[2] / "ui-acceptance" / "scripts"
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


def started(ticket=77, **fields):
    """One readable `worker.started`, with caller overrides for the field under test."""
    payload = dict(session=f"wk-{ticket}", runner="paseo", machine="mac-1", host="codex",
                   model="gpt-5", effort="high", grade="senior-worker",
                   worktree=f"/repo/.worktrees/issue-{ticket}", branch=f"issue-{ticket}",
                   base="0" * 40)
    payload.update(fields)
    return event("worker.started", "Worker started", ticket=ticket, **payload)


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
    if run == "reverify":
        actor = fields.setdefault("actor", "worker")
        fields.setdefault("stage", _events.checked_stage(run, actor))
    payload = {"run": run, "commit": commit, "result": result,
               "counts": _vt.tally(criteria, abandons), "criteria": results,
               "failed": failed,
               "shape": _vt.shape_digest([row for row in lines
                                          if not row.startswith("ABANDON:")])}
    payload.update(fields)
    return _events.build("ticket.checked", ticket=ticket,
                         line=f"{run} on {commit[:12]}: {summary or result}", text=text,
                         at=AT, **payload)


def current_evidence(check: str, expect: str) -> str:
    """A pass line as gate-check writes it for this CHECK and EXPECT with no CWD:
    `definition-sha256` is `gateDefinitionDigest` in `mmw-v2/upstream-unlazy/scripts/lib/gates.mjs`."""
    definition = json.dumps(["unlazy.gate-definition", 1, check, expect, None],
                            separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(definition.encode("utf-8")).hexdigest()
    return (f"automatic-evidence=v1; definition-sha256={digest}; exit=0; EXPECT=matched; "
            f"output-sha256={'a' * 64}; output-bytes=13; shell=/bin/sh; cwd=.")

def ticket(*criteria: str, owns: str = "- src/**") -> str:
    return "## Owns\n\n" + owns + "\n\n## Acceptance criteria\n\n" + "\n".join(criteria) + "\n"

def payload_of(comment: str) -> dict:
    what, payload = _events.parse(comment)
    assert what == "event", (what, payload, comment)
    return payload

def git_repo(root: Path):
    """A repository with one commit at `root`; returns a function running git there."""
    def sh(*args, cwd=root):
        subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)

    sh("init", "-q", "-b", "main")
    sh("config", "user.email", "t@t")
    sh("config", "user.name", "t")
    return sh

def lease_in(home: Path):
    """`lease.py` of the ui-acceptance skill, its registry under `home`, not ~/.mmw."""
    spec = importlib.util.spec_from_file_location(f"lease_for_tests_{id(home)}",
                                                  UI_ACCEPTANCE / "lease.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # `lease.py` asks `home()` for the root every time it needs a path, so the test's
    # own root is given by replacing that one reader, not by writing paths into it.
    module.home = lambda: home
    return module
