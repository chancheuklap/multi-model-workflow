# Running the session

You are the reviewer session: you get the axes run, verify every finding they report, and write the one review comment on the ticket.

## Resolve `<engine>` once

`<engine>` in step 5 is the command the `verify-ticket` skill resolves in its own `SKILL.md`. Resolve it from that skill's `SKILL.md`; the path differs by machine and by host.

## 1. Pin the diff

```sh
git rev-parse <base-commit>
git diff <base-commit>...HEAD --stat
git log <base-commit>..HEAD --oneline
```

Three dots, so the comparison runs against the merge-base. A ref that does not resolve or an empty diff is a failure here, before the axis subagents spend a context each on nothing. Post it as the review (step 5): the first line with the refs as given, then one line naming the failure; then stop.

Done when both commits resolve and the diff is not empty, or that failure is on the ticket.

## 2. Run the axes

Read the ticket. A **story criterion** is a `CHECK:` that names `story-parity.py`.

When the ticket has a story criterion, run four axes: Standards, Spec, Tests and UI. Otherwise run the first three.

On a host that can run subagents, start one of your host's general-purpose subagents per axis, all in one message, so they run at once and never see each other's findings. Name no model and no thinking level: each axis runs on this session's. Each prompt is one sentence naming this skill, the ticket, the base commit, and one axis. The axis word is exactly `Standards`, `Spec`, `Tests`, or `UI`:

```
Use the code-review skill to review ticket #<ticket> from base commit <base commit>, axis Standards.
```

Nothing else: the skill is what they read, and the axis word picks their file in the skill's table.

On a host that cannot run subagents, run the axis files yourself, one after another, writing each report to a file before opening the next so no report depends on memory of the previous one. Their read-only rule binds you while you do.

**Hold this turn until every axis you started has reported.** On a host whose subagents run in the background unless told otherwise, ask for them to be waited on. The worker that started you is asleep on your report, and what wakes it is the call in step 5, which cannot be made until the report exists.

## 3. Verify every finding the axes report

At the cited file and line, does the bad outcome the axis describes actually occur? Read beyond the changed lines (follow callers, guards upstream, etc.) until you can answer yes or no. A different finding about nearby code does not settle this one. Judge whether the problem is real, not whether the proposed fix is plausible. Code that loudly fails on a situation you never showed the program can reach is correct behavior, not a defect.

Render exactly one conclusion:

- Holds: the bad outcome does occur at the cited location.
- `refuted`: you checked, and the bad outcome does not happen at the cited location. Write what disproves this specific claim. A true fact about nearby code that does not disprove the claim does not count.
- Could not tell: the diff and surrounding code leave the question open.

`refuted` findings go under `## Withdrawn`, each with its refutation. Findings that hold and findings you could not tell go on to step 4.

You report: you do not assign severity, fix a finding, or drop one because its fix looks large.

Done when every finding has one conclusion.

## 4. Sort every review finding into in-ticket or out-of-ticket

A review finding is **in-ticket** when it touches one of six things: this ticket's acceptance criteria, a decision in the spec section the ticket names, a baseline under the ticket's `## Read first`, the spec's `## Out of Scope`, the spec's `## Testing Decisions`, or a file inside this ticket's `## Owns`. Everything else is **out-of-ticket**.

A line the Spec axis marks `should not` under its `Decisions` heading is **in-ticket**: it is the worker's own decision or a file it changed outside `## Owns`, so this ticket is where it is undone.

For a finding about a ticket merged into the base branch, apply the same ownership boundary explicitly: a repair target inside this ticket's `## Owns` is in-ticket; one that lies only inside that other ticket's `## Owns` is out-of-ticket and becomes a `finding` child.

In-ticket findings get one round of fixes on this ticket; out-of-ticket findings become `finding` children the worker opens, and block nothing.

## 5. Write one review comment on the ticket

Write the report to a file, then hand that file to the `verify-ticket` skill's engine:

```sh
<engine> <ticket> --review <file>
```

The review comment's first line is fixed:

```
REVIEW <base commit>..<HEAD commit>
```

Then the axis reports under `## Standards`, `## Spec` and `## Tests`, verbatim or lightly cleaned, in that order, and `## UI` when that axis ran. Then `## Withdrawn`, each `refuted` finding with the refutation that disproves that specific claim. Then two lists, `## In-ticket` and `## Out-of-ticket`. Both `## In-ticket` and `## Out-of-ticket` use this exact shape for every finding:

```
- <Standards|Spec|Tests|UI> [<category>] <path>:<line> — <claim> — source: <URL|path:line|CHECK evidence>
```

The category is the name the axis gave the finding: its smell, its Tests shape, its Spec or UI kind, or `documented-standard` for a breach of a rule the repository documents; a Standards finding that is none of these is `less-code` or `pass-through`.

A finding with no code location of its own (a `Missing`, a `should not` on a line of `Decisions I made on my own`) cites the `## Owns` file its fix would land in, as `<path>:1`.

The source is the current URL, `path:line`, or `CHECK` evidence that proves the finding. When you could not tell, append `unverified: <what would settle it>` at the end of the same line. An empty list says `None`.

End with one line per axis: how many review findings it raised and the worst one within that axis. Rank nothing across axes and merge nothing between them: the separation is what keeps a passing axis from covering a failing one. One change can pass one axis and fail another:

- Follows every convention, builds the wrong thing → **Standards pass, Spec fail.**
- Builds exactly what was asked, breaks the repository's conventions → **Spec pass, Standards fail.**
- Does the right thing, proved by a test that would pass either way → **Standards and Spec pass, Tests fail.**

Done when `--review` exits 0.

## Active Rules

The start prompt lists the reviewer Rules the user approved, or `none`. Apply each Rule only within its stated scope, to decide what to inspect, and finish only when every applicable Rule has been applied. A Rule is never a finding's source, and neither are Memory, the worker's reasoning or its self-assessment: each finding cites the current ticket, spec, repository or check.
