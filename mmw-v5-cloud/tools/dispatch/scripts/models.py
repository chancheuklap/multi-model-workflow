#!/usr/bin/env python3
"""Project model choices for native cloud agents; no local CLI catalog or runner."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

ROLES = ('junior-worker', 'senior-worker', 'advisor', 'researcher', 'candidate', 'review-axis')


def config_path() -> Path:
    root = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True, check=True).stdout.strip()
    return Path(root) / '.cursor' / 'models.json'


def validate(value: dict) -> dict:
    if not isinstance(value, dict) or type(value.get('max_workers')) is not int or value['max_workers'] < 1:
        raise ValueError('max_workers must be a positive integer')
    rows = value.get('rows')
    if not isinstance(rows, dict):
        raise ValueError('rows must be an object of native role settings')
    for role in ROLES:
        row = rows.get(role)
        if not isinstance(row, dict) or any(not isinstance(row.get(k), str) or not row[k].strip() for k in ('host', 'model', 'effort')):
            raise ValueError(f'{role} needs host, model and effort (or inherit)')
    if 'runner' in value or 'subagents' in value:
        raise ValueError('cloud models use native rows, not local runner/subagent configuration')
    return value


def read_config(at: str | None = None) -> dict:
    if at is None:
        text = config_path().read_text(encoding="utf-8")
    else:
        text = subprocess.run(["git", "show", f"{at}:.cursor/models.json"], capture_output=True, text=True, check=True).stdout
    return validate(json.loads(text))


def row(role: str, host: str, at: str) -> dict:
    chosen = dict(read_config(at)['rows'][role])
    if chosen['host'] not in ('inherit', host):
        raise ValueError(f'{role} requests {chosen["host"]}; this native host is {host}')
    return {key: val for key, val in chosen.items() if val != 'inherit' and key != 'host'}


def write_config(value: dict) -> None:
    path = config_path()
    text = json.dumps(validate(value), ensure_ascii=False, indent=2) + '\n'
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, prefix='.models-', delete=False) as output:
        temporary = Path(output.name)
        output.write(text)
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    show = sub.add_parser('show'); show.add_argument('--at', required=True, help='the existing run starting commit')
    get = sub.add_parser('row'); get.add_argument('role', choices=ROLES); get.add_argument('host'); get.add_argument('--at', required=True, help='the existing run starting commit that fixes the model configuration')
    args = parser.parse_args()
    try:
        print(json.dumps(read_config(args.at) if args.command == 'show' else row(args.role, args.host, args.at), ensure_ascii=False))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        parser.exit(2, f'models: {exc}\n')

if __name__ == '__main__':
    main()
