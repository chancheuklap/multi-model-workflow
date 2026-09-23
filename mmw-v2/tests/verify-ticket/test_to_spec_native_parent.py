"""The to-spec prompt contract for map versus standalone native parent.

The test reads the skill text, the Tickets context and the to-spec merge-note. It
writes no tracker state. The create-and-readback sequence it requires is the same
GitHub `--parent` flow `to-tickets` already tells the agent to use.

    python3 -m unittest discover -s mmw-v2/tests/verify-ticket -p test_to_spec_native_parent.py
"""

import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MMW = HERE.parents[1]
ROOT = HERE.parents[2]
SKILL = MMW / "upstream" / "skills" / "engineering" / "to-spec" / "SKILL.md"
TICKETS = ROOT / "docs" / "contexts" / "tickets" / "CONTEXT.md"
MERGE_NOTE = MMW / "merge-notes" / "to-spec.md"
DOCS_PAGE = MMW / "upstream" / "docs" / "engineering" / "to-spec.md"


def words(text: str) -> str:
    return " ".join(text.split())


class ToSpecNativeParent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = SKILL.read_text()
        cls.tickets = TICKETS.read_text()
        cls.merge_note = MERGE_NOTE.read_text()
        cls.docs_page = DOCS_PAGE.read_text()
        cls.skill_words = words(cls.skill)

    def test_every_spec_from_the_map_is_parented_not_only_the_first(self):
        self.assertIn("publish each spec from that map", self.skill_words)
        process = self.skill.split("<spec-template>", 1)[0]
        self.assertIn("one spec or several", process)
        self.assertIn("## Specs", process)

    def test_native_parent_rules_live_in_the_skill_and_the_glossary_only_defines(self):
        for rule in ("parent.number", "semantic similarity", "native sub-issue of the map"):
            self.assertIn(rule, self.skill)
        spec = self.tickets.split("**spec**:", 1)[1].split("_Home_:", 1)[0]
        self.assertIn("native sub-issue of that map", spec)
        mapping = self.tickets.split("**map**:", 1)[1].split("_Home_:", 1)[0]
        self.assertIn("specs published from it", mapping)

    def test_the_merge_note_records_the_native_parent_prompt(self):
        self.assertIn("native parent", self.merge_note)
        self.assertIn("parent.number", self.merge_note)
        self.assertIn("gh issue create --parent", self.merge_note)
        self.assertIn("do not invent a map parent", self.merge_note)

    def test_the_promoted_docs_page_explains_map_and_standalone_parentage(self):
        self.assertIn("created as the map's native sub-issue", self.docs_page)
        self.assertIn("read back before completion is reported", self.docs_page)
        self.assertIn("standalone spec has no invented map parent", self.docs_page)


if __name__ == "__main__":
    unittest.main()
