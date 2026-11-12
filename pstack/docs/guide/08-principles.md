# Steer with principle names

pstack ships 32 principles as individual skills. [poteto-mode](../../skills/poteto-mode/SKILL.md) reads their index at the start of every multi-step task, applies the ones the task triggers, and names each applied principle in its reply along with the decision it changed.

The mode index and each skill's description say when the rule applies. You can steer with its name. The agent reads the full rule when the task calls for it, including when another skill names it.

## Steering in practice

Say the agent is about to bolt a new adapter onto three existing ones:

```text
use subtract before you add. delete the obsolete adapters first, then design what's left.
```

Say it claims success because the build passed:

```text
apply prove it works. run the real import flow and show me the written records.
```

Say two parallel attempts are about to write to the same branch:

```text
separate before serializing shared state. give each attempt its own worktree, no locks.
```

Each phrase lands because the rule behind it is specific. The agent still has to say, in its reply, which decision the rule changed. A principle citation with no decision behind it means the agent named the rule without applying it.

## The 32, briefly

The core principles decide how much to build and when to rethink the design:

- [principle-laziness-protocol](../../skills/principle-laziness-protocol/SKILL.md) prefers deletion and the smallest change that solves the problem.
- [principle-foundational-thinking](../../skills/principle-foundational-thinking/SKILL.md) chooses the core data structures before writing logic.
- [principle-first-principles-thinking](../../skills/principle-first-principles-thinking/SKILL.md) tests the assumptions behind an unsettled plan before you invest in it.
- [principle-redesign-from-first-principles](../../skills/principle-redesign-from-first-principles/SKILL.md) integrates a new requirement as if it had been there from day one.
- [principle-baseline-is-the-contract](../../skills/principle-baseline-is-the-contract/SKILL.md) preserves what an approved spec, prototype, or answer actually settled. A timing prototype can settle a timing decision without setting the UI.
- [principle-attack-the-premise](../../skills/principle-attack-the-premise/SKILL.md) writes down the premise that two or more failed fixes shared and tests it directly before the next fix.
- [principle-subtract-before-you-add](../../skills/principle-subtract-before-you-add/SKILL.md) removes dead weight first and asks which failure or requirement justifies a new guard.
- [principle-minimize-reader-load](../../skills/principle-minimize-reader-load/SKILL.md) reduces the layers and hidden state a reader must trace. A helper earns its place through reuse, a complex boundary, or a name that makes the caller clearer.
- [principle-outcome-oriented-execution](../../skills/principle-outcome-oriented-execution/SKILL.md) converges rewrites on the target design instead of preserving throwaway compatibility states.
- [principle-experience-first](../../skills/principle-experience-first/SKILL.md) chooses the user's result over implementation convenience.
- [principle-start-from-what-exists](../../skills/principle-start-from-what-exists/SKILL.md) looks for an implementation you could use or extend before you start a new one.
- [principle-exhaust-the-design-space](../../skills/principle-exhaust-the-design-space/SKILL.md) builds two or three competing prototypes when there's no precedent.
- [principle-build-the-lever](../../skills/principle-build-the-lever/SKILL.md) builds the script that does or proves the work, so a reviewer can rerun it. When an agent keeps doing the same thing by hand, have it write the tool or skill it wishes it had. If a script can do a step the same way every time, use the script, and save agents for the judgment calls.

The architecture principles decide where state, validation, and compatibility live:

- [principle-model-the-domain](../../skills/principle-model-the-domain/SKILL.md) encodes repeated rules in one structure, not scattered conditionals.
- [principle-boundary-discipline](../../skills/principle-boundary-discipline/SKILL.md) validates input at its boundary and catches errors where they can be handled or translated for the caller.
- [principle-type-system-discipline](../../skills/principle-type-system-discipline/SKILL.md) makes illegal states unrepresentable.
- [principle-make-operations-idempotent](../../skills/principle-make-operations-idempotent/SKILL.md) converges retries on the same end state.
- [principle-migrate-callers-then-delete-legacy-apis](../../skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md) migrates and deletes in one wave.
- [principle-separate-before-serializing-shared-state](../../skills/principle-separate-before-serializing-shared-state/SKILL.md) removes the sharing before adding coordination.

The verification principles define what counts as proof:

- [principle-read-before-you-conclude](../../skills/principle-read-before-you-conclude/SKILL.md) checks what the source and its callers actually establish before you change a file or make a claim about it.
- [principle-prove-it-works](../../skills/principle-prove-it-works/SKILL.md) checks a finding against the current artifact before you act on it and verifies the actual result before you declare the work done.
- [principle-fix-root-causes](../../skills/principle-fix-root-causes/SKILL.md) tests competing explanations against the reproduction. A failing check can expose a fault in the code or in the check itself.
- [principle-sequence-verifiable-units](../../skills/principle-sequence-verifiable-units/SKILL.md) gives each unit its own check. A test commit proves it can reproduce the failure before the fix makes it pass.
- [principle-test-behavior-not-implementation](../../skills/principle-test-behavior-not-implementation/SKILL.md) asserts what the code's users can observe, so a test fails when that behavior breaks and survives a change to the internals.
- [principle-explain-the-number](../../skills/principle-explain-the-number/SKILL.md) checks what limits a performance number or what an eval actually tested across trials. [benchmark-checklist](../../skills/benchmark-checklist/SKILL.md) covers the performance procedure.

The delegation principles keep parallel work sane:

- [principle-guard-the-context-window](../../skills/principle-guard-the-context-window/SKILL.md) uses a focused excerpt when it answers the question. For a delegated read, the subagent returns only its findings and their sources to its parent agent.
- [principle-never-block-on-the-human](../../skills/principle-never-block-on-the-human/SKILL.md) keeps reversible work moving under the authority you gave the agent. While a required decision waits for you, the agent can finish work that does not depend on it.

The meta principles guide recurring corrections and the material you hand to people or agents.

- [principle-encode-lessons-in-structure](../../skills/principle-encode-lessons-in-structure/SKILL.md) removes the way to make a recurring mistake or enforces the rule in code. [correct](../../skills/correct/SKILL.md) applies it to a whole repo, as shown in [Make it yours](./09-make-it-yours.md#fix-the-environment-with-correct).
- [principle-write-for-where-it-is-read](../../skills/principle-write-for-where-it-is-read/SKILL.md) asks what a person, agent, or program can see where it will use your output.
- [principle-anchor-every-reference](../../skills/principle-anchor-every-reference/SKILL.md) uses the names in the source or glossary so you can identify a reference without looking back.
- [principle-everything-at-hand](../../skills/principle-everything-at-hand/SKILL.md) puts labels beside their marks and keeps the views you are comparing together at the same scale.
- [principle-files-describe-the-present](../../skills/principle-files-describe-the-present/SKILL.md) keeps code and working docs about the current system, with change history in decision records, changelogs, and commits.

Don't memorize the list. Skim it now, then come back when you catch the agent doing something a name here would have prevented. That's how the vocabulary sticks.

Next: [Make it yours](./09-make-it-yours.md).
