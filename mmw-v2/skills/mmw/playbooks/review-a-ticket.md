### Review a ticket

**You own the one review report; verify every finding, fix none.**

A worker wrote this diff and the tests that prove it, and watched them pass. This review is the first reading by anyone who did not write it: what it reports, the worker fixes before the ticket closes; what it misses ships.

Commands of this skill's `bash scripts/dispatch.sh` and `python3 scripts/ticket_state.py` are named bare below.

**Entry.**
- **Started by `start`.** The start prompt names the ticket, the base commit and **Pin the diff**. Read the file its `Data:` names first: it holds the installed paths, the reviewer Rules the user approved and the path of each axis brief.
- **Compacted, or unsure.** Go to **Where you are**.

**Where you are.** Run `dispatch.sh where <n>` and go to the step it prints. Only **Write the report**, or a failed **Pin the diff** through the same command, writes on the ticket, so running the earlier steps again repeats no write.

#### Steps

1. **Pin the diff.** Run `git rev-parse <base-commit>`, `git diff <base-commit>...HEAD --stat` and `git log <base-commit>..HEAD --oneline`.

   Three dots, so the comparison runs against the merge-base. A ref that does not resolve or an empty diff is a failure here, before the axis subagents spend a context each on nothing. Post it as the review with `ticket_state.py <n> --review <file>`, as **Write the report** says: the first line with the refs as given, then one line naming the failure; then stop.

   Done when both commits resolve and the diff is not empty, or that failure is on the ticket.
2. **Run the axes.** Read the ticket. A **story criterion** is a `CHECK:` that names `story-parity.py`.

   When the ticket has a story criterion, run four axes: Standards, Spec, Tests and UI. Otherwise run the first three.

   On a host that can run subagents, start one of your host's general-purpose subagents per axis, all in one message, so they run at once and never see each other's findings. Each prompt is one line, `Read <brief path> and review ticket #<ticket> from base commit <base-commit>, axis <Axis>.`, where `<brief path>` is the absolute path of that axis's brief from the `Review brief` lines of the file the start prompt's `Data:` names. The axis word is exactly `Standards`, `Spec`, `Tests`, or `UI`.

   The Spec axis's line ends with `dispatch.sh: <path>.`, the path the same file gives for `dispatch.sh`, because that brief runs `landed-since` and the axis reads nothing else that says where the script is.

   Nothing else: the brief is what they read.

   On a host that cannot run subagents, run the axis files yourself, one after another, writing each report to a file before opening the next so no report depends on memory of the previous one. Their read-only rule binds you while you do.

   **Hold this turn until every axis you started has reported.** The worker that started you is asleep on your report, and what wakes it is the call in **Write the report**, which cannot be made until the report exists.

   Done when every axis you started has reported and each report is in a file.
3. **Verify every finding.** The axes read the code in slices, and some of what they report is wrong. The worker treats every in-ticket line as work to do before the ticket closes: a false finding you pass on costs a fix round and can break code that was right; a real one you withdraw ships.

   At the cited file and line, does the bad outcome the axis describes actually occur? Read beyond the changed lines (follow callers, guards upstream, etc.) until you can answer yes or no. A different finding about nearby code does not settle this one. Judge whether the problem is real, not whether the proposed fix is plausible. Code that loudly fails on a situation you never showed the program can reach is correct behavior, not a defect.

   Render exactly one conclusion (**principle-clues-are-not-evidence**):

   - Holds: the bad outcome does occur at the cited location.
   - `refuted`: you checked, and the bad outcome does not happen at the cited location. Write what disproves this specific claim. A true fact about nearby code that does not disprove the claim does not count.
   - Could not tell: the diff and surrounding code leave the question open.

   `refuted` findings go under `## Withdrawn`, each with its refutation. Findings that hold and findings you could not tell go on to **Sort in-ticket and out-of-ticket**.

   You report: you do not assign severity, fix a finding, or drop one because its fix looks large.

   `#### Active Rules` and `#### Unattended outlets` hold until the report is posted.

   Done when every finding has one conclusion.
