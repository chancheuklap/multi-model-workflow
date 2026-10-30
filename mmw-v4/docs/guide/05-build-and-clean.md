# Build the change and clean the diff

The build playbooks share one discipline. You say what you observed, and the playbook demands the evidence. This page shows who writes the code in each build playbook, what to put in the request, and the cleanup that keeps a diff reviewable.

## Know who writes the code

A worker the `dispatch` skill sends writes every change, and the session you opened never does. The session's part is to find the plan and write it into a ticket. [Bug fix](../../skills/mmw-mode/playbooks/bug-fix.md), [Perf issue](../../skills/mmw-mode/playbooks/perf-issue.md), [Hillclimb](../../skills/mmw-mode/playbooks/hillclimb.md), [Feature](../../skills/mmw-mode/playbooks/feature.md), [Refactoring](../../skills/mmw-mode/playbooks/refactoring.md) and [Authoring or modifying a skill](../../skills/mmw-mode/playbooks/authoring-a-skill.md) all run the same way:

1. The first step opens a GitHub issue for the ticket, holding only `## Problem`: which playbook it needs, and what was seen, in your words. It also cuts a worktree `.worktrees/fix-<n>` on a branch `fix-<n>`. Whatever the session writes while it finds the plan (a reproduction, a benchmark harness, a sketch, a glossary entry) is committed there.
2. The middle steps are the playbook's own: a bug is reproduced and diagnosed, a slowness measured, a feature designed.
3. The plan is written into the same ticket: what to build, what to read first, where to test, and acceptance criteria that are commands.
4. The last step hands the ticket back to you. You can ask for changes, put it off (it gets `needs-triage`), turn it down, or say go.
5. On your go, the [One ticket](../../skills/mmw-mode/playbooks/one-ticket.md) playbook labels the ticket ready, sends a worker with `dispatch.sh send worker <n>`, and ends its turn. The ticket's `junior-worker` or `senior-worker` label picks the role, and `~/.mmw/models.json` picks that role's host and model.
6. The worker writes the code until the ticket's criteria pass and its reviewer has read it, then closes the ticket. The relay wakes the session with `#<n> ticket.passed`.
7. The session runs the playbook's own check in `.worktrees/issue-<n>`, such as the original reproduction for a bug. It merges the latest project branch into `fix-<n>`, runs `dispatch.sh land <n>`, and opens one pull request, which merges when you say yes.

The `mmw-mode` skill holds a rule behind this. A ticket with acceptance criteria is worked only by a worker the dispatch skill sends. The criteria are commands, so a ticket passes on a machine's verdict, not on the word of the agent that wrote the code.

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

- **Bug fix** reproduces the bug on the same surface a user meets it, through the matching control skill. It narrows the cause by ruling hypotheses out with runtime evidence. The ticket's first criterion is a regression test that fails on the project branch, and the worker commits that failing test before the fix, with the [test-audit skill](../../skills/test-audit/SKILL.md). When the worker is done, the session runs the original reproduction again. If it still fails, nothing lands and the hunt goes back to the cause.
- **Feature** runs the how skill, then writes a throughput checkpoint of four items: what must run first, which work can run in parallel, what state is shared, and the smallest safe split. It uses the prototype skill's branch gate for code shape, names the data shape before any logic and writes the plan into one ticket; a worker builds it, and the session verifies it on the matching surface.
- **Refactoring** pins the current behavior first with a characterization test, a snapshot, or an equivalence script. A type check is not a pin. It deletes dead code before it adds the new shape, migrates every caller and deletes the old API in one wave, and proves the behavior unchanged. If the diff does not make the code easier to read somewhere, it does not land.
- **Improve the architecture** walks the parts of the code that change most, finds where a change is slow or easy to get wrong, and draws the candidates as one page for you, each with a before and after picture. It carries the strongest into Refactoring, whose ticket you say go or no to.
- **Perf issue** captures a baseline trace and vets it with the [benchmark-checklist skill](../../skills/benchmark-checklist/SKILL.md). It tries the performance mantras cheapest first, starting with "don't do it". The ticket's first criterion is the benchmark command, which prints a line only a run that meets the target prints. After the worker is done, the session measures again. A target the numbers miss is reported as missed, never met by changing the benchmark.

For sustained improvement of one number, use **Hillclimb**. Give it the metric, a target, and a floor on attempts:

```text
hillclimb the search p50 on the 60k-row fixture. at least 40% better than baseline and at least 10 iterations.
```

The session builds a measurement harness, proves it can tell a slow case from a fast one, vets it with the benchmark-checklist skill, and freezes it. It posts the baseline as `Attempt 0` on the ticket. The ticket carries the loop, and the worker runs it: one hypothesis per attempt, measured before and after, kept only when the number moves past noise and the regression tests stay green, otherwise reverted in full. Every attempt gets an `Attempt <id>:` comment, kept or reverted. The criterion counts these comments with `gh api`. The session then runs the frozen harness itself and checks that each kept attempt has its commit and each reverted attempt left nothing behind.

To match a design pixel for pixel, write a `toHaveScreenshot` test in `tests/e2e/<product>/` when preparing the ticket, following `verify-<product>`. To align two implementations pixel for pixel, use Refactoring with the screenshot test as its pin.

Sometimes you want the cause before any fix. For a live symptom, such as a leak, an idle CPU spin, or a visual glitch, the [Runtime forensics playbook](../../skills/mmw-mode/playbooks/runtime-forensics.md) instruments the running process. For a profile you already captured, the [Trace forensics playbook](../../skills/mmw-mode/playbooks/trace-forensics.md) reads the file and maps the hot frame to source. Both return a diagnosis, not a fix:

```text
here's a cpuprofile from the slow startup. tell me where the time goes and which source lines own it. no fix yet.
```

## Use test-audit throughout a test's life

The [test-audit skill](../../skills/test-audit/SKILL.md) owns common test judgments and methods. Its writing branch includes TDD and behavior-preserving pins; its other branches handle review, failure diagnosis and audits of existing tests. The mode and existing playbooks reach it when needed. Native test runners and the delivery pipeline keep their own execution responsibilities.

```text
/test-audit audit the checkout tests. preserve each independent contract and identify repeated proof.
```

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

A worker runs the no-comments skill on its branch before it sends its reviewer, and the `mmw-mode` skill's Non-negotiables require it before any review. To run it yourself:

```text
/no-comments the diff
```

## Clean the prose with the unslop skill

The [unslop skill](../../skills/unslop/SKILL.md) removes the patterns that make text read machine-written: filler, hedging, inflated vocabulary, long dashes, and colons used as connectors. The `mmw-mode` skill applies it to every prose surface, the reply included. Commit messages also go through the [technical-writing skill](../../skills/technical-writing/SKILL.md) first. A pull request's body is a fixed record and its owner's page is drawn, as the Opening a PR playbook says. To run it on a file yourself:

```text
/unslop the readme changes
```

Extra code in the diff is caught by review, not by a cleanup skill. The code-review skill's Standards axis asks of every hunk whether the same result exists with less code, and reports the shorter form when it can write it.

**Pitfall.** Cleanup is not optional polish. A diff with narrating comments and defensive dead code reads as unfinished, and the extra code is where the next bug hides. The comment pass and the review run before the pull request opens, not after a reviewer complains.

Next: [Verify and ship](./06-verify-and-ship.md).
