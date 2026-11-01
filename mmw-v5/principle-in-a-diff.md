# In a diff：从 principle 移出的审查原文

暂存供整理 code-review 使用。按来源 principle 保存原文，不合并重复规则，不改写判断。

提取范围：MMW v5 的全部 principle，以及 MMW v4 退役目录中的全部 principle。没有 `In a diff` 小节的 principle 不生成条目。MMW v4 文件保持原样。

共 21 个来源小节、81 条列表要求。17 个小节来自 MMW v5，4 个小节来自 MMW v4 的退役目录。

## principle-baseline-is-the-contract

提取来源：`mmw-v5/skills/principle-baseline-is-the-contract/SKILL.md` 的 `In a diff` 小节。

- Behavior no line of the ticket, the named spec sections or a baseline asked for, above all something the spec's `## Out of Scope` lists: remove it, or raise the gap to whoever owns the baseline.
- Something that looks implemented but does not match what was asked (the wrong value, state name, order or error): copy it from the source.
- A baseline the ticket names under `## Read first` holds the diff exactly as the spec does.

## principle-boundary-discipline

提取来源：`mmw-v5/skills/principle-boundary-discipline/SKILL.md` 的 `In a diff` 小节。

- Untrusted input that reaches a dangerous sink (SQL, a shell, `eval`, `innerHTML`) unescaped: escape or parameterize it at the sink, and trace the input path that reaches it.
- A new endpoint or entry point with no authentication or authorization check: check both at its door.
- A secret in code, a log or an error message: keep it in the environment or a secret store, and redact it wherever it would leave the process.
- Feature logic leaking into a shared path, an implementation detail leaking through an interface, or a bespoke helper where the repository already has the canonical one: move the logic to its layer and call the canonical helper.
- An external dependency reached directly from inside the logic, or through one generic fetcher: inject it, one function per operation, so a test stands in for it at the boundary.
- A worry about a case an enforced invariant already rules out (a shared component, a framework contract, a type, one source of truth) is not a defect, and a guard against it goes. A worry about an invariant that is only assumed, depends on timing, or crosses an async or state boundary still stands.

## principle-encode-lessons-in-structure

提取来源：`mmw-v5/skills/principle-encode-lessons-in-structure/SKILL.md` 的 `In a diff` 小节。

- A comment or convention saying "don't do X" that a type, a lint or a runtime check could enforce: offer that mechanism (**Pick the strongest mechanism**), and delete the instruction once it exists.

## principle-experience-first

提取来源：`mmw-v5/skills/principle-experience-first/SKILL.md` 的 `In a diff` 小节。

- A feature, control or option the experience does not justify, or one shipped half-finished: cut it or finish it. A half-finished feature is worse than a missing one.
- A visual change made on purpose is not a defect. One that costs accessibility (focus visibility, keyboard navigation, color contrast) or changes a component's API contract is, however intentional.

## principle-files-describe-the-present

提取来源：`mmw-v5/skills/principle-files-describe-the-present/SKILL.md` 的 `In a diff` 小节。

- A comment that restates the code or narrates steps (`// Phase 1: add cards`): delete it; only a non-obvious why stays (**mmw-mode** `## Comments`).
- A file, comment or docstring that says what changed ("now", "previously", "no longer") instead of what is true: rewrite it as what is true.

## principle-fix-root-causes

提取来源：`mmw-v5/skills/principle-fix-root-causes/SKILL.md` 的 `In a diff` 小节。

- A guard clause that masks a broken invariant, a retry that hides a broken contract, or a cast that silences a modeling error covers a symptom: find what breaks the invariant and fix it there.
- A fix in one module that belongs in another module's contract: move it to the contract that broke.
- A workaround: ask why it is needed and what the proper fix would be.
- A defect fixed at the one caller that met it, while the shared code still hands it to the other callers: fix the shared source.
- A comment that explains a surprise in our own code: delete it, and reshape the code (rename, extract, type, rearchitect) until the behavior is obvious without prose.
- A test change that weakens an existing assertion, or bends the check as the last pattern line says: put the check back. An honest "not met" costs the owner one look; a false pass lands broken behavior under a green mark, and everything built on it inherits it.

## principle-make-operations-idempotent

提取来源：`mmw-v5/skills/principle-make-operations-idempotent/SKILL.md` 的 `In a diff` 小节。

- A state-mutating operation whose second run, or whose run after a crash halfway, depends on what was left behind: add the reconciliation step.
- Related updates that can leave state half-applied: make them one atomic step (write then rename, one transaction, a compare-and-swap).

## principle-minimize-reader-load

提取来源：`mmw-v5/skills/principle-minimize-reader-load/SKILL.md` 的 `In a diff` 小节。

