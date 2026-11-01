"""Setup prerequisites through temp repositories, fake GitHub and isolated model state."""

import importlib.util
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[2] / 'tools'
CHECK = TOOLS / 'setup-mmw/scripts/check.py'
spec = importlib.util.spec_from_file_location('v5_setup_under_test', CHECK)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)
labels_spec = importlib.util.spec_from_file_location('v5_setup_fixture_labels', TOOLS / 'verify-ticket/scripts/labels.py')
labels = importlib.util.module_from_spec(labels_spec)
labels_spec.loader.exec_module(labels)

GH = r'''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args=sys.argv[1:]
with open(os.environ['SETUP_GH_LOG'],'a') as log: log.write(json.dumps(args)+'\n')
if args[:2]==['repo','view'] and '--jq' in args:
    assert args[2]=='https://github.test/owner/project.git',args
    assert 'GH_REPO' not in os.environ
    print('owner/project');sys.exit()
assert os.environ['GH_REPO']=='owner/project',os.environ.get('GH_REPO')
if args[:2]==['repo','view']:
    if os.environ.get('BAD_REPO_JSON'): print('not json');sys.exit()
    print(json.dumps({'nameWithOwner':'owner/project','hasIssuesEnabled':not os.environ.get('ISSUES_OFF'),
                      'defaultBranchRef':{'name':'main'}}));sys.exit()
if args[:2]==['issue','list']:
    if os.environ.get('ISSUE_READ_FAIL'): print('HTTP 502: issues unreadable',file=sys.stderr);sys.exit(1)
    print('[]' if os.environ.get('NO_ISSUES') else '[{"number":7}]');sys.exit()
if args[:2]==['issue','view']:
    assert args[2:]==['7','--json','parent,blockedBy'],args
    if os.environ.get('GH_LINK_FIELDS_OFF'): print('Unknown JSON field: blockedBy',file=sys.stderr);sys.exit(1)
    print('{"parent":null,"blockedBy":{"nodes":[]}}');sys.exit()
if args[:2]==['label','list']:
    if os.environ.get('LABEL_READ_FAIL'): print('HTTP 403: labels unreadable',file=sys.stderr);sys.exit(1)
    print(Path(os.environ['SETUP_LABELS']).read_text());sys.exit()
if args[:1]==['api']:
    path=next(arg for arg in args[1:] if not arg.startswith('-'))
    assert path.startswith('repos/owner/project/'),path
    if path.endswith('/dependencies/blocked_by') and os.environ.get('LINKS_OFF'):
        print('HTTP 404: native dependency endpoint unavailable',file=sys.stderr);sys.exit(1)
    if 'protected=true' in path: print(os.environ.get('PROTECTED_BRANCH',''));sys.exit()
    if path.endswith('/rulesets'): sys.exit()
    assert path in ('repos/owner/project/issues/7/sub_issues',
                    'repos/owner/project/issues/7/dependencies/blocked_by'),args
    print('[]');sys.exit()
raise AssertionError('unexpected or non-read-only gh command: '+repr(args))
'''


