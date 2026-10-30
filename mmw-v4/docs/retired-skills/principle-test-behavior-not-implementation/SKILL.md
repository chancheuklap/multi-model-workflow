---
name: principle-test-behavior-not-implementation
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Test Behavior, Not Implementation

A test is a claim about what the code does for its users: a caller, an end user, or another service. Behavior is what those users can observe through the interface they use. That includes return values, errors, state they can read back, and effects on systems outside the code, such as a request sent, a row written, or a message emitted. Implementation is what they cannot observe: private helpers, internal call order, intermediate data, and which internal collaborator did the work.

Judge each test against two imagined edits:

- **Break the behavior.** Make the code return a wrong value, skip an effect, or do the effect twice. If the test still passes, it proves nothing. The usual causes are an assertion looser than the contract, an expected value computed by the code under test, a restated constant or prompt string that never runs the code that reads it, and an assertion on data that the test built itself.
- **Change the internals.** Keep every observable result the same and restructure the code underneath. If the test now fails, it is pinned to the implementation. It will need a rewrite on every refactor and still catches no bug.

Keep a test that catches the first edit and survives the second. Rewrite or delete the rest. To write a test that does both, drive the code through its users' interface with a concrete input. Derive the expected value from the requirement, not from a run of the code. Assert what the contract promises, no less and no more.

The contract decides, not the shape of the assertion. When "an empty cart never charges" is the promise, an assertion that the payment client got no call is behavior. Pair it with a case where the charge happens, so that the test shows it can see a call. The payload that a mocked external service receives is behavior, because that service observes it. A call to an internal helper is implementation, because no user can see it. An empty list is the exact answer when no record matches, and a hollow check when the test only needs some result. An exact error message pins wording that no caller reads. The error type that callers branch on is the contract.

A test can pin an invariant instead of a call, such as a key that must exist in two tables or a compile-time type check. The invariant is the behavior.

**Red for the right reason.** Run a new test before the code it covers exists, and read why it fails. Red from a missing file, an import error or a typo in a case name proves nothing; the test counts as red only when it fails because the behavior is absent.

**Pin behavior that must not change.** A change that keeps a behavior as it is (a restructuring, a move, a dependency swapped for another) has no red to see. Pin the behavior first with a characterization test, a snapshot, or a comparison of old and new output, run it green before the structure moves and green again after. It counts as able to fail once you have broken that behavior by hand and watched the pin go red. A type check or a lint is not a pin.

**Name the object a check checks.** A check that finds its object by searching and taking the first hit (`gh issue list --search … | head -1` and its kind) checks whatever the search happens to return, and often cannot fail at all.

**In a diff:**

- Judge the case against the two imagined edits above: it fails when behavior breaks and keeps passing when only the internals change. Rewrite or delete a case that fails either test.
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
