"""The closing gate: who it governs, what it stops, and what it says.

Every test drives `hook.py` the way a host does — one event as JSON on stdin, one
answer as JSON on stdout. The gate runs no command and reads no file, so there is
nothing here to stub out.
"""

import importlib.util
import io
import json
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "hook.py"


def load():
    spec = importlib.util.spec_from_file_location("mmw_hook", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hk = load()

TICKET = 64
WORKER = {"MMW_TICKET": str(TICKET)}
CLOSE = f"gh issue close {TICKET} --reason completed"

# One event per host, in the shape that host actually sends. Cursor's is the payload
# captured 2026-08-29 from cursor-agent 2026.08.25: the command at the top level, and
# `"cwd": ""` because a Cursor session can hold several checkouts at once.
EVENTS = {
    "claude": {"hook_event_name": "PreToolUse", "cwd": "/w", "tool_name": "Bash",
               "tool_input": {"command": CLOSE}},
    "codex": {"hook_event_name": "PreToolUse", "cwd": "/w", "tool_name": "Bash",
              "tool_input": {"command": CLOSE}},
    "grok": {"hookEventName": "pre_tool_use", "cwd": "/w",
             "toolName": "run_terminal_command", "toolInput": {"command": CLOSE}},
    "cursor": {"hook_event_name": "beforeShellExecution", "cwd": "", "sandbox": False,
               "command": CLOSE, "workspace_roots": ["/w"]},
    "pi": {"hook_event_name": "PreToolUse", "tool_name": "bash",
           "tool_input": {"command": CLOSE}},
}


def call(host: str, event: dict, env: dict | None = None) -> tuple[int, dict | None]:
    """Run the gate as its host would, and read back the answer it printed."""
    out = io.StringIO()
    with mock.patch.dict(os.environ, env if env is not None else WORKER, clear=False), \
         mock.patch.object(hk.sys, "stdin", io.StringIO(json.dumps(event))), \
         redirect_stdout(out), redirect_stderr(io.StringIO()):
        code = hk.main(["pretool", host])
    printed = out.getvalue().strip()
    return code, json.loads(printed) if printed else None


def reason_of(answer: dict) -> str:
    """The one sentence the model reads, wherever this host keeps it."""
    if "hookSpecificOutput" in answer:
        return answer["hookSpecificOutput"]["permissionDecisionReason"]
    for key in ("reason", "agent_message"):
        if key in answer:
            return answer[key]
    raise AssertionError(f"no reason in {answer}")


def with_command(host: str, command: str) -> dict:
    """The host's event, carrying a different command."""
    event = json.loads(json.dumps(EVENTS[host]))
    for holder in (event.get("tool_input"), event.get("toolInput")):
        if isinstance(holder, dict):
            holder["command"] = command
            return event
    event["command"] = command
    return event


# ------------------------------------------------------------------------ AC1

class TestSelfScope(unittest.TestCase):
    """Without the `MMW_TICKET` variable `dispatch.sh` sets there is no gate, and nothing
    is looked up."""

    def test_no_marker_no_gate(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(call("claude", EVENTS["claude"], env={}), (0, None))

    def test_a_marker_that_is_not_a_ticket_number_is_no_marker(self):
        for value in ("", "  ", "issue-64", "64x", "-64"):
            with self.subTest(marker=value):
                self.assertEqual(call("claude", EVENTS["claude"], {"MMW_TICKET": value}),
                                 (0, None))

    def test_the_gate_runs_nothing_and_opens_nothing(self):
        """It is told which ticket it governs, so it never has to go and find out."""
        with mock.patch("subprocess.run") as run, mock.patch("subprocess.Popen") as popen, \
             mock.patch("builtins.open") as opened:
            code, answer = call("claude", EVENTS["claude"])
        self.assertEqual(code, 0)
        self.assertIsNotNone(answer)
        run.assert_not_called()
        popen.assert_not_called()
        opened.assert_not_called()

    def test_the_source_imports_no_way_to_reach_the_network_or_the_disk(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for name in ("subprocess", "socket", "urllib", "tempfile", "shutil", "pathlib"):
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
    """Each host is refused in the vocabulary it understands."""

    def test_claude_and_codex(self):
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                code, answer = call(host, EVENTS[host])
                inner = answer["hookSpecificOutput"]
                self.assertEqual(inner["hookEventName"], "PreToolUse")
                self.assertEqual(inner["permissionDecision"], "deny")
                self.assertEqual(code, 0)

    def test_grok(self):
        _, answer = call("grok", EVENTS["grok"])
        self.assertEqual(answer["decision"], "deny")

    def test_cursor(self):
        _, answer = call("cursor", EVENTS["cursor"])
        self.assertEqual(answer["permission"], "deny")
        self.assertEqual(answer["user_message"], answer["agent_message"])

    def test_pi(self):
        _, answer = call("pi", EVENTS["pi"])
        self.assertIs(answer["block"], True)

    def test_the_answer_is_on_stdout_and_the_exit_code_stays_zero(self):
        """Every one of the five honours a deny on stdout whatever the exit code is;
        exiting non-zero as well would only make a failure look like a refusal."""
        for host in hk.HOSTS:
            with self.subTest(host=host):
                code, answer = call(host, EVENTS[host])
                self.assertEqual(code, 0)
                self.assertIsNotNone(answer)


# ------------------------------------------------------------------------ AC4

class TestInputShapes(unittest.TestCase):
    """Three spellings of one event, one decision, one sentence."""

    def test_every_host_reads_the_command_out_of_its_own_event(self):
        for host, event in EVENTS.items():
            with self.subTest(host=host):
                self.assertEqual(hk.command_of(event), CLOSE)

    def test_an_event_with_no_command_decides_nothing(self):
        for event in ({}, {"tool_input": {}}, {"command": ""}, {"tool_input": "ls"}):
            with self.subTest(event=event):
                self.assertIsNone(hk.command_of(event))

    def test_the_same_command_is_refused_on_all_five_with_the_same_words(self):
        reasons = {host: reason_of(call(host, EVENTS[host])[1]) for host in hk.HOSTS}
        self.assertEqual(len(set(reasons.values())), 1, reasons)

    def test_the_same_harmless_command_goes_through_on_all_five(self):
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

    def test_it_arrives_whole_on_the_host_that_clips_it(self):
        """Grok Build clips a deny reason at 256 characters and hides the rest.

        A sentence that runs past that loses its tail, and the tail is where the way
        out lives. Five digits is more ticket numbers than this tracker will ever hold.
        """
        for number in (7, 86, 640, 6400, 99999):
            with self.subTest(ticket=number):
                whole = hk.HOST_PREFIX + len(hk.REFUSAL.format(n=number))
                self.assertLessEqual(whole, hk.REASON_LIMIT)


# ------------------------------------------------------------------------ AC6

class TestTheQuestionGate(unittest.TestCase):
    """A dispatched session may not put a question on the screen."""

    AUTONOMOUS = {"MMW_AUTONOMOUS": "1"}
    ASKS = {
        "claude": {"hook_event_name": "PreToolUse", "tool_name": "AskUserQuestion",
                   "tool_input": {"questions": []}},
        "codex": {"hook_event_name": "PreToolUse", "tool_name": "request_user_input",
                  "tool_input": {}},
        "grok": {"hookEventName": "pre_tool_use", "toolName": "ask_user_question",
                 "toolInput": {"questions": []}},
    }

    def ask(self, host: str, env: dict) -> tuple[int, dict | None]:
        out = io.StringIO()
        with mock.patch.dict(os.environ, env, clear=True), \
             mock.patch.object(hk.sys, "stdin", io.StringIO(json.dumps(self.ASKS[host]))), \
             redirect_stdout(out), redirect_stderr(io.StringIO()):
            code = hk.main(["question", host])
        printed = out.getvalue().strip()
        return code, json.loads(printed) if printed else None

    def test_an_autonomous_session_is_refused_on_every_session_host(self):
        for host in self.ASKS:
            with self.subTest(host=host):
                code, answer = self.ask(host, self.AUTONOMOUS)
                self.assertEqual(code, 0)
                self.assertIsNotNone(answer)

    def test_a_session_nobody_dispatched_may_ask(self):
        for host in self.ASKS:
            with self.subTest(host=host):
                self.assertEqual(self.ask(host, {}), (0, None))
                self.assertEqual(self.ask(host, {"MMW_TICKET": "64"}), (0, None))

    def test_another_tool_under_the_same_gate_goes_through(self):
        event = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                 "tool_input": {"command": "ls"}}
        out = io.StringIO()
        with mock.patch.dict(os.environ, self.AUTONOMOUS, clear=True), \
             mock.patch.object(hk.sys, "stdin", io.StringIO(json.dumps(event))), \
             redirect_stdout(out):
            hk.main(["question", "claude"])
        self.assertEqual(out.getvalue().strip(), "")

    def test_the_reason_says_where_the_question_goes(self):
        _, answer = self.ask("grok", self.AUTONOMOUS)
        reason = reason_of(answer)
        self.assertIn("Decisions I made on my own", reason)
        self.assertIn("ABANDON: AC<n> decision", reason)
        self.assertIn("needs-triage", reason)

    def test_it_arrives_whole_on_the_host_that_clips_it(self):
        self.assertLessEqual(hk.HOST_PREFIX + len(hk.NO_QUESTION), hk.REASON_LIMIT)


class TestNothingBlocksOnBadInput(unittest.TestCase):
    """A gate that cannot read its input has learned nothing, so it refuses nothing."""

    def quiet(self, argv, stdin="{}"):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, WORKER, clear=False), \
             mock.patch.object(hk.sys, "stdin", io.StringIO(stdin)), \
             redirect_stdout(out), redirect_stderr(err):
            code = hk.main(argv)
        return code, out.getvalue()

    def test_an_unreadable_event(self):
        self.assertEqual(self.quiet(["pretool", "claude"], "not json"), (0, ""))

    def test_an_event_that_is_not_an_object(self):
        self.assertEqual(self.quiet(["pretool", "claude"], '["ls"]'), (0, ""))

    def test_a_host_it_does_not_know(self):
        self.assertEqual(self.quiet(["pretool", "emacs"]), (0, ""))

    def test_a_gate_it_does_not_know(self):
        self.assertEqual(self.quiet(["stop", "claude"]), (0, ""))

    def test_the_question_gate_reads_nothing_it_cannot(self):
        with mock.patch.dict(os.environ, {"MMW_AUTONOMOUS": "1"}, clear=True), \
             mock.patch.object(hk.sys, "stdin", io.StringIO("not json")), \
             redirect_stdout(io.StringIO()) as out:
            self.assertEqual(hk.main(["question", "grok"]), 0)
        self.assertEqual(out.getvalue(), "")

    def test_no_arguments_at_all(self):
        self.assertEqual(self.quiet([]), (0, ""))


if __name__ == "__main__":
    unittest.main()
