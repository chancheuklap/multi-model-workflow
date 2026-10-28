#!/usr/bin/env python3
"""Gather retrospective evidence and record analyst answers.

Exit 0 completes the command. Exit 1 means some writes may have succeeded.
Exit 2 refuses without a GitHub write. Never reads conversations or external memory.
"""
from __future__ import annotations

import argparse
import importlib.util
import hashlib
import io
import json
import os
import re
import sys
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


SKILLS = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


register = load('register', SKILLS / 'register-problem/scripts/register.py')
events = register.events
RetroError = register.RegistrationError



class PartialWrite(RetroError):
    pass



class UnreadableEvidence(RetroError):
    def __init__(self,source,detail):
        super().__init__(detail)
        self.source = source


def primary_json(source,args):
    try:
        return register.gh_json(args)
    except RetroError as exc:
        raise UnreadableEvidence(source,str(exc)) from None

def write(args,body=None):
    try:
        return register.body_file_command(args,body) if body is not None else register.command(['gh',*args])
    except (RetroError,OSError,ValueError,KeyError,TypeError) as exc:
        raise PartialWrite(f'GitHub write incomplete: {exc}; inspect the issue, then rerun the same command') from None


def timestamp(value):
    if not isinstance(value,str):
        raise RetroError(f'{value!r} is not an ISO 8601 timestamp; repair its source')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise RetroError(f'{value!r} needs an ISO 8601 timezone; correct the event')
    return parsed


def labels(row):
    return {item['name'] for item in row['labels']}


def history(repo, number):
    comments = register.comments(repo, number)
    state = events.fold(comments, issue=number)
    if state['unreadable']:
        raise RetroError(f'{repo}#{number} has unreadable events: {state["unreadable"]}; repair the comments')
    return comments, state


ANGLES = {'判断': 'judgement', '环境': 'environment', '流程': 'process'}


def inventory(source, status, detail=''):
    return dict(source=source, status=status, detail=detail)


def event_comments(comments, url_prefix, *, skip=()):
    out = []
    for item in comments:
        what, value = events.parse(item.get('body') or '')
        if what == 'event' and value.get('event') not in skip:
            out.append(inventory(item.get('html_url') or item.get('url') or
                                 f'{url_prefix}#issuecomment-{item.get("id")}',
                                 'present', 'script-written event comment'))
    return out


def issue_url(repo, number):
    return f'https://github.com/{repo}/issues/{number}'