- A name that does not say what the thing does or holds: rename it. When no honest name comes, the design is murky.
- A file the change takes from under 1000 lines to over without a structural reason: name the part that should stand on its own and extract it.
- A new dependency that will make future changes harder: name what it ties together, and cut the tie.
- A message chain (`a.b().c().d()`) the caller should not depend on: hide the walk behind one method on the first object.
- The deletion test, on every module the change adds or reshapes: imagine deleting it. If the complexity vanishes, it was a pass-through and goes; if the complexity reappears across its callers, it earns its keep.

## principle-model-the-domain

提取来源：`mmw-v5/skills/principle-model-the-domain/SKILL.md` 的 `In a diff` 小节。

- The same logic shape in more than one place is extracted when a change to one copy would have to change the other. Similar statements alone do not justify an abstraction.
- A data structure that does not match the dominant access patterns: choose one that does.
- New one-off conditionals inserted into a flow that was not about them: move the logic into the helper, module, state machine or table it belongs to.
- A generic or magic mechanism that hides a simple data-shape assumption, where direct code would do: write the direct, boring version.
- Feature Envy, a function that reaches into another object's data more than its own: move it onto that data.
- Data Clumps, the same few fields or parameters travelling together: bundle them into one type.
- Repeated Switches, the same `switch` or if-cascade on the same type in more than one place: replace them with one map or one polymorphic call both sites share.
- Shotgun Surgery, one logical change scattered as edits across many files: gather what changes together into one module.
- Divergent Change, one module edited for several unrelated reasons: split it so each part changes for one reason.
- Refused Bequest, a subclass or implementer that ignores most of what it inherits: drop the inheritance and compose.

## principle-outcome-oriented-execution

提取来源：`mmw-v5/skills/principle-outcome-oriented-execution/SKILL.md` 的 `In a diff` 小节。

- A small deliberate duplicate that keeps a new path parallel to one the plan deletes is not a finding during the declared transition, unless it touches security, billing, data access or API behavior, or a long-lived shared abstraction would clearly reduce the risk.
- A new path beside an old one after migration completion, or a caller still using the superseded contract: finish the caller migration and remove the old path before calling the work done.

## principle-prove-it-works

提取来源：`mmw-v5/skills/principle-prove-it-works/SKILL.md` 的 `In a diff` 小节。

- Code that checks liveness by a file's mtime or cached state instead of the actual value, or trusts a delegate's self-report instead of its output artifact: read the real thing.
- Something the ticket, a named spec section or a baseline asked for that the diff does not do, or does only in part, is not done (**Done means done** below).
- A claim about a host's or a tool's behavior recorded from documentation: record it from a dated, version-pinned measurement of a real run.

## principle-read-before-you-conclude

提取来源：`mmw-v5/skills/principle-read-before-you-conclude/SKILL.md` 的 `In a diff` 小节。

- Before judging a hunk, read beyond it: callers, callees, guards upstream, type definitions, sibling modules, and why the code exists, until you can say whether the change addresses the right layer. A finding that rests on code you did not read is labelled `inferred`.

## principle-redesign-from-first-principles

提取来源：`mmw-v5/skills/principle-redesign-from-first-principles/SKILL.md` 的 `In a diff` 小节。

- A change patched onto the design rather than read as if the design always held it: ask whether the code would look like this had the requirement been known from the start, and write that form. One that reaches beyond the ticket's files is a finding outside the ticket.

## principle-separate-before-serializing-shared-state

提取来源：`mmw-v5/skills/principle-separate-before-serializing-shared-state/SKILL.md` 的 `In a diff` 小节。

- Mutable state several actors touch, kept safe by a convention or an instruction: give each actor its own target, or serialize by structure (a lock, sequential phases, one owner).
- Independent work run one after another for no reason: run it in parallel. Nothing is shared, so nothing needs ordering.
- A fixed name under `/tmp`, or any fixed shared path a script writes: every run shares it. Make it per run (`mktemp`) or owned by one actor.

## principle-start-from-what-exists

提取来源：`mmw-v5/skills/principle-start-from-what-exists/SKILL.md` 的 `In a diff` 小节。

- A hand-built copy of something the platform already does (native sticky positioning, scroll targeting, hit-testing, focus handling): use the native behavior. A manual reimplementation breeds real bugs, so a finding against one defaults to a fix.

## principle-subtract-before-you-add

提取来源：`mmw-v5/skills/principle-subtract-before-you-add/SKILL.md` 的 `In a diff` 小节。

