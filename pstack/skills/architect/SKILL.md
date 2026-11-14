---
name: architect
description: "Sketch types, signatures, and module structure before code, then stay in the loop while implementation fills in. Use for /architect, 'architect this', 'design this', or non-trivial work where jumping to code would lock in the wrong shape."
---

# Architect

Sketch types, function signatures, class shapes, and module boundaries with `not implemented` bodies and pseudocode. Synthesize across multiple model perspectives, then fill in code against the chosen sketch.

## Start

Start a checklist with one entry per phase before starting.

1. Ground
2. Sketch
3. Agree
4. Implement
5. Scrap

## Phase A: Ground the problem

Start with the evidence the invoker supplies: real callers, contracts, dependencies and decisions already settled.

Build a real mental model of every system the new code touches. Run the [how](../how/SKILL.md) skill over each system that evidence leaves unexplained, where the gap could change the interface. Naming a file isn't grounding. Produce the architectural explanation [how](../how/SKILL.md) prescribes. If the design redefines ownership or layering, also run the [why](../why/SKILL.md) skill on the existing shape so the rationale becomes a constraint, not a guess.

Skip Phase A only when the work is genuinely greenfield with no surrounding system to integrate.

Done when the evidence accounts for the constraints the sketch must satisfy.

## Phase B: Sketch

Run the [arena](../arena/SKILL.md) skill with the design-sketch task and the Phase A grounding artifacts. Pass `references/runner-prompt.md` as each runner's prompt. Include the project's domain vocabulary.

Take the runners from the `architect runners` line in the [pstack model rule](../setup-pstack/SKILL.md#model-rule), in place of the `arena runners` line. Follow the runner rules in [arena](../arena/SKILL.md) Phase A. When the invoker asks for alternative interfaces to one module, assign each runner one direction from [interface-directions](references/interface-directions.md).

Design it twice. Require at least two structurally distinct candidates before synthesis, even when the first looks sufficient. This is the [principle-exhaust-the-design-space](../principle-exhaust-the-design-space/SKILL.md) principle skill made concrete. Whole-shape alternatives, not point fixes inside one shape.

Screen every candidate against [`references/design-red-flags.md`](references/design-red-flags.md) before synthesis. Assume the next contributor is an agent that sees only the files it opened, copies the nearest example, and takes the shortest path that compiles. Prefer the design where a change that looks right from one file is right for the whole repo.

Compare viable candidates on interface depth. Prefer the design that hides more complexity behind a smaller, simpler public surface. A rich interface can keep call chains short by concentrating capability instead of scattering it across layers. Compare the returned usage examples, the complexity each interface hides and the consequences for existing callers. When a design deepens a module, use [codebase-dic](../codebase-dic/SKILL.md) to compare locality and seam placement.

Arena returns one synthesized design package. Its synthesis decision fills the rationale's "Synthesis decision" section. State how any missing candidate limits the comparison. Done when you can recommend a design and explain the constraint or trade-off that decided it.

## Phase C: Agree (opt-in)

Default: proceed directly to implementation with the synthesized design. No human checkpoint. When the invoker assigns implementation to another agent, return the synthesized design package to the invoker and stop. That agent receives the package as its contract.

Opt in to a checkpoint when the invoker explicitly asks: "/architect with checkpoint," "stop and show me before implementing," or similar. Then surface the synthesized design and pause for sign-off.

The synthesis can ship as its own commit either way, as the "scaffold first" mode of the [principle-foundational-thinking](../principle-foundational-thinking/SKILL.md) principle skill. Planned and scoped breakage during fill-in is fine, per the [principle-outcome-oriented-execution](../principle-outcome-oriented-execution/SKILL.md) principle skill. For adversarial pressure on the design before implementing, run the [interrogate](../interrogate/SKILL.md) skill on the synthesized sketch.

If the human pushes back on the shape (in a checkpoint or after the fact), treat that as Phase A evidence. Re-ground and re-run Phase B before writing more code.

## Phase D: Implement against the sketch

Replace `not implemented` bodies with code, pseudocode with logic. The synthesized sketch is the contract. Deviations from it are signal to surface, not friction to absorb silently. If a function needs a parameter the sketch didn't anticipate, ask whether the sketch was wrong, the requirement was missed, or the implementation is overreaching.

## Phase E: Scrap when the architecture is wrong

If implementation keeps producing friction the sketch can't absorb, throw the sketch out. Don't bolt fixes onto a wrong design, per the [principle-redesign-from-first-principles](../principle-redesign-from-first-principles/SKILL.md) and [principle-fix-root-causes](../principle-fix-root-causes/SKILL.md) principle skills.

The signal is a *pattern*, not single instances. Tells:

- The same shape of workaround appearing repeatedly across unrelated code.
- Multiple unrelated edge cases that all need special-case branches.
- Types that need escape hatches (`any`, casts, optional fields always set in practice) to compile.
- The "we need a lock" reflex when the sketch said the state wasn't shared.
- Callers having to know the abstraction's internal rules to use it.
- Two or more independent Phase D deviations of the same shape across the implementation.

Use judgment. A few edge cases don't condemn an architecture. Some problems are legitimately complex. Complexity in the data is not complexity in the design.

When you scrap:

1. Re-run the [how](../how/SKILL.md) skill over what's been built.
2. Redesign as if the new constraints had been day-one assumptions, per redesign-from-first-principles.
3. Subtract before adding, per the [principle-subtract-before-you-add](../principle-subtract-before-you-add/SKILL.md) principle skill. The new sketch should be smaller than the old one before it grows.
4. Return to Phase B and re-run [arena](../arena/SKILL.md).

## Outputs

The caller's usage is written first and the type sketch derived from it. One file with new types and signatures for small changes. Module map plus type definitions for larger work. The rationale ships alongside, shaped per `references/rationale-template.md`, including the usage sketch and the synthesis decision.
