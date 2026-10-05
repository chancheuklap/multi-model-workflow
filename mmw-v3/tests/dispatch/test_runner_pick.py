"""Which runner: MMW_RUNNER, then models.json, then for `auto` the runner this
process runs in, then orca.

    python3 -m unittest discover -s mmw-v3/tests/dispatch -p test_runner_pick.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
MODELS_PY = HERE.parents[1] / "skills" / "dispatch" / "scripts" / "models.py"
_spec = importlib.util.spec_from_file_location("mmw_models", MODELS_PY)
models = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(models)

HERDR = {"HERDR_ENV": "1"}
ORCA = {"TERM_PROGRAM": "Orca"}


class RunnerName(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name)
        patch = mock.patch.dict(os.environ, {"MMW_HOME": tmp.name})
        patch.start()
        self.addCleanup(patch.stop)

    def saved(self, runner):
        config = models.default_local_config()
        config["runner"] = runner
        (self.home / "models.json").write_text(json.dumps(config) + "\n", encoding="utf-8")

    def test_mmw_runner_beats_the_saved_runner(self):
        self.saved("paseo")
        self.assertEqual(models.runner_name({"MMW_RUNNER": "herdr", **ORCA}), "herdr")

    def test_the_saved_runner_beats_the_environment(self):
        self.saved("paseo")
        self.assertEqual(models.runner_name(HERDR), "paseo")

    def test_auto_takes_herdr_from_the_environment(self):
        self.saved("auto")
        self.assertEqual(models.runner_name(HERDR), "herdr")

    def test_auto_takes_orca_from_the_environment(self):
        self.saved("auto")
        self.assertEqual(models.runner_name(ORCA), "orca")

    def test_herdr_opened_inside_orca_is_herdr(self):
        self.saved("auto")
        self.assertEqual(models.runner_name({**HERDR, **ORCA}), "herdr")

    def test_auto_with_no_signal_is_orca(self):
        self.saved("auto")
        self.assertEqual(models.runner_name({}), "orca")

    def test_mmw_runner_auto_is_not_overruled_by_the_saved_runner(self):
        self.saved("paseo")
        self.assertEqual(models.runner_name({"MMW_RUNNER": "auto", **HERDR}), "herdr")

    def test_a_named_runner_without_an_adapter_is_returned_as_given(self):
        self.saved("auto")
        self.assertEqual(models.runner_name({"MMW_RUNNER": "tmux", **HERDR}), "tmux")

    def test_the_command_prints_the_auto_choice(self):
        self.saved("auto")
        out = models.subprocess.run(
            [models.sys.executable, str(MODELS_PY), "runner"], capture_output=True, text=True,
            env={**os.environ, "MMW_HOME": str(self.home), **HERDR,
                 "MMW_RUNNER": "", "TERM_PROGRAM": ""})
        self.assertEqual((out.returncode, out.stdout.strip()), (0, "herdr"), out.stderr)


class Adapters(unittest.TestCase):
    def test_the_adapters_are_the_files_beside_models_py(self):
        self.assertEqual(
            [name for name in ("herdr", "orca", "paseo", "tmux") if models.has_adapter(name)],
            ["herdr", "orca", "paseo"])


if __name__ == "__main__":
    unittest.main()
