"""The tool guard: who it governs, what it stops, and what it says.

Every test drives `tool-guard.py` the way a host does — one event as JSON on stdin, one
answer as JSON on stdout. `pretool` reads the working directory's basename;
the question gate reads the same session directory. Tests name a temporary directory
`issue-<n>`. An inherited `PASEO_AGENT_CWD` is cleared unless a test names it.
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

SKILLS = Path(__file__).resolve().parents[2] / "skills"
DISPATCH_SCRIPTS = SKILLS / "dispatch" / "scripts"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(f"mmw_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hk = load(DISPATCH_SCRIPTS / "tool-guard.py", "tool_guard")

TICKET = 64
CLOSE = f"gh issue close {TICKET} --reason completed"

# One event per host, in the shape that host actually sends.
EVENTS = {
    "claude": {"hook_event_name": "PreToolUse", "cwd": "/w", "tool_name": "Bash",
               "tool_input": {"command": CLOSE}},
    "codex": {"hook_event_name": "PreToolUse", "cwd": "/w", "tool_name": "Bash",
              "tool_input": {"command": CLOSE}},
}


@contextmanager
def named_cwd(basename: str):
    """A temporary session directory for a host-payload test."""
    with tempfile.TemporaryDirectory() as root:
        path = os.path.join(root, basename)
        os.mkdir(path)
        previous = os.getcwd()
        os.chdir(path)
        try:
            yield path
        finally:
            os.chdir(previous)


def call(host: str, event: dict, env: dict | None = None,
         *, cwd_basename: str | None = None) -> tuple[int, dict | None]:
    """Run the gate as its host would, and read back the answer it printed.

    The session directory is the temp cwd this helper just created. A parent
    `PASEO_AGENT_CWD` (the worktree of the agent running the suite) must not
    leak into `governed_ticket`, or a dispatched session governs a test that
    names no ticket; tests that want a different session directory pass
    `PASEO_AGENT_CWD` in `env`.
    """
    if cwd_basename is None:
        cwd_basename = f"issue-{TICKET}"
    out = io.StringIO()
    with named_cwd(cwd_basename) as path:
        merged = dict(os.environ)
        if env:
            merged.update(env)
        if not env or "PASEO_AGENT_CWD" not in env:
            merged["PASEO_AGENT_CWD"] = path
        if not env or "MMW_HOME" not in env:
            merged["MMW_HOME"] = str(Path(path) / ".mmw")
        with mock.patch.dict(os.environ, merged, clear=True), \
             mock.patch.object(hk.sys, "stdin", io.StringIO(json.dumps(event))), \
             redirect_stdout(out), redirect_stderr(io.StringIO()):
            code = hk.main(["pretool", host])
    printed = out.getvalue().strip()
    return code, json.loads(printed) if printed else None


def reason_of(answer: dict) -> str:
    """The one sentence the model reads."""
    return answer["hookSpecificOutput"]["permissionDecisionReason"]


def with_command(host: str, command: str) -> dict:
    """The host's event, carrying a different command."""
    event = json.loads(json.dumps(EVENTS[host]))
    event["tool_input"]["command"] = command
    return event


# ------------------------------------------------------------------------ cwd names the ticket


class TestKillIsNotGuarded(unittest.TestCase):
    def test_process_commands_get_no_refusal(self):
        for host in EVENTS:
            with named_cwd(f"issue-{TICKET}") as cwd:
                env = {**os.environ, "MMW_HOME": str(Path(cwd) / ".mmw"),
                       "PASEO_AGENT_CWD": cwd}
                for command in ("kill -9 1", "pkill -f x", "killall x", "killall5",
                                "echo 123 | xargs kill -9"):
                    with self.subTest(host=host, command=command):
                        run = subprocess.run(
                            [sys.executable, str(DISPATCH_SCRIPTS / "tool-guard.py"),
                             "pretool", host], input=json.dumps(with_command(host, command)),
                            env=env, capture_output=True, text=True)
                        self.assertEqual(run.returncode, 0, run.stderr)
                        self.assertEqual(run.stdout, "")


