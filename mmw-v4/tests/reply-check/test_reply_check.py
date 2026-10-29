import hashlib
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


class HookCase(unittest.TestCase):
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

    def run_artifact(self, tool_input, cwd=None):
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Artifact",
                   "tool_input": tool_input, "cwd": str(cwd or self.repo)}
        return subprocess.run([sys.executable, str(SCRIPT), "artifact", "claude"],
                              input=json.dumps(payload), capture_output=True, text=True,
                              cwd=cwd or self.repo, env=self.env, timeout=15)

    def checklist_text(self, run):
        name = run.stderr.split(" against ", 1)[1].split(", rewrite", 1)[0]
        return Path(name).read_text()

    def glossary(self, text):
        path = self.repo / "docs/contexts/x/CONTEXT.md"
        path.parent.mkdir(parents=True)
        path.write_text(text)
        (self.repo / "CONTEXT-MAP.md").write_text("[X](docs/contexts/x/CONTEXT.md)\n")
        return path


class TestGlossaryFollowsContextMap(HookCase):
    def test_only_linked_glossaries_appear_in_link_order(self):
        for name in ("a", "b", "old"):
            path = self.repo / name / "CONTEXT.md"
            path.parent.mkdir()
            path.write_text(f"**local {name} name**:\n")
        (self.repo / "CONTEXT.md").write_text("**unlisted root name**:\n")
        (self.repo / "CONTEXT-MAP.md").write_text(
            "[B](b/CONTEXT.md)\n[A](./a/CONTEXT.md)\n[Other](notes.md)\n")
        nested = self.repo / "src"
        nested.mkdir()
        run = self.run_hook("Done.", cwd=nested)
        self.assertEqual(run.returncode, 2, run.stderr)
        text = self.checklist_text(run)
        self.assertLess(text.index("local b name"), text.index("local a name"))
        self.assertNotIn("local old name", text)
        self.assertNotIn("unlisted root name", text)


class TestSameGlossaryListedOnce(HookCase):
    def test_working_copy_of_mmw_glossary_keeps_only_mmw_entry(self):
        source = V4.parent / "docs/contexts/toolbox/CONTEXT.md"
        local = self.repo / "CONTEXT.md"
        local.write_text(source.read_text())
        run = self.run_hook("Done.")
        self.assertEqual(run.returncode, 2, run.stderr)
        text = self.checklist_text(run)
        self.assertEqual(text.splitlines().count("host hook"), 1)
        self.assertIn(str(source), text)
        self.assertNotIn(str(local), text)


class TestRootGlossaryWithoutMap(HookCase):
    def test_root_glossary_or_no_additional_names(self):
        run = self.run_hook("Done.")
        self.assertEqual(run.returncode, 2, run.stderr)
        mmw_only = self.checklist_text(run)
        self.assertNotIn(str(self.repo), mmw_only)
        root = self.repo / "CONTEXT.md"
        root.write_text("**root local name**:\n_Avoid_: local alias\n")
        run = self.run_hook("Done.")
        self.assertEqual(run.returncode, 2, run.stderr)
        text = self.checklist_text(run)
        self.assertIn(str(root), text)
        self.assertIn("root local name\n_Avoid_: local alias", text)
        root.unlink()
        self.assertEqual(self.checklist_text(self.run_hook("Done.")), mmw_only)


class TestBlockIsOneLine(HookCase):
    def test_blocks_point_to_reusable_checklist_files(self):
        (self.repo / "CONTEXT.md").write_text("**registered local name**:\n_Avoid_: alias\n")
        page = self.repo / "page.html"
        page.write_text("<html>page</html>")
        pattern = (V4 / "skills/principle-anchor-every-reference/SKILL.md").read_text().split(
            "**Pattern:**\n", 1)[1].strip().split("\n\n", 1)[0]
        for host in ("claude", "codex"):
            run = self.run_hook("Done.", host)
            self.assertEqual(run.returncode, 2, run.stderr)
            self.assertEqual(run.stdout, "")
            self.assertEqual(len(run.stderr.splitlines()), 1, run.stderr)
            name = run.stderr.split(" against ", 1)[1].split(", rewrite", 1)[0]
            checklist = Path(name)
            text = checklist.read_text()
            self.assertEqual(checklist.parent, self.mmw / "state/reply-check")
            self.assertEqual(checklist.name,
                             f"checklist-{hashlib.sha256(text.encode()).hexdigest()[:12]}.md")
            self.assertIn("**Pattern:**\n" + pattern, text)
            self.assertIn("registered local name", text)
            self.assertIn("_Avoid_: alias", text)
            self.assertEqual(run.stderr, f"MMW reply check: reread what you wrote for the owner "
                             f"against {checklist}, rewrite what breaks it, then finish again.\n")
            before = checklist.stat().st_mtime_ns
            self.assertEqual(self.run_hook("Done.", host).stderr, run.stderr)
            self.assertEqual(checklist.stat().st_mtime_ns, before)
        run = self.run_artifact({"file_path": str(page)})
        self.assertEqual(run.returncode, 2, run.stderr)
        self.assertEqual(len(run.stderr.splitlines()), 1, run.stderr)
        name = run.stderr.split(" against ", 1)[1].split(", rewrite", 1)[0]
        self.assertEqual(run.stderr, f"MMW reply check: reread {page} against {name}, "
                         "rewrite what breaks it, then publish again.\n")
        self.assertIn("registered local name", Path(name).read_text())
        self.assertIn("principle-everything-at-hand", Path(name).read_text())
        self.assertEqual(self.run_artifact({"file_path": str(page)}).returncode, 0)