class SetupCheck(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='mmw-v5-setup-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        subprocess.run(['git', '-C', str(self.repo), 'remote', 'add', 'origin',
                        'https://github.test/owner/project.git'], check=True)
        (self.repo / '.gitignore').write_text('.worktrees/\n.scratch/\n')
        (self.repo / 'scripts').mkdir()
        self.entrypoint = self.repo / 'scripts/check'
        self.entrypoint.write_text('#!/bin/sh\necho unexpected check execution >&2\nexit 93\n')
        self.entrypoint.chmod(0o755)
        self.home = self.root / '.mmw-v5'
        self.home.mkdir()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        for name in ('git','bash','python3','realpath','dirname'):
            (self.bin / name).symlink_to(shutil.which(name))
        for name in ('gh', 'paseo', 'orca', 'herdr', 'codex', 'claude'):
            path = self.bin / name
            path.write_text(GH if name == 'gh' else '#!/bin/sh\necho unexpected host start >&2\nexit 94\n')
            path.chmod(0o755)
        self.label_file = self.root / 'labels.json'
        self.label_file.write_text(json.dumps([{'name': name, 'color': value[0], 'description': value[1]}
                                               for name, value in labels.LABELS.items()]))
        self.catalog = self.root / 'catalog.json'
        offerings = {'codex': [{'id': 'chosen-model', 'name': 'Chosen model', 'thinkingOptionIds': ['high']}],
                     'claude': [{'id': 'sonnet', 'name': 'Sonnet', 'thinkingOptionIds': ['high']}]}
        self.catalog.write_text(json.dumps({source: offerings for source in ('cli', 'paseo', 'codex-app')}))
        config = check.models.default_local_config()
        config['runner'] = 'paseo'
        for row in config['rows'].values():
            row.update(host='codex', model='chosen-model', effort='high')
        config['rows']['reviewer'].update(host='claude', model='unavailable-model')
        self.config = self.home / 'models.json'
        self.config.write_text(json.dumps(config))
        self.log = self.root / 'gh.jsonl'
        self.env = dict(os.environ, HOME=str(self.root), MMW_HOME=str(self.home), MMW_RUNNER='',
                        MMW_HOST_CATALOG=str(self.catalog), MMW_CATALOG_MODE='wrong-source',
                        GH_REPO='foreign/default', SETUP_GH_LOG=str(self.log),
                        SETUP_LABELS=str(self.label_file), PATH=str(self.bin))
        for name in ('CODEX_THREAD_ID','CODEX_APP_RUNTIME_CLI_PATH','CODEX_APP_TOOLS_PIPE_PATH',
                     'HERDR_ENV','TERM_PROGRAM'):
            self.env.pop(name,None)

    def run_check(self, *args, extra=None):
        return subprocess.run([sys.executable, str(CHECK), *args], cwd=self.repo,
                              env={**self.env, **(extra or {})}, capture_output=True, text=True, timeout=15)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_selected_role_uses_origin_and_does_not_require_unused_host_or_installation(self):
        before=self.config.read_bytes()
        for binary in ('orca','herdr','claude'):
            (self.bin / binary).unlink()
        result=self.run_check('--role','researcher')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('tracker: owner/project on GitHub',result.stdout)
        self.assertIn('model researcher: codex chosen-model (high) via paseo',result.stdout)
        self.assertIn('SETUP OK',result.stdout)
        self.assertEqual(self.config.read_bytes(),before)
        self.assertFalse((self.home / 'installed-root').exists())
        self.assertFalse((self.repo / 'CLAUDE.md').exists())
        self.assertTrue(all(call[:1]==['api'] or call[:2] in
                            (['repo','view'],['issue','list'],['issue','view'],['label','list']) for call in self.calls()))

    def test_repository_check_must_exist_and_be_executable(self):
        for absent in (False,True):
            with self.subTest(absent=absent):
                if absent: self.entrypoint.unlink()
                else: self.entrypoint.chmod(0o644)
                result=self.run_check()
                self.assertEqual(result.returncode,1,result.stdout+result.stderr)
                self.assertRegex(result.stdout,r'(?m)^missing +repository +scripts/check:')

    def test_issues_off_is_missing_and_branch_protection_remains_a_note(self):
        result=self.run_check(extra={'ISSUES_OFF':'1','PROTECTED_BRANCH':'main'})
        self.assertEqual(result.returncode,1,result.stdout)
        self.assertRegex(result.stdout,r'(?m)^missing +repository +tracker: owner/project has Issues turned off')
        self.assertRegex(result.stdout,r'(?m)^note +repository +branch rules: protected branches main')

    def test_missing_labels_and_native_links_are_reported_without_writing(self):
        self.label_file.write_text('[]')
        result=self.run_check(extra={'LINKS_OFF':'1'})
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        self.assertIn('ready-for-agent',result.stdout)
        self.assertIn('native dependency endpoint unavailable',result.stdout)
        self.assertNotIn(['label','create'],[call[:2] for call in self.calls()])

    def test_failed_reads_are_missing_while_an_empty_issue_list_is_unchecked(self):
        for variable,detail in (('BAD_REPO_JSON','tracker:'),('ISSUE_READ_FAIL','issues unreadable'),
                                ('LABEL_READ_FAIL','labels unreadable'),
                                ('GH_LINK_FIELDS_OFF','Unknown JSON field: blockedBy')):
            with self.subTest(variable=variable):
                result=self.run_check(extra={variable:'1'})
                self.assertEqual(result.returncode,1,result.stdout+result.stderr)
                self.assertIn(detail,result.stdout)
        result=self.run_check(extra={'NO_ISSUES':'1'})
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertRegex(result.stdout,r'(?m)^unchecked +repository +sub-issues and dependencies:')

    def test_environment_entrypoints_are_facts_and_never_executed(self):
        marker=self.root / 'environment-was-run'
        environment=self.repo / 'scripts/env'
        environment.write_text(f'#!{sys.executable}\nfrom pathlib import Path\nPath({str(marker)!r}).write_text("ran")\nraise SystemExit(95)\n')
        environment.chmod(0o755)
        (self.repo / 'compose.yaml').write_text('services: {}\n')
        result=self.run_check()
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertRegex(result.stdout,r'(?m)^note +repository +scripts/env:.*not executed')
        self.assertFalse(marker.exists())
        listed=subprocess.run(['git','worktree','list','--porcelain'],cwd=self.repo,capture_output=True,text=True,check=True)
        self.assertEqual(listed.stdout.count('worktree '),1)
        environment.unlink()
        result=self.run_check()
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('compose configuration present',result.stdout)

    def test_default_home_is_v5_and_no_role_does_not_query_models(self):
        result=self.run_check(extra={'MMW_HOME':'', 'MMW_HOST_CATALOG':str(self.root/'absent-catalog.json')})
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn(str(self.home / 'models.json'),result.stdout)
        self.assertRegex(result.stdout,r'(?m)^unchecked +machine +models: no --role supplied')
        self.assertFalse((self.root / '.mmw').exists())

    def test_used_bad_model_and_global_dispatch_shape_error_both_fail(self):
        result=self.run_check('--role','reviewer')
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        self.assertIn('unavailable-model',result.stdout)
        config=json.loads(self.config.read_text())
        del config['rows']['advisor']
        self.config.write_text(json.dumps(config))
        result=self.run_check('--role','researcher')
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        self.assertIn('missing advisor',result.stdout)

    def test_worktree_and_check_log_directories_must_be_ignored(self):
        (self.repo / '.gitignore').unlink()
        result=self.run_check()
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        self.assertRegex(result.stdout,r'(?m)^missing +repository +.gitignore:')
        self.assertIn('.worktrees/',result.stdout)
        self.assertIn('.scratch/',result.stdout)
        self.assertFalse((self.repo / '.worktrees').exists())
        self.assertFalse((self.repo / '.scratch').exists())

    def test_cli_runner_checks_only_used_host_binary(self):
        result=self.run_check('--role','researcher',extra={'MMW_RUNNER':'orca'})
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        (self.bin / 'codex').unlink()
        result=self.run_check('--role','researcher',extra={'MMW_RUNNER':'orca'})
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        self.assertRegex(result.stdout,r'(?m)^missing +machine +codex:')
        self.assertNotIn('model reviewer:',result.stdout)

    def test_only_selected_runner_binary_is_required(self):
        (self.bin / 'paseo').unlink()
        result=self.run_check('--role','researcher')
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        self.assertRegex(result.stdout,r'(?m)^missing +machine +paseo:')

    def test_selected_app_uses_its_own_binary_and_refuses_unsupported_host(self):
        result=self.run_check('--role','researcher',extra={'MMW_RUNNER':'codex-app',
                              'CODEX_APP_RUNTIME_CLI_PATH':str(self.bin/'codex')})
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('Codex App binary:',result.stdout)
        config=json.loads(self.config.read_text())
        config['rows']['researcher'].update(host='claude',model='sonnet')
        self.config.write_text(json.dumps(config))
        result=self.run_check('--role','researcher',extra={'MMW_RUNNER':'codex-app',
                              'CODEX_APP_RUNTIME_CLI_PATH':str(self.bin/'codex')})
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        self.assertIn('cannot start host claude',result.stdout)

    def test_missing_origin_and_missing_config_are_explicit_failures(self):
        self.config.unlink()
        result=self.run_check('--role','researcher')
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        self.assertIn('models.py init',result.stdout)
        subprocess.run(['git','remote','remove','origin'],cwd=self.repo,check=True)
        result=self.run_check()
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        self.assertIn('cannot read origin',result.stdout)
        self.assertNotIn('Traceback',result.stderr)


if __name__ == '__main__':
    unittest.main()
