# Steer with principle names

The skill set has 35 principles, each a skill of its own under `skills/principle-<slug>/`. The `## Principles` section of the `mmw-mode` skill ([mmw-mode](../../skills/mmw-mode/SKILL.md)) indexes them: one line per principle, naming when it applies and the rule. Every session reads that index with the mode. A session reads a principle's own file in full when it applies it, and its reply names each principle that shaped a decision and the choice it changed. The mode allows a session to cite only a principle whose file it read in that session.

You do not invoke principles. Their names are for steering. Each name points at a complete rule the session already has an index line for, so one phrase redirects the work more precisely than a paragraph of instructions.

## Steering in practice

Say the session is about to add a new adapter beside three old ones:

```text
use principle-subtract-before-you-add. delete the obsolete adapters first, then design what's left.
```

Say it claims success because the build passed:

```text
apply principle-prove-it-works. run the real import flow and show me the written records.
```

Say two parallel attempts are about to write to the same branch:

```text
principle-separate-before-serializing-shared-state. give each attempt its own worktree, no locks.
```

Each phrase works because the rule behind it is specific. The session still has to say, in its reply, which decision the rule changed. A principle cited with no decision behind it was named, not applied.

## The 35, by the mode's groups

Each line below gives the rule as the mode's index and the principle's own file state it. The frontmatter `description` of every principle is the same sentence (`Run only when the user, mmw-mode or another skill names it`), because a principle is reached through its index line, not by its description.

### Core

How much to build, and when to rethink the design.

- [`principle-laziness-protocol`](../../skills/principle-laziness-protocol/SKILL.md). Aim for the most result with the least code and complexity; prefer deletion and the smallest change that solves the problem.
- [`principle-foundational-thinking`](../../skills/principle-foundational-thinking/SKILL.md). Get the core types and data structures right before writing logic.
- [`principle-redesign-from-first-principles`](../../skills/principle-redesign-from-first-principles/SKILL.md). Integrate a new requirement as if it had been there from the start, instead of bolting it on.
- [`principle-attack-the-premise`](../../skills/principle-attack-the-premise/SKILL.md). When two or more fixes that share one premise have failed the same gate, write the premise down and test it directly before another fix that assumes it.
- [`principle-subtract-before-you-add`](../../skills/principle-subtract-before-you-add/SKILL.md). Remove dead weight first, then build on the simpler base.
- [`principle-minimize-reader-load`](../../skills/principle-minimize-reader-load/SKILL.md). Count the layers and hidden state a reader must trace, and reduce them.
- [`principle-outcome-oriented-execution`](../../skills/principle-outcome-oriented-execution/SKILL.md). Converge on the target design; do not keep throwaway compatibility states.
- [`principle-experience-first`](../../skills/principle-experience-first/SKILL.md). When implementation convenience conflicts with the user's experience, choose the user's experience.
- [`principle-exhaust-the-design-space`](../../skills/principle-exhaust-the-design-space/SKILL.md). For a decision with no precedent, build two or three competing prototypes and compare them before committing.
- [`principle-first-principles-thinking`](../../skills/principle-first-principles-thinking/SKILL.md). Before refining a plan, ask whether it should exist; keep only the constraints with independent support and rebuild the simplest solution.
- [`principle-start-from-what-exists`](../../skills/principle-start-from-what-exists/SKILL.md). Search this repository, then GitHub and the package registries, before building; the reply records the search.
- [`principle-read-before-you-conclude`](../../skills/principle-read-before-you-conclude/SKILL.md). Read a file before saying anything about it or changing it, and label a conclusion that rests on an unread part as inferred.
- [`principle-build-the-lever`](../../skills/principle-build-the-lever/SKILL.md). For non-trivial work, build the tool that does or proves it (a codemod, a script, a generator), so a reviewer can rerun it.

### Architecture

Where state, validation and compatibility live.

