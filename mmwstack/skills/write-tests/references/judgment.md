# Test judgment

Use [principle-test-behavior-not-implementation](../../principle-test-behavior-not-implementation/SKILL.md) to judge what the test observes.

- Derive expected values from the requirement or a known-good example, independently of the code under test.
- Reuse existing proof that catches the same regression. Add coverage for a distinct risk.
- Change an assertion when the expected behavior changes, not to make an incorrect implementation pass.
