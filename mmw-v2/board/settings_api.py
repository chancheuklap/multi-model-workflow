#!/usr/bin/env python3
"""Read, validate, scan, and replace the machine's saved agent configuration."""

from __future__ import annotations

import importlib.util
import json
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

MODELS_PY = Path(__file__).resolve().parents[1] / "skills" / "dispatch" / "scripts" / "models.py"
_spec = importlib.util.spec_from_file_location("mmw_board_models", MODELS_PY)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load {MODELS_PY}")
models = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = models
_spec.loader.exec_module(models)

_state_lock = threading.Lock()
_scan: dict | None = None


def _json(status: int, value: dict) -> tuple[int, dict[str, str], bytes]:
    body = (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    return status, {"Content-Type": "application/json; charset=utf-8"}, body


def _body(request) -> dict:
    raw_length = request.headers.get("Content-Length") or "0"
    try:
        length = int(raw_length)
        data = json.loads(request.rfile.read(length) or b"{}")
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"request body is not JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("request body is not a JSON object")
    return data


def _source_for_runner(runner: str) -> str:
    return "paseo" if runner == "paseo" else "cli"


def _scan_for(runner_or_source: str) -> dict:
    runner = "paseo" if runner_or_source == "paseo" else "auto"
    return models.scan_host_catalogs(runner)


def _current_scan(runner: str) -> dict:
    global _scan
    with _state_lock:
        if _scan is None:
            _scan = _scan_for(_source_for_runner(runner))
        return _scan


def _replace_scan(source: str) -> dict:
    global _scan
    if source not in ("cli", "paseo"):
        raise ValueError(f"source must be cli or paseo, got {source!r}")
    fresh = _scan_for(source)
    with _state_lock:
        _scan = fresh
    return fresh


def initialize() -> None:
    """Scan once while the board process is starting, before it prints its origin."""
    try:
        config = models.read_local_config()
    except models.ConfigMissing:
        return
    _replace_scan(_source_for_runner(str(config.get("runner"))))


def _options() -> dict:
    catalog = models.load_hosts()
    hosts = []
    for name, spec in catalog["hosts"].items():
        hosts.append({"name": name, "binary": spec.get("binary", name),
                      "cli": "cli" in spec, "paseo": "paseo" in spec})
    runners = sorted(path.stem for path in models.RUNNERS_DIR.glob("*.sh")
                     if path.stem in {"herdr", "orca", "paseo"})
    runners.append("auto")
    return {"hosts": hosts, "runners": runners,
            "sources": {"hosts": "dispatch/hosts.json",
                        "runners": "dispatch/scripts/runners/*.sh"}}


def _get() -> tuple[int, dict[str, str], bytes]:
    config = models.read_local_config()
    return _json(200, {**config, **_options(), "scan": _current_scan(config["runner"])})


def _put(request) -> tuple[int, dict[str, str], bytes]:
    proposed = _body(request)
    expected = proposed.get("version")
    if not isinstance(expected, int):
        return _json(422, {"errors": [{"cell": "version", "reason": "version must be an integer"}]})
    try:
        written = models.write_local_config(proposed, expected,
                                            _current_scan(str(proposed.get("runner"))))
    except models.VersionConflict as exc:
        return _json(409, {"error": str(exc), "modified_at": exc.modified_at})
    except models.InvalidConfig as exc:
        return _json(422, {"errors": exc.errors})
    except models.ConfigLockHeld as exc:
        return _json(423, {"error": str(exc), "holder": exc.holder})
    return _json(200, {"version": written["version"],
                       "saved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})


def _post_scan(request) -> tuple[int, dict[str, str], bytes]:
    data = _body(request)
    source = data.get("source")
    if source is None and "runner" in data:
        source = _source_for_runner(str(data["runner"]))
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
    except (ValueError, json.JSONDecodeError) as exc:
        return _json(400, {"error": str(exc)})


if Path(sys.argv[0]).resolve() == Path(__file__).resolve().with_name("server.py"):
    initialize()
