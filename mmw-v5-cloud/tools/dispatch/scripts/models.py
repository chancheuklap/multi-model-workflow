#!/usr/bin/env python3
"""Project model choices for native cloud agents; no local CLI catalog or runner."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile

from status import GitHub, current_night, labels, read_plan

ROLES = ('junior-worker', 'senior-worker', 'advisor', 'researcher', 'candidate', 'review-axis', 'verifier')
INSTALLATIONS = {'.agents': 'codex', '.cursor': 'cursor'}
WORKER_GRADES = ('junior-worker', 'senior-worker')


def installation() -> Path:
    path = Path(__file__).resolve().parents[3]
    if path.name not in INSTALLATIONS:
        raise ValueError('cloud runtime needs a project .agents or .cursor installation')
    return path


def config_path() -> Path:
    return installation() / 'models.json'


def validate(value: dict) -> dict:
    if not isinstance(value, dict):
        raise ValueError('models config must be an object')
    value = {key: item for key, item in value.items() if key != 'max_workers'}
    rows = value.get('rows')
    if not isinstance(rows, dict):
        raise ValueError('rows must be an object of native role settings')
    host = native_host()
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
        root = Path(git_text("rev-parse", "--show-toplevel")).resolve()
        relative = config_path().relative_to(root).as_posix()
        text = subprocess.run(["git", "show", f"{at}:{relative}"], capture_output=True, text=True, check=True).stdout
    return validate(json.loads(text))


def row(role: str, at: str) -> dict:
    return read_config(at)['rows'][native_host()][role]


def git_text(*args: str) -> str:
    run = subprocess.run(['git', *args], capture_output=True, text=True)
    if run.returncode != 0:
        detail = (run.stderr or run.stdout).strip()
        raise ValueError(detail or 'git failed')
    return run.stdout.strip()


def commit_of(ref: str) -> str:
    try:
        return git_text('rev-parse', '--verify', f'{ref}^{{commit}}')
    except ValueError as exc:
        raise ValueError(f'{ref} does not resolve') from exc


def require_file(path: str, label: str) -> str:
    if not path or not Path(path).is_file():
        raise ValueError(f'{label} is not a file: {path}')
    return str(Path(path).resolve())


def assignment(role: str, chosen: dict, description: str, prompt: str) -> dict:
    return {'description': description, 'prompt': prompt, 'model_row': {'role': role, **chosen}}


def ref_exists(ref: str) -> bool:
    return subprocess.run(['git', 'rev-parse', '--verify', '--quiet', ref], capture_output=True).returncode == 0


def is_ancestor(older: str, newer: str) -> bool:
    return subprocess.run(['git', 'merge-base', '--is-ancestor', older, newer], capture_output=True).returncode == 0


def exists_at(commit: str, path: str) -> bool:
    return subprocess.run(['git', 'cat-file', '-e', f'{commit}:{path}'], capture_output=True).returncode == 0


def native_host() -> str:
    return INSTALLATIONS[installation().name]


def fetch_origin() -> None:
    run = subprocess.run(['git', 'fetch', 'origin'], capture_output=True, text=True)
    if run.returncode != 0:
        raise ValueError((run.stderr or run.stdout).strip() or 'git fetch failed')


def publish(ref: str, sha: str) -> None:
    git_text('push', 'origin', f'{sha}:refs/heads/{ref}')
    git_text('fetch', 'origin', f'+refs/heads/{ref}:refs/remotes/origin/{ref}')


def project_fork(night: str) -> tuple[str, str]:
    night_sha = commit_of(night)
    found = []
    listing = git_text('for-each-ref', '--format=%(refname:short)', 'refs/remotes/origin/project')
    for ref in listing.splitlines():
        if not ref.startswith('origin/project/'):
            continue
        try:
            base = git_text('merge-base', night_sha, ref)
        except ValueError:
            continue
        if is_ancestor(base, night_sha):
            found.append((ref.removeprefix('origin/'), base))
    if not found:
        raise ValueError(f'no project branch is a base of {night}')
    bases = {base for _ref, base in found}
    closest = []
    for ref, base in found:
        older = any(base != other and is_ancestor(base, other) for other in bases)
        if not older:
            closest.append((ref, base))
    distinct = {base for _ref, base in closest}
    if len(distinct) != 1:
        names = ', '.join(ref for ref, _base in closest)
        raise ValueError(f'project branch tie: {names}')
    return closest[0]


def resolve_at(at: str | None) -> str:
    if at:
        return at
    branch = git_text('rev-parse', '--abbrev-ref', 'HEAD')
    if re.fullmatch(r'(night/(spec|ticket)|ticket/issue)-\d+', branch):
        _project, fork = project_fork(branch)
        return fork
    return 'HEAD'


def adopt_branch(name: str) -> None:
    current = git_text('rev-parse', '--abbrev-ref', 'HEAD')
    if current == 'HEAD':
        raise ValueError('this checkout is detached; open the night from a branch')
    if current == name:
        return
    if ref_exists(f'refs/heads/{name}'):
        raise ValueError(f'{name} is another branch in this checkout')
    git_text('branch', '-m', current, name)


def open_night(project: str, spec: str, ticket: str) -> dict:
    if bool(spec) == bool(ticket):
        raise ValueError('open takes exactly one of --spec and --ticket')
    number = spec or ticket
    if not number.isdigit() or number == '0':
        raise ValueError('the issue number is a positive integer')
    project_branch = f'project/{project}'
    night = f'night/spec-{spec}' if spec else f'night/ticket-{ticket}'
    git_text('check-ref-format', '--branch', project_branch)
    git_text('check-ref-format', '--branch', night)
    fetch_origin()
    if not ref_exists(f'origin/{project_branch}'):
        if not ref_exists('origin/dev'):
            raise ValueError('origin/dev does not resolve')
        publish(project_branch, commit_of('origin/dev'))
    remote_night = f'origin/{night}'
    if ref_exists(remote_night):
        head, tip = commit_of('HEAD'), commit_of(remote_night)
        if head != tip:
            if not is_ancestor(head, tip):
                raise ValueError(f'start from {night}; this checkout has commits that branch does not')
            git_text('merge', '--ff-only', remote_night)
        adopt_branch(night)
    else:
        if commit_of('HEAD') != commit_of(f'origin/{project_branch}'):
            raise ValueError(f'start from {project_branch} to open {night}')
        adopt_branch(night)
        publish(night, commit_of('HEAD'))
    git_text('branch', '--set-upstream-to', remote_night)
    _project, fork = project_fork(night)
    return {'project_branch': project_branch, 'night_branch': night, 'fork': fork}


def aligned_tip(branch: str) -> str:
    fetch_origin()
    local = commit_of('HEAD')
    remote = f'origin/{branch}'
    if not ref_exists(remote):
        publish(branch, local)
        return local
    remote_sha = commit_of(remote)
    if local == remote_sha:
        return local
    if is_ancestor(remote_sha, local):
        publish(branch, local)
        return local
    if is_ancestor(local, remote_sha):
        git_text('merge', '--ff-only', remote)
        return commit_of('HEAD')
    raise ValueError(f'{branch} diverged from origin')


def ticket_start(ticket: str, night_branch: str) -> str:
    name = f'ticket/issue-{ticket}'
    git_text('check-ref-format', '--branch', name)
    remote = f'origin/{name}'
    fetched = subprocess.run(['git', 'fetch', 'origin', f'+refs/heads/{name}:refs/remotes/origin/{name}'], capture_output=True, text=True)
    if fetched.returncode == 0 and ref_exists(remote):
        return name
    return night_branch


def verify_skill_names(commit: str) -> list[str]:
    listing = git_text('ls-tree', '-r', '--name-only', commit)
    names = []
    for line in listing.splitlines():
        match = re.fullmatch(re.escape(installation().name) + r'/skills/(verify-[^/]+)/SKILL\.md', line)
        if match:
            names.append(match.group(1))
    return names


def named_feature_paths(bodies: list[str], commit: str) -> list[str]:
    found = []
    for body in bodies:
        for match in re.findall(re.escape(installation().name) + r'/skills/verify-[^\s]+/features/[^\s]+', body):
            path = match.rstrip(').,;`\'"')
            if path not in found and exists_at(commit, path):
                found.append(path)
    return found


def feature_changes(base: str, head: str) -> list[str]:
    names = git_text('diff', '--name-only', base, head, '--', f'{installation().name}/skills')
    found = []
    for line in names.splitlines():
        if re.fullmatch(re.escape(installation().name) + r'/skills/verify-[^/]+/features/.+', line) and exists_at(head, line):
            found.append(line)
    return found


def worker_grade(ticket: str, api) -> str | None:
    grades = [name for name in labels(api.issue(int(ticket))) if name in WORKER_GRADES]
    if len(grades) != 1:
        return None
    return grades[0]


def spawn_worker(ticket: str, *, api=None) -> dict:
    host = native_host()
    if not ticket.isdigit() or ticket == '0':
        raise ValueError('--ticket is a positive issue number')
    night = current_night()
    api = api or GitHub()
    grade = worker_grade(ticket, api)
    if grade is None:
        return {'host': host, 'skipped': ['worker'], 'cards': []}
    aligned_tip(night['branch'])
    start = ticket_start(ticket, night['branch'])
    _project, fork = project_fork(night['branch'])
    chosen = row(grade, fork)
    prompt = '\n'.join([
        'Load the installed dispatch skill.',
        'Assigned role: worker.',
        'Follow the Worker reference.',
        'Run in your own cloud checkout at the starting commit.',
        'When the verifier fails, fix the ticket and send a new verifier card.',
        'When the passing commit is the PR head, write the result in the PR.',
        '',
        f'Ticket #{ticket}',
        f'Night branch: {night["branch"]}',
        f'Starting branch: {start}',
        f'Starting commit: {commit_of(f"origin/{start}")}',
        f'issue-N branch: ticket/issue-{ticket}',
        f'Before the first push, rename the current branch to ticket/issue-{ticket}.',
    ])
    return {'host': host, 'skipped': [], 'cards': [assignment(grade, chosen, f'Implement ticket #{ticket}', prompt)]}


def open_pr(api, branch: str) -> dict:
    matched = [pr for pr in api.listing('pulls?state=open')
               if pr['head']['ref'] == branch and pr['state'] == 'open' and str(pr['base']['ref']).startswith('night/')]
    if len(matched) != 1:
        raise ValueError(f'{branch} needs one open PR into a night branch')
    return matched[0]


def spawn_verifier(*, api=None) -> dict:
    host = native_host()
    branch = git_text('rev-parse', '--abbrev-ref', 'HEAD')
    if not re.fullmatch(r'ticket/issue-\d+', branch):
        raise ValueError('spawn verifier runs on ticket/issue-N')
    fetch_origin()
    remote = f'origin/{branch}'
    if not ref_exists(remote):
        raise ValueError('HEAD is not pushed')
    local, pushed = commit_of('HEAD'), commit_of(remote)
    if local != pushed:
        raise ValueError('HEAD is not pushed')
    api = api or GitHub()
    pr = open_pr(api, branch)
    if pr['head']['sha'] != pushed:
        raise ValueError('PR head is not the pushed HEAD')
    skills = verify_skill_names(pushed)
    if len(skills) > 1:
        raise ValueError('more than one verify-<app>: ' + ', '.join(skills))
    features = feature_changes(pr['base']['sha'], pushed)
    if len(skills) != 1 or not features:
        return {'host': host, 'skipped': ['verifier'], 'cards': []}
    _project, fork = project_fork(f'origin/{pr["base"]["ref"]}')
    chosen = row('verifier', fork)
    prompt = '\n'.join([
        'Load the installed dispatch skill.',
        'Assigned role: verifier.',
        'Follow the Verifier reference.',
        'Start in your own cloud checkout at the named commit.',
        'Return pass or fail to the Worker.',
        '',
        f'Branch: {branch}',
        f'Commit: {pushed}',
        'Features:',
        *features,
    ])
    return {'host': host, 'skipped': [], 'cards': [assignment('verifier', chosen, f'Verify {branch}', prompt)]}


def axis_card(chosen: dict, role: str, night: str, fork: str, tip: str, spec_line: str, landed_line: str, *, standards: list[str] | None = None) -> dict:
    title = {'standards': 'Standards', 'spec': 'Spec', 'tests': 'Tests'}[role]
    returns = {
        'standards': 'Return the Standards report to the Coordinator.',
        'spec': 'Return the Spec report, reproduction scripts, and their output to the Coordinator.',
        'tests': 'Return the Tests report, reproduction scripts, and their output to the Coordinator.',
    }[role]
    lines = [
        'Load the installed dispatch skill.',
        f'Assigned role: {role}.',
        f'Use code-review and follow the {title} reference.',
        returns,
        '',
        'This checkout is a temporary branch at the reviewed commit. Keep its name and push nothing.',
        'Run in your own cloud environment.',
        f'Night branch: {night}',
        f'Pinned comparison: {fork}',
        f'Reviewed commit: {tip}',
        f'Diff: git diff {fork} {tip}',
        spec_line,
        landed_line,
    ]
    if standards:
        lines.append('Standards: ' + ', '.join(standards))
    return assignment('review-axis', chosen, title, '\n'.join(lines))


def spawn_review(*, api=None) -> dict:
    host = native_host()
    night = current_night()
    tip = aligned_tip(night['branch'])
    project, fork = project_fork(night['branch'])
    api = api or GitHub()
    plan = read_plan(night['number'], night['branch'], single=night['single'], api=api)
    landed = [row_item for row_item in plan['tickets'] if row_item['landed']]
    landed_line = 'Landed tickets: ' + (', '.join(f'#{item["number"]}' for item in landed) if landed else 'none')
    spec_line = f'Spec #{night["number"]}' if night['kind'] == 'spec' else 'Spec: none'
    skipped = []
    cards = []
    diff = git_text('diff', '--name-only', fork, tip)
    if diff.strip():
        chosen = row('review-axis', fork)
        present = [name for name in ('CODING_STANDARDS.md', 'CONTRIBUTING.md') if exists_at(tip, name)]
        cards.append(axis_card(chosen, 'standards', night['branch'], fork, tip, spec_line, landed_line, standards=present))
        if night['kind'] == 'spec':
            cards.append(axis_card(chosen, 'spec', night['branch'], fork, tip, spec_line, landed_line))
        else:
            skipped.append('spec')
        cards.append(axis_card(chosen, 'tests', night['branch'], fork, tip, spec_line, landed_line))
    else:
        skipped.extend(['standards', 'spec', 'tests'])
    skills = verify_skill_names(tip)
    if len(skills) > 1:
        raise ValueError('more than one verify-<app>: ' + ', '.join(skills))
    features = feature_changes(fork, tip)
    if features:
        for path in named_feature_paths([item.get('body') or '' for item in landed], tip):
            if path not in features:
                features.append(path)
    if len(skills) == 1 and features:
        chosen = row('verifier', fork)
        prompt = '\n'.join([
            'Load the installed dispatch skill.',
            'Assigned role: verifier.',
            'Follow the Verifier reference.',
            'Return pass or fail to the Coordinator.',
            'This checkout is a temporary branch at the named commit. Keep its name and push nothing.',
            'Run in your own cloud environment.',
            '',
            f'Night branch: {night["branch"]}',
            f'Commit: {tip}',
            'Features:',
            *features,
        ])
        cards.append(assignment('verifier', chosen, f'Verify {night["branch"]}', prompt))
    else:
        skipped.append('verifier')
    return {'host': host, 'skipped': skipped, 'cards': cards, 'project_branch': project, 'fork': fork, 'reviewed': tip}


def spawn_researcher(prompt: str, at: str | None = None) -> dict:
    path = require_file(prompt, '--prompt')
    chosen = row('researcher', resolve_at(at))
    text = Path(path).read_text(encoding='utf-8')
    return {'host': native_host(), 'skipped': [], 'cards': [assignment('researcher', chosen, 'Researcher', text)]}


def write_config(value: dict) -> None:
    path = config_path()
    value = validate(value)
    if path.exists():
        current = read_config()
        host = native_host()
        value = {**current, 'rows': {**current['rows'], host: value['rows'][host]}}
    text = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, prefix='.models-', delete=False) as output:
        temporary = Path(output.name)
        output.write(text)
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(prog='dispatch.sh', description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    opened = sub.add_parser('open')
    opened.add_argument('--project', required=True)
    group = opened.add_mutually_exclusive_group(required=True)
    group.add_argument('--spec', default='')
    group.add_argument('--ticket', default='')
    show = sub.add_parser('show')
    show.add_argument('--at', default='')
    get = sub.add_parser('row')
    get.add_argument('role', choices=ROLES)
    get.add_argument('--at', default='')
    spawn = sub.add_parser('spawn')
    spawn.add_argument('kind', choices=('worker', 'verifier', 'review', 'researcher'))
    spawn.add_argument('--ticket', default='')
    spawn.add_argument('--prompt', default='')
    args = parser.parse_args()
    try:
        if args.command == 'open':
            printed = open_night(args.project, args.spec, args.ticket)
        elif args.command == 'show':
            printed = read_config(resolve_at(args.at or None))
        elif args.command == 'row':
            printed = row(args.role, resolve_at(args.at or None))
        elif args.kind == 'worker':
            if not args.ticket:
                raise ValueError('worker spawn needs --ticket')
            printed = spawn_worker(args.ticket)
        elif args.kind == 'verifier':
            printed = spawn_verifier()
        elif args.kind == 'review':
            printed = spawn_review()
        else:
            if not args.prompt:
                raise ValueError('researcher spawn needs --prompt')
            printed = spawn_researcher(args.prompt)
        print(json.dumps(printed, ensure_ascii=False, indent=2))
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        parser.exit(2, f'dispatch: {exc}\n')

if __name__ == '__main__':
    main()
