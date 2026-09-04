"""The screen-contract rules: what `--lint` reports under `[screen-contract]`, and the
closeout refusal when the Spec axis reported a `Missing` against a row the draft ignores.
"""

import os
import tempfile
import unittest

from tests._load import load

vt = load()

WIRING = ("uv run ~/.agents/skills/verify-ticket/scripts/wiring-check.py --contract "
          "docs/specs/x/screen-contract.yaml --rows create-project.add-material")
PARITY = ("uv run ~/.agents/skills/verify-ticket/scripts/visual-parity.py --contract "
          "docs/specs/x/screen-contract.yaml --mount create-project")


def gate(gate_id, check):
    return (f"- [ ] {gate_id}: something a stranger could judge\n"
            f"  CHECK: {check}\n  EXPECT: /^OK$/m\n  EVIDENCE: pending")


def ticket(read_first, *criteria, parent="", blocked_by=""):
    body = ""
    if parent:
        body += "## Parent\n\n" + parent + "\n\n"
    body += ("## Read first\n\n" + read_first + "\n\n## Acceptance criteria\n\n"
             + "\n".join(criteria) + "\n")
    if blocked_by:
        body += "\n## Blocked by\n\n" + blocked_by + "\n"
    return body


ROWS = "- docs/specs/x/screen-contract.yaml rows: create-project.add-material (baseline)"

CONTRACT = """
target: {kind: electron, adapter: verify-ticket/references/targets/electron.md}
viewports: [1440x900]
pages:
  "Component · 新建商品项目.dc.html": {mount: create-project, route: '#/new-project', component: cp}
  "Component · 壳头.dc.html": {mount: shell-header, route: '#/', component: sh}
mechanisms:
  seed:library-ready: {via: api, built_by: '#637'}
  seed:draft-existing: {via: storage, built_by: '#639', proven_by: '#639 AC4'}
scenes:
  empty: {page: "Component · 新建商品项目.dc.html", reach: [seed:library-ready]}
  material-added: {page: "Component · 新建商品项目.dc.html", reach: [seed:draft-existing]}
  shell-header.ready: {page: "Component · 壳头.dc.html", reach: [seed:library-ready]}
rows:
- id: create-project.add-material
  component: cp
  calls: ['POST /x']
  reach: seed:library-ready
  source: ['#537 story 2', '#537 Implementation Decisions 2', 'ADR-0021', '#420', 'docs/context/chameleon-product.md 新建商品项目', 'README §4.1']
- id: create-project.name
  component: cp
  calls: [none]
  reach: seed:library-ready
  source: ['#537 Testing Decisions']
- id: shell.sign-in
  component: sh
  calls: ['ipc x']
  reach: seed:library-ready
  source: ['#536 Implementation Decisions 3']
"""


