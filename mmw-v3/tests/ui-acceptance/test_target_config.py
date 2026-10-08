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


def write_product_layout(root: Path, *, products=("gateway", "parrot"), ports=(7, 3),
                         needs=None):
    """A new-layout repository: root `checks`, `products`, `needs`, and one file per product."""
    mmw = root / ".mmw"
    mmw.mkdir()
    (mmw / "target.json").write_text(json.dumps({
        "checks": ["echo ok"],
        "products": list(products),
        "needs": {"parrot": ["gateway"]} if needs is None else needs,
    }))
    discovers = {
        "gateway": "gateway-discover",
        "parrot": "parrot-discover",
        "hedgehog": "hedgehog-discover",
    }
    for name, count in zip(products, ports):
        (mmw / name).mkdir()
        (mmw / name / "target.json").write_text(json.dumps({
            "ports": count,
            "discover": discovers[name],
        }))


def write_product_layout_ports(root: Path, ports: dict):
    """Replace each product's `ports`, leaving the root and the other keys."""
    for name, count in ports.items():
        path = root / ".mmw" / name / "target.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["ports"] = count
        path.write_text(json.dumps(payload))


class TestTargetCheck(unittest.TestCase):
    """`target_config.py --check` is the setup-time bar for one repository: it
    names every field of `.mmw/target.json` still to answer, and passes once the file
    is complete. The runtime reader `target_config` keeps its smaller bar."""

    def test_a_product_config_is_read_from_its_directory(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            write_product_layout(root)
            gateway = tc.read_target_json(root, product="gateway")
            parrot = tc.read_target_json(root, product="parrot")
            self.assertEqual(gateway["discover"], "gateway-discover")
            self.assertEqual(parrot["discover"], "parrot-discover")
            self.assertEqual(parrot["ports"], 3)
            self.assertEqual(gateway.root["checks"], ["echo ok"])
            self.assertEqual(gateway.root["products"], ["gateway", "parrot"])
            self.assertEqual(gateway.root["needs"], {"parrot": ["gateway"]})
            self.assertEqual(set(gateway.root), {"checks", "products", "needs"})
            code, out, err = self.run_target("--check", "--repo", d)
            self.assertEqual(code, 0, out + err)
            code, out, err = self.run_target("--check", "--repo", d, "--product", "parrot")
            self.assertEqual(code, 0, out + err)
            code, out, err = self.run_target("--check", "--repo", d, "--product", "billing")
            self.assertNotEqual(code, 0, out + err)
            self.assertIn("billing", out + err)
            payload = {
                "checks": ["echo ok"],
                "products": ["gateway", "parrot"],
                "needs": {"parrot": ["gateway"]},
                "kind": "web",
            }
            (root / ".mmw" / "target.json").write_text(json.dumps(payload))
            code, out, err = self.run_target("--check", "--repo", d)
            self.assertNotEqual(code, 0, out + err)
            self.assertIn("kind", out + err)
            payload.pop("kind")
            (root / ".mmw" / "target.json").write_text(json.dumps(payload))
            (root / ".mmw" / "parrot" / "target.json").unlink()
            code, out, err = self.run_target("--check", "--repo", d)
            self.assertNotEqual(code, 0, out + err)
            self.assertIn(".mmw/parrot/target.json", out + err)

    def test_ports_beyond_the_block_are_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            write_product_layout(root, ports=(10, 10))
            code, out, err = self.run_target("--check", "--repo", d)
            self.assertEqual(code, 0, out + err)
            write_product_layout_ports(root, {"gateway": 11, "parrot": 10})
            code, out, err = self.run_target("--check", "--repo", d)
            text = out + err
            self.assertNotEqual(code, 0, text)
            self.assertIn("gateway 11", text)
            self.assertIn("parrot 10", text)
            self.assertIn("at most 20", text)
            write_product_layout_ports(root, {"gateway": "many", "parrot": 3})
            code, out, err = self.run_target("--check", "--repo", d)
            text = out + err
            self.assertNotEqual(code, 0, text)
            self.assertIn("gateway", text)
            self.assertIn("many", text)

    def test_needs_must_name_listed_products(self):
        with tempfile.TemporaryDirectory() as d:
            write_product_layout(Path(d), needs={"parrot": ["billing"]})
            code, out, err = self.run_target("--check", "--repo", d)
            text = out + err
            self.assertNotEqual(code, 0, text)
            self.assertIn("billing", text)
        with tempfile.TemporaryDirectory() as d:
            write_product_layout(
                Path(d),
                products=("gateway", "parrot", "hedgehog"),
                ports=(3, 3, 3),
                needs={"parrot": ["gateway"], "gateway": ["parrot"]},
            )
            code, out, err = self.run_target("--check", "--repo", d)
            text = out + err
            self.assertNotEqual(code, 0, text)
            self.assertIn("gateway", text)
            self.assertIn("parrot", text)
            self.assertNotIn("hedgehog", text)

    def test_one_product_is_read_without_a_name_and_a_bad_file_is_a_problem(self):
        """One product needs no `--product`. A product file that is not JSON is one problem line."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            write_product_layout(root, products=("gateway",), ports=(3,), needs={})
            cfg = tc.read_target_json(root)
            self.assertEqual(cfg.name, "gateway")
            self.assertEqual(cfg["discover"], "gateway-discover")
            self.assertEqual(cfg.root["checks"], ["echo ok"])
            code, out, err = self.run_target("--check", "--repo", d)
            self.assertEqual(code, 0, out + err)
            (root / ".mmw" / "gateway" / "target.json").write_text("{")
            code, out, err = self.run_target("--check", "--repo", d)
            self.assertEqual(code, 1, out + err)
            self.assertIn(".mmw/gateway/target.json", out + err)

    def test_a_name_on_the_old_layout_is_refused(self):
        """The old layout has no named product, so `--product` cannot select one."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / ".mmw").mkdir()
            (root / ".mmw" / "target.json").write_text(json.dumps(self.COMPLETE))
            code, out, err = self.run_target("--check", "--repo", d, "--product", "nonesuch")
            text = out + err
            self.assertNotEqual(code, 0, text)
            self.assertIn("nonesuch", text)

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
        problems = tc.target_problems({**self.COMPLETE, "harness_markers": "nope"})
        self.assertEqual([k for k, _ in problems], ["harness_markers"])
        leaves = tc.target_problems({**self.COMPLETE, "leaves_machine": "nope"})
        self.assertEqual([k for k, _ in leaves], ["leaves_machine"])
        self.assertIn("[] when nothing leaves", leaves[0][1])


if __name__ == "__main__":
    unittest.main()
