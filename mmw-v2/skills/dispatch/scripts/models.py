"""读本机 models.json，扫描目录，再按 hosts.json 展开成启动参数。

hosts.json 跟着技能走，记下每个 host 怎么起及首次安装的默认值。models.json 是
MMW_HOME 下唯一的可写配置；board、命令行、dispatch.sh 与 install.sh 共用本文件的
读取、验证、锁与整体替换。runner 自己的命令只由 runners/<runner>.sh 执行。
"""

from __future__ import annotations

import json
import shlex
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, NamedTuple

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
import statedir  # noqa: E402

SKILL_DIR = SCRIPTS_DIR.parent
HOSTS_JSON = SKILL_DIR / "hosts.json"
RUNNERS_DIR = SKILL_DIR / "scripts" / "runners"
ALLOWED_AGENTS = (
    "junior-worker", "senior-worker", "reviewer", "verifier", "advisor")
# Lody cuts its own worktree. Level 4 must not pick it; ticket / env / live may.
WORKTREE_OWNING = frozenset({"lody"})
DEFAULT_RUNNER = "orca"
# Which catalog a row resolves against: `paseo` asks paseo, `cli` asks the host's own
# CLI (a runner that runs the CLI in a terminal starts it with those ids). dispatch.sh
# sets MMW_CATALOG_MODE from tonight's runner; tests set it or MMW_HOST_CATALOG.
DEFAULT_CATALOG_MODE = "cli"
CLI_HOSTS = ("cursor", "grok", "claude", "codex", "pi")
_CURSOR_EFFORT_IN_ID = re.compile(
    r"-(none|low|medium|high|xhigh|max)(?:-fast)?$", re.I)


