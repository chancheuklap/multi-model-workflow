"""The screen-contract rules: what `--lint` reports under `[screen-contract]`, and the
closeout refusal when the Spec axis reported a `Missing` against a row the draft ignores.
"""

import os
import tempfile
import unittest
from _load import load

vt = load()

STORY = ("story-parity.py --contract "
         "docs/specs/x/screen-contract.yaml --pages create-project")
BOUNDARY = 'boundary-check.py --run "pnpm vitest run tests/boundary/add-material.test.ts"'
JOURNEY = "journey.py run smoke"
OK_EXPECT = "/^OK$/m"


def gate(gate_id, check, expect=OK_EXPECT):
    return (f"- [ ] {gate_id}: something a stranger could judge\n"
            f"  CHECK: {check}\n  EXPECT: {expect}\n  EVIDENCE: pending")


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
  "App · 工作台.dc.html": {mount: app-shell, route: '#/', component: app}
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
  observe: ['GET /x -> .ok == true']
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
        self.path = path

    def tearDown(self):
        self.dir.cleanup()

    def story(self, pages="create-project"):
        return STORY.replace("docs/specs/x/screen-contract.yaml", self.path).replace(
            "--pages create-project", f"--pages {pages}")

    def lint(self, *criteria):
        return vt.lint_screen_contract(ticket(self.rows, *criteria, parent=self.parent,
                                              blocked_by="- #637"), 639)
    def test_an_interface_ticket_without_row_ids_is_an_error(self):
        findings = vt.lint_screen_contract(ticket("- README (baseline)", gate("AC1", STORY)))
        self.assertEqual(len(findings), 1)
        self.assertIn("names no", findings[0])

    def test_a_story_criterion_with_row_ids_is_fine(self):
        self.assertEqual(self.lint(gate("AC1", self.story("create-project"))), [])

    def test_a_check_that_stubs_fetch_is_an_error(self):
        stubbed = "pnpm vitest run src/__tests__/live.spec.ts  # vi.stubGlobal('fetch', ...)"
        findings = self.lint(gate("AC1", self.story("create-project")), gate("AC2", stubbed))
        self.assertEqual(len(findings), 1)
        self.assertIn("AC2", findings[0])

    def test_msw_nock_and_fetch_mock_are_refused(self):
        for check in (
            "pnpm vitest run t.ts  # setupServer from msw",
            "nock('https://api.example').get('/x').reply(200)",
            "import fetchMock from 'fetch-mock'",
        ):
            findings = self.lint(gate("AC1", self.story("create-project")), gate("AC2", check))
            self.assertEqual(len(findings), 1, check)
            self.assertIn("AC2", findings[0])

    def test_mocking_the_product_api_client_is_fine(self):
        mocked = "pnpm vitest run tests/boundary/add-material.test.ts  # vi.mock('@/api/client')"
        self.assertEqual(self.lint(gate("AC1", self.story("create-project")),
                                   gate("AC2", mocked)), [])

    def test_a_ticket_without_interface_or_rows_has_nothing_to_say(self):
        self.assertEqual(vt.lint_screen_contract(ticket("- ADR-0013 (baseline)", gate("AC1", "pytest -q"))), [])


