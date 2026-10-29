# Running the session

You are the reviewer: you get the axes run, verify every finding they report, and write the one review report on the ticket.

## 1. Pin the diff

```sh
git rev-parse <base-commit>
git diff <base-commit>...HEAD --stat
git log <base-commit>..HEAD --oneline
```

Three dots, so the comparison runs against the merge-base; it holds only committed work, so a change still uncommitted in the working tree is not reviewed. A ref that does not resolve or an empty diff is a failure here, before the axis subagents spend a context each on nothing. Post it as the review (step 5): the first line with the refs as given, then one line naming the failure; then stop.

Done when both commits resolve and the diff is not empty, or that failure is on the ticket.

## 2. Run the axes

Read the ticket (`gh issue view <ticket>`, comments included), the spec sections its `## Parent` line names, and the spec's `## Out of Scope` and `## Testing Decisions`: step 4 sorts every finding against them. A ticket with no `## Parent` is its own whole spec.

Run four axes: Standards, Spec, Tests and Correctness.

On a host that can run subagents, start one of your host's general-purpose subagents per axis on the `review-axis` row, all in one message, so they run at once and never see each other's findings. Each prompt names the axis's file, the ticket and the base commit, with the file one of `standards-reviewer.md`, `spec-reviewer.md`, `tests-reviewer.md` and `correctness-reviewer.md`:

```
Read the mmw-mode skill in full, then follow the code-review skill's references/standards-reviewer.md: review ticket #<ticket> from base commit <base-commit>, and hand back its Report section's report as your last message. It is your whole task: what came before it is done, and you start no agent it does not name.
```

Nothing else: the mode and the axis file are what they read.

On a host that cannot run subagents, run the axis files yourself, one after another, writing each report to a file before opening the next so no report depends on memory of the previous one. Their read-only rule binds you while you do.

**Hold this turn until every axis you started has reported.** On a host whose subagents run in the background unless told otherwise, ask for them to be waited on. The worker that started you is asleep on your report, and what wakes it is the call in step 5, which cannot be made until the report exists.

## 3. Verify every finding the axes report

The axes read the code in slices, and some of what they report is wrong. The worker treats every in-ticket line as work to do before the ticket closes: a false finding you pass on costs a fix round and can break code that was right; a real one you withdraw ships.

At the cited file and line, does the bad outcome the axis describes actually occur? Read as **principle-read-before-you-conclude** says until you can answer yes or no. A different finding about nearby code does not settle this one. Judge whether the problem is real, not whether the proposed fix is plausible. Code that loudly fails on a situation you never showed the program can reach is correct behavior, not a defect.

Four filters apply while you judge:

- A finding that amounts to "I would have written it differently" is `refuted` unless it shows a concrete problem with the code as written; say that it is a preference.
- A pattern consistent with the rest of the codebase is not a defect of this diff: `refuted`, citing where the codebase does the same.
- An axis whose every finding is a nitpick or a style preference has found the code fine on its question; its line at the end of the report says so (step 5). Its findings are still judged and sorted like any other.
- Before you refute a security or correctness finding, look again: follow its traced path to the end yourself. A finding with a concrete execution path, or one that shows you something you had wrong about the code, is refuted only on evidence, never because it seems unlikely.

Render exactly one conclusion:

- Holds: the bad outcome does occur at the cited location.
- `refuted`: you checked, and the bad outcome does not happen at the cited location. Write what disproves this specific claim. A true fact about nearby code that does not disprove the claim does not count.
- Could not tell: the diff and surrounding code leave the question open.

`refuted` findings go under `## Withdrawn`, each with its refutation. Findings that hold and findings you could not tell go on to step 4.

You report: you do not assign severity, fix a finding, or drop one because its fix looks large.

Done when every finding has one conclusion.

## 4. Sort every review finding into in-ticket or out-of-ticket

The split asks whose work the repair is: in-ticket means this ticket should not close with it unfixed.

A review finding is **in-ticket** when it touches one of six things: this ticket's acceptance criteria, a decision in the spec section the ticket names, a baseline under the ticket's `## Read first`, the spec's `## Out of Scope`, the spec's `## Testing Decisions`, or a file inside this ticket's `## Owns`. Everything else is **out-of-ticket**.

A line the Spec axis marks `should not` under its `Decisions` heading is **in-ticket**: it is the worker's own decision or a file it changed outside `## Owns`, so this ticket is where it is undone.

For a finding about a ticket merged into the base branch, apply the same ownership boundary explicitly: a repair target inside this ticket's `## Owns` is in-ticket; one that lies only inside that other ticket's `## Owns` is out-of-ticket and becomes a `finding` child.

A finding whose fix reaches beyond this ticket's `## Owns` (a restructuring of code the ticket does not own) is **out-of-ticket**, even when the hunk that shows it is inside.

In-ticket findings get one round of fixes on this ticket, because a review never comes back clean: each run finds new judgement calls; out-of-ticket findings become `finding` children the worker opens, and block nothing.

## 5. Write one review report on the ticket

Answer the register-problem skill's three self-check questions before writing the report. Review findings still go in this report for the worker to handle through the existing finding workflow. Register other problems with the register-problem skill's `scripts/register.py add`.

Write the report to a file, then hand that file to the `verify-ticket` skill's `verify-ticket.py`:

```sh
verify-ticket.py <ticket> --review <file>
```

The review report's first line is fixed:

```
REVIEW <base-commit>..<HEAD commit>
```

Then the axis reports under `## Standards`, `## Spec`, `## Tests` and `## Correctness`, verbatim or lightly cleaned, in that order. Then `## Withdrawn`, each `refuted` finding with the refutation that disproves that specific claim. Then two lists, `## In-ticket` and `## Out-of-ticket`. Both `## In-ticket` and `## Out-of-ticket` use this exact shape for every finding:

```
- <Standards|Spec|Tests|Correctness> [<category>] <path>:<line> — <claim> — source: <URL|path:line|CHECK evidence>
```

The category is the name the axis gave the finding: the principle it applies, without the `principle-` prefix (`fail-loudly`); the bug from the Correctness axis's checklist; the Spec kind; or `documented-standard` for a breach of a decision, term, rule or fact the repository documents.

A finding with no code location of its own (a `Missing`, a `should not` on a line of `Decisions I made on my own`) cites the `## Owns` file its fix would land in, as `<path>:1`.

The source is the current URL, `path:line`, or `CHECK` evidence that proves the finding; never the worker's reasoning or its self-assessment. When you could not tell, append `unverified: <what would settle it>` at the end of the same line. An empty list says `None`.

End with one line per axis: how many review findings it raised and the worst one within that axis, or that the code is fine on its question when every finding was a nitpick or a style preference. Rank nothing across axes and merge nothing between them: the separation is what keeps a passing axis from covering a failing one. One change can pass one axis and fail another:

- Follows every convention, builds the wrong thing → **Standards pass, Spec fail.**
- Builds exactly what was asked, breaks the repository's conventions → **Spec pass, Standards fail.**
- Does the right thing, proved by a test that would pass either way → **Standards and Spec pass, Tests fail.**

Done when `--review` exits 0.

