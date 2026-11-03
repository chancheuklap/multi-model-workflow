from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / 'mmw-v5-cloud/tools/dispatch/scripts'
sys.path.insert(0, str(TOOLS))

def load(name):
    spec = importlib.util.spec_from_file_location('cloud_test_' + name, TOOLS / (name + '.py'))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

status = load('status'); land = load('land'); models = load('models')

class API:
    repo = 'example/project'
    def __init__(self): self.items = {}; self.children = {}; self.blockers = {}; self.prs = []
    def issue(self, n): return self.items[n]
    def get(self, address): return self.prs[0] if address.startswith('pulls/') else self.items[int(address.split('/')[1])]
    def listing(self, address):
        if address.startswith('pulls?'): return self.prs
        n = int(address.split('/')[1])
        if '/sub_issues' in address: return [self.items[x] for x in self.children.get(n, [])]
        if '/dependencies/blocked_by' in address: return [self.items[x] for x in self.blockers.get(n, [])]
        raise AssertionError(address)
    def add(self, n, kind='mmw:ticket', state='open'):
        tags = [kind] + (['ready-for-agent', 'junior-worker'] if kind == 'mmw:ticket' else [])
        self.items[n] = {'number': n, 'title': f'Work {n}', 'body': f'Body {n}', 'state': state, 'labels': [{'name': x} for x in tags]}

