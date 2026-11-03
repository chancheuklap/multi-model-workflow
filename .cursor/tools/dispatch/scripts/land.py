#!/usr/bin/env python3
"""Validate one PR's actual NIGHT merge candidate with scripts/check, then merge that exact PR head."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
from status import GitHub, command


def land(number: int, into: str, head: str, *, api=None) -> dict:
    api = api or GitHub()
    root = Path(command('git', 'rev-parse', '--show-toplevel'))
    pr = api.get(f'pulls/{number}')
    if pr['base']['ref'] != into or pr['base']['repo']['full_name'].lower() != api.repo.lower():
        raise ValueError('PR does not target this repository and assigned NIGHT branch')
    if pr['head']['sha'] != head or pr.get('merged_at') or pr['state'] != 'open' or pr.get('draft'):
        raise ValueError('PR is not the open, ready candidate supplied by the Worker')
    command('git', 'check-ref-format', '--branch', into)
    command('git', 'fetch', 'origin', f'+refs/heads/{into}:refs/remotes/origin/{into}')
    command('git', 'fetch', 'origin', f'refs/pull/{number}/head')
    tip = command('git', 'rev-parse', f'origin/{into}')
    if tip != pr['base']['sha'] or command('git', 'rev-parse', 'FETCH_HEAD') != head:
        raise ValueError('PR/base moved while reading; inspect current commits before retrying')
    with tempfile.TemporaryDirectory(prefix='mmw-cloud-land-') as temporary:
        candidate = Path(temporary) / 'candidate'
        command('git', 'worktree', 'add', '--detach', str(candidate), tip)
        try:
            command('git', 'merge', '--no-ff', '--no-edit', head, cwd=candidate)
            tree = command('git', 'write-tree', cwd=candidate)
            path = candidate / 'scripts' / 'check'
            if not (path.is_file() and os.access(path, os.X_OK)):
                raise RuntimeError('the merge candidate has no executable scripts/check; NIGHT was not updated')
            env = os.environ.copy()
            env['MMW_BASE_REF'] = f'origin/{into}'
            run = subprocess.run([str(path)], cwd=candidate, env=env, text=True)
            if run.returncode:
                raise RuntimeError(f'scripts/check exited {run.returncode}; NIGHT was not updated')
            if subprocess.run(['git', 'diff', '--quiet'], cwd=candidate).returncode:
                raise RuntimeError('verification changed tracked candidate files; NIGHT was not updated')
            if command('git', 'write-tree', cwd=candidate) != tree:
                raise RuntimeError('verification changed the staged candidate; NIGHT was not updated')
            current = api.get(f'pulls/{number}')
            if current['head']['sha'] != head or current['base']['sha'] != tip or current['base']['ref'] != into:
                raise ValueError('PR/base moved during verification; candidate was not merged')
            answer = json.loads(command('gh', 'api', '--method', 'PUT', f'repos/{api.repo}/pulls/{number}/merge',
                                        '-f', f'sha={head}', '-f', 'merge_method=merge'))
            if not answer.get('merged'):
                raise RuntimeError(answer.get('message') or 'GitHub did not merge the PR')
            command('git', 'fetch', 'origin', f'+refs/heads/{into}:refs/remotes/origin/{into}')
            merged = answer['sha']
            command('git', 'merge-base', '--is-ancestor', merged, f'origin/{into}')
            if command('git', 'rev-parse', f'{merged}^{{tree}}') != tree:
                raise RuntimeError(f'PR merged at {merged}, but its tree differs from checked candidate; inspect before releasing dependencies')
            return {'pr': number, 'into': into, 'head': head, 'merged_commit': merged, 'checked_tree': tree}
        finally:
            subprocess.run(['git', 'worktree', 'remove', '--force', str(candidate)], cwd=root, capture_output=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pr', type=int); parser.add_argument('--into', required=True)
    parser.add_argument('--head', required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(land(args.pr, args.into, args.head)))
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        parser.exit(2, f'land: {exc}\n')

if __name__ == '__main__':
    main()
