# Running the session

You are the reviewer session. You run three general-purpose subagents, one per axis, over one diff and write their axis reports onto one ticket. You review nothing yourself, and you are the only one of the four agents that writes anything.

The caller gives you two values: the base commit the diff starts from, and the ticket number.

## 1. Pin the diff

```sh
git rev-parse <base-commit>
git diff <base-commit>...HEAD --stat
git log <base-commit>..HEAD --oneline
```

Three dots, so the comparison runs against the merge-base. A ref that does not resolve or an empty diff is a failure here, before three subagents spend a context each on nothing. Report it on the ticket anyway, through the same call step 4 uses, first line `REVIEW <base commit>..<HEAD commit>` (the refs as you were given them, when one of them does not resolve), then one line saying which of the two failures it was. That report is what the worker is waiting for, so write it even when there is nothing to review. Then stop.

Capture the base commit and the `HEAD` commit. Both go in the first line of the review comment.

## 2. Launch three general-purpose subagents in parallel

One message, three calls, each to your host's general-purpose subagent, so they run at once and never see each other's review findings. Name no model and no thinking level: each axis runs on this session's. If your host lets a call restrict what a subagent may do, restrict it to reading, searching and running commands. Each prompt is one sentence naming this skill, the ticket, the base commit, and one axis. The axis word is exactly `Standards`, `Spec`, or `Tests`:

```
Use the code-review skill to review ticket #<ticket> from base commit <base commit>, axis Standards.
```

Nothing else. No summary of the change, no list of files, no restatement of what that axis looks for, no path. The skill is what they read, and the axis word is which door they take.

**Hold this turn until all three have answered.** On a host whose subagents run in the background unless told otherwise, ask for them to be waited on. The worker that started you is asleep on your report, and what wakes it is the call in step 4 — which cannot be made until the report exists. A turn ended here leaves the report unwritten, so nothing has gone out and the worker is still waiting.

## 3. Sort every review finding into in-ticket or out-of-ticket

A review finding is **in-ticket** when it touches one of six things: this ticket's acceptance criteria, a decision in the spec section the ticket names, a baseline under the ticket's `## Read first`, the spec's `## Out of Scope`, the spec's `## Testing Decisions`, or a file inside this ticket's `## Owns`. Everything else is **out-of-ticket**.

A line the Spec axis marks `should not` under its `Decisions` heading is **in-ticket**: it is the worker's own decision or a file it changed outside `## Owns`, so this ticket is where it is undone.

A file outside `## Owns` is still not written: the sixth condition sorts a review finding onto this ticket's fix round; it does not widen where the worker may write.

For a finding about a ticket merged into the base branch, apply the same ownership boundary explicitly: a repair target inside this ticket's `## Owns` is in-ticket; one that lies only inside that other ticket's `## Owns` is out-of-ticket and becomes a `finding` child.

The split decides what happens next, which is why you make it rather than leaving it to the reader: in-ticket review findings get one round of fixes on this ticket; out-of-ticket review findings become this ticket's `finding` children (`--sub-issue finding`) and block nothing. The worker opens them; you list them. The parent is this ticket.

The Tests axis splits on one question — is the test case the review finding names one that a `CHECK:` names?

- A test case some `CHECK:` runs → **in-ticket**. That criterion's green is what the review finding is about.
- Any other test file in the diff → **out-of-ticket**.

## 4. Write one review comment on the ticket

Write the report to a file, then hand that file to the `verify-ticket` skill's engine, resolving `<engine>` from that skill's own `SKILL.md`:

```sh
<engine> <ticket> --review <file>
```

What that run does with the file, and what it refuses, is the `verify-ticket` skill's `references/reporting.md`.

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

You report. You do not decide whether a review finding is worth fixing, and you do not fix one. The repair path lives in the `implement` skill — one fix round for in-ticket findings, a `finding` child for the rest — and the worker who reads your review comment applies it.
