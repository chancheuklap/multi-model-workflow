"""读本机 models.json，扫描目录，再按 hosts.json 展开成启动参数。

hosts.json 与 roles.json 跟着技能走：hosts.json 只记每个 host 怎么起，roles.json 记每个
角色，连同它首次安装的默认 host、模型与 effort（`default`）。models.json 是
MMW_HOME 下唯一的可写配置；board、命令行、dispatch.sh 与 install.sh 共用本文件的
读取、验证、锁与整体替换。runner 的命令和原生工具调用只在 runners/ 中实现。
"""

from __future__ import annotations

import json
import shlex
import os
import re
import subprocess
import select
import tempfile
import threading
import time
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
ROLES_JSON = SKILL_DIR / "roles.json"
RUNNERS_DIR = SKILL_DIR / "scripts" / "runners"


def _roles() -> list[dict]:
    return json.loads(ROLES_JSON.read_text(encoding="utf-8"))["roles"]


def session_roles() -> tuple[str, ...]:
    """The roles dispatch.sh starts as sessions, in roles.json's order: one models.json row each."""
    return tuple(r["name"] for r in _roles())


def subagent_rows() -> tuple[str, ...]:
    return tuple(r["name"] for r in json.loads(
        ROLES_JSON.read_text(encoding="utf-8"))["subagents"])


def subagent_row(name: str, host: str) -> dict[str, str]:
    if name not in subagent_rows():
        raise ValueError(f"unknown subagent row {name!r}; choose one of {', '.join(subagent_rows())}")
    if host not in CLI_HOSTS:
        raise ValueError(f"unknown subagent host {host!r}; choose one of {', '.join(CLI_HOSTS)}")
    try:
        config = read_local_config()
    except ConfigMissing:
        config = {}
    row = config.get("subagents", {})
    cell = "subagents"
    for key in (name, host):
        if not isinstance(row, dict):
            raise InvalidConfig([{"cell": cell, "reason": "must be a settings object"}])
        row = row.get(key, {})
        cell += f".{key}"
    if not isinstance(row, dict):
        raise InvalidConfig([{"cell": cell, "reason": "must contain model and effort"}])
    settings = {key: row.get(key, "inherit") for key in ("model", "effort")}
    for key, value in settings.items():
        if not isinstance(value, str) or not value.strip():
            raise InvalidConfig([{"cell": f"{cell}.{key}", "reason": "must be a nonempty string"}])
    return settings


ALLOWED_AGENTS = session_roles()
# Lody cuts its own worktree. Runtime detection must not pick it; an explicit choice may.
DEFAULT_RUNNER = "orca"
# How many tickets a night runs at once when models.json names no cap.
DEFAULT_MAX_WORKERS = 3
# Which catalog a row resolves against: `paseo` asks paseo, `cli` asks the host's own
# CLI (a runner that runs the CLI in a terminal starts it with those ids). dispatch.sh
# sets MMW_CATALOG_MODE from tonight's runner; tests set it or MMW_HOST_CATALOG.
DEFAULT_CATALOG_MODE = "cli"
CLI_HOSTS = ("claude", "codex")


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
    """The one local configuration path."""
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
    """The version-1 configuration installed on a machine with no prior choice: each role's
    `default` in roles.json."""
    rows = {}
    for role in _roles():
        default = role.get("default") or {}
        rows[role["name"]] = {key: default.get(key) for key in ("host", "model", "effort")}
    return {"version": 1, "runner": DEFAULT_RUNNER, "rows": rows, "max_workers": DEFAULT_MAX_WORKERS}


def _version_errors(value: object) -> list[dict[str, str]]:
    if not isinstance(value, int) or value < 1:
        return [{"cell": "version", "reason": "must be a positive integer"}]
    return []


def _validate_config_shape(config: dict) -> list[dict[str, str]]:
    errors = _version_errors(config.get("version"))
    runner = config.get("runner")
    if not isinstance(runner, str) or not runner.strip():
        errors.append({"cell": "runner", "reason": "is required"})
    rows = config.get("rows")
    if not isinstance(rows, dict):
        return errors + [{"cell": "rows", "reason": "one row per role is required: " + ", ".join(ALLOWED_AGENTS)}]
    missing = [role for role in ALLOWED_AGENTS if role not in rows]
    extra = [role for role in rows if role not in ALLOWED_AGENTS]
    if missing or extra:
        reason = "one row per role is required"
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


class SessionRow(NamedTuple):
    agent: str
    host: str
    model: str
    effort: str


class InstallResult(NamedTuple):
    config: dict
    created: bool


def install_local_config() -> InstallResult:
    """Create models.json once from the roles' defaults in roles.json. An existing file is kept as
    it is, except that a role it has no row for gets its default: a role added to
    roles.json reaches a machine configured before it."""
    path = models_json_path()
    with config_lock(purpose="install models.json"):
        if path.is_file():
            config = read_local_config()
            rows = config.get("rows")
            missing = [role for role in ALLOWED_AGENTS
                       if isinstance(rows, dict) and role not in rows]
            if missing:
                defaults = default_local_config()["rows"]
                for role in missing:
                    rows[role] = defaults[role]
                config["version"] = int(config.get("version") or 0) + 1
                statedir.write_atomic(
                    path, json.dumps(config, ensure_ascii=False, indent=2) + "\n")
            return InstallResult(config, False)
        config = default_local_config()
        errors = _validate_config_shape(config)
        if errors:
            raise InvalidConfig(errors)
        statedir.write_atomic(
            path, json.dumps(config, ensure_ascii=False, indent=2) + "\n")
        return InstallResult(config, True)


