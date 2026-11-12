# Formal verification

The formal verification skill records what a piece of code promises, how to check it, and which revision the check describes.

## Language

### The property and its scope

**Formal verification**:
A check of a promise in every case within a stated scope, such as every order of events in a model, every input up to a bound, or every input covered by a proof.

**Property**:
A promise the covered code makes, stated precisely enough for a verifier to check. For example, two workers must never run the same job at the same time. The property and the harm a violation would cause are separate statements.

**Formal check**:
A repeatable check of one property against named code or a model of that code. Its result applies to the recorded bounds and assumptions. One command in the project-local skill reruns the check with the specified tool version.

**Covered code**:
The files, functions, and operations that the check describes, including every writer that can affect the state guarded by the property. Moving or renaming a function can leave it in scope. A new writer can bring previously uncovered code into scope.

**Model**:
A description of the state, actions, and choices that matter to the property. Each modeled action maps to code a reviewer can locate. For an ordering question, the model includes orders the real code permits even if ordinary tests rarely exercise them.

**Indivisible step**:
An operation the model treats as one action that another action cannot interrupt. The matching code must provide the same guarantee. Splitting the operation in the code can introduce an order the old model never considered.

**Bound**:
A stated limit on the cases a formal check covers, such as the number of workers, input length, or range of a counter. A pass within a bound leaves larger cases open.

**Assumption**:
A condition taken as given by a check. For example, a property about a retried job might assume that a continuously enabled retry eventually runs. The result applies to executions that satisfy the condition.

Sources include [create-formal-verification-skill](../../../skills/create-formal-verification-skill/SKILL.md), [maintain-formal-verification-skill](../../../skills/maintain-formal-verification-skill/SKILL.md), and the [formal verification guide](../../guide/06-verify-and-ship.md#prove-a-property-with-a-formal-verification-skill).

### Verification tools and evidence

**Model checker**:
A tool that explores the states and orders of events a model permits and checks its properties. TLA+ expresses the ordering model that pstack uses by default. TLC checks that model, and the statechart presents its results in the reader's terms. [Statechart](../statechart/GLOSSARY.md).

**Code-level verifier**:
A tool that checks a property against the implementation itself, for example memory safety, absence of overflow, or a data-structure invariant over inputs within its scope. Here the verifier is a tool. In product verification, a verifier is an agent. [Product verification](../product-verification/GLOSSARY.md#evidence-and-observation).

**Formal verification harness**:
The part of a formal check that connects the covered code to the chosen verifier. Its setup determines which inputs and operations the verifier can examine. A code change can cause the harness to omit a new path even when the old check still passes.

**Proof assistant**:
A tool for establishing a property by proof. A proof can cover every input size under its assumptions when a finite model check would cover only the chosen sizes.

**SMT-backed verifier**:
A verifier that asks a satisfiability modulo theories (SMT) solver to settle logical conditions derived from the property and the code. Its coverage depends on the encoded conditions, bounds, and assumptions.

**Generated-input test**:
A test that exercises the real implementation on generated inputs. The formal verification skill uses this option when the relevant language has no suitable code-level verifier. The evidence covers the cases the test exercised.

**Counterexample**:
A case that violates a stated property. In an ordering model it is a trace through the actions. In an input check it can be a failing input. A counterexample to a progress property can contain a loop that repeats forever.

**Counterexample replay**:
An attempt to reproduce a counterexample against the real code, step by step. A step the code cannot take identifies a modeling error. A realizable path that breaks the current promise identifies a product bug.

**Broken variant**:
A temporary change to the covered code that deliberately violates the property, for example removing a guard or reordering two steps. A check that catches the change demonstrates its ability to detect that failure. The scratch change is then discarded.

Sources include [create-formal-verification-skill](../../../skills/create-formal-verification-skill/SKILL.md), [maintain-formal-verification-skill](../../../skills/maintain-formal-verification-skill/SKILL.md), and [statechart](../../../skills/statechart/SKILL.md).

### Keeping a check aligned with the code

**Formal verification skill**:
A project-local skill that records how to rerun formal checks, identify changes to covered code, interpret a failure, and bring the checks back into sync. Projects choose their own skill name.

**Coverage record**:
The record for a check that names its property, covered code, bounds, assumptions, command, and sync commit. It gives the next agent the starting point for examining a change.

**Sync commit**:
The revision at which someone last confirmed that the verification describes the covered code. A new sync commit records a completed check of that correspondence. A blocked check keeps its previous sync commit.

**Verification drift**:
A mismatch between the model, the harness, or the recorded property and the current code or its intended promise. A stale check can pass because it still describes an earlier implementation.

**Intended change to a promise**:
A change to the property supported by evidence in the change itself, such as the tests, a doc comment, a changelog, or a commit message. The maintenance report records the old wording, the new wording, and that evidence.

**Formal maintenance outcome**:
The assessment for one check. `in sync` means the existing description still matches the code and the check passes. `updated` on its own means the verification now describes changed code and the check passes. `bug` means the check describes the current code and the code breaks the property. A check can be both updated and a bug when updating it exposes a violation. `blocked` means the check could not run or the verification could not be aligned.

These outcomes come from [maintain-formal-verification-skill](../../../skills/maintain-formal-verification-skill/SKILL.md).
