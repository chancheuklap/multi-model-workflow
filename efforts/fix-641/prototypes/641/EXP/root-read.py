#!/usr/bin/env python3
"""Compare read-only root discovery on the current repository; never changes GitHub."""
import json
from pathlib import Path
import statistics
import subprocess
import time

QUERY = '''query($o:String!, $n:String!) {
  repository(owner:$o, name:$n) {
    nameWithOwner
    maps: issues(first:100, states:OPEN, labels:["mmw:map"]) {
      nodes { number title state labels(first:100) { nodes { name } pageInfo { hasNextPage } } }
      pageInfo { hasNextPage endCursor }
    }
    specs: issues(first:100, states:OPEN, labels:["mmw:spec"]) {
      nodes { number title state labels(first:100) { nodes { name } pageInfo { hasNextPage } } }
      pageInfo { hasNextPage endCursor }
    }
  }
  rateLimit { cost }
}'''
ROOT = Path(__file__).resolve().parents[5]
OUTPUT = ROOT / '.scratch/fix-641/root-read.json'


def gh(args):
    result = subprocess.run(['gh', *args], capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or 'GitHub read failed')
    return result.stdout


def old():
    repo = gh(['repo', 'view', '--json', 'nameWithOwner', '--jq', '.nameWithOwner']).strip()
    rows = {}
    for label in ('map', 'spec'):
        rows[label] = json.loads(gh(['issue', 'list', '--state', 'open', '--label', 'mmw:' + label,
            '--limit', '1000', '--json', 'number,title,state,labels']))
    return {'repo': repo, 'maps': rows['map'], 'specs': rows['spec']}


def merged():
    answer = json.loads(gh(['api', 'graphql', '-F', 'o={owner}', '-F', 'n={repo}', '-f', 'query=' + QUERY]))
    assert not answer.get('errors'), answer.get('errors')
    repo = answer['data']['repository']
    result = {'repo': repo['nameWithOwner']}
    for name in ('maps', 'specs'):
        connection = repo[name]
        assert not connection['pageInfo']['hasNextPage'], 'this bounded experiment requires one root page'
        result[name] = []
        for node in connection['nodes']:
            assert not node['labels']['pageInfo']['hasNextPage'], 'label list exceeds this experiment'
            result[name].append({**node, 'labels': node['labels']['nodes']})
    return result


def canonical(value):
    return {**value, 'maps': sorted(value['maps'], key=lambda n: n['number']),
            'specs': sorted(value['specs'], key=lambda n: n['number'])}


if __name__ == '__main__':
    runs = []
    baseline = None
    for repeat in range(5):
        for name in (('old', 'merged') if repeat % 2 == 0 else ('merged', 'old')):
            start = time.perf_counter()
            answer = canonical(old() if name == 'old' else merged())
            elapsed = time.perf_counter() - start
            baseline = answer if baseline is None else baseline
            assert answer == baseline, 'repository roots changed or the candidate lost data'
            row = {'repeat': repeat, 'path': name, 'seconds': elapsed,
                   'gh_commands': 3 if name == 'old' else 1, 'errors': 0}
            runs.append(row)
            print(json.dumps(row), flush=True)
    summary = {}
    for name in ('old', 'merged'):
        times = [r['seconds'] for r in runs if r['path'] == name]
        summary[name] = {'median_seconds': statistics.median(times), 'range_seconds': [min(times), max(times)]}
    result = {'scope': 'live root discovery only, not full-board latency or quota',
              'data': baseline, 'runs': runs, 'summary': summary}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2))
    print(json.dumps(summary, indent=2))
