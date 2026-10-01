"""`.mmw/target.json` reading and `target_config.py --check`.
"""

import importlib.util
import json
import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "ui-acceptance" / "scripts" / "target_config.py"
HOME = tempfile.mkdtemp(prefix="mmw-target-config-home-")


def load():
    """A fresh `target_config`, and with it a `lease` bound to `HOME`.

    Every command `target_config` declares runs with this run's lease in its
    environment, and acquiring one writes to a registry `lease.py` fixes at import
    from `MMW_HOME`. Without a registry of its own here, the suite acquires real
    slots and overwrites the record of a run that is live — after which `release`
    refuses, because the ports are still listened on, and that slot is lost for good.
    """
    with mock.patch.dict(os.environ, {"MMW_HOME": HOME}, clear=False):
        spec = importlib.util.spec_from_file_location("target_config", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        sys.modules["target_config"] = module
        spec.loader.exec_module(module)
    return module


tc = load()


def tearDownModule():
    shutil.rmtree(HOME, ignore_errors=True)


class TestTargetConfig(unittest.TestCase):
    def test_target_json_is_required_and_read(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with self.assertRaises(SystemExit) as raised:
                tc.target_config(root)
            self.assertIn("target.json", str(raised.exception))
            (root / ".mmw").mkdir()
            (root / ".mmw" / "target.json").write_text(json.dumps(
                {"discover": "printf %s '{\"cdp\": \"http://127.0.0.1:9229\"}'"}))
            cfg = tc.target_config(root)
            self.assertEqual(cfg["discover"], "printf %s '{\"cdp\": \"http://127.0.0.1:9229\"}'")


class TestTargetCheck(unittest.TestCase):
    """`target_config.py --check` is the setup-time bar for one repository: it
    names every field of `.mmw/target.json` still to answer, and passes once the file
    is complete. The runtime reader `target_config` keeps its smaller bar."""

    COMPLETE = {"start": "s", "stop": "t", "discover": "d", "stories": "st",
                "leaves_machine": [], "harness_markers": []}

    def run_target(self, *argv):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = tc.target_main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_a_repository_without_the_file_is_told_every_required_field(self):
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = self.run_target("--check", "--repo", d)
        self.assertEqual(code, 1)
        for f in tc.FIELDS:
            self.assertIn(("  missing  " if f.required else "  absent   ") + f.key, out)
        self.assertIn("    origin — where the product is served", out)
        self.assertNotIn("  missing  reach", out)
        self.assertNotIn("transport_off", out)
        self.assertIn("e.g.", out)

    def test_a_complete_file_passes_and_optional_keys_stay_optional(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / ".mmw").mkdir()
            (Path(d) / ".mmw" / "target.json").write_text(json.dumps(self.COMPLETE))
            code, out, _ = self.run_target("--check", "--repo", d)
            self.assertEqual(code, 0, out)
            self.assertIn("complete", out)
            code, out, _ = self.run_target("--validate", "--repo", d)
            self.assertEqual(code, 0, out)

    def test_check_without_repo_uses_the_target_json_above_cwd(self):
        """A fixture lives inside another git worktree. `--repo` is omitted, so
        the walk from cwd has to find that fixture's file, not the worktree root."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / ".mmw").mkdir()
            (root / ".mmw" / "target.json").write_text(json.dumps(self.COMPLETE))
            nested = root / "inner"
            nested.mkdir()
            here = Path.cwd()
            os.chdir(nested)
            try:
                code, out, _ = self.run_target("--check")
            finally:
                os.chdir(here)
            self.assertEqual(code, 0, out)
            self.assertIn("complete: the oracles can drive this repository", out)
            self.assertIn(str(root / ".mmw" / "target.json"), out)

    def test_validate_names_the_first_problem_and_counts_the_rest(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / ".mmw").mkdir()
            cfg = dict(self.COMPLETE)
            cfg["start"] = ""
            cfg["leaves_machine"] = "browser"
            (Path(d) / ".mmw" / "target.json").write_text(json.dumps(cfg))
            code, out, _ = self.run_target("--validate", "--repo", d)
        self.assertEqual(code, 1)
        self.assertIn("start must be a non-empty command", out)
        self.assertIn("(+1 more)", out)

    def test_a_wrong_instance_shape_is_named(self):
        cfg = dict(self.COMPLETE)
        cfg["instance"] = {"max": 0}
        with tempfile.TemporaryDirectory() as d:
            problems = tc.target_problems(cfg, Path(d))
        self.assertEqual([k for k, _ in problems], ["instance"])

    def test_a_file_that_is_not_json_is_a_fault_not_absence(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / ".mmw").mkdir()
            (Path(d) / ".mmw" / "target.json").write_text("{bad")
            code, _, err = self.run_target("--check", "--repo", d)
        self.assertEqual(code, 2)
        self.assertIn("cannot be read as JSON", err)

    def test_stale_keys_are_reported_without_failing_a_complete_file(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / ".mmw").mkdir()
            (root / ".mmw" / "target.json").write_text(json.dumps(
                {**self.COMPLETE, "kind": "electron", "unknown": True}))
            code, out, _ = self.run_target("--check", "--repo", d)
        self.assertEqual(code, 0, out)
        self.assertIn("  stale  kind", out)
        self.assertIn("  stale  unknown", out)

    def test_the_runtime_refusal_names_the_check_command(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit) as raised:
                tc.target_config(Path(d))
        self.assertIn("target_config.py --check", str(raised.exception))

    def test_check_prints_no_gateway_rule(self):
        """`target_config.py --check` prints the rules block without Gateway."""
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = self.run_target("--check", "--repo", d)
        self.assertEqual(code, 1)
        self.assertNotIn("Gateway", out)
        self.assertIn("rules:", out)
        self.assertIn("automation uses placeholder keys, vendor stubs, and local accounts", out)
        self.assertIn("leaves_machine actions record under MMW_AUTOMATION=1", out)

    def test_harness_markers_is_required_as_a_list_of_strings(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / ".mmw").mkdir()
            (Path(d) / ".mmw" / "target.json").write_text("{}")
            code, out, _ = self.run_target("--check", "--repo", d)
            self.assertEqual(code, 1)
            self.assertIn("  missing  harness_markers (list of strings)", out)
            problems = tc.target_problems(
                {**self.COMPLETE, "harness_markers": "nope"}, Path(d))
            self.assertEqual([k for k, _ in problems], ["harness_markers"])
            leaves = tc.target_problems(
                {**self.COMPLETE, "leaves_machine": "nope"}, Path(d))
            self.assertEqual([k for k, _ in leaves], ["leaves_machine"])
            self.assertIn("[] when nothing leaves", leaves[0][1])

    def check_with_delivery(self, delivery=None, playbooks=()):
        """Write a complete `.mmw/target.json`, optionally with `delivery`, and
        one `.mmw/playbooks/<slug>.md` per slug, then run `--check`."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            books = root / ".mmw" / "playbooks"
            books.mkdir(parents=True)
            for slug in playbooks:
                (books / f"{slug}.md").write_text("# " + slug + "\n")
            cfg = dict(self.COMPLETE)
            if delivery is not None:
                cfg["delivery"] = delivery
            (root / ".mmw" / "target.json").write_text(json.dumps(cfg))
            return self.run_target("--check", "--repo", d)

    def test_delivery_absent_is_fine(self):
        code, out, _ = self.check_with_delivery()
        self.assertEqual(code, 0, out)
        self.assertIn("  absent   delivery (string, optional)", out)

    def test_delivery_commit_is_fine(self):
        code, out, _ = self.check_with_delivery(delivery="commit")
        self.assertEqual(code, 0, out)
        self.assertIn("  ok       delivery\n", out)

    def test_delivery_naming_an_existing_playbook_is_fine(self):
        code, out, _ = self.check_with_delivery(
            delivery="playbook:promote-a-change", playbooks=("promote-a-change",))
        self.assertEqual(code, 0, out)
        self.assertIn("  ok       delivery\n", out)

    def test_delivery_naming_a_missing_playbook_is_wrong(self):
        code, out, _ = self.check_with_delivery(
            delivery="playbook:promote-a-change", playbooks=("pull-an-upstream",))
        self.assertEqual(code, 1)
        self.assertIn(
            "  wrong    delivery (string) names .mmw/playbooks/promote-a-change.md", out)
        self.assertNotIn("  ok       delivery", out)

    def test_delivery_with_any_other_value_is_wrong(self):
        values = ("pr", "Commit", "playbook:", "playbook:../promote-a-change",
                  1, None, ["commit"])
        # These two would name a file outside `.mmw/playbooks/` if the slug
        # check were skipped. An empty directory still yields a `delivery`
        # problem from the missing-file branch, so the key alone cannot go red.
        escapes = ("playbook:", "playbook:../promote-a-change")
        with tempfile.TemporaryDirectory() as d:
            for value in values:
                with self.subTest(value=value):
                    problems = tc.target_problems(
                        {**self.COMPLETE, "delivery": value}, Path(d))
                    self.assertEqual([k for k, _ in problems], ["delivery"])
                    if value in escapes:
                        self.assertIn("lowercase words joined by hyphens", problems[0][1])
        code, out, _ = self.check_with_delivery(delivery="pr")
        self.assertEqual(code, 1)
        self.assertIn(
            "  wrong    delivery (string) must be `commit` or `playbook:<slug>`", out)


if __name__ == "__main__":
    unittest.main()
