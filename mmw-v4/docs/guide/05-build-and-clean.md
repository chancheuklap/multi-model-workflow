# Build the change and clean the diff

The build playbooks share one discipline. You say what you observed, and the playbook demands the evidence. This page shows who writes the code in each build playbook, what to put in the request, and the cleanup that keeps a diff reviewable.

## Know who writes the code

The `mmw-mode` skill's `## Playbooks` list splits the build playbooks into two groups.

**The session you opened writes the change.** [Feature](../../skills/mmw-mode/playbooks/feature.md), [Refactoring](../../skills/mmw-mode/playbooks/refactoring.md), and [Visual parity](../../skills/mmw-mode/playbooks/visual-parity.md) are for a change you have already described. The session writes it on a branch. When its plan finds slices that share no file, it can give each slice to a native subagent of the host, in its own git worktree. The session reads each subagent's diff before it merges the slice back. All three close with [Shared closing](../../skills/mmw-mode/playbooks/shared-closing.md), which proves the change, has it reviewed, and opens one pull request. [Verify and ship](./06-verify-and-ship.md) covers that closing.

**A dispatched worker writes the fix.** [Bug fix](../../skills/mmw-mode/playbooks/bug-fix.md), [Perf issue](../../skills/mmw-mode/playbooks/perf-issue.md), and [Hillclimb](../../skills/mmw-mode/playbooks/hillclimb.md) start from a problem that is still open. The session you opened does the diagnosis or the measurement itself, then writes one ticket with acceptance criteria and publishes it as a GitHub issue. It then runs **One ticket** of the [Run a night playbook](../../skills/mmw-mode/playbooks/run-a-night.md):

1. It makes a branch `fix-<n>` for the ticket and pushes it.
2. It sends a worker with `dispatch.sh send worker <n>` and ends its turn. The ticket's `junior-worker` or `senior-worker` label picks the role, and `~/.mmw/models.json` picks that role's host and model.
3. The worker writes the code until the ticket's criteria pass and its reviewer has read it, then closes the ticket. The relay wakes the session with `#<n> ticket.passed`.
4. The session checks the result the way the playbook says, in the ticket's worktree `.worktrees/issue-<n>`. It then runs `dispatch.sh land <n>`.
5. It opens one pull request from `fix-<n>` to the project branch and merges it when you say yes.

The `mmw-mode` skill holds a rule behind this split. A ticket with acceptance criteria is worked only by a worker the dispatch skill sends. The criteria are commands, so a ticket passes on a machine's verdict, not on the word of the agent that wrote the code.

## Prompt each build playbook with what you know

A bug request states the symptom and asks for a reproduction first:

```text
this command emits two records after a retry. reproduce it first, then fix it and show me it's gone.
```

A feature request states the behavior and what must not change:

```text
add a --json flag. text output stays byte-identical. verify both forms.
```

A refactoring request pins behavior before structure moves:

```text
move parsing into one module, zero behavior change. record the current output first and prove it's unchanged after.
```

A perf request states a measurement, not an impression:

```text
startup takes 1.8s on this fixture. trace it, fix the measured cause, show me before and after.
```

Each request routes to its playbook, and the playbook supplies the steps you did not type.

- **Bug fix** reproduces the bug on the same surface a user meets it, through the matching control skill. It narrows the cause by ruling hypotheses out with runtime evidence. The ticket's first criterion is a regression test that fails on the project branch, and the worker commits that failing test before the fix, with the [tdd skill](../../skills/tdd/SKILL.md). When the worker is done, the session runs the original reproduction again. If it still fails, nothing lands and the hunt goes back to the cause.
- **Feature** runs the how skill and the architect skill, then writes a throughput checkpoint of four items: what must run first, which work can run in parallel, what state is shared, and the smallest safe split. It names the data shape before any logic, writes the code, verifies on the matching surface, and rebases into small ordered commits.
- **Refactoring** pins the current behavior first with a characterization test, a snapshot, or an equivalence script. A type check is not a pin. It deletes dead code before it adds the new shape, migrates every caller and deletes the old API in one wave, and proves the behavior unchanged. If the diff does not make the code easier to read somewhere, it reverts the diff.
- **Perf issue** captures a baseline trace and vets it with the [benchmark-checklist skill](../../skills/benchmark-checklist/SKILL.md). It tries the performance mantras cheapest first, starting with "don't do it". The ticket's first criterion is the benchmark command, which prints a line only a run that meets the target prints. After the worker is done, the session measures again. A target the numbers miss is reported as missed, never met by changing the benchmark.

For sustained improvement of one number, use **Hillclimb**. Give it the metric, a target, and a floor on attempts:

