"""What a worker sees when a criterion fails.

The run is the same one `test_verify_ticket.py` drives: a fixed ticket body, the real
gate-check, and the one `ticket.checked` comment the run posts. Nothing here calls
the tracker. The worktree is one this test creates, so a log left by an earlier run
cannot satisfy an assertion.
"""

from __future__ import annotations

import io
import json
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from _load import load, started

vt = load()
STARTED = started(ticket=1, into="spec-337")


def ticket(*criteria: str, owns: str = "- src/**") -> str:
    return "## Owns\n\n" + owns + "\n\n## Acceptance criteria\n\n" + "\n".join(criteria) + "\n"


def python_output(stdout_lines: list[str], stderr_lines: list[str] | None = None) -> str:
    """One shell command that writes these lines and exits 1."""
    parts = ["import sys"]
    for line in stdout_lines:
        parts.append("sys.stdout.write(" + json.dumps(line + "\n") + ")")
    for line in stderr_lines or []:
        parts.append("sys.stderr.write(" + json.dumps(line + "\n") + ")")
    parts.append("sys.exit(1)")
    return "python3 -c " + json.dumps("; ".join(parts))


def evidence_value(comment: str) -> str:
    for line in comment.splitlines():
        stripped = line.strip()
        if stripped.startswith("EVIDENCE:"):
            return stripped[len("EVIDENCE:"):].strip()
    return ""


def refusal_line(printed: str) -> str:
    for line in printed.splitlines():
        if "ticket #1" in line:
            return line
    return ""


