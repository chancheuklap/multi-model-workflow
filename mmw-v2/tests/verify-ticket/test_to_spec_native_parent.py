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

MAP_INSTRUCTION = """
When the reference is a wayfinder map and the tracker is GitHub, publish each
spec from that map as a native sub-issue of the map. Create the spec with
`gh issue create --parent <map>`, then read the created issue back and require
its native `parent.number` to equal the map number before reporting the publish
as complete. A missing or different native parent is a failed publish and is
corrected before the spec is handed on. `## Sources`, `## Further Notes`, the
spec title, and semantic similarity do not replace the native parent.
""".strip()

STANDALONE_INSTRUCTION = """
When the reference is not a wayfinder map, do not invent a map parent. A spec
from the conversation, a file, a standalone issue, or another non-map source
remains parentless at the map layer unless that source already supplies a
native parent.
""".strip()

OTHER_TRACKERS = (
    "Other trackers keep using their native sub-issue relationship; "
    "do not add a custom Parent field or a second task-root metadata store."
)


def words(text: str) -> str:
    return " ".join(text.split())


class ToSpecNativeParent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = SKILL.read_text()
        cls.tickets = TICKETS.read_text()
        cls.merge_note = MERGE_NOTE.read_text()
        cls.skill_words = words(cls.skill)

    def test_the_map_instruction_is_present_complete_and_in_order(self):
        self.assertIn(words(MAP_INSTRUCTION), self.skill_words)

    def test_the_standalone_instruction_is_present_complete_and_follows_the_map_one(self):
        self.assertIn(words(STANDALONE_INSTRUCTION), self.skill_words)
        self.assertLess(
            self.skill_words.index(words(MAP_INSTRUCTION)),
            self.skill_words.index(words(STANDALONE_INSTRUCTION)),
        )

    def test_create_readback_correction_and_human_readable_fields_stay_in_that_order(self):
        block = words(MAP_INSTRUCTION)
        self.assertIn(block, self.skill_words)
        markers = [
            "gh issue create --parent <map>",
            "parent.number",
            "failed publish",
            "corrected before the spec is handed on",
            "`## Sources`",
            "`## Further Notes`",
            "spec title",
            "semantic similarity do not replace the native parent",
        ]
        found = [block.index(marker) for marker in markers]
        self.assertEqual(found, sorted(found))

    def test_every_spec_from_the_map_is_parented_not_only_the_first(self):
        self.assertIn("publish each spec from that map", self.skill_words)
        process = self.skill.split("<spec-template>", 1)[0]
        self.assertIn("one spec or several", process)
        self.assertIn("## Specs", process)

    def test_other_trackers_keep_native_sub_issues_and_gain_no_second_store(self):
        self.assertIn(words(OTHER_TRACKERS), self.skill_words)
        self.assertLess(
            self.skill_words.index(words(STANDALONE_INSTRUCTION)),
            self.skill_words.index(words(OTHER_TRACKERS)),
        )

    def test_tickets_context_keeps_native_parent_as_the_only_machine_ownership(self):
        spec = self.tickets.split("**spec**:", 1)[1].split("_Admitted_:", 1)[0]
        self.assertIn("native sub-issue of that map", spec)
        self.assertIn("parent.number", spec)
        self.assertIn("no map parent", spec)
        self.assertIn("`## Sources`", spec)
        self.assertIn("semantic similarity", spec)
        self.assertNotIn("A top-level issue that holds a batch of tickets", spec)

        mapping = self.tickets.split("**map**:", 1)[1].split("_Admitted_:", 1)[0]
        self.assertIn("native sub-issue", mapping)

        sub = self.tickets.split("**sub-issue**:", 1)[1].split("_Admitted_:", 1)[0]
        self.assertIn("native sub-issue of the map", sub)
        self.assertIn("only machine ownership", sub)

    def test_the_merge_note_records_the_native_parent_prompt(self):
        self.assertIn("native parent", self.merge_note)
        self.assertIn("parent.number", self.merge_note)
        self.assertIn("gh issue create --parent", self.merge_note)
        self.assertIn("do not invent a map parent", self.merge_note)


if __name__ == "__main__":
    unittest.main()
