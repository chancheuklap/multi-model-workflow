#!/usr/bin/env python3
"""Stateful gh boundary for rehearsals; unknown calls fail instead of passing silently.

MMW_FAKE_GH_STATE is a JSON file with repository, issues and monotonic counters.
MMW_FAKE_GH_LOG receives one line per invocation. Writers serialize the complete
read/modify/replace transaction so relay reads cannot lose a worker's comment.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit


class Unhandled(ValueError):
    pass


FIELDS = {'number', 'id', 'url', 'title', 'body', 'comments', 'state', 'stateReason',
          'labels', 'assignees', 'blockedBy', 'parent', 'createdAt', 'closedAt'}
COMMON = {'--repo', '-R', '--jq', '-q'}
OPTIONS = {
    ('issue', 'view'): COMMON | {'--json'},
    ('issue', 'create'): COMMON | {'--title', '--body', '--body-file', '--label', '--parent'},
    ('issue', 'edit'): COMMON | {'--add-label', '--remove-label', '--add-assignee',
                                '--remove-assignee', '--parent'},
    ('issue', 'close'): COMMON | {'--reason', '--duplicate-of'},
    ('issue', 'reopen'): COMMON,
    ('issue', 'comment'): COMMON | {'--body', '--body-file'},
    ('issue', 'list'): COMMON | {'--state', '--label', '--limit', '--json'},
    ('label', 'create'): COMMON | {'--color', '--description', '--force'},
    ('repo', 'view'): COMMON | {'--json'},
    ('api',): {'--jq', '-q', '--method', '-X', '-F', '-f', '-H', '--header',
              '--paginate', '--slurp', '-i', '--include'},
}
FLAGS = {'--paginate', '--slurp', '-i', '--include', '--force'}


def parse(args):
    command = tuple(args[:1] if args[:1] == ['api'] else args[:2])
    if command not in OPTIONS:
        raise Unhandled()
    positional, opts = [], {}
    tail = args[len(command):]
    while tail:
        arg = tail.pop(0)
        if arg.startswith('-'):
            if arg not in OPTIONS[command]:
                raise Unhandled()
            value = True if arg in FLAGS else tail.pop(0) if tail else None
            if value is None:
                raise Unhandled()
            opts.setdefault(arg, []).append(value)
        else:
            positional.append(arg)
    return command, positional, opts


def one(opts, *names, default=''):
    return next((opts[name][-1] for name in names if name in opts), default)


def atomic_write(path, value):
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=path.name + '.')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False)
            stream.write('\n')
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def log_call(path, args, unhandled=False):
    clean = [arg.replace('\n', '\\n').replace('\r', '\\r') for arg in args]
    line = ('UNHANDLED ' + ' '.join(clean) if unhandled else 'gh :: ' + ' :: '.join(clean))
    with path.open('a', encoding='utf-8') as stream:
        stream.write(line + '\n')


def stamp(state):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    if state.get('clock'):
        now = max(now, datetime.fromisoformat(state['clock'].replace('Z', '+00:00'))
                  + timedelta(seconds=1))
    state['clock'] = now.isoformat().replace('+00:00', 'Z')
    return state['clock']


def issue(state, number):
    try:
        return state['issues'][str(int(number))]
    except (KeyError, ValueError):
        raise LookupError(f'no issue #{number}') from None


def by_id(state, ident):
    return next(row for row in state['issues'].values() if row['id'] == int(ident))


def children(state, number):
    return [row for row in state['issues'].values()
            if (row.get('parent') or {}).get('number') == int(number)]


def attach(state, parent, child):
    issue(state, parent)
    row = issue(state, child)
    ancestor = int(parent)
    while ancestor:
        if ancestor == int(child):
            raise ValueError('sub-issue cycle')
        ancestor = (issue(state, ancestor).get('parent') or {}).get('number')
    row['parent'] = {'number': int(parent)}
    return row


def body(opts):
    if '--body' in opts:
        return one(opts, '--body')
    if '--body-file' not in opts:
        raise Unhandled()
    path = one(opts, '--body-file')
    return sys.stdin.read() if path == '-' else Path(path).read_text(encoding='utf-8')


def selected(row, fields):
    wanted = fields.split(',')
    if not fields or set(wanted) - FIELDS:
        raise Unhandled()
    return {key: row[key] for key in wanted}


def jq_output(value, query):
    """The selectors used by the pipeline; unsupported jq programs are unknown calls."""
    omit_null = query.strip().endswith('// empty')
    if omit_null:
        query = query.rsplit('// empty', 1)[0].strip()
    values = [value]
    for expression in query.split('|'):
        expression = expression.strip()
        condition = re.fullmatch(r'select\(\.(\w+)\s*==\s*("[^"]*"|true|false|\d+)\)', expression)
        if condition:
            field, expected = condition.groups()
            values = [row for row in values if isinstance(row, dict) and row.get(field) == json.loads(expected)]
            continue
        if expression == '.':
            continue
        if not re.fullmatch(r'\.(?:\[\]|\w+(?:\[\])?)(?:\.\w+(?:\[\])?)*', expression):
            raise Unhandled()
        for field in expression[1:].split('.'):
            each = field.endswith('[]')
            key = field[:-2] if each else field
            selected_values = [row.get(key) if isinstance(row, dict) else None for row in values] if key else values
            if each:
                if any(not isinstance(row, (dict, list)) for row in selected_values):
                    raise Unhandled()
                values = [item for row in selected_values
                          for item in (row.values() if isinstance(row, dict) else row)]
            else:
                values = selected_values
    values = [value for value in values if value is not None or not omit_null]
    return '\n'.join(value if isinstance(value, str) else json.dumps(value) for value in values)


def rest_issue(row):
    return {**row, 'state': row['state'].lower(), 'created_at': row['createdAt'],
            'closed_at': row['closedAt']}


def rest_comment(row):
    return {**row, 'created_at': row['createdAt'], 'updated_at': row['updatedAt'],
            'html_url': row['url']}


def tree(state, row, sizes, depth=0):
    kids = children(state, row['number'])
    blockers = [issue(state, node['number']) for node in row['blockedBy']['nodes']]
    result = {key: row[key] for key in ('number', 'title', 'state')}
    result.update(labels={'nodes': row['labels'][:10], 'totalCount': len(row['labels'])},
                  blockedBy={'nodes': [{'number': node['number'], 'state': node['state']}
                                       for node in blockers[:10]], 'totalCount': len(blockers)},
                  subIssuesSummary={'total': len(kids),
                                    'completed': sum(kid['state'] == 'CLOSED' for kid in kids)})
    if depth < len(sizes):
        result['subIssues'] = {'nodes': [tree(state, kid, sizes, depth + 1)
                                        for kid in kids[:sizes[depth]]]}
    return result


def dispatch(state, command, pos, opts):
    """Return (JSON-or-text, output-is-text, exit-code). Mutations stay under the lock."""
    repo = state['repository']
    explicit_repo = one(opts, '--repo', '-R')
    if explicit_repo and explicit_repo != repo:
        raise LookupError(f'no repository {explicit_repo}')
    login = state.get('login', 'rehearsal')
    if command == ('repo', 'view'):
        if pos not in ([], [repo]):
            raise Unhandled()
        row = {'nameWithOwner': repo, 'url': f'https://github.com/{repo}'}
        fields = one(opts, '--json').split(',')
        if not fields or any(field not in row for field in fields):
            raise Unhandled()
        return {key: row[key] for key in fields}, False, 0
    if command == ('label', 'create'):
        if len(pos) != 1:
            raise Unhandled()
        state.setdefault('labels', {})[pos[0]] = {
            'name': pos[0], 'color': one(opts, '--color'),
            'description': one(opts, '--description')}
        return '', True, 0
    if command == ('issue', 'create'):
        if pos or not one(opts, '--title'):
            raise Unhandled()
        number = max([0, *(int(n) for n in state['issues'])]) + 1
        created = stamp(state)
        row = {'number': number, 'id': 100000 + number,
               'url': f'https://github.com/{repo}/issues/{number}',
               'title': one(opts, '--title'), 'body': body(opts), 'state': 'OPEN',
               'stateReason': None, 'createdAt': created, 'closedAt': None,
               'labels': [{'name': label} for value in opts.get('--label', [])
                          for label in value.split(',')], 'assignees': [],
               'comments': [], 'blockedBy': {'nodes': []}, 'parent': None}
        state['issues'][str(number)] = row
        if '--parent' in opts:
            attach(state, one(opts, '--parent').rsplit('/', 1)[-1], number)
        return row['url'], True, 0
    if command == ('issue', 'list'):
        if pos:
            raise Unhandled()
        fields = one(opts, '--json')
        if not fields or set(fields.split(',')) - FIELDS:
            raise Unhandled()
        rows = list(state['issues'].values())
        desired = one(opts, '--state', default='open').upper()
        if desired not in ('OPEN', 'CLOSED', 'ALL'):
            raise Unhandled()
        labels = {label for value in opts.get('--label', []) for label in value.split(',')}
        rows = [row for row in rows if (desired == 'ALL' or row['state'] == desired)
                and labels <= {item['name'] for item in row['labels']}]
        rows = rows[:int(one(opts, '--limit', default='30'))]
        return [selected(row, one(opts, '--json')) for row in rows], False, 0
    if command[0] == 'issue':
        if len(pos) != 1:
            raise Unhandled()
        row = issue(state, pos[0])
        verb = command[1]
        if verb == 'view':
            # Resolve blocker states at read time, not when the edge was added.
            row = {**row, 'blockedBy': {'nodes': [
                {'number': node['number'], 'state': issue(state, node['number'])['state']}
                for node in row['blockedBy']['nodes']]}}
            return selected(row, one(opts, '--json')), False, 0
        if verb == 'comment':
            text = body(opts)
            ident = state.get('next_comment', 5000)
            state['next_comment'] = ident + 1
            at = stamp(state)
            url = row['url'] + f'#issuecomment-{ident}'
            row['comments'].append({'id': ident, 'body': text, 'url': url,
                                    'createdAt': at, 'updatedAt': at})
            return url, True, 0
        if verb == 'edit':
            for flag, key, field in (('label', 'labels', 'name'), ('assignee', 'assignees', 'login')):
                for value in opts.get('--remove-' + flag, []):
                    remove = {login if item == '@me' else item for item in value.split(',')}
                    row[key] = [item for item in row[key] if item[field] not in remove]
                for value in opts.get('--add-' + flag, []):
                    for item in value.split(','):
                        item = login if item == '@me' else item
                        if not any(old[field] == item for old in row[key]):
                            row[key].append({field: item})
            if '--parent' in opts:
                attach(state, one(opts, '--parent').rsplit('/', 1)[-1], pos[0])
        elif verb == 'close':
            reason = one(opts, '--reason', default='completed')
            if reason not in ('completed', 'not planned'):
                raise Unhandled()
            if '--duplicate-of' in opts:
                issue(state, one(opts, '--duplicate-of'))
                row['duplicateOf'] = int(one(opts, '--duplicate-of'))
                reason = 'not planned'
            row.update(state='CLOSED', stateReason='COMPLETED' if reason == 'completed'
                       else 'NOT_PLANNED', closedAt=stamp(state))
        elif verb == 'reopen':
            row.update(state='OPEN', stateReason='REOPENED', closedAt=None)
        else:
            raise Unhandled()
        return row['url'], True, 0
    if command != ('api',) or len(pos) != 1:
        raise Unhandled()
    address = pos[0]
    fields = dict(value.split('=', 1) for flag in ('-F', '-f') for value in opts.get(flag, []))
    method = one(opts, '--method', '-X', default='POST' if fields else 'GET').upper()
    if address == 'graphql':
        query = fields.get('query', '')
        if not all(word in query for word in ('repository', 'issue(number:$root)', 'subIssuesSummary')):
            raise Unhandled()
        # Accept the tree reader's fields, not an unknown GraphQL query sharing its prefix.
        without_variables = re.sub(r'query\([^)]*\)', '', query)
        without_arguments = re.sub(r'\([^)]*\)', '', without_variables)
        names = set(re.findall(r'\b[A-Za-z_]\w*\b', without_arguments))
        if names - {'repository', 'issue', 'number', 'title', 'state', 'subIssuesSummary',
                    'total', 'completed', 'subIssues', 'nodes', 'labels', 'blockedBy', 'totalCount', 'name'}:
            raise Unhandled()
        sizes = [int(value) for value in re.findall(r'subIssues\(first:(\d+)\)', query)]
        if set(fields) != {'o', 'n', 'root', 'query'} or method != 'POST':
            raise Unhandled()
        result = tree(state, issue(state, fields['root']), sizes)
        return {'data': {'repository': {'issue': result}}}, False, 0
    if address == 'user' and method == 'GET':
        return {'login': login}, False, 0
    url = urlsplit(address)
    path = url.path.removeprefix('/').removeprefix('repos/')
    if address.startswith('https://api.github.com/'):
        path = url.path.removeprefix('/repos/')
    pieces = path.split('/')
    if len(pieces) < 3 or '/'.join(pieces[:2]) not in (repo, '{owner}/{repo}'):
        raise Unhandled()
    suffix = pieces[2:]
    params = parse_qs(url.query)
    if suffix[:1] == ['commits'] and len(suffix) == 2 and method == 'GET':
        sha = suffix[1]
        run = subprocess.run(['git', 'rev-parse', '--verify', sha + '^{commit}'],
                             capture_output=True, text=True)
        if run.returncode:
            raise LookupError(f'commit {sha} not found')
        return {'sha': run.stdout.strip()}, False, 0
    if suffix[:2] == ['issues', 'comments'] and len(suffix) == 3 and method == 'GET':
        row = next((comment for item in state['issues'].values() for comment in item['comments']
                    if str(comment['id']) == suffix[2]), None)
        if row is None:
            raise LookupError('comment not found')
        return rest_comment(row), False, 0
    if suffix == ['issues'] and method == 'GET':
        labels = set(params.get('labels', [''])[0].split(',')) - {''}
        desired = params.get('state', ['open'])[0].upper()
        rows = [rest_issue(row) for row in state['issues'].values()
                if (desired == 'ALL' or row['state'] == desired)
                and labels <= {label['name'] for label in row['labels']}]
    elif suffix[:1] == ['issues'] and len(suffix) >= 2:
        row = issue(state, suffix[1])
        kind = suffix[2:]
        if not kind and method == 'GET':
            return rest_issue(row), False, 0
        if kind == ['sub_issues']:
            if method == 'POST' and set(fields) == {'sub_issue_id'}:
                child = by_id(state, fields['sub_issue_id'])
                return rest_issue(attach(state, row['number'], child['number'])), False, 0
            if method != 'GET':
                raise Unhandled()
            rows = [rest_issue(child) for child in children(state, row['number'])]
        elif kind == ['dependencies', 'blocked_by']:
            if method == 'POST' and set(fields) == {'issue_id'}:
                blocker = by_id(state, fields['issue_id'])
                if blocker['number'] not in [node['number'] for node in row['blockedBy']['nodes']]:
                    row['blockedBy']['nodes'].append({'number': blocker['number']})
                return rest_issue(blocker), False, 0
            if method != 'GET':
                raise Unhandled()
            rows = [rest_issue(issue(state, node['number'])) for node in row['blockedBy']['nodes']]
        elif kind == ['comments'] and method == 'GET':
            rows = [rest_comment(comment) for comment in row['comments']
                    if comment['updatedAt'] >= params.get('since', [''])[0]]
        else:
            raise Unhandled()
    else:
        raise Unhandled()
    size = int(params.get('per_page', ['30'])[0])
    page = int(params.get('page', ['1'])[0])
    if size <= 0 or page <= 0:
        raise Unhandled()
    if '--paginate' in opts:
        pages = [rows[i:i + size] for i in range((page - 1) * size, len(rows), size)] or [[]]
        return pages if '--slurp' in opts else [row for part in pages for row in part], False, 0
    selected_page = rows[(page - 1) * size:page * size]
    if '-i' in opts or '--include' in opts:
        etag = '"' + hashlib.sha256(json.dumps(selected_page, sort_keys=True).encode()).hexdigest() + '"'
        headers = opts.get('-H', []) + opts.get('--header', [])
        if any(header.lower().startswith('if-none-match:') and header.split(':', 1)[1].strip() == etag
               for header in headers):
            return 'HTTP/2 304 Not Modified\nETag: ' + etag + '\n\n', True, 1
        header = 'HTTP/2 200 OK\nETag: ' + etag + '\n'
        if len(rows) > page * size:
            query = {key: value[-1] for key, value in params.items()}
            query['page'] = str(page + 1)
            base = address.split('?', 1)[0]
            if not base.startswith('https://'):
                base = 'https://api.github.com/' + base
            header += f'Link: <{base}?{urlencode(query)}>; rel="next"\n'
        return header + '\n' + json.dumps(selected_page), True, 0
    return selected_page, False, 0


def main(args=None):
    args = list(sys.argv[1:] if args is None else args)
    state_path = Path(os.environ['MMW_FAKE_GH_STATE'])
    log = Path(os.environ['MMW_FAKE_GH_LOG'])
    with state_path.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            command, pos, opts = parse(args.copy())
            state = json.loads(state_path.read_text(encoding='utf-8'))
            value, plain, code = dispatch(state, command, pos, opts)
            jq = one(opts, '--jq', '-q')
            if jq:
                if plain:
                    raise Unhandled()
                value, plain = jq_output(value, jq), True
            atomic_write(state_path, state)
        except Unhandled:
            log_call(log, args, True)
            print('UNHANDLED ' + ' '.join(args), file=sys.stderr)
            return 2
        except (OSError, ValueError, LookupError, StopIteration) as exc:
            log_call(log, args)
            print(f'fake gh: {exc}', file=sys.stderr)
            return 1
        log_call(log, args)
        print(value if plain else json.dumps(value, ensure_ascii=False))
        return code


if __name__ == '__main__':
    raise SystemExit(main())