def session_rows() -> list[SessionRow]:
    """One saved row per dispatched role, in the fixed role order."""
    config = read_local_config()
    errors = _validate_config_shape(config)
    if errors:
        raise InvalidConfig(errors)
    return [SessionRow(role, **config["rows"][role]) for role in ALLOWED_AGENTS]


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
    return runner_description(runner)["catalog"]


def runner_description(runner: str) -> dict:
    """Adapter-owned launch capability and optional host-tool executor."""
    if runner == "auto":
        runner = detected_runner(os.environ) or DEFAULT_RUNNER
    if runner == "cli":
        return {"catalog": "cli", "launch": "cli"}
    if not has_adapter(runner):
        return {"catalog": DEFAULT_CATALOG_MODE, "launch": ""}
    path = RUNNERS_DIR / f"{runner}.sh"
    prefix = "# MMW_RUNNER: "
    declaration = next((line[len(prefix):] for line in path.read_text().splitlines()
                        if line.startswith(prefix)), "null")
    description = json.loads(declaration)
    if not isinstance(description, dict) or not all(
            isinstance(description.get(key), str) and description[key]
            for key in ("catalog", "launch")):
        raise ValueError(f"runner {runner} returned no catalog and launch capability")
    if description.get("executor"):
        description["executor"] = str(RUNNERS_DIR / description["executor"])
    return description


def tool_executor() -> str:
    """Execution belongs to the caller's runner, even when it dispatches elsewhere."""
    caller = detected_runner(os.environ)
    return runner_description(caller).get("executor", "") if caller else ""


def _can_start(runner: str, host_spec: dict) -> bool:
    return runner_description(runner)["launch"] in host_spec


def detected_runner(environ: Mapping[str, str]) -> str | None:
    """The runner this process runs in, read from its environment, or None.

    Herdr when HERDR_ENV is set, Orca when TERM_PROGRAM says orca. Herdr is checked
    first because Herdr opened inside an Orca terminal keeps Orca's TERM_PROGRAM.
    A native App binding identifies its own session. Paseo is chosen only by name.
    """
    if (environ.get("HERDR_ENV") or "").strip():
        return "herdr"
    if (environ.get("TERM_PROGRAM") or "").strip().lower() == "orca":
        return "orca"
    if all(environ.get(key) for key in (
            "CODEX_THREAD_ID", "CODEX_APP_RUNTIME_CLI_PATH", "CODEX_APP_TOOLS_PIPE_PATH")):
        return "codex-app"
    return None


def _norm(text: str) -> str:
    return re.sub(r"[\s_]+", "-", text.strip().strip("`").lower())


def _want_fast(query: str) -> bool:
    return "fast" in _norm(query).split("-")


def _is_fast_id(model_id: str) -> bool:
    return bool(re.search(r"-fast$", model_id.lower()))


