"""Which runner: five levels, first speaker wins.

    python3 -m unittest discover -s mmw-v2/tests/dispatch -p test_runner_pick.py
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
import json
import os

from pathlib import Path

HERE = Path(__file__).resolve().parent
MODELS_PY = HERE.parents[1] / "skills" / "dispatch" / "scripts" / "models.py"
_spec = importlib.util.spec_from_file_location("mmw_models", MODELS_PY)
models = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(models)

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
            models.pick_runner(runtime=("orca",), default="paseo"), "orca")

    def test_default_when_nobody_spoke(self):
        self.assertEqual(models.pick_runner(), "orca")

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
                live="herdr", runtime=("orca",), default="paseo"),
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
                runtime=("orca", "herdr"), default="paseo"),
            "herdr")

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


class RuntimeHasAnAdapterTest(unittest.TestCase):
    def test_the_adapters_are_the_files_beside_models_py(self):
        self.assertEqual(
            [name for name in ("herdr", "orca", "paseo", "tmux", "lody")
             if models.has_adapter(name)],
            ["herdr", "orca", "paseo"])

    def test_tmux_alone_falls_through_to_the_default(self):
        environ = {"TMUX": "/tmp/tmux-1000/default"}
        self.assertEqual(models.runtime_from_environ(environ), ("tmux",))
        self.assertEqual(models.pick_runner(runtime=environ), "orca")
        self.assertEqual(
            models.pick_runner(runtime=environ, default="paseo"), "paseo")

    def test_herdr_env_and_tmux_pick_herdr(self):
        environ = {"HERDR_ENV": "1", "TMUX": "/tmp/tmux-1000/default"}
        self.assertEqual(models.runtime_from_environ(environ), ("herdr", "tmux"))
        self.assertEqual(
            models.pick_runner(runtime=environ, default="paseo"), "herdr")

    def test_an_explicit_runner_without_an_adapter_is_returned_as_given(self):
        self.assertEqual(
            models.runner_name({"MMW_RUNNER": "tmux", "HERDR_ENV": "1"}), "tmux")
        self.assertEqual(
            models.pick_runner(live="tmux", runtime={"HERDR_ENV": "1"}), "tmux")


class WorktreeOwningTest(unittest.TestCase):
    def test_worktree_owning_runtime_is_ignored(self):
        self.assertEqual(
            models.pick_runner(runtime=("lody",), default="paseo"), "paseo")

    def test_worktree_owning_among_runtime_signals_is_skipped(self):
        self.assertEqual(
            models.pick_runner(
                runtime=("orca", "herdr", "lody"), default="paseo"),
            "herdr")

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


class ConfigRunnerTest(unittest.TestCase):
    def test_saved_runner_precedes_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            saved = os.environ.get("MMW_HOME")
            os.environ["MMW_HOME"] = tmp
            try:
                Path(tmp, "models.json").write_text(
                    json.dumps(models.default_local_config()) + "\n", encoding="utf-8")
                self.assertEqual(models.runner_name({"HERDR_ENV": "1"}), "orca")
            finally:
                if saved is None:
                    os.environ.pop("MMW_HOME", None)
                else:
                    os.environ["MMW_HOME"] = saved


if __name__ == "__main__":
    unittest.main()