4. **Sort in-ticket and out-of-ticket.** (judgement) The split asks whose work the repair is: in-ticket means this ticket should not close with it unfixed.

   A review finding is **in-ticket** when it touches one of six things: this ticket's acceptance criteria, a decision in the spec section the ticket names, a baseline under the ticket's `## Read first`, the spec's `## Out of Scope`, the spec's `## Testing Decisions`, or a file inside this ticket's `## Owns`. Everything else is **out-of-ticket**.

   A line the Spec axis marks `should not` under its `Decisions` heading is **in-ticket**: it is the worker's own decision or a file it changed outside `## Owns`, so this ticket is where it is undone.

   For a finding about a ticket merged into the base branch, apply the same ownership boundary explicitly: a repair target inside this ticket's `## Owns` is in-ticket; one that lies only inside that other ticket's `## Owns` is out-of-ticket and becomes a `finding` child.

   In-ticket findings get one round of fixes on this ticket; out-of-ticket findings become `finding` children the worker opens, and block nothing.

   A finding whose repair would change a sentence this ticket's `## Moves` fixes word for word is neither in-ticket nor out-of-ticket: the worker may not change that sentence, so write it under `## Manifest notes`, quoting the sentence and the change you propose.

   Done when every finding that holds or that you could not tell is under `## In-ticket`, `## Out-of-ticket` or `## Manifest notes`.
5. **Write the report.** Write the report to a file in the shape `#### Report format` gives, then hand that file to `ticket_state.py <n> --review <file>`.

   Done when `--review` exits 0.

#### Active Rules

The file the start prompt's `Data:` names lists the reviewer Rules the user approved, or `none`. Apply each Rule only within its stated scope, to decide what to inspect, and finish only when every applicable Rule has been applied. A Rule is never a finding's source, and neither are Memory, the worker's reasoning or its self-assessment: each finding cites the current ticket, spec, repository or check.

#### Unattended outlets

When you could not tell, append `unverified: <what would settle it>` at the end of that finding's line in the `REVIEW` report. At the end of the report, after the line per axis, write each step you skipped as `skip: <step title>: <reason>` and each principle that changed a decision, with the choice it changed.

#### Report format

The review report's first line is fixed:

```
REVIEW <base-commit>..<HEAD commit>
```

Then the axis reports under `## Standards`, `## Spec` and `## Tests`, verbatim or lightly cleaned, in that order, and `## UI` when that axis ran. Then `## Withdrawn`, each `refuted` finding with the refutation that disproves that specific claim. Then two lists, `## In-ticket` and `## Out-of-ticket`. Both `## In-ticket` and `## Out-of-ticket` use this exact shape for every finding:

```
- <Standards|Spec|Tests|UI> [<category>] <path>:<line> — <claim> — source: <URL|path:line|CHECK evidence>
```

The category is the name the axis gave the finding: its smell, its Tests shape, its Spec or UI kind, or `documented-standard` for a breach of a rule the repository documents; a Standards finding that is none of these is `less-code` or `pass-through`.

A finding with no code location of its own (a `Missing`, a `should not` on a line of `Decisions I made on my own`) cites the `## Owns` file its fix would land in, as `<path>:1`.

The source is the current URL, `path:line`, or `CHECK` evidence that proves the finding. An empty list says `None`.

`## Manifest notes` follows `## Out-of-ticket`: one line per finding on a sentence the ticket's `## Moves` fixes, the sentence quoted, then the proposed change; `None` when there is none.

End with one line per axis: how many review findings it raised and the worst one within that axis. Rank nothing across axes and merge nothing between them: the separation is what keeps a passing axis from covering a failing one. One change can pass one axis and fail another:

- Follows every convention, builds the wrong thing → **Standards pass, Spec fail.**
- Builds exactly what was asked, breaks the repository's conventions → **Spec pass, Standards fail.**
- Does the right thing, proved by a test that would pass either way → **Standards and Spec pass, Tests fail.**

**Reply:** the `REVIEW <base-commit>..<HEAD commit>` comment `--review` posted.
