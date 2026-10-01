"""Directly import ticket_state; reuse the shared tracker-history fixtures."""

import importlib.util
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "mmw" / "scripts" / "ticket_state.py"
EVENTS = SCRIPT.parent / "events.py"

_fixture_path = Path(__file__).resolve().parents[1] / "verify-ticket" / "_load.py"
_fixture_spec = importlib.util.spec_from_file_location("criteria_test_fixtures", _fixture_path)
fixtures = importlib.util.module_from_spec(_fixture_spec)
_fixture_spec.loader.exec_module(fixtures)


def load():
    sys.path.insert(0, str(SCRIPT.parent))
    import ticket_state
    ticket_state.engine.ticket_spec = lambda number: None
    return ticket_state


load_events = fixtures.load_events
event = fixtures.event
started = fixtures.started
checked = fixtures.checked
current_evidence = fixtures.current_evidence
ticket = fixtures.ticket
payload_of = fixtures.payload_of
git_repo = fixtures.git_repo
lease_in = fixtures.lease_in
AT = fixtures.AT
