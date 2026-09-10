"""Load verify-ticket.py as a module; its filename is not a Python identifier.

`event` writes a comment the way the pipeline's scripts post one, for fixtures that stand
for a ticket's history.
"""

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "verify-ticket" / "scripts" / "verify-ticket.py"
EVENTS = SCRIPT.parent / "events.py"


def load():
    spec = importlib.util.spec_from_file_location("verify_ticket", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_events():
    spec = importlib.util.spec_from_file_location("mmw_events_for_tests", EVENTS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_events = load_events()


def event(name, text, ticket=77, **fields):
    """`text` posted as event `name`: its first line, the rest of it, then the block."""
    first, _, rest = text.partition("\n")
    return _events.build(name, ticket=ticket, line=first, text=rest.strip("\n"),
                         at="2026-09-10T00:00:00Z", **fields)
