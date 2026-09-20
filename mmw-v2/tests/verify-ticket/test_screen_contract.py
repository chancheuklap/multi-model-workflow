"""The screen-contract rules: what `--lint` reports under `[screen-contract]`, and the
closeout refusal when the Spec axis reported a `Missing` against a row the draft ignores.
"""

import os
import tempfile
import unittest
from _load import event, load

vt = load()

STORY = ("story-parity.py --contract "
         "docs/specs/x/screen-contract.yaml --pages create-project")
BOUNDARY = 'boundary-check.py --run "pnpm vitest run tests/boundary/add-material.test.ts"'
JOURNEY = "journey.py run smoke"
OK_EXPECT = "/^OK$/m"


def gate(gate_id, check, expect=OK_EXPECT):
    return (f"- [ ] {gate_id}: something a stranger could judge\n"
            f"  CHECK: {check}\n  EXPECT: {expect}\n  EVIDENCE: pending")


def ticket(read_first, *criteria, parent="", blocked_by="", owns=""):
    body = ""
    if parent:
        body += "## Parent\n\n" + parent + "\n\n"
    body += ("## Read first\n\n" + read_first + "\n\n## Acceptance criteria\n\n"
             + "\n".join(criteria) + "\n")
    if blocked_by:
        body += "\n## Blocked by\n\n" + blocked_by + "\n"
    if owns:
        body += "\n## Owns\n\n" + owns + "\n"
    return body


ROWS = "- docs/specs/x/screen-contract.yaml rows: create-project.add-material (baseline)"

CONTRACT = """
effort: x
baselines:
  look: docs/prototypes/x/claude-design
  precedence: "look and copy -> handoff; behaviour -> contract"
locale: zh-CN
viewports: [1440x900]
pages:
  "Component · 新建商品项目.dc.html": {mount: create-project, component: cp}
  "Component · 壳头.dc.html": {mount: shell-header, component: sh}
  "App · 工作台.dc.html": {mount: app-shell}
scenes:
  empty: {page: "Component · 新建商品项目.dc.html"}
  material-added: {page: "Component · 新建商品项目.dc.html"}
  shell-header.ready: {page: "Component · 壳头.dc.html"}
states: [app-awaiting-browser]
backend_without_ui: []
proposed_operations: []
retired_ids: []
rows:
- id: create-project.add-material
  component: cp
  trigger: create-project.add-material-button
  precondition: {material: none}
  scenes: [empty]
  calls: ['POST /x']
  shows: {}
  next: material-added
  on_failure: {failed: toast}
  source: ['#537 story 2', '#537 Implementation Decisions 2', 'ADR-0021', '#420', 'docs/context/chameleon-product.md 新建商品项目', 'README §4.1']
  gap: aligned
- id: create-project.name
  component: cp
  trigger: create-project.name
  precondition: {}
  scenes: [empty, material-added]
  calls: [none]
  shows: {}
  next: stay
  source: ['#537 Testing Decisions']
  gap: aligned
- id: shell.sign-in
  component: sh
  trigger: shell.sign-in
  precondition: {}
  scenes: [shell-header.ready]
  calls: ['ipc x']
  shows: {}
  next: app-awaiting-browser
  on_failure: {failed: toast}
  source: ['#537 Implementation Decisions 2']
  gap: aligned
- id: desk.filter-customer
  component: sh
  app: "App · 工作台.dc.html"
  trigger: shell.filter-customer
  precondition: {}
  scenes: [shell-header.ready]
  calls: ['GET /x']
  shows: {}
  next: material-added
  on_failure: {failed: toast}
  source: ['#537 Implementation Decisions 2']
  gap: aligned
"""


class ContractFixture:
    """A screen contract on disk, and a story criterion pointed at it."""

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

    def story(self, mounts="create-project"):
        return STORY.replace("docs/specs/x/screen-contract.yaml", self.path).replace(
            "--pages create-project", f"--pages {mounts}")

    def lint(self, *criteria):
        return vt.lint_screen_contract(ticket(self.rows, *criteria, parent=self.parent,
                                              blocked_by="- #637"), 639)


