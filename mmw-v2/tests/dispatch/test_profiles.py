"""profile_rows: unique ids for a fallback host, and only `bypass` rows become profiles.

    python3 -m unittest discover -s mmw-v2/tests/dispatch -p test_profiles.py
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2] / "skills" / "dispatch"
MODELS_PY = SKILL / "scripts" / "models.py"
_spec = importlib.util.spec_from_file_location("mmw_models", MODELS_PY)
models = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(models)

TABLE_HEAD = (
    "| agent | host | model | effort | permissions |\n"
    "| --- | --- | --- | --- | --- |\n"
)


def rows_from(text: str) -> list:
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
        fh.write("# Models\n\n" + TABLE_HEAD + text)
        path = Path(fh.name)
    previous = models.MODELS
    try:
        models.MODELS = path
        return models.profile_rows()
    finally:
        models.MODELS = previous
        path.unlink(missing_ok=True)


class ProfileRowsTest(unittest.TestCase):
    def test_two_bypass_rows_for_one_agent_do_not_share_a_profile_id(self):
        rows = rows_from(
            "| junior-worker | cursor | `grok-4.6` | high | bypass |\n"
            "| junior-worker | grok | `grok-4.6` | high | bypass |\n"
        )
        ids = [row.profile_id for row in rows]
        self.assertEqual(ids, ["junior-worker", "junior-worker@grok"])
        self.assertEqual(len(ids), len(set(ids)))
        by_id = {row.profile_id: row for row in rows}
        self.assertEqual(by_id["junior-worker"].host, "cursor")
        self.assertEqual(by_id["junior-worker@grok"].host, "grok")
        self.assertEqual(by_id["junior-worker"].agent, "junior-worker")
        self.assertEqual(by_id["junior-worker@grok"].agent, "junior-worker")

    def test_a_row_whose_permissions_are_not_bypass_makes_no_profile(self):
        rows = rows_from(
            "| reviewer | claude | `claude-opus-5` | high | bypass |\n"
            "| reviewer | claude | `claude-opus-5` | high | — |\n"
            "| reviewer | grok | `grok-4.6` | high | — |\n"
        )
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.profile_id, "reviewer")
        self.assertEqual(row.agent, "reviewer")
        self.assertEqual(row.host, "claude")
        self.assertEqual(row.permissions, "bypass")
        self.assertEqual(row.model, "claude-opus-5")
        self.assertEqual(row.effort, "high")

    def test_a_second_fallback_bypass_row_is_refused(self):
        with self.assertRaisesRegex(ValueError, "more than one fallback"):
            rows_from(
                "| junior-worker | cursor | `grok-4.6` | high | bypass |\n"
                "| junior-worker | grok | `grok-4.6` | high | bypass |\n"
                "| junior-worker | claude | `claude-opus-5` | high | bypass |\n"
            )

    def test_two_bypass_rows_on_the_same_host_are_refused(self):
        with self.assertRaisesRegex(ValueError, "two bypass rows on"):
            rows_from(
                "| junior-worker | cursor | `grok-4.6` | high | bypass |\n"
                "| junior-worker | cursor | `grok-4.6` | high | bypass |\n"
            )

    def test_the_live_table_gives_junior_worker_a_grok_fallback_and_advisor_one_row(self):
        previous = models.MODELS
        models.MODELS = SKILL / "models.md"
        self.addCleanup(setattr, models, "MODELS", previous)
        rows = models.profile_rows()
        ids = [row.profile_id for row in rows]
        self.assertEqual(len(ids), len(set(ids)), ids)
        by_id = {row.profile_id: row for row in rows}
        self.assertEqual(by_id["junior-worker"].host, "cursor")
        self.assertEqual(by_id["junior-worker@grok"].host, "grok")
        self.assertEqual(by_id["junior-worker@grok"].model, "grok-4.6")
        self.assertEqual(by_id["junior-worker@grok"].effort, "high")
        advisor = [row for row in rows if row.agent == "advisor"]
        self.assertEqual(len(advisor), 1)
        self.assertEqual(advisor[0].profile_id, "advisor")
        self.assertEqual(advisor[0].host, "claude")
        parsed = models.parse_model_rows()
        advisor_rows = [row for row in parsed if row[0] == "advisor"]
        self.assertEqual([(row[1], row[4]) for row in advisor_rows], [("claude", "bypass")])


if __name__ == "__main__":
    unittest.main()
