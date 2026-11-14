# Engineering design

A design sketch describes the code a caller will use. A refactoring changes the structure while preserving the behavior a caller observes.

## Language

### Engineering decisions

**Principle**:
A reusable rule for an engineering decision. pstack packages each principle as a skill. A playbook can apply several principles to one task. A principle citation names the decision the rule changed.

**Settled baseline**:
A decision already fixed by the material the work must follow. It can be an operator's answer, a value in an agreed spec, or the interaction in an [approved prototype](../design-and-presentation/GLOSSARY.md). The Baseline Is the Contract gives that decision its authority. A timing prototype settles only the timing question it answered.
_Avoid_: baseline alone when it could mean a starting measurement or a reference screenshot.

**First-Principles Thinking**:
The rule for questioning the premises of an open proposal. A measured capacity or a contract can establish a constraint. A convention needs independent support before it can constrain the design.

**Foundational Thinking**:
The rule for choosing data structures from the ways the code will use them, before writing the logic. Its *scaffold first* rule puts shared types, tests, or other setup first when every later phase benefits from them.

**Redesign From First Principles**:
The rule for incorporating a new requirement into an existing design. The target is the shape the system would have had if the requirement had been present from the start. The work can reach that shape incrementally.

**Laziness Protocol**:
The rule for choosing the smallest change that solves the problem and keeping each decision in one place. Subtract Before You Add applies that preference to the order of work by removing dead paths or redundant checks before adding a new structure.

**Start From What Exists**:
The rule for choosing among reuse, extension, and a new implementation. A suitable implementation in the repository can settle the choice. Where a gap remains, existing implementations elsewhere supply candidates for comparison.

**Attack the Premise**:
The rule for two or more fixes that assume the same thing and fail the same gate. The shared assumption becomes the subject of a check whose result would differ if the assumption were false.

**Lever**:
A file that performs or verifies the work repeatably under Build the Lever. A codemod can apply a change to many callers. A shared skill can give delegates the same recipe and verification contract. A reviewer can rerun a script and compare the result with the expected change.

**Encode Lessons in Structure**:
The rule for a correction that keeps recurring. A single owner can remove the opportunity for the mistake. A check that fails on a past instance can enforce the rule when the design still permits the mistake.

### The design seen by its callers

**Design package**:
A candidate or chosen design comprising a type sketch and its rationale, with a module map for larger changes. Under Exhaust the Design Space, an architectural comparison uses at least two structurally distinct candidates. The chosen sketch guides implementation. Arena's synthesis returns the synthesized design package, which architect also calls the synthesized design or synthesized sketch. A design package the operator approves is a settled baseline for the agent that writes the code.

**Usage sketch**:
The caller's view of the proposed design, shown by example imports, calls, and results. The type sketch is derived from this usage. Under Experience First, the person importing a library is a user of the design, as is the engineer maintaining it.

**Type sketch**:
The proposed types, function signatures, and module boundaries, with the implementation left open. The sketch makes it possible to trace data from input to output before the bodies are written.

**Design rationale**:
The record accompanying a sketch. It explains the choice of shape, its tradeoffs, and the alternatives considered. Its *synthesis decision* says which candidate supplied the base, what the chosen design took from other candidates, and what it left out.

**Agree (opt-in)**:
The design checkpoint an invoker can request in [architect](../../../skills/architect/SKILL.md). The invoker reviews the synthesized sketch before implementation. By default, implementation starts once the sketch is ready. When the invoker assigns implementation to another agent, architect returns the design package and stops.

**Architecture vocabulary**:
The terms module, interface, depth, seam, adapter, leverage, and locality as [codebase-dic](../../../skills/codebase-dic/SKILL.md) defines them. They describe the shape of the code and mean the same in every project.

**Domain vocabulary**:
The terms the project's own glossary defines for its concepts. They name modules and seams. When a deepened module takes its name from a concept the glossary lacks, [domain-modeling](../../../skills/domain-modeling/SKILL.md) adds the term.

**Module**:
Anything with an interface and an implementation. It can be a function, a class, a package, or a slice across tiers.
_Avoid_: unit, component, service as substitutes for module.

**Interface**:
Everything a caller must know to use the module correctly, including types, invariants, ordering constraints, error modes, required configuration, and performance characteristics. A TypeScript `interface` declaration covers only its type-level part.
_Avoid_: API or signature when referring to this entire contract.