def load_hosts() -> dict:
    if not HOSTS_JSON.is_file():
        raise ValueError(f"缺 hosts.json：{HOSTS_JSON}")
    data = json.loads(HOSTS_JSON.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "hosts" not in data:
        raise ValueError(f"{HOSTS_JSON} 不是一份 host 启动表")
    return data


class ConfigMissing(ValueError):
    pass


class VersionConflict(ValueError):
    def __init__(self, expected: int, found: int, modified_at: str):
        self.expected = expected
        self.found = found
        self.modified_at = modified_at
        super().__init__(f"expected version {expected}, found {found}; reload the saved configuration")


class InvalidConfig(ValueError):
    def __init__(self, errors: list[dict[str, str]]):
        self.errors = errors
        super().__init__("; ".join(f"{item['cell']}: {item['reason']}" for item in errors))


class ConfigLockHeld(ValueError):
    def __init__(self, lock_error):
        self.holder = lock_error.record
        super().__init__(f"{lock_error}; retry after that process releases the lock")


def models_json_path() -> Path:
    """The one local configuration path; legacy model path variables never affect it."""
    return statedir.home() / "models.json"


def models_lock_path() -> Path:
    return statedir.home() / "models.lock"


@contextmanager
def config_lock(*, purpose: str = "write models.json") -> Iterator[None]:
    """Hold the machine-wide configuration lock without waiting."""
    models_lock_path().parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with statedir.locked(models_lock_path(), wait=0, purpose=purpose):
        yield


def _modified_at(path: Path) -> str:
    stamp = path.stat().st_mtime
    return datetime.fromtimestamp(stamp, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_local_config() -> dict:
    path = models_json_path()
    if not path.is_file():
        raise ConfigMissing(f"no models.json at {path}; run install.sh first")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a configuration object")
    return data


class _HostBinaries:
    def get(self, key, default=None):
        spec = load_hosts()["hosts"].get(key) or {}
        return spec.get("binary", default if default is not None else key)


HOST_BINARIES = _HostBinaries()


def default_local_config() -> dict:
    """The version-1 configuration installed on a machine with no prior choice."""
    rows = {}
    for row in load_hosts().get("defaults") or []:
        rows[row["agent"]] = {key: row[key] for key in ("host", "model", "effort")}
    return {"version": 1, "runner": DEFAULT_RUNNER, "rows": rows}


def _validate_config_shape(config: dict) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    if not isinstance(config.get("version"), int) or config.get("version", 0) < 1:
        errors.append({"cell": "version", "reason": "must be a positive integer"})
    runner = config.get("runner")
    if not isinstance(runner, str) or not runner.strip():
        errors.append({"cell": "runner", "reason": "is required"})
    rows = config.get("rows")
    if not isinstance(rows, dict):
        return errors + [{"cell": "rows", "reason": "five role rows are required"}]
    missing = [role for role in ALLOWED_AGENTS if role not in rows]
    extra = [role for role in rows if role not in ALLOWED_AGENTS]
    if missing or extra:
        reason = "five role rows are required"
        if missing:
            reason += "; missing " + ", ".join(missing)
        if extra:
            reason += "; unknown " + ", ".join(extra)
        errors.append({"cell": "rows", "reason": reason})
    for role in ALLOWED_AGENTS:
        row = rows.get(role)
        if not isinstance(row, dict):
            if role not in missing:
                errors.append({"cell": role, "reason": "host, model, and effort are required"})
            continue
        for key in ("host", "model", "effort"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                errors.append({"cell": f"{role}.{key}", "reason": "is required"})
    return errors


def parse_legacy_rows(source: Path) -> list[tuple[str, str, str, str]]:
    """Read the retired Markdown table during the installer's one-time migration."""
    if not source.is_file():
        raise ValueError(f"missing migration source: {source}")
    rows: list[tuple[str, str, str, str]] = []
    text = source.read_text(encoding="utf-8")
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip().strip("`").strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0].lower() == "runner":
            continue
        if len(cells) == 5:
            cells = cells[:4]
        if len(cells) != 4:
            continue
        agent, host, model, effort = cells
        if agent == "agent" or set(agent) <= set("- "):
            continue
        if agent not in ALLOWED_AGENTS:
            raise ValueError(f"{source}: {agent} is not a dispatched role")
        if not host or not model:
            raise ValueError(f"{source}: {agent} lacks host or model")
        rows.append((agent, host, model, effort))
    if not rows:
        raise ValueError(f"{source} has no agent row")
    return rows


def parse_legacy_runner(source: Path) -> str | None:
    """Read the retired Markdown runner cell during one-time migration."""
    if not source.is_file():
        return None
    for line in source.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip().strip("`").strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0].lower() == "runner":
            return _spoken_runner(cells[1])
    return None


class SessionRow(NamedTuple):
    agent: str
    host: str
    model: str
    effort: str


def session_rows(path: Path | None = None) -> list[SessionRow]:
    """One saved row per dispatched role, in the fixed role order."""
    if path is not None:
        raise ValueError("session_rows no longer accepts a Markdown path")
    config = read_local_config()
    errors = _validate_config_shape(config)
    if errors:
        raise InvalidConfig(errors)
    return [SessionRow(role, **config["rows"][role]) for role in ALLOWED_AGENTS]


def bypass_rows(path: Path | None = None) -> list[SessionRow]:
    """旧名：全部派出的行都是会话。"""
    return session_rows(path)


def _spoken_runner(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip().strip("`").lower()
    if not text or text in ("—", "-", "none"):
        return None
    return text


def has_adapter(name: str) -> bool:
    """True when the dispatch skill has an adapter for this runner, `runners/<name>.sh`."""
    return (RUNNERS_DIR / f"{name}.sh").is_file()


def config_runners() -> tuple[str, ...]:
    """Runners a saved configuration may name, derived from installed adapters."""
    return tuple(sorted(path.stem for path in RUNNERS_DIR.glob("*.sh"))) + ("auto",)


def catalog_source(runner: str) -> str:
    return "paseo" if runner == "paseo" else "cli"


def _can_start(runner: str, host_spec: dict) -> bool:
    return catalog_source(runner) in host_spec


def runtime_from_environ(environ: Mapping[str, str]) -> tuple[str, ...]:
    """Runners visible in this process: TERM_PROGRAM, then HERDR_ENV, then TMUX.

    Environment variables cannot express nesting. TERM_PROGRAM is treated as
    the outer signal: Herdr opened inside an Orca terminal is herdr, not orca.
    When HERDR_ENV and TMUX are both set, this returns tmux last; that does not
    say which is nested in which. This reports what the environment shows, adapter
    or not; `pick_runner` is what passes over a runner no adapter can drive.
    """
    found: list[str] = []
    if (environ.get("TERM_PROGRAM") or "").strip().lower() == "orca":
        found.append("orca")
    if (environ.get("HERDR_ENV") or "").strip():
        found.append("herdr")
    if (environ.get("TMUX") or "").strip():
        found.append("tmux")
    return tuple(found)


def pick_runner(
    ticket: str | None = None,
    env: str | None = None,
    live: str | None = None,
    runtime: Mapping[str, str] | Sequence[str] = (),
    default: str = DEFAULT_RUNNER,
) -> str:
    """First speaker wins: ticket, env, saved config, innermost runtime, default.

    A name given by the ticket, the environment or saved config is returned as given,
    adapter or not: someone chose it, and `start` refuses a runner it has no adapter for
    by name. The runtime level is a guess from the environment, so it only names a
    runner that has an adapter (`has_adapter`) and does not cut its own worktree: a
    guess that names tmux, which nothing here can drive, would refuse every start.
    """
    for value in (ticket, env, live):
        spoken = _spoken_runner(value)
        if spoken:
            return spoken
    if isinstance(runtime, Mapping):
        names = runtime_from_environ(runtime)
    else:
        names = tuple(
            spoken for spoken in (_spoken_runner(n) for n in runtime) if spoken)
    detected = [name for name in names
                if name not in WORKTREE_OWNING and has_adapter(name)]
    if detected:
        return detected[-1]
    spoken = _spoken_runner(default)
    if spoken:
        return spoken
    raise ValueError("no runner")


def _norm(text: str) -> str:
    return re.sub(r"[\s_]+", "-", text.strip().strip("`").lower())


def _want_fast(query: str) -> bool:
    return "fast" in _norm(query).split("-")


def _ends_with_effort(model_id: str, effort: str) -> bool:
    if not effort or effort in ("—", "-", ""):
        return True
    return bool(re.search(
        rf"(?:^|-){re.escape(effort.lower())}(?:-fast)?$", model_id.lower()))


def _is_fast_id(model_id: str) -> bool:
    return bool(re.search(r"-fast$", model_id.lower()))


def match_offering(
    query: str,
    offerings: list[dict],
    *,
    effort: str = "",
    effort_in_model: bool = False,
) -> dict:
    """Pick the unique offering for an everyday name. Raise ValueError otherwise."""
    if not offerings:
        raise ValueError(f"host catalog is empty; {query!r} matches nothing")
    pool = offerings
    if effort_in_model and effort and effort not in ("—", "-", ""):
        pool = [o for o in pool if _ends_with_effort(str(o.get("id") or ""), effort)]
        if not pool:
            raise ValueError(
                f"{query!r} at effort {effort} matches nothing in the catalog")
    needle = _norm(query)
    hits = []
    for offering in pool:
        oid = _norm(str(offering.get("id") or ""))
        name = _norm(str(offering.get("name") or ""))
        # The catalog display renders ids through `_slug_everyday`,
        # so a cell copied from it ("fable 5.1") must match the id it was
        # rendered from ("claude-fable-5-1"). Compare against that form too, or
        # the table tells you to write a name nothing can resolve.
        slug = _norm(_slug_everyday(str(offering.get("id") or "")))
        cursor_name = _norm(_cursor_family_name(
            str(offering.get("name") or ""), str(offering.get("id") or ""),
            fast=_is_fast_id(str(offering.get("id") or "")))) if effort_in_model else ""
        if needle in (oid, name, slug, cursor_name) or needle in oid or needle in name:
            hits.append(offering)
    # exact id, name or everyday name wins over substring
    exact = [
        o for o in hits
        if needle in (
            _norm(str(o.get("id") or "")),
            _norm(str(o.get("name") or "")),
            _norm(_slug_everyday(str(o.get("id") or ""))),
            _norm(_cursor_family_name(
                str(o.get("name") or ""), str(o.get("id") or ""),
                fast=_is_fast_id(str(o.get("id") or "")))) if effort_in_model else "",
        )
    ]
    if len(exact) == 1:
        hits = exact
    elif len(exact) > 1:
        hits = exact
    if len(hits) > 1 and not _want_fast(query):
        ordinary = [o for o in hits if not _is_fast_id(str(o.get("id") or ""))]
        if len(ordinary) == 1:
            hits = ordinary
        elif ordinary:
            hits = ordinary
    if len(hits) == 1:
        return hits[0]
    ids = [str(o.get("id") or "") for o in hits]
    if not hits:
        raise ValueError(f"{query!r} matches nothing in the catalog")
    raise ValueError(
        f"{query!r} matches more than one offering: " + ", ".join(ids))


def _which(name: str) -> str | None:
    # The only caller is `_run`, which has to find each host's CLI from a non-login
    # shell whose PATH may be short: an agent's shell tool, `install.sh` refreshing the
    # copy table, `dispatch.sh` starting an agent. On this machine those CLIs are
    # installed in ~/.local/bin and /opt/homebrew/bin, so the list assumes a Mac with
    # Homebrew.
    extra = [
        str(Path.home() / ".local" / "bin"),
        "/opt/homebrew/bin",
        "/usr/local/bin",
    ]
    path = os.pathsep.join(extra + [os.environ.get("PATH") or ""])
    for folder in path.split(os.pathsep):
        if not folder:
            continue
        candidate = Path(folder) / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def _run(argv: list[str], timeout: int = 30) -> str:
    if not argv:
        return ""
    binary = argv[0]
    resolved = binary if "/" in binary else (_which(binary) or "")
    if not resolved:
        return ""
    try:
        proc = subprocess.run(
            [resolved, *argv[1:]],
            check=False, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return proc.stdout or ""


def _runner_call(runner: str, verb: str, *args: str, timeout: int = 30) -> str:
    """Ask a runner adapter; runner CLI command shapes remain inside that adapter."""
    adapter = RUNNERS_DIR / f"{runner}.sh"
    if not adapter.is_file():
        return ""
    return _run(["bash", str(adapter), verb, *args], timeout=timeout)


def _parse_cursor_models(text: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.lower().startswith("available"):
            continue
        if " - " in line:
            ident, name = line.split(" - ", 1)
            ident, name = ident.strip(), name.strip()
        elif re.match(r"^[\w.-]+$", line):
            ident = name = line
        else:
            continue
        effort = ""
        matched = _CURSOR_EFFORT_IN_ID.search(ident)
        if matched:
            effort = matched.group(1).lower()
        out.append({"id": ident, "name": name, "thinkingOptionIds": [effort] if effort else []})
    return out


def _parse_grok_models(text: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        m = re.search(r"^\s*[*-]\s+(\S+)", line)
        if m:
            ident = m.group(1).strip("()")
            out.append({"id": ident, "name": ident})
    return out


def _parse_claude_help(text: str) -> tuple[list[str], list[str]]:
    """Aliases mentioned under --model, and --effort levels."""
    start = text.find("--model")
    chunk = text[start:start + 800] if start != -1 else ""
    aliases = [a for a in re.findall(r"'([A-Za-z0-9][A-Za-z0-9._:-]*)'", chunk) if a not in ("e.g.",)]
    effort_m = re.search(
        r"--effort <level>\s+Effort level for the current session\s+\(([^)]+)\)",
        text, re.S)
    if effort_m is None:
        effort_m = re.search(r"--effort <level>[^(]*\(([^)]+)\)", text)
    efforts = [p.strip() for p in effort_m.group(1).split(",")] if effort_m else []
    return aliases, efforts


def _claude_settings_models() -> list[str]:
    path = Path.home() / ".claude" / "settings.json"
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(data, dict):
        return []
    names = []
    current = data.get("model")
    if isinstance(current, str) and current.strip():
        names.append(current.strip())
    settings = data.get("modelSettings")
    if isinstance(settings, dict):
        names.extend(str(k) for k in settings if k)
    seen = set()
    out = []
    for name in names:
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


def _parse_codex_debug_models(text: str) -> list[dict]:
    if not text.strip():
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    rows = data.get("models") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        return []
    out = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        ident = str(item.get("slug") or item.get("id") or "")
        if not ident:
            continue
        name = str(item.get("display_name") or ident)
        levels = []
        for level in item.get("supported_reasoning_levels") or []:
            if isinstance(level, dict):
                value = level.get("effort") or level.get("id") or level.get("level")
            else:
                value = level
            if value:
                levels.append(str(value))
        out.append({"id": ident, "name": name, "thinkingOptionIds": levels})
    return out


def _parse_pi_models(text: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        if not line.strip() or line.lower().startswith("provider"):
            continue
        m = re.match(r"^(\S+)\s+(\S+)\s+\S+\s+\S+\s+(\S+)\s+(\S+)\s*$", line)
        if not m:
            continue
        provider, model, thinking, _images = m.groups()
        ident = f"{provider}/{model}"
        out.append({
            "id": ident,
            "name": model,
            "thinkingOptionIds": (
                ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
                if thinking.lower() == "yes" else []
            ),
        })
    return out


def _paseo_models(host: str) -> list[dict]:
    raw = _runner_call("paseo", "catalog-models", host)
    if not raw.strip():
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    out = []
    for item in data:
        if not isinstance(item, dict):
            continue
        ident = str(item.get("id") or "")
        name = str(item.get("model") or ident)
        thinking = item.get("thinkingOptionIds") or []
        out.append({"id": ident, "name": name, "thinkingOptionIds": thinking})
    return out


def _host_efforts(host: str, offering: dict | None = None) -> list[str]:
    ids = [str(x) for x in ((offering or {}).get("thinkingOptionIds") or []) if x]
    if ids:
        return ids
    spec = load_hosts()["hosts"].get(host) or {}
    return [str(x) for x in (spec.get("efforts") or [])]


def fetch_cli_offerings(host: str) -> list[dict]:
    """Ask the host CLI. Never Paseo. Empty if the binary is missing or silent."""
    if host == "cursor":
        return _parse_cursor_models(_run(["cursor-agent", "models"]))
    if host == "grok":
        rows = _parse_grok_models(_run(["grok", "models"]))
        efforts = _host_efforts("grok")
        for row in rows:
            row.setdefault("thinkingOptionIds", list(efforts))
        return rows
    if host == "claude":
        aliases, efforts = _parse_claude_help(_run(["claude", "--help"]))
        names = list(aliases)
        for name in _claude_settings_models():
            if name not in names:
                names.append(name)
        return [
            {"id": name, "name": name, "thinkingOptionIds": list(efforts)}
            for name in names
        ]
    if host == "codex":
        return _parse_codex_debug_models(_run(["codex", "debug", "models"], timeout=45))
    if host == "pi":
        rows = _parse_pi_models(_run(["pi", "--list-models"]))
        fallback = ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
        for row in rows:
            if not row.get("thinkingOptionIds"):
                row["thinkingOptionIds"] = list(fallback)
        return rows
    return []


def scan_cli_catalogs() -> dict[str, list[dict]]:
    """Tonight's five CLI catalogs. Tests set MMW_HOST_CATALOG to skip the binaries."""
    fixture = _fixture_catalog()
    if fixture is not None:
        return {host: _fixture_offerings(fixture, "cli", host) for host in CLI_HOSTS}
    return {host: fetch_cli_offerings(host) for host in CLI_HOSTS}


_EFFORT_ORDER = (
    "none", "off", "minimal", "low", "medium", "high", "xhigh", "max",
    "ultra", "ultracode")


def _sort_efforts(values: list[str]) -> list[str]:
    rank = {name: i for i, name in enumerate(_EFFORT_ORDER)}
    seen = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    return sorted(seen, key=lambda x: (rank.get(x, 99), x))


def _slug_everyday(ident: str) -> str:
    text = ident.strip()
    text = re.sub(r"^(claude|cursor)-", "", text, flags=re.I)
    text = re.sub(r"(?<=\D)(\d)-(\d)(?=\D|$)", r"\1.\2", text)
    if "/" in text:
        text = text.split("/", 1)[-1]
    text = text.replace("-", " ").replace("_", " ")
    return re.sub(r"\s+", " ", text).strip().lower()


def _cursor_family_name(name: str, ident: str, *, fast: bool) -> str:
    text = name.strip() or ident
    text = re.sub(r"\s*\([^)]*\)", "", text)
    text = re.sub(r"\s+Fast$", "", text, flags=re.I)
    text = re.sub(r"\s+1M\b", "", text, flags=re.I)
    for _ in range(4):
        text = re.sub(
            r"\s+(Low|Medium|High|Extra High|Max|None|Thinking)$",
            "", text, flags=re.I)
    text = re.sub(r"^Cursor\s+", "", text, flags=re.I)
    text = re.sub(r"^Claude\s+", "", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip().lower()
    if ident and "thinking" in ident.lower() and "thinking" not in text.split():
        text = f"{text} thinking"
    if not text:
        text = _slug_everyday(_CURSOR_EFFORT_IN_ID.sub("", ident))
    if fast and "fast" not in text.split():
        text = f"{text} fast"
    return text


def _collapse_fillable(rows: list[tuple[str, str]]) -> list[tuple[str, str]]:
    efforts: dict[str, list[str]] = {}
    order: list[str] = []
    for model, cell in rows:
        if model not in efforts:
            order.append(model)
            efforts[model] = []
        efforts[model].extend(
            part.strip() for part in cell.split(",") if part.strip() and part.strip() != "—")
    out = []
    for model in order:
        names = _sort_efforts(efforts[model])
        out.append((model, ", ".join(names) if names else "—"))
    return out


def fillable_rows(host: str, offerings: list[dict]) -> list[tuple[str, str]]:
    """Return the model and effort names accepted by configuration commands."""
    if host == "cursor":
        rows = []
        seen: set[tuple[str, str]] = set()
        for offering in offerings:
            ident = str(offering.get("id") or "")
            name = str(offering.get("name") or ident)
            fast = ident.lower().endswith("-fast")
            matched = _CURSOR_EFFORT_IN_ID.search(ident)
            effort = matched.group(1).lower() if matched else "—"
            model = _cursor_family_name(name, ident, fast=fast)
            pair = (model, effort)
            if pair in seen:
                continue
            seen.add(pair)
            rows.append(pair)
        rows.sort(key=lambda item: (
            item[0],
            _EFFORT_ORDER.index(item[1]) if item[1] in _EFFORT_ORDER else 99,
        ))
        return rows

    skip = {"opus", "sonnet", "fable"} if host == "claude" else set()
    rows = []
    seen = set()
    for offering in offerings:
        ident = str(offering.get("id") or "")
        name = str(offering.get("name") or ident)
        if ident.lower() in skip or name.lower() in skip:
            continue
        if host == "pi":
            model = ident.split("/", 1)[-1] if ident else name
        elif name and name.lower() != ident.lower() and not re.search(r"\d", name):
            model = name.lower().strip()
        else:
            model = _slug_everyday(name if re.search(r"\d", name) else ident)
        if not model or model in seen:
            continue
        seen.add(model)
        efforts = _sort_efforts(_host_efforts(host, offering))
        rows.append((model, ", ".join(efforts) if efforts else "—"))
    return _collapse_fillable(rows)


_STATE_LABELS = {
    "ok": "答出了几个 model",
    "missing": "本机没装",
    "silent": "没有回答",
    "down": "Paseo 没开",
    "unlaunchable": "这个 runner 起不了它",
}


def _fixture_catalog() -> dict | None:
    source = os.environ.get("MMW_HOST_CATALOG")
    if not source:
        return None
    data = json.loads(Path(source).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{source} is not a host catalog object")
    return data


def _fixture_entry(data: dict, source: str, host: str):
    section = data.get(source)
    if isinstance(section, dict):
        if source == "paseo" and section.get("state") == "down":
            return {"state": "down"}
        if host in section:
            return section[host]
    if host in data:
        return data[host]
    return None


def _fixture_offerings(data: dict, source: str, host: str) -> list[dict]:
    entry = _fixture_entry(data, source, host)
    if isinstance(entry, list):
        return list(entry)
    if isinstance(entry, dict):
        return list(entry.get("offerings") or [])
    return []


def _resolve_from_offerings(host: str, model: str, effort: str,
                            offerings: list[dict], source: str) -> tuple[str, str, str]:
    hosts = load_hosts()["hosts"]
    if host not in hosts:
        raise ValueError(f"unknown host {host}")
    spec = hosts[host]
    offering = match_offering(
        model, offerings, effort=effort,
        effort_in_model=bool(spec.get("effort_in_model")) and source != "paseo")
    resolved = str(offering.get("id") or "")
    allowed = spec.get("efforts")
    thinking_ids = offering.get("thinkingOptionIds")
    if allowed and effort not in ("—", "-", "") and spec.get("thinking") != "boolean":
        names = [str(x) for x in (thinking_ids or allowed)]
        if names and effort not in names and spec.get("paseo", {}).get("thinking") != "boolean":
            if not spec.get("effort_in_model") and effort not in [str(x) for x in allowed]:
                raise ValueError(
                    f"effort {effort!r} is not one of {', '.join(str(x) for x in allowed)}")
    return host, resolved, effort


def _offered_rows(host: str, offerings: list[dict], source: str) -> list[dict]:
    rows: list[dict] = []
    by_model: dict[str, dict] = {}
    for model, effort_text in fillable_rows(host, offerings):
        efforts = [part.strip() for part in effort_text.split(",") if part.strip()]
        for effort in efforts or ["—"]:
            try:
                _resolve_from_offerings(host, model, effort, offerings, source)
            except ValueError:
                continue
            if model not in by_model:
                by_model[model] = {"model": model, "efforts": []}
                rows.append(by_model[model])
            if effort not in by_model[model]["efforts"]:
                by_model[model]["efforts"].append(effort)
    return rows


def _host_result(state: str, offered: list[dict] | None = None) -> dict:
    return {"state": state, "label": _STATE_LABELS[state], "offered": offered or []}


def _scan_one_host(host: str, runner: str, source: str, fixture: dict | None) -> dict:
    spec = load_hosts()["hosts"].get(host) or {}
    if not _can_start(runner, spec):
        return _host_result("unlaunchable")

    entry = _fixture_entry(fixture, source, host) if fixture is not None else None
    if fixture is not None:
        if isinstance(entry, list):
            offerings = list(entry)
            state = "ok" if offerings else "silent"
        elif isinstance(entry, dict):
            state = str(entry.get("state") or "")
            offerings = _fixture_offerings(fixture, source, host)
            if not state:
                state = "ok" if offerings else "silent"
        else:
            state, offerings = "silent", []
    elif source == "paseo":
        offerings = _paseo_models(host)
        state = "ok" if offerings else "silent"
    else:
        binary = HOST_BINARIES.get(host)
        if _which(binary) is None:
            state, offerings = "missing", []
        else:
            offerings = fetch_cli_offerings(host)
            state = "ok" if offerings else "silent"
    if state not in _STATE_LABELS:
        raise ValueError(f"MMW_HOST_CATALOG gives {host} unknown state {state!r}")
    return _host_result(
        state, _offered_rows(host, offerings, source) if state == "ok" else [])


def scan_host_catalogs(runner: str, hosts: Sequence[str] = CLI_HOSTS) -> dict:
    """Scan all requested hosts concurrently from the source the runner will use."""
    source = catalog_source(runner)
    fixture = _fixture_catalog()
    selected = [host for host in CLI_HOSTS if host in hosts]

    paseo_down = False
    if source == "paseo":
        if fixture is not None:
            paseo = fixture.get("paseo")
            paseo_down = isinstance(paseo, dict) and paseo.get("state") == "down"
        else:
            paseo_down = not bool(_runner_call("paseo", "catalog-status"))
    if paseo_down:
        result = {host: _host_result("down") for host in selected}
    else:
        with ThreadPoolExecutor(max_workers=max(1, len(selected))) as pool:
            values = pool.map(lambda host: _scan_one_host(host, runner, source, fixture), selected)
            result = dict(zip(selected, values))
    return {
        "source": source,
        "scanned_at": statedir.now_iso(),
        "scanning": False,
        "hosts": result,
    }


def _validate_local_config(config: dict, scan: dict,
                           roles: Sequence[str] | None = None) -> list[dict[str, str]]:
    errors = _validate_config_shape(config)
    runner = config.get("runner")
    valid_runner = runner == "auto" or (isinstance(runner, str) and has_adapter(runner))
    if not valid_runner:
        errors.append({"cell": "runner", "reason":
                       f"{runner!r} has no adapter; choose one of {', '.join(config_runners())}"})
    required_source = catalog_source(str(runner))
    if valid_runner and scan.get("source") != required_source:
        errors.append({"cell": "runner",
                       "reason": f"runner {runner} requires a fresh {required_source} scan; scan it and retry"})
    rows = config.get("rows")
    if not isinstance(rows, dict):
        return errors
    missing = [role for role in ALLOWED_AGENTS if role not in rows]
    checked = set(roles or ALLOWED_AGENTS)
    catalog_hosts = scan.get("hosts") if isinstance(scan, dict) else {}
    host_specs = load_hosts()["hosts"]
    for role in ALLOWED_AGENTS:
        row = rows.get(role)
        if not isinstance(row, dict):
            if role not in missing:
                errors.append({"cell": role, "reason": "host, model, and effort are required"})
            continue
        if role not in checked:
            continue
        host = row.get("host")
        if host not in host_specs:
            errors.append({"cell": f"{role}.host", "reason": f"unknown host {host!r}"})
            continue
        launch_block = catalog_source(str(runner))
        if valid_runner and not _can_start(str(runner), host_specs[host]):
            errors.append({"cell": f"{role}.host",
                           "reason": f"runner {runner} cannot start host {host}: hosts.json has no {launch_block} block; choose another host or runner"})
            continue
        found = catalog_hosts.get(host) if isinstance(catalog_hosts, dict) else None
        if not isinstance(found, dict) or found.get("state") != "ok":
            state = found.get("label") if isinstance(found, dict) else "was not scanned"
            errors.append({"cell": f"{role}.host", "reason":
                           f"host {host} is unavailable: {state}; restore it and scan again"})
            continue
        model = row.get("model")
        offered = next((item for item in found.get("offered") or []
                        if item.get("model") == model), None)
        if offered is None:
            errors.append({"cell": f"{role}.model",
                           "reason": f"model {model!r} is not in the current {scan.get('source')} catalog for {host}; choose an offered model"})
            continue
        effort = row.get("effort")
        if effort not in (offered.get("efforts") or []):
            errors.append({"cell": f"{role}.effort",
                           "reason": f"effort {effort!r} is not offered for {host} model {model!r}; choose an offered effort"})
    return errors


def write_local_config(config: dict, expected_version: int, scan: dict,
                       *, validate_roles: Sequence[str] | None = None) -> dict:
    """Validate, lock, version-check, and atomically replace models.json."""
    path = models_json_path()
    if not path.is_file():
        raise ConfigMissing(f"no models.json at {path}; run install.sh first")
    errors = _validate_local_config(config, scan, validate_roles)
    if errors:
        raise InvalidConfig(errors)
    try:
        with config_lock():
            current = read_local_config()
            found_version = current.get("version")
            if found_version != expected_version:
                raise VersionConflict(expected_version, found_version, _modified_at(path))
            written = {
                "version": expected_version + 1,
                "runner": config["runner"],
                "rows": {
                    role: {key: config["rows"][role][key]
                           for key in ("host", "model", "effort")}
                    for role in ALLOWED_AGENTS
                },
            }
            statedir.write_atomic(path, json.dumps(written, ensure_ascii=False, indent=2) + "\n")
            return written
    except statedir.LockHeld as exc:
        raise ConfigLockHeld(exc) from None


def fetch_offerings(host: str) -> list[dict]:
    mode = os.environ.get("MMW_CATALOG_MODE", DEFAULT_CATALOG_MODE)
    fixture = _fixture_catalog()
    if fixture is not None:
        return _fixture_offerings(fixture, mode, host)
    if mode == "paseo":
        return _paseo_models(host)
    # One catalog source per host. Asking two different sources is how a saved name
    # can validate in the editor and then fail at start.
    return fetch_cli_offerings(host)


def resolve_row(host: str, model: str, effort: str) -> tuple[str, str, str]:
    """Everyday cells → (host, resolved model id, effort to pass on)."""
    offerings = fetch_offerings(host)
    mode = os.environ.get("MMW_CATALOG_MODE", DEFAULT_CATALOG_MODE)
    return _resolve_from_offerings(host, model, effort, offerings, mode)


def bypass_argv(host: str, model: str, effort: str, name: str) -> list[str]:
    """The host CLI's own launch flags, model and effort filled in.

    Read from the `cli` block of a host in hosts.json: the host's own command-line argv.
    Every runner that starts a host by running its CLI in a terminal — Herdr after
    `agent start … --`, Orca inside `terminal create --command` — runs these same flags,
    so an edit to the block is an edit to how that host starts on all of them. The runner
    adapters build their launch line from here (`models.py bypass-argv` and `models.py
    launch-line`); none keeps a copy. An empty effort (`—`) drops the effort flag rather
    than passing `—`.
    """
    spec = load_hosts()["hosts"].get(host)
    if not spec or "cli" not in spec:
        raise ValueError(f"no bypass argv for host {host}: hosts.json gives it no `cli` block")
    template = list(spec["cli"]["argv"])
    argv = []
    skip_next = False
    for i, part in enumerate(template):
        if skip_next:
            skip_next = False
            continue
        if part == "{effort}" or (isinstance(part, str) and "{effort}" in part):
            if effort in ("—", "-", ""):
                if argv and argv[-1] in (
                        "--reasoning-effort", "--effort", "-c"):
                    argv.pop()
                continue
        filled = (
            part.replace("{model}", model)
                .replace("{effort}", effort)
                .replace("{name}", name)
        )
        argv.append(filled)
    return argv


def create_agent_settings(host: str, permissions: str = "bypass") -> dict:
    if permissions != "bypass":
        raise ValueError(f"permissions 只能是 bypass，得到 {permissions!r}")
    spec = load_hosts()["hosts"].get(host)
    if not spec or "paseo" not in spec:
        return {"features": {"auto_accept": True}}
    return json.loads(json.dumps(spec["paseo"]["settings"]))


def apply_permissions(profile: dict, host: str, permissions: str = "bypass") -> dict:
    settings = create_agent_settings(host, permissions)
    for key, name in (("features", "featureValues"), ("modeId", "modeId")):
        if key in settings:
            profile[name] = settings[key]
        else:
            profile.pop(name, None)
    return profile


def thinking_option(host: str, effort: str, offering: dict | None = None) -> str | None:
    spec = load_hosts()["hosts"].get(host) or {}
    kind = (spec.get("paseo") or {}).get("thinking")
    if not kind:
        return None
    if kind == "boolean":
        if effort in ("—", "-", "", "off", "false"):
            return "false"
        return "true"
    if effort in ("—", "-", ""):
        return None
    ids = (offering or {}).get("thinkingOptionIds") or spec.get("efforts") or []
    if ids and effort not in [str(x) for x in ids]:
        raise ValueError(
            f"effort {effort!r} is not a thinking option for {host}")
    return effort


def resolve_session(agent: str) -> SessionRow:
    rows = [r for r in session_rows() if r.agent == agent]
    if not rows:
        raise ValueError(f"no row for {agent}")
    row = rows[0]
    host, model, effort = resolve_row(row.host, row.model, row.effort)
    return SessionRow(row.agent, host, model, effort)


def row_tsv(agent: str) -> str:
    """host<TAB>resolved-model<TAB>effort for dispatch.sh."""
    row = resolve_session(agent)
    return f"{row.host}\t{row.model}\t{row.effort}"


def runner_name(environ: Mapping[str, str] | None = None) -> str:
    """Tonight's runner: MMW_RUNNER, then models.json, then the
    innermost runner this process runs in that has an adapter, then the default."""
    env = os.environ if environ is None else environ
    explicit = _spoken_runner(env.get("MMW_RUNNER"))
    if explicit:
        return explicit
    configured = read_local_config().get("runner")
    if configured == "auto":
        configured = None
    return pick_runner(
        live=configured,
        runtime=env,
    )


def paseo_run_args(host: str, model: str, effort: str) -> list[str]:
    """The `paseo run` flags for a host: provider/model, mode and thinking level.

    `paseo run` carries `--mode` and `--thinking` and no other setting (Paseo 0.7.2,
    `cli/dist/commands/agent/run.js`), so a host's `features` are not passed.
    """
    settings = create_agent_settings(host)
    argv = ["--provider", f"{host}/{model}"]
    if settings.get("modeId"):
        argv += ["--mode", str(settings["modeId"])]
    thinking = thinking_option(host, effort)
    if thinking is not None:
        argv += ["--thinking", thinking]
    return argv


def worker_role_names() -> list[str]:
    seen = []
    for row in session_rows():
        if row.agent.endswith("-worker") and row.agent not in seen:
            seen.append(row.agent)
    return seen


def launch_line(host: str, model: str, effort: str, name: str,
                prompt: str = "") -> list[str]:
    """The whole command that starts a host: its binary, then `bypass_argv`, then the
    first prompt when there is one.

    Each host with a launch block takes an initial prompt as its last positional
    argument (`grok [PROMPT]`, `codex [PROMPT]`, `claude [prompt]`, `cursor-agent
    [prompt]`), so a runner that starts the host from this line does not type the prompt
    into it afterwards. A prompt that begins with `-` is refused: the host would read it
    as a flag.
    """
    argv = [HOST_BINARIES.get(host), *bypass_argv(host, model, effort, name)]
    if prompt:
        if prompt.startswith("-"):
            raise ValueError(
                "the first prompt begins with '-', and the host would read it as a flag")
        argv.append(prompt)
    return argv


USAGE = ("usage: models.py config show\n"
         "       models.py config runner <runner>\n"
         "       models.py config set <role> <host> <model> <effort>\n"
         "       models.py runner\n"
         "       models.py paseo-args <host> <model> <effort>\n"
         "       models.py bypass-argv <host> <model> <effort> <name>\n"
         "       models.py launch-line <host> <model> <effort> <name> [<prompt>]\n")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["config"]:
        try:
            if args == ["config", "show"]:
                print(json.dumps(read_local_config(), ensure_ascii=False, indent=2))
                return 0
            if len(args) == 3 and args[1] == "runner":
                current = read_local_config()
                proposed = json.loads(json.dumps(current))
                proposed["runner"] = args[2]
                scan = scan_host_catalogs(args[2])
                written = write_local_config(proposed, current["version"], scan)
                print(json.dumps(written, ensure_ascii=False))
                return 0
            if len(args) == 6 and args[1] == "set":
                role, host, model, effort = args[2:]
                current = read_local_config()
                if role not in ALLOWED_AGENTS:
                    raise InvalidConfig([{"cell": "role", "reason": f"unknown role {role!r}"}])
                proposed = json.loads(json.dumps(current))
                proposed["rows"][role] = {"host": host, "model": model, "effort": effort}
                scan = scan_host_catalogs(current["runner"], [host])
                written = write_local_config(
                    proposed, current["version"], scan, validate_roles=[role])
                print(json.dumps(written, ensure_ascii=False))
                return 0
        except (ValueError, OSError) as exc:
            sys.stderr.write(f"models.py: {exc}\n")
            return 2
        sys.stderr.write(USAGE)
        return 2
    if args == ["runner"]:
        try:
            print(runner_name())
            return 0
        except (ValueError, OSError) as exc:
            sys.stderr.write(f"models.py: {exc}\n")
            return 2
    if len(args) == 4 and args[0] == "paseo-args":
        try:
            print("\n".join(paseo_run_args(*args[1:])))
        except (ValueError, OSError) as exc:
            sys.stderr.write(f"models.py: {exc}\n")
            return 2
        return 0
    if (len(args) == 5 and args[0] == "bypass-argv") or (
            len(args) in (5, 6) and args[0] == "launch-line"):
        verb, host, model, effort, name = args[:5]
        prompt = args[5] if len(args) == 6 else ""
        try:
            if verb == "bypass-argv":
                print("\n".join(bypass_argv(host, model, effort, name)))
            else:
                print(shlex.join(launch_line(host, model, effort, name, prompt)))
        except (ValueError, OSError) as exc:
            # A host with no launch block, or a hosts.json that cannot be read, is a
            # refusal: starting the host without its model and effort would run a session
            # nobody asked for, and would look like one that started fine.
            sys.stderr.write(f"models.py: cannot build the launch line for {host}: {exc}\n")
            return 2
        return 0
    sys.stderr.write(USAGE)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
