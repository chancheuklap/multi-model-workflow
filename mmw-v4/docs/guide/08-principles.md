# Shared principles and automatic loading

The skill set has 30 principles, each under `skills/principle-<slug>/`. Each holds a judgment needed by different tasks. Its body is the shared source: a new playbook or skill reuses that judgment by naming the principle, rather than copying its rules.

## How a task reaches a principle

Every session reads the [mmw-mode index](../../skills/mmw-mode/SKILL.md#principles). Each index line names a situation and the principle to read in full when that situation arises. Playbooks and skills also name principles at the steps that need their judgments. The owner gives a goal; loading the right principles does not depend on the owner remembering their names.

For example, Bug fix names Fix Root Causes before forming hypotheses. The tdd skill names Test Behavior, Not Implementation before its loop. The benchmark checklist and Eval share Explain the Number, while keeping their different measurement methods. A new task can use the same judgment through the mode's condition or an explicit call from its own step.

Principles hold shared judgments. Skills hold methods. The prototype skill owns comparing candidate designs and sends each kind of question to its branch. The mode calls prototype for a novel decision without precedent or an open design direction.

The frontmatter description of a principle says it runs only when named. The mode's conditional index and the named calls are its automatic entry points. A session reads a principle's body before applying it and explains the reasons and effects of its decisions. You can name a principle to redirect a run, but manual steering is optional.

## The 30 principles

These summaries follow the mode's groups. The linked bodies hold the full rules.

### Core

- [`principle-subtract-before-you-add`](../../skills/principle-subtract-before-you-add/SKILL.md). Refactoring, sizing a diff, or preparing an addition or new mechanism. Remove dead weight first, then make the smallest change that meets the request and preserves its protections.
- [`principle-redesign-from-first-principles`](../../skills/principle-redesign-from-first-principles/SKILL.md). Integrating a new requirement into an existing design, or code written against a sketch keeps failing to fit it. Redesign as if it had been foundational from day one.
- [`principle-minimize-reader-load`](../../skills/principle-minimize-reader-load/SKILL.md). Shaping modules, hidden state or new dependencies. Reduce the layers and information a reader must trace and hold.
- [`principle-outcome-oriented-execution`](../../skills/principle-outcome-oriented-execution/SKILL.md). Planned rewrites, internal API replacements and migrations. Declare transitions and verification boundaries, migrate callers and remove old paths by completion, and preserve external compatibility obligations.
- [`principle-experience-first`](../../skills/principle-experience-first/SKILL.md). Product, UX, or feature-scope tradeoffs. Choose user delight over implementation convenience.
- [`principle-first-principles-thinking`](../../skills/principle-first-principles-thinking/SKILL.md). Forming a recommendation whose path is unclear. Challenge requirements and constraints, keep only independently supported constraints, and rebuild the simplest solution.
- [`principle-start-from-what-exists`](../../skills/principle-start-from-what-exists/SKILL.md). Before proposing an approach or writing non-trivial code. Search this repository, then GitHub and the package registries, read an implementation file of each serious candidate, and decide to use, extend or build; the reply records the search.
- [`principle-read-before-you-conclude`](../../skills/principle-read-before-you-conclude/SKILL.md). Saying anything about a file, or changing one. Read it before you change it, read whole what you edit or reason about in detail, and label a conclusion that rests on an unread part as inferred.
- [`principle-build-the-lever`](../../skills/principle-build-the-lever/SKILL.md). Any non-trivial work. Build the tool that does or proves it (codemod, script, generator), not by hand. The tool is the artifact a reviewer reruns.

### Architecture

- [`principle-model-the-domain`](../../skills/principle-model-the-domain/SKILL.md). Before writing logic or designing data, state or interfaces. Define the data shape first and choose a structure that fits its access patterns.
- [`principle-boundary-discipline`](../../skills/principle-boundary-discipline/SKILL.md). Wiring validation, error handling, or framework adapters. Guards at system boundaries, trust internal types, keep business logic pure.
- [`principle-type-system-discipline`](../../skills/principle-type-system-discipline/SKILL.md). Designing types or a signature in any typed language. Make illegal states unrepresentable, brand primitives, parse external data at boundaries.
- [`principle-make-operations-idempotent`](../../skills/principle-make-operations-idempotent/SKILL.md). Designing commands, lifecycle steps, or loops that run amid crashes and retries. Converge to the same end state.
- [`principle-separate-before-serializing-shared-state`](../../skills/principle-separate-before-serializing-shared-state/SKILL.md). Concurrent actors might write the same file, branch, key, or object. Eliminate the sharing first.

### Verification

- [`principle-prove-it-works`](../../skills/principle-prove-it-works/SKILL.md). After a task, before declaring done. Verify against the real artifact, not a proxy or "it compiles".
- [`principle-fix-root-causes`](../../skills/principle-fix-root-causes/SKILL.md). Debugging, a failing check, or two failed fixes sharing a premise. Reproduce and distinguish hypotheses. After two fixes on the same premise fail, test that premise before another fix.
- [`principle-sequence-verifiable-units`](../../skills/principle-sequence-verifiable-units/SKILL.md). Multi-step work, shared prerequisites, and the order of commits and PRs. Prepare common foundations first, then advance through declared verification units.
- [`principle-test-behavior-not-implementation`](../../skills/principle-test-behavior-not-implementation/SKILL.md). Writing, changing, or keeping a test. Assert what the code's users can observe, so the test fails when that behavior breaks and keeps passing when only the internals change.
- [`principle-baseline-is-the-contract`](../../skills/principle-baseline-is-the-contract/SKILL.md). Writing from an answer, a winning prototype, a signed-off page or any settled conclusion. Copy it, never improve it from memory; raise a gap to whoever owns it.
- [`principle-run-the-smallest-test-set`](../../skills/principle-run-the-smallest-test-set/SKILL.md). Running tests. Run the smallest set that proves the change; a full suite only for a gate that requires it or a named risk, with the reason stated first.
- [`principle-explain-the-number`](../../skills/principle-explain-the-number/SKILL.md). Before trusting, reporting or acting on a measurement, performance number or agent eval result. Establish what ran, what the number measures and what scope the evidence supports.
- [`principle-fail-loudly`](../../skills/principle-fail-loudly/SKILL.md). Writing a check, a guard, a refusal or error handling. A failure names what failed, what was expected and where to change it; nothing passes silently.

### Delegation

- [`principle-guard-the-context-window`](../../skills/principle-guard-the-context-window/SKILL.md). Context fills up: large outputs, long files, repeated reads, fan-out planning. Read large payloads in chunks, or give them to the subagent the current step sends for them; keep only summaries in the main thread.
- [`principle-never-block-on-the-human`](../../skills/principle-never-block-on-the-human/SKILL.md). Tempted to ask "should I do X?" on reversible work, or a step failed or was interrupted. Proceed, present the result, let the human course-correct.
- [`principle-progress-is-what-the-record-says`](../../skills/principle-progress-is-what-the-record-says/SKILL.md). Picking work up or resuming it. Where you are is what the ticket, the branch, the map or the resume note says, not what the session remembers.

### Writing

- [`principle-everything-at-hand`](../../skills/principle-everything-at-hand/SKILL.md). Making any page or diagram for a person. Put everything needed to understand each place where the reader looks at that place.
- [`principle-write-for-where-it-is-read`](../../skills/principle-write-for-where-it-is-read/SKILL.md). Before writing anything another reader picks up: a subagent brief, a spec, a ticket, a document, a script's output. Name who reads it, what they are doing then, and what they can see.
- [`principle-anchor-every-reference`](../../skills/principle-anchor-every-reference/SKILL.md). Mentioning a thing, place, action or event in a reply or a document. Use its source name so the reader can identify it in the current sentence or paragraph; add a path and location when the reader needs to find or check the source.
- [`principle-files-describe-the-present`](../../skills/principle-files-describe-the-present/SKILL.md). Writing or editing any file. Write only what is true now; what changed and why goes in the commit message and the reply.

### Meta

- [`principle-encode-lessons-in-structure`](../../skills/principle-encode-lessons-in-structure/SKILL.md). You catch yourself writing the same instruction a second time. Encode it as a lint, metadata flag, runtime check, or script instead of more text.

Next: [Make it yours](./09-make-it-yours.md).
