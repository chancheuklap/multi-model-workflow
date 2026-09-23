# Running the session

You are the reviewer session. You write the axis reports onto one ticket. On a host that can run subagents you run no axis yourself, and you verify every finding the axes report; on one that cannot, you run the axis files yourself. You are the only one that writes on the ticket.

The caller gives you two values: the base commit the diff starts from, and the ticket number.

## Resolve `<engine>` once

`<engine>` in step 5 is the command the `verify-ticket` skill resolves in its own `SKILL.md`. Resolve it from that skill's `SKILL.md`; the path differs by machine and by host.

## 1. Pin the diff

```sh
git rev-parse <base-commit>
git diff <base-commit>...HEAD --stat
git log <base-commit>..HEAD --oneline
```

Three dots, so the comparison runs against the merge-base. A ref that does not resolve or an empty diff is a failure here, before the axis subagents spend a context each on nothing. Report it on the ticket anyway, through the same call step 5 uses, first line `REVIEW <base commit>..<HEAD commit>` (the refs as you were given them, when one of them does not resolve), then one line saying which of the two failures it was. Then stop.

Capture the base commit and the `HEAD` commit. Both go in the first line of the review comment.

Done when both commits resolve and the diff is not empty, or that failure is on the ticket.

## 2. Run the axes

Read the ticket. A **story criterion** is a `CHECK:` that names `story-parity.py`.

When the host can run subagents, start three at once, one per default axis: Standards, Spec, Tests. When the ticket has a story criterion, start a fourth in the same turn, axis `UI`. When the host cannot run subagents, run those axis files yourself one after another, writing each axis report to a file before opening the next, so no report depends on memory of the previous one. The axis file's read-only rule binds that pass; step 5 is still yours to write.

On a host that can run subagents, that start is one message, one call per axis you start, each to your host's general-purpose subagent, so they run at once and never see each other's review findings. Name no model and no thinking level: each axis runs on this session's. If your host lets a call restrict what a subagent may do, restrict it to reading, searching and running commands. Each prompt is one sentence naming this skill, the ticket, the base commit, and one axis. The axis word is exactly `Standards`, `Spec`, `Tests`, or `UI`:

```
Use the code-review skill to review ticket #<ticket> from base commit <base commit>, axis Standards.
```

Nothing else: the skill is what they read, and the axis word picks their row in the skill's table. The UI prompt is the same sentence with `axis UI`.

**Hold this turn until every axis you started has reported.** On a host whose subagents run in the background unless told otherwise, ask for them to be waited on. The worker that started you is asleep on your report, and what wakes it is the call in step 5, which cannot be made until the report exists.

## 3. Verify every finding the axes report

Once every axis has reported (and not before), verify each finding at the cited file and line, ahead of any sorting.

At the cited file and line, does the bad outcome the axis describes actually occur? Read beyond the changed lines (follow callers, guards upstream, etc.) until you can answer yes or no. A different finding about nearby code does not settle this one. Judge whether the problem is real, not whether the proposed fix is plausible. Code that loudly fails on a situation you never showed the program can reach is correct behavior, not a defect.

Render exactly one conclusion:

- Holds: the bad outcome does occur at the cited location.
- `refuted`: you checked, and the bad outcome does not happen at the cited location. Write what disproves this specific claim. A true fact about nearby code that does not disprove the claim does not count.
- Could not tell: the diff and surrounding code leave the question open. Sort it as usual and end the line with `unverified: <what would settle it>`.

`refuted` findings go under `## Withdrawn`, each with its refutation. Findings that hold and findings you could not tell go on to step 4.

You do not assign severity, and you do not drop a finding because the fix looks large.

Done when every finding has one conclusion.

## 4. Sort every review finding into in-ticket or out-of-ticket

A review finding is **in-ticket** when it touches one of six things: this ticket's acceptance criteria, a decision in the spec section the ticket names, a baseline under the ticket's `## Read first`, the spec's `## Out of Scope`, the spec's `## Testing Decisions`, or a file inside this ticket's `## Owns`. Everything else is **out-of-ticket**.