class TestLintScreenContract(ContractFixture, unittest.TestCase):
    """An interface ticket names its screen-contract rows; no CHECK stubs the
    application's own network. Against a contract that is on disk."""
    def test_an_interface_ticket_without_row_ids_is_an_error(self):
        findings = vt.lint_screen_contract(ticket("- README (baseline)", gate("AC1", STORY)))
        self.assertEqual(len(findings), 1)
        self.assertIn("names no", findings[0])

    def test_a_story_criterion_with_row_ids_is_fine(self):
        self.assertEqual(self.lint(gate("AC1", self.story("create-project")),
                                   gate("AC2", BOUNDARY)), [])

    def test_a_ticket_with_rows_and_no_story_criterion_is_an_error(self):
        findings = self.lint(gate("AC1", BOUNDARY))
        self.assertTrue(any("create-project" in f and "story" in f for f in findings),
                        findings)

    def test_a_ticket_with_rows_and_its_story_criterion_is_clean(self):
        self.assertEqual(self.lint(gate("AC1", self.story()), gate("AC2", BOUNDARY)), [])

    def test_each_claimed_design_page_needs_its_mount_in_a_story_criterion(self):
        self.rows = self.rows.replace("rows: create-project.add-material`",
                                      "rows: create-project.add-material, shell.sign-in`")
        findings = self.lint(gate("AC1", self.story("create-project")),
                             gate("AC2", BOUNDARY))
        self.assertTrue(any("shell-header" in finding and "story" in finding
                            for finding in findings), findings)

    def test_a_row_without_its_boundary_criterion_is_named(self):
        self.rows = self.rows.replace("rows: create-project.add-material`",
                                      "rows: create-project.add-material, shell.sign-in`")
        path = os.path.join(self.dir.name, "one-row.test.ts")
        with open(path, "w", encoding="utf-8") as f:
            f.write("clickByDataUi('create-project.add-material-button')\n")
        findings = self.lint(gate("AC1", self.story("create-project,shell-header")),
                             gate("AC2", self.boundary_for(path)))
        self.assertTrue(any("shell.sign-in" in f and "boundary" in f
                            for f in findings), findings)

    def test_a_row_with_its_boundary_criterion_is_clean(self):
        self.rows = self.rows.replace("rows: create-project.add-material`",
                                      "rows: create-project.add-material, shell.sign-in`")
        path = os.path.join(self.dir.name, "both-rows.test.ts")
        with open(path, "w", encoding="utf-8") as f:
            f.write("clickByDataUi('create-project.add-material-button')\n"
                    "clickByDataUi('shell.sign-in')\n")
        self.assertEqual(
            self.lint(gate("AC1", self.story("create-project,shell-header")),
                      gate("AC2", self.boundary_for(path))), [])

    def test_a_cross_component_row_without_a_boundary_criterion_is_an_error(self):
        self.rows = f"- `{self.path} rows: desk.filter-customer`（基线）"
        findings = self.lint(gate("AC1", self.story("app-shell")))
        self.assertTrue(any("desk.filter-customer" in f and "cross-component" in f
                            for f in findings), findings)

    def test_a_cross_component_row_with_a_boundary_criterion_is_clean(self):
        self.rows = f"- `{self.path} rows: desk.filter-customer`（基线）"
        self.assertEqual(self.lint(gate("AC1", self.story("app-shell")),
                                   gate("AC2", BOUNDARY)), [])

    def boundary_for(self, path):
        return f'boundary-check.py --run "pnpm vitest run {path}"'

    def test_a_boundary_test_without_the_row_trigger_id_is_an_error(self):
        path = os.path.join(self.dir.name, "add-material.test.ts")
        with open(path, "w", encoding="utf-8") as f:
            f.write("test('submits a material', () => {})\n")
        findings = self.lint(gate("AC1", self.story()),
                             gate("AC2", self.boundary_for(path)))
        self.assertTrue(any("create-project.add-material" in f
                            and "create-project.add-material-button" in f
                            and "does not appear" in f for f in findings), findings)

    def test_a_boundary_test_with_the_row_trigger_id_is_clean(self):
        path = os.path.join(self.dir.name, "add-material.test.ts")
        with open(path, "w", encoding="utf-8") as f:
            f.write("clickByDataUi('create-project.add-material-button')\n")
        self.assertEqual(self.lint(gate("AC1", self.story()),
                                   gate("AC2", self.boundary_for(path))), [])

    def test_an_unreadable_boundary_test_file_is_said_so(self):
        path = os.path.join(self.dir.name, "unreadable.test.ts")
        os.makedirs(path)
        findings = self.lint(gate("AC1", self.story()),
                             gate("AC2", self.boundary_for(path)))
        self.assertTrue(any(path in f and "could not be read" in f for f in findings),
                        findings)

    def test_a_boundary_test_file_not_written_yet_is_a_warning(self):
        path = os.path.join(self.dir.name, "not-written.test.ts")
        warnings = []
        body = ticket(self.rows, gate("AC1", self.story()),
                      gate("AC2", self.boundary_for(path)), parent=self.parent)
        findings = vt.lint_screen_contract(body, 639, root=self.dir.name,
                                            warnings=warnings)
        self.assertEqual(findings, [])
        self.assertTrue(any(path in warning and "not written yet" in warning
                            for warning in warnings), warnings)

    def test_a_check_that_stubs_fetch_is_an_error(self):
        stubbed = "pnpm vitest run src/__tests__/live.spec.ts  # vi.stubGlobal('fetch', ...)"
        findings = self.lint(gate("AC1", self.story("create-project")),
                             gate("AC2", BOUNDARY), gate("AC3", stubbed))
        self.assertEqual(len(findings), 1)
        self.assertIn("AC3", findings[0])

    def test_a_word_that_merely_contains_a_library_name_is_no_stub(self):
        check = "printf dreamsweeper"
        self.assertEqual(
            self.lint(gate("AC1", self.story("create-project")), gate("AC2", BOUNDARY),
                      gate("AC3", check)), [])

    def test_a_real_fetch_stub_is_still_refused(self):
        check = "pnpm vitest run live.test.ts  # vi.stubGlobal('fetch', replacement)"
        findings = self.lint(gate("AC1", self.story("create-project")),
                             gate("AC2", BOUNDARY), gate("AC3", check))
        self.assertEqual(len(findings), 1)
        self.assertIn("own network", findings[0])

    def test_msw_nock_and_fetch_mock_are_refused(self):
        for check in (
            "pnpm vitest run t.ts  # setupServer from msw",
            "nock('https://api.example').get('/x').reply(200)",
            "import fetchMock from 'fetch-mock'",
        ):
            findings = self.lint(gate("AC1", self.story("create-project")),
                                 gate("AC2", BOUNDARY), gate("AC3", check))
            self.assertEqual(len(findings), 1, check)
            self.assertIn("AC3", findings[0])

    def test_mocking_the_product_api_client_is_fine(self):
        mocked = "pnpm vitest run tests/boundary/add-material.test.ts  # vi.mock('@/api/client')"
        self.assertEqual(self.lint(gate("AC1", self.story("create-project")),
                                   gate("AC2", BOUNDARY), gate("AC3", mocked)), [])

    def test_a_ticket_without_interface_or_rows_has_nothing_to_say(self):
        self.assertEqual(vt.lint_screen_contract(ticket("- ADR-0013 (baseline)", gate("AC1", "pytest -q"))), [])


