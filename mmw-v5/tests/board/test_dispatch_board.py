from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
import urllib.request

from test_supervisor import EnsureFixture


class DispatchBoardTests(EnsureFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.dispatch = self.script.parents[1] / 'tools/dispatch/scripts/dispatch.sh'
        self.browser_log = self.base / 'browser.jsonl'
        browser = self.bin / 'board-test-browser'
        browser.write_text('#!/usr/bin/env python3\nimport json,os,sys\nfrom pathlib import Path\nwith Path(os.environ["BROWSER_LOG"]).open("a") as f:f.write(json.dumps(sys.argv[1:])+"\\n")\n')
        browser.chmod(0o755)
        self.env.update(BROWSER='board-test-browser %s',BROWSER_LOG=str(self.browser_log))

    def command(self,*args,cwd=None):
        result=subprocess.run(['bash',str(self.dispatch),'board',*args],cwd=cwd or self.repo,
                              env=self.env,capture_output=True,text=True,timeout=20)
        self.own_current_processes()
        return result

    def test_url_starts_and_reuses_the_board_without_opening_a_browser(self):
        first=self.command('--url');self.assertEqual(first.returncode,0,first.stdout+first.stderr)
        self.assertEqual(first.stdout.strip(),f'http://127.0.0.1:{self.port}')
        with urllib.request.urlopen(first.stdout.strip()) as response:self.assertEqual(response.status,200)
        record=json.loads((self.home/'board-supervisor.json').read_text())
        second=self.command('--url');self.assertEqual(second.returncode,0,second.stdout+second.stderr)
        self.assertEqual(second.stdout,first.stdout)
        self.assertEqual(json.loads((self.home/'board-supervisor.json').read_text())['pid'],record['pid'])
        self.assertFalse(self.browser_log.exists())

    def test_default_opens_the_system_browser_at_the_same_local_url(self):
        result=self.command();self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(json.loads(self.browser_log.read_text().strip()),[f'http://127.0.0.1:{self.port}'])
        self.assertEqual(result.stdout.strip(),f'http://127.0.0.1:{self.port}')

    def test_a_child_worktree_registers_the_main_checkout(self):
        env=self.env
        def git(*args):subprocess.run(['git',*args],cwd=self.repo,env=env,check=True,capture_output=True)
        git('config','user.name','Test');git('config','user.email','test@example.invalid');git('config','core.hooksPath','/dev/null');git('config','commit.gpgsign','false')
        (self.repo/'file').write_text('base');git('add','.');git('commit','-qm','base')
        child=self.base/'child';git('worktree','add','--detach',str(child))
        result=self.command('--url',cwd=child);self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        registry=json.loads((self.home/'boards.json').read_text())
        self.assertEqual(registry,{str(self.repo.resolve()):self.port})

    def test_unknown_option_starts_nothing(self):
        result=self.command('--unknown');self.assertEqual(result.returncode,2)
        self.assertFalse((self.home/'boards.json').exists());self.assertEqual(self.owned,[])

    def test_opening_the_page_does_not_require_github_or_model_configuration(self):
        (self.bin/'gh').write_text('#!/usr/bin/env python3\nraise SystemExit(1)\n')
        result=self.command('--url');self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertFalse((self.home/'models.json').exists())
        with urllib.request.urlopen(result.stdout.strip()) as response:self.assertEqual(response.status,200)


if __name__=='__main__':unittest.main()