class TestFailureReport(unittest.TestCase):
    def make_repo(self) -> Path:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)

        def sh(*args: str) -> None:
            subprocess.run(["git", *args], cwd=tmp, check=True, capture_output=True)

        sh("init", "-q", "-b", "main")
        sh("config", "user.email", "t@t")
        sh("config", "user.name", "t")
        (tmp / "README").write_text("x\n")
        sh("add", "-A")
        sh("commit", "-qm", "init")
        return tmp

    def run_ticket(self, body: str, reverify: bool = False, comments: list[str] | None = None,
                   actor: str | None = None, outside=(), started_event=STARTED,
                   root: Path | None = None):
        root = root or self.make_repo()
        posted: list[str] = []
        history = ([] if started_event is None else [started_event]) + (comments or [])
        with mock.patch.object(vt, "repo_root", return_value=root), \
             mock.patch.object(vt, "fetch_body", return_value=body), \
             mock.patch.object(vt, "fetch_comments", return_value=history), \
             mock.patch.object(vt, "outside_owns", return_value=list(outside)), \
             mock.patch.object(vt, "current_branch", return_value="issue-1"), \
             mock.patch.object(vt, "post_comment", side_effect=lambda n, b: posted.append(b)):
            with redirect_stdout(io.StringIO()) as out:
                code = vt.run_checks(1, reverify, actor)
        return code, (posted[0] if posted else ""), out.getvalue(), root

    def test_failing_criterion_output_saved(self):
        root = self.make_repo()
        stale = root / ".scratch" / "criteria" / "1" / "STALE.log"
        stale.parent.mkdir(parents=True)
        stale.write_text("stale-run\n")
        stdout_lines = ["stdout-marker"] + [f"body-{i}" for i in range(1, 28)]
        stdout_lines.append("    indented-log-line")
        stderr_lines = ["stderr-marker"]
        code, comment, printed, root = self.run_ticket(ticket(
            "- [ ] AC2: the run keeps the whole output",
            "  CHECK: " + python_output(stdout_lines, stderr_lines),
            "  EXPECT: never-this-token-zz",
            "  EVIDENCE: pending",
        ), root=root)
        self.assertEqual(code, 1, comment)
        rel = ".scratch/criteria/1/AC2.log"
        self.assertIn(rel, printed)
        log = root / rel
        self.assertEqual(log.read_text(encoding="utf-8"),
                         "".join(line + "\n" for line in stdout_lines + stderr_lines))
        self.assertIn("body-10", log.read_text(encoding="utf-8"))
        self.assertFalse(stale.exists())

    def test_ticket_evidence_keeps_error_line(self):
        lines = [
            "E AssertionError: assert 16.9915 == 16.99",
            "src/pricing.py:42",
        ]
        lines += ["fail-" + str(n) + "-" + ("x" * 180) for n in range(3, 28)]
        lines.append("only-in-the-middle")
        lines += ["closing-one", "closing-two"]
        code, comment, _, _root = self.run_ticket(ticket(
            "- [ ] AC3: the ticket keeps the assertion",
            "  CHECK: " + python_output(lines),
            "  EXPECT: never-this-token-zz",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 1, comment)
        evidence = evidence_value(comment)
        self.assertLessEqual(len(evidence), 900)
        self.assertGreater(len(evidence), 700)
        self.assertIn("E AssertionError: assert 16.9915 == 16.99", evidence)
        self.assertIn("src/pricing.py:42", evidence)
        self.assertNotIn("only-in-the-middle", evidence)
        self.assertRegex(evidence, r"\+\d+ more")
        self.assertIn(".scratch/criteria/1/AC3.log", evidence)

    def test_failing_criterion_prints_tail(self):
        lines = ["early-only-marker"]
        lines += [f"pad-{n}" for n in range(2, 45)]
        lines.append("    indented-tail-marker")
        lines += [f"pad-{n}" for n in range(46, 51)]
        code, comment, printed, _root = self.run_ticket(ticket(
            "- [ ] AC4: the screen shows the tail",
            "  CHECK: " + python_output(lines),
            "  EXPECT: never-this-token-zz",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 1, comment)
        self.assertEqual(len(lines), 50)
        self.assertIn("    indented-tail-marker", printed)
        self.assertIn("pad-11", printed)
        self.assertNotIn("pad-10", printed)
        self.assertNotIn("early-only-marker", printed)
        evidence = evidence_value(comment)
        self.assertNotIn("indented-tail-marker", evidence)
        self.assertNotIn("early-only-marker", evidence)

    def test_failing_criterion_prints_tail_as_a_quote(self):
        lines = [
            "STORY OK x",
            "JOURNEY OK y",
            "HARNESS OK z",
            "LINT OK w",
            "HANDOFF REQUIRED: 1 abandoned",
            "ALL MET (9 met)",
            "VISIBLE",
        ]
        code, comment, printed, _root = self.run_ticket(ticket(
            "- [ ] AC4: the tail is quoted",
            "  CHECK: " + python_output(lines),
            "  EXPECT: never-this-token-zz",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 1, comment)
        self.assertNotRegex(printed, r"(?m)^(ALL MET|HANDOFF REQUIRED:)")
        self.assertRegex(printed, r"(?m)^UNMET:")
        self.assertNotIn("STORY OK", printed)
        self.assertNotIn("JOURNEY OK", printed)
        self.assertNotIn("HARNESS OK", printed)
        self.assertNotIn("LINT OK", printed)
        self.assertIn("VISIBLE", printed)
        self.assertRegex(comment, r"Own run on [0-9a-f]+: UNMET:")
        self.assertNotRegex(comment, r"Own run on [0-9a-f]+: (ALL MET|HANDOFF REQUIRED:)")

    def test_unrunnable_criterion_names_ticket(self):
        code, comment, printed, _root = self.run_ticket(ticket(
            "- [ ] AC6: the command spans a line",
            "  CHECK: python3 -c \"",
            "print('nope')\"",
            "  EXPECT: nope",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 2)
        self.assertEqual(comment, "")
        self.assertIn("AC6", refusal_line(printed))
        self.assertIn("verify-ticket.py 1 --sub-issue contract", printed)
        self.assertNotRegex(printed, r"/var/|/tmp/|/private/|verify-ticket-")
        self.assertNotRegex(printed, r"\bline \d+:")
        self.assertNotIn("criterion unknown", printed)

        code, comment, printed, _root = self.run_ticket(ticket(
            "- [ ] AC6: the attribute sits under the criterion",
            "CHECK: echo nope",
            "  EXPECT: nope",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 2)
        self.assertEqual(comment, "")
        self.assertIn("AC6", refusal_line(printed))
        self.assertNotIn("criterion unknown", printed)
        self.assertNotRegex(printed, r"\bline \d+:")


if __name__ == "__main__":
    unittest.main()