- Dead code, unused imports, vestigial parameters and orphan references: delete them.
- Speculative Generality, an abstraction, parameter, hook, configuration or "just in case" path for a need nobody has: delete it and inline back.
- Of every hunk, ask whether the acceptance criteria still pass with less: the hunk deleted, folded into a branch that already exists, or replaced by a helper the repository already has. Raise it only when you can write the shorter form; one you cannot write is a preference.
- Look for the reframing that keeps the behavior and makes a block of branches, helpers, modes or layers disappear, rather than rearranging it. One that reaches beyond the ticket's files is a finding outside the ticket, never a demand on this diff.
- A new file, dependency or configuration entry with no recorded reason the existing one was not enough: ask for the reason, or remove it.
- A defence no real run needed, one whose reason names no run, or one that guards a path normal input does not reach goes unless the user agreed to its cost. State the residual risk once.
- A simplification that removes a security check, error handling that prevents data loss, accessibility, or something the request asked for: put it back (**Keep intact**).

## principle-type-system-discipline

提取来源：`mmw-v5/skills/principle-type-system-discipline/SKILL.md` 的 `In a diff` 小节。

- An input the type admits and the code does not handle (empty, nil or undefined, a boundary value): narrow the type so it cannot arrive, or handle it.
- Unnecessary optionality, `unknown`, `any`, or cast-heavy code where a clearer type boundary could exist, or a loosely shaped ad-hoc object: write the typed model.
- Primitive Obsession, a primitive or string standing for a domain concept: give the concept its own small type.
- An invariant the change relies on that no type holds and no assertion checks, so a regression would pass unseen: put it in the type, or assert it at the boundary.
- A suppression (`eslint-disable`, `@ts-ignore`, `@ts-expect-error`) of a rule that catches real bugs: remove it and fix what it hid.

## principle-foundational-thinking

提取来源：`mmw-v4/docs/retired-skills/principle-foundational-thinking/SKILL.md` 的 `In a diff` 小节。

- The same logic shape in more than one hunk or file is extracted when a change to one copy would have to change the other. Simple code is not a finding for lacking abstraction: an abstraction is premature until the code must change in a second way.
- A new dependency that will make future changes harder: name what it ties together, and cut the tie.
- A data structure that does not match the access patterns the code actually uses: choose the one that fits the dominant path.

## principle-laziness-protocol

提取来源：`mmw-v4/docs/retired-skills/principle-laziness-protocol/SKILL.md` 的 `In a diff` 小节。

- Of every hunk, ask whether the acceptance criteria still pass with less: the hunk deleted, folded into a branch that already exists, or replaced by a helper the repository already has. Raise it only when you can write the shorter form; one you cannot write is a preference.
- Look for the reframing that keeps the behavior and makes a block of branches, helpers, modes or layers disappear, rather than rearranging it. One that reaches beyond the ticket's files is a finding outside the ticket, never a demand on this diff.
- A simplification that removes a security check, error handling that prevents data loss, accessibility, or something the request asked for: put it back (**Keep intact**).

## principle-migrate-callers-then-delete-legacy-apis

提取来源：`mmw-v4/docs/retired-skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md` 的 `In a diff` 小节。

- A new path added beside the old one, or compatibility scaffolding kept after the migration is done: migrate the callers and delete the old path in the same change.

## principle-test-behavior-not-implementation

提取来源：`mmw-v4/docs/retired-skills/principle-test-behavior-not-implementation/SKILL.md` 的 `In a diff` 小节。

- Judge the case against the two imagined edits above: it fails when behavior breaks and keeps passing when only the internals change. Rewrite or delete a case that fails either test.
- An expected value recomputed the way the code computes it passes by construction (tautological): write the literal value.
- A case that mocks an internal collaborator, tests a private method, or asserts call counts or order breaks on a refactor that keeps the behavior: test through the public interface only.
- A case that checks the result through a side channel (a database read, a file the code writes) where the interface shows it: assert through the interface.
- A case named for how the code works rather than what it does: name it for the behavior.
- A mock of something the repository can run: mock only at a system boundary (an external API, time, randomness, sometimes the database or the file system).
- A case that covers only the ordinary input while the behavior depends on an edge, a boundary or an error path: name the untested path and what should happen on it.
- An assertion on the wording of prose no program reads (a skill's text, a document, a message nothing parses), where the request fixes no wording: assert exit codes, strings a program reads, produced facts and effects.
- A committed test no criterion names, where the repository keeps no test of that kind for that kind of change, or more than one focused case for one stated behavior: delete the extra.
- A case that makes more than one logical assertion: split it, one behavior per case.
- A new test whose only recorded red came from a missing file, an import error or a typo has not been shown able to fail (**Red for the right reason**).
- A restructuring, move or swapped dependency with no pin run green before and after it, or with a type check or lint as its only pin: pin the behavior first (**Pin behavior that must not change**).
- A check that finds its object by searching and taking the first hit: name the object (**Name the object a check checks**).
- A bug fix carries one focused test that reproduces the bug, deterministic even when the bug was flaky, and a change across an integration boundary a test of its whole path. When the ticket's criteria name neither, that is a gap in the ticket, raised as such, never a test the review adds to the diff.
