"""A throwaway install target for the real mmw-v3/install.sh.

MMW_V3_HOME moves the whole install target and MMW_HOME the state directory to
the same temporary home, so no test reads or writes the machine's own home.
PATH is a fake `bin` in front of the system directories only: every service
install.sh may call (`orca`, `paseo`, `launchctl`, `nmem`) is a fake that logs
each call, and no binary the tester has installed elsewhere is reached.
`python3` in that `bin` is the interpreter running the tests. MMW_HOST_CATALOG
answers models.py's catalog scan from a file, so no host CLI is asked.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

MMW = Path(__file__).resolve().parents[2]
REPO = MMW.parent
INSTALLER = MMW / "install.sh"
SKILLS = MMW / "skills"
RUNNERS = SKILLS / "mmw-mode" / "scripts" / "runners"
SYSTEM_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"

# A session that runs these tests carries its own identity in these variables;
# none of them may reach the installer under test.
_STRIP = (
    "MMW_TICKET",
    "MMW_ROLE",
    "MMW_BASE_REF",
    "MMW_CATALOG_MODE",
    "MMW_HOST_CATALOG",
    "MMW_RUNNER",
    "MMW_SPEC",
    "MMW_TASK_SCOPE",
    "MMW_KIND",
    "MMW_EVENTS_PY",
    "MMW_V3_LAUNCHCTL",
    "PASEO_AGENT_ID",
    "PASEO_AGENT_CWD",
    "ORCA_TERMINAL_HANDLE",
    "HERDR_PANE_ID",
    "CODEX_HOME",
    "PI_CODING_AGENT_DIR",
    "PI_HOME",
    "GROK_AGENT",
    "GROK_HOOK_EVENT",
)


def adapter_uses(name: str) -> dict[str, list[str]]:
    """{"<subcommand>": [flags]} from one runner adapter's `# MMW_USES:` lines."""
    uses = {}
    for line in (RUNNERS / f"{name}.sh").read_text(encoding="utf-8").splitlines():
        if not line.startswith("# MMW_USES:"):
            continue
        tokens = line.split(":", 1)[1].split()
        command = " ".join(t for t in tokens if not t.startswith("-"))
        uses.setdefault(command, []).extend(t for t in tokens if t.startswith("-"))
    return uses


def host_catalog() -> dict:
    """One offered model per hosts.json default row, so the default rows validate."""
    offerings = {}
    defaults = json.loads((SKILLS / "mmw-mode" / "hosts.json").read_text())["defaults"]
    for row in defaults:
        name = row["model"].split("[")[0]
        offered = {"id": name.replace(" ", "-"), "name": name,
                   "thinkingOptionIds": ["low", "medium", "high", "xhigh"]}
        rows = offerings.setdefault(row["host"], [])
        if offered not in rows:
            rows.append(offered)
    return offerings


_LOG = """
def log(name):
    path = os.environ.get("MMW_TEST_SERVICE_LOG")
    if path:
        with open(path, "a") as out:
            out.write(json.dumps([name, *sys.argv[1:]]) + "\\n")
"""


def write_fakes(bin_dir: Path, *, repo_kind: str = "folder") -> None:
    """The fake services, the interpreter link and the host catalog, in `bin_dir`."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    (bin_dir / "python3").symlink_to(sys.executable)
    (bin_dir / "host-catalog.json").write_text(json.dumps(host_catalog()))

    orca_catalog = {"commands": [{"command": command, "flags": [f.lstrip("-") for f in flags]}
                                 for command, flags in adapter_uses("orca").items()]}
    executable(bin_dir / "orca", f"""#!/usr/bin/env python3
import json, os, sys
{_LOG}
log("orca")
args = sys.argv[1:]
if args[:2] == ["project", "setups"]:
    result = {{"setups": []}}
elif args[:2] == ["repo", "list"]:
    result = {{"repos": [{{
        "id": "repo_1",
        "path": "/Users/example",
        "displayName": "example",
        "kind": {repo_kind!r},
        "externalWorktreeVisibility": None,
    }}]}}
elif args == ["agent-context", "--json"]:
    print(json.dumps({json.dumps(orca_catalog)}))
    raise SystemExit(0)
else:
    raise SystemExit(f"unexpected orca call: {{args}}")
print(json.dumps({{"ok": True, "result": result}}))
""")

    executable(bin_dir / "paseo", f"""#!/usr/bin/env python3
import json, os, sys
{_LOG}
log("paseo")
USES = {json.dumps(adapter_uses("paseo"))}
args = sys.argv[1:]
if args and args[-1] in ("--help", "-h"):
    command = " ".join(args[:-1])
    if not command:
        print("Paseo fake\\n\\nUsage: paseo <command>")
    else:
        print(f"Usage: paseo {{command}} [options]\\n\\nOptions:")
        for flag in USES.get(command, []):
            print(f"  {{flag}}")
    raise SystemExit(0)
