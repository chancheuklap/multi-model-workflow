#!/usr/bin/env python3
"""Project model choices for native cloud agents; no local CLI catalog or runner."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

ROLES = ('junior-worker', 'senior-worker', 'advisor', 'researcher', 'candidate', 'review-axis')
HOSTS = ('codex', 'cursor')


def config_path() -> Path:
    root = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True, check=True).stdout.strip()
    return Path(root) / '.cursor' / 'models.json'


def validate(value: dict) -> dict:
    if not isinstance(value, dict) or type(value.get('max_workers')) is not int or value['max_workers'] < 1:
        raise ValueError('max_workers must be a positive integer')
    rows = value.get('rows')
    if not isinstance(rows, dict):
        raise ValueError('rows must be an object of native role settings')
    for host in HOSTS:
        roles = rows.get(host)
        if not isinstance(roles, dict):
            raise ValueError(f'rows needs a {host} group with settings for each role')
        for role in ROLES:
            row = roles.get(role)
            if not isinstance(row, dict) or any(not isinstance(row.get(k), str) or not row[k].strip() for k in ('model', 'effort')):
                raise ValueError(f'{host}/{role} needs model and effort (or inherit)')
            if host == 'cursor':
                if 'context' in row and (not isinstance(row['context'], str) or not row['context'].strip()):
                    raise ValueError(f'{host}/{role} context must be a non-empty string, such as 256k')
                if 'fast' in row and type(row['fast']) is not bool:
                    raise ValueError(f'{host}/{role} fast must be true or false')
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
    if host not in HOSTS:
        raise ValueError(f'unsupported native host: {host}')
    chosen = {key: val for key, val in read_config(at)['rows'][host][role].items() if val != 'inherit'}
    if host == 'cursor' and chosen.get('model'):
        options = [f'{key}={str(chosen[key]).lower()}' for key in ('effort', 'context', 'fast') if key in chosen]
        model = chosen['model'] + ('[' + ','.join(options) + ']' if options else '')
        return {'model': model}
    return chosen


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
    get = sub.add_parser('row'); get.add_argument('role', choices=ROLES); get.add_argument('host', choices=HOSTS); get.add_argument('--at', required=True, help='the existing run starting commit that fixes the model configuration')
    args = parser.parse_args()
    try:
        print(json.dumps(read_config(args.at) if args.command == 'show' else row(args.role, args.host, args.at), ensure_ascii=False))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        parser.exit(2, f'models: {exc}\n')

if __name__ == '__main__':
    main()