class TestPipelineFlags(unittest.TestCase):
    """story-parity.py and boundary-check.py are given what they need, nothing they
    retired, and nothing their `--help` does not list — the one check that catches
    a criterion naming a capability that does not exist at the moment it is written.
    The scripts belong to the ui-acceptance skill and reach the lint through
    `--tools`, so the test hands their directory over the way the agent does."""

    def setUp(self):
        from pathlib import Path
        vt.TOOLS[:] = [Path(__file__).resolve().parents[2] / "skills" / "ui-acceptance" / "scripts"]
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
        stale = STORY + " --impl http://127.0.0.1:5173/"
        findings = vt.lint_pipeline_flags("AC1", stale)
        self.assertEqual(len(findings), 1)
        self.assertIn(".mmw/target.json", findings[0])

    def test_a_flag_help_does_not_list_is_refused(self):
        findings = vt.lint_pipeline_flags("AC1", STORY + " --reach-hook x")
        self.assertEqual(len(findings), 1)
        self.assertIn("--reach-hook", findings[0])
        self.assertIn("--help", findings[0])

    def test_a_whole_product_flag_is_one_help_does_not_list(self):
        """`--seed` is no longer a retired flag; `--help` does not list it, and
        that is the refusal. `--cdp` is the same shape."""
        seed = vt.lint_pipeline_flags("AC1", STORY + ' --seed "uv run reach.py seed:x"')
        self.assertEqual(len(seed), 1)
        self.assertIn("--seed", seed[0])
        self.assertIn("--help does not list it", seed[0])
        cdp = vt.lint_pipeline_flags("AC1", STORY + " --cdp http://127.0.0.1:9229")
        self.assertEqual(len(cdp), 1)
        self.assertIn("--cdp", cdp[0])
        self.assertIn("--help does not list it", cdp[0])

    def test_a_flag_inside_a_quoted_run_value_belongs_to_that_command(self):
        """`--run` carries a whole command; `pnpm --dir <app>` is how this repository
        runs a front-end test, and `--dir` is pnpm's, not the judge's."""
        check = ('boundary-check.py --run "pnpm --dir desktop-chameleon exec vitest run '
                 'tests/boundary/add-material.test.ts"')
        self.assertEqual(vt.lint_pipeline_flags("AC2", check), [])

    def test_a_run_value_carrying_an_operator_is_still_one_value(self):
        check = 'boundary-check.py --run "pnpm --dir app build && pnpm --dir app test"'
        self.assertEqual(vt.lint_pipeline_flags("AC2", check), [])

    def test_an_equals_run_value_hides_its_commands_flags_too(self):
        check = "boundary-check.py --run='pnpm --dir app exec vitest run t.ts'"
        self.assertEqual(vt.lint_pipeline_flags("AC2", check), [])

    def test_a_flag_of_the_judge_after_a_quoted_run_value_is_still_read(self):
        check = 'boundary-check.py --run "pnpm --dir app test" --reach-hook x'
        findings = vt.lint_pipeline_flags("AC2", check)
        self.assertEqual(len(findings), 1)
        self.assertIn("--reach-hook", findings[0])

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

