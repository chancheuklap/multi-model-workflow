from __future__ import annotations
import importlib.util
import json
import os
import shutil
import shlex
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / 'mmw-v5-cloud/tools/dispatch/scripts'
sys.path.insert(0, str(TOOLS))

def load(name, path=None):
    spec = importlib.util.spec_from_file_location('cloud_test_' + name, path or TOOLS / (name + '.py'))
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
        self.root = (Path(self.temp.name) / 'repo').resolve(); self.root.mkdir(); self.remote = Path(self.temp.name) / 'origin.git'
        self.old = Path.cwd(); os.chdir(self.root); self.addCleanup(os.chdir, self.old)
        self.env = patch.dict(os.environ, {'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1', 'HOME': str(Path(self.temp.name) / 'home')})
        self.env.start(); self.addCleanup(self.env.stop)
        self.models = self.model_tool('cursor')
        self.codex = self.model_tool('codex')
        subprocess.run(['git', 'init', '--bare', '-q', str(self.remote)], check=True)
        self.git('init', '-q', '-b', 'night/test'); self.git('config', 'user.name', 'Cloud test'); self.git('config', 'user.email', 'test@example.invalid')
        self.git('remote', 'add', 'origin', str(self.remote))
        (self.root / 'base.txt').write_text('base\n')
        check = self.root / 'scripts' / 'check'
        check.parent.mkdir()
        check.write_text('#!/usr/bin/env bash\n'
                         '[ "$MMW_BASE_REF" = origin/night/test ] || exit 9\n'
                         '[ $# -eq 0 ] || exit 8\n'
                         'exit 0\n')
        check.chmod(0o755)
        self.commit('base'); self.base = self.git('rev-parse', 'HEAD')
        self.git('push', '-q', 'origin', 'night/test')
        self.git('switch', '-q', '-c', 'ticket/issue-1'); (self.root / 'feature.txt').write_text('work\n'); self.commit('work')
        self.head = self.git('rev-parse', 'HEAD'); self.git('push', '-q', 'origin', 'HEAD:refs/pull/7/head'); self.git('switch', '-q', 'night/test')
        self.api = API(); self.api.add(90, 'mmw:spec'); self.api.add(1); self.api.add(2); self.api.children[90] = [1, 2]
        self.api.blockers[2] = [1]
        self.pr = {'number':7,'state':'open','draft':False,'merged_at':None,'merge_commit_sha':None,
                   'head':{'ref':'ticket/issue-1','sha':self.head},'base':{'ref':'night/test','sha':self.base,'repo':{'full_name':self.api.repo}}}
        self.api.prs = [self.pr]; self.merges = 0

    def git(self, *args):
        return subprocess.run(['git', *args], capture_output=True, text=True, check=True).stdout.strip()
    def commit(self, message): self.git('add', '.'); self.git('commit', '--allow-empty', '-q', '-m', message)

    def model_tool(self, host):
        path = Path(self.temp.name) / 'home/.agents/mmw/tools/dispatch/scripts/models.py'
        (self.root / '.agents').mkdir(exist_ok=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(TOOLS / 'models.py', path)
        shutil.copy2(TOOLS / 'status.py', path.with_name('status.py'))
        tool = load('models', path)
        tool.HOST = host
        return tool

    def publish_pr_check(self, body):
        self.git('switch', '-q', 'ticket/issue-1')
        path = self.root / 'scripts' / 'check'
        path.write_text('#!/usr/bin/env bash\n' + body + '\n')
        path.chmod(0o755)
        self.commit('check')
        self.head = self.git('rev-parse', 'HEAD')
        self.git('push', '-q', '--force', 'origin', 'HEAD:refs/pull/7/head')
        self.git('switch', '-q', 'night/test')
        self.pr['head']['sha'] = self.head
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
            result = land.land(7, 'night/test', self.head, api=self.api)
        self.assertEqual(self.merges, 1); self.assertEqual(result['merged_commit'], self.git('rev-parse','HEAD'))
        plan = status.read_plan(90, 'night/test', api=self.api)
        self.assertTrue(plan['tickets'][0]['landed']); self.assertTrue(plan['tickets'][1]['eligible'])

    def test_failed_checks_do_not_update_night(self):
        self.publish_pr_check('echo check-failed >&2; exit 7')
        with patch.object(land, 'command', self.merge_command):
            with self.assertRaises(RuntimeError) as caught:
                land.land(7, 'night/test', self.head, api=self.api)
        message = str(caught.exception)
        self.assertIn('scripts/check exited 7', message)
        self.assertIn('check-failed', message)
        self.assertEqual(self.merges,0); self.assertEqual(self.git('rev-parse','origin/night/test'), self.base)
        self.assertEqual(self.git('worktree','list','--porcelain').count('worktree '), 1)

    def test_check_modifying_tracked_files_is_not_landed(self):
        self.publish_pr_check('echo changed > base.txt')
        with patch.object(land, 'command', self.merge_command):
            with self.assertRaisesRegex(RuntimeError, 'changed tracked files'):
                land.land(7, 'night/test', self.head, api=self.api)
        self.assertEqual(self.merges,0)

    def test_missing_check_does_not_update_night(self):
        self.git('switch', '-q', 'ticket/issue-1')
        self.git('rm', '-q', 'scripts/check')
        self.commit('drop check')
        self.head = self.git('rev-parse', 'HEAD')
        self.git('push', '-q', '--force', 'origin', 'HEAD:refs/pull/7/head')
        self.git('switch', '-q', 'night/test')
        self.pr['head']['sha'] = self.head
        with patch.object(land, 'command', self.merge_command):
            with self.assertRaisesRegex(RuntimeError, 'no executable scripts/check'):
                land.land(7, 'night/test', self.head, api=self.api)
        self.assertEqual(self.merges, 0)
        self.assertEqual(self.git('rev-parse', 'origin/night/test'), self.base)

    def test_non_executable_check_does_not_update_night(self):
        self.git('switch', '-q', 'ticket/issue-1')
        (self.root / 'scripts' / 'check').chmod(0o644)
        self.git('add', '--chmod=-x', 'scripts/check')
        self.commit('drop check mode')
        self.head = self.git('rev-parse', 'HEAD')
        self.git('push', '-q', '--force', 'origin', 'HEAD:refs/pull/7/head')
        self.git('switch', '-q', 'night/test')
        self.pr['head']['sha'] = self.head
        with patch.object(land, 'command', self.merge_command):
            with self.assertRaisesRegex(RuntimeError, 'no executable scripts/check'):
                land.land(7, 'night/test', self.head, api=self.api)
        self.assertEqual(self.merges, 0)
        self.assertEqual(self.git('rev-parse', 'origin/night/test'), self.base)

    def test_conflict_is_preserved_as_failure_without_merging(self):
        self.git('switch','-q','ticket/issue-1'); (self.root/'base.txt').write_text('worker\n'); self.commit('worker base'); self.head=self.git('rev-parse','HEAD')
        self.git('push','-q','--force','origin','HEAD:refs/pull/7/head'); self.git('switch','-q','night/test')
        (self.root/'base.txt').write_text('night\n'); self.commit('night base'); self.git('push','-q','origin','night/test')
        self.pr['head']['sha']=self.head; self.pr['base']['sha']=self.git('rev-parse','HEAD')
        with patch.object(land,'command',self.merge_command):
            with self.assertRaisesRegex(RuntimeError,'CONFLICT'):
                land.land(7,'night/test',self.head,api=self.api)
        self.assertEqual(self.merges,0)

    def test_wrong_target_or_head_never_runs_checks(self):
        sentinel = self.root / 'should-not-exist'
        self.publish_pr_check(f'touch {shlex.quote(str(sentinel))}')
        for into, head in [('dev', self.head), ('night/test', self.base)]:
            with self.subTest(into=into, head=head):
                with self.assertRaises(ValueError):
                    land.land(7, into, head, api=self.api)
                self.assertFalse(sentinel.exists())

    def test_models_use_the_user_file_and_ignore_project_copies(self):
        config = json.loads((ROOT / 'mmw-v5-cloud/models.json').read_text())
        config['rows']['codex']['review-axis'] = {'model': 'user-model', 'effort': 'high'}
        self.codex.write_config(config)
        (self.root / '.agents/models.json').write_text('{"rows": {}}')
        self.assertEqual(self.codex.row('review-axis'), {'model': 'user-model', 'effort': 'high'})
        other = Path(self.temp.name) / 'outside-git'; other.mkdir()
        os.chdir(other)
        self.assertEqual(self.codex.row('review-axis')['model'], 'user-model')
        self.assertEqual(self.codex.config_path(), Path.home() / '.agents/models.json')

    def test_native_host_settings_apply_to_each_worker_grade_and_review_role(self):
        (self.root/'.cursor').mkdir(exist_ok=True)
        config={'max_workers':3,'rows':{
            'codex':{role:{'model':'gpt-6.1-sol','effort':'high'} for role in self.models.ROLES},
            'cursor':{role:{'model':'grok-4.7','effort':'high','context':'256k','fast':True} for role in self.models.ROLES},
        }}
        config['rows']['codex']['senior-worker']['model']='senior-specific-model'
        config['rows']['cursor']['junior-worker']['fast']=False
        self.models.write_config(config);self.codex.write_config(config);self.commit('host-specific role settings')
        fixed=self.git('rev-parse','HEAD')
        self.assertEqual(self.codex.row('senior-worker'),{'model':'senior-specific-model','effort':'high'})
        self.assertEqual(self.models.row('junior-worker'),config['rows']['cursor']['junior-worker'])
        for role in self.models.ROLES:
            if role!='senior-worker':
                self.assertEqual(self.codex.row(role),{'model':'gpt-6.1-sol','effort':'high'})
            if role!='junior-worker':
                self.assertEqual(self.models.row(role),config['rows']['cursor'][role])

    def check_assignments(self, host):
        tool = self.codex if host == 'codex' else self.models
        folder = tool.project_agents()
        config = json.loads((ROOT / 'mmw-v5-cloud/models.json').read_text())
        self.models.write_config(config); self.codex.write_config(config)
        self.commit('models')
        fork = self.git('rev-parse', 'HEAD')
        self.git('branch', 'dev'); self.git('branch', 'project/demo'); self.git('branch', 'night/spec-90')
        self.git('push', '-q', 'origin', 'dev', 'project/demo', 'night/spec-90')
        self.git('switch', '-q', 'night/spec-90')
        api = API(); api.add(90, 'mmw:spec'); api.add(18); api.children[90] = [18]
        plain = API(); plain.add(18)
        plain.items[18]['labels'] = [{'name': 'mmw:ticket'}, {'name': 'ready-for-agent'}]
        self.assertEqual(tool.spawn_worker('18', api=plain)['cards'], [])
        worker = tool.spawn_worker('18', api=api)['cards'][0]
        self.assertEqual(worker['model_row'], {'role': 'junior-worker', **config['rows'][host]['junior-worker']})
        self.assertIn(f'Repository: {api.repo}', worker['prompt'])
        self.assertIn('Starting branch: night/spec-90', worker['prompt'])
        self.assertIn(f'Starting commit: {fork}', worker['prompt'])
        self.assertIn('own cloud checkout', worker['prompt'])
        self.assertIn('issue-N branch: ticket/issue-18', worker['prompt'])
        self.assertEqual(self.git('rev-parse', '--abbrev-ref', 'HEAD'), 'night/spec-90')
        self.git('switch', '-q', '-c', 'ticket/issue-18')
        (self.root / 'resume.txt').write_text('existing work\n')
        self.commit('existing ticket work'); resumed_head = self.git('rev-parse', 'HEAD')
        self.git('push', '-q', 'origin', 'ticket/issue-18')
        self.git('switch', '-q', 'night/spec-90')
        again = tool.spawn_worker('18', api=api)['cards'][0]
        self.assertIn('Starting branch: ticket/issue-18', again['prompt'])
        self.assertIn(f'Starting commit: {resumed_head}', again['prompt'])
        self.assertEqual(self.git('rev-parse', '--abbrev-ref', 'HEAD'), 'night/spec-90')
        self.assertEqual(tool.spawn_review(api=api)['cards'], [])
        self.git('switch', '-q', 'ticket/issue-18')
        api.prs = [{'number': 8, 'state': 'open', 'draft': True, 'head': {'ref': 'ticket/issue-18', 'sha': resumed_head},
                    'base': {'ref': 'night/spec-90', 'sha': fork, 'repo': {'full_name': api.repo}}}]
        self.assertEqual(tool.spawn_verifier(api=api)['cards'], [])
        feature = folder / 'skills/verify-demo/features/login.md'
        feature.parent.mkdir(parents=True)
        (feature.parent.parent / 'SKILL.md').write_text('name: verify-demo\n')
        feature.write_text('login\n')
        changed = json.loads(json.dumps(config))
        changed['rows'][host]['researcher']['model'] = 'next-run-only'
        tool.write_config(changed)
        self.commit('feature and future settings'); head = self.git('rev-parse', 'HEAD')
        self.git('push', '-q', 'origin', 'ticket/issue-18'); api.prs[0]['head']['sha'] = head
        ticket = tool.spawn_verifier(api=api)['cards'][0]
        feature_path = feature.relative_to(self.root).as_posix()
        self.assertIn(f'Repository: {api.repo}', ticket['prompt'])
        self.assertIn(f'Commit: {head}', ticket['prompt'])
        self.assertIn('own cloud checkout', ticket['prompt'])
        self.assertIn(feature_path, ticket['prompt'])
        self.assertIn('Return pass or fail to the Worker.', ticket['prompt'])
        self.assertEqual(ticket['model_row'], {'role': 'verifier', **config['rows'][host]['verifier']})
        self.assertEqual(tool.named_feature_paths([f'Feature: `{feature_path}`'], head), [feature_path])
        question = self.root / 'question.md'; question.write_text('Trace the login flow.')
        researcher = tool.spawn_researcher(str(question))['cards'][0]
        self.assertEqual(researcher['model_row']['model'], changed['rows'][host]['researcher']['model'])
        self.assertEqual(question.read_text(), researcher['prompt'])
        self.git('commit', '-q', '--allow-empty', '-m', 'unpushed')
        with self.assertRaisesRegex(ValueError, 'HEAD is not pushed'): tool.spawn_verifier(api=api)
        self.git('reset', '--hard', head)
        self.git('switch', '-q', 'night/spec-90')
        self.git('merge', '--no-ff', '--no-edit', 'ticket/issue-18')
        tip = self.git('rev-parse', 'HEAD'); self.git('push', '-q', 'origin', 'night/spec-90')
        api.prs[0].update(merged_at='2026-11-05T00:00:00Z', merge_commit_sha=tip, state='closed')
        review = tool.spawn_review(api=api)
        self.assertEqual([x['description'] for x in review['cards']], ['Standards', 'Spec', 'Tests', 'Verify night/spec-90'])
        for card in review['cards']:
            self.assertIn(tip, card['prompt'])
            self.assertIn('own cloud checkout', card['prompt'])
        self.assertIn('Spec #90', review['cards'][1]['prompt'])
        self.assertIn(feature_path, review['cards'][-1]['prompt'])
        self.assertIn('Return pass or fail to the Coordinator.', review['cards'][-1]['prompt'])
        self.assertEqual(self.git('rev-parse', '--abbrev-ref', 'HEAD'), 'night/spec-90')

    def test_cursor_assignments_use_project_commits_and_verification(self):
        self.check_assignments('cursor')

    def test_codex_assignments_use_project_commits_and_verification(self):
        self.check_assignments('codex')

    def prepare_multiple_verifiers(self, feature_changed):
        config = json.loads((ROOT / 'mmw-v5-cloud/models.json').read_text())
        self.codex.write_config(config)
        for name in ('alpha', 'beta', 'gamma'):
            skill = self.root / f'.agents/skills/verify-{name}'
            (skill / 'features').mkdir(parents=True)
            (skill / 'SKILL.md').write_text(f'name: verify-{name}\n')
            (skill / 'features/screen.md').write_text('existing screen\n')
        self.commit('existing verification skills')
        fork = self.git('rev-parse', 'HEAD')
        self.git('branch', 'project/demo'); self.git('branch', 'night/spec-90')
        self.git('push', '-q', 'origin', 'project/demo', 'night/spec-90')
        self.git('switch', '-q', '-c', 'ticket/issue-18', 'night/spec-90')
        (self.root / 'backend.py').write_text('backend change\n')
        if feature_changed:
            (self.root / '.agents/skills/verify-alpha/features/screen.md').write_text('changed screen\n')
        self.commit('ticket change'); head = self.git('rev-parse', 'HEAD')
        self.git('push', '-q', 'origin', 'ticket/issue-18')
        api = API(); api.add(90, 'mmw:spec'); api.add(18); api.children[90] = [18]
        api.prs = [{'number': 8, 'state': 'open', 'draft': True,
                    'head': {'ref': 'ticket/issue-18', 'sha': head},
                    'base': {'ref': 'night/spec-90', 'sha': fork, 'repo': {'full_name': api.repo}}}]
        return api, fork, head

    def merge_multiple_verifier_ticket(self, api):
        self.git('switch', '-q', 'night/spec-90')
        self.git('merge', '--no-ff', '--no-edit', 'ticket/issue-18')
        tip = self.git('rev-parse', 'HEAD'); self.git('push', '-q', 'origin', 'night/spec-90')
        api.prs[0].update(merged_at='2026-11-05T00:00:00Z', merge_commit_sha=tip, state='closed')
        return tip

    def test_multiple_verifiers_skip_backend_only_ticket(self):
        api, _, _ = self.prepare_multiple_verifiers(False)
        self.assertEqual(self.codex.spawn_verifier(api=api), {'host': 'codex', 'skipped': ['verifier'], 'cards': []})

    def test_multiple_verifiers_skip_backend_only_review(self):
        api, fork, _ = self.prepare_multiple_verifiers(False)
        tip = self.merge_multiple_verifier_ticket(api)
        review = self.codex.spawn_review(api=api)
        self.assertEqual([card['description'] for card in review['cards']], ['Standards', 'Spec', 'Tests'])
        self.assertEqual(review['skipped'], ['verifier'])
        self.assertEqual((review['fork'], review['reviewed']), (fork, tip))
        for card in review['cards']:
            self.assertIn(f'Diff: git diff {fork} {tip}', card['prompt'])
            self.assertIn('Landed tickets: #18', card['prompt'])

    def test_multiple_verifiers_reject_changed_feature(self):
        api, _, _ = self.prepare_multiple_verifiers(True)
        message = 'more than one verify-<app>: verify-alpha, verify-beta, verify-gamma'
        with self.assertRaisesRegex(ValueError, message):
            self.codex.spawn_verifier(api=api)
        self.merge_multiple_verifier_ticket(api)
        with self.assertRaisesRegex(ValueError, message):
            self.codex.spawn_review(api=api)

    def test_research_cli_preserves_inherit_and_cursor_options(self):
        config = json.loads((ROOT / 'mmw-v5-cloud/models.json').read_text())
        for tool, host in [(self.models, 'cursor'), (self.codex, 'codex')]:
            config['rows'][host]['researcher'].update(model='inherit', effort='inherit')
            if host == 'cursor': config['rows'][host]['researcher'].update(context='256k', fast=False)
            tool.write_config(config)
        self.commit('inherited settings')
        question = self.root / 'question.md'; question.write_text('Read the existing feature map.')
        for tool, host in [(self.models, 'cursor'), (self.codex, 'codex')]:
            with self.subTest(host=host):
                run = subprocess.run([sys.executable, tool.__file__, 'spawn', 'researcher', '--prompt', str(question), '--host', host],
                                     capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stderr)
                card = json.loads(run.stdout)['cards'][0]
                self.assertEqual(card['model_row'], {'role': 'researcher', **config['rows'][host]['researcher']})
                self.assertEqual(question.read_text(), card['prompt'])

    def test_open_night_adopts_and_resumes_published_branch(self):
        config = json.loads((ROOT / 'mmw-v5-cloud/models.json').read_text())
        self.models.write_config(config); self.commit('models')
        self.git('branch', 'dev'); self.git('push', '-q', 'origin', 'dev')
        self.git('switch', '-q', '-c', 'host/open', 'dev')
        opened = self.models.open_night('other', '', '3')
        self.assertEqual(opened['night_branch'], 'night/ticket-3')
        self.assertEqual(opened['project_branch'], 'project/other')
        self.assertEqual(self.git('rev-parse', '--abbrev-ref', 'HEAD'), 'night/ticket-3')
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.git('rev-parse', 'origin/project/other'))
        self.git('commit', '-q', '--allow-empty', '-m', 'night moved'); self.git('push', '-q', 'origin', 'night/ticket-3')
        self.git('branch', 'host/resume', 'night/ticket-3~1'); self.git('switch', '-q', 'host/resume')
        self.git('branch', '-D', 'night/ticket-3')
        resumed = self.models.open_night('other', '', '3')
        self.assertEqual(resumed['night_branch'], 'night/ticket-3')
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.git('rev-parse', 'origin/night/ticket-3'))
        self.git('switch', '-q', '-c', 'host/wrong', 'dev')
        (self.root / 'wrong.txt').write_text('unrelated work'); self.commit('wrong start')
        with self.assertRaisesRegex(ValueError, 'start from project/other'):
            self.models.open_night('other', '', '4')

    def test_hosts_share_config_and_only_validate_the_selected_host(self):
        config=json.loads((ROOT/'mmw-v5-cloud/models.json').read_text())
        for tool, host in [(self.codex,'codex'),(self.models,'cursor')]:
            selected={'rows':{host:config['rows'][host]}}
            tool.config_path().unlink(missing_ok=True)
            tool.write_config(selected)
            self.assertEqual(tool.read_config(),selected)
        self.assertEqual(self.codex.config_path(),self.models.config_path())
        self.codex.config_path().unlink()
        with self.assertRaises(FileNotFoundError): self.codex.read_config()
        self.assertEqual(self.models.native_host(), 'cursor')
        self.assertEqual(self.codex.native_host(), 'codex')

    def test_partial_or_malformed_github_pages_fail_explicitly(self):
        api=object.__new__(status.GitHub);api.repo='example/project'
        with patch.object(status,'command',return_value='{"message":"unreadable"}'):
            with self.assertRaises(ValueError):api.listing('issues')

if __name__ == '__main__':unittest.main()
