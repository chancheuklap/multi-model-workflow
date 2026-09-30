"""A throwaway install target for the real install.sh.

Precedent: mmw-v2/tests/dispatch/test_install_orca_folder.py. MMW_V2_HOME
moves the whole install target, and orca and nmem on PATH answer only the
calls install.sh makes during an install. MMW_HOME is the same temporary
home, so a worker session's own ~/.mmw is not read or written.
"""

import os
import shutil
import subprocess
from pathlib import Path

MMW = Path(__file__).resolve().parents[2]
INSTALLER = MMW / "install.sh"

_STRIP = (
    "MMW_TICKET",
    "MMW_BASE_REF",
    "MMW_CATALOG_MODE",
    "MMW_SPEC",
    "MMW_TASK_SCOPE",
    "MMW_KIND",
    "MMW_EVENTS_PY",
    "PASEO_AGENT_ID",
    "ORCA_TERMINAL_HANDLE",
    "HERDR_PANE_ID",
    "CODEX_HOME",
    "PI_CODING_AGENT_DIR",
    "PI_HOME",
)


def write_fakes(bin_dir: Path) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)
    orca = bin_dir / "orca"
    orca.write_text(
        """#!/usr/bin/env python3
import json
import sys

args = sys.argv[1:]
if args[:2] == ["project", "setups"]:
    result = {"setups": []}
elif args[:2] == ["repo", "list"]:
    result = {"repos": [{
        "id": "folder_1",
        "path": "/Users/example",
        "displayName": "example",
        "kind": "folder",
        "externalWorktreeVisibility": None,
    }]}
else:
    raise SystemExit(f"unexpected orca call: {args}")
print(json.dumps({"ok": True, "result": result}))
""",
        encoding="utf-8",
    )
    orca.chmod(0o755)

    nmem = bin_dir / "nmem"
    nmem.write_text(
        """#!/usr/bin/env python3
import json
import sys

args = [arg for arg in sys.argv[1:] if arg != "--json"]
if args == ["spaces", "show", "mmw-toolbox"]:
    result = {"id": "mmw-toolbox", "name": "MMW Toolbox",
              "defaultRetrievalMode": "strict", "sharedSpaceIds": []}
elif args[:2] == ["agents", "show"] and args[2] in ("mmw-worker", "mmw-reviewer"):
    role = args[2].removeprefix("mmw-")
    result = {"id": args[2], "displayName": "MMW " + role.title(),
              "role": role, "defaultSpaceId": "mmw-toolbox"}
else:
    raise SystemExit(f"unexpected nmem call: {args}")
print(json.dumps(result))
""",
        encoding="utf-8",
    )
    nmem.chmod(0o755)


def run_install(installer: Path, home: Path, bin_dir: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    for name in list(env):
        if name in _STRIP or name.startswith("NMEM_"):
            env.pop(name, None)
    env["MMW_V2_HOME"] = str(home)
    env["MMW_HOME"] = str(home / ".mmw")
    env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    return subprocess.run(
        ["bash", str(installer)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def copy_mmw(scratch: Path) -> Path:
    """Copy this checkout's mmw-v2 to <scratch>/checkout/mmw-v2.

    The path has to contain a /mmw-v2/ segment: ours_skill_target claims a
    symlink only when its target has one.
    """
    dest = scratch / "checkout" / "mmw-v2"
    shutil.copytree(
        MMW,
        dest,
        symlinks=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    return dest