def gather(args):
    repo = register.current_repo()
    number = args.spec or args.ticket
    comments, state = history(repo, number)
    starts = ('spec.opened',) if args.spec else ('worker.started', 'ticket.claimed')
    receipt = events.newest(comments, 'spec.retroed', 'ticket.retroed')
    opened = min((record for record in state['events'] if record['event'] in starts
                  and (not receipt or timestamp(record['at']) > timestamp(receipt['at']))),
                 key=lambda record: timestamp(record['at']), default=None)
    if not opened and receipt:
        source = f'{issue_url(repo,number)}#issuecomment-{receipt["comment"]}'
        raise RetroError(f'{repo}#{number} has no run start after {source}; start a new run before gathering')
    if not opened or not opened['at']:
        raise RetroError(f'{repo}#{number} has no run start; restore its start event before gathering')
    since = opened['at']
    items = {angle: [] for angle in ANGLES.values()}
    checked = event_comments(comments, issue_url(repo, number), skip=('spec.retroed','ticket.retroed'))
    context = dict(repo=repo, spec=args.spec, ticket=args.ticket, since=since,
                   registered=0, recurred_after_wontfix=[], landed_since_last=0,
                   evidence='complete', unreadable_sources=[], issues={})
    for source_repo in args.repos:
        rows = register.whole_list(f'repos/{source_repo}/issues?state=all&labels=mmw%3Alesson&since={since}&per_page=100')
        for row in rows:
            if 'pull_request' in row or 'mmw:lesson' not in labels(row):
                continue
            n = row['number']
            _, folded = history(source_repo, n)
            current = [seen for seen in folded['occurrences'] if
                       seen['seen_in'] == repo and seen['spec' if args.spec else 'ticket'] == number
                       and timestamp(seen['at']) >= timestamp(since)]
            if not current:
                continue
            fields = register.problem_fields(row.get('body') or '')
            angle = ANGLES.get(fields.get('角度'))
            if not angle:
                raise RetroError(f'{source_repo}#{n} has no lesson angle in ## Problem; correct the registration')
            code = fields.get('问题代号')
            context['issues'][code] = dict(repo=source_repo, number=n)
            context['issues'][issue_url(source_repo,n)] = dict(repo=source_repo,number=n)
            items[angle].append(dict(kind='registration', source=issue_url(source_repo,n),
                                     code=code, body=row['body'], state=row['state'],
                                     occurrences=folded['occurrences']))
            if timestamp(row['created_at']) >= timestamp(since):
                context['registered'] += 1
            if 'wontfix' in labels(row):
                context['recurred_after_wontfix'].append(n)
                items[angle].append(dict(kind='recurred-after-wontfix',source=issue_url(source_repo,n)))
    run_numbers = [number]
    if args.spec:
        children = register.whole_list(f'repos/{repo}/issues/{number}/sub_issues?per_page=100')
        run_numbers.extend(r['number'] for r in children if 'mmw:ticket' in labels(r))
    for source_repo in args.repos:
        for row in register.issue_list(source_repo):
            if ('mmw:child' not in labels(row) or 'needs-triage' in labels(row)
                    or row['state'].lower() != 'open'):
                continue
            child = register.read_issue(source_repo,row['number'])
            parent = child.get('parent')
            if not parent or source_repo != repo or parent['number'] not in run_numbers:
                continue
            parent_row = register.read_issue(source_repo,parent['number'])
            if parent_row['state'].lower() != 'closed':
                continue
            _, parent_state = history(source_repo,parent['number'])
            resolution = parent_state['children'].get(str(row['number']),{})
            if not resolution.get('resolution'):
                items['process'].append(dict(kind='orphaned-child',source=issue_url(source_repo,row['number']),
                                             parent=issue_url(source_repo,parent['number'])))
    merges = []
    previous_retro = []
    for row in register.issue_list(repo):
        if not labels(row) & {'mmw:spec','mmw:ticket'}:
            continue
        prior_comments, _ = history(repo,row['number'])
        receipt = events.newest(prior_comments,'spec.retroed','ticket.retroed')
        if receipt and timestamp(receipt['at']) < timestamp(since):
            previous_retro.append(receipt)
        merged = events.newest(prior_comments,'spec.merged')
        if merged and timestamp(merged['at']) < timestamp(since):
            merges.append(merged)
    if merges:
        last = max(merges,key=lambda r:timestamp(r['at']))
        sha = last['payload']['merge']
        log = register.command(['git','log','--format=%H%x00%B%x00',f'{sha}..HEAD'])
        parts = log.split('\0')
        for i in range(0,len(parts)-1,2):
            commit, message = parts[i].strip(),parts[i+1]
            reverted = re.search(r'This reverts commit ([0-9a-f]{40})',message)
            if reverted:
                items['process'].append(dict(kind='reverted-commit',source=f'https://github.com/{repo}/commit/{commit}',
                                             reverted=reverted[1]))
    stats_since = max((r['at'] for r in previous_retro),key=timestamp,default=since)
    for source_repo in args.repos:
        for row in register.issue_list(source_repo):
            fields = register.problem_fields(row.get('body') or '')
            if (row['state'].lower()!='closed' or row.get('state_reason')!='completed' or
                    'mmw:ticket' not in labels(row) or fields.get('角度') not in ANGLES):
                continue
            link = register.closing_link(source_repo,row['number'])
            angle = ANGLES[fields['角度']]
            if not link:
                items[angle].append(dict(kind='approved-without-commit',source=issue_url(source_repo,row['number']),
                                         body=row['body']))
            elif timestamp(row.get('closed_at') or row['updated_at']) >= timestamp(stats_since):
                context['landed_since_last'] += 1
    current_sources = [m for group in items.values() for m in group if m['kind']=='registration']
    for source_repo in args.repos:
        for row in register.issue_list(source_repo):
            if 'mmw:lesson' not in labels(row):
                continue
            source = issue_url(source_repo,row['number'])
            if any(m['source']==source for m in current_sources):
                continue
            fields = register.problem_fields(row.get('body') or '')
            related = [m for m in current_sources if m['code']==fields.get('问题代号') or
                       register.problem_fields(m['body']).get('发生了什么')==fields.get('发生了什么') or
                       set(re.findall(r'[a-z0-9]+',m['code'] or '')) &
                       set(re.findall(r'[a-z0-9]+',fields.get('问题代号','')))]
            for angle in {ANGLES[register.problem_fields(m['body'])['角度']] for m in related}:
                _,folded = history(source_repo,row['number'])
                items[angle].append(dict(kind='related-lesson',source=source,state=row['state'],body=row['body'],
                                         occurrences=folded['occurrences']))
                code = fields.get('问题代号')
                context['issues'].setdefault(code,dict(repo=source_repo,number=row['number']))
                context['issues'][source] = dict(repo=source_repo,number=row['number'])
    for ticket in run_numbers:
        ticket_comments,_ = history(repo,ticket)
        checked.extend(event_comments(ticket_comments,issue_url(repo,ticket),skip=('spec.retroed','ticket.retroed')))
        for c in events.normalise(ticket_comments):
            what,payload = events.parse(c['body'])
            if what!='event' or timestamp(payload['at']) < timestamp(since):
                continue
            signal = payload['event'] in ('ticket.returned','ticket.bounced','ticket.regressed','worker.lost') or (
                payload['event']=='child.opened' and payload.get('kind') in ('fault','contract')) or (
                payload['event']=='ticket.checked' and payload.get('result')=='handoff')
            if signal:
                source = f'{issue_url(repo,ticket)}#issuecomment-{c["id"] or c["position"]}'
                item = dict(kind='signal',source=source,event=payload,body=c['body'])
                if payload['event'] == 'child.opened' and payload['kind'] == 'contract':
                    child = register.gh_json(['api',f'repos/{repo}/issues/{payload["child"]}'])
                    item['child_body'] = child['body']
                    settlement = events.newest(
                        [comment for comment in ticket_comments
                         if events.parse(comment['body'])[0] == 'event'
                         and str(events.parse(comment['body'])[1].get('child')) == str(payload['child'])],
                        'child.closed')
                    item['settlement'] = settlement['body'] if settlement else 'not yet settled'
                items['process'].append(item)
                if not any(source in m['body'] for m in current_sources):
                    items['process'].append(dict(kind='unregistered-signal',source=source,event=payload['event']))
    args.out.mkdir(parents=True, exist_ok=True)
    for angle, material in items.items():
        path = args.out / f'{angle}.md'
        if not material:
            if path.exists():
                path.unlink()
            continue
        path.write_text(f'# {angle} materials\n\n' + json.dumps(material,ensure_ascii=False,indent=2) + '\n',encoding='utf-8')
        print(f'{path}\t{len(material)}')
    context['evidence_checked'] = checked
    (args.out/'context.json').write_text(json.dumps(context,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return 0


def backlog(args):
    lessons = []
    assessed = 0
    for repo in dict.fromkeys(args.repos):
        for row in register.whole_list(f'repos/{repo}/issues?state=open&labels=mmw%3Alesson&per_page=100'):
            if 'pull_request' in row or row['state'].lower() != 'open' or 'mmw:lesson' not in labels(row):
                continue
            comments, state = history(repo, row['number'])
            records = [events.parse(c['body'])[1] for c in events.normalise(comments)
                       if events.parse(c['body'])[0] == 'event']
            assessments = [r for r in records if r['event'] == 'lesson.assessed']
            last_merge = max((i for i, r in enumerate(records) if r['event'] == 'lessons.merged'), default=-1)
            merged = records[last_merge] if last_merge >= 0 else None
            problem = re.search(r'^## Problem[^\S\n]*\n(.*?)(?=^## |\Z)',
                                row.get('body') or '', re.M | re.S)
            lessons.append(dict(repo=repo, number=row['number'],
                                problem=problem[1].strip() if problem else '',
                                occurrences=state['occurrences'], assessments=assessments, merged=merged))
            assessed += sum(r['event'] == 'lesson.assessed' for r in records[last_merge+1:])
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out/'backlog.json').write_text(json.dumps(lessons, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'BACKLOG {len(lessons)} open, {assessed} assessed since last merge')
    return 0


def answer_rows(path):
    text = path.read_text(encoding='utf-8')
    rows = []
    for line_number,line in enumerate(text.splitlines(),1):
        if not line.lstrip().startswith('|'):
            continue
        cells = [c.strip() for c in re.split(r'(?<!\\)\|',line.strip().strip('|'))]
        if cells[0] == '代号' or all(re.fullmatch(r'[: -]+',c) for c in cells):
            continue
        if len(cells) != 5:
            rows.append(dict(path=str(path),line=line_number,error='expected five table cells'))
        else:
            rows.append(dict(path=str(path),line=line_number,code=cells[0],conclusion=cells[1],
                             reason=cells[2],evidence=cells[3],plan=cells[4]))
    return rows


def evidence_source(source):
    if not source.startswith(('https://','http://')):
        match = re.fullmatch(r'(.+):([1-9][0-9]*)',source)
        if not match:
            raise RetroError(f'evidence {source!r} needs path:line')
        root = Path.cwd().resolve()
        target = (root/match[1]).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            raise UnreadableEvidence(source,f'evidence file {source!r} cannot be read inside {root}')
        lines = target.read_text(encoding='utf-8').splitlines()
        if int(match[2]) > len(lines):
            raise UnreadableEvidence(source,f'evidence {source!r} has no such line')
        return 'file',lines[int(match[2])-1]
    parsed = urlparse(source)
    if parsed.netloc == 'github.com':
        match = re.fullmatch(r'/([^/]+/[^/]+)/(issues|commit)/([0-9]+|[0-9a-f]{40})',parsed.path)
        if not match:
            raise RetroError(f'evidence URL {source!r} is not an issue or commit')
        repo,kind,ident = match.groups()
        if kind == 'commit':
            return 'commit',primary_json(source,['api',f'repos/{repo}/commits/{ident}'])
        if parsed.fragment:
            comment = re.fullmatch(r'issuecomment-([0-9]+)',parsed.fragment)
            if not comment:
                raise RetroError(f'evidence URL {source!r} has no comment identifier')
            row = primary_json(source,['api',f'repos/{repo}/issues/comments/{comment[1]}'])
            if not isinstance(row.get('body'),str):
                raise UnreadableEvidence(source,f'{source} has no readable primary comment')
            return 'event',row['body']
        return 'issue',primary_json(source,['issue','view',ident,'--repo',repo,'--json','body,title'])
    raise RetroError(f'evidence URL {source!r} is not a GitHub primary source; supply an issue, commit, or path:line')


def check_evidence(evidence):
    if not evidence.strip():
        raise RetroError('missing evidence; supply a URL or path:line')
    if not re.search(r'https?://[^\s|]+|[^\s|]+:[1-9][0-9]*',evidence):
        raise RetroError('evidence needs a URL or path:line')
    links = re.findall(r'https?://[^\s；;,|)]+|[^\s；;,|()]+:[1-9][0-9]*',evidence.replace('`',''))
    for link in links:
        try:
            evidence_source(link)
        except (OSError,UnicodeError) as exc:
            raise UnreadableEvidence(link,str(exc)) from None


def check_analysis(row):
    if row.get('error'):
        raise RetroError(row['error'])
    check_evidence(row['evidence'])
    if row['conclusion'] not in ('candidate','propose','reject') and not re.fullmatch(r'merge:\S.*', row['conclusion']):
        raise RetroError('conclusion must be merge:<target>, reject, candidate or propose')
    if not row['code'] or not row['reason']:
        raise RetroError('missing problem code or reason')


def resolve_issue(code,context):
    code = re.sub(r'\s*[（(].*[）)]\s*$', '', code).strip()
    if code in context['issues']:
        return context['issues'][code]
    match = re.fullmatch(r'#?([1-9][0-9]*)',code)
    if match:
        return dict(repo=context['repo'],number=int(match[1]))
    match = re.fullmatch(r'([A-Za-z0-9-]+/[A-Za-z0-9._-]+)#([1-9][0-9]*)', code)
    if not match:
        match = re.fullmatch(r'https://github.com/([A-Za-z0-9-]+/[A-Za-z0-9._-]+)/issues/([1-9][0-9]*)/?', code)
    if match:
        return dict(repo=register.repository(match[1]), number=int(match[2]))
    raise RetroError(f'unknown problem code {code!r}; use a gathered code or issue URL')


def qualifies(occurrences):
    if any(o['source'] in ('stall','owner-correction') for o in occurrences):
        return True
    identities = {(o['seen_in'],o['ticket']) for o in occurrences if o['ticket'] is not None}
    specs = {(o['seen_in'],o['spec']) for o in occurrences if o['spec'] is not None}
    sessions = {o['session'] for o in occurrences if o['session'] != 'none' and o['session']}
    return len(occurrences) >= 2 and any(len(values)>=2 for values in (identities,specs,sessions))


def lesson_reference(value):
    match = re.fullmatch(r'([A-Za-z0-9-]+/[A-Za-z0-9._-]+)#([1-9][0-9]*)', value)
    if not match:
        raise RetroError(f'{value!r} needs owner/repo#number; correct the decisions file')
    return dict(repo=register.repository(match[1]), number=int(match[2]))


def merge_lesson(source, target, occurrences):
    repo, number = target['repo'], target['number']
    comments, _ = history(repo, number)
    saved = {events.parse(c['body'])[1].get('request') for c in comments
             if events.parse(c['body'])[0] == 'event'}
    for index, occurrence in enumerate(occurrences):
        request = f'merge-{source["repo"]}-{source["number"]}-{index}'
        if request in saved:
            continue
        body = events.build('lesson.seen', line=f'Merged from {issue_url(source["repo"], source["number"])}',
                            lesson=number, request=request, **occurrence)
        write(['issue', 'comment', str(number), '--repo', repo], body)


def merge_apply(args):
    data = json.loads(args.decisions.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise RetroError(f'{args.decisions}: expected a JSON object with batch and decisions; correct the file')
    for field in ('batch', 'decisions'):
        if field not in data:
            raise RetroError(f'{args.decisions}: missing {field}; add the field to the decisions file')
    batch = data['batch']
    rows = data['decisions']
    if not isinstance(rows, list):
        raise RetroError(f'{args.decisions}: decisions must be a list; correct the file')
    events.build('lessons.merged', ticket=None, line='Validate batch', decision='kept', batch=batch)
    plan = []
    sources = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise RetroError(f'{args.decisions}: decisions[{index}] must be an object; correct the file')
        for field in ('lesson', 'decision', 'reason'):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise RetroError(f'{args.decisions}: decisions[{index}].{field} needs a nonempty string; correct the file')
        source = lesson_reference(row['lesson'])
        source_key = f'{source["repo"]}#{source["number"]}'
        if source_key in sources:
            raise RetroError(f'{row["lesson"]} has more than one decision; reconcile the decisions file')
        sources[source_key] = row['decision']
        decision, reason = row['decision'], row['reason']
        body = events.build('lessons.merged', ticket=None, batch=batch, decision=decision,
                            line=f'{decision}. {reason}')
        target = None
        if decision.startswith('merged:'):
            target = lesson_reference(decision.split(':', 1)[1])
        elif decision not in ('closed', 'kept'):
            raise RetroError('merge-apply accepts closed, merged:owner/repo#number or kept; record spec/ticket with events.py')
        current = register.gh_json(['api', f'repos/{source["repo"]}/issues/{source["number"]}'])
        if 'pull_request' in current or 'mmw:lesson' not in labels(current):
            raise RetroError(f'{row["lesson"]} is not a lesson; correct the decisions file')
        comments, state = history(source['repo'], source['number'])
        completed = [events.parse(c['body'])[1] for c in comments
                     if events.parse(c['body'])[0] == 'event'
                     and events.parse(c['body'])[1]['event'] == 'lessons.merged'
                     and events.parse(c['body'])[1].get('batch') == batch]
        if completed:
            if any(r.get('decision') != decision for r in completed):
                raise RetroError(f'{row["lesson"]} already has another decision for batch {batch}; use a new batch')
            continue
        if target:
            destination = register.gh_json(['api', f'repos/{target["repo"]}/issues/{target["number"]}'])
            if 'pull_request' in destination or 'mmw:lesson' not in labels(destination):
                raise RetroError('merge target is not a lesson; correct the decisions file')
            if destination['state'].lower() != 'open':
                raise RetroError(f'{target["repo"]}#{target["number"]} is closed; choose an open merge destination in {args.decisions}')
            history(target['repo'], target['number'])
        plan.append(dict(source=source, target=target, decision=decision, body=body,
                         occurrences=state['occurrences'], state=current['state']))
    for row in plan:
        target = row['target']
        if target and sources.get(f'{target["repo"]}#{target["number"]}', 'kept') != 'kept':
            raise RetroError('a merge target is also being closed or merged; choose the final destination in the decisions file')
    try:
        for row in plan:
            source, target = row['source'], row['target']
            if target:
                merge_lesson(source, target, row['occurrences'])
            if row['decision'] != 'kept' and row['state'].lower() != 'closed':
                command = ['issue', 'close', str(source['number']), '--repo', source['repo']]
                command += (['--reason', 'duplicate', '--duplicate-of', issue_url(target['repo'], target['number'])]
                            if target else ['--reason', 'not planned'])
                write(command)
            write(['issue', 'comment', str(source['number']), '--repo', source['repo']], row['body'])
    except (RetroError, events.EventError, OSError, ValueError, KeyError, TypeError) as exc:
        raise PartialWrite(f'merge-apply incomplete: {exc}; rerun the same decisions file') from None
    print(f'MERGED {len(plan)} decisions, batch {batch}')
    return 0


def new_problems(path):
    result = dict(problems=[],errors=[],unreadable=[])
    text = path.read_text(encoding='utf-8')
    section = re.search(r'^## Problems[ \t]*\n(.*)\Z',text,re.M|re.S)
    if not section:
        raise RetroError(f'{path} needs ## Problems; write None when there are no new problems')
    content = section[1].strip()
    if not content:
        raise RetroError(f'{path} ## Problems is empty; write None or a registration')
    if content == 'None':
        return result
    chunks = re.split(r'^### [^\n]+\n',content,flags=re.M)
    for chunk in chunks:
        if not chunk.strip():
            continue
        body = re.sub(r'^([ \t]*)- (?=(?:问题代号|角度|发生了什么|证据|代价|该谁修)\s*[:：])',
                      r'\1', chunk.strip(), flags=re.M)
        body = re.sub(r'^([ \t]*该谁修[ \t]*[:：][ \t]*[^\n]+?)[ \t]*[（(].*[）)][ \t]*$',
                      r'\1', body, flags=re.M)
        if not body.startswith('## Problem\n'):
            body = '## Problem\n'+body
        fields = register.problem_fields(body)
        try:
            required = ('问题代号','角度','发生了什么','证据','代价','该谁修')
            if any(not fields.get(k) for k in required):
                raise RetroError('lacks a six-field registration; complete the entry before applying')
            owner = fields['该谁修']
            register.repository(register.toolbox_repo() if owner in ('MMW','MMW 仓库') else owner)
            if (fields['角度'] not in ('判断','环境','流程','产品')
                    or not re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*',fields['问题代号'])
                    or len(fields['问题代号']) > 80):
                raise RetroError('invalid problem code or angle; correct the entry')
            check_evidence(fields['证据'])
        except (RetroError,OSError,UnicodeError) as exc:
            message = f'{path} ## Problems {fields.get("问题代号", chunk.splitlines()[0])}: {exc}'
            print(message,file=sys.stderr)
            if isinstance(exc,UnreadableEvidence):
                result['errors'].append(message)
                result['unreadable'].append(exc.source)
            continue
        result['problems'].append((body,fields))
    return result


def register_new_problem(path,body,fields,context):
    owner = fields['该谁修']
    repo = register.toolbox_repo() if owner in ('MMW','MMW 仓库') else register.repository(owner)
    path.write_text(body+'\n',encoding='utf-8')
    prior = {key:os.environ.get(key) for key in ('MMW_SPEC','MMW_TICKET')}
    try:
        for key,value in (('MMW_SPEC',context['spec']),('MMW_TICKET',context['ticket'])):
            if value is None:
                os.environ.pop(key,None)
            else:
                os.environ[key] = str(value)
        with redirect_stdout(io.StringIO()) as output:
            rc = register.main(['add',str(path),'--repo',repo,'--source','retro-signal'])
    finally:
        for key,value in prior.items():
            if value is None:
                os.environ.pop(key,None)
            else:
                os.environ[key] = value
    printed = output.getvalue()
    print(printed,end='')
    if rc:
        raise PartialWrite(f'{path} registration exited {rc}; follow register-problem stderr and rerun')
    action = re.search(r'^(OPENED|APPENDED|REOPENED|ALREADY RECORDED):',printed,re.M)
    if not action:
        raise PartialWrite(f'{path} registration printed no known outcome; inspect register-problem output before retrying')
    conclusion = 'registered' if action[1] == 'OPENED' else 'appended'
    matches = [dict(repo=destination,number=row['number'],conclusion=conclusion)
               for destination in dict.fromkeys((repo,register.toolbox_repo()))
               for row in register.issue_list(destination)
               if register.problem_fields(row.get('body') or '').get('问题代号') == fields['问题代号']]
    if len(matches) != 1:
        raise PartialWrite(f'{path} registration has {len(matches)} matching issues; inspect its problem code and rerun')
    return matches[0]


def prepare_answers(args,context):
    valid,errors,problems,unreadable,unrecorded = [],[],[],[],[]
    for path in args.answers:
        new = new_problems(path)
        problems.extend(new['problems'])
        errors.extend(new['errors'])
        unreadable.extend(new['unreadable'])
    for path in args.answers:
        for row in answer_rows(path):
            try:
                check_analysis(row)
            except RetroError as exc:
                message = f'{row["path"]}:{row["line"]}: {exc}'
                print(message,file=sys.stderr)
                errors.append(message)
                if isinstance(exc,UnreadableEvidence):
                    unreadable.append(exc.source)
                continue
            try:
                target = resolve_issue(row['code'],context)
            except RetroError as exc:
                reason = str(exc)
            else:
                current = register.gh_json(['issue','view',str(target['number']),'--repo',target['repo'],'--json','body,labels,state'])
                reason = (None if 'mmw:lesson' in labels(current) else
                          'answer target is not a lesson; product problems and children stay in their workflows')
            if reason:
                unrecorded.append(dict(code=row['code'],conclusion='unrecorded',reason=reason))
                print(f'{row["path"]}:{row["line"]}: unrecorded: {reason}',file=sys.stderr)
                continue
            _,state = history(target['repo'],target['number'])
            row['target'] = target
            row['occurrences'] = state['occurrences']
            valid.append(row)
    if errors and not valid and not unrecorded and not problems:
        print('no recordable answer rows or new problems; correct the answer file',file=sys.stderr)
        return 2
    return dict(context=context,rows=valid,errors=errors,problems=problems,unreadable=unreadable,
                unrecorded=unrecorded,done=[])


def comment_once(repo,number,body,request):
    marker = f'<!-- retro-apply {request} -->'
    comments,_ = history(repo,number)
    if not any(marker in c['body'] for c in comments):
        write(['issue','comment',str(number),'--repo',repo],body+'\n'+marker+'\n')


def execute_plan(plan,journal):
    context,valid,errors,problems = (plan[k] for k in ('context','rows','errors','problems'))
    context_path = journal.parent.parent/'context.json'
    request = journal.stem
    def save():
        register.statedir.write_atomic(journal,json.dumps(plan,ensure_ascii=False))
    for index,row in enumerate(valid):
        if index in plan['done']:
            continue
        target = row['target']
        assessment = events.build(
            'lesson.assessed', ticket=context['ticket'], spec=context['spec'],
            line=f'{row["conclusion"]}: {row["reason"]}',
            conclusion=row['conclusion'], reason=row['reason'], evidence=row['evidence'], plan=row['plan'],
            run=f'{context["repo"]}#{context["spec"] or context["ticket"]}',
            qualifies=qualifies(row['occurrences']), request=f'{request}-row-{index}')
        comment_once(target['repo'],target['number'],assessment,f'{request}-row-{index}')
        plan['done'].append(index)
        save()
    if problems:
        directory = context_path.parent/'problems'
        directory.mkdir(parents=True,exist_ok=True)
        for index,(body,fields) in enumerate(problems):
            if index in plan.get('problems_done',[]):
                continue
            entry = register_new_problem(directory/f'{fields["问题代号"]}.md',body,fields,context)
            plan.setdefault('registered_problems',[]).append(entry)
            if entry['conclusion'] == 'registered':
                context['registered'] += 1
            plan.setdefault('problems_done',[]).append(index)
            save()
    counts = dict(merged=sum(r['conclusion'].startswith('merge:') for r in valid),
                  rejected=sum(r['conclusion']=='reject' for r in valid),
                  candidates=sum(r['conclusion']=='candidate' for r in valid),
                  proposals=sum(r['conclusion']=='propose' for r in valid))
    unreadable = list(dict.fromkeys(context['unreadable_sources'] + plan['unreadable']))
    disposed = []
    for row in valid:
        disposed.append(dict(**row['target'],conclusion=row['conclusion']))
    disposed.extend(plan.get('registered_problems',[]))
    disposed.extend(plan.get('unrecorded',[]))
    payload = dict(result='recorded',registered=context['registered'],
                   problems=disposed,
                   recurred_after_wontfix=context['recurred_after_wontfix'],landed_since_last=context['landed_since_last'],
                   evidence='partial' if unreadable else 'complete',unreadable_sources=unreadable,**counts)
    name = 'spec.retroed' if context['spec'] else 'ticket.retroed'
    receipt = events.build(name,ticket=context['ticket'],spec=context['spec'],line='复盘已记录。',**payload)
    comment_once(context['repo'],context['spec'] or context['ticket'],receipt,f'{request}-receipt')
    print(events.describe(events.newest([receipt],name)))
    return 1 if errors else 0


def apply_answers(args):
    context_path = args.context or args.answers[0].parent/'context.json'
    context = json.loads(context_path.read_text(encoding='utf-8'))
    if (args.spec is not None and (args.spec!=context['spec'] or context['ticket'] is not None)) or (args.ticket is not None and (args.ticket!=context['ticket'] or context['spec'] is not None)):
        raise RetroError('apply target differs from context.json; use the matching gather artifact')
    events.build('spec.retroed' if context['spec'] else 'ticket.retroed',
                 ticket=context['ticket'],spec=context['spec'],line='Validate gather context',
                 result='recorded',registered=context['registered'],merged=0,rejected=0,candidates=0,proposals=0,
                 recurred_after_wontfix=context['recurred_after_wontfix'],landed_since_last=context['landed_since_last'],
                 evidence=context['evidence'],unreadable_sources=context['unreadable_sources'])
    request = hashlib.sha256(json.dumps([context,[(str(p.resolve()),p.read_text(encoding='utf-8'))
                                                     for p in args.answers]],sort_keys=True).encode()).hexdigest()
    directory = context_path.parent/'.retro-apply'
    directory.mkdir(parents=True,exist_ok=True)
    journal = directory/f'{request}.json'
    with register.statedir.locked(directory/f'{request}.lock',purpose='apply retrospective answers'):
        if journal.exists():
            plan = json.loads(journal.read_text(encoding='utf-8'))
        else:
            plan = prepare_answers(args,context)
            if plan == 2:
                return 2
            register.statedir.write_atomic(journal,json.dumps(plan,ensure_ascii=False))
        return execute_plan(plan,journal)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='verb', required=True)
    gathering = sub.add_parser('gather')
    target = gathering.add_mutually_exclusive_group(required=True)
    target.add_argument('--spec', type=int)
    target.add_argument('--ticket', type=int)
    gathering.add_argument('repos', nargs='+')
    gathering.add_argument('--out', type=Path, required=True)
    listing = sub.add_parser('backlog')
    listing.add_argument('repos', nargs='+')
    listing.add_argument('--out', type=Path, required=True)
    merging = sub.add_parser('merge-apply')
    merging.add_argument('decisions', type=Path)
    applying = sub.add_parser('apply')
    applying.add_argument('answers', nargs='+',type=Path)
    applying.add_argument('--context',type=Path)
    selection = applying.add_mutually_exclusive_group()
    selection.add_argument('--spec',type=int)
    selection.add_argument('--ticket',type=int)
    args = parser.parse_args(argv)
    try:
        if args.verb in ('gather', 'backlog'):
            args.repos = [register.repository(r) for r in args.repos]
            return gather(args) if args.verb == 'gather' else backlog(args)
        if args.verb == 'merge-apply':
            return merge_apply(args)
        return apply_answers(args)
    except PartialWrite as exc:
        print(f'retro: {exc}',file=sys.stderr)
        return 1
    except (RetroError, register.statedir.LockHeld, events.EventError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f'retro: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