- [`principle-model-the-domain`](../../skills/principle-model-the-domain/SKILL.md). Encode the domain in one structure (a state machine, a typed model, a table) instead of scattered conditionals.
- [`principle-boundary-discipline`](../../skills/principle-boundary-discipline/SKILL.md). Validate and handle errors at system boundaries, trust internal types, and keep business logic in pure functions.
- [`principle-type-system-discipline`](../../skills/principle-type-system-discipline/SKILL.md). Make illegal states unrepresentable, and parse external data at the boundary.
- [`principle-make-operations-idempotent`](../../skills/principle-make-operations-idempotent/SKILL.md). An operation that runs twice, or after a crash halfway, converges to the same end state.
- [`principle-migrate-callers-then-delete-legacy-apis`](../../skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md). When a new internal API replaces an old one, migrate every caller and delete the old API in one wave.
- [`principle-separate-before-serializing-shared-state`](../../skills/principle-separate-before-serializing-shared-state/SKILL.md). When concurrent actors might write the same file, branch, key or object, remove the sharing first; add locking only when the sharing is real.

### Verification

What counts as proof.

- [`principle-prove-it-works`](../../skills/principle-prove-it-works/SKILL.md). Check the real artifact directly, not a proxy, a self-report or "it compiles".
- [`principle-fix-root-causes`](../../skills/principle-fix-root-causes/SKILL.md). Trace each symptom back to the first place the system went wrong and fix it there; a guard counts as a fix only when the state it handles is legitimate.
- [`principle-sequence-verifiable-units`](../../skills/principle-sequence-verifiable-units/SKILL.md). Break work into small units that each end in a check, and verify each before starting the next.
- [`principle-test-behavior-not-implementation`](../../skills/principle-test-behavior-not-implementation/SKILL.md). Assert what the code's users can observe, so a test fails when that behavior breaks and keeps passing when only the internals change.
- [`principle-baseline-is-the-contract`](../../skills/principle-baseline-is-the-contract/SKILL.md). A settled conclusion (an answer, a winning prototype, a signed-off page) is copied, never improved from memory; a gap goes to whoever owns it.
- [`principle-run-the-smallest-test-set`](../../skills/principle-run-the-smallest-test-set/SKILL.md). Run the smallest set of tests that proves the change; a full suite only when a gate requires it or a named risk does.
- [`principle-explain-the-number`](../../skills/principle-explain-the-number/SKILL.md). Before trusting or reporting a measured number, find what limits it and rule out that it measured something else. The [benchmark-checklist](../../skills/benchmark-checklist/SKILL.md) skill applies it to a benchmark.
- [`principle-fail-loudly`](../../skills/principle-fail-loudly/SKILL.md). A check, guard or refusal that cannot do its job says what failed, what was expected and where to change it; one that checked nothing never reports a pass. The review's Standards and Correctness axes judge a diff by it.

### Delegation

How work is shared between sessions.

- [`principle-guard-the-context-window`](../../skills/principle-guard-the-context-window/SKILL.md). Send bulk reading to subagents and keep summaries in the main session.
- [`principle-never-block-on-the-human`](../../skills/principle-never-block-on-the-human/SKILL.md). Proceed on reversible work and present the result; ask only for a decision that is the owner's.
- [`principle-progress-is-what-the-record-says`](../../skills/principle-progress-is-what-the-record-says/SKILL.md). Where the work stands is what the ticket, the branch, the map or the resume note says, not what the session remembers.

### Writing

How anything another reader picks up is written.

- [`principle-everything-at-hand`](../../skills/principle-everything-at-hand/SKILL.md). Making any page or diagram for a person, put everything needed to understand each place where the reader looks at that place.
- [`principle-write-for-where-it-is-read`](../../skills/principle-write-for-where-it-is-read/SKILL.md). Before writing a brief, a spec, a ticket, a document or a script's output, name who reads it, what they are doing then, and what they can see.
- [`principle-anchor-every-reference`](../../skills/principle-anchor-every-reference/SKILL.md). Use the source name so the reader can identify each reference in the current sentence or paragraph. Add a path and location when the reader needs to find or check the source.
- [`principle-files-describe-the-present`](../../skills/principle-files-describe-the-present/SKILL.md). A file says only what is true now; what changed and why goes in the commit message and the reply.

### Meta

- [`principle-encode-lessons-in-structure`](../../skills/principle-encode-lessons-in-structure/SKILL.md). An instruction written a second time becomes a lint, a metadata flag, a runtime check or a script instead. The [correct](../../skills/correct/SKILL.md) skill applies it to a whole repository, as [Make it yours](./09-make-it-yours.md) shows.

Do not memorize the list. Skim it now, and come back when a session does something a name here would have prevented.

Next: [Make it yours](./09-make-it-yours.md).
