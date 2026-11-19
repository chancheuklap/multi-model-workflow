#!/usr/bin/env python3
"""Keep the dispatch resource inventory and binary text transports in sync.

Authoring only. The plugin runtime uses the prepared files without a build step.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def generated(edition: Path) -> dict[Path, bytes]:
    skill = edition / 'skills/dispatch'
    files = {}
    outputs = {}
    for file in sorted((skill / 'runtime').rglob('*')):
        if not file.is_file() or '__pycache__' in file.parts or file.suffix in ('.pyc', '.pyo'):
            continue
        if file.is_symlink():
            raise ValueError(f'runtime resource is a symlink: {file}')
        path = file.relative_to(skill / 'runtime').as_posix()
        data = file.read_bytes()
        try:
            data.decode('utf-8')
            encoding, resource = 'utf-8', f'runtime/{path}'
        except UnicodeDecodeError:
            encoding, resource = 'base64', f'resources/{path}.base64.txt'
            outputs[skill / resource] = base64.b64encode(data)
        files[path] = {'resource': resource, 'encoding': encoding,
                       'sha256': hashlib.sha256(data).hexdigest(),
                       'mode': 0o755 if file.stat().st_mode & 0o111 else 0o644}
    manifest = {'format': 1, 'version': json.loads((edition / 'plugin.json').read_text())['version'], 'files': files}
    outputs[skill / 'runtime-manifest.json'] = (json.dumps(manifest, indent=2, ensure_ascii=False) + '\n').encode()
    return outputs


def sync(edition: Path, check: bool = False) -> None:
    outputs = generated(edition)
    resources = edition / 'skills/dispatch/resources'
    extra = {p for p in resources.rglob('*') if p.is_file()} - outputs.keys()
    stale = extra | {p for p, data in outputs.items() if not p.exists() or p.read_bytes() != data}
    if check:
        if stale:
            raise ValueError('dispatch resources need sync: ' + ', '.join(str(p.relative_to(edition)) for p in sorted(stale)))
        return
    for p in extra:
        p.unlink()
    for p, data in outputs.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        sync(ROOT / 'mmw-v5-cloud', args.check)
    except (OSError, ValueError) as exc:
        parser.exit(2, f'dispatch resources: {exc}\n')


if __name__ == '__main__':
    main()