**Implementation (module)**:
The code inside a module. An adapter has its own implementation. Writing code, as the implementer of an execution ticket does, is a different sense.

**Module boundary**:
The boundary around the knowledge and state a module owns. Its public interface is what callers use to reach its behavior. Operations that run at different times can belong to the same module when they depend on the same knowledge.

**Interface depth**:
The behavior and policy a module hides relative to what a caller must learn to use it. A deep module can complete an operation through one call. A shallow module makes callers coordinate its internal stages. A long call chain measures a different property. In [codebase-dic](../../../skills/codebase-dic/SKILL.md), *depth* is shorthand for interface depth.

**Deepening opportunity**:
A refactoring that moves complexity from callers into a module so its interface can stay small. It answers friction found while exploring, such as a shallow module or a seam that leaks. The recommendation describes the gain in leverage, locality, or testability.
_Avoid_: candidate, which names an Arena runner's design.

**Architecture review**:
One run of the [Improve codebase architecture playbook](../../../skills/poteto-mode/playbooks/improve-codebase-architecture.md). Its report is a self-contained HTML file with a card for each deepening opportunity, shown before and after.

**Leverage**:
What callers get from depth. More capability per unit of interface they learn. One implementation pays back across N call sites and M tests. Leverage is a term of art here and is exempt from [unslop](../../../skills/unslop/SKILL.md)'s plain-word rule.

**Locality**:
What maintainers get from depth. Change, bugs, knowledge, and verification concentrate in one place rather than spreading across callers. Fix once, fixed everywhere.

**Deletion test**:
A thought experiment about removing a module. If complexity vanishes, the module was a pass-through. If complexity reappears across its callers, the module was earning its keep.

**Seam**:
A place where behavior can change without editing the code at that place. An external seam sits at the module's interface. An internal seam lets its implementation substitute a dependency. A [test seam](../product-verification/GLOSSARY.md#evidence-and-observation) names where a test observes behavior.
_Avoid_: boundary as a substitute for seam. A module boundary describes ownership.

**Port**:
The interface a module uses to reach a replaceable dependency at a seam.

**Adapter**:
A concrete implementation that satisfies an interface at a seam. One adapter describes a hypothetical seam. Two justified adapters, such as a production transport and an in-memory test adapter, make the variation concrete.

**Dependency category**:
The distinction that determines how a deepened module can be tested. An **in-process** dependency needs no adapter. A **local-substitutable** dependency has a local stand-in. A **remote but owned** service uses a transport adapter. A **true external** service is outside the project's control and uses a mock adapter in tests.

**Design red flag**:
A property of a candidate design that warrants revision or rejection. Examples include callers able to import private implementation details, a hand-synced list whose copies can drift, or two public paths to the same operation.

**Information leakage**:
One implementation decision that several modules must know. Exposing a transport representation to callers, for example, makes a protocol change require edits outside the module that handles the protocol.

**Temporal decomposition**:
A division of modules by execution order that spreads the same domain knowledge across the steps. Separate load, validate, and save modules exhibit this problem when each must know the same representation and its rules.

**Reader load**:
The effort required to understand code. Minimize Reader Load distinguishes the layers a reader must trace from the hidden or mutable state they must hold in mind. A pass-through method adds a layer to trace. Even in one file, shared mutable state can make behavior hard to follow. A focused refactoring earns its place by reducing reader load somewhere. [principle-minimize-reader-load](../../../skills/principle-minimize-reader-load/SKILL.md)

**Split ownership**:
Several modules write the same state or maintain copies that must agree. Under Separate Before Serializing Shared State, actors publishing independent facts can own separate write targets and combine the facts when reading. A genuine single shared target requires structural control over concurrent writes.

### Domain rules and types

**Domain model**:
The concepts, rules and relationships of the system being changed. [domain-modeling](../../../skills/domain-modeling/SKILL.md) settles what those terms mean with the operator and records them in the project's glossary. The data structures express those rules in code. Under Model the Domain, a state machine can replace flags that must stay synchronized, or a registry can replace the same choice repeated across callers. A change earns the extra structure when it removes duplicated rules, invalid states, or branches.

