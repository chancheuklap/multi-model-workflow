"""Read, validate, scan, and replace the machine's saved agent configuration."""

from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parents[1] / "skills" / "dispatch" / "scripts"
if str(MODELS_DIR) not in sys.path:
    sys.path.insert(0, str(MODELS_DIR))
import models  # noqa: E402

_state_lock = threading.Condition()
_scan_active = False
_scan: dict | None = None


def _json(status: int, value: dict) -> tuple[int, dict[str, str], bytes]:
    body = (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    return status, {"Content-Type": "application/json; charset=utf-8"}, body


def _body(request) -> dict:
    raw_length = request.headers.get("Content-Length") or "0"
    try:
        length = int(raw_length)
        data = json.loads(request.rfile.read(length) or b"{}")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"request body is not JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("request body is not a JSON object")
    return data


def _run_scan(source: str) -> dict:
    global _scan, _scan_active
    try:
        fresh = models.scan_host_catalogs(source)
        with _state_lock:
            _scan = fresh
        return fresh
    finally:
        with _state_lock:
            if _scan is not None:
                _scan = {**_scan, "scanning": False}
            _scan_active = False
            _state_lock.notify_all()


def _begin_scan(runner: str) -> None:
    global _scan, _scan_active
    source = models.catalog_source(runner)
    if not os.environ.get("MMW_HOST_CATALOG") or _scan is None or _scan.get("source") != source:
        _scan = models.cached_host_catalogs(runner)
    _scan = {**_scan, "scanning": True}
    _scan_active = True


def _cached_scan(runner: str) -> dict:
    global _scan
    source = models.catalog_source(runner)
    with _state_lock:
        if not _scan_active:
            _begin_scan(runner)
            threading.Thread(target=_run_scan, args=(runner,), daemon=True).start()
        return dict(_scan)


def _ready_scan(runner: str) -> dict:
    source = models.catalog_source(runner)
    with _state_lock:
        while _scan_active:
            _state_lock.wait()
        if _scan is not None and _scan["source"] == source:
            return dict(_scan)
        return models.cached_host_catalogs(runner)


def _replace_scan(source: str) -> dict:
    if source not in (*models.config_runners(), "cli"):
        raise ValueError(f"source must name an installed runner or cli, got {source!r}")
    with _state_lock:
        while _scan_active:
            _state_lock.wait()
        _begin_scan(source)
    return _run_scan(source)


def initialize() -> None:
    try:
        config = models.read_local_config()
    except models.ConfigMissing:
        return
    source = str(config.get("runner"))
    if os.environ.get("MMW_HOST_CATALOG"):
        _replace_scan(source)
    else:
        _cached_scan(source)


def _options() -> dict:
    catalog = models.load_hosts()
    hosts = []
    for name, spec in catalog["hosts"].items():
        hosts.append({"name": name, "binary": models.HOST_BINARIES.get(name),
                      "cli": "cli" in spec, "paseo": "paseo" in spec,
                      "launch": [key for key in spec if isinstance(spec[key], dict)]})
    return {"hosts": hosts, "runners": list(models.config_runners()),
            "runner_options": {name: models.runner_description(name)
                               for name in models.config_runners()},
            "sources": {
                "hosts": str(models.HOSTS_JSON.relative_to(models.SKILL_DIR)),
                "runners": str(models.RUNNERS_DIR.relative_to(models.SKILL_DIR) / "*.sh")}}


def _get() -> tuple[int, dict[str, str], bytes]:
    config = models.read_local_config()
    runner = config["runner"]
    scan = _cached_scan(runner)
    if scan["source"] != models.catalog_source(runner):
        scan = models.cached_host_catalogs(runner)
    if not scan["scanned_at"]:
        scan = _ready_scan(runner)
        if not scan["scanned_at"]:
            scan = _replace_scan(models.catalog_source(runner))
    subagents = _subagents(config)
    return _json(200, {**config, **_options(), "scan": {**scan, "scanning": False},
                       **_subagent_answer(config["rows"], subagents, scan["hosts"])})


def _subagents(config: dict) -> dict:
    saved = config.get("subagents") if isinstance(config.get("subagents"), dict) else {}
    return {row: {host: {"model": "inherit", "effort": "inherit", **(saved.get(row, {}).get(host) or {})}
                  for host in models.CLI_HOSTS}
            for row in models.subagent_rows()}


def _subagent_answer(rows: dict, subagents: dict, hosts: dict) -> dict:
    """The subagent cells with their choices, one name per model id, and each saved model the catalog lacks."""
    choices = models.subagent_choices()
    codex_ids = [item["model"] for item in choices["codex"]["models"]]
    stale = []
    for agent, row in rows.items():
        scan = hosts.get(row.get("host"), {})
        offered = [item["model"] for item in scan.get("offered", [])]
        if scan.get("state") == "ok" and row.get("model") not in offered:
            stale.append({"cell": f"rows.{agent}.model", "host": row["host"],
                          "stored": row.get("model"), "offered": offered})
    stored = []
    for name, cells in subagents.items():
        model = cells["codex"]["model"]
        if model != "inherit":
            stored.append(model)
            if codex_ids and model not in codex_ids:
                stale.append({"cell": f"subagents.{name}.codex.model", "host": "codex",
                              "stored": model, "offered": codex_ids})
    labels = models.model_labels({"claude": choices["claude"]["models"],
                                  "codex": list(dict.fromkeys(codex_ids + stored))})
    return {"subagents": subagents, "stale": stale,
            "subagent_options": {**choices, "labels": labels}}


def _put(request) -> tuple[int, dict[str, str], bytes]:
    proposed = _body(request)
    expected = proposed.get("version")
    if not isinstance(expected, int):
        return _json(422, {"errors": [{"cell": "version", "reason": "version must be an integer"}]})
    try:
        written = models.write_local_config(proposed, expected,
                                            _ready_scan(str(proposed.get("runner"))))
    except models.VersionConflict as exc:
        return _json(409, {"error": str(exc), "modified_at": exc.modified_at})
    except models.InvalidConfig as exc:
        return _json(422, {"errors": exc.errors})
    except models.ConfigLockHeld as exc:
        return _json(423, {"error": str(exc), "holder": exc.holder})
    return _json(200, {"version": written["version"],
                       "saved_at": models.statedir.now_iso()})


def _post_scan(request) -> tuple[int, dict[str, str], bytes]:
    data = _body(request)
    source = data.get("source")
    if source is None and "runner" in data:
        source = models.catalog_source(str(data["runner"]))
    try:
        return _json(200, _replace_scan(str(source)))
    except ValueError as exc:
        return _json(422, {"errors": [{"cell": "source", "reason": str(exc)}]})


def handle(request) -> tuple[int, dict[str, str], bytes]:
    """Handle exactly the three settings operations declared by the screen contract."""
    path = request.path.split("?", 1)[0]
    try:
        if request.command == "GET" and path == "/api/settings":
            return _get()
        if request.command == "PUT" and path == "/api/settings":
            return _put(request)
        if request.command == "POST" and path == "/api/settings/scan":
            return _post_scan(request)
        return _json(404, {"error": "unknown settings operation"})
    except models.ConfigMissing as exc:
        return _json(503, {"error": str(exc)})
    except ValueError as exc:
        return _json(400, {"error": str(exc)})