class TestPullRequestCreation(unittest.TestCase):
    def test_guard_refuses_gh_pr_create(self):
        for host in EVENTS:
            for cwd in ("night-work", f"issue-{TICKET}"):
                for command in (
                    "gh pr create --base main --head night --title Changes --body-file body.md",
                    "echo hi # don't\ngh pr create\n# it's done",
                    "cat > body.md <<'EOF'\ndon't\nEOF\ngh pr create\n",
                    "env FOO=1 gh pr create",
                    "gh -R o/r pr create",
                    "gh --repo o/r pr create",
                    "gh --repo=o/r pr create",
                    "gh -Ro/r pr create",
                ):
                    with self.subTest(host=host, cwd=cwd, command=command):
                        code, answer = call(host, with_command(host, command), cwd_basename=cwd)
                        self.assertEqual(code, 0)
                        self.assertIsNotNone(answer)
                        self.assertEqual(answer["hookSpecificOutput"]["permissionDecision"], "deny")
                        self.assertIn("dispatch.sh pr --base", reason_of(answer))
            for command in (
                "cat > body.md <<'EOF'\nDo not run gh pr create\ngh pr create\nEOF",
                "echo 'gh pr create'",
                "gh pr view 7",
                "bash /skills/dispatch/scripts/dispatch.sh pr --base main --head night --title Changes --body-file body.md",
            ):
                with self.subTest(host=host, command=command):
                    _, answer = call(host, with_command(host, command), cwd_basename="night-work")
                    self.assertIsNone(answer)


