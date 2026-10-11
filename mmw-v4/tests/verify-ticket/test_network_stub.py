"""`--lint` refuses a `CHECK:` that stubs the application's own network, and reads a
ticket's `## Parent` into the spec sections it names."""

import unittest
from _load import load

vt = load()


def gate(gate_id, check):
    return (f"- [ ] {gate_id}: something a stranger could judge\n"
            f"  CHECK: {check}\n  EXPECT: /^OK$/m\n  EVIDENCE: pending")


def ticket(*criteria):
    return "## Acceptance criteria\n\n" + "\n".join(criteria) + "\n"


class TestNetworkStubs(unittest.TestCase):
    def lint(self, check):
        return vt.lint_network_stubs(ticket(gate("AC1", "pytest -q"), gate("AC3", check)))

    def test_a_check_that_stubs_fetch_is_an_error(self):
        findings = self.lint("pnpm vitest run src/__tests__/live.spec.ts  # vi.stubGlobal('fetch', ...)")
        self.assertEqual(len(findings), 1)
        self.assertIn("AC3", findings[0])

    def test_a_word_that_merely_contains_a_library_name_is_no_stub(self):
        self.assertEqual(self.lint("printf dreamsweeper"), [])

    def test_msw_nock_and_fetch_mock_are_refused(self):
        for check in (
            "pnpm vitest run t.ts  # setupServer from msw",
            "pnpm vitest run jest-msw tests",
            "pnpm vitest run msw-trpc setup",
            "import nock from 'nock'",
            "nock('https://api.example').get('/x').reply(200)",
            "import fetchMock from 'fetch-mock'",
        ):
            findings = self.lint(check)
            self.assertEqual(len(findings), 1, check)
            self.assertIn("AC3", findings[0])

    def test_mocking_the_product_api_client_is_fine(self):
        self.assertEqual(
            self.lint("pnpm vitest run tests/boundary/add-material.test.ts  # vi.mock('@/api/client')"), [])


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


if __name__ == "__main__":
    unittest.main()
