import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "mmw-v2" / "migrations" / "remove-verifier.py"


class MigrationCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        self.bin = Path(self.tmp.name) / "bin"
        self.repo = Path(self.tmp.name) / "repo"
        self.home.mkdir()
        self.bin.mkdir()
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "remote", "add", "origin",
                        "https://github.com/acme/widget.git"], check=True)
        (self.home / "boards.json").write_text(json.dumps({str(self.repo): 47100}))
        (self.home / "models.json").write_text(json.dumps({"version": 1, "runner": "orca", "rows": {
            "junior-worker": {}, "senior-worker": {}, "reviewer": {}, "verifier": {}, "advisor": {}}}))
        self.state = Path(self.tmp.name) / "tracker.json"
        body = lambda event, line: f'{line}\n\n<!-- mmw {{"v":1,"event":"{event}"}} -->\n'
        self.state.write_text(json.dumps({"comments": [
            {"id": 10, "issue_url": "https://api.github.com/repos/acme/widget/issues/7",
             "body": body("verifier.started", "started")},
            {"id": 11, "issue_url": "https://api.github.com/repos/acme/widget/issues/7",
             "body": body("verifier.passed", "passed")},
            {"id": 12, "issue_url": "https://api.github.com/repos/acme/widget/issues/8",
             "body": body("ticket.checked", "keep")},
        ], "issues": [{"number": 7}], "edits": []}))
        fake = self.bin / "gh"
        fake.write_text("""#!/usr/bin/env python3
import json, os, sys
p = os.environ['FAKE_TRACKER']; data = json.load(open(p))
a = sys.argv[1:]
if '--method' in a:
    cid = int(next(x for x in a if '/issues/comments/' in x).rsplit('/',1)[1])
    body = next(x[5:] for x in a if x.startswith('body='))
    for c in data['comments']:
        if c['id'] == cid: c['body'] = body
    data['edits'].append(cid); json.dump(data, open(p,'w')); print('{}')
elif any('issues/comments?' in x for x in a):
    print(json.dumps(data['comments'] if any('repos/acme/widget/' in x for x in a) else []))
elif any('issues?state=open' in x for x in a):
    print(json.dumps(data['issues'] if any('repos/acme/widget/' in x for x in a) else []))
else: print('unknown request', file=sys.stderr); sys.exit(2)
""")
        fake.chmod(0o755)

    def tearDown(self):
        self.tmp.cleanup()

    def invoke(self, *args):
        env = dict(os.environ, MMW_HOME=str(self.home), FAKE_TRACKER=str(self.state),
                   PATH=f"{self.bin}:{os.environ['PATH']}")
        return subprocess.run(["python3", str(SCRIPT), *args], cwd=self.repo,
                              env=env, text=True, capture_output=True)

    def test_migrates_comments_and_model_row_then_is_idempotent(self):
        run = self.invoke()
        self.assertEqual(run.returncode, 0, run.stderr)
        data = json.loads(self.state.read_text())
        self.assertEqual(data["edits"], [10, 11])
        self.assertEqual(data["comments"][0]["body"], "started\n")
        config = json.loads((self.home / "models.json").read_text())
        self.assertNotIn("verifier", config["rows"])
        self.assertEqual(config["version"], 2)
        again = self.invoke()
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn("acme/widget: 0 comment(s)", again.stdout)

    def test_dry_run_only_prints_comment_count(self):
        before = self.state.read_text()
        run = self.invoke("--dry-run")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("acme/widget: 2 comment(s)", run.stdout)
        self.assertEqual(self.state.read_text(), before)
        self.assertIn("verifier", json.loads((self.home / "models.json").read_text())["rows"])

    def test_open_watch_refuses_before_any_change(self):
        state_dir = self.home / "state" / "acme__widget"
        state_dir.mkdir(parents=True)
        (state_dir / "watches.json").write_text('{"spec:1": {}}')
        before = self.state.read_text()
        run = self.invoke()
        self.assertEqual(run.returncode, 2)
        self.assertIn("open watch", run.stderr)
        self.assertEqual(self.state.read_text(), before)
        self.assertIn("verifier", json.loads((self.home / "models.json").read_text())["rows"])

    def test_unfinished_started_event_refuses_before_any_change(self):
        data = json.loads(self.state.read_text())
        data["comments"] = data["comments"][:1]
        self.state.write_text(json.dumps(data))
        before = self.state.read_text()
        run = self.invoke()
        self.assertEqual(run.returncode, 2)
        self.assertIn("has no result", run.stderr)
        self.assertEqual(self.state.read_text(), before)
        self.assertIn("verifier", json.loads((self.home / "models.json").read_text())["rows"])

    def test_held_models_lock_refuses_without_a_traceback_or_changes(self):
        holder = subprocess.Popen([
            "python3", "-c",
            "import fcntl,json,sys,time; "
            "f=open(sys.argv[1],'w'); fcntl.flock(f,fcntl.LOCK_EX); "
            "f.write(json.dumps({'pid':__import__('os').getpid(),'identity':'test',"
            "'since':'now','purpose':'test'})); f.flush(); print('ready',flush=True); time.sleep(30)",
            str(self.home / "models.lock"),
        ], text=True, stdout=subprocess.PIPE)
        try:
            self.assertEqual(holder.stdout.readline().strip(), "ready")
            tracker_before = self.state.read_text()
            models_before = (self.home / "models.json").read_text()
            run = self.invoke()
            self.assertEqual(run.returncode, 2)
            self.assertNotIn("Traceback", run.stderr)
            self.assertIn("Re-run after that process releases the lock", run.stderr)
            self.assertEqual(self.state.read_text(), tracker_before)
            self.assertEqual((self.home / "models.json").read_text(), models_before)
        finally:
            holder.terminate()
            holder.wait(timeout=5)
            holder.stdout.close()


if __name__ == "__main__":
    unittest.main()