```text
hillclimb the search p50 on the 60k-row fixture. at least 40% better than baseline and at least 10 iterations.
```

The session builds a measurement harness, proves it can tell a slow case from a fast one, vets it with the benchmark-checklist skill, and freezes it. It opens a decision log `decision.tsv` under `efforts/<effort>/` whose first row is the baseline. The ticket carries the loop, and the worker runs it: one hypothesis per attempt, measured before and after, kept only when the number moves past noise and the regression tests stay green, otherwise reverted in full. Every attempt gets a row, kept or reverted. The session then runs the frozen harness itself and checks that each kept row has its commit and each reverted row left nothing behind.

For pixel-exact UI work, use **Visual parity**:

```text
migrate the settings panel to the new styling system. it must match the current screenshots pixel for pixel.
```

It builds the screenshot baseline before any change. It never edits the harness or the baseline to make a diff pass. It migrates one component at a time until the image diff is zero.

Sometimes you want the cause before any fix. For a live symptom, such as a leak, an idle CPU spin, or a visual glitch, the [Runtime forensics playbook](../../skills/mmw-mode/playbooks/runtime-forensics.md) instruments the running process. For a profile you already captured, the [Trace forensics playbook](../../skills/mmw-mode/playbooks/trace-forensics.md) reads the file and maps the hot frame to source. Both return a diagnosis, not a fix:

```text
here's a cpuprofile from the slow startup. tell me where the time goes and which source lines own it. no fix yet.
```

## Write the failing test first with the tdd skill

The tdd skill is the red-to-green loop. Each cycle writes one test that fails for the intended reason, then only enough code to make it pass, then runs that one test. Tests go only at seams agreed in writing. With a ticket, the seams are the ones its `## Seam` section names. With no ticket, the session writes the seams down and confirms them with you before any test is written:

```text
/tdd add the empty-cart case to checkout. test it at the checkout api, not the cart internals.
```

The skill rejects three kinds of test. One breaks on a refactor that changes no behavior. One recomputes its expected value the way the code does, so it can never disagree with the code. One belongs to a batch of tests written before any code. Refactoring is a separate pass after every slice is green. The skill's report names the test that failed before the change, the failure it printed, and the run that passed after.

## Let the mode load the TypeScript rules

The `mmw-mode` skill's Non-negotiables load the [typescript-best-practices skill](../../skills/typescript-best-practices/SKILL.md) whenever a session reads or edits a `.ts` or `.tsx` file. It turns the type-system principles into concrete rules: discriminated unions, `unknown` at boundaries, no `as` casts before validation, and exhaustive switches. You do not need to name it.

## Strip the comments with the no-comments skill

Comments need their own pass, and not from the agent that wrote them, because an author defends its own comments. The [no-comments skill](../../skills/no-comments/SKILL.md) sends one fresh subagent that works from [`references/comment-sicko.md`](../../skills/no-comments/references/comment-sicko.md), a reader with a short keep list:

- Legal or license headers.
- Behavior forced by an external dependency, platform, or protocol you cannot change.
- Lint suppressions whose rule is faulty or style-only.
- Doc comments that define a public API.
- Issue or RFC links that explain a constraint the code cannot express.

Everything else goes. A comment that explains a surprise in your own code comes back as a `MUST KILL` flag on the symbol, and the skill fixes the code so the comment is no longer needed. When a comment claims a constraint, such as "do not remove", the skill offers to encode the claim as a type, a test, or a lint before it deletes the comment.

Shared closing runs the no-comments skill on every day change before review, and the `mmw-mode` skill's Non-negotiables require it before any review. To run it yourself:

```text
/no-comments the diff
```

## Clean the prose with the unslop skill

The [unslop skill](../../skills/unslop/SKILL.md) removes the patterns that make text read machine-written: filler, hedging, inflated vocabulary, long dashes, and colons used as connectors. The `mmw-mode` skill applies it to every prose surface, the reply included. PR titles, PR descriptions, and commit messages also go through the [technical-writing skill](../../skills/technical-writing/SKILL.md) first, as Shared closing's **The pull request** says. To run it on a file yourself:

```text
/unslop the readme changes
```

Extra code in the diff is caught by review, not by a cleanup skill. The code-review skill's Standards axis asks of every hunk whether the same result exists with less code, and reports the shorter form when it can write it.

**Pitfall.** Cleanup is not optional polish. A diff with narrating comments and defensive dead code reads as unfinished, and the extra code is where the next bug hides. The comment pass and the review run before the pull request opens, not after a reviewer complains.

Next: [Verify and ship](./06-verify-and-ship.md).