class TestPipelineFlags(unittest.TestCase):
    """The two pipeline scripts are given what they need, nothing they retired, and
    nothing their `--help` does not list — the one check that catches a criterion
    naming a capability that does not exist at the moment it is written. The scripts
    belong to the drive-target skill and reach the lint through `--tools`, so the
    test hands their directory over the way the agent does."""

    def setUp(self):
        from pathlib import Path
        vt.TOOLS[:] = [Path(__file__).resolve().parents[2] / "skills" / "drive-target" / "scripts"]
        vt._HELP_FLAGS.clear()

    def tearDown(self):
        vt.TOOLS[:] = []
        vt._HELP_FLAGS.clear()

    def test_story_parity_without_pages(self):
        findings = vt.lint_pipeline_flags(
            "AC1", "story-parity.py --contract c.yaml")
        self.assertTrue(any("without --pages" in f for f in findings))

    def test_story_parity_without_contract(self):
        findings = vt.lint_pipeline_flags("AC1", "story-parity.py --pages demo")
        self.assertTrue(any("without --contract" in f for f in findings))

    def test_boundary_check_without_run(self):
        findings = vt.lint_pipeline_flags("AC2", "boundary-check.py")
        self.assertTrue(any("without --run" in f for f in findings))

    def test_an_address_on_the_line_is_refused(self):
        stale = STORY + " --cdp http://127.0.0.1:9229 --impl http://127.0.0.1:5173/"
        findings = vt.lint_pipeline_flags("AC1", stale)
        self.assertEqual(len(findings), 2)
        self.assertTrue(all(".mmw/target.json" in f for f in findings))

    def test_a_flag_help_does_not_list_is_refused(self):
        findings = vt.lint_pipeline_flags("AC1", STORY + " --reach-hook x")
        self.assertEqual(len(findings), 1)
        self.assertIn("--reach-hook", findings[0])
        self.assertIn("--help", findings[0])

    def test_the_seed_belongs_to_the_contract_now(self):
        findings = vt.lint_pipeline_flags("AC1", STORY + ' --seed "uv run reach.py seed:x"')
        self.assertEqual(len(findings), 1)
        self.assertIn("--seed", findings[0])

    def test_only_the_scripts_own_segment_is_read(self):
        chained = ("uv run python scripts/testing/reach.py seed:x --perturb && " + STORY)
        self.assertEqual(vt.lint_pipeline_flags("AC1", chained), [])
        self.assertEqual(vt.script_segment(chained, "story-parity.py"),
                         " --contract docs/specs/x/screen-contract.yaml --pages create-project")


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
        self.story_check = STORY.replace("docs/specs/x/screen-contract.yaml", self.path)
        self.boundary_check = BOUNDARY

    def tearDown(self):
        self.dir.cleanup()

    def _lint(self, read_first_extra="", parent="", blocked_by="- #637", number=639):
        body = ticket(self.rows + "\n" + read_first_extra, gate("AC1", self.story_check),
                      gate("AC2", self.boundary_check), parent=parent, blocked_by=blocked_by)
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

    def test_a_story_page_the_contract_does_not_declare_is_named(self):
        body = ticket(self.rows, gate("AC1", self.story_check.replace(
            "--pages create-project", "--pages nowhere")),
                      gate("AC2", self.boundary_check), blocked_by="- #637")
        findings = vt.lint_screen_contract(body, 639)
        self.assertTrue(any("--pages nowhere" in f for f in findings))


REVIEW = ("REVIEW abc..def\n\n## Standards\n\nnone\n\n## Spec\n\n### Missing\n\n"
          "1. **create-project.add-material calls nothing.** The button toggles a boolean.\n\n"
          "## Tests\n\nnone\n")
BODY = ticket(ROWS, gate("AC1", STORY))


class TestReviewProblems(unittest.TestCase):
    def test_a_missing_against_an_owned_row_the_draft_ignores_is_refused(self):
        problems = vt.review_problems("ALL MET\nBranch: x\n", BODY, [REVIEW])
        self.assertEqual(len(problems), 1)
        self.assertIn("create-project.add-material", problems[0])

    def test_naming_the_row_in_the_draft_answers_it(self):
        draft = ("ALL MET\nBranch: x\n\n"
                 "Sub-issues opened: #91 (create-project.add-material wired, review finding)\n")
        self.assertEqual(vt.review_problems(draft, BODY, [REVIEW]), [])

    def test_no_review_no_problem(self):
        self.assertEqual(vt.review_problems("ALL MET\n", BODY, ["self-run\nALL MET (1 met)"]), [])

    def test_a_ticket_without_rows_is_not_held_to_it(self):
        body = ticket("- ADR-0013 (baseline)", gate("AC1", "pytest -q"))
        self.assertEqual(vt.review_problems("ALL MET\n", body, [REVIEW]), [])


class TestContractPathInBackticks(unittest.TestCase):
    """A Read first line usually wraps the path in backticks; the contract is still read."""

    def test_an_unreadable_contract_is_a_finding_not_a_pass(self):
        read_first = "- `/nowhere/screen-contract.yaml rows: a.view`（基线）"
        findings = vt.lint_screen_contract(ticket(read_first, gate("AC1", STORY)))
        self.assertTrue(any("could not be read" in f for f in findings))

    def test_backticked_path_is_opened(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "screen-contract.yaml")
            with open(path, "w", encoding="utf-8") as f:
                f.write("pages:\n  'Component · A.dc.html': {mount: create-project, route: '#/'}\n"
                        "scenes:\n  s: {page: 'Component · A.dc.html'}\n"
                        "rows:\n- id: a.view\n  calls: [none]\n- id: a.save\n  "
                        "calls: ['POST /x']\n  observe: ['GET /x -> .ok']\n")
            read_first = f"- `{path} rows: a.view, a.save`（基线）"
            findings = vt.lint_screen_contract(ticket(read_first, gate("AC1", STORY)))
        self.assertFalse(any("could not be read" in f for f in findings), findings)


