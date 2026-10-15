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
    """A temporary directory whose basename is the only fact `pretool` reads."""
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
    """A basename that is not `issue-<n>` is not a ticket worktree. `pretool` reads the
    two directories of `governed_ticket` and nothing else."""

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

    def test_the_source_imports_no_socket_urllib_tempfile_shutil_or_pathlib(self):
        source = (DISPATCH_SCRIPTS / "tool-guard.py").read_text(encoding="utf-8")
        for name in ("socket", "urllib", "tempfile", "shutil", "pathlib"):
            self.assertNotIn(f"import {name}", source)


# ------------------------------------------------------------------------ AC2


class TestWhatItStops(unittest.TestCase):
    """Two commands finish a ticket. Everything else is the worker's own business."""

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


class EndingAProcess(unittest.TestCase):
    """The third refusal: a run never ends a process it did not start.

    Several tickets are worked on one machine at once. Another run's application is
    indistinguishable from a stuck one, and on 2026-09-05 a worker ended one to take its
    ports. The gate refuses the whole family rather than trying to work out whose process
    it is — the same "refuses rather than checks" the `gh issue close` refusal above is built on,
    for the same reason: guessing wrong is the outcome the gate exists to prevent.
    """

    def test_the_kill_family_is_refused(self):
        for command in ("kill 123", "kill -9 4321", "pkill -f Electron",
                        "killall Electron", "lsof -ti:5173 | xargs kill -9",
                        "lsof -tnP -iTCP:8794 | xargs -r kill"):
            with self.subTest(command=command):
                code, answer = call("claude", with_command("claude", command))
                self.assertEqual(code, 0)
                self.assertIsNotNone(answer, f"{command} was allowed through")

    def test_every_host_is_told(self):
        for host in EVENTS:
            with self.subTest(host=host):
                _code, answer = call(host, with_command(host, "kill 123"))
                self.assertIsNotNone(answer)

    def test_the_refusal_says_what_to_do_instead(self):
        """A refusal that only diagnoses is where the improvising starts."""
        _code, answer = call("claude", with_command("claude", "kill 123"))
        reason = reason_of(answer)
        self.assertIn("verify-<product>", reason)

    def test_prose_and_ordinary_commands_pass(self):
        """Splitting on the shell's own separators tells a command from a mention."""
        for command in ("uv run pytest", "grep -rn kill src/",
                        "cat <<'EOF'\nI did not kill anything\nEOF",
                        "git log --oneline | head -5"):
            with self.subTest(command=command):
                code, answer = call("claude", with_command("claude", command))
                self.assertEqual(code, 0)
                self.assertIsNone(answer, f"{command} was refused")


