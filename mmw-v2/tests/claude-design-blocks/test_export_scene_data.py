"""Export each scene's data from a miniature handoff package.

The script is the seam: a real `src/*.py` + `data/fixtures.js` + `scenes.json`,
Node running the page LOGIC, no browser. State arrives only from those files.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "claude-design-blocks"
    / "scripts"
    / "export_scene_data.py"
)
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "handoff"


def export(handoff: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(handoff)],
        capture_output=True,
        text=True,
    )


class ExportSceneData(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.handoff = Path(self.tmp.name) / "h"
        shutil.copytree(FIXTURE, self.handoff)
        self.addCleanup(self.tmp.cleanup)

    def scenes(self):
        return json.loads((self.handoff / "scenes.json").read_text(encoding="utf-8"))

    def test_four_scenes_get_data_including_the_window_listener_page(self):
        result = export(self.handoff)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("exported 4/4 scenes", result.stdout)
        rows = self.scenes()
        self.assertEqual(len(rows), 4)
        by_name = {row["name"]: row for row in rows}
        for name in ("list.ready", "list.empty", "canvas.idle", "canvas.dragging"):
            data = by_name[name]["data"]
            self.assertIsNotNone(data["vals"])
            self.assertIn("state", data)
            self.assertTrue(data["state"]["fx"])
            self.assertTrue(data["vals"]["fx"])
        ready = by_name["list.ready"]["data"]
        self.assertEqual(len(ready["state"]["items"]), 2)
        self.assertTrue(ready["state"]["ready"])
        self.assertEqual(ready["vals"]["count"], 2)
        self.assertEqual(ready["vals"]["title"], "Ready")
        self.assertTrue(ready["vals"]["ready"])
        self.assertEqual(by_name["list.empty"]["data"]["vals"]["count"], 0)
        self.assertEqual(by_name["canvas.idle"]["data"]["vals"]["label"], "Board")
        self.assertEqual(by_name["canvas.dragging"]["data"]["vals"]["scene"], "dragging")

    def test_functions_are_stripped_from_vals(self):
        result = export(self.handoff)
        self.assertEqual(result.returncode, 0, result.stderr)
        ready = next(row for row in self.scenes() if row["name"] == "list.ready")
        self.assertNotIn("pick", ready["data"]["vals"])
        self.assertEqual(ready["data"]["vals"]["items"][0]["name"], "Alpha")

    def test_standalone_scene_is_named_and_refused(self):
        shutil.copyfile(
            self.handoff / "scenes.standalone.json",
            self.handoff / "scenes.json",
        )
        result = export(self.handoff)
        self.assertEqual(result.returncode, 2)
        self.assertIn("list.empty", result.stdout + result.stderr)
        for row in self.scenes():
            self.assertNotIn("data", row)

    def test_page_prop_defaults_fill_a_scene_that_omits_them(self):
        rows = self.scenes()
        idle = next(row for row in rows if row["name"] == "canvas.idle")
        idle["props"] = {}
        (self.handoff / "scenes.json").write_text(
            json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        result = export(self.handoff)
        self.assertEqual(result.returncode, 0, result.stderr)
        idle = next(row for row in self.scenes() if row["name"] == "canvas.idle")
        self.assertEqual(idle["data"]["vals"]["scene"], "idle")

    def test_a_failed_scene_is_named_and_exits_1(self):
        src = self.handoff / "src" / "Component · list.py"
        src.write_text(
            src.read_text(encoding="utf-8").replace(
                "this.setState({ items, ready: true });",
                'throw new Error("boom-list");',
            ),
            encoding="utf-8",
        )
        result = export(self.handoff)
        self.assertEqual(result.returncode, 1)
        combined = result.stdout + result.stderr
        self.assertIn("list.ready", combined)
        self.assertIn("boom-list", combined.splitlines()[-1])


if __name__ == "__main__":
    unittest.main()
