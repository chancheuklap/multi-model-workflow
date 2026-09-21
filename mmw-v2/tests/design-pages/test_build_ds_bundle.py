"""build_ds_bundle.py: components become `window.<Namespace>.<Name>` in one classic script.

The bundle is loaded in Node with a stand-in `window` and a React stand-in that is set
only after the bundle has run, the order the page runtime loads them in.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "design-pages" / "scripts" / "build_ds_bundle.py"

PROBE = """
global.window = {};
require(process.argv[1]);
window.React = {createElement: (type, props, ...kids) => ({type, props, kids})};
const ns = window.Board_ab12;
console.log(JSON.stringify({names: Object.keys(ns).sort(), lamp: ns.Lamp({tone: "orange", "data-ui": "x.lamp"})}));
"""


class BuildBundle(unittest.TestCase):
    def setUp(self):
        if not shutil.which("npx") or not shutil.which("node"):
            self.fail("node and npx are required")
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        status = self.root / "components" / "status"
        status.mkdir(parents=True)
        (status / "Lamp.jsx").write_text(
            'import React from "react";\n'
            'export function Lamp({tone, ...rest}) { return <span className={"lamp " + tone} {...rest}></span>; }\n')
        (status / "Pill.jsx").write_text(
            'import React from "react";\nexport function Pill({phase}) { return <span className={"pill " + phase}>{phase}</span>; }\n')
        (status / "helpers.jsx").write_text("export const notAComponent = 1;\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_bundle_exposes_components_and_reads_react_late(self):
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.root), "--namespace", "Board_ab12"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("bundled 2 components into", result.stdout)
        bundle = self.root / "_ds_bundle.js"
        header = json.loads(bundle.read_text().split("\n", 1)[0][len("/* @ds-bundle: "):-len(" */")])
        self.assertEqual(header["namespace"], "Board_ab12")
        self.assertEqual(header["components"], ["Lamp", "Pill"])
        probe = subprocess.run(["node", "-e", PROBE, str(bundle)], capture_output=True, text=True)
        self.assertEqual(probe.returncode, 0, probe.stderr)
        out = json.loads(probe.stdout)
        self.assertEqual(out["names"], ["Lamp", "Pill"])
        self.assertEqual(out["lamp"]["type"], "span")
        self.assertEqual(out["lamp"]["props"]["className"], "lamp orange")
        self.assertEqual(out["lamp"]["props"]["data-ui"], "x.lamp")

    def test_bad_namespace_and_empty_directory(self):
        bad = subprocess.run([sys.executable, str(SCRIPT), str(self.root), "--namespace", "a-b"], capture_output=True, text=True)
        self.assertEqual(bad.returncode, 2)
        empty = tempfile.mkdtemp()
        none = subprocess.run([sys.executable, str(SCRIPT), empty, "--namespace", "A"], capture_output=True, text=True)
        self.assertEqual(none.returncode, 2)
        shutil.rmtree(empty)


if __name__ == "__main__":
    unittest.main()