class TestStopBlocksOnceWithChecklist(HookCase):
    def test_ordinary_reply_blocks_then_continuation_passes(self):
        principle = V4 / "skills/principle-anchor-every-reference/SKILL.md"
        pattern = principle.read_text().split("**Pattern:**\n", 1)[1].strip().split("\n\n", 1)[0]
        for host in ("claude", "codex"):
            for reply in ("The plan is complete.", "", "计划已经完成。"):
                with self.subTest(host=host, reply=reply):
                    run = self.run_hook(reply, host)
                    self.assertEqual(run.returncode, 2, run.stderr)
                    self.assertEqual(run.stdout, "")
                    self.assertEqual(len(run.stderr.splitlines()), 1)
                    text = self.checklist_text(run)
                    self.assertIn(pattern, text)
                    self.assertTrue(text.rstrip().endswith(
                        "A name not registered above is written as a plain description, "
                        "or proposed to the owner before it is used."))
                    self.assertEqual(self.run_hook(reply, host, stop_hook_active=True).returncode, 0)
        self.assertTrue(list((self.mmw / "state/reply-check").glob("checklist-*.md")))
        self.assertFalse(self.log.exists())


class TestChecklistListsRegisteredNames(HookCase):
    def test_names_and_avoid_lines_keep_language_and_discovery_order(self):
        local = self.glossary("**order plan**:\n_Avoid_: main agent (not another use), 规格\n"
                              "\n**订单**:\n_Avoid_: order, 订货\n\n**plain name**:\nDefinition.\n")
        later = self.repo / "docs/contexts/z/CONTEXT.md"
        later.parent.mkdir(parents=True)
        later.write_text("**later local name**:\n_Avoid_: later alias\n")
        (self.repo / "CONTEXT-MAP.md").write_text(
            "[X](docs/contexts/x/CONTEXT.md)\n[Z](docs/contexts/z/CONTEXT.md)\n")
        nested = self.repo / "src"
        nested.mkdir()
        for host in ("claude", "codex"):
            run = self.run_hook("A completely ordinary reply.", host, cwd=nested)
            self.assertEqual(run.returncode, 2, run.stderr)
            text = self.checklist_text(run)
            last = -1
            for path in [V4.parent / "docs/contexts" / name / "CONTEXT.md"
                         for name in ("toolbox", "tickets", "ticket-run", "night",
                                      "ui-acceptance", "task-board", "release")] + [local, later]:
                self.assertIn(str(path), text)
                at = text.index(str(path))
                self.assertGreater(at, last)
                last = at
                block = text[at + len(str(path)) + 1:].split("\n\n", 1)[0]
                for line in path.read_text().splitlines():
                    if line.startswith("**"):
                        self.assertIn(line.split("**", 2)[1], block)
                    if line.startswith("_Avoid_:"):
                        self.assertIn(line, block)
            self.assertIn("_Avoid_: main agent (not another use), 规格", text)
            self.assertIn("_Avoid_: order, 订货", text)
            self.assertIn("plain name", text)

    def test_mmw_repository_lists_each_glossary_once(self):
        for host in ("claude", "codex"):
            run = self.run_hook("Done.", host, cwd=V4)
            self.assertEqual(run.returncode, 2, run.stderr)
            text = self.checklist_text(run)
            for path in sorted((V4.parent / "docs/contexts").glob("*/CONTEXT.md")):
                self.assertEqual(text.splitlines().count(str(path)), 1, str(path))

    def test_outside_repository_reads_only_cwd_beside_mmw_glossaries(self):
        outside = self.root / "outside"
        nested = outside / "other-project"
        nested.mkdir(parents=True)
        (outside / "CONTEXT.md").write_text("**local term**:\n_Avoid_: 本地用词\n")
        (nested / "CONTEXT.md").write_text("**unrelated term**:\n_Avoid_: 无关用词\n")
        run = self.run_hook("Done.", cwd=outside)
        self.assertEqual(run.returncode, 2, run.stderr)
        text = self.checklist_text(run)
        self.assertIn("local term", text)
        self.assertIn("host hook", text)
        self.assertNotIn("unrelated term", text)


