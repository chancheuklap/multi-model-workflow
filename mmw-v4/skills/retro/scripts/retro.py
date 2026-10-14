#!/usr/bin/env python3
"""Expire candidates, gather retrospective evidence, and apply analyst answers.

Exit 0 completes the command. Exit 1 means some writes may have succeeded.
Exit 2 refuses without a GitHub write. Never reads conversations or external memory.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen


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


def write(args,body=None):
    try:
        return register.body_file_command(args,body) if body is not None else register.command(['gh',*args])
    except (RetroError,OSError,ValueError,KeyError,TypeError) as exc:
        raise PartialWrite(f'GitHub write incomplete: {exc}; inspect the issue, then rerun the same command') from None


def now():
    value = os.environ.get('MMW_NOW')
    if not value:
        return datetime.now(timezone.utc)
    return timestamp(value)


def timestamp(value):
    if not isinstance(value,str):
        raise RetroError(f'{value!r} is not an ISO 8601 timestamp; repair its source')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise RetroError(f'{value!r} needs an ISO 8601 timezone; correct MMW_NOW or the event')
    return parsed


def labels(row):
    return {item['name'] for item in row['labels']}


def history(repo, number):
    comments = register.comments(repo, number)
    state = events.fold(comments, issue=number)
    if state['unreadable']:
        raise RetroError(f'{repo}#{number} has unreadable events: {state["unreadable"]}; repair the comments')
    return comments, state


def expire(repos):
    cutoff = now() - timedelta(days=30)
    plans = []
    for repo in repos:
        for row in register.issue_list(repo):
            if row['state'].lower() != 'open' or 'mmw:lesson' not in labels(row) or 'needs-triage' in labels(row):
                continue
            _, state = history(repo, row['number'])
            occurrences = state['occurrences']
            if occurrences and max(timestamp(o['at']) for o in occurrences) < cutoff:
                plans.append((repo, row['number']))
    for repo, number in plans:
        write(['issue', 'comment', str(number), '--repo', repo],
                                   '30 天没再出现，自动关闭；再出现会重开')
        write([ 'issue', 'close', str(number), '--repo', repo, '--reason', 'not planned'])
        print(f'CLOSED: {repo}#{number}')
    return 0

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
    opened = events.newest(comments, 'spec.opened' if args.spec else 'worker.started', 'ticket.claimed')
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
    for source_repo in args.repos:
        for row in register.issue_list(source_repo):
            if 'mmw:child' not in labels(row) or row['state'].lower() != 'open':
                continue
            child = register.read_issue(source_repo,row['number'])
            parent = child.get('parent')
            if not parent:
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
    run_numbers = [number]
    if args.spec:
        children = register.whole_list(f'repos/{repo}/issues/{number}/sub_issues?per_page=100')
        run_numbers.extend(r['number'] for r in children if 'mmw:ticket' in labels(r))
    for ticket in run_numbers:
        ticket_comments,_ = history(repo,ticket)
        checked.extend(event_comments(ticket_comments,issue_url(repo,ticket),skip=('spec.retroed','ticket.retroed')))
        for c in events.normalise(ticket_comments):
            what,payload = events.parse(c['body'])
            if what!='event' or timestamp(payload['at']) < timestamp(since):
                continue
            signal = payload['event'] in ('ticket.returned','ticket.bounced','ticket.regressed','worker.lost') or (
                payload['event']=='child.opened' and payload.get('kind')=='fault') or (
                payload['event']=='ticket.checked' and payload.get('result')=='handoff')
            if signal:
                source = f'{issue_url(repo,ticket)}#issuecomment-{c["id"] or c["position"]}'
                items['process'].append(dict(kind='signal',source=source,event=payload,body=c['body']))
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
            raise RetroError(f'evidence file {source!r} cannot be read inside {root}')
        lines = target.read_text(encoding='utf-8').splitlines()
        if int(match[2]) > len(lines):
            raise RetroError(f'evidence {source!r} has no such line')
        return 'file',lines[int(match[2])-1]
    parsed = urlparse(source)
    if parsed.netloc == 'github.com':
        match = re.fullmatch(r'/([^/]+/[^/]+)/(issues|commit)/([0-9]+|[0-9a-f]{40})',parsed.path)
        if not match:
            raise RetroError(f'evidence URL {source!r} is not an issue or commit')
        repo,kind,ident = match.groups()
        if kind == 'commit':
            return 'commit',register.gh_json(['api',f'repos/{repo}/commits/{ident}'])
        if parsed.fragment:
            comment = re.fullmatch(r'issuecomment-([0-9]+)',parsed.fragment)
            if not comment:
                raise RetroError(f'evidence URL {source!r} has no comment identifier')
            row = register.gh_json(['api',f'repos/{repo}/issues/comments/{comment[1]}'])
            if not isinstance(row.get('body'),str):
                raise RetroError(f'{source} has no readable primary comment')
            return 'event',row['body']
        return 'issue',register.gh_json(['issue','view',ident,'--repo',repo,'--json','body,title'])
    with urlopen(source,timeout=30) as response:
        return 'url',response.read(100000).decode('utf-8',errors='replace')


def check_analysis(row):
    if row.get('error'):
        raise RetroError(row['error'])
    if not row['evidence'].strip():
        raise RetroError('missing evidence; supply a URL or path:line')
    if not re.search(r'https?://[^\s|]+|[^\s|]+:[1-9][0-9]*',row['evidence']):
        raise RetroError('evidence needs a URL or path:line')
    links = re.findall(r'https?://[^\s；;,|)]+|[^\s；;,|()]+:[1-9][0-9]*',row['evidence'].replace('`',''))
    for link in links:
        evidence_source(link)
    if row['conclusion'] not in ('candidate','propose','reject') and not row['conclusion'].startswith('merge:'):
        raise RetroError('conclusion must be merge:<target>, reject, candidate or propose')
    if not row['code'] or not row['reason']:
        raise RetroError('missing problem code or reason')


def resolve_issue(code,context):
    if code in context['issues']:
        return context['issues'][code]
    match = re.fullmatch(r'#?([1-9][0-9]*)',code)
    if match:
        return dict(repo=context['repo'],number=int(match[1]))
    raise RetroError(f'unknown problem code {code!r}; use a gathered code or issue URL')


def qualifies(occurrences):
    if any(o['source'] in ('stall','owner-correction') for o in occurrences):
        return True
    identities = {(o['seen_in'],o['ticket']) for o in occurrences if o['ticket'] is not None}
    specs = {(o['seen_in'],o['spec']) for o in occurrences if o['spec'] is not None}
    sessions = {o['session'] for o in occurrences if o['session'] != 'none' and o['session']}
    return len(occurrences) >= 2 and any(len(values)>=2 for values in (identities,specs,sessions))


def merge_lesson(row,context):
    source = row['target']
    target = resolve_issue(row['conclusion'].split(':',1)[1],context)
    if source == target:
        raise RetroError('cannot merge a lesson into itself')
    repo,number = target['repo'],target['number']
    comments,_ = history(repo,number)
    saved = {events.parse(c['body'])[1].get('request') for c in comments
             if events.parse(c['body'])[0]=='event'}
    for index, occurrence in enumerate(row['occurrences']):
        request = f'merge-{source["repo"]}-{source["number"]}-{index}'
        if request in saved:
            continue
        body = events.build('lesson.seen',line=f'Merged from {issue_url(source["repo"],source["number"])}',
                            lesson=number,request=request,**occurrence)
        write(['issue','comment',str(number),'--repo',repo],body)
    write(['issue','close',str(source['number']),'--repo',source['repo'],
                      '--reason','duplicate','--duplicate-of',issue_url(repo,number)])


def proposal(plan):
    repo = re.search(r'(?:仓库|repository)[:：]\s*([A-Za-z0-9-]+/[A-Za-z0-9._-]+)',plan)
    path = re.search(r'(?:文件|file)[:：]\s*([^；;\s]+)',plan)
    playbook = re.search(r'Playbook:\s*([^；;\n]+)',plan)
    if not repo or not path or not playbook or not re.search(r'(?:加|删|add|remove)[:：]',plan):
        raise RetroError('proposal needs repository, add/remove, file and Playbook')
    if Path(path[1]).name in ('AGENTS.md','CLAUDE.md','CODING_STANDARDS.md') or 'nowledgemem' in plan:
        raise RetroError('proposal targets an owner-managed file or external memory; choose an allowed destination')
    return dict(repo=register.repository(repo[1]),file=path[1],playbook=playbook[1].strip())


def new_problems(path):
    text = path.read_text(encoding='utf-8')
    section = re.search(r'^## Problems[ \t]*\n(.*)\Z',text,re.M|re.S)
    if not section:
        raise RetroError(f'{path} needs ## Problems; write None when there are no new problems')
    content = section[1].strip()
    if content == 'None':
        return []
    chunks = re.split(r'^### [^\n]+\n',content,flags=re.M)
    bodies = []
    for chunk in chunks:
        if not chunk.strip():
            continue
        body = chunk.strip()
        if not body.startswith('## Problem\n'):
            body = '## Problem\n'+body
        fields = register.problem_fields(body)
        required = ('问题代号','角度','发生了什么','证据','代价','该谁修')
        if any(not fields.get(k) for k in required):
            raise RetroError(f'{path} ## Problems lacks a six-field registration; complete it before applying')
        bodies.append((body,fields))
    if not bodies:
        raise RetroError(f'{path} ## Problems is empty; write None or a registration')
    return bodies


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
        rc = register.main(['add',str(path),'--repo',repo,'--source','retro-signal'])
    finally:
        for key,value in prior.items():
            if value is None:
                os.environ.pop(key,None)
            else:
                os.environ[key] = value
    if rc:
        raise PartialWrite(f'{path} registration exited {rc}; follow register-problem stderr and rerun')


def apply_answers(args):
    context_path = args.context or args.answers[0].parent/'context.json'
    context = json.loads(context_path.read_text(encoding='utf-8'))
    if (args.spec is not None and (args.spec!=context['spec'] or context['ticket'] is not None)) or (args.ticket is not None and (args.ticket!=context['ticket'] or context['spec'] is not None)):
        raise RetroError('apply target differs from context.json; use the matching gather artifact')
    events.build('spec.retroed' if context['spec'] else 'ticket.retroed',
                 ticket=context['ticket'],spec=context['spec'],line='Validate gather context',
                 result='recorded',registered=context['registered'],merged=0,rejected=0,candidates=0,proposals=[],
                 recurred_after_wontfix=context['recurred_after_wontfix'],landed_since_last=context['landed_since_last'],
                 evidence=context['evidence'],unreadable_sources=context['unreadable_sources'])
    valid,errors,problems = [],[],[]
    for path in args.answers:
        for body,fields in new_problems(path):
            owner = fields['该谁修']
            repo = register.toolbox_repo() if owner in ('MMW','MMW 仓库') else register.repository(owner)
            if fields['角度'] not in ('判断','环境','流程','产品') or not re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*',fields['问题代号']):
                raise RetroError(f'{path} ## Problems has an invalid code or angle')
            evidence_source(fields['证据'])
            existing = any(register.problem_fields(r.get('body') or '').get('问题代号')==fields['问题代号']
                           for destination in dict.fromkeys((repo,register.toolbox_repo()))
                           for r in register.issue_list(destination))
            problems.append((body,fields,existing))
    for path in args.answers:
        for row in answer_rows(path):
            try:
                check_analysis(row)
                if row['conclusion'] == 'propose':
                    row['proposal'] = proposal(row['plan'])
                target = resolve_issue(row['code'],context)
                _,state = history(target['repo'],target['number'])
                row['target'] = target
                row['occurrences'] = state['occurrences']
                row['current'] = register.gh_json(['issue','view',str(target['number']),'--repo',target['repo'],'--json','body,labels,state'])
                if 'mmw:lesson' not in labels(row['current']):
                    raise RetroError('answer target is not a lesson; product problems and children stay in their workflows')
                if row['conclusion'].startswith('merge:'):
                    canonical = resolve_issue(row['conclusion'].split(':',1)[1],context)
                    if canonical == target:
                        raise RetroError('cannot merge a lesson into itself')
                    destination = register.gh_json(['issue','view',str(canonical['number']),'--repo',canonical['repo'],'--json','labels'])
                    if 'mmw:lesson' not in labels(destination):
                        raise RetroError('merge target is not a lesson')
                if row['conclusion'] == 'propose' and row['proposal']['repo'] != target['repo']:
                    if row['proposal']['repo'] != register.toolbox_repo():
                        raise RetroError('a proposal transfer must target the installed MMW repository')
                valid.append(row)
            except RetroError as exc:
                message = f'{row["path"]}:{row["line"]}: {exc}'
                print(message,file=sys.stderr)
                errors.append(message)
    if errors and not valid:
        return 2
    counts = dict(merged=0,rejected=0,candidates=0,proposals=[])
    for row in valid:
        if row['conclusion'] != 'candidate' and 'needs-triage' in labels(row['current']):
            row['conclusion'] = 'candidate'
            print(f'{row["code"]}: candidate, already awaiting the owner')
        if row['conclusion'] != 'candidate' and 'wontfix' in labels(row['current']):
            row['conclusion'] = 'candidate'
            print(f'{row["code"]}: candidate, owner refusal preserved; recurrence is recorded in the receipt')
        if row['conclusion'] == 'propose' and not qualifies(row['occurrences']):
            row['conclusion'] = 'candidate'
            print(f'{row["code"]}: candidate, fewer than two independent occurrences and no stall or owner correction')
        if row['conclusion'] == 'candidate':
            counts['candidates'] += 1
        if row['conclusion'] == 'reject':
            counts['rejected'] += 1
            target = row['target']
            write(['issue','comment',str(target['number']),'--repo',target['repo']],row['reason'])
            write(['issue','close',str(target['number']),'--repo',target['repo'],'--reason','not planned'])
        if row['conclusion'].startswith('merge:'):
            counts['merged'] += 1
            merge_lesson(row,context)
        if row['conclusion'] == 'propose':
            target = row['target']
            repo,number = target['repo'],target['number']
            current = row['current']
            if row['proposal']['repo'] != repo:
                transferred = write(['issue','transfer',str(number),row['proposal']['repo'],'--repo',repo])
                match = re.search(r'https://github.com/([^/]+/[^/]+)/issues/([0-9]+)',transferred)
                if not match:
                    raise PartialWrite(f'transfer of {repo}#{number} printed no new URL; inspect its destination before retrying')
                repo,number = match[1],int(match[2])
            body = re.sub(r'(^## Problem[ \t]*\n)(?:[ \t]*\n)*(?:Playbook:[^\n]*\n)?',lambda m: m[1]+f'Playbook: {row["proposal"]["playbook"]}\n',current['body'],count=1,flags=re.M)
            write(['issue','edit',str(number),'--repo',repo],body)
            write(['issue','comment',str(number),'--repo',repo],row['reason']+'\n\n'+row['plan'])
            if 'needs-triage' not in labels(current):
                write(['issue','edit',str(number),'--repo',repo,'--add-label','needs-triage'])
            counts['proposals'].append(number)
    if problems:
        directory = context_path.parent/'problems'
        directory.mkdir(parents=True,exist_ok=True)
        for body,fields,existing in problems:
            register_new_problem(directory/f'{fields["问题代号"]}.md',body,fields,context)
            if not existing:
                context['registered'] += 1
    unreadable = list(dict.fromkeys(context['unreadable_sources'] + errors))
    payload = dict(result='recorded',registered=context['registered'],
                   recurred_after_wontfix=context['recurred_after_wontfix'],landed_since_last=context['landed_since_last'],
                   evidence='partial' if unreadable else 'complete',unreadable_sources=unreadable,**counts)
    name = 'spec.retroed' if context['spec'] else 'ticket.retroed'
    receipt = events.build(name,ticket=context['ticket'],spec=context['spec'],line='复盘已记录。',**payload)
    write(['issue','comment',str(context['spec'] or context['ticket']),'--repo',context['repo']],receipt)
    print(events.describe(events.newest([receipt],name)))
    return 1 if errors else 0

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='verb', required=True)
    expiration = sub.add_parser('expire')
    expiration.add_argument('repos', nargs='+')
    gathering = sub.add_parser('gather')
    target = gathering.add_mutually_exclusive_group(required=True)
    target.add_argument('--spec', type=int)
    target.add_argument('--ticket', type=int)
    gathering.add_argument('repos', nargs='+')
    gathering.add_argument('--out', type=Path, required=True)
    applying = sub.add_parser('apply')
    applying.add_argument('answers', nargs='+',type=Path)
    applying.add_argument('--context',type=Path)
    selection = applying.add_mutually_exclusive_group()
    selection.add_argument('--spec',type=int)
    selection.add_argument('--ticket',type=int)
    args = parser.parse_args(argv)
    try:
        if args.verb == 'expire':
            return expire([register.repository(r) for r in args.repos])
        if args.verb == 'gather':
            args.repos = [register.repository(r) for r in args.repos]
            return gather(args)
        return apply_answers(args)
    except PartialWrite as exc:
        print(f'retro: {exc}',file=sys.stderr)
        return 1
    except (RetroError, events.EventError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f'retro: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
