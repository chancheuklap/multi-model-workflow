"""Which runner: five levels, first speaker wins.

    python3 -m unittest discover -s mmw-v2/tests/dispatch -p test_runner_pick.py
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODELS_PY = HERE.parents[1] / "skills" / "dispatch" / "scripts" / "models.py"
_spec = importlib.util.spec_from_file_location("mmw_models", MODELS_PY)
models = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(models)

TABLE_HEAD = (
    "| agent | host | model | effort |\n"
    "| --- | --- | --- | --- |\n"
)


def write_live(text: str) -> Path:
    fh = tempfile.NamedTemporaryFile(
        "w", suffix=".md", delete=False, encoding="utf-8")
    fh.write("# Models\n\n" + text)
    fh.close()
    return Path(fh.name)


class PickRunnerLevelsTest(unittest.TestCase):
    def test_ticket_alone_is_used(self):
        self.assertEqual(
            models.pick_runner(ticket="herdr", default="paseo"), "herdr")

    def test_env_alone_is_used(self):
        self.assertEqual(
            models.pick_runner(env="orca", default="paseo"), "orca")

    def test_live_alone_is_used(self):
        self.assertEqual(
            models.pick_runner(live="herdr", default="paseo"), "herdr")

    def test_runtime_alone_is_used(self):
        self.assertEqual(
            models.pick_runner(runtime=("tmux",), default="paseo"), "tmux")

    def test_default_when_nobody_spoke(self):
        self.assertEqual(models.pick_runner(), "paseo")

    def test_ticket_beats_env(self):
        self.assertEqual(
            models.pick_runner(
                ticket="herdr", env="orca", default="paseo"),
            "herdr")

    def test_env_beats_live(self):
        self.assertEqual(
            models.pick_runner(env="orca", live="herdr", default="paseo"),
            "orca")

    def test_live_beats_runtime(self):
        self.assertEqual(
            models.pick_runner(
                live="herdr", runtime=("tmux",), default="paseo"),
            "herdr")

    def test_runtime_beats_default(self):
        self.assertEqual(
            models.pick_runner(runtime=("herdr",), default="paseo"), "herdr")

    def test_blank_ticket_does_not_speak(self):
        self.assertEqual(
            models.pick_runner(
                ticket="  ", env="orca", default="paseo"),
            "orca")

    def test_innermost_runtime_signal_wins(self):
        self.assertEqual(
            models.pick_runner(
                runtime=("herdr", "tmux"), default="paseo"),
            "tmux")

    def test_herdr_env_and_tmux_detect_as_tmux(self):
        names = models.runtime_from_environ(
            {"HERDR_ENV": "1", "TMUX": "/tmp/tmux-1000/default"})
        self.assertEqual(names, ("herdr", "tmux"))
        self.assertEqual(
            models.pick_runner(runtime=names, default="paseo"), "tmux")

    def test_term_program_orca_is_orca(self):
        names = models.runtime_from_environ({"TERM_PROGRAM": "Orca"})
        self.assertEqual(names, ("orca",))
        self.assertEqual(
            models.pick_runner(runtime=names, default="paseo"), "orca")

    def test_runtime_reads_environ(self):
        self.assertEqual(
            models.pick_runner(runtime={"HERDR_ENV": "1"}), "herdr")

    def test_herdr_inside_orca(self):
        env = {"HERDR_ENV": "1", "TERM_PROGRAM": "Orca"}
        self.assertEqual(models.runtime_from_environ(env), ("orca", "herdr"))
        self.assertEqual(models.pick_runner(runtime=env), "herdr")


class WorktreeOwningTest(unittest.TestCase):
    def test_worktree_owning_runtime_is_ignored(self):
        self.assertEqual(
            models.pick_runner(runtime=("lody",), default="paseo"), "paseo")

    def test_worktree_owning_among_runtime_signals_is_skipped(self):
        self.assertEqual(
            models.pick_runner(
                runtime=("herdr", "lody", "tmux"), default="paseo"),
            "tmux")

    def test_worktree_owning_ticket_is_used(self):
        self.assertEqual(
            models.pick_runner(
                ticket="lody", runtime=("herdr",), default="paseo"),
            "lody")

    def test_worktree_owning_env_is_used(self):
        self.assertEqual(
            models.pick_runner(env="lody", default="paseo"), "lody")

    def test_worktree_owning_live_is_used(self):
        self.assertEqual(
            models.pick_runner(
                live="lody", runtime=("tmux",), default="paseo"),
            "lody")


class LiveRunnerRowTest(unittest.TestCase):
    def tearDown(self):
        for path in getattr(self, "_temps", ()):
            path.unlink(missing_ok=True)

    def _live(self, text: str) -> Path:
        path = write_live(text)
        self._temps = (*getattr(self, "_temps", ()), path)
        return path

    def test_two_cell_runner_row_is_read(self):
        path = self._live(
            "| runner | orca |\n"
            "| --- | --- |\n"
            "\n"
            + TABLE_HEAD
            + "| junior-worker | grok | grok 4.6 | high |\n"
        )
        self.assertEqual(models.parse_live_runner(path), "orca")
        previous = models.MODELS
        try:
            models.MODELS = path
            rows = models.session_rows()
        finally:
            models.MODELS = previous
        self.assertEqual([r.agent for r in rows], ["junior-worker"])

    def test_four_cell_runner_row_is_not_an_agent(self):
        path = self._live(
            TABLE_HEAD
            + "| junior-worker | grok | grok 4.6 | high |\n"
            + "| runner | herdr | — | — |\n"
        )
        self.assertEqual(models.parse_live_runner(path), "herdr")
        previous = models.MODELS
        try:
            models.MODELS = path
            rows = models.session_rows()
        finally:
            models.MODELS = previous
        self.assertEqual([r.agent for r in rows], ["junior-worker"])

    def test_missing_runner_row_is_silent(self):
        path = self._live(
            TABLE_HEAD + "| junior-worker | grok | grok 4.6 | high |\n")
        self.assertIsNone(models.parse_live_runner(path))

    def test_fresh_table_reaches_runtime(self):
        fh = tempfile.NamedTemporaryFile(
            "w", suffix=".md", delete=False, encoding="utf-8")
        fh.write(models.default_live_markdown())
        fh.close()
        path = Path(fh.name)
        self._temps = (*getattr(self, "_temps", ()), path)
        live = models.parse_live_runner(path)
        self.assertIsNone(live)
        self.assertEqual(
            models.pick_runner(live=live, runtime={"HERDR_ENV": "1"}),
            "herdr")
        self.assertEqual(models.pick_runner(live=live), "paseo")


if __name__ == "__main__":
    unittest.main()