class TestStopExemptionsStillPass(HookCase):
    def test_null_reply_passes(self):
        for host in ("claude", "codex"):
            run = self.run_hook(None, host)
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
        run = self.run_artifact({"file_path": "missing.html"}, cwd=ticket)
        self.assertEqual((run.returncode, run.stdout, run.stderr), (0, "", ""))
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
        run = self.run_artifact({"file_path": "missing.html"})
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
        run = self.run_artifact({"file_path": "missing.html"})
        self.assertEqual((run.returncode, run.stdout, run.stderr), (0, "", ""))
        self.assertEqual(sorted(p.name for p in state.iterdir()), ["watches.json"])
        self.env["FAKE_SELF"] = "someone-else"
        self.assertEqual(self.run_hook("see above").returncode, 2)
        watches.write_text("{}")
        self.env["FAKE_SELF"] = "parent"
        self.assertEqual(self.run_hook("see above").returncode, 2)



class TestArtifactBlocksOncePerContent(HookCase):
    def test_publish_checks_each_content_once_and_shows_page_rules(self):
        page = self.repo / "page.html"
        page.write_text("<html>First page</html>")
        self.glossary("**页面**:\n_Avoid_: page (for this concept)\n")
        run = self.run_artifact({"file_path": str(page)})
        self.assertEqual(run.returncode, 2, run.stderr)
        self.assertEqual(run.stdout, "")
        self.assertIn(str(page), run.stderr.splitlines()[0])
        self.assertIn("publish again", run.stderr.splitlines()[0])
        text = self.checklist_text(run)
        last = -1
        for name in ("principle-anchor-every-reference", "principle-everything-at-hand"):
            path = V4 / "skills" / name / "SKILL.md"
            pattern = path.read_text().split("**Pattern:**\n", 1)[1].strip().split("\n\n", 1)[0]
            self.assertIn(pattern, text)
            self.assertGreater(text.index(pattern), last)
            last = text.index(pattern)
        self.assertIn("页面", text)
        self.assertIn("_Avoid_: page (for this concept)", text)
        self.assertGreater(text.index("页面"), last)
        again = self.run_artifact({"file_path": str(page)})
        self.assertEqual((again.returncode, again.stdout, again.stderr), (0, "", ""))
        page.write_text("<html>Changed page</html>")
        changed = self.run_artifact({"file_path": "page.html"})
        self.assertEqual(changed.returncode, 2, changed.stderr)
        self.assertEqual(self.run_artifact({"file_path": str(page)}).returncode, 0)
        files = [p for p in self.mmw.rglob("*") if p.is_file()]
        self.assertEqual(len([p for p in files if not p.name.startswith("checklist-")]), 2)
        self.assertEqual(len([p for p in files if p.name.startswith("checklist-")]), 1)
        self.assertTrue(all(p.is_relative_to(self.mmw / "state") for p in files))
        self.assertFalse(self.log.exists())


class TestArtifactWithoutPagePasses(HookCase):
    def test_non_publish_actions_and_assets_do_not_block_or_write(self):
        for tool_input in ({}, {"action": "list"}, {"action": "open"},
                           {"action": "quickstart", "intent": "other", "design_systems": False},
                           {"file_path": "missing-image.png", "asset": True}):
            with self.subTest(tool_input=tool_input):
                run = self.run_artifact(tool_input)
                self.assertEqual((run.returncode, run.stdout, run.stderr), (0, "", ""))
        self.assertEqual(list(self.mmw.iterdir()), [])


class TestErrorsDoNotBlock(HookCase):
    def test_non_object_payloads_exit_one_on_both_entries(self):
        for entry, host in (("stop", "claude"), ("stop", "codex"), ("artifact", "claude")):
            for payload in ("[]", "null", "123", "{"):
                with self.subTest(entry=entry, host=host, payload=payload):
                    run = subprocess.run([sys.executable, str(SCRIPT), entry, host], input=payload,
                                         cwd=self.repo, env=self.env, text=True, capture_output=True)
                    self.assertEqual(run.returncode, 1, run.stderr)
                    self.assertEqual(run.stdout, "")
                    self.assertIn(f"reply-check: could not check {entry}", run.stderr)

    def test_unreadable_glossary_and_missing_page_do_not_block_or_mark_content(self):
        glossary = self.glossary("**name**:\n_Avoid_: 别名\n")
        glossary.write_bytes(b"\xff")
        page = self.repo / "page.html"
        page.write_text("<html>page</html>")
        for run in (self.run_hook("Done.", "claude"), self.run_hook("Done.", "codex"),
                    self.run_artifact({"file_path": str(page)}),
                    self.run_artifact({"file_path": "missing.html"})):
            self.assertEqual(run.returncode, 1, run.stderr)
            self.assertIn("reply-check: could not check", run.stderr)
        self.assertEqual(list(self.mmw.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