class TestCriterionShapes(unittest.TestCase):
    """The three criterion shapes `--lint` now checks, plus the fetch rule."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = self.dir.name
        path = os.path.join(self.root, "screen-contract.yaml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(CONTRACT)
        self.path = path
        self.rows = (
            f"- `{path} rows: create-project.add-material`（基线）\n"
            "- `docs/adr/chameleon/0021-chameleon-two-gates.md`（基线）\n"
            "- [两道门（#420）](u)（基线）\n"
            "- `docs/context/chameleon-product.md`——正名"
        )
        self.parent = "[Spec（#537）](u)，Implementation Decisions 第 2 节与 Testing Decisions"
        os.makedirs(os.path.join(self.root, ".mmw", "journeys", "smoke"), exist_ok=True)

    def tearDown(self):
        self.dir.cleanup()

    def story(self, pages):
        return STORY.replace("docs/specs/x/screen-contract.yaml", self.path).replace(
            "--pages create-project", f"--pages {pages}")

    def lint(self, *criteria):
        return vt.lint_screen_contract(
            ticket(self.rows, *criteria, parent=self.parent, blocked_by="- #637"),
            639, root=self.root)

    def test_pages_in_the_contract_that_are_not_app_pages_are_fine(self):
        self.assertEqual(self.lint(gate("AC1", self.story("create-project"))), [])

    def test_a_page_the_contract_does_not_declare_is_an_error(self):
        findings = self.lint(gate("AC1", self.story("nowhere")))
        self.assertTrue(any("nowhere" in f and "no page" in f for f in findings), findings)

    def test_an_app_page_in_pages_is_an_error(self):
        findings = self.lint(gate("AC1", self.story("app-shell")))
        self.assertTrue(any("app-shell" in f and "App" in f for f in findings), findings)

    def test_an_app_page_in_a_comma_list_is_an_error(self):
        findings = self.lint(gate("AC1", self.story("create-project,app-shell")))
        self.assertTrue(any("app-shell" in f and "App" in f for f in findings), findings)

    def test_an_equals_pages_flag_is_read(self):
        check = STORY.replace("docs/specs/x/screen-contract.yaml", self.path).replace(
            "--pages create-project", "--pages=app-shell")
        findings = self.lint(gate("AC1", check))
        self.assertTrue(any("app-shell" in f and "App" in f for f in findings), findings)

    def test_a_second_pages_flag_is_read(self):
        check = self.story("create-project") + " --pages app-shell"
        findings = self.lint(gate("AC1", check))
        self.assertTrue(any("app-shell" in f and "App" in f for f in findings), findings)

    def test_boundary_run_must_not_be_empty(self):
        findings = self.lint(gate("AC1", 'boundary-check.py --run ""'))
        self.assertTrue(any("AC1" in f and "--run" in f and "empty" in f for f in findings),
                        findings)

    def test_a_bare_run_flag_is_empty(self):
        findings = self.lint(gate("AC1", "boundary-check.py --run"))
        self.assertTrue(any("AC1" in f and "--run" in f and "empty" in f for f in findings),
                        findings)

    def test_a_non_empty_boundary_run_is_fine(self):
        findings = self.lint(gate("AC1", BOUNDARY))
        self.assertFalse(any("empty" in f for f in findings), findings)

    def test_a_journey_name_that_exists_is_fine(self):
        self.assertEqual(self.lint(gate("AC1", JOURNEY)), [])

    def test_a_chained_journey_check_reads_only_the_name(self):
        self.assertEqual(self.lint(gate("AC1", "journey.py run smoke; true")), [])

    def test_a_journey_name_missing_under_journeys_is_an_error(self):
        findings = self.lint(gate("AC1", "journey.py run paid-smoke"))
        self.assertTrue(any("paid-smoke" in f and ".mmw/journeys" in f for f in findings),
                        findings)


if __name__ == "__main__":
    unittest.main()