A line the Spec axis marks `should not` under its `Decisions` heading is **in-ticket**: it is the worker's own decision or a file it changed outside `## Owns`, so this ticket is where it is undone.

For a finding about a ticket merged into the base branch, apply the same ownership boundary explicitly: a repair target inside this ticket's `## Owns` is in-ticket; one that lies only inside that other ticket's `## Owns` is out-of-ticket and becomes a `finding` child.

The split decides what happens next: in-ticket review findings get one round of fixes on this ticket; out-of-ticket review findings become this ticket's `finding` children (`--sub-issue finding`) and block nothing. The worker opens them; you list them. The parent is this ticket.

The Tests axis splits on one question: is the test case the review finding names one that a `CHECK:` names?

- A test case some `CHECK:` runs → **in-ticket**. That criterion's green is what the review finding is about.
- Any other test file in the diff → by the rule above: **in-ticket** inside this ticket's `## Owns`, **out-of-ticket** outside it.

## 5. Write one review comment on the ticket

Write the report to a file, then hand that file to the `verify-ticket` skill's engine:

```sh
<engine> <ticket> --review <file>
```

What that run does with the file, and what it refuses, is the `verify-ticket` skill's `references/review-report.md`.

The review comment's first line is fixed:

```
REVIEW <base commit>..<HEAD commit>
```

Then the axis reports under `## Standards`, `## Spec` and `## Tests`, verbatim or lightly cleaned, in that order, and `## UI` when that axis ran. Then `## Withdrawn`, each `refuted` finding with the refutation that disproves that specific claim. Then two lists, `## In-ticket` and `## Out-of-ticket`. Both `## In-ticket` and `## Out-of-ticket` use this exact shape for every finding:

```
- <Standards|Spec|Tests|UI> [<category>] <path>:<line> — <claim> — source: <URL|path:line|CHECK evidence>
```

Use the narrowest category already defined by that axis. Standards uses `documented-standard`, `less-code`, `pass-through`, or the original smell name from its smell baseline. Spec uses `Missing`, `Scope creep`, or `Built wrong`. Tests uses `Tautological`, `Implementation-coupled`, `Verified through a side channel`, `Named for the how, not the what`, `Over-mocked`, or `Only the happy path`. UI uses `undecorated`, `overall-look`, or `design-page`.

A finding with no code location of its own (a `Missing`, a `should not` on a line of `Decisions I made on my own`) cites the `## Owns` file its fix would land in, as `<path>:1`.

The source is the current URL, `path:line`, or `CHECK` evidence that proves the finding. When you could not tell, append `unverified: <what would settle it>` at the end of the same line. An empty list says `None`.

End with one line per axis: how many review findings it raised and the worst one within that axis. Rank nothing across axes and merge nothing between them: the separation is what keeps a passing axis from covering a failing one.

Done when `--review` exits 0.

## Default axes and the UI pilot

Three axes run on every ticket. One change can pass one of them and fail another:

- Follows every convention, builds the wrong thing → **Standards pass, Spec fail.**
- Builds exactly what was asked, breaks the repository's conventions → **Spec pass, Standards fail.**
- Does the right thing, proved by a test that would pass either way → **Standards and Spec pass, Tests fail.**

A fourth axis, UI, is a pilot. Step 2 starts it only when the ticket has a story criterion.

## Active Rules

The start prompt names the reviewer Rules the user approved for this review. Apply every active Rule only within its stated scope. Use the Rules to decide what to inspect. Establish every finding and verdict independently from the current ticket, parent spec, repository authority, diff, and checks; every finding still needs a current source, and the report names that source. Ordinary Memory, Working Memory, Thread, worker reasoning, worker self-assessment, and the worker's retrieval results stay outside the review evidence. Complete the review only after every applicable Rule has been applied and every reported finding has a current source. Repository-specific standards remain repository authority and checks, not a global Rule.

## What you do not do

You report. You do not decide whether a review finding is worth fixing, and you do not fix one. The repair path lives in the `implement` skill (one fix round for in-ticket findings, a `finding` child for the rest), and the worker who reads your review comment applies it.
