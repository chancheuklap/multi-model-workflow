import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS / "dispatch" / "scripts"))
EVENTS = TOOLS / "verify-ticket" / "scripts" / "events.py"


def load_events():
    spec = importlib.util.spec_from_file_location("v5_events_for_tests", EVENTS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_tool(group, name):
    path = TOOLS / group / "scripts" / name
    spec = importlib.util.spec_from_file_location("v5_" + name.replace(".", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