**Architecture decision record (ADR)**:
The record of an architectural choice and its reason. A decision warrants an ADR when it is hard to reverse, would surprise a future reader without context, and involved a real trade-off. [domain-modeling](../../../skills/domain-modeling/SKILL.md#offer-adrs-sparingly)

**Design tree**:
A design discussion organized by which decisions depend on which answers. Its *frontier* is the set of questions whose prerequisites are settled. The operator considers one question at a time. [grilling](../../../skills/grilling/SKILL.md)
_Avoid_: decision frontier for this set when discussing the separately claimable GitHub tickets on a Wayfinder map.

**Boundary validation**:
The conversion of external input into a domain type where it enters the system. Under Boundary Discipline, internal code can then rely on the established guarantee. Code handles an error where it can recover or translate the error for its caller.

**Constructive modeling**:
A representation whose parts make an illegal combination impossible to construct. The PR watcher, for example, defines a clean CI state with empty lists of failed and pending checks. Type System Discipline also makes every variant of a result distinguishable to its caller.

**Branded type**:
A type that distinguishes values with different domain meanings even when they share an underlying type. In the PR watcher, a positive integer validated as a PR number can be passed wherever that particular domain value is required.

**Schema-derived type**:
A type whose shape comes from the schema that owns the data. A change to the schema then reaches its callers without requiring a separate hand-maintained declaration for the same shape.

**Simplest total type**:
The least restrictive type for which an operation handles every allowed input. Summing an empty list already gives a result. Choosing a winner needs either a nonempty list or a result that admits no winner.

**Idempotent operation**:
An operation that converges to the same correct state on repetition, including after a previous attempt stopped partway through. Make Operations Idempotent includes whether the next attempt can recognize and reconcile an incomplete result.

### Refactoring and executable checks

**Behavior contract**:
The results a caller, product user, or external service can observe through its interface. They can include errors, persisted state, or a request sent. Under Test Behavior, Not Implementation, a test catches a violation of that contract and survives a change confined to the internals.

**Pin**:
A characterization test, snapshot, or equivalence harness that captures current behavior before a refactoring changes the structure. The pin supplies the reference for an equivalence check, which compares the old and new behavior under the same conditions.

**Verifiable unit**:
A small step with a specific result. Sequence work into verifiable units requires each result to be checked before the next step begins. A behavior-preserving change keeps its checks green. For a bug fix, the check must fail for the intended reason in the reproduction commit and pass after the fix. [principle-sequence-verifiable-units](../../../skills/principle-sequence-verifiable-units/SKILL.md)

**Outcome-Oriented Execution**:
The rule for a planned rewrite or migration with explicit verification boundaries. It permits a scoped, reversible break within a declared phase while the code moves toward the target design. The completed plan requires static and runtime verification.

**Migrate Callers Then Delete Legacy APIs**:
The rule for replacing an internal interface when all callers can move together and no external consumer depends on the old contract. Updating the callers and removing the old API belong to one coordinated migration.

**Failing-before evidence**:
The test or executable check that fails for the intended reason before the change and passes after it. A bug fix needs it. A specified behavior gets it from the red step of its cycle. When a local test would need brittle mocks or unrelated setup, the closest executable check supplies it. [write-tests](../../../skills/write-tests/SKILL.md)
_Avoid_: TDD, TDD Bug Fix

**Authoring gate**:
The four questions answered before a test is added: what behavior it protects, what regression makes it fail, why existing proof misses it, and whether it needs a test-only hook with no production caller. [write-tests judgment](../../../skills/write-tests/references/judgment.md)

**Retention bar**:
The contracts a test may keep even when it looks static or slow, such as a public API, a migration or a package contract. A test that is only static or slow is not deleted for that reason. [write-tests judgment](../../../skills/write-tests/references/judgment.md)

### Code cleanup and comment review

**Code slop**:
Unnecessary changes introduced in a branch, such as a guard on an already trusted path, a cast that hides a type error, or a comment that narrates the code. Code cleanup examines the diff against the surrounding code's conventions. Prose has its own review.

**Comment Sicko**:
The fresh reviewer of comments in the assigned files or diff. It can delete comments and flag application code that needs reshaping. The calling agent adjudicates its findings and makes any accepted code changes.

**Keep-list exception**:
A documented reason a comment can stay, such as a legal header, a public API contract, or an external constraint the code cannot express. A suppression for a style-only rule can qualify. A suppression that hides a correctness error leaves the affected code open for repair.

**MUST KILL**:
A Comment Sicko finding that identifies an exact in-scope symbol requiring a fix. A surprise caused by the project's own code can produce this flag after the explanatory comment is deleted. A suppression hiding a real correctness issue can also leave a flag.

**Constraint comment**:
A comment claiming an obligation, such as preserving specific wording. Where the project owns the constraint, a type, test, or lint rule can enforce it. An obligation left without an approved encoding is reported as unenforced.

### Code review

**Code review**:
One review of a project branch after the tickets of its spec have landed on it, on the Standards, Spec and Tests axes. The operator asks for it. It runs once. The [code-review](../../../skills/code-review/SKILL.md) skill reviews and reports, and the [Code review playbook](../../../skills/poteto-mode/playbooks/code-review.md) repairs once and stops. It differs from an ambiguity scan, which reads a draft before any code exists, and from [interrogate](../../../skills/interrogate/SKILL.md), which tries to break a change with runs.
_Avoid_: review alone for any of these. A forge check named Code Review Gate is a separate thing.

**Review axis**:
One of the three questions a code review asks, each answered by its own fresh reviewer. Standards compares the diff with the repository's documented standards and a fixed smell baseline. Spec compares it with the spec and the landed tickets, and tries to break it. Tests audits the tests against the write-tests judgment. A stage belongs to an ambiguity scan, an axis to a code review.

**Hard finding**:
A documented-standard breach, a spec finding, or a test finding that the main chat kept after checking it against the reviewed commit. The Code review playbook repairs it when it is in scope. A smell from the baseline is a **judgement call**. It is reported under its axis and not repaired.

## Sources

The [principles guide](../../guide/08-principles.md) explains how a named principle changes a decision. The different decisions about binding constraints, shared foundations, and new requirements appear in [principle-first-principles-thinking](../../../skills/principle-first-principles-thinking/SKILL.md), [principle-foundational-thinking](../../../skills/principle-foundational-thinking/SKILL.md), and [principle-redesign-from-first-principles](../../../skills/principle-redesign-from-first-principles/SKILL.md).

The settled decision, shared-premise test, and rerunnable tool come from [principle-baseline-is-the-contract](../../../skills/principle-baseline-is-the-contract/SKILL.md), [principle-attack-the-premise](../../../skills/principle-attack-the-premise/SKILL.md), and [principle-build-the-lever](../../../skills/principle-build-the-lever/SKILL.md).

The [architect](../../../skills/architect/SKILL.md) skill, [candidate brief](../../../skills/architect/references/runner-prompt.md), [design red flags](../../../skills/architect/references/design-red-flags.md), and [rationale template](../../../skills/architect/references/rationale-template.md) define the design package and its supporting decisions. The typed representations appear in [typescript-best-practices](../../../skills/typescript-best-practices/SKILL.md). The [PR watcher's types](../../../skills/poteto-mode/scripts/watch-pr/types.ts) show the validated PR number and the clean CI state.

The [Improve codebase architecture playbook](../../../skills/poteto-mode/playbooks/improve-codebase-architecture.md) uses [codebase-dic](../../../skills/codebase-dic/SKILL.md) to assess deepening opportunities. Its [dependency categories](../../../skills/codebase-dic/references/deepening.md#dependency-categories) explain how the module is tested at its seam. codebase-dic repeats the architecture vocabulary for agents that read only the skill. Change both together.

The [Feature playbook](../../../skills/poteto-mode/playbooks/feature.md) uses the domain model in an implementation brief. The [Refactoring playbook](../../../skills/poteto-mode/playbooks/refactoring.md) holds a pin through structural changes. [principle-test-behavior-not-implementation](../../../skills/principle-test-behavior-not-implementation/SKILL.md) and [write-tests](../../../skills/write-tests/SKILL.md) define the test contract and failing-before evidence.

The cleanup roles are defined by [deslop](../../../skills/deslop/SKILL.md), [no-comments](../../../skills/no-comments/SKILL.md), and the [Comment Sicko role](../../../agents/comment-sicko.md). The [code cleanup guide](../../guide/05-build-and-clean.md) and [Opening a PR](../../../skills/poteto-mode/playbooks/opening-a-pr.md) place the code, comment, and prose checks in the delivery process.
