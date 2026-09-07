"""profile_rows: unique ids for a fallback host, advisor's two same-host rows untouched.

    python3 -m unittest discover -s mmw-v2/tests/dispatch -p test_profiles.py
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ASSEMBLE_PATH = Path(__file__).resolve().parents[2] / "agents" / "assemble.py"
_spec = importlib.util.spec_from_file_location("mmw_assemble", ASSEMBLE_PATH)
assemble = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(assemble)

TABLE_HEAD = (
    "| agent | host | model | effort | permissions |\n"
    "| --- | --- | --- | --- | --- |\n"
)


def rows_from(text: str) -> list[tuple[str, str, str, str, str, str]]:
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
        fh.write("# Models\n\n" + TABLE_HEAD + text)
        path = Path(fh.name)
    previous = assemble.MODELS
    try:
        assemble.MODELS = path
        return assemble.profile_rows()
    finally:
        assemble.MODELS = previous
        path.unlink(missing_ok=True)


class ProfileRowsTest(unittest.TestCase):
    def test_two_bypass_rows_for_one_agent_do_not_share_a_profile_id(self):
        rows = rows_from(
            "| junior-worker | cursor | `grok-4.6` | high | bypass |\n"
            "| junior-worker | grok | `grok-4.6` | high | bypass |\n"
        )
        ids = [row[0] for row in rows]
        self.assertEqual(ids, ["junior-worker", "junior-worker@grok"])
        self.assertEqual(len(ids), len(set(ids)))
        by_id = {row[0]: row for row in rows}
        self.assertEqual(by_id["junior-worker"][2], "cursor")
        self.assertEqual(by_id["junior-worker@grok"][2], "grok")
        self.assertEqual(by_id["junior-worker"][1], "junior-worker")
        self.assertEqual(by_id["junior-worker@grok"][1], "junior-worker")

    def test_advisor_bypass_and_native_on_the_same_host_still_make_one_profile(self):
        rows = rows_from(
            "| advisor | claude | `claude-fable-5-1` | medium | bypass |\n"
            "| advisor | claude | `claude-fable-5-1` | medium | — |\n"
            "| advisor | grok | `grok-4.6` | xhigh | — |\n"
        )
        self.assertEqual(len(rows), 1)
        profile_id, agent, host, model, effort, permissions = rows[0]
        self.assertEqual(profile_id, "advisor")
        self.assertEqual(agent, "advisor")
        self.assertEqual(host, "claude")
        self.assertEqual(permissions, "bypass")
        self.assertEqual(model, "claude-fable-5-1")
        self.assertEqual(effort, "medium")

    def test_a_second_fallback_bypass_row_is_refused(self):
        with self.assertRaises(ValueError):
            rows_from(
                "| junior-worker | cursor | `grok-4.6` | high | bypass |\n"
                "| junior-worker | grok | `grok-4.6` | high | bypass |\n"
                "| junior-worker | claude | `claude-opus-5` | high | bypass |\n"
            )

    def test_two_bypass_rows_on_the_same_host_are_refused(self):
        with self.assertRaises(ValueError):
            rows_from(
                "| junior-worker | cursor | `grok-4.6` | high | bypass |\n"
                "| junior-worker | cursor | `grok-4.6` | high | bypass |\n"
            )

    def test_the_live_table_gives_junior_worker_a_grok_fallback_and_leaves_advisor(self):
        assemble.MODELS = ASSEMBLE_PATH.parent.parent / "skills" / "dispatch" / "models.md"
        rows = assemble.profile_rows()
        ids = [row[0] for row in rows]
        self.assertEqual(len(ids), len(set(ids)), ids)
        by_id = {row[0]: row for row in rows}
        self.assertEqual(by_id["junior-worker"][2], "cursor")
        self.assertEqual(by_id["junior-worker@grok"][2], "grok")
        self.assertEqual(by_id["junior-worker@grok"][3], "grok-4.6")
        self.assertEqual(by_id["junior-worker@grok"][4], "high")
        advisor = [row for row in rows if row[1] == "advisor"]
        self.assertEqual(len(advisor), 1)
        self.assertEqual(advisor[0][0], "advisor")
        self.assertEqual(advisor[0][2], "claude")
        parsed = assemble.parse_model_rows()
        advisor_claude = [row for row in parsed if row[0] == "advisor" and row[1] == "claude"]
        self.assertEqual({row[4] for row in advisor_claude}, {"bypass", "—"})


if __name__ == "__main__":
    unittest.main()
