"""读本机活表，问今晚的目录，再按 hosts.json 展开成启动参数。

活表是 ~/.mmw/models.md（MMW_LIVE_MODELS / MMW_V2_HOME 可改）。hosts.json 跟着
技能走，记下每个 host 在 Herdr 和 Paseo 上怎么起，以及第一次 install 拷进活表的
默认行。`python3 models.py offerings` 扫五个 CLI host 的目录，写在活表下半；
`start` 不读那一块。dispatch.sh 的 start 与 install.sh 共用本文件。
"""

from __future__ import annotations

import json
import shlex
import os
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import NamedTuple

SKILL_DIR = Path(__file__).resolve().parent.parent
HOSTS_JSON = SKILL_DIR / "hosts.json"
ALLOWED_AGENTS = (
    "junior-worker", "senior-worker", "reviewer", "verifier", "advisor")
# Lody cuts its own worktree. Level 4 must not pick it; ticket / env / live may.
WORKTREE_OWNING = frozenset({"lody"})
DEFAULT_RUNNER = "orca"
# Herdr checkout asks the host CLI; Paseo checkout asks paseo. Tests set
# MMW_CATALOG_MODE or MMW_HOST_CATALOG.
DEFAULT_CATALOG_MODE = "herdr"
CLI_HOSTS = ("cursor", "grok", "claude", "codex", "pi")
OFFERINGS_BEGIN = "<!-- mmw-offerings -->"
OFFERINGS_END = "<!-- /mmw-offerings -->"
_CURSOR_EFFORT_IN_ID = re.compile(
    r"-(none|low|medium|high|xhigh|max)(?:-fast)?$", re.I)


def live_path() -> Path:
    override = os.environ.get("MMW_LIVE_MODELS")
    if override:
        return Path(override)
    home = os.environ.get("MMW_V2_HOME") or os.environ.get("HOME") or ""
    return Path(home) / ".mmw" / "models.md"


# Tests and older callers still assign MODELS; live_path() wins unless this is set.
MODELS: Path | None = None


def _models_file() -> Path:
    return MODELS if MODELS is not None else live_path()