class TestCommandPrefixes(unittest.TestCase):
    def test_prefix_env_path_and_split_options_keep_command_arguments(self):
        for command, expected in (
            ("env -P /bin kill 1", "kill 1"),
            ("env -S 'kill 1'", "kill 1"),
            ("env -iS 'kill 1'", "kill 1"),
            ("env --split-string='kill 1'", "kill 1"),
            ("env -S 'kill' 1", "kill 1"),
            ("env -S \"echo 'kill 1'\"", None),
            ("env -S '(kill 1)'", None),
            ("env -S 'kill; echo ok'", None),
            ("env -P kill echo ok", None),
        ):
            with self.subTest(command=command):
                self.assertEqual(hk.ends_a_process(command), expected)

    def test_prefix_ticket_commands_are_refused_by_both_hosts(self):
        for command in (
            f"(gh issue close {TICKET})",
            f">out gh issue close {TICKET}",
            f"env FOO=1 gh issue close {TICKET}",
            f"X=$(date) gh issue close {TICKET}",
            f"sudo -n env FOO=1 gh issue edit {TICKET} --remove-label ready-for-agent",
        ):
            for host in EVENTS:
                with self.subTest(command=command, host=host):
                    code, answer = call(host, with_command(host, command))
                    decision = answer["hookSpecificOutput"]["permissionDecision"] if answer else None
                    self.assertEqual((code, decision), (0, "deny"))

    def test_prefix_literal_text_is_not_a_command(self):
        self.assertEqual(hk.ends_a_process("env FOO=1 kill 1"), "kill 1")
        for command in (
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
        ):
            with self.subTest(command=command):
                self.assertIsNone(hk.ends_a_process(command))
                self.assertEqual(call("codex", with_command("codex", command)), (0, None))

    def test_prefix_programs_expose_the_termination_command(self):
        for command in (
            "env FOO=1 kill 1",
            "env -i -u OLD --chdir /tmp FOO='two words' kill 1",
            "env --unset=OLD -- kill 1",
            "sudo -n kill 1",
            "sudo -nu root -g staff --preserve-env=FOO -- kill 1",
            "sudo --user root --group=staff kill 1",
            "nohup kill 1",
            "command kill 1",
            "command -p kill 1",
            "builtin kill 1",
            "exec kill 1",
            "exec -a worker kill 1",
            "nice -n 5 kill 1",
            "nice --adjustment=5 kill 1",
            "nice -5 kill 1",
            "time -p kill 1",
            "time -f '%E' -o timing.log kill 1",
            "(FLAG=1 >out env -i FOO=1 sudo -n nohup nice -n 5 "
            "command builtin exec -a worker time -p ! { kill 1; })",
        ):
            with self.subTest(command=command):
                self.assertEqual(hk.ends_a_process(command), "kill 1")

    def test_prefix_shell_syntax_exposes_the_termination_command(self):
        for command, expected in (
            ("FOO=$(x) kill 1", "kill 1"),
            ("X=$(date) kill 1", "kill 1"),
            ("X=a$(b) kill 1", "kill 1"),
            ("X=$((1+2)) kill 1", "kill 1"),
            ("a && X=$(y) kill 1", "kill 1"),
            ("X=$(a$(b$(c))) kill 1", "kill 1"),
            ('X="$(date)" kill 1', "kill 1"),
            ("X=`date` kill 1", "kill 1"),
            ("a & (kill 1)", "kill 1)"),
            ("a ; (kill 1)", "kill 1)"),
            ("a & { kill 1; }", "kill 1"),
            ("a ; { kill 1; }", "kill 1"),
            ("! kill 1", "kill 1"),
            ("a & >out kill 1", "kill 1"),
            ("a ; >out kill 1", "kill 1"),
            ("a & \\\nkill 1", "kill 1"),
            ("a ; \\\nkill 1", "kill 1"),
            ("2>/dev/null kill 1", "kill 1"),
            ("> out >>out <in 2>err 2>&1 &>out kill 1", "kill 1"),
            (">'out file' 2> \"error file\" kill 1", "kill 1"),
            ("(FLAG=1 >out ! \\\n { OTHER='two words' kill 1; })", "kill 1"),
        ):
            with self.subTest(command=command):
                self.assertEqual(hk.ends_a_process(command), expected)


