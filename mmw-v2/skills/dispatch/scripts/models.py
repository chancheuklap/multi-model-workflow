"""读本机活表，问今晚的目录，再按 hosts.json 展开成启动参数。

活表是 ~/.mmw/models.md（MMW_LIVE_MODELS / MMW_V2_HOME 可改）。hosts.json 跟着
技能走，记下每个 host 在 Herdr 和 Paseo 上怎么起，以及第一次 install 拷进活表的
默认行。一个库，没有命令行入口。dispatch.sh 的 start 与 install.sh 共用。
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import NamedTuple

SKILL_DIR = Path(__file__).resolve().parent.parent
HOSTS_JSON = SKILL_DIR / "hosts.json"
ALLOWED_AGENTS = (
    "junior-worker", "senior-worker", "reviewer", "verifier", "advisor")
# Herdr checkout asks the host CLI; Paseo checkout asks paseo. Tests set
# MMW_CATALOG_MODE or MMW_HOST_CATALOG.
DEFAULT_CATALOG_MODE = "herdr"


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
        "This machine's table. `start` reads it. Edit it to change host, model or effort;",
        "do not commit it. First `install.sh` copies the defaults; later ones leave it.",
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


def parse_live_rows(path: Path | None = None) -> list[tuple[str, str, str, str]]:
    """活表每一行：(agent, host, model, effort)。"""
    source = path or _models_file()
    if not source.is_file():
        raise ValueError(f"缺活表：{source}；跑 install.sh")
    rows: list[tuple[str, str, str, str]] = []
    for line in source.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip().strip("`").strip() for c in line.strip().strip("|").split("|")]
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
    primary: bool


def session_rows(path: Path | None = None) -> list[SessionRow]:
    """第一条是 start 用的 host，后一条是 fallback。同一 agent 不能两个同一 host。"""
    source = path or _models_file()
    primary_host: dict[str, str] = {}
    have_fallback: set[str] = set()
    out: list[SessionRow] = []
    for agent, host, model, effort in parse_live_rows(source):
        if agent not in primary_host:
            primary_host[agent] = host
            out.append(SessionRow(agent, host, model, effort, True))
            continue
        if host == primary_host[agent]:
            raise ValueError(f"{source}: {agent} has two rows on {host}")
        if agent in have_fallback:
            raise ValueError(f"{source}: {agent} has more than one fallback row")
        have_fallback.add(agent)
        out.append(SessionRow(agent, host, model, effort, False))
    return out


def bypass_rows(path: Path | None = None) -> list[SessionRow]:
    """旧名：全部派出的行都是会话。"""
    return session_rows(path)


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
        if needle == oid or needle == name or needle in oid or needle in name:
            hits.append(offering)
    # exact id or name wins over substring
    exact = [
        o for o in hits
        if needle in (_norm(str(o.get("id") or "")), _norm(str(o.get("name") or "")))
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


def _run(argv: list[str]) -> str:
    try:
        proc = subprocess.run(
            argv, check=False, capture_output=True, text=True, timeout=20)
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
            out.append({"id": ident.strip(), "name": name.strip()})
        elif re.match(r"^[\w.-]+$", line):
            out.append({"id": line, "name": line})
    return out


def _parse_grok_models(text: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        m = re.search(r"^\s*[*-]\s+(\S+)", line)
        if m:
            ident = m.group(1).strip("()")
            out.append({"id": ident, "name": ident})
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


def fetch_offerings(host: str) -> list[dict]:
    catalog = os.environ.get("MMW_HOST_CATALOG")
    if catalog:
        data = json.loads(Path(catalog).read_text(encoding="utf-8"))
        rows = data.get(host) or []
        return list(rows)
    mode = os.environ.get("MMW_CATALOG_MODE", DEFAULT_CATALOG_MODE)
    if mode == "paseo":
        return _paseo_models(host)
    binaries = {
        "cursor": ["cursor-agent", "models"],
        "grok": ["grok", "models"],
    }
    if host == "cursor":
        return _parse_cursor_models(_run(binaries["cursor"]))
    if host == "grok":
        return _parse_grok_models(_run(binaries["grok"]))
    if host in ("claude", "codex", "pi"):
        paseo = _paseo_models(host)
        if paseo:
            return paseo
    return []


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
    """Resolved model expanded to the argv after `herdr agent start … --`."""
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


def resolve_session(agent: str, nth: int = 1) -> SessionRow:
    rows = [r for r in session_rows() if r.agent == agent]
    if nth < 1 or nth > len(rows):
        raise ValueError(f"no row {nth} for {agent}")
    row = rows[nth - 1]
    host, model, effort = resolve_row(row.host, row.model, row.effort)
    return SessionRow(row.agent, host, model, effort, row.primary)


def row_tsv(agent: str, nth: int = 1) -> str:
    """host<TAB>resolved-model<TAB>effort for dispatch.sh."""
    row = resolve_session(agent, nth)
    return f"{row.host}\t{row.model}\t{row.effort}"


def worker_role_names() -> list[str]:
    seen = []
    for row in session_rows():
        if row.agent.endswith("-worker") and row.agent not in seen:
            seen.append(row.agent)
    return seen
