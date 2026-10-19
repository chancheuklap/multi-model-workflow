import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

V4 = Path(__file__).resolve().parents[2]
SCRIPT = V4 / "skills/mmw-mode/scripts/reply-check.py"
BRIEFS = V4 / "skills/dispatch/scripts/briefs.py"


class ReplyCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.mmw = self.root / "mmw"
        self.mmw.mkdir()
        self.runners = self.root / "runners"
        self.runners.mkdir()
        (self.runners / "fake.sh").write_text(
            'echo "$*" >> "$RUNNER_LOG"\n'
            'case "$1" in self) echo "$FAKE_SELF" ;; *) exit 77 ;; esac\n')
        self.log = self.root / "runner.log"
        self.ghlog = self.root / "gh.log"
        tools = self.root / "bin"
        tools.mkdir()
        gh = tools / "gh"
        gh.write_text('#!/bin/sh\necho "$*" >> "$GH_LOG"\nexit 77\n')
        gh.chmod(0o755)
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith(("MMW_", "NMEM_", "ORCA_", "PASEO_", "HERDR_"))}
        self.env.update(MMW_HOME=str(self.mmw), MMW_RUNNERS_DIR=str(self.runners),
                        RUNNER_LOG=str(self.log), FAKE_SELF="owner-session",
                        GH_LOG=str(self.ghlog), PATH=f"{tools}:{self.env['PATH']}")

    def tearDown(self):
        self.assertFalse(self.ghlog.exists(), "a Stop hook must not ask the tracker")

    def run_hook(self, reply, host="claude", cwd=None, **fields):
        payload = {"hook_event_name": "Stop", "stop_hook_active": False,
                   "last_assistant_message": reply, "cwd": str(cwd or self.repo), **fields}
        return subprocess.run([sys.executable, str(SCRIPT), "stop", host],
                              input=json.dumps(payload), capture_output=True, text=True,
                              cwd=cwd or self.repo, env=self.env, timeout=15)

    def glossary(self, text):
        path = self.repo / "docs/contexts/x/CONTEXT.md"
        path.parent.mkdir(parents=True)
        path.write_text(text)
        return path

    def test_a_reply_pointing_back_is_blocked(self):
        phrases = ("上一条", "上面列的", "前面列的", "如上", "见上", "上文", "前文",
                   "the ones above", "as above", "see above", "point 2", "Point 13")
        for host in ("claude", "codex"):
            for phrase in phrases:
                with self.subTest(host=host, phrase=phrase):
                    run = self.run_hook(f"The plan is {phrase}.", host)
                    self.assertEqual(run.returncode, 2, run.stderr)
                    self.assertEqual(run.stdout, "")
                    self.assertIn(phrase, run.stderr)
            for reply, hit in (("内容如上所述", "如上"), ("详情见上文", "见上"),
                               ("请见上图", "见上"), ("沿用前文的计划", "前文"),
                               ("上文解释过", "上文")):
                with self.subTest(host=host, reply=reply):
                    run = self.run_hook(reply, host)
                    self.assertEqual(run.returncode, 2, run.stderr)
                    self.assertIn(hit, run.stderr)
        run = self.run_hook("上一条 and see above and point 2")
        for phrase in ("上一条", "see above", "point 2"):
            self.assertIn(phrase, run.stderr)
        self.assertEqual(list(self.mmw.iterdir()), [])
        self.assertFalse(self.log.exists())

    def test_a_reply_with_an_avoided_wording_is_blocked_naming_the_term(self):
        self.glossary("**feature file**:\nA feature.\n_Avoid_: 功能文件, 特性文档\n"
                      "_Home_: elsewhere\n\n**`verify-<product>`**:\n"
                      "_Avoid_: 产品验证技能\n")
        nested = self.repo / "src"
        nested.mkdir()
        for host in ("claude", "codex"):
            run = self.run_hook("功能文件、特性文档和产品验证技能都已完成。", host, cwd=nested)
            self.assertEqual(run.returncode, 2, run.stderr)
            self.assertEqual(run.stdout, "")
            for fact in ("功能文件", "特性文档", "feature file", "产品验证技能", "verify-<product>"):
                self.assertIn(fact, run.stderr)

    def test_a_clean_reply_ends_the_turn(self):
        self.glossary("**feature file**:\n_Avoid_: 功能文件\n")
        for host in ("claude", "codex"):
            for reply in ("", "The feature file describes the saved plan.", "这份计划包含全部工作。", "checkpoint 2",
                          "例如上海", "比如上海", "以上文件已改", "以上文件已更新",
                          "之前文档", "之前文件里没有", "意见上一致", "他的意见上没问题"):
                with self.subTest(host=host, reply=reply):
                    run = self.run_hook(reply, host)
                    self.assertEqual((run.returncode, run.stdout, run.stderr), (0, "", ""))

    def test_an_english_avoided_wording_is_not_matched(self):
        self.glossary("**orchestrator**:\n_Avoid_: main agent (for this, not another use), "
                      "host (中文解释), 编排者\n")
        run = self.run_hook("The main agent and host work together. 中文解释 is a note.")
        self.assertEqual((run.returncode, run.stdout, run.stderr), (0, "", ""))

    def test_a_continuation_of_a_block_is_never_blocked(self):
        self.glossary("**feature file**:\n_Avoid_: 功能文件\n")
        for host in ("claude", "codex"):
            run = self.run_hook("上一条功能文件", host, stop_hook_active=True)
            self.assertEqual((run.returncode, run.stdout, run.stderr), (0, "", ""))
        self.assertFalse(self.log.exists())

    def test_a_ticket_worktree_session_is_never_checked(self):
        ticket = self.root / "issue-1179"
        ticket.mkdir()
        for host in ("claude", "codex"):
            run = self.run_hook("see above", host, cwd=ticket)
            self.assertEqual((run.returncode, run.stdout, run.stderr), (0, "", ""))
        self.assertFalse(self.log.exists())
        other = self.root / "issue-not-a-ticket"
        other.mkdir()
        self.assertEqual(self.run_hook("see above", cwd=other).returncode, 2)

    def open_brief(self):
        args = [sys.executable, str(BRIEFS)]
        run = subprocess.run(args + ["new", "--repo", "o/r", "--role", "researcher",
                                    "--count", "1", "--runner", "fake", "--session", "parent"],
                             env=self.env, capture_output=True, text=True, check=True)
        batch = run.stdout.strip()
        subprocess.run(args + ["started", "--repo", "o/r", "--brief", f"{batch}/1",
                               "--runner", "fake", "--session", "child", "--host", "codex",
                               "--model", "test", "--effort", "high"], env=self.env,
                       capture_output=True, text=True, check=True)
        return batch

    def test_an_open_brief_session_is_never_checked(self):
        self.open_brief()
        self.env["FAKE_SELF"] = "child"
        before = {p: p.read_bytes() for p in self.mmw.rglob("*") if p.is_file()}
        for host in ("claude", "codex"):
            run = self.run_hook("see above", host)
            self.assertEqual((run.returncode, run.stdout, run.stderr), (0, "", ""))
        after = {p: p.read_bytes() for p in self.mmw.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(set(self.log.read_text().splitlines()), {"self"})
        self.env["FAKE_SELF"] = "someone-else"
        self.assertEqual(self.run_hook("see above").returncode, 2)

    def test_an_orchestrator_session_is_never_checked(self):
        state = self.mmw / "state/o__r"
        state.mkdir(parents=True)
        watches = state / "watches.json"
        watches.write_text(json.dumps({"spec:76": {"spec": 76, "runner": "fake", "session": "parent"}}))
        self.env["FAKE_SELF"] = "parent"
        for host in ("claude", "codex"):
            run = self.run_hook("see above", host)
            self.assertEqual((run.returncode, run.stdout, run.stderr), (0, "", ""))
        self.assertEqual(set(self.log.read_text().splitlines()), {"self"})
        self.assertEqual(sorted(p.name for p in state.iterdir()), ["watches.json"])
        self.env["FAKE_SELF"] = "someone-else"
        self.assertEqual(self.run_hook("see above").returncode, 2)
        watches.write_text("{}")
        self.env["FAKE_SELF"] = "parent"
        self.assertEqual(self.run_hook("see above").returncode, 2)

    def test_an_error_of_its_own_exits_1_and_never_blocks(self):
        glossary = self.glossary("**feature file**:\n_Avoid_: 功能文件\n")
        glossary.write_bytes(b"\xff")
        for host in ("claude", "codex"):
            run = self.run_hook("see above", host)
            self.assertEqual(run.returncode, 1)
            self.assertEqual(run.stdout, "")
            self.assertIn(str(glossary), run.stderr)
            self.assertIn("reply-check", run.stderr)
        for payload in ("{", "[]", '{"last_assistant_message": 123}'):
            run = subprocess.run([sys.executable, str(SCRIPT), "stop", "codex"], input=payload,
                                 cwd=self.repo, env=self.env, text=True, capture_output=True)
            self.assertEqual(run.returncode, 1)
            self.assertIn("reply-check", run.stderr)


if __name__ == "__main__":
    unittest.main()
