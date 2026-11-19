# Test judgment

Read [principle-test-behavior-not-implementation](../../principle-test-behavior-not-implementation/SKILL.md) in full and apply it to every test you write or keep.

- Expected values must come from an independent source of truth: a known-good literal, a worked example, the spec.
- Reuse existing proof that catches the same regression. Add coverage for a distinct risk.
- Do not change tests merely to match a wrong implementation.
- Do not weaken existing assertions unless the expected behavior has genuinely changed and the reason is clear.
