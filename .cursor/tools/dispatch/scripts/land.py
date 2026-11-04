#!/usr/bin/env python3
"""Validate one ticket head merged into the night branch with scripts/check, then merge that exact commit."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
from status import GitHub, command, current_night


def land(number: int, into: str, head: str, *, api=None) -> dict:
    api = api or GitHub()
    root = Path(command('git', 'rev-parse', '--show-toplevel'))
    pr = api.get(f'pulls/{number}')
    if pr['base']['ref'] != into or pr['base']['repo']['full_name'].lower() != api.repo.lower():
        raise ValueError('PR does not target this repository and the assigned night branch')
    if pr['head']['sha'] != head or pr.get('merged_at') or pr['state'] != 'open' or pr.get('draft'):
        raise ValueError('PR is not open and ready at the ticket head supplied by the Worker')
    command('git', 'check-ref-format', '--branch', into)
    command('git', 'fetch', 'origin', f'+refs/heads/{into}:refs/remotes/origin/{into}')
    command('git', 'fetch', 'origin', f'refs/pull/{number}/head')
    tip = command('git', 'rev-parse', f'origin/{into}')
    if tip != pr['base']['sha'] or command('git', 'rev-parse', 'FETCH_HEAD') != head:
        raise ValueError('PR/base moved while reading; inspect current commits before retrying')
    with tempfile.TemporaryDirectory(prefix='mmw-cloud-land-') as temporary:
        trial = Path(temporary) / 'trial'
        command('git', 'worktree', 'add', '--detach', str(trial), tip)
        try:
            command('git', 'merge', '--no-ff', '--no-edit', head, cwd=trial)
            tree = command('git', 'write-tree', cwd=trial)
            path = trial / 'scripts' / 'check'
            if not (path.is_file() and os.access(path, os.X_OK)):
                raise RuntimeError('the trial merge has no executable scripts/check; the night branch was not updated')
            env = os.environ.copy()
            env['MMW_BASE_REF'] = f'origin/{into}'
            run = subprocess.run([str(path)], cwd=trial, env=env, text=True, capture_output=True)
            if run.returncode:
                output = '\n'.join(part for part in (run.stdout, run.stderr) if part)
                raise RuntimeError(f'scripts/check exited {run.returncode}; the night branch was not updated\n{output}'.rstrip())
            if subprocess.run(['git', 'diff', '--quiet'], cwd=trial).returncode:
                raise RuntimeError('verification changed tracked files in the trial merge; the night branch was not updated')
            if command('git', 'write-tree', cwd=trial) != tree:
                raise RuntimeError('verification changed the staged trial merge; the night branch was not updated')
            current = api.get(f'pulls/{number}')
            if current['head']['sha'] != head or current['base']['sha'] != tip or current['base']['ref'] != into:
                raise ValueError('PR/base moved during verification; ticket head was not merged')
            answer = json.loads(command('gh', 'api', '--method', 'PUT', f'repos/{api.repo}/pulls/{number}/merge',
                                        '-f', f'sha={head}', '-f', 'merge_method=merge'))
            if not answer.get('merged'):
                raise RuntimeError(answer.get('message') or 'GitHub did not merge the PR')
            command('git', 'fetch', 'origin', f'+refs/heads/{into}:refs/remotes/origin/{into}')
            merged = answer['sha']
            command('git', 'merge-base', '--is-ancestor', merged, f'origin/{into}')
            if command('git', 'rev-parse', f'{merged}^{{tree}}') != tree:
                raise RuntimeError(f'PR merged at {merged}, but its tree differs from the checked trial merge; inspect before releasing dependencies')
            return {'pr': number, 'into': into, 'head': head, 'merged_commit': merged, 'checked_tree': tree}
        finally:
            subprocess.run(['git', 'worktree', 'remove', '--force', str(trial)], cwd=root, capture_output=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pr', type=int)
    args = parser.parse_args()
    try:
        api = GitHub()
        into = current_night()['branch']
        head = api.get(f'pulls/{args.pr}')['head']['sha']
        print(json.dumps(land(args.pr, into, head, api=api)))
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        parser.exit(2, f'land: {exc}\n')

if __name__ == '__main__':
    main()
