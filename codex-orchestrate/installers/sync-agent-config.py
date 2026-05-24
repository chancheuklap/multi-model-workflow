#!/usr/bin/env python3
"""Register or remove codex-orchestrate managed sub-agent roles in config.toml."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path


BEGIN = "# BEGIN codex-orchestrate managed agents"
END = "# END codex-orchestrate managed agents"


def toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def toml_array(values: list[str]) -> str:
    return "[" + ", ".join(toml_string(v) for v in values) + "]"


def read_config(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def strip_block(text: str) -> str:
    pattern = re.compile(rf"\n?{re.escape(BEGIN)}.*?{re.escape(END)}\n?", re.DOTALL)
    return pattern.sub("\n", text).rstrip() + "\n"


def load_agents(source_agents_dir: Path, target_agents_dir: Path) -> list[tuple[str, dict[str, object], Path]]:
    agents: list[tuple[str, dict[str, object], Path]] = []
    for source_file in sorted(source_agents_dir.glob("*.toml")):
        with source_file.open("rb") as handle:
            data = tomllib.load(handle)
        name = str(data.get("name") or source_file.stem)
        agents.append((name, data, target_agents_dir / source_file.name))
    return agents


def build_block(source_agents_dir: Path, target_agents_dir: Path) -> str:
    lines = [
        BEGIN,
        "# Managed by codex-orchestrate/installers/sync-agent-config.py.",
    ]
    for name, data, target_file in load_agents(source_agents_dir, target_agents_dir):
        lines.append("")
        lines.append(f"[agents.{name}]")
        lines.append(f"config_file = {toml_string(str(target_file))}")
        description = data.get("description")
        if isinstance(description, str) and description.strip():
            lines.append(f"description = {toml_string(description.strip())}")
        nicknames = data.get("nickname_candidates")
        if isinstance(nicknames, list) and all(isinstance(item, str) for item in nicknames):
            lines.append(f"nickname_candidates = {toml_array(nicknames)}")
    lines.append("")
    lines.append(END)
    return "\n".join(lines) + "\n"


def ensure_no_unmanaged_duplicates(config_text: str, agent_names: list[str], config_file: Path) -> None:
    try:
        parsed = tomllib.loads(config_text or "")
    except tomllib.TOMLDecodeError as exc:
        raise SystemExit(f"sync-agent-config: invalid TOML before update: {config_file}: {exc}") from exc
    existing = parsed.get("agents", {})
    if not isinstance(existing, dict):
        return
    duplicates = [name for name in agent_names if name in existing]
    if duplicates:
        joined = ", ".join(sorted(duplicates))
        raise SystemExit(f"sync-agent-config: refusing to overwrite unmanaged agent config: {joined}")


def write_checked(config_file: Path, text: str, dry_run: bool) -> None:
    try:
        tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise SystemExit(f"sync-agent-config: generated invalid TOML: {exc}") from exc
    if dry_run:
        print(text)
        return
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(text, encoding="utf-8")


def install(args: argparse.Namespace) -> None:
    config_file = Path(args.config_file).expanduser()
    source_agents_dir = Path(args.source_agents_dir).expanduser()
    target_agents_dir = Path(args.target_agents_dir).expanduser()
    agents = load_agents(source_agents_dir, target_agents_dir)
    base_text = strip_block(read_config(config_file))
    ensure_no_unmanaged_duplicates(base_text, [name for name, _, _ in agents], config_file)
    block = build_block(source_agents_dir, target_agents_dir)
    next_text = base_text.rstrip() + "\n\n" + block
    write_checked(config_file, next_text, args.dry_run)


def remove(args: argparse.Namespace) -> None:
    config_file = Path(args.config_file).expanduser()
    next_text = strip_block(read_config(config_file))
    write_checked(config_file, next_text, args.dry_run)


def verify(args: argparse.Namespace) -> None:
    config_file = Path(args.config_file).expanduser()
    source_agents_dir = Path(args.source_agents_dir).expanduser()
    target_agents_dir = Path(args.target_agents_dir).expanduser()
    try:
        with config_file.open("rb") as handle:
            config = tomllib.load(handle)
    except FileNotFoundError as exc:
        raise SystemExit(f"sync-agent-config: config file missing: {config_file}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise SystemExit(f"sync-agent-config: invalid TOML: {config_file}: {exc}") from exc

    configured_agents = config.get("agents", {})
    if not isinstance(configured_agents, dict):
        raise SystemExit("sync-agent-config: [agents] table missing or invalid")

    for name, data, target_file in load_agents(source_agents_dir, target_agents_dir):
        entry = configured_agents.get(name)
        if not isinstance(entry, dict):
            raise SystemExit(f"sync-agent-config: missing [agents.{name}] config entry")
        configured_file = entry.get("config_file")
        if configured_file != str(target_file):
            raise SystemExit(
                f"sync-agent-config: [agents.{name}].config_file drift: {configured_file!r} != {str(target_file)!r}"
            )
        if "description" not in entry:
            raise SystemExit(f"sync-agent-config: [agents.{name}].description missing")
        if data.get("nickname_candidates") and "nickname_candidates" not in entry:
            raise SystemExit(f"sync-agent-config: [agents.{name}].nickname_candidates missing")
    print("sync-agent-config: agent config verified")


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("install", "remove", "verify"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--config-file", required=True)
        sub.add_argument("--source-agents-dir")
        sub.add_argument("--target-agents-dir")
        sub.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    if args.command in {"install", "verify"}:
        if not args.source_agents_dir or not args.target_agents_dir:
            parser.error(f"{args.command} requires --source-agents-dir and --target-agents-dir")
    if args.command == "install":
        install(args)
    elif args.command == "remove":
        remove(args)
    elif args.command == "verify":
        verify(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
