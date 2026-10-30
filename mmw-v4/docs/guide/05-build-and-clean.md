# Build the change and clean the diff

The build playbooks share one discipline. You say what you observed, and the playbook demands the evidence. This page shows who writes the code in each build playbook, what to put in the request, and the cleanup that keeps a diff reviewable.

## Know who writes the code

A dispatched worker writes ordinary code and scripts. [Develop a change](../../skills/mmw-mode/playbooks/develop-a-change.md) prepares the requested change using existing materials and only the methods it needs. Skill text that one ticket can carry is the exception: [Authoring or modifying a skill](../../skills/mmw-mode/playbooks/authoring-a-skill.md) writes it and proves its behavior with a fresh agent.

1. Keep the existing issue and effort branch, or create a preparation record before durable assets.
2. Fill missing evidence and decisions with the relevant methods. A clear small change needs no interview or spec.
3. Use to-tickets for one independent change, or to-spec and the batch entry for coordinated units.
4. Existing execution Go carries forward. Otherwise return the prepared plan and the remaining owner decision.
5. One ticket executes an independent ticket; Run a night executes a spec batch, even with one ticket. The existing worker, independent review, final proof and landing protocol remain.
6. The executor reads the actual method and product verification sources, then delivers one runnable PR. The owner runs it, scoped feedback is repaired in the same PR, and acceptance of the checked version precedes merge / finish.

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

The mode routes a code-change request to preparation, a ready result directly to its executor, or a read-only question to diagnosis. Specialist methods can be combined inside the same task.

- **Bug fix** reproduces the bug on the same surface a user meets it, through the matching control skill. It narrows the cause by ruling hypotheses out with runtime evidence. The ticket's first criterion is a regression test that fails on the project branch, and the worker commits that failing test before the fix, with the [test-audit skill](../../skills/test-audit/SKILL.md). When the worker is done, the session runs the original reproduction again. If it still fails, nothing lands and the hunt goes back to the cause.
- **Develop a change** uses the how skill and considers four decomposition questions: what must run first, which work can run in parallel, what state is shared, and the smallest safe split. It uses the prototype skill's branch gate for code shape, names the data shape before any logic and writes an independent ticket or spec batch; a worker builds it, and the session verifies it on the matching surface.
- **Refactoring** pins the current behavior first with a characterization test, a snapshot, or an equivalence script. A type check is not a pin. It deletes dead code before it adds the new shape, migrates every caller and deletes the old API in one wave, and proves the behavior unchanged. If the diff does not make the code easier to read somewhere, it does not land.
- **Improve the architecture** walks the parts of the code that change most, finds where a change is slow or easy to get wrong, and draws the candidates as one page for you, each with a before and after picture. A report-only request ends there. An authorized candidate continues through Develop a change with the refactoring method.
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