class CloudRuntime(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mmw-cloud-test-'); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'; self.root.mkdir(); self.remote = Path(self.temp.name) / 'origin.git'
        self.old = Path.cwd(); os.chdir(self.root); self.addCleanup(os.chdir, self.old)
        self.env = patch.dict(os.environ, {'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1'})
        self.env.start(); self.addCleanup(self.env.stop)
        subprocess.run(['git', 'init', '--bare', '-q', str(self.remote)], check=True)
        self.git('init', '-q', '-b', 'night/test'); self.git('config', 'user.name', 'Cloud test'); self.git('config', 'user.email', 'test@example.invalid')
        self.git('remote', 'add', 'origin', str(self.remote))
        (self.root / 'base.txt').write_text('base\n'); self.commit('base'); self.base = self.git('rev-parse', 'HEAD')
        self.git('push', '-q', 'origin', 'night/test')
        self.git('switch', '-q', '-c', 'issue-1'); (self.root / 'feature.txt').write_text('work\n'); self.commit('work')
        self.head = self.git('rev-parse', 'HEAD'); self.git('push', '-q', 'origin', 'HEAD:refs/pull/7/head'); self.git('switch', '-q', 'night/test')
        self.api = API(); self.api.add(90, 'mmw:spec'); self.api.add(1); self.api.add(2); self.api.children[90] = [1, 2]
        self.api.blockers[2] = [1]
        self.pr = {'number':7,'state':'open','draft':False,'merged_at':None,'merge_commit_sha':None,
                   'head':{'ref':'issue-1','sha':self.head},'base':{'ref':'night/test','sha':self.base,'repo':{'full_name':self.api.repo}}}
        self.api.prs = [self.pr]; self.merges = 0

    def git(self, *args):
        return subprocess.run(['git', *args], capture_output=True, text=True, check=True).stdout.strip()
    def commit(self, message): self.git('add', '.'); self.git('commit', '-q', '-m', message)
    def merge_command(self, *args, **kwargs):
        if args[:4] == ('gh', 'api', '--method', 'PUT'):
            self.merges += 1
            self.git('merge', '--no-ff', '--no-edit', self.head); self.git('push', '-q', 'origin', 'night/test')
            sha = self.git('rev-parse', 'HEAD'); self.pr.update(merged_at='2026-11-02T00:00:00Z',merge_commit_sha=sha,state='closed')
            return json.dumps({'merged':True,'sha':sha})
        return status.command(*args, **kwargs)

    def test_single_ticket_does_not_dispatch_children_or_siblings(self):
        self.api.children[1] = [2]
        plan = status.read_plan(1, 'night/test', single=True, api=self.api)
        self.assertEqual([r['number'] for r in plan['tickets']], [1]); self.assertTrue(plan['tickets'][0]['eligible'])

    def test_closed_predecessor_without_landing_still_blocks(self):
        self.api.items[1]['state'] = 'closed'
        plan = status.read_plan(90, 'night/test', api=self.api)
        self.assertFalse(plan['tickets'][1]['eligible']); self.assertFalse(plan['tickets'][1]['blockers'][0]['resolved'])

    def test_landing_releases_only_actual_merged_dependency(self):
        with patch.object(land, 'command', self.merge_command):
            result = land.land(7, 'night/test', self.head, 'git cat-file -e HEAD:feature.txt', api=self.api)
        self.assertEqual(self.merges, 1); self.assertEqual(result['merged_commit'], self.git('rev-parse','HEAD'))
        plan = status.read_plan(90, 'night/test', api=self.api)
        self.assertTrue(plan['tickets'][0]['landed']); self.assertTrue(plan['tickets'][1]['eligible'])

    def test_failed_checks_do_not_update_night(self):
        with patch.object(land, 'command', self.merge_command):
            with self.assertRaisesRegex(RuntimeError, 'NIGHT was not updated'):
                land.land(7, 'night/test', self.head, 'exit 7', api=self.api)
        self.assertEqual(self.merges,0); self.assertEqual(self.git('rev-parse','origin/night/test'), self.base)
        self.assertEqual(self.git('worktree','list','--porcelain').count('worktree '), 1)

    def test_check_modifying_tracked_candidate_is_not_landed(self):
        with patch.object(land, 'command', self.merge_command):
            with self.assertRaisesRegex(RuntimeError, 'changed tracked candidate'):
                land.land(7, 'night/test', self.head, 'echo changed > base.txt', api=self.api)
        self.assertEqual(self.merges,0)

    def test_conflict_is_preserved_as_failure_without_merging(self):
        self.git('switch','-q','issue-1'); (self.root/'base.txt').write_text('worker\n'); self.commit('worker base'); self.head=self.git('rev-parse','HEAD')
        self.git('push','-q','--force','origin','HEAD:refs/pull/7/head'); self.git('switch','-q','night/test')
        (self.root/'base.txt').write_text('night\n'); self.commit('night base'); self.git('push','-q','origin','night/test')
        self.pr['head']['sha']=self.head; self.pr['base']['sha']=self.git('rev-parse','HEAD')
        with patch.object(land,'command',self.merge_command):
            with self.assertRaisesRegex(RuntimeError,'CONFLICT'):
                land.land(7,'night/test',self.head,'true',api=self.api)
        self.assertEqual(self.merges,0)

    def test_wrong_target_or_head_never_runs_checks(self):
        for into, head in [('dev',self.head),('night/test',self.base)]:
            with self.subTest(into=into,head=head):
                with self.assertRaises(ValueError):land.land(7,into,head,'touch should-not-exist',api=self.api)
        self.assertFalse((self.root/'should-not-exist').exists())

    def test_model_reads_project_not_local_home(self):
        folder=self.root/'.cursor'; folder.mkdir(); config=json.loads((ROOT/'mmw-v5-cloud/models.json').read_text())
        config['rows']['review-axis']={'host':'codex','model':'chosen-native-id','effort':'high'}
        models.write_config(config)
        self.commit('project model configuration')
        fixed = self.git('rev-parse','HEAD')
        changed = json.loads(json.dumps(config)); changed['rows']['review-axis']['model'] = 'next-run-only'; models.write_config(changed)
        with patch.dict(os.environ,{'MMW_HOME':str(self.root/'unused-local-home')}):
            self.assertEqual(models.row('review-axis','codex',fixed),{'model':'chosen-native-id','effort':'high'})
            with self.assertRaisesRegex(ValueError,'native host'):models.row('review-axis','cursor',fixed)
        self.assertEqual(models.row('junior-worker','codex',fixed),{})

    def test_partial_or_malformed_github_pages_fail_explicitly(self):
        api=object.__new__(status.GitHub);api.repo='example/project'
        with patch.object(status,'command',return_value='{"message":"unreadable"}'):
            with self.assertRaises(ValueError):api.listing('issues')

if __name__ == '__main__':unittest.main()