class TestBackgroundCommands(unittest.TestCase):
    def test_background_process_commands_are_recognised(self):
        for command, expected in (
            ("a & kill 1", "kill 1"),
            ("a&kill 1", "kill 1"),
            ("a& pkill x", "pkill x"),
            ("a &killall y", "killall y"),
            ("a & FLAG=1 kill 1", "kill 1"),
            (r"echo \>&kill 1", "kill 1"),
            (r"echo \>&kill 1 $(true)", "kill 1 $(true)"),
            (r"echo \<&kill 1 $(true)", "kill 1 $(true)"),
            (r"echo \\\>&kill 1 $(true)", "kill 1 $(true)"),
            ("echo 'a & kill 1", "kill 1"),
            ("echo a & kill 1\\", "kill 1\\"),
            ("bash -c 'a & kill 1'", "kill 1'"),
        ):
            with self.subTest(command=command):
                self.assertEqual(hk.ends_a_process(command), expected)

    def test_background_ampersands_in_data_and_redirections_stay_data(self):
        for command, expected in (
            ("kill 1", "kill 1"),
            ("a && kill 1", "kill 1"),
            ("cmd 2>&1", None),
            ("cmd >&2", None),
            ("cmd &>log", None),
            ("kill &>/dev/null 1", "kill &>/dev/null 1"),
            ("kill &>>/dev/null 1", "kill &>>/dev/null 1"),
            (r"echo \\>&kill 1 $(true)", None),
            ("cmd <&0", None),
            ("cmd >&kill 1", None),
            ("cmd <&kill 1", None),
            ("echo 'a & b'", None),
            ('echo "a & kill 1"', None),
            (r"echo a\& b", None),
            (r"echo a\& kill 1", None),
        ):
            with self.subTest(command=command):
                self.assertEqual(hk.ends_a_process(command), expected)

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
    def test_quoted_separators_are_not_process_commands(self):
        for command in (
            "rg -n 'tool.guard|kill|refus' x.py",
            'grep "a; kill 1" f',
            "echo 'x && pkill y'",
            'echo "x || killall y"',
            "echo 'x\nkill 1'",
            'echo "x | kill 1"',
            "echo '$(true; kill 1)'",
            "echo '`true; kill 1`'",
            "echo '# literal; kill 1'",
            'echo "<< literal; kill 1"',
        ):
            with self.subTest(command=command):
                self.assertIsNone(hk.ends_a_process(command))

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

    def test_quoted_and_escaped_boundaries(self):
        for command, expected in (
            (r"echo a\; kill 1", None),
            (r"echo a\| kill 1", None),
            (r"echo a\&\& pkill x", None),
            (r"echo a\|\| killall x", None),
            ("echo a\\\nkill 1", None),
            (r'echo "a \" | kill 1"', None),
            ('echo "a \' | kill 1"', None),
            (r"echo 'a\'; kill 1", "kill 1"),
            (r'echo "a \\"; kill 1', "kill 1"),
            ('echo "a; kill 1"; pkill x', "pkill x"),
        ):
            with self.subTest(command=command):
                self.assertEqual(hk.ends_a_process(command), expected)

    def test_quoted_text_does_not_close_the_ticket(self):
        command = f"echo 'a; gh issue close {TICKET}'"
        self.assertEqual(hk.runs(command), [])
        self.assertEqual(call("codex", with_command("codex", command)), (0, None))

    def test_quoted_real_process_commands_are_still_recognised(self):
        for command, expected in (
            ("foo | kill 1", "kill 1"),
            ("lsof -ti:5173 | xargs kill -9", "xargs kill -9"),
            ("a; pkill x", "pkill x"),
            ("a && killall y", "killall y"),
            ("a || kill 1", "kill 1"),
            ("a\nkill 1", "kill 1"),
            (" ; ; FLAG=1 kill 1", "kill 1"),
        ):
            with self.subTest(command=command):
                self.assertEqual(hk.ends_a_process(command), expected)

    def test_quoted_unclosed_input_uses_conservative_boundaries(self):
        for command, expected in (
            ("echo 'a | kill 1", "kill 1"),
            ('echo "a; pkill x', "pkill x"),
        ):
            with self.subTest(command=command):
                self.assertEqual(hk.ends_a_process(command), expected)

    def test_quoted_comment_and_heredoc_text_cannot_hide_commands(self):
        for command in (
            "echo hi # don't\nkill 1\n# it's done",
            "# Don't leave stale\nkill 1234\n# It's fine",
            "echo hi;# don't\nkill 1\n# it's done",
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
            "bash -c 'echo hi; kill 1'",
            'sh -c "a | pkill x"',
            f"bash -c 'x; gh issue close {TICKET}'",
            'echo "$(true; kill 1)"',
            'echo "`true; kill 1`"',
            "echo $(true; kill 1)",
            "echo `true; kill 1`",
            "FLAG=1 /bin/bash -lc 'echo hi; kill 1'",
            "'bash' -c 'echo hi; kill 1'",
        ):
            for host in EVENTS:
                with self.subTest(command=command, host=host):
                    _, answer = call(host, with_command(host, command))
                    decision = answer["hookSpecificOutput"]["permissionDecision"] if answer else None
                    self.assertEqual(decision, "deny")


if __name__ == "__main__":
    unittest.main()
