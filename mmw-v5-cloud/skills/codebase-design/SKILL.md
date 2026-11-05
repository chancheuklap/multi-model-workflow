---
name: codebase-design
description: Sketch types, signatures, and module structure before code. Use when designing or improving a module's interface, deciding where a seam goes, or exploring alternative interfaces for a chosen deepening candidate. Return the chosen sketch to the caller. The vocabulary is codebase-dic.
---

# codebase-design

You are called while a shape is still open. The caller is the Worker landing a ticket, or the agent in improve-codebase-architecture after a deepening candidate is chosen. The moment is before code is written against that shape. Return the chosen sketch. The caller writes the code, or shows the sketch to a person.

Use **codebase-dic** for the vocabulary: module, interface, depth, seam, adapter, leverage, locality.

Sketch types, function signatures, class shapes, and module boundaries with `not implemented` bodies and pseudocode. Open a todolist with one entry per phase before starting.

1. Ground
2. Sketch
3. Agree

## Phase A: Ground the problem

Build a real mental model of every system the new code touches. Use **how** for those systems. Naming a file isn't grounding. If the design redefines ownership or layering, read the existing rationale so it becomes a constraint, not a guess.

Skip Phase A only when the work is genuinely greenfield with no surrounding system to integrate.

Done when you can name every system the new code touches, or the work is greenfield.

## Phase B: Sketch

Design it twice. Whole-shape alternatives, not point fixes inside one shape. Based on "Design It Twice" (Ousterhout): your first idea is unlikely to be the best.

### 1. Frame the problem space

Before spawning sub-agents, write a user-facing explanation of the problem space for the chosen candidate:

- The constraints any new interface would need to satisfy
- The dependencies it would rely on, and which category they fall into (see [deepening.md](references/deepening.md))
- A rough illustrative code sketch to ground the constraints, not a proposal, just a way to make the constraints concrete

Hand this explanation to the caller, then immediately proceed to Step 2. The caller reads it while the sub-agents work in parallel.

Done when the constraints, the dependency categories, and the rough sketch are in the explanation.

### 2. Spawn sub-agents

Prepare prompts for 3+ fresh sub-agents. Each must produce a **radically different** interface for the module.

Pass [runner-prompt.md](references/runner-prompt.md) as each runner's prompt. Prompt each sub-agent with a separate technical brief (file paths, coupling details, dependency category from [deepening.md](references/deepening.md), what sits behind the seam). The brief is independent of the user-facing problem-space explanation in Step 1. Give each agent a different design constraint:

- Agent 1: "Minimize the interface: aim for 1–3 entry points max. Maximise leverage per entry point."
- Agent 2: "Maximise flexibility: support many use cases and extension."
- Agent 3: "Optimise for the most common caller: make the default case trivial."
- Agent 4 (if applicable): "Design around ports & adapters for cross-seam dependencies."

Include both the codebase-dic vocabulary and GLOSSARY.md vocabulary in the brief so each sub-agent names things consistently with the architecture language and the project's domain language.

Each sub-agent outputs:

1. Interface (types, methods, params, plus invariants, ordering, error modes)
2. Usage example showing how callers use it
3. What the implementation hides behind the seam
4. Dependency strategy and adapters (see [deepening.md](references/deepening.md))
5. Trade-offs: where leverage is high, where it's thin

Save each completed prompt to FILE and run `dispatch.sh spawn researcher --prompt FILE --host HOST`. Send all printed assignments in parallel as [Dispatch](../dispatch/SKILL.md) describes.

Done when at least three candidates have returned those outputs, and a fourth only when its constraint applies.

### Screen every candidate against design-red-flags

Screen every candidate against [design-red-flags.md](references/design-red-flags.md) before synthesis. Assume the next contributor is an agent that sees only the files it opened, copies the nearest example, and takes the shortest path that compiles. Prefer the design where a change that looks right from one file is right for the whole repo.

Done when every candidate has been revised or rejected against those flags.

### 3. Present and compare

Return the designs to the caller one at a time, then compare them in prose. Compare viable candidates on interface **depth** (leverage at the interface), **locality** (where change concentrates), and **seam placement**. Prefer the design that hides more complexity behind a smaller, simpler public surface. A rich interface can keep call chains short by concentrating capability instead of scattering it across layers.

After comparing, give your own recommendation: which design you think is strongest and why. If elements from different designs would combine well, propose a hybrid. Be opinionated: the caller wants a strong read, not a menu.

The recommendation fills the rationale's [Synthesis decision](references/rationale-template.md#synthesis-decision).

Done when the rationale's Synthesis decision names the base, what was adapted from the others, and what was rejected.

## Phase C: Agree

Return the synthesized design to the caller.

## Outputs

The caller's usage is written first and the type sketch derived from it. One file with new types and signatures for small changes. Module map plus type definitions for larger work. The rationale ships alongside, shaped per [rationale-template.md](references/rationale-template.md), including the usage sketch and the synthesis decision.

Done when that package is in the caller's hands.
