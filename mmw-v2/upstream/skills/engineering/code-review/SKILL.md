---
name: code-review
description: "Review one ticket's diff from a base commit along three axes — Standards, Spec, Tests — in parallel read-only subagents, and write the axis reports as one review comment on the ticket. The caller gives two values: the base commit the diff starts from, and the ticket number."
---

You are the reviewer session. You run three `reviewer` subagents, one per axis, over one diff and write their axis reports onto one ticket. You review nothing yourself, and you are the only one of the four agents that writes anything.

The caller gives you two values: the base commit the diff starts from, and the ticket number.

## 1. Pin the diff

```sh
git rev-parse <base-commit>
git diff <base-commit>...HEAD --stat
git log <base-commit>..HEAD --oneline
```

Three dots, so the comparison runs against the merge-base. A ref that does not resolve or an empty diff is a failure here, before three subagents spend a context each on nothing. Report it on the ticket anyway: `gh issue comment <ticket>`, first line `REVIEW <base commit>..<HEAD commit>` (the refs as you were given them, when one of them does not resolve), then one line saying which of the two failures it was. That is what returns the waiting worker at once. Then stop.

Capture the resolved base commit and the resolved `HEAD` commit. Both go in the first line of the review comment.

## 2. Launch three `reviewer` subagents in parallel

One message, three calls, each to the `reviewer` subagent this toolbox installs on your host, so they run at once and never see each other's review findings. The subagent's model and effort are its definition file's, assembled from the `reviewer` row of the `dispatch` skill's `models.md`; name no model in the call. Each prompt is three values:

```
base commit: <resolved base commit>
ticket: #<ticket>
your instructions: <absolute path to that agent's reference file>
```

| Axis | Reference file |
| --- | --- |
| Standards | [references/standards-reviewer.md](references/standards-reviewer.md) |
| Spec | [references/spec-reviewer.md](references/spec-reviewer.md) |
| Tests | [references/tests-reviewer.md](references/tests-reviewer.md) |

Nothing else. No summary of the change, no list of files, no restatement of what that axis looks for: the reference file says all of it, and a subagent that reads it gets the current wording rather than your paraphrase of it. Everything fixed — what to look for, where to find the repository's documented standards, how to reach the spec, which test files are in scope — is already written there.

## 3. Sort every review finding into in-ticket or out-of-ticket

A review finding is **in-ticket** when it touches one of five things: this ticket's acceptance criteria, a decision in the spec section the ticket names, a baseline under the ticket's `## Read first`, the spec's `## Out of Scope`, or the spec's `## Testing Decisions`. Everything else is **out-of-ticket**.

A line the Spec axis marks `should not` under its `Decisions` heading is **in-ticket**: it is the worker's own decision or a file it changed outside `## Owns`, so this ticket is where it is undone.

The split decides what happens next, which is why you make it rather than leaving it to the reader: in-ticket review findings get one round of fixes on this ticket; out-of-ticket review findings become this ticket's sub-issues (`--sub-issue review`) and block nothing. The worker opens them; you list them. The parent is this ticket.

The Tests axis splits on one question — is the test case the review finding names one that a `CHECK:` names?

- A test case some `CHECK:` runs → **in-ticket**. That criterion's green is what the review finding is about.
- Any other test file in the diff → **out-of-ticket**.

## 4. Write one review comment on the ticket

```sh
gh issue comment <ticket> --body-file <file>
```

The review comment's first line is fixed:

```
REVIEW <base commit>..<HEAD commit>
```

Then the three axis reports under `## Standards`, `## Spec` and `## Tests`, verbatim or lightly cleaned, in that order. Then two lists, `## In-ticket` and `## Out-of-ticket`, each entry naming the axis it came from and the file and line it points at. An empty list says `None`.

End with one line per axis: how many review findings it raised and the worst one within that axis. Rank nothing across axes and merge nothing between them — the separation is what keeps a passing axis from covering a failing one.

The reviewer session ends; the ticket outlives it, and the worker who fixes these review findings reads the ticket, not your transcript. A report that exists only in this conversation reaches nobody.

## Why three axes

One change can pass one axis and fail another:

- Follows every convention, builds the wrong thing → **Standards pass, Spec fail.**
- Builds exactly what was asked, breaks the repository's conventions → **Spec pass, Standards fail.**
- Does the right thing, proved by a test that would pass either way → **Standards and Spec pass, Tests fail.**

## What you do not do

You report. You do not decide whether a review finding is worth fixing, and you do not fix one. The three-round cap and the repair path live in the `implement` skill, and the worker who reads your review comment applies them.
