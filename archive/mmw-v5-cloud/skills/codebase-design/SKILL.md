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

Start with the caller’s evidence: real callers, contracts, dependencies and decisions already settled. Investigate gaps that could change the interface. Use **how** when an unresolved cross-module dependency or ownership question needs a walkthrough. For ownership changes, read the existing rationale.

Done when the evidence accounts for the constraints the sketch must satisfy.

## Phase B: Sketch

Start with the caller’s usage and derive the interface from it. If an existing contract or precedent determines the shape, sketch it directly and state the constraint that settles it.

When viable alternatives differ in compatibility, ownership, or what callers must know, explain that trade-off to the caller. Compare those alternatives in parallel. Give each **FRESH AGENT** [the runner prompt](references/runner-prompt.md), the Phase A evidence, an isolated working directory and one viable design to explore. Include the project’s domain vocabulary. For dependency boundaries, consult [Deepening](references/deepening.md).

Save each candidate assignment to FILE and use the installed **dispatch** skill's Runtime section to resolve DISPATCH, then run `bash DISPATCH spawn researcher --prompt FILE --host HOST`. Send each card as [Dispatch](../dispatch/SKILL.md) describes. Compare the returned usage examples, the complexity each interface hides and the consequences for existing callers. State how any missing candidate limits the comparison.

Screen the proposed shape against [design red flags](references/design-red-flags.md). Done when you can recommend a design and explain the constraint or trade-off that decided it.

## Phase C: Agree

Return the synthesized design to the caller.

## Outputs

The caller's usage is written first and the type sketch derived from it. One file with new types and signatures for small changes. Module map plus type definitions for larger work. The rationale ships alongside, shaped per [rationale-template.md](references/rationale-template.md), including the usage sketch and the synthesis decision.

Done when that package is in the caller's hands.