class TestSources(ContractFixture, unittest.TestCase):
    """What a worker cannot see does not exist: every baseline-class source of an owned
    row is under `## Read first`, and every spec section is under `## Parent`."""

    def setUp(self):
        super().setUp()
        self.rows = (f"- `{self.path} rows: create-project.add-material, create-project.name`"
                     "（基线）")
        self.story_check = STORY.replace("docs/specs/x/screen-contract.yaml", self.path)
        self.boundary_check = BOUNDARY

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


REVIEW = event("reviewer.reported",
               "REVIEW abc..def\n\n## Standards\n\nnone\n\n## Spec\n\n### Missing\n\n"
               "1. **create-project.add-material calls nothing.** The button toggles a boolean.\n\n"
               "## Tests\n\nnone\n", base="abc", head="def")
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
                f.write("pages:\n  'Component · A.dc.html': {mount: create-project, component: a}\n"
                        "scenes:\n  s: {page: 'Component · A.dc.html'}\n"
                        "rows:\n- id: a.view\n  trigger: a.view\n  calls: [none]\n"
                        "- id: a.save\n  trigger: a.save\n  calls: ['POST /x']\n")
            read_first = f"- `{path} rows: a.view, a.save`（基线）"
            findings = vt.lint_screen_contract(ticket(read_first, gate("AC1", STORY)))
        self.assertFalse(any("could not be read" in f for f in findings), findings)


