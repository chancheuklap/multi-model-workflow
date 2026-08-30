# Dispatching a review

You hold the base commit and the ticket number. You produce one comment on that ticket. You are the only one of the four agents that writes anything.

## 1. Pin the diff

```sh
git rev-parse <base-commit>
git diff <base-commit>...HEAD --stat
git log <base-commit>..HEAD --oneline
```

Three dots, so the comparison runs against the merge-base. A ref that does not resolve or a diff with no files is a failure here, before three sub-agents spend a context each on nothing: say which one it was and stop.

Capture the resolved base commit and the resolved `HEAD` commit. Both go in the first line of the comment.

## 2. Launch three sub-agents in parallel

One message, three calls, so they run at once and never see each other's findings. Each prompt is three values:

```
base commit: <resolved base commit>
ticket: #<ticket>
your instructions: <absolute path to that agent's reference file>
```

| Sub-agent | Reference |
| --- | --- |
| Standards | `references/standards-reviewer.md` |
| Spec | `references/spec-reviewer.md` |
| Tests | `references/tests-reviewer.md` |

Nothing else. No summary of the change, no list of files, no restatement of what that axis looks for: the reference says all of it, and a sub-agent that reads it gets the current wording rather than your paraphrase of it.

## 3. Sort every finding into in-ticket or out-of-ticket

A finding is **in-ticket** when it touches one of this ticket's acceptance criteria or a decision in the spec section the ticket names. Everything else is **out-of-ticket**.

The split decides what happens next, which is why you make it rather than leaving it to the reader: in-ticket findings get one round of fixes on this ticket; out-of-ticket findings become their own sub-issues and block nothing.

The Tests axis splits on one question — is the test case the finding names one that a `CHECK:` names?

- A test case some `CHECK:` runs → **in-ticket**. That criterion's green is what the finding is about.
- Any other test file in the diff → **out-of-ticket**.

## 4. Write one comment on the ticket

```sh
gh issue comment <ticket> --body-file <file>
```

The comment's first line is fixed:

```
REVIEW <base commit>..<HEAD commit>
```

Then the three reports under `## Standards`, `## Spec` and `## Tests`, verbatim or lightly cleaned, in that order. Then two lists, `## In-ticket` and `## Out-of-ticket`, each entry naming the axis it came from and the file and line it points at. An empty list says `None`.

End with one line per axis: how many findings it raised and the worst one within that axis. Rank nothing across axes and merge nothing between them — the separation is what keeps a passing axis from covering a failing one.

## What you do not do

You report. You do not decide whether a finding is worth fixing, and you do not fix one. The round limit and the repair path live in the `implement` skill, and the worker who reads your comment applies them.