class TestLintScreenContract(unittest.TestCase):
    """The four original rules, against a contract that is on disk."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        path = os.path.join(self.dir.name, "screen-contract.yaml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(CONTRACT)
        self.rows = f"- `{path} rows: create-project.add-material`（基线）\n- `docs/adr/chameleon/0021-x.md`\n- #420\n- `docs/context/chameleon-product.md`"
        self.parent = "[Spec（#537）](u)，Implementation Decisions 第 2 节"
        self.wiring = WIRING.replace("docs/specs/x/screen-contract.yaml", path)
        self.parity = PARITY.replace("docs/specs/x/screen-contract.yaml", path)

    def tearDown(self):
        self.dir.cleanup()

    def lint(self, *criteria):
        return vt.lint_screen_contract(ticket(self.rows, *criteria, parent=self.parent,
                                              blocked_by="- #637"), 639)
    def test_an_interface_ticket_without_row_ids_is_an_error(self):
        findings = vt.lint_screen_contract(ticket("- README (baseline)", gate("AC1", PARITY)))
        self.assertEqual(len(findings), 1)
        self.assertIn("names no", findings[0])

    def test_a_row_with_calls_needs_a_wiring_criterion(self):
        findings = self.lint(gate("AC1", self.parity))
        self.assertEqual(len(findings), 1)
        self.assertIn("create-project.add-material", findings[0])
        self.assertIn("wiring-check.py", findings[0])

    def test_a_wiring_criterion_naming_the_row_satisfies_it(self):
        self.assertEqual(self.lint(gate("AC1", self.parity), gate("AC2", self.wiring)), [])

    def test_a_check_that_stubs_fetch_is_an_error(self):
        stubbed = "pnpm vitest run src/__tests__/live.spec.ts  # vi.stubGlobal('fetch', ...)"
        findings = self.lint(gate("AC1", self.wiring), gate("AC2", stubbed))
        self.assertEqual(len(findings), 1)
        self.assertIn("AC2", findings[0])

    def test_a_ticket_without_interface_or_rows_has_nothing_to_say(self):
        self.assertEqual(vt.lint_screen_contract(ticket("- ADR-0013 (baseline)", gate("AC1", "pytest -q"))), [])


class TestPipelineFlags(unittest.TestCase):
    """The two pipeline scripts are given what they need, nothing they retired, and
    nothing their `--help` does not list — the one check that catches a criterion
    naming a capability that does not exist at the moment it is written."""

    def test_visual_parity_without_contract_or_mount(self):
        bare = "uv run ~/.agents/skills/verify-ticket/scripts/visual-parity.py --scenes a"
        findings = vt.lint_pipeline_flags("AC1", bare)
        self.assertTrue(any("without --contract" in f for f in findings))
        self.assertTrue(any("without --mount" in f for f in findings))

    def test_wiring_check_without_rows(self):
        findings = vt.lint_pipeline_flags(
            "AC2", "uv run ~/.agents/skills/verify-ticket/scripts/wiring-check.py --contract c.yaml")
        self.assertEqual(len(findings), 1)
        self.assertIn("without --rows", findings[0])

    def test_an_address_on_the_line_is_refused(self):
        stale = PARITY + " --cdp http://127.0.0.1:9229 --impl http://127.0.0.1:5173/"
        findings = vt.lint_pipeline_flags("AC1", stale)
        self.assertEqual(len(findings), 2)
        self.assertTrue(all(".mmw/target.json" in f for f in findings))

    def test_a_flag_help_does_not_list_is_refused(self):
        findings = vt.lint_pipeline_flags("AC1", PARITY + " --reach-hook x")
        self.assertEqual(len(findings), 1)
        self.assertIn("--reach-hook", findings[0])
        self.assertIn("--help", findings[0])

    def test_the_seed_belongs_to_the_contract_now(self):
        findings = vt.lint_pipeline_flags("AC1", WIRING + ' --seed "uv run reach.py seed:x"')
        self.assertEqual(len(findings), 1)
        self.assertIn("--seed", findings[0])

    def test_only_the_scripts_own_segment_is_read(self):
        chained = ("uv run python scripts/testing/reach.py seed:x --perturb && " + PARITY)
        self.assertEqual(vt.lint_pipeline_flags("AC1", chained), [])
        self.assertEqual(vt.script_segment(chained, "visual-parity.py"),
                         " --contract docs/specs/x/screen-contract.yaml --mount create-project")


class TestParentSections(unittest.TestCase):
    def test_chinese_shape(self):
        parsed = vt.parent_sections(
            "[Spec（#537）](u)，Implementation Decisions 第 2、9、11 节，User Stories 第 1、2 条；"
            "[Spec（#536）](u)，Implementation Decisions 第 13 节与 Testing Decisions")
        self.assertEqual(parsed[537]["sections"], {2, 9, 11})
        self.assertFalse(parsed[537]["testing"])
        self.assertEqual(parsed[536]["sections"], {13})
        self.assertTrue(parsed[536]["testing"])

    def test_english_shape(self):
        parsed = vt.parent_sections("#535, Implementation Decisions sections 5 and 7")
        self.assertEqual(parsed[535]["sections"], {5, 7})




class TestSourcesAndMechanisms(unittest.TestCase):
    """What a worker cannot see does not exist: every baseline-class source of an owned
    row is under `## Read first`, every spec section under `## Parent`, and every
    mechanism used is built by a ticket this one is blocked by."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "screen-contract.yaml")
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(CONTRACT)
        self.rows = (f"- `{self.path} rows: create-project.add-material, create-project.name`"
                     "（基线）")
        self.wiring = WIRING.replace("docs/specs/x/screen-contract.yaml", self.path)
        self.parity = PARITY.replace("docs/specs/x/screen-contract.yaml", self.path)

    def tearDown(self):
        self.dir.cleanup()

    def _lint(self, read_first_extra="", parent="", blocked_by="- #637", number=639):
        body = ticket(self.rows + "\n" + read_first_extra, gate("AC1", self.parity),
                      gate("AC2", self.wiring), parent=parent, blocked_by=blocked_by)
        return vt.lint_screen_contract(body, number)

    def test_every_missing_source_is_named_once(self):
        findings = self._lint()
        self.assertTrue(any("ADR-0021" in f for f in findings))
        self.assertTrue(any("#420" in f for f in findings))
        self.assertTrue(any("docs/context/chameleon-product.md" in f for f in findings))
        self.assertTrue(any("Implementation Decisions section 2" in f for f in findings))
        self.assertTrue(any("Testing Decisions" in f for f in findings))
        self.assertFalse(any("story" in f for f in findings))
        self.assertFalse(any("README" in f for f in findings))

    def test_sources_in_read_first_and_parent_are_satisfied(self):
        extra = ("- `docs/adr/chameleon/0021-chameleon-two-gates.md`（基线）\n"
                 "- [两道门（#420）](u)（基线）\n- `docs/context/chameleon-product.md`——正名")
        parent = "[Spec（#537）](u)，Implementation Decisions 第 2 节与 Testing Decisions"
        self.assertEqual(self._lint(extra, parent), [])

    def test_a_mechanism_built_elsewhere_needs_the_blocking_link(self):
        findings = self._lint(blocked_by="None (can start immediately)")
        self.assertTrue(any("seed:library-ready is built by #637" in f for f in findings))

    def test_the_building_ticket_is_not_blocked_by_itself(self):
        findings = self._lint(blocked_by="None (can start immediately)", number=637)
        self.assertFalse(any("built by #637" in f for f in findings))

    def test_a_scene_reached_under_the_mount_counts_as_used(self):
        # material-added is under mount create-project and reaches seed:draft-existing (#639)
        findings = self._lint(blocked_by="- #637", number=640)
        self.assertTrue(any("seed:draft-existing is built by #639" in f for f in findings))

    def test_explicit_scenes_stay_inside_the_mount(self):
        body = ticket(self.rows, gate("AC1", self.parity + " --scenes empty,shell-header.ready"),
                      gate("AC2", self.wiring), blocked_by="- #637")
        findings = vt.lint_screen_contract(body, 639)
        self.assertTrue(any("outside its mounts: shell-header.ready" in f for f in findings))

    def test_an_unknown_mount_is_named(self):
        body = ticket(self.rows, gate("AC1", self.parity.replace("create-project", "nowhere")),
                      gate("AC2", self.wiring), blocked_by="- #637")
        findings = vt.lint_screen_contract(body, 639)
        self.assertTrue(any("--mount nowhere" in f for f in findings))


