# Sketch Prototype

Design before implementing. Sketch types, function signatures, class shapes, and seams with `not implemented` bodies and pseudocode. Synthesize across several design angles. A sketch type-checks with one command.

## Phase A: Ground the problem

Build a real mental model of every system the new code touches. Run the **how** skill over the relevant subsystems, and follow **principle-start-from-what-exists** before sketching. What the caller already traced or found, you take from it rather than doing again.

Naming a file isn't grounding. Produce the architectural explanation `how` prescribes. If the design redefines ownership or layering, also run the **why** skill on the existing shape so the rationale becomes a constraint, not a guess.

From the grounding, write down the constraints any new interface would need to satisfy, the dependencies it would rely on and the category each falls into, as the **codebase-design** skill sorts them, and a rough illustrative code sketch that makes the constraints concrete, not a proposal. Keep this grounding, including file paths, coupling details and what sits behind the seam, in `grounding.md` in the leaf directory `SKETCH/`.

Skip Phase A only when the work is genuinely greenfield with no surrounding system to integrate.

## Phase B: Sketch

Run the **arena** skill with the design-sketch task, the Phase A grounding artifacts, and the constraints below as the candidates' angles. Its `## Task` names the **prototype** skill's `references/sketch-candidate.md`, `references/rationale-template.md` and `references/design-red-flags.md` as the shape of the artifact. When Phase A ran, each candidate's brief names `SKETCH/grounding.md` by its repository path under `## Known`. On the greenfield path that skips Phase A, the brief names no grounding file.

Each candidate's brief adds only its different design constraint. Run three, and the fourth when it applies:

- Candidate 1: "Minimize the interface: aim for 1–3 entry points max. Maximise leverage per entry point."
- Candidate 2: "Maximise flexibility: support many use cases and extension."
- Candidate 3: "Optimise for the most common caller: make the default case trivial."
- Candidate 4 (if applicable): "Design around ports & adapters for cross-seam dependencies."

Screen every candidate against [`references/design-red-flags.md`](references/design-red-flags.md) before synthesis. Assume the next contributor is an agent that sees only the files it opened, copies the nearest example, and takes the shortest path that compiles. Prefer the design where a change that looks right from one file is right for the whole repo.

Hand arena its rubric: depth (leverage at the interface), locality (where change concentrates), and seam placement. Prefer the deeper design, in the **codebase-design** skill's terms. A rich interface can keep call chains short by concentrating capability instead of scattering it across layers.

Arena returns one synthesized design package. Its synthesis decision fills the rationale's "Synthesis decision" section. Arena's verification of a sketch is the red-flag screen and the **codebase-design** skill's measures above.

## Phase C: Hand back

Hand the synthesized sketch and its rationale back to the caller.

If the human pushes back on the shape, or the worker building it raises a `contract` child saying it does not hold, treat that as Phase A evidence. The session that coordinates the ticket re-grounds and re-runs Phase B, as **One ticket**'s **Each wake** or **Run a night**'s **Each time something wakes you** says.

## Outputs

One file with new types and signatures for small changes. Module map plus type definitions for larger work. The sketch goes in the leaf directory `SKETCH/`; its rationale, shaped per `references/rationale-template.md`, is the verdict comment `SKILL.md` rule 6 names.
