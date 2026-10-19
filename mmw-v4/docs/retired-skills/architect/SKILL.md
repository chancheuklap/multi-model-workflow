---
name: architect
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Architect

Design before implementing. Sketch types, function signatures, class shapes, and seams with `not implemented` bodies and pseudocode. Synthesize across several design angles.

## Phase A: Ground the problem

Build a real mental model of every system the new code touches. Run the **how** skill over the relevant subsystems, and look for what already solves the problem, in the repository and outside it, before sketching (**principle-start-from-what-exists**). What the caller already traced or found, you take from it rather than doing again.

Naming a file isn't grounding. Produce the architectural explanation `how` prescribes. If the design redefines ownership or layering, also run the **why** skill on the existing shape so the rationale becomes a constraint, not a guess.

From the grounding, write down the constraints any new interface would need to satisfy, the dependencies it would rely on and the category each falls into, as the **codebase-design** skill sorts them, and a rough illustrative code sketch that makes the constraints concrete, not a proposal.

Skip Phase A only when the work is genuinely greenfield with no surrounding system to integrate.

## Phase B: Sketch

Several candidates are for a shape later work builds on: an interface that code outside this change calls, a data shape that is stored or passes between subsystems, or a change spanning more than one subsystem. Any other change, such as passing one more value along calls the change edits itself, takes the Phase A sketch as its design, finished as `## Outputs` says and screened against [`references/design-red-flags.md`](references/design-red-flags.md), with no arena.

Otherwise, run the **arena** skill with the design-sketch task, the Phase A grounding artifacts, and the constraints below as the candidates' angles. Each candidate reads `references/runner-prompt.md` itself, since arena's send has it follow that file, and produces a design package shaped per `references/rationale-template.md`. The synthesized sketch goes where the caller says; under the **prototype** skill that is the leaf `SKETCH/` directory, with the rationale as its `README.md`.

Design it twice. Require at least two structurally distinct candidates before synthesis, even when the first looks sufficient. This is the **exhaust-the-design-space** principle skill made concrete. Whole-shape alternatives, not point fixes inside one shape.

Give each candidate its technical facts (file paths, coupling details, the dependency category of each dependency, what sits behind the seam) and a different design constraint. Run three, and the fourth when it applies:

- Candidate 1: "Minimize the interface: aim for 1–3 entry points max. Maximise leverage per entry point."
- Candidate 2: "Maximise flexibility: support many use cases and extension."
- Candidate 3: "Optimise for the most common caller: make the default case trivial."
- Candidate 4 (if applicable): "Design around ports & adapters for cross-seam dependencies."

Screen every candidate against [`references/design-red-flags.md`](references/design-red-flags.md) before synthesis. Assume the next contributor is an agent that sees only the files it opened, copies the nearest example, and takes the shortest path that compiles. Prefer the design where a change that looks right from one file is right for the whole repo.

Hand arena its rubric: depth (leverage at the interface), locality (where change concentrates), and seam placement. Prefer the deeper design, in the **codebase-design** skill's terms. A rich interface can keep call chains short by concentrating capability instead of scattering it across layers.

Arena returns one synthesized design package. Its synthesis decision fills the rationale's "Synthesis decision" section. Arena's verification of a sketch is the red-flag screen and the **codebase-design** skill's measures above.

## Phase C: Hand back

Hand the synthesized sketch and its rationale back to the caller.

If the human pushes back on the shape, treat that as Phase A evidence. Re-ground and re-run Phase B.

## Outputs

The caller's usage is written first and the type sketch derived from it. One file with new types and signatures for small changes. Module map plus type definitions for larger work. The rationale ships alongside, shaped per `references/rationale-template.md`, including the usage sketch and the synthesis decision.