def match_offering(query: str, offerings: list[dict]) -> dict:
    """Pick the unique offering for an everyday name. Raise ValueError otherwise."""
    if not offerings:
        raise ValueError(f"host catalog is empty; {query!r} matches nothing")
    needle = _norm(query)
    hits = []
    for offering in offerings:
        oid = _norm(str(offering.get("id") or ""))
        name = _norm(str(offering.get("name") or ""))
        # Configuration displays ids through `_slug_everyday`; a displayed name
        # ("fable 5.1") must match the source id ("claude-fable-5-1").
        slug = _norm(_slug_everyday(str(offering.get("id") or "")))
        if needle in (oid, name, slug) or needle in oid or needle in name:
            hits.append(offering)
    # exact id, name or everyday name wins over substring
    exact = [
        o for o in hits
        if needle in (
            _norm(str(o.get("id") or "")),
            _norm(str(o.get("name") or "")),
            _norm(_slug_everyday(str(o.get("id") or ""))),
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


CATALOG_TIMEOUT = 45
_catalog_lock = threading.Lock()


class CatalogFailure(ValueError):
    def __init__(self, kind: str, detail: str):
        self.kind = kind
        self.detail = detail
        super().__init__(f"{kind}: {detail}")

    def record(self) -> dict:
        return {"kind": self.kind, "detail": self.detail, "at": statedir.now_iso()}


def _search_folders() -> list[str]:
    # LaunchAgents and non-login agent shells can omit the CLI installation directories
    # from PATH, even though the host and its interpreter are installed there.
    return [str(Path.home() / ".local" / "bin"), "/opt/homebrew/bin", "/usr/local/bin",
            *filter(None, (os.environ.get("PATH") or "").split(os.pathsep))]


def _which(name: str) -> str | None:
    for folder in _search_folders():
        candidate = Path(folder) / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def _binary(name: str) -> str:
    resolved = name if "/" in name else _which(name)
    if not resolved:
        raise CatalogFailure("missing", f"{name} not found; searched " + ", ".join(_search_folders()))
    return resolved


def _exit_failure(code: int, stderr: str) -> CatalogFailure:
    first = stderr.strip().splitlines()
    return CatalogFailure("exit", f"exit {code}: {first[0] if first else 'no error output'}")


def _command_env() -> dict[str, str]:
    return {**os.environ, "PATH": os.pathsep.join(_search_folders())}


def _run(argv: list[str], timeout: float = 30, stdin: str | None = None) -> str:
    resolved = _binary(argv[0])
    try:
        proc = subprocess.run([resolved, *argv[1:]], input=stdin, check=False,
                              capture_output=True, text=True, timeout=timeout,
                              env=_command_env())
    except subprocess.TimeoutExpired:
        raise CatalogFailure("timeout", f"{argv[0]} exceeded {timeout} seconds") from None
    except OSError as exc:
        raise CatalogFailure("exit", f"cannot execute {resolved}: {exc}") from exc
    if proc.returncode:
        raise _exit_failure(proc.returncode, proc.stderr)
    return proc.stdout or ""


def _runner_call(runner: str, verb: str, *args: str, timeout: float = 30) -> str:
    _binary(runner)
    adapter = RUNNERS_DIR / f"{runner}.sh"
    return _run(["bash", str(adapter), verb, *args], timeout=timeout)


def _codex_model_list(binary: str | None = None) -> str:
    binary = _binary(binary or HOST_BINARIES.get("codex"))
    deadline = time.monotonic() + CATALOG_TIMEOUT
    with tempfile.TemporaryFile() as errors:
        try:
            proc = subprocess.Popen([binary, "app-server"], stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=errors, env=_command_env(), bufsize=0)
        except OSError as exc:
            raise CatalogFailure("exit", f"cannot execute {binary}: {exc}") from exc
        buffer = b""
        raw = ""

        def send(message):
            proc.stdin.write((json.dumps(message) + "\n").encode())
            proc.stdin.flush()

        def answer(ident):
            nonlocal buffer, raw
            raw = ""
            while True:
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    raw += line.decode("utf-8", errors="replace") + "\n"
                    try:
                        data = json.loads(line)
                    except (ValueError, UnicodeError):
                        raise CatalogFailure("unparseable", raw[:200]) from None
                    if isinstance(data, dict) and data.get("id") == ident:
                        if "error" in data or not isinstance(data.get("result"), dict):
                            raise CatalogFailure("unparseable", raw[:200])
                        return json.dumps(data["result"])
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not select.select([proc.stdout], [], [], remaining)[0]:
                    raise CatalogFailure("timeout", f"codex exceeded {CATALOG_TIMEOUT} seconds")
                chunk = os.read(proc.stdout.fileno(), 65536)
                if not chunk:
                    code = proc.wait(timeout=max(0.01, deadline - time.monotonic()))
                    errors.seek(0)
                    stderr = errors.read().decode("utf-8", errors="replace")
                    if code:
                        raise _exit_failure(code, stderr)
                    raise CatalogFailure("unparseable", (raw + buffer.decode(errors="replace"))[:200])
                buffer += chunk

        try:
            send({"id": 1, "method": "initialize", "params": {
                "clientInfo": {"name": "mmw", "title": "MMW", "version": "4"}}})
            answer(1)
            send({"method": "initialized"})
            send({"id": 2, "method": "model/list", "params": {}})
            return answer(2)
        except (BrokenPipeError, subprocess.TimeoutExpired) as exc:
            if isinstance(exc, subprocess.TimeoutExpired):
                raise CatalogFailure("timeout", f"codex exceeded {CATALOG_TIMEOUT} seconds") from None
            code = proc.poll()
            errors.seek(0)
            stderr = errors.read().decode(errors="replace")
            if code:
                raise _exit_failure(code, stderr) from None
            raise CatalogFailure("unparseable", f"codex closed stdin before model/list: {stderr[:200]}") from None
        finally:
            if proc.poll() is None:
                proc.terminate()
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            proc.stdin.close()
            proc.stdout.close()


# Claude Code has no model-listing subcommand. One `list_models` control request over
# `-p` stream-json returns its `/model` picker without starting an API turn (Claude
# Code 2.1.280, measured 2026-09-23: about 2 s; the same request Orca 1.4.205 sends in
# `out/shared/claude-model-list-probe.js`).
CLAUDE_LIST_MODELS_ARGS = [
    "claude", "-p", "--input-format", "stream-json", "--output-format", "stream-json",
    "--verbose", "--no-session-persistence"]
CLAUDE_LIST_MODELS_STDIN = json.dumps({
    "type": "control_request", "request_id": "mmw-model-list",
    "request": {"subtype": "list_models"}}) + "\n"
# A picker row pinned to one version (`claude-fable-5-1[1m]`) is saved as its family
# alias (`fable[1m]`), so the row follows the family's newest model like `opus[1m]` does.
_CLAUDE_PINNED = re.compile(r"^claude-(fable|opus|sonnet|haiku)-[\d-]+(\[[^\]]*\])?$", re.I)


def _parse_claude_model_list(text: str) -> list[dict]:
    """The `/model` picker as offerings: family aliases, per-model efforts, and a note
    naming the model the alias resolves to today (`Opus 5.5 with 1M context`)."""
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{") or "control_response" not in line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = data.get("response") if isinstance(data, dict) else None
        if not isinstance(response, dict) or response.get("subtype") != "success":
            continue
        payload = response.get("response")
        rows = payload.get("models") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            continue
        out, seen = [], set()
        for item in rows:
            if not isinstance(item, dict) or item.get("disabled") is True:
                continue
            ident = str(item.get("value") or "").strip()
            # `default` repeats whichever row it resolves to.
            if not ident or ident == "default":
                continue
            pinned = _CLAUDE_PINNED.match(ident)
            if pinned:
                ident = pinned.group(1).lower() + (pinned.group(2) or "")
            if ident in seen:
                continue
            seen.add(ident)
            levels = item.get("supportedEffortLevels") if item.get("supportsEffort") else []
            note = str(item.get("description") or "").split(" · ", 1)[0].strip()
            out.append({"id": ident, "name": ident,
                        "thinkingOptionIds": [str(x) for x in levels or [] if x],
                        "note": note})
        return out
    raise CatalogFailure("unparseable", text[:200])


def _parse_codex_model_list(text: str) -> list[dict]:
    try:
        data = json.loads(text)
        rows = data.get("data") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            raise ValueError("expected model/list data")
        out = []
        for item in rows:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                raise ValueError("expected a model id")
            if item.get("hidden") is not False:
                continue
            out.append({"id": item["id"], "name": item["displayName"],
                        "thinkingOptionIds": [level["reasoningEffort"]
                                              for level in item["supportedReasoningEfforts"]],
                        "isDefault": item["isDefault"]})
        return out
    except (ValueError, KeyError, TypeError):
        raise CatalogFailure("unparseable", text[:200]) from None


def _host_efforts(host: str, offering: dict | None = None) -> list[str]:
    ids = [str(x) for x in ((offering or {}).get("thinkingOptionIds") or []) if x]
    if ids:
        return ids
    spec = load_hosts()["hosts"].get(host) or {}
    return [str(x) for x in (spec.get("efforts") or [])]


def read_catalog_cache() -> dict:
    path = statedir.home() / "catalog.json"
    try:
        data = statedir.read_json(path, {})
        if not isinstance(data, dict):
            raise ValueError("expected a catalog object")
        return data
    except (json.JSONDecodeError, ValueError) as exc:
        sys.stderr.write(f"models.py: cannot read catalog cache at {path}: {exc}; "
                         "ignoring cache and rebuilding from host reads\n")
        return {}
    except OSError as exc:
        raise ValueError(f"cannot read catalog cache at {path}: {exc}; remove the cache and scan again") from exc


def _store_catalog(source: str, host: str, entry: dict) -> dict:
    path = statedir.home() / "catalog.json"
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with _catalog_lock, statedir.locked(path.with_suffix(".lock"), purpose="write catalog.json"):
        cache = read_catalog_cache()
        section = cache.setdefault(source, {})
        if "failure" in entry:
            entry = {**section.get(host, {}), **entry}
        section[host] = entry
        statedir.write_atomic(path, json.dumps(cache, ensure_ascii=False, indent=2) + "\n")
    return entry


def _catalog_version(host: str, source: str) -> str:
    if source not in ("cli", "paseo"):
        return _run(["bash", str(RUNNERS_DIR / f"{source}.sh"),
                     "catalog-version", host]).strip()
    return _run([HOST_BINARIES.get(host), "--version"]).strip()


def _read_catalog(host: str, source: str, version: str | None = None) -> dict:
    try:
        version = version if version is not None else _catalog_version(host, source)
        if source == "paseo":
            raw = _runner_call("paseo", "catalog-models", host, timeout=CATALOG_TIMEOUT)
            try:
                rows = json.loads(raw)
                if not isinstance(rows, list):
                    raise ValueError("expected Paseo model list")
                offerings = [{"id": item["id"], "name": item.get("model") or item["id"],
                              "thinkingOptionIds": item.get("thinkingOptionIds") or []}
                             for item in rows]
            except (ValueError, KeyError, TypeError):
                raise CatalogFailure("unparseable", raw[:200]) from None
        elif source != "cli":
            raw = _run(["bash", str(RUNNERS_DIR / f"{source}.sh"),
                        "catalog-models", host], timeout=CATALOG_TIMEOUT)
            try:
                offerings = json.loads(raw)
                if not isinstance(offerings, list) or not all(
                        isinstance(item, dict) and isinstance(item.get("id"), str)
                        for item in offerings):
                    raise ValueError("expected adapter model offerings")
            except ValueError:
                raise CatalogFailure("unparseable", raw[:200]) from None
        elif host == "claude":
            offerings = _parse_claude_model_list(_run(
                CLAUDE_LIST_MODELS_ARGS, timeout=60, stdin=CLAUDE_LIST_MODELS_STDIN))
        else:
            offerings = _parse_codex_model_list(_codex_model_list())
        if not offerings:
            raise CatalogFailure("empty", f"{host} returned an empty model list")
        return _store_catalog(source, host, {"offerings": offerings, "read_at": statedir.now_iso(),
                                             "version": version})
    except CatalogFailure as exc:
        return _store_catalog(source, host, {"failure": exc.record()})


def _cached_host_result(host: str, source: str, record: dict) -> dict:
    failure = record.get("failure")
    state = "missing" if failure and failure["kind"] == "missing" else "silent" if failure else "ok"
    offerings = record.get("offerings") or []
    result = {**_host_result(state, _offered_rows(host, offerings, source)),
              "read_at": record.get("read_at", ""), "ids": [item["id"] for item in offerings]}
    if failure:
        result["failure"] = failure
    return result


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
    text = re.sub(r"^claude-", "", text, flags=re.I)
    text = re.sub(r"(?<=\D)(\d)-(\d)(?=\D|$)", r"\1.\2", text)
    if "/" in text:
        text = text.split("/", 1)[-1]
    text = text.replace("-", " ").replace("_", " ")
    return re.sub(r"\s+", " ", text).strip().lower()


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


def everyday_name(offering: dict) -> str:
    """The name a catalog offering goes by in models.json rows and on the board."""
    ident = str(offering.get("id") or "")
    name = str(offering.get("name") or ident)
    if name and name.lower() != ident.lower() and not re.search(r"\d", name):
        return name.lower().strip()
    return _slug_everyday(name if re.search(r"\d", name) else ident)


def fillable_rows(host: str, offerings: list[dict]) -> list[tuple[str, str]]:
    """Return the model and effort names accepted by configuration commands."""
    rows = []
    seen = set()
    for offering in offerings:
        model = everyday_name(offering)
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


_CLAUDE_BRACKET_SUFFIX = re.compile(r"^(.+?)(\[[^\[\]]+\])$")


def _resolve_from_offerings(host: str, model: str, effort: str,
                            offerings: list[dict], source: str) -> tuple[str, str, str]:
    hosts = load_hosts()["hosts"]
    if host not in hosts:
        raise ValueError(f"unknown host {host}")
    spec = hosts[host]
    try:
        offering = match_offering(model, offerings)
        resolved = str(offering.get("id") or "")
    except ValueError:
        # Claude Code's own `/model` picker is this catalog, and a picker upgrade can
        # stop listing a bracket suffix (`[1m]`, 1M context) as a row of its own even
        # though the CLI still accepts it appended to a family name. When the full name
        # does not match, a bracketed claude row is matched by the name in front of the
        # bracket instead, checked for effort against that catalog entry, and passed on
        # to the CLI exactly as the configuration wrote it.
        bracket = _CLAUDE_BRACKET_SUFFIX.match(model) if host == "claude" else None
        if not bracket:
            raise
        offering = match_offering(bracket.group(1), offerings)
        resolved = model
    allowed = [str(x) for x in spec.get("efforts") or []]
    if allowed and effort not in ("—", "-", ""):
        names = [str(x) for x in (offering.get("thinkingOptionIds") or allowed)]
        if effort not in names and effort not in allowed:
            raise ValueError(f"effort {effort!r} is not one of {', '.join(allowed)}")
    return host, resolved, effort


def _offered_rows(host: str, offerings: list[dict], source: str) -> list[dict]:
    rows: list[dict] = []
    by_model: dict[str, dict] = {}
    for model, effort_text in fillable_rows(host, offerings):
        efforts = [part.strip() for part in effort_text.split(",") if part.strip()]
        for effort in efforts or ["—"]:
            try:
                _, resolved, _ = _resolve_from_offerings(host, model, effort, offerings, source)
            except ValueError:
                continue
            if model not in by_model:
                by_model[model] = {"model": model, "efforts": []}
                note = next((str(o.get("note") or "") for o in offerings
                             if str(o.get("id") or "") == resolved), "")
                if note:
                    by_model[model]["note"] = note
                rows.append(by_model[model])
            if effort not in by_model[model]["efforts"]:
                by_model[model]["efforts"].append(effort)
    return rows


def _host_result(state: str, offered: list[dict] | None = None) -> dict:
    return {"state": state, "label": _STATE_LABELS[state], "offered": offered or [], "read_at": ""}


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
    else:
        return _cached_host_result(host, source, _read_catalog(host, source))
    if state not in _STATE_LABELS:
        raise ValueError(f"MMW_HOST_CATALOG gives {host} unknown state {state!r}")
    result = _host_result(
        state, _offered_rows(host, offerings, source) if state == "ok" else [])
    if isinstance(entry, dict):
        result["read_at"] = str(entry.get("read_at") or "")
        if entry.get("failure"):
            result["failure"] = entry["failure"]
    return result


def cached_host_catalogs(runner: str) -> dict:
    """The persisted catalog without starting any host command."""
    source = catalog_source(runner)
    entries = read_catalog_cache().get(source, {})
    hosts = {}
    for host in CLI_HOSTS:
        spec = load_hosts()["hosts"].get(host) or {}
        if not _can_start(runner, spec):
            hosts[host] = _host_result("unlaunchable")
        elif host in entries:
            hosts[host] = _cached_host_result(host, source, entries[host])
        else:
            hosts[host] = {**_host_result("silent"), "read_at": ""}
    return {"source": source, "scanned_at": max(
        (entry.get("read_at", "") for entry in entries.values()), default=""),
        "scanning": False, "hosts": hosts}


def scan_host_catalogs(runner: str, hosts: Sequence[str] = CLI_HOSTS) -> dict:
    """Scan all requested hosts concurrently from the source the runner will use."""
    source = catalog_source(runner)
    fixture = _fixture_catalog()
    selected = [host for host in CLI_HOSTS if host in hosts]

    paseo_down = False
    paseo_failure = None
    if source == "paseo":
        if fixture is not None:
            paseo = fixture.get("paseo")
            paseo_down = isinstance(paseo, dict) and paseo.get("state") == "down"
        else:
            try:
                status = _runner_call("paseo", "catalog-status")
                if not status.strip():
                    raise CatalogFailure("empty", "paseo returned an empty provider list")
            except CatalogFailure as exc:
                paseo_down = True
                paseo_failure = exc
    if paseo_down:
        result = {}
        for host in selected:
            if paseo_failure:
                record = _store_catalog(source, host, {"failure": paseo_failure.record()})
                result[host] = {**_cached_host_result(host, source, record),
                                "state": "down", "label": _STATE_LABELS["down"]}
            else:
                result[host] = _host_result("down")
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


def _offered_row(offered: list[dict], host: str, model: str) -> dict | None:
    """The scanned catalog row for a configured model; a bracketed claude name
    (`opus[1m]`) the picker does not list as a row of its own is checked against the
    row of the name in front of the bracket, as `_resolve_from_offerings` resolves it."""
    for name in (model, *(m.group(1) for m in [_CLAUDE_BRACKET_SUFFIX.match(model)]
                          if m and host == "claude")):
        row = next((item for item in offered if item.get("model") == name), None)
        if row is not None:
            return row
    return None


def _validate_local_config(config: dict, scan: dict,
                           roles: Sequence[str] | None = None) -> list[dict[str, str]]:
    errors = _validate_config_shape(config)
    runner = config.get("runner")
    valid_runner = runner == "auto" or (isinstance(runner, str) and has_adapter(runner))
    if not valid_runner:
        errors.append({"cell": "runner", "reason":
                       f"{runner!r} has no adapter; choose one of {', '.join(config_runners())}"})
    required_source = catalog_source(str(runner)) if valid_runner else None
    if valid_runner and scan.get("source") != required_source:
        errors.append({"cell": "runner",
                       "reason": f"runner {runner} requires a fresh {required_source} scan; scan it and retry"})
    rows = config.get("rows")
    if not isinstance(rows, dict):
        return errors
    checked = set(roles or ALLOWED_AGENTS)
    catalog_hosts = scan.get("hosts") if isinstance(scan, dict) else {}
    host_specs = load_hosts()["hosts"]
    for role in ALLOWED_AGENTS:
        row = rows.get(role)
        if not isinstance(row, dict) or role not in checked:
            continue
        host = row.get("host")
        if host not in host_specs:
            errors.append({"cell": f"{role}.host", "reason": f"unknown host {host!r}"})
            continue
        launch_block = runner_description(str(runner))["launch"] if valid_runner else ""
        if valid_runner and not _can_start(str(runner), host_specs[host]):
            errors.append({"cell": f"{role}.host",
                           "reason": f"runner {runner} cannot start host {host}: hosts.json has no {launch_block} block; choose another host or runner"})
            continue
        found = catalog_hosts.get(host) if isinstance(catalog_hosts, dict) else None
        if not isinstance(found, dict) or found.get("state") != "ok":
            state = found.get("label") if isinstance(found, dict) else "was not scanned"
            if isinstance(found, dict) and found.get("failure"):
                failure = found["failure"]
                state = f"{state}; {failure['kind']}: {failure['detail']}"
            errors.append({"cell": f"{role}.host", "reason":
                           f"host {host} is unavailable: {state}; restore it and scan again"})
            continue
        model = row.get("model")
        offered = _offered_row(found.get("offered") or [], host, str(model))
        if offered is None:
            choices = ", ".join(item["model"] for item in found.get("offered") or [])
            ids = ", ".join(found.get("ids") or [])
            errors.append({"cell": f"{role}.model",
                           "reason": f"{role} saved model {model!r} is not in the current {scan.get('source')} catalog for {host}; choose one of {choices}" + (f" (ids: {ids})" if ids else "")})
            continue
        effort = row.get("effort")
        if effort not in (offered.get("efforts") or []):
            errors.append({"cell": f"{role}.effort",
                           "reason": f"effort {effort!r} is not offered for {host} model {model!r}; choose an offered effort"})
    return errors


def check_local_config(config: dict | None = None) -> tuple[dict, dict, list[dict[str, str]]]:
    """Read and scan the saved configuration once, returning every validation error."""
    current = read_local_config() if config is None else config
    runner = str(current.get("runner") or "")
    scan = scan_host_catalogs(runner)
    return current, scan, _validate_local_config(current, scan)


def max_workers() -> int:
    """max_workers() reads the saved night cap, or DEFAULT_MAX_WORKERS when absent, without checking roles."""
    value = read_local_config().get("max_workers", DEFAULT_MAX_WORKERS)
    _validate_max_workers(value)
    return value


def _validate_max_workers(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise InvalidConfig([{"cell": "max_workers",
                              "reason": "must be a whole number of at least 1"}])


SUBAGENT_CLAUDE_CHOICES = {
    "model": ("sonnet", "opus", "haiku", "fable"),
    "effort": ("low", "medium", "high", "xhigh", "max"),
}


def _codex_subagent_offerings() -> list[dict]:
    """The stored cli codex catalog, which a subagent's codex cell is checked against."""
    return read_catalog_cache().get("cli", {}).get("codex", {}).get("offerings", [])


def _common_efforts(offerings: list[dict]) -> list[str]:
    levels = [set(item.get("thinkingOptionIds", [])) for item in offerings]
    return _sort_efforts(list(set.intersection(*levels))) if levels else []


def subagent_choices() -> dict:
    """What each subagent cell may hold besides `inherit`: rows, claude's fixed values, codex's catalog ids."""
    offerings = _codex_subagent_offerings()
    return {
        "rows": list(subagent_rows()),
        "claude": {"models": list(SUBAGENT_CLAUDE_CHOICES["model"]),
                   "efforts": list(SUBAGENT_CLAUDE_CHOICES["effort"])},
        "codex": {
            "models": [{"model": item["id"], "efforts": list(item.get("thinkingOptionIds", []))}
                       for item in offerings],
            "inherit_efforts": _common_efforts(offerings),
        },
    }


def model_labels(ids: dict[str, list[str]]) -> dict[str, dict[str, str]]:
    """The board's name for each model id per host: its everyday name, then " · <note>" when the
    stored cli catalog has one; an id the catalog no longer lists gets its everyday spelling."""
    cache = read_catalog_cache().get("cli", {})
    labels: dict[str, dict[str, str]] = {}
    for host, wanted in ids.items():
        offered = {str(o.get("id")): o for o in cache.get(host, {}).get("offerings", [])}
        labels[host] = {}
        for ident in wanted:
            offering = offered.get(ident)
            name = everyday_name(offering) if offering else _slug_everyday(ident)
            note = str(offering.get("note") or "") if offering else ""
            labels[host][ident] = f"{name} · {note}" if note else name
    return labels


def _validate_subagents(value: object) -> list[dict[str, str]]:
    errors = []
    names = subagent_rows()
    if not isinstance(value, dict):
        return [{"cell": "subagents", "reason": "must map a subagent row to host settings"}]
    for name, hosts in value.items():
        cell = f"subagents.{name}"
        if name not in names:
            errors.append({"cell": cell, "reason": f"unknown row; choose one of {', '.join(names)}"})
            continue
        if not isinstance(hosts, dict):
            errors.append({"cell": cell, "reason": "must map hosts to model and effort"})
            continue
        for host, row in hosts.items():
            host_cell = f"{cell}.{host}"
            if host not in CLI_HOSTS:
                errors.append({"cell": host_cell, "reason": f"choose one of {', '.join(CLI_HOSTS)}"})
                continue
            if not isinstance(row, dict):
                errors.append({"cell": host_cell, "reason": "must contain model and effort"})
                continue
            if host == "claude":
                for key, values in SUBAGENT_CLAUDE_CHOICES.items():
                    allowed = (*values, "inherit")
                    if row.get(key, "inherit") not in allowed:
                        errors.append({"cell": f"{host_cell}.{key}", "reason":
                                       f"choose one of {', '.join(allowed)}"})
            else:
                offerings = _codex_subagent_offerings()
                offered = {item["id"]: item for item in offerings}
                model = row.get("model", "inherit")
                if not isinstance(model, str) or model not in (*offered, "inherit"):
                    reason = f"choose one of {', '.join((*offered, 'inherit'))}"
                    if not offered:
                        reason += "; no cli codex catalog at " + str(statedir.home() / "catalog.json")
                        reason += "; click 重新扫描 on the board or run install.sh --check first"
                    errors.append({"cell": f"{host_cell}.model", "reason": reason})
                    continue
                if model == "inherit":
                    efforts = _common_efforts(offerings)
                else:
                    efforts = offered[model].get("thinkingOptionIds", [])
                if row.get("effort", "inherit") not in (*efforts, "inherit"):
                    errors.append({"cell": f"{host_cell}.effort", "reason":
                                   f"choose one of {', '.join((*efforts, 'inherit'))} for codex model {model!r}"})
    return errors


def write_local_config(config: dict, expected_version: int, scan: dict | None,
                       *, validate_roles: Sequence[str] | None = None,
                       merge_subagents: bool = False) -> dict:
    """Validate, lock, version-check, and atomically replace models.json.

    With scan=None, update max_workers or subagents and keep runner and rows unchecked.
    With merge_subagents=True, validate supplied cells and merge them into the saved table.
    """
    path = models_json_path()
    if not path.is_file():
        raise ConfigMissing(f"no models.json at {path}; run install.sh first")
    if "max_workers" in config:
        _validate_max_workers(config.get("max_workers"))
    if scan is None:
        errors = _version_errors(expected_version)
    else:
        errors = _validate_local_config(config, scan, validate_roles)
    if "subagents" in config:
        errors += _validate_subagents(config["subagents"])
    if errors:
        raise InvalidConfig(errors)
    try:
        with config_lock():
            current = read_local_config()
            found_version = current.get("version")
            if found_version != expected_version:
                raise VersionConflict(expected_version, found_version, _modified_at(path))
            if scan is None:
                written = {**current, "version": expected_version + 1}
            else:
                written = {
                    "version": expected_version + 1,
                    "runner": config["runner"],
                    "rows": {
                        role: {key: config["rows"][role][key]
                               for key in ("host", "model", "effort")}
                        for role in ALLOWED_AGENTS
                    },
                }
            cap_config = config if "max_workers" in config else current
            if "max_workers" in cap_config:
                written["max_workers"] = cap_config["max_workers"]
            subagents_config = config if "subagents" in config else current
            if "subagents" in subagents_config:
                subagents = subagents_config["subagents"]
                if merge_subagents:
                    saved = current.get("subagents", {})
                    if not isinstance(saved, dict):
                        raise InvalidConfig([{"cell": "subagents", "reason": "must be a settings object"}])
                    subagents = dict(saved)
                    for name, patch in config["subagents"].items():
                        hosts = saved.get(name, {})
                        if not isinstance(hosts, dict):
                            raise InvalidConfig([{"cell": f"subagents.{name}",
                                                  "reason": "must map hosts to model and effort"}])
                        subagents[name] = {**hosts, **patch}
                written["subagents"] = subagents
            statedir.write_atomic(path, json.dumps(written, ensure_ascii=False, indent=2) + "\n")
            return written
    except statedir.LockHeld as exc:
        raise ConfigLockHeld(exc) from None


def fetch_offerings(host: str) -> list[dict]:
    mode = os.environ.get("MMW_CATALOG_MODE", DEFAULT_CATALOG_MODE)
    fixture = _fixture_catalog()
    if fixture is not None:
        return _fixture_offerings(fixture, mode, host)
    stored = read_catalog_cache().get(mode, {}).get(host, {})
    try:
        version = _catalog_version(host, mode)
    except CatalogFailure as exc:
        record = _store_catalog(mode, host, {"failure": exc.record()})
    else:
        if stored.get("offerings") and version == stored.get("version"):
            return stored["offerings"]
        record = _read_catalog(host, mode, version)
    failure = record.get("failure")
    if failure:
        if not record.get("offerings"):
            raise CatalogFailure(failure["kind"], failure["detail"])
        sys.stderr.write(f"models.py: {host} {failure['kind']}: {failure['detail']}; "
                         f"using catalog read at {record['read_at']}\n")
    return record.get("offerings") or []


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
                if argv and argv[-1] in ("--effort", "-c"):
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
    if not (spec.get("paseo") or {}).get("thinking"):
        return None
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
    """Tonight's runner: MMW_RUNNER, then models.json's `runner`. Either one saying
    `auto`, or neither saying anything, means the runner this process runs in
    (`detected_runner`), then orca. A named runner is returned as given, adapter or
    not: `start` refuses one it has no adapter for, by name."""
    env = os.environ if environ is None else environ
    for value in (env.get("MMW_RUNNER"), read_local_config().get("runner")):
        spoken = _spoken_runner(value)
        if spoken == "auto":
            break
        if spoken:
            return spoken
    return detected_runner(env) or DEFAULT_RUNNER


def paseo_run_args(host: str, model: str, effort: str) -> list[str]:
    """The `paseo run` flags for a host: provider/model, mode and thinking option.

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

    The model is the host's own id, passed through unchanged. models.json keeps everyday
    names (`gpt 5.6 sol`), which a host refuses; `row <role>` prints the row with the
    name resolved against the runner's catalog, which is what `dispatch.sh` hands here.

    Each host with a launch block takes an initial prompt as its last positional
    argument (`codex [PROMPT]`, `claude [prompt]`), so a runner that starts the host from this line does not type the prompt
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
         "       models.py config set <role> <host> <model> <level>\n"
         "       models.py config set max_workers <n>\n"
         "       models.py config subagent <row> <host> <model|inherit> <effort|inherit>\n"
         "       models.py subagent <row> <host>\n"
         "       models.py runner\n"
         "       models.py executor\n"
         "       models.py catalog-source <runner>\n"
         "       models.py paseo-args <host> <model> <level>\n"
         "       models.py row <role>\n"
         "       models.py bypass-argv <host> <model-id> <level> <name>\n"
         "       models.py launch-line <host> <model-id> <level> <name> [<prompt>]\n")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["executor"]:
        print(tool_executor())
        return 0
    if len(args) == 2 and args[0] == "catalog-source":
        print(catalog_source(args[1]))
        return 0
    if len(args) == 3 and args[0] == "subagent":
        try:
            row = subagent_row(*args[1:])
            print(f"model={row['model']} effort={row['effort']}")
            return 0
        except (ValueError, OSError) as exc:
            sys.stderr.write(f"models.py: {exc}\n")
            return 2
    if args[:1] == ["config"]:
        try:
            if args == ["config", "show"]:
                print(json.dumps(read_local_config(), ensure_ascii=False, indent=2))
                return 0
            if len(args) == 6 and args[1] == "subagent":
                name, host, model, effort = args[2:]
                current = read_local_config()
                subagents = {name: {host: {"model": model, "effort": effort}}}
                written = write_local_config({"subagents": subagents}, current.get("version"), None,
                                             merge_subagents=True)
                print(json.dumps(written, ensure_ascii=False))
                return 0
            if len(args) == 4 and args[1:3] == ["set", "max_workers"]:
                try:
                    value = int(args[3])
                except ValueError:
                    raise InvalidConfig([{"cell": "max_workers",
                                          "reason": "must be a whole number of at least 1"}]) from None
                current = read_local_config()
                written = write_local_config(
                    {"max_workers": value}, current.get("version"), None)
                print(json.dumps(written, ensure_ascii=False))
                return 0
            if len(args) == 3 and args[1] == "runner":
                current = read_local_config()
                proposed = json.loads(json.dumps(current))
                proposed.pop("max_workers", None)
                proposed.pop("subagents", None)
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
                proposed.pop("max_workers", None)
                proposed.pop("subagents", None)
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
    if len(args) == 2 and args[0] == "row":
        try:
            print(row_tsv(args[1]))
        except (ValueError, OSError) as exc:
            sys.stderr.write(f"models.py: cannot resolve the {args[1]} row: {exc}\n")
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
