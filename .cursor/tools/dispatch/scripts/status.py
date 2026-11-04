#!/usr/bin/env python3
"""Read native Issue relationships and actual PR ancestry; never fold session events."""
from __future__ import annotations
import argparse
import json
import re
import subprocess
from urllib.parse import quote


def command(*args, cwd=None):
    run = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if run.returncode:
        raise RuntimeError(run.stderr.strip() or run.stdout.strip() or f'{args[0]} exited {run.returncode}')
    return run.stdout.strip()


class GitHub:
    def __init__(self):
        remote = command('git', 'remote', 'get-url', 'origin')
        self.repo = command('gh', 'repo', 'view', remote, '--json', 'nameWithOwner', '--jq', '.nameWithOwner')
        self.issues = {}

    def get(self, address):
        return json.loads(command('gh', 'api', f'repos/{self.repo}/{address}'))

    def listing(self, address):
        address += ('&' if '?' in address else '?') + 'per_page=100'
        pages = json.loads(command('gh', 'api', f'repos/{self.repo}/{address}', '--paginate', '--slurp'))
        if not isinstance(pages, list) or any(not isinstance(page, list) for page in pages):
            raise ValueError(f'GitHub did not return complete list pages: {address}')
        return [item for page in pages for item in page]

    def issue(self, number):
        if number not in self.issues:
            self.issues[number] = self.get(f'issues/{number}')
        return self.issues[number]


def labels(issue):
    return [label['name'] if isinstance(label, dict) else label for label in issue.get('labels', [])]


def current_night():
    branch = command('git', 'rev-parse', '--abbrev-ref', 'HEAD')
    match = re.fullmatch(r'night/(spec|ticket)-(\d+)', branch)
    if not match:
        raise ValueError('this checkout is not night/spec-N or night/ticket-N')
    kind, number = match.group(1), int(match.group(2))
    return {'branch': branch, 'kind': kind, 'number': number, 'single': kind == 'ticket'}


def read_plan(number, into, *, single=False, api=None):
    api = api or GitHub()
    command('git', 'check-ref-format', '--branch', into)
    command('git', 'fetch', 'origin', f'+refs/heads/{into}:refs/remotes/origin/{into}')
    tip = command('git', 'rev-parse', f'origin/{into}')
    prs = api.listing(f'pulls?state=all&base={quote(into, safe="")}')
    root = api.issue(number)
    visited = set()
    tickets = []

    def tree(issue):
        n = issue['number']
        if n in visited:
            return {**issue, 'children': []}
        visited.add(n)
        children = [tree(item) for item in api.listing(f'issues/{n}/sub_issues')]
        item = {**issue, 'children': children}
        if 'mmw:ticket' in labels(issue):
            tickets.append(item)
        return item

    if single:
        if 'mmw:ticket' not in labels(root):
            raise ValueError('single-ticket status requires the authorized mmw:ticket itself')
        root = {**root, 'children': api.listing(f'issues/{number}/sub_issues')}
        tickets = [root]
    else:
        if 'mmw:spec' not in labels(root):
            raise ValueError('Spec status requires mmw:spec; use --ticket for one execution ticket')
        root = tree(root)
    merged_cache = {}

    def landing(n):
        if n not in merged_cache:
            candidates = [pr for pr in prs if pr['head']['ref'] == f'ticket/issue-{n}']
            landed = False
            for pr in candidates:
                sha = pr.get('merge_commit_sha')
                if pr.get('merged_at') and sha:
                    check = subprocess.run(['git', 'merge-base', '--is-ancestor', sha, tip], capture_output=True)
                    if check.returncode not in (0, 1):
                        raise RuntimeError(f'cannot establish PR #{pr["number"]} ancestry in {into}')
                    landed = landed or check.returncode == 0
            merged_cache[n] = (landed, candidates)
        return merged_cache[n]

    rows = []
    for issue in tickets:
        n = issue['number']; tags = labels(issue)
        landed, candidates = landing(n)
        blockers = []
        for ref in api.listing(f'issues/{n}/dependencies/blocked_by'):
            source = api.issue(ref['number'])
            resolved = landing(source['number'])[0] if 'mmw:ticket' in labels(source) else source['state'] == 'closed'
            blockers.append({'number': source['number'], 'title': source['title'], 'resolved': resolved})
        grades = [tag for tag in tags if tag in ('junior-worker', 'senior-worker')]
        reasons = []
        if landed: reasons.append('already merged into the night branch')
        elif issue['state'] != 'open': reasons.append('ticket closed without a proven landing on the night branch')
        if 'ready-for-agent' not in tags or any(tag in tags for tag in ('needs-triage', 'ready-for-human', 'wontfix')):
            reasons.append('not in the authorized agent queue')
        if len(grades) != 1: reasons.append('ticket needs exactly one worker grade')
        if any(not row['resolved'] for row in blockers): reasons.append('predecessor work not resolved/merged')
        rows.append({'number': n, 'title': issue['title'], 'state': issue['state'], 'labels': tags,
                     'grade': grades[0] if len(grades) == 1 else None,
                     'body': issue.get('body') or '', 'url': issue.get('html_url'),
                     'children': issue.get('children', []), 'blockers': blockers,
                     'prs': candidates, 'landed': landed, 'eligible': not reasons, 'reasons': reasons})
    return {'repo': api.repo, 'root': root, 'into': into, 'night_commit': tip, 'tickets': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('number', nargs='?', type=int)
    parser.add_argument('--into', default='')
    parser.add_argument('--ticket', action='store_true')
    args = parser.parse_args()
    try:
        if args.number is None:
            if args.into or args.ticket:
                raise ValueError('status with no number reads the night branch name')
            night = current_night()
            number, into, single = night['number'], night['branch'], night['single']
        else:
            if not args.into:
                raise ValueError('status N requires --into')
            number, into, single = args.number, args.into, args.ticket
        print(json.dumps(read_plan(number, into, single=single), ensure_ascii=False))
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        parser.exit(2, f'status: {exc}\n')

if __name__ == '__main__':
    main()
