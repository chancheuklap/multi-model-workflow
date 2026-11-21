---
name: architect
description: "Sketch types, interfaces, and module boundaries before code, then stay in the loop while implementation fills in. Use for /architect, 'architect this', 'design this', or non-trivial work where jumping to code would lock in the wrong shape."
---

# Architect

You are the designing agent shaping code before implementation. Use [codebase-dic](../codebase-dic/SKILL.md) for the architecture vocabulary (**module**, **interface**, **implementation**, **depth**, **seam**, **adapter**, **leverage**, **locality**) and its principles. Keep **seam** for where behavior or a dependency can be substituted, and **module boundary** for the state and knowledge a module owns.

If the invoker supplies a settled **design package**, treat it as the baseline and skip re-sketching.

## Ground and shape

Start with the real callers, contracts, dependencies, and settled decisions the invoker supplies. Trace each system that evidence leaves unexplained where the gap could change the interface.

Choose the exploration path before sketching:

- **Default**: sketch two structurally distinct shapes yourself.
- **Large or contested design**: run [arena](../arena/SKILL.md) instead of sketching alone. Give every runner the same real callers, contracts, and constraints, require a complete design package, and set the rubric to depth, locality, seam placement, single ownership, and the design red flags below.
- **Alternative interfaces to one module**: follow [Design it twice](references/design-it-twice.md).

Each **design package** contains:

- A caller **usage sketch** written first.
- A **type sketch** derived from that usage, giving the types, type signatures, and module boundaries that realize the interface, including invariants, ordering constraints, and error modes.
- A short **design rationale** covering trade-offs and rejected alternatives.
- A module map for larger changes.

Screen every shape against these **design red flags**: shallow module, information leakage, temporal decomposition, pass-through method, split ownership, two ways to do one task, importable internals, and hand-synced list. Pick the shape where each piece of state has one owner, each task has one way to do it, and callers need to know least.

When [arena](../arena/SKILL.md) runs before code, verify the synthesized design package in Phase F against the real call sites, invariants, dependencies, and settled constraints.

## Handoff and reporting

- **Invoker assigns implementation to another agent**: return the recommended design package and design rationale to the invoker, then end architecture work so the invoker can continue.
- **Operator requests a design review before implementation**: present the competing shapes or Arena candidates with a plain-language summary and diagram when helpful, then wait for approval.
- **Direct implementation**: proceed with the chosen design package, redesigning instead of patching if workarounds repeat. Report the recommended shape, gains in depth, locality, or seam placement, and core trade-offs to the operator in plain language rather than code signatures.
