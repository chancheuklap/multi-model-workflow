#!/usr/bin/env python3
"""Restore one dispatch runtime from same-skill text resources."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tempfile


def identity(manifest: dict) -> str:
    return hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def entries(manifest: dict) -> dict:
    if not isinstance(manifest, dict) or manifest.get('format') != 1 or not isinstance(manifest.get('version'), str):
        raise ValueError('expected a versioned dispatch runtime manifest')
    files = manifest.get('files')
    if not isinstance(files, dict) or not files:
        raise ValueError('runtime manifest has no files')
    for path, entry in files.items():
        name = PurePosixPath(path)
        if not name.parts or name.is_absolute() or str(name) != path or '..' in name.parts or '\\' in path:
            raise ValueError(f'unsafe runtime path: {path}')
        if not isinstance(entry, dict):
            raise ValueError(f'invalid resource entry: {path}')
        resource = entry.get('resource', '')
        if resource != f'runtime/{path}' and resource != f'resources/{path}.base64.txt':
            raise ValueError(f'expected a same-skill resource for {path}')
        if entry.get('encoding') not in ('utf-8', 'base64') or entry.get('mode') not in (0o644, 0o755):
            raise ValueError(f'invalid resource encoding or mode: {path}')
        digest = entry.get('sha256', '')
        if len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError(f'invalid sha256: {path}')
    return files


def verify(root: Path, files: dict) -> None:
    for path, entry in files.items():
        file = root / path
        if file.is_symlink() or not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError(f'runtime sha256 mismatch: {path}')


def materialize(manifest: dict, contents: dict, cache: Path) -> Path:
    files = entries(manifest)
    if not isinstance(contents, dict):
        raise ValueError('resource contents must be a JSON object')
    target = cache / identity(manifest)
    if target.exists():
        verify(target, files)
        return target
    decoded = {}
    for path, entry in files.items():
        text = contents.get(entry['resource'])
        if not isinstance(text, str):
            raise ValueError(f'missing complete resource: {entry["resource"]}')
        data = base64.b64decode(text, validate=True) if entry['encoding'] == 'base64' else text.encode('utf-8')
        if hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise ValueError(f'resource sha256 mismatch: {path}')
        decoded[path] = data
    cache.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.runtime-', dir=cache))
    try:
        for path, data in decoded.items():
            file = temporary / path
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(data)
            file.chmod(files[path]['mode'])
        try:
            temporary.rename(target)
        except OSError:
            if not target.is_dir():
                raise
            verify(target, files)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--contents', type=Path, help='JSON object: resource path to complete text')
    parser.add_argument('--cache', type=Path, default=Path.home() / '.cache/mmw-v5/runtimes')
    parser.add_argument('--local', action='store_true', help='use the adjacent installed runtime')
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
        if args.local:
            runtime = args.manifest.resolve().parent / 'runtime'
            verify(runtime, entries(manifest))
        else:
            contents = json.loads(args.contents.read_text(encoding='utf-8')) if args.contents else {}
            runtime = materialize(manifest, contents, args.cache)
        print(json.dumps({'version': manifest['version'], 'identity': identity(manifest),
                          'runtime': str(runtime),
                          'dispatch': str(runtime / 'tools/dispatch/scripts/dispatch.sh'),
                          'labels': str(runtime / 'tools/setup-mmw/scripts/labels.py')}))
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(2, f'materialize: {exc}\n')


if __name__ == '__main__':
    main()