def load_hosts() -> dict:
    if not HOSTS_JSON.is_file():
        raise ValueError(f"缺 hosts.json：{HOSTS_JSON}")
    data = json.loads(HOSTS_JSON.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "hosts" not in data:
        raise ValueError(f"{HOSTS_JSON} 不是一份 host 启动表")
    return data


class _HostBinaries:
    def get(self, key, default=None):
        spec = load_hosts()["hosts"].get(key) or {}
        return spec.get("binary", default if default is not None else key)


HOST_BINARIES = _HostBinaries()


def default_live_markdown() -> str:
    rows = load_hosts().get("defaults") or []
    lines = [
        "# Models",
        "",
        "This machine's table. `start` reads the rows. Copy `model` and `effort` from the tables below.",
        "Do not commit this file. First `install.sh` copies the defaults; later ones leave the rows",
        "and refresh the copy-tables.",
        "",
        "| runner | orca |",
        "| --- | --- |",
        "",
        "| agent | host | model | effort |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {agent} | {host} | {model} | {effort} |".format(**row))
    lines.append("")
    return "\n".join(lines)


def adopt_live_table() -> bool:
    """Write the default table if the live file is missing. Return True if written."""
    dest = live_path()
    if dest.is_file():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(default_live_markdown(), encoding="utf-8")
    return True


def strip_offerings(text: str) -> str:
    """Keep the fill-in table; drop a previous scanned catalog block."""
    start = text.find(OFFERINGS_BEGIN)
    if start == -1:
        return text.rstrip() + "\n"
    end = text.find(OFFERINGS_END)
    if end == -1:
        return text[:start].rstrip() + "\n"
    after = text[end + len(OFFERINGS_END):]
    return (text[:start] + after).strip() + "\n"


def parse_live_rows(path: Path | None = None) -> list[tuple[str, str, str, str]]:
    """活表每一行：(agent, host, model, effort)。"""
    source = path or _models_file()
    if not source.is_file():
        raise ValueError(f"缺活表：{source}；跑 install.sh")
    rows: list[tuple[str, str, str, str]] = []
    text = source.read_text(encoding="utf-8")
    cut = text.find(OFFERINGS_BEGIN)
    if cut != -1:
        text = text[:cut]
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
            raise ValueError(f"{source}: {agent} 不是派出的角色")
        if not host or not model:
            raise ValueError(f"{source}: {agent} 缺 host 或 model")
        rows.append((agent, host, model, effort))
    if not rows:
        raise ValueError(f"{source} 里一行 agent 都没有")
    return rows


class SessionRow(NamedTuple):
    agent: str
    host: str
    model: str
    effort: str


def session_rows(path: Path | None = None) -> list[SessionRow]:
    """一个 agent 一行：今晚这个角色跑在哪，只有一个答案。"""
    source = path or _models_file()
    seen: set[str] = set()
    out: list[SessionRow] = []
    for agent, host, model, effort in parse_live_rows(source):
        if agent in seen:
            raise ValueError(
                f"{source}: {agent} has two rows, and an agent has one; "
                f"delete the row you do not want tonight")
        seen.add(agent)
        out.append(SessionRow(agent, host, model, effort))
    return out


def bypass_rows(path: Path | None = None) -> list[SessionRow]:
    """旧名：全部派出的行都是会话。"""
    return session_rows(path)


def parse_live_runner(path: Path | None = None) -> str | None:
    """活表的 runner 行。没有这一行、或格子是空的，返回 None。"""
    source = path or _models_file()
    if not source.is_file():
        return None
    text = source.read_text(encoding="utf-8")
    cut = text.find(OFFERINGS_BEGIN)
    if cut != -1:
        text = text[:cut]
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip().strip("`").strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        if cells[0].lower() != "runner":
            continue
        if set(cells[1]) <= set("- "):
            continue
        spoken = _spoken_runner(cells[1])
        if spoken:
            return spoken
    return None


def _spoken_runner(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip().strip("`").lower()
    if not text or text in ("—", "-", "none"):
        return None
    return text


def runtime_from_environ(environ: Mapping[str, str]) -> tuple[str, ...]:
    """Runners visible in this process: TERM_PROGRAM, then HERDR_ENV, then TMUX.

    Environment variables cannot express nesting. TERM_PROGRAM is treated as
    the outer signal: Herdr opened inside an Orca terminal is herdr, not orca.
    When HERDR_ENV and TMUX are both set, this returns tmux last; that does not
    say which is nested in which.
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
    """First speaker wins: ticket, env, live table, innermost runtime, default."""
    for value in (ticket, env, live):
        spoken = _spoken_runner(value)
        if spoken:
            return spoken
    if isinstance(runtime, Mapping):
        names = runtime_from_environ(runtime)
    else:
        names = tuple(
            spoken for spoken in (_spoken_runner(n) for n in runtime) if spoken)
    detected = [name for name in names if name not in WORKTREE_OWNING]
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
        # The block under the live table renders ids through `_slug_everyday`,
        # so a cell copied from it ("fable 5.1") must match the id it was
        # rendered from ("claude-fable-5-1"). Compare against that form too, or
        # the table tells you to write a name nothing can resolve.
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
    raw = _run(["paseo", "provider", "models", host, "--json"])
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
    catalog = os.environ.get("MMW_HOST_CATALOG")
    if catalog:
        data = json.loads(Path(catalog).read_text(encoding="utf-8"))
        return {host: list(data.get(host) or []) for host in CLI_HOSTS}
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
    """(model cell, effort cell) — the two values to copy into the live table."""
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


def offerings_markdown(catalogs: dict | None = None) -> str:
    catalogs = catalogs if catalogs is not None else scan_cli_catalogs()
    lines = [
        OFFERINGS_BEGIN,
        "## What to write in `model` and `effort`",
        "",
        "Each row below is one pair you can copy into the table above.",
        "`start` does not read this block.",
        "",
    ]
    for host in CLI_HOSTS:
        lines.append(f"### {host}")
        lines.append("")
        offerings = catalogs.get(host) or []
        rows = fillable_rows(host, offerings)
        if not rows:
            lines.append("Nothing to copy tonight.")
            lines.append("")
            continue
        if host == "cursor":
            lines.append(
                "Copy one whole row. Cursor effort is set per model in the Cursor app; "
                "a level that has no row is not available until you add it there and scan again."
            )
            lines.append("")
        lines.append("| model | effort |")
        lines.append("| --- | --- |")
        for model, effort in rows:
            lines.append(f"| {model} | {effort} |")
        lines.append("")
    lines.append(OFFERINGS_END)
    lines.append("")
    return "\n".join(lines)


def refresh_live_offerings() -> Path:
    """Write or replace the scanned catalog under the live table. Rows stay."""
    dest = live_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file():
        body = strip_offerings(dest.read_text(encoding="utf-8"))
    else:
        body = default_live_markdown()
    dest.write_text(body.rstrip() + "\n\n" + offerings_markdown(), encoding="utf-8")
    return dest


def fetch_offerings(host: str) -> list[dict]:
    catalog = os.environ.get("MMW_HOST_CATALOG")
    if catalog:
        data = json.loads(Path(catalog).read_text(encoding="utf-8"))
        rows = data.get(host) or []
        return list(rows)
    mode = os.environ.get("MMW_CATALOG_MODE", DEFAULT_CATALOG_MODE)
    if mode == "paseo":
        return _paseo_models(host)
    # One catalog source per host, shared with the block written under the live
    # table: what `offerings_markdown` lists is exactly what `resolve_row` can
    # resolve. Asking two different sources is how a name the block told you to
    # write ends up matching nothing.
    return fetch_cli_offerings(host)


def resolve_row(host: str, model: str, effort: str) -> tuple[str, str, str]:
    """Everyday cells → (host, resolved model id, effort to pass on)."""
    hosts = load_hosts()["hosts"]
    if host not in hosts:
        raise ValueError(f"unknown host {host}")
    spec = hosts[host]
    offerings = fetch_offerings(host)
    mode = os.environ.get("MMW_CATALOG_MODE", DEFAULT_CATALOG_MODE)
    # Cursor on Herdr burns effort into the model id; on Paseo the same host
    # lists `grok-4.6` and thinking is on/off, so do not require a `-high` suffix.
    effort_in_model = bool(spec.get("effort_in_model")) and mode != "paseo"
    offering = match_offering(
        model, offerings,
        effort=effort,
        effort_in_model=effort_in_model,
    )
    resolved = str(offering.get("id") or "")
    allowed = spec.get("efforts")
    thinking_ids = offering.get("thinkingOptionIds")
    if allowed and effort not in ("—", "-", "") and spec.get("thinking") != "boolean":
        names = [str(x) for x in (thinking_ids or allowed)]
        if names and effort not in names and spec.get("paseo", {}).get("thinking") != "boolean":
            if not spec.get("effort_in_model"):
                if effort not in [str(x) for x in allowed]:
                    raise ValueError(
                        f"effort {effort!r} is not one of {', '.join(str(x) for x in allowed)}")
    return host, resolved, effort


def bypass_argv(host: str, model: str, effort: str, name: str) -> list[str]:
    """The host CLI's own launch flags, model and effort filled in.

    Read from the `herdr` block of a host in hosts.json. That block is the host's
    command-line argv and nothing Herdr-specific: every runner that starts a host by
    running its CLI in a terminal — Herdr after `agent start … --`, Orca inside
    `terminal create --command` — runs these same flags, so an edit to the block is an
    edit to how that host starts on all of them. The runner adapters build their launch
    line from here (`models.py bypass-argv` and `models.py launch-line`); none keeps a
    copy. An empty effort (`—`) drops the effort flag rather than passing `—`.
    """
    spec = load_hosts()["hosts"].get(host)
    if not spec or "herdr" not in spec:
        raise ValueError(f"no bypass argv for host {host}")
    template = list(spec["herdr"]["argv"])
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
    """Tonight's runner: MMW_RUNNER, then the live table's runner row, then the
    innermost runner this process runs in, then the default."""
    env = os.environ if environ is None else environ
    return pick_runner(
        env=env.get("MMW_RUNNER"),
        live=parse_live_runner(),
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


def launch_line(host: str, model: str, effort: str, name: str) -> list[str]:
    """The whole command that starts a host: its binary, then `bypass_argv`."""
    return [HOST_BINARIES.get(host), *bypass_argv(host, model, effort, name)]


USAGE = ("usage: models.py offerings\n"
         "       models.py runner\n"
         "       models.py paseo-args <host> <model> <effort>\n"
         "       models.py bypass-argv <host> <model> <effort> <name>\n"
         "       models.py launch-line <host> <model> <effort> <name>\n")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["offerings"]:
        print(refresh_live_offerings())
        return 0
    if args == ["runner"]:
        print(runner_name())
        return 0
    if len(args) == 4 and args[0] == "paseo-args":
        try:
            print("\n".join(paseo_run_args(*args[1:])))
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            sys.stderr.write(f"models.py: {exc}\n")
            return 2
        return 0
    if len(args) == 5 and args[0] in ("bypass-argv", "launch-line"):
        verb, host, model, effort, name = args
        try:
            if verb == "bypass-argv":
                print("\n".join(bypass_argv(host, model, effort, name)))
            else:
                print(shlex.join(launch_line(host, model, effort, name)))
        except (ValueError, OSError, json.JSONDecodeError) as exc:
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