class TestCwdNamesTheTicket(unittest.TestCase):
    """`pretool` reads a directory basename, never a ticket number handed to it.

    Two directories can name the ticket and either is enough: the process's own, and
    the one Paseo opened the session in.
    """

    def test_pretool_guards_the_ticket_named_by_cwd(self):
        event = with_command("claude", "gh issue close 12")
        code, answer = call("claude", event, env={}, cwd_basename="issue-12")
        self.assertEqual(code, 0)
        self.assertIsNotNone(answer)

    def test_pretool_ignores_a_cwd_that_is_not_a_ticket(self):
        event = with_command("claude", "gh issue close 12")
        self.assertEqual(
            call("claude", event, {"MMW_TICKET": "12"}, cwd_basename="workspace"),
            (0, None),
        )

    def test_a_hook_run_from_elsewhere_is_governed_by_the_session_directory(self):
        """The process directory names no ticket; Paseo says where the session was
        opened, and that is what governs."""
        code, answer = call("claude", EVENTS["claude"],
                            env={"PASEO_AGENT_CWD": f"/w/issue-{TICKET}"},
                            cwd_basename="elsewhere")
        self.assertEqual(code, 0)
        self.assertEqual(answer["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_neither_directory_naming_a_ticket_governs_nothing(self):
        self.assertEqual(
            call("claude", EVENTS["claude"],
                 env={"PASEO_AGENT_CWD": "/w/multi-model-workflow"},
                 cwd_basename="elsewhere"),
            (0, None),
        )


class TestSelfScope(unittest.TestCase):
    """Ticket closeout uses the process and session directory names, without a runner."""

    def test_a_marker_that_is_not_a_ticket_number_is_no_marker(self):
        for name in ("issue", "issue-", "issue-64x", "64", "Issue-64"):
            with self.subTest(cwd=name):
                self.assertEqual(
                    call("claude", EVENTS["claude"], cwd_basename=name),
                    (0, None),
                )

    def test_the_gate_runs_nothing_and_opens_nothing(self):
        """The basename is the ticket number, so pretool never has to go and find out."""
        with mock.patch("subprocess.run") as run, mock.patch("subprocess.Popen") as popen, \
             mock.patch("builtins.open") as opened:
            code, answer = call("claude", EVENTS["claude"])
        self.assertEqual(code, 0)
        self.assertIsNotNone(answer)
        run.assert_not_called()
        popen.assert_not_called()
        opened.assert_not_called()

# ------------------------------------------------------------------------ AC2


class TestWhatItStops(unittest.TestCase):
    """The ticket-closeout gate refuses commands that finish this ticket by hand."""

    STOPPED = [
        f"gh issue close {TICKET}",
        f"gh issue close {TICKET} --reason completed",
        f"gh issue close {TICKET} --reason not_planned",
        f"gh issue edit {TICKET} --add-label ready-for-human",
        f"gh issue edit {TICKET} --remove-label ready-for-agent",
        f"gh issue edit {TICKET} --add-label 'ready-for-human' --remove-label ready-for-agent",
        f"gh issue edit {TICKET} --add-label needs-triage --remove-label ready-for-agent",
        f"gh issue edit {TICKET} --add-label needs-triage",
        f"cd /repo && gh issue close {TICKET}",
        f"MMW_TICKET={TICKET} gh issue close {TICKET}",
        f"pytest -q; gh issue close {TICKET}",
    ]
    PASSED = [
        "ls",
        "pytest -q",
        f"python3 {SKILLS}/register-problem/scripts/register.py add problem.md",
        f"gh issue view {TICKET} --json comments",
        f"gh issue comment {TICKET} --body-file draft.md",
        f"gh issue edit {TICKET} --add-assignee @me",
        "gh issue create --parent 76 --label needs-triage --title 'AC3 needs a call'",
        "gh issue close 640",
        "gh issue close 9 --reason completed",
        "gh pr close 12",
        # A worker writing its closing comment says in it that it did not close the
        # ticket by hand. 2026-08-30: the first worker to meet this gate unconstrained
        # was refused for writing exactly that, and correctly called it a false positive.
        f"cat > /tmp/closeout-{TICKET}.md <<'EOF'\nALL MET\n\n本票没有直接调用 gh issue close "
        f"{TICKET}，走的是 --closeout。\nEOF",
        f"echo 'do not run gh issue close {TICKET} by hand' >> notes.md",
        f"git commit -m 'close #{TICKET} through gh issue close is refused by the gate'",
    ]

    def test_the_two_that_finish_the_ticket_are_recognised(self):
        for command in self.STOPPED:
            with self.subTest(command=command):
                self.assertTrue(hk.leaves_the_agent_lane(command, TICKET))
                _, answer = call("claude", with_command("claude", command))
                self.assertIsNotNone(answer, command)

    def test_everything_else_goes_through(self):
        for command in self.PASSED:
            with self.subTest(command=command):
                self.assertEqual(call("claude", with_command("claude", command)), (0, None))

    def test_another_ticket_is_not_this_gate_s_business(self):
        """A worker opens sub-issues under the spec; those are not the ticket it holds."""
        self.assertFalse(hk.leaves_the_agent_lane("gh issue close 58", TICKET))
        self.assertFalse(hk.leaves_the_agent_lane(f"gh issue close {TICKET}0", TICKET))

    def test_guard_edit_last_is_refused(self):
        for host in EVENTS:
            for directory in (f"issue-{TICKET}", "night-76", "workspace"):
                for command in (
                    "gh issue comment 64 --edit-last --body correction",
                    "gh pr comment 64 --body-file report.md --edit-last",
                    "gh issue comment 64 --edit-last=true --body correction",
                    "gh -R o/r issue comment 64 --edit-last",
                    "gh pr --repo=o/r comment 64 --edit-last",
                    "echo ok; env FOO=1 gh pr comment 64 --edit-last",
                ):
                    with self.subTest(host=host, directory=directory, command=command):
                        code, answer = call(host, with_command(host, command), cwd_basename=directory)
                        self.assertEqual(code, 0)
                        self.assertIsNotNone(answer)
                        self.assertIn("gh api", reason_of(answer))
                        self.assertIn("comment id", reason_of(answer))
            for command in (
                "gh issue comment 64 --body '--edit-last'",
                "gh pr comment 64 --body='the --edit-last flag is forbidden'",
                "gh api repos/o/r/issues/comments/123 -X PATCH -f body=correction",
                "echo 'gh issue comment 64 --edit-last'",
                "cat <<EOF\ngh pr comment 64 --edit-last\nEOF",
            ):
                self.assertEqual(call(host, with_command(host, command)), (0, None))


# ------------------------------------------------------------------------ AC3


class TestRefusalShape(unittest.TestCase):
    """Both hosts read one refusal shape."""

    def test_claude_and_codex(self):
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                code, answer = call(host, EVENTS[host])
                inner = answer["hookSpecificOutput"]
                self.assertEqual(inner["hookEventName"], "PreToolUse")
                self.assertEqual(inner["permissionDecision"], "deny")
                self.assertEqual(code, 0)

    def test_the_answer_is_on_stdout_and_the_exit_code_stays_zero(self):
        """Both hosts honour a deny on stdout whatever the exit code is;
        exiting non-zero as well would only make a failure look like a refusal."""
        for host in hk.HOSTS:
            with self.subTest(host=host):
                code, answer = call(host, EVENTS[host])
                self.assertEqual(code, 0)
                self.assertIsNotNone(answer)


# ------------------------------------------------------------------------ AC4


class TestInputShapes(unittest.TestCase):
    """One event shape, one decision, one sentence."""

    def test_every_host_reads_the_command_out_of_its_own_event(self):
        for host, event in EVENTS.items():
            with self.subTest(host=host):
                self.assertEqual(hk.command_of(event), CLOSE)

    def test_an_event_with_no_command_decides_nothing(self):
        for event in ({}, {"tool_input": {}}, {"command": ""}, {"tool_input": "ls"}):
            with self.subTest(event=event):
                self.assertIsNone(hk.command_of(event))

    def test_the_same_command_is_refused_on_both_with_the_same_words(self):
        reasons = {host: reason_of(call(host, EVENTS[host])[1]) for host in hk.HOSTS}
        self.assertEqual(len(set(reasons.values())), 1, reasons)

    def test_the_same_harmless_command_goes_through_on_both(self):
        for host in hk.HOSTS:
            with self.subTest(host=host):
                event = with_command(host, f"gh issue comment {TICKET} --body ok")
                self.assertEqual(call(host, event), (0, None))


# ------------------------------------------------------------------------ AC5


class TestTheWordingSaysWhatToDoNext(unittest.TestCase):
    """Read it as the agent that just hit the closed door reads it."""

    def reason(self) -> str:
        return reason_of(call("claude", EVENTS["claude"])[1])

    def test_it_names_the_ticket(self):
        self.assertIn(f"#{TICKET}", self.reason())

    def test_it_hands_over_the_command_that_does_work(self):
        self.assertIn(f"verify-ticket.py {TICKET} --closeout", self.reason())

    def test_it_names_the_way_out_for_work_that_is_not_finished(self):
        self.assertIn("HANDOFF REQUIRED", self.reason())

    def test_it_does_not_point_back_at_the_command_it_just_refused(self):
        reason = self.reason()
        self.assertNotIn("gh issue close", reason)
        self.assertNotIn("--add-label ready-for-human", reason)

    def test_no_placeholder_survives_into_what_the_model_reads(self):
        self.assertNotIn("{", self.reason())


# ------------------------------------------------------------------------ AC6


class TestTheQuestionGate(unittest.TestCase):
    """A session in a ticket worktree may not put a question on the screen, on any runner."""

    ASKS = {
        "claude": {"hook_event_name": "PreToolUse", "tool_name": "AskUserQuestion",
                   "tool_input": {"questions": []}},
        "codex": {"hook_event_name": "PreToolUse", "tool_name": "request_user_input",
                  "tool_input": {}},
    }

    def ask(self, host: str, cwd_basename: str = f"issue-{TICKET}", env: dict | None = None,
            event: dict | None = None) -> tuple[int, dict | None]:
        out = io.StringIO()
        with named_cwd(cwd_basename):
            merged = {k: v for k, v in os.environ.items()
                      if not k.startswith("PASEO_")}
            merged.update(env or {})
            with mock.patch.dict(os.environ, merged, clear=True), \
                 mock.patch.object(hk.sys, "stdin",
                                   io.StringIO(json.dumps(event or self.ASKS[host]))), \
                 redirect_stdout(out), redirect_stderr(io.StringIO()):
                code = hk.main(["question", host])
        printed = out.getvalue().strip()
        return code, json.loads(printed) if printed else None

    def test_question_refuses_in_a_ticket_worktree_with_no_runner_variables(self):
        # An Orca or Herdr session carries no PASEO_* variable; the worktree alone decides.
        for host in self.ASKS:
            with self.subTest(host=host):
                code, answer = self.ask(host, env={"ORCA_TERMINAL_HANDLE": "term_1"})
                self.assertEqual(code, 0)
                self.assertIsNotNone(answer)

    def test_question_passes_outside_a_ticket_worktree(self):
        for host in self.ASKS:
            with self.subTest(host=host):
                self.assertEqual(self.ask(host, cwd_basename="multi-model-workflow"), (0, None))

    def test_the_question_gate_asks_no_runner(self):
        with mock.patch("subprocess.run") as run, mock.patch("subprocess.Popen") as popen:
            _, answer = self.ask("codex")
        self.assertIsNotNone(answer)
        run.assert_not_called()
        popen.assert_not_called()

    def test_another_tool_under_the_same_gate_goes_through(self):
        event = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                 "tool_input": {"command": "ls"}}
        self.assertEqual(self.ask("claude", event=event), (0, None))

    def test_the_reason_says_where_the_question_goes(self):
        _, answer = self.ask("codex")
        reason = reason_of(answer)
        self.assertIn("Decisions I made on my own", reason)
        self.assertIn("ABANDON: AC<n> decision", reason)
        self.assertIn("needs-triage", reason)


class TestNothingBlocksOnBadInput(unittest.TestCase):
    """A gate that cannot read its input has learned nothing, so it refuses nothing."""

    def quiet(self, argv, stdin="{}"):
        out, err = io.StringIO(), io.StringIO()
        with named_cwd(f"issue-{TICKET}"), \
             mock.patch.object(hk.sys, "stdin", io.StringIO(stdin)), \
             redirect_stdout(out), redirect_stderr(err):
            code = hk.main(argv)
        return code, out.getvalue()

    def test_an_unreadable_event(self):
        self.assertEqual(self.quiet(["pretool", "claude"], "not json"), (0, ""))

    def test_an_event_that_is_not_an_object(self):
        self.assertEqual(self.quiet(["pretool", "claude"], '["ls"]'), (0, ""))

    def test_a_host_it_does_not_know(self):
        for host in ("emacs", "grok", "cursor"):
            with self.subTest(host=host):
                self.assertEqual(self.quiet(["pretool", host]), (0, ""))

    def test_a_gate_it_does_not_know(self):
        self.assertEqual(self.quiet(["stop", "claude"]), (0, ""))

    def test_the_question_gate_reads_nothing_it_cannot(self):
        with named_cwd(f"issue-{TICKET}"), \
             mock.patch.object(hk.sys, "stdin", io.StringIO("not json")), \
             redirect_stdout(io.StringIO()) as out:
            self.assertEqual(hk.main(["question", "codex"]), 0)
        self.assertEqual(out.getvalue(), "")

    def test_no_arguments_at_all(self):
        self.assertEqual(self.quiet([]), (0, ""))


class TestCommandPrefixes(unittest.TestCase):
    LITERAL_COMMANDS = (
        "grep -n kill x.py",
        'echo "(kill 1)"',
        "rg 'env kill' x",
        "env FOO=1 grep -n kill x.py",
        "sudo -n echo '(kill 1)'",
        "command -v kill",
        "env --help kill",
        ">kill echo ok",
        "2> 'kill 1' echo ok",
        "env -u kill echo ok",
        "sudo -u kill echo ok",
        f"echo '(gh issue close {TICKET})'",
        f"env FOO=1 echo 'gh issue close {TICKET}'",
    )

    def test_prefix_ticket_commands_are_refused_by_both_hosts(self):
        for command in (
            f"(gh issue close {TICKET})",
            f">out gh issue close {TICKET}",
            f"env FOO=1 gh issue close {TICKET}",
            f'env "FOO=a b" gh issue close {TICKET}',
            f"X=$(date) gh issue close {TICKET}",
            f"sudo -n env FOO=1 gh issue edit {TICKET} --remove-label ready-for-agent",
        ):
            for host in EVENTS:
                with self.subTest(command=command, host=host):
                    code, answer = call(host, with_command(host, command))
                    decision = answer["hookSpecificOutput"]["permissionDecision"] if answer else None
                    self.assertEqual((code, decision), (0, "deny"))

    def test_prefix_literal_text_passes_the_hook(self):
        for command in self.LITERAL_COMMANDS:
            with self.subTest(command=command):
                self.assertEqual(call("codex", with_command("codex", command)), (0, None))


class TestBackgroundCommands(unittest.TestCase):

    def test_background_ticket_close_is_refused(self):
        for command in (f"a & gh issue close {TICKET}",
                        f"a&gh issue close {TICKET}",
                        f"a & gh issue close &>/dev/null {TICKET}",
                        f"a & gh issue close &>>/dev/null {TICKET}",
                        rf"echo \>&gh issue close {TICKET} $(true)",
                        f"a & gh issue close &>/dev/null {TICKET} $(true)",
                        f"bash -c 'a & gh issue close {TICKET}'"):
            for host in EVENTS:
                with self.subTest(command=command, host=host):
                    _, answer = call(host, with_command(host, command))
                    decision = answer["hookSpecificOutput"]["permissionDecision"] if answer else None
                    self.assertEqual(decision, "deny")


class TestQuotedCommands(unittest.TestCase):
    def test_guard_shell_heredoc_bodies_are_checked_as_code(self):
        for host in EVENTS:
            for consumer in ("bash <<EOF", "sh <<EOF", "cat <<EOF | sh",
                             "env FOO=1 /bin/bash <<EOF"):
                for body in (f"gh issue close {TICKET}", "rm -rf .",
                             f"gh pr comment {TICKET} --edit-last"):
                    for terminator in ("EOF", ""):
                        command = f"{consumer}\n{body}\n{terminator}"
                        with self.subTest(host=host, command=command):
                            self.assertIsNotNone(call(host, with_command(host, command))[1])

    def test_guard_arithmetic_shifts_do_not_hide_later_commands(self):
        for host in EVENTS:
            for arithmetic in ("echo $((1<<2))", "echo $((1 << 2))", "((1 << 2))"):
                for forbidden in (f"gh issue close {TICKET}",):
                    for tail in ("", "2\n"):
                        command = f"{arithmetic}\n{forbidden}\n{tail}"
                        with self.subTest(host=host, command=command):
                            self.assertIsNotNone(call(host, with_command(host, command))[1])

    def test_guard_a_command_after_the_heredoc_is_checked(self):
        for command in (
            f"cat <<EOF\nkill: 'data\nEOF\ngh issue close {TICKET}",
            f"cat <<-'EOF'\n\tdata\n\tEOF\ngh issue close {TICKET}",
            f'cat <<"A" <<B\nfirst\nA\nsecond\nB\ngh issue close {TICKET}',
            f"cat <<EOF; gh issue close {TICKET}\ndata\nEOF",
            f"echo '<<EOF'\ngh issue close {TICKET}\nEOF",
            f"echo ok # <<EOF\ngh issue close {TICKET}\nEOF",
        ):
            for host in EVENTS:
                with self.subTest(command=command, host=host):
                    code, answer = call(host, with_command(host, command))
                    self.assertEqual(code, 0)
                    self.assertIsNotNone(answer)

    def test_guard_a_heredoc_body_is_data(self):
        for marker, terminator in (("EOF", "EOF"), ("'EOF'", "EOF"),
                                   ('"EOF"', "EOF"), ("-EOF", "\tEOF")):
            command = f"cat <<{marker}\n{{ pid: number; kill: () => boolean }}\n{terminator}\n"
            for host in EVENTS:
                with self.subTest(marker=marker, host=host):
                    self.assertEqual(call(host, with_command(host, command)), (0, None))
        command = "cat <<A <<-'B'\nkill: 'data\nA\n\tpkill data\n\tB\necho ok"
        self.assertEqual(call("codex", with_command("codex", command)), (0, None))

    def test_quoted_original_command_passes_the_hook(self):
        command = (
            "rg -n 'tool.guard|kill|refus' mmw-v4/tests/install/test_install.py\n"
            "cat /Users/cheuklapchan/.agents/skills/principle-prove-it-works/SKILL.md\n"
            "cat /Users/cheuklapchan/.agents/skills/"
            "principle-progress-is-what-the-record-says/SKILL.md\n"
        )
        for host in EVENTS:
            with self.subTest(host=host):
                self.assertEqual(call(host, with_command(host, command)), (0, None))

    def test_quoted_text_does_not_close_the_ticket(self):
        command = f"echo 'a; gh issue close {TICKET}'"
        self.assertEqual(hk.runs(command), [])
        self.assertEqual(call("codex", with_command("codex", command)), (0, None))

    def test_quoted_comment_and_heredoc_text_cannot_hide_commands(self):
        for command in (
            f"cat > d <<'EOF'\ndon't\nEOF\ngh issue close {TICKET}\n"
            "cat <<'EOF'\nit's\nEOF",
        ):
            for host in EVENTS:
                with self.subTest(command=command, host=host):
                    _, answer = call(host, with_command(host, command))
                    decision = answer["hookSpecificOutput"]["permissionDecision"] if answer else None
                    self.assertEqual(decision, "deny")

    def test_quoted_nested_shell_code_is_conservatively_checked(self):
        for command in (
            f"bash -c 'x; gh issue close {TICKET}'",
        ):
            for host in EVENTS:
                with self.subTest(command=command, host=host):
                    _, answer = call(host, with_command(host, command))
                    decision = answer["hookSpecificOutput"]["permissionDecision"] if answer else None
                    self.assertEqual(decision, "deny")


class BriefWorktreeGuard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.worktree = self.root / "sender"
        self.worktree.mkdir()
        self.home = self.root / "home"
        self.runners = self.root / "runners"
        self.runners.mkdir()
        self.calls = self.root / "runner-calls"
        (self.runners / "fake.sh").write_text(
            'printf "%s\\n" "$1" >> "$FAKE_CALLS"\n'
            '[ "$1" = self ] && printf "%s\\n" "$FAKE_SELF"\n')
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("MMW_")}
        self.env.update(MMW_HOME=str(self.home), MMW_RUNNERS_DIR=str(self.runners),
                        FAKE_SELF="child", FAKE_CALLS=str(self.calls))
        self.briefs = load(DISPATCH_SCRIPTS / "briefs.py", "guard_test_briefs")
        with mock.patch.dict(os.environ, self.env, clear=True):
            self.state = self.briefs.state_for("o/r")
        self.batch = self.briefs.create(self.state, "researcher", 1, "fake", "parent",
                                       worktree=self.worktree)
        self.briefs.mark_started(self.state, self.batch, 1,
                                {"runner": "fake", "session": "child"})

    def hook(self, command, *, host="codex", cwd=None):
        run = subprocess.run([sys.executable, str(DISPATCH_SCRIPTS / "tool-guard.py"),
                              "pretool", host], input=json.dumps(with_command(host, command)),
                             cwd=cwd or self.worktree, env=self.env,
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        return json.loads(run.stdout) if run.stdout.strip() else None

    def test_a_brief_session_commit_is_refused(self):
        self.env["FAKE_PRIVATE_VALUE"] = "private-environment-value"
        answer = self.hook('git commit -m "$FAKE_PRIVATE_VALUE"')
        self.assertIsNotNone(answer)
        self.assertNotIn(self.env["FAKE_PRIVATE_VALUE"], reason_of(answer))
        commands = [f"git {verb}" for verb in (
            "commit -m findings", "merge topic", "rebase dev", "reset --hard", "push origin dev",
            "pull", "stash", "cherry-pick HEAD", "revert HEAD", "am patch", "tag v1",
            "worktree add ../candidate")]
        commands += [
            "bash <<EOF\ngit commit -m findings\nEOF",
            "cat <<EOF | sh\ngit commit -m findings\nEOF",
            "env NOTE=1 git commit -m findings", "sudo -n git commit -m findings",
            "command git commit -m findings", "(git commit -m findings)",
            "! { git commit -m findings; }", ">out git commit -m findings",
            "true && git commit -m findings", "false || git commit -m findings",
            "echo ok; git commit -m findings", "echo ok & git commit -m findings",
            "echo ok | git commit -m findings", "echo ok\ngit commit -m findings",
            "git -c user.name=Researcher -C . commit -m findings",
            "git --git-dir=.git commit -m findings"]
        for host in EVENTS:
            for command in commands:
                with self.subTest(host=host, command=command):
                    answer = self.hook(command, host=host)
                    self.assertIsNotNone(answer)
                    self.assertIn(f"{self.batch}/1", reason_of(answer))

    def test_a_brief_session_branch_switch_is_refused(self):
        for command in ("git checkout -b findings", "git switch dev", "git branch findings",
                        "git branch -d findings", "git branch -D findings", "git branch -m findings",
                        "git branch -M findings", "git branch -c findings", "git branch -C findings",
                        "git branch --delete findings", "git branch --move findings",
                        "git branch --copy findings", "git branch --create-reflog findings",
                        "git branch --format '%(refname:short)' findings",
                        "git branch --sort committerdate findings"):
            with self.subTest(command=command):
                self.assertIsNotNone(self.hook(command))

    def test_a_brief_session_may_write_files(self):
        for command in ("cat > answer.md", "mkdir -p candidates/1", "git status",
                        "git diff", "git log -3", "git branch --list", "git branch -a",
                        "git worktree list", "echo 'git commit -m findings'",
                        "git branch --show-current", "git branch --contains HEAD",
                        "git branch --list 'topic*'", "git branch -l 'topic*'",
                        "git branch --format '%(refname:short)'", "git branch --sort committerdate",
                        "git branch --sort -committerdate", "git branch --format '-d'",
                        "git --no-pager log -3"):
            with self.subTest(command=command):
                self.assertIsNone(self.hook(command))

    def test_a_session_that_is_no_brief_may_commit(self):
        self.env["FAKE_SELF"] = "parent"
        self.assertIsNone(self.hook("git commit -m findings"))
        self.env["FAKE_SELF"] = "child"
        self.briefs.mark_lost(self.state, self.batch, 1, "stopped")
        self.assertIsNone(self.hook("git commit -m findings"))

    def test_a_command_with_no_git_write_asks_no_runner(self):
        self.assertIsNone(self.hook("git status && echo 'git commit -m findings'"))
        self.assertFalse(self.calls.exists())

    def test_removing_the_worktree_this_session_runs_in_is_refused(self):
        self.env["FAKE_SELF"] = "parent"
        nested = self.worktree / "notes"
        nested.mkdir()
        for host in EVENTS:
            for command in ("git worktree remove --force ..", "rm -rf ..", "rm -rf .",
                            f"rm -rf '{self.worktree}'", f"git -C '{self.root}' worktree remove sender",
                            "cd ../.. && rm -rf sender", "cd ../.. && git worktree remove sender",
                            "cd ..; cd ..; rm -rf sender", "(cd ../.. && rm -rf sender)",
                            "(cd ../.. && true); rm -rf ../notes"):
                with self.subTest(host=host, command=command):
                    answer = self.hook(command, host=host, cwd=nested)
                    self.assertIsNotNone(answer)
                    self.assertIn(str(nested), reason_of(answer))
        self.assertIsNone(self.hook("rm -f answer.md", cwd=nested))
        self.assertIsNone(self.hook("cd .. && rm -f answer.md", cwd=nested))
        self.assertIsNone(self.hook("git worktree remove ../../unused", cwd=nested))
        self.briefs.remove(self.state, self.batch)
        self.assertIsNotNone(self.hook("rm -rf ..", cwd=nested))

    def test_removing_a_worktree_an_open_batch_runs_in_is_refused(self):
        self.env["FAKE_SELF"] = "unrelated"
        other = self.root / "other"
        other.mkdir()
        protected = self.briefs.create(self.state, "candidate", 1, "fake", "sender",
                                       worktree=other)
        for command in (f"git worktree remove --force '{other}'", f"rm -rf '{other}'",
                        f"env NOTE=1 git worktree remove '{other}'", f"(rm -rf '{other}')",
                        f'wt="{other}"; rm -rf "$wt"',
                        f'wt="{other}"; git worktree remove "${{wt}}"',
                        f'{{ wt="{other}"; rm -rf "$wt"; }}'):
            with self.subTest(command=command):
                answer = self.hook(command)
                self.assertIsNotNone(answer)
                self.assertIn(protected, reason_of(answer))
                self.assertIn(f"dispatch.sh brief close {protected}", reason_of(answer))
        self.briefs.mark_lost(self.state, protected, 1, "stopped")
        self.assertIsNotNone(self.hook(f"rm -rf '{other}'"))
        self.assertIsNone(self.hook(f'wt="{other}"; rm -rf \'$wt\''))
        self.assertIsNone(self.hook('wt="unused"; rm -rf "$wt"'))
        self.briefs.remove(self.state, protected)
        self.assertIsNone(self.hook(f"rm -rf '{other}'"))


if __name__ == "__main__":
    unittest.main()