class TestCriterionShapes(ContractFixture, unittest.TestCase):
    """Each `--pages` mount is a non-App page of the contract; a boundary-check.py
    --run is a non-empty command; a journey.py run <name> exists under .mmw/journeys/."""

    def setUp(self):
        super().setUp()
        self.root = self.dir.name
        self.rows = (
            f"- `{self.path} rows: create-project.add-material`（基线）\n"
            "- `docs/adr/chameleon/0021-chameleon-two-gates.md`（基线）\n"
            "- [两道门（#420）](u)（基线）\n"
            "- `docs/context/chameleon-product.md`——正名"
        )
        self.parent = "[Spec（#537）](u)，Implementation Decisions 第 2 节与 Testing Decisions"
        os.makedirs(os.path.join(self.root, ".mmw", "journeys", "smoke"), exist_ok=True)

    def lint(self, *criteria, owns=""):
        criteria = list(criteria)
        if not any("story-parity.py" in criterion for criterion in criteria):
            criteria.append(gate("AC90", self.story("create-project")))
        if not any("boundary-check.py" in criterion for criterion in criteria):
            criteria.append(gate("AC91", BOUNDARY))
        return vt.lint_screen_contract(
            ticket(self.rows, *criteria, parent=self.parent, blocked_by="- #637", owns=owns),
            639, root=self.root)

    def test_pages_in_the_contract_that_are_not_app_pages_are_fine(self):
        self.assertEqual(self.lint(gate("AC1", self.story("create-project"))), [])

    def test_a_page_the_contract_does_not_declare_is_an_error(self):
        findings = self.lint(gate("AC1", self.story("nowhere")))
        self.assertTrue(any("nowhere" in f and "no page" in f for f in findings), findings)

    def test_an_app_page_mount_is_allowed_in_pages(self):
        self.rows = f"- `{self.path} rows: desk.filter-customer`（基线）"
        self.assertEqual(self.lint(gate("AC1", self.story("app-shell"))), [])

    def test_an_app_page_in_a_comma_list_is_allowed(self):
        self.rows = f"- `{self.path} rows: desk.filter-customer`（基线）"
        self.assertEqual(self.lint(gate("AC1", self.story("create-project,app-shell"))), [])

    def test_an_equals_pages_flag_is_read(self):
        self.rows = f"- `{self.path} rows: desk.filter-customer`（基线）"
        check = STORY.replace("docs/specs/x/screen-contract.yaml", self.path).replace(
            "--pages create-project", "--pages=app-shell")
        self.assertEqual(self.lint(gate("AC1", check)), [])

    def test_a_second_pages_flag_is_read(self):
        self.rows = f"- `{self.path} rows: desk.filter-customer`（基线）"
        check = self.story("create-project") + " --pages app-shell"
        self.assertEqual(self.lint(gate("AC1", check)), [])

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

    def test_a_journey_under_a_directory_the_check_cds_into_is_fine(self):
        """A criterion that drives journey.py against a fixture `cd`s into it first, so
        the journey it names is under that directory's `.mmw/`, not the repository's."""
        os.makedirs(os.path.join(self.root, "fixtures", "repo", ".mmw", "journeys", "demo"),
                    exist_ok=True)
        self.assertEqual(
            self.lint(gate("AC1", "cd fixtures/repo && journey.py run demo")), [])

    def test_a_journey_missing_under_the_directory_the_check_cds_into_is_an_error(self):
        os.makedirs(os.path.join(self.root, "fixtures", "repo", ".mmw", "journeys", "demo"),
                    exist_ok=True)
        findings = self.lint(gate("AC1", "cd fixtures/repo && journey.py run absent"))
        self.assertTrue(any("absent" in f and ".mmw/journeys" in f for f in findings),
                        findings)

    def test_a_journey_this_ticket_owns_is_not_yet_expected_to_exist(self):
        """The ticket that builds the journey names it before it is there; `## Owns`
        covering the directory is what says this ticket is that ticket."""
        self.assertEqual(
            self.lint(gate("AC1", "journey.py run money"), owns="- `.mmw/journeys/money/**`"), [])

    def test_a_wider_owns_glob_covers_the_journey_directory(self):
        self.assertEqual(
            self.lint(gate("AC1", "journey.py run money"), owns="- `.mmw/**`"), [])

    def test_an_owns_glob_for_another_journey_does_not_cover_this_one(self):
        findings = self.lint(gate("AC1", "journey.py run money"),
                             owns="- `.mmw/journeys/login-gate/**`")
        self.assertTrue(any("money" in f and ".mmw/journeys" in f for f in findings), findings)

    def test_owns_covers_a_journey_under_the_directory_the_check_cds_into(self):
        os.makedirs(os.path.join(self.root, "fixtures", "repo", ".mmw"), exist_ok=True)
        self.assertEqual(
            self.lint(gate("AC1", "cd fixtures/repo && journey.py run absent"),
                      owns="- `fixtures/repo/.mmw/journeys/absent/**`"), [])


class TestJourneyBreakRules(unittest.TestCase):
    SPEC = """## Testing Decisions

- **Critical flows** (关键流程):
  - `checkout` — Implementation Decisions sections 2 and 3
"""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        for name in ("smoke", "checkout", "owner-demo"):
            os.makedirs(os.path.join(self.dir.name, ".mmw", "journeys", name))

    def tearDown(self):
        self.dir.cleanup()

    def lint(self, flow, *, break_value="", owns="", spec_body=None):
        check = f"journey.py run {flow}" + (f' --break "{break_value}"' if break_value else "")
        body = ticket("- ADR-0008 (baseline)", gate("AC1", check),
                      parent="#537, Implementation Decisions sections 2 and 3",
                      owns=owns)
        warnings = []
        findings = vt.lint_screen_contract(
            body, 639, root=self.dir.name, warnings=warnings,
            spec_bodies={537: spec_body} if spec_body is not None else {})
        return findings, warnings

    def test_an_acceptance_journey_without_break_is_an_error(self):
        findings, warnings = self.lint("checkout", spec_body=self.SPEC)
        self.assertTrue(any("checkout" in f and "--break" in f for f in findings), findings)
        self.assertEqual(warnings, [])

    def test_an_acceptance_journey_with_break_is_clean(self):
        self.assertEqual(
            self.lint("checkout", break_value="POST /items", spec_body=self.SPEC), ([], []))

    def test_a_contract_smoke_journey_needs_no_break(self):
        self.assertEqual(self.lint("smoke", owns="- `.mmw/**`"), ([], []))

    def test_an_owner_named_journey_without_break_is_a_warning(self):
        findings, warnings = self.lint("owner-demo")
        self.assertEqual(findings, [])
        self.assertTrue(any("owner-demo" in warning and "--break" in warning
                            for warning in warnings), warnings)

    def test_an_owner_named_journey_with_break_is_clean(self):
        self.assertEqual(self.lint("owner-demo", break_value="POST /demo"), ([], []))


if __name__ == "__main__":
    unittest.main()
