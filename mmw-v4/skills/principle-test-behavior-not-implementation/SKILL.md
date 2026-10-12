---
name: principle-test-behavior-not-implementation
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Test Behavior, Not Implementation

A test calls the code the way its users do and asserts the result they observe against a literal expected value. A test that asserts which calls the code made, or restates a constant the code contains, does neither.

The check: before you keep a test, ask whether it would still pass if every function it imports returned `undefined`. If yes, it observes no behavior and cannot fail for a defect. Rewrite the assertion or delete the test.

**Why:** A test that cannot fail for a defect costs CI time and review attention and catches nothing. A constant pin also fails when someone edits the constant or the prompt it restates, so it prevents that edit.

**Five shapes that still pass when every imported function returns `undefined`:**

- **Weak or no assertion.** No `expect`, or only `toBeDefined`, `toBeTruthy`, `not.toThrow`, `toBeInstanceOf`, `toBeGreaterThan(0)`.
- **Mock or absence only.** Only `toHaveBeenCalled`, `not.toHaveBeenCalled`, `toBeUndefined`, `toEqual([])`, `toHaveLength(0)`, `not.toBe(wrongValue)`.
- **Self-referential.** The expected value comes from the code under test: `expect(f(a)).toBe(f(a))`, `expect(parsed.url).toBe(buildUrl(...))`.
- **Constant pin.** The assertion restates a hand-maintained constant, config default, table row, or prompt string: `expect(LIMITS.maxTools).toBe(8)`, `expect(PROMPT).toContain("You are")`.
- **Fixture asserts fixture.** The assertion reads data the test built or a value computed in `beforeEach`, and the subject never runs inside the body.

**The fix:** call the subject inside the test body with one concrete input and assert the literal output or the observable effect, `expect(slugify("Hello, World!")).toBe("hello-world")`. For an absence, assert the presence on the other input in the same test. For a constant, test the mechanism that reads it with one input instead of restating the value. For a mock, assert the payload it received or the state after the call, not that it was called. When no such assertion exists, delete the test.

**Keep** a test of a relation across a table's rows (a key present in two tables, a parent that exists), and a compile-time check in a `*.test-d.ts` file.

**Red for the right reason.** Run a new test before the code it covers exists, and read why it fails. Red from a missing file, an import error or a typo in a case name proves nothing; the test counts as red only when it fails because the behavior is absent.

**Pin behavior that must not change.** A change that keeps a behavior as it is (a restructuring, a move, a dependency swapped for another) has no red to see. Pin the behavior first with a characterization test, a snapshot, or a comparison of old and new output, run it green before the structure moves and green again after. It counts as able to fail once you have broken that behavior by hand and watched the pin go red. A type check or a lint is not a pin.

**Name the object a check checks.** A check that finds its object by searching and taking the first hit checks whatever the search happens to return, and often cannot fail at all.

**In a diff:**

- Ask first whether the case would still pass if every function it imports returned `undefined` (the five shapes above), or, for a behavior the change keeps, whether it observes that behavior at all. If not, it is the finding whatever else the case is; rewrite it as **The fix** says.
- An expected value recomputed the way the code computes it passes by construction (tautological): write the literal value.
- A case that mocks an internal collaborator, tests a private method, or asserts call counts or order breaks on a refactor that keeps the behavior: test through the public interface only.
- A case that checks the result through a side channel (a database read, a file the code writes) where the interface shows it: assert through the interface.
- A case named for how the code works rather than what it does: name it for the behavior.
- A mock of something the repository can run: mock only at a system boundary (an external API, time, randomness, sometimes the database or the file system).
- A case that covers only the ordinary input while the behavior depends on an edge, a boundary or an error path: name the untested path and what should happen on it.
- An assertion on the wording of prose no program reads (a skill's text, a document, a message nothing parses), where the request fixes no wording: assert exit codes, strings a program reads, produced facts and effects.
- A committed test no criterion names, where the repository keeps no test of that kind for that kind of change, or more than one focused case for one stated behavior: delete the extra.
- A case that makes more than one logical assertion: split it, one behavior per case.
- A new test whose only recorded red came from a missing file, an import error or a typo has not been shown able to fail (**Red for the right reason**).
- A restructuring, move or swapped dependency with no pin run green before and after it, or with a type check or lint as its only pin: pin the behavior first (**Pin behavior that must not change**).
- A check that finds its object by searching and taking the first hit: name the object (**Name the object a check checks**).
- A bug fix carries one focused test that reproduces the bug, deterministic even when the bug was flaky, and a change across an integration boundary a test of its whole path. When the ticket's criteria name neither, that is a gap in the ticket, raised as such, never a test the review adds to the diff.