class TestScenePartition(unittest.TestCase):
    """Across the batch: every scene once, and every mount owned."""

    def setUp(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            f.write(CONTRACT)
        self.doc = vt.load_yaml_file(f.name)
        os.unlink(f.name)

    def body(self, mounts, scenes=None):
        check = PARITY.replace("--mount create-project", f"--mount {mounts}")
        if scenes:
            check += f" --scenes {scenes}"
        return ticket(ROWS, gate("AC1", check))

    def test_a_clean_partition_has_no_findings(self):
        bodies = {1: self.body("create-project"), 2: self.body("shell-header")}
        self.assertEqual(vt.lint_scene_partition(bodies, self.doc), [])

    def test_a_page_split_by_explicit_scenes(self):
        bodies = {1: self.body("create-project", "empty"),
                  2: self.body("create-project", "material-added"),
                  3: self.body("shell-header")}
        self.assertEqual(vt.lint_scene_partition(bodies, self.doc), [])

    def test_an_uncovered_scene_and_a_doubly_covered_one(self):
        bodies = {1: self.body("create-project", "empty"), 2: self.body("create-project")}
        findings = vt.lint_scene_partition(bodies, self.doc)
        self.assertTrue(any("shell-header.ready is covered by no ticket" in f for f in findings))
        self.assertTrue(any("empty is covered by more than one ticket" in f for f in findings))
        self.assertTrue(any("mount shell-header is owned by no ticket" in f for f in findings))


REVIEW = ("REVIEW abc..def\n\n## Standards\n\nnone\n\n## Spec\n\n### Missing\n\n"
          "1. **create-project.add-material calls nothing.** The button toggles a boolean.\n\n"
          "## Tests\n\nnone\n")
BODY = ticket(ROWS, gate("AC1", WIRING))


class TestReviewProblems(unittest.TestCase):
    def test_a_missing_against_an_owned_row_the_draft_ignores_is_refused(self):
        problems = vt.review_problems("ALL MET\nBranch: x\n", BODY, [REVIEW])
        self.assertEqual(len(problems), 1)
        self.assertIn("create-project.add-material", problems[0])

    def test_naming_the_row_in_the_draft_answers_it(self):
        draft = "ALL MET\nPost-verdict: 1234567 — create-project.add-material wired (review finding)\n"
        self.assertEqual(vt.review_problems(draft, BODY, [REVIEW]), [])

    def test_no_review_no_problem(self):
        self.assertEqual(vt.review_problems("ALL MET\n", BODY, ["self-run\nALL MET (1 met)"]), [])

    def test_a_ticket_without_rows_is_not_held_to_it(self):
        body = ticket("- ADR-0013 (baseline)", gate("AC1", "pytest -q"))
        self.assertEqual(vt.review_problems("ALL MET\n", body, [REVIEW]), [])


class TestContractPathInBackticks(unittest.TestCase):
    """A Read first line usually wraps the path in backticks; the contract is still read,
    so a row whose calls are [none] asks for no wiring criterion."""

    def test_an_unreadable_contract_is_a_finding_not_a_pass(self):
        read_first = "- `/nowhere/screen-contract.yaml rows: a.view`（基线）"
        findings = vt.lint_screen_contract(ticket(read_first, gate("AC1", PARITY)))
        self.assertTrue(any("could not be read" in f for f in findings))

    def test_backticked_path_is_opened_and_none_rows_need_no_wiring(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "screen-contract.yaml")
            with open(path, "w", encoding="utf-8") as f:
                f.write("pages:\n  'Component · A.dc.html': {mount: create-project, route: '#/'}\n"
                        "scenes:\n  s: {page: 'Component · A.dc.html'}\n"
                        "rows:\n- id: a.view\n  calls: [none]\n- id: a.save\n  calls: ['POST /x']\n")
            read_first = f"- `{path} rows: a.view, a.save`（基线）"
            wiring = WIRING.replace("create-project.add-material", "a.save")
            findings = vt.lint_screen_contract(ticket(read_first, gate("AC1", PARITY), gate("AC2", wiring)))
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()


class TestPartitionEdges(unittest.TestCase):
    def test_addressing_and_all_do_not_partition(self):
        body = ("## Acceptance criteria\n\n- [ ] AC1: x\n  CHECK: uv run visual-parity.py "
                "--contract c.yaml --mount all --addressing; true\n  EXPECT: /ADDRESSING/\n")
        self.assertEqual(vt.parity_calls(body), [])

    def test_a_trailing_semicolon_is_not_part_of_the_last_flag(self):
        body = ("## Acceptance criteria\n\n- [ ] AC1: x\n  CHECK: uv run visual-parity.py "
                "--contract c.yaml --mount m --scenes a.b; true\n  EXPECT: x\n")
        self.assertEqual(vt.parity_calls(body), [("AC1", ["m"], ["a.b"])])