print("{{}}")
""")

    # Stateful: `print` answers 0 only between a `bootstrap` and the next `bootout`.
    executable(bin_dir / "launchctl", f"""#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
{_LOG}
log("launchctl")
state = Path(os.environ.get("MMW_TEST_LAUNCHD_STATE", "/nonexistent"))
verb = sys.argv[1]
label = sys.argv[2].rsplit("/", 1)[-1]
if verb == "print":
    loaded = json.loads(state.read_text()) if state.is_file() else []
    raise SystemExit(0 if label in loaded else 113)
if verb == "bootout":
    loaded = json.loads(state.read_text()) if state.is_file() else []
    state.write_text(json.dumps([x for x in loaded if x != label]))
    raise SystemExit(0)
if verb == "bootstrap":
    if os.environ.get("MMW_TEST_BOOTSTRAP_FAIL"):
        raise SystemExit(1)
    plist = Path(sys.argv[3]).stem
    loaded = json.loads(state.read_text()) if state.is_file() else []
    state.write_text(json.dumps(sorted(set(loaded) | {{plist}})))
    raise SystemExit(0)
raise SystemExit(2)
""")

    # install.sh does not use Nowledge Mem; a call is logged and fails.
    executable(bin_dir / "nmem", f"""#!/usr/bin/env python3
import json, os, sys
{_LOG}
log("nmem")
raise SystemExit(1)
""")
    executable(bin_dir / "uname", "#!/bin/sh\necho Darwin\n")


def executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def calls(log: Path) -> list[list[str]]:
    if not log.is_file():
        return []
    return [json.loads(line) for line in log.read_text().splitlines()]


def run_install(installer: Path, home: Path, bin_dir: Path, *args: str,
                env_overrides: dict[str, str | None] | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    for name in list(env):
        if name in _STRIP or name.startswith("NMEM_"):
            env.pop(name, None)
    env["MMW_V3_HOME"] = str(home)
    env["MMW_HOME"] = str(home / ".mmw")
    env["HOME"] = str(home)
    env["PATH"] = str(bin_dir) + os.pathsep + SYSTEM_PATH
    env["MMW_HOST_CATALOG"] = str(bin_dir / "host-catalog.json")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for name, value in (env_overrides or {}).items():
        if value is None:
            env.pop(name, None)
        else:
            env[name] = value
    return subprocess.run(
        ["bash", str(installer), *args],
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def copy_mmw(scratch: Path, name: str = "checkout") -> Path:
    """Copy this checkout's mmw-v3 to <scratch>/<name>/mmw-v3 and return that directory.

    The path has a /mmw-v3/ segment, which ours_skill_target needs to claim a link.
    `skills/diagram-design` is a relative link into mmw-v2's diagram-design subtree;
    the copy gets that skill's SKILL.md at the same relative place, so the link
    resolves inside the copy. check_skill_text.py reads each file an `imports.tsv`
    names as its upstream source, relative to the checkout; those files are copied
    to the same relative places, so --check on the copy reads what it reads here.
    """
    checkout = scratch / name
    dest = checkout / "mmw-v3"
    shutil.copytree(MMW, dest, symlinks=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    link = dest / "skills" / "diagram-design"
    target = (link.parent / os.readlink(link)).resolve(strict=False)
    real = (SKILLS / "diagram-design").resolve()
    target.mkdir(parents=True)
    shutil.copy2(real / "SKILL.md", target / "SKILL.md")
    for imports in SKILLS.glob("*/imports.tsv"):
        for line in imports.read_text(encoding="utf-8").splitlines()[1:]:
            source = line.split("\t")[2]
            if (REPO / source).is_file() and not (checkout / source).exists():
                (checkout / source).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(REPO / source, checkout / source)
    return dest


def listed_skills(skills_txt: Path = MMW / "skills.txt") -> list[str]:
    names = []
    for raw in skills_txt.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            names.append(line)
    return names


def snapshot(root: Path) -> dict[str, tuple]:
    """Every path under `root` with what it is: a link and its target, a file and its bytes."""
    found = {}
    for directory, dirs, files in os.walk(root):
        for name in dirs + files:
            path = Path(directory) / name
            key = str(path.relative_to(root))
            if path.is_symlink():
                found[key] = ("link", os.readlink(path))
            elif path.is_dir():
                found[key] = ("dir",)
            else:
                found[key] = ("file", path.read_bytes())
    return found


GROK_GUARD = '[ -z "${GROK_AGENT:-}${GROK_HOOK_EVENT:-}" ] || exit 0; '


def mode_hook_command(launcher: Path, host: str, argument: str) -> str:
    command = f"exec python3 '{launcher}' mode-hook {argument} {host}"
    return GROK_GUARD + command if host == "claude" else command


def commands_in(path: Path) -> list[str]:
    """Every handler command in one host hook file, whatever its grouping."""
    if not path.is_file():
        return []
    found = []
    for entries in (json.loads(path.read_text()).get("hooks") or {}).values():
        for entry in entries:
            if "command" in entry:
                found.append(entry["command"])
            for handler in entry.get("hooks") or []:
                found.append(handler.get("command", ""))
    return found
