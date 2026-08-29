"""Load verify-ticket.py as a module; its filename is not a Python identifier."""

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify-ticket.py"


def load():
    spec = importlib.util.spec_from_file_location("verify_ticket", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
