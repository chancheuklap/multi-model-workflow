---
name: architect
description: "Sketch types, interfaces, and module boundaries before code, then stay in the loop while implementation fills in. Use for /architect, 'architect this', 'design this', or non-trivial work where jumping to code would lock in the wrong shape."
---

# Architect

Use [codebase-dic](../codebase-dic/SKILL.md) for the architecture vocabulary (**module**, **interface**, **implementation**, **depth**, **seam**, **adapter**, **leverage**, **locality**) and its principles. Keep **seam** for where behavior or a dependency can be substituted, and **module boundary** for the state and knowledge a module owns.

Before writing code, start with the real callers, contracts, dependencies, and settled decisions the invoker supplies. Trace each system that evidence leaves unexplained where the gap could change the interface.

Produce a **design package**: write the caller's **usage sketch** first, derive the **type sketch** (types, type signatures, and module boundaries that realize the interface, including invariants, ordering, and error modes), add a short **design rationale** with trade-offs and rejected alternatives, and include a module map for larger changes.

Sketch two structurally distinct shapes and screen each against these **design red flags**: shallow module, information leakage, temporal decomposition, pass-through method, split ownership, two ways to do one task, importable internals, and hand-synced list. Pick the shape where each piece of state has one owner, each task has one way to do it, and callers need to know least. Redesign instead of patching if workarounds repeat.

## Parallel exploration

- **Large or contested design**: run [arena](../arena/SKILL.md) using the current host's `arena runners` entry in `~/.agents/mmwstack-models.md` (or the supplied rule file) instead of sketching alone. Give every runner the same real callers, contracts, and constraints, and require a complete design package.
- **Alternative interfaces to one module**: follow [Design it twice](references/design-it-twice.md), which runs [arena](../arena/SKILL.md) with contrasting design directions and a deep-module rubric.

In [arena](../arena/SKILL.md) Phase F, verify a pre-code design package against the real call sites, invariants, dependencies, and settled constraints.

## Handoff and reporting

When the invoker assigns implementation to another agent, return the recommended design package and the reason for the choice, then stop. For the operator, report the recommended shape, gains in depth, locality, or seam placement, and core trade-offs in plain language (with a diagram when helpful) rather than code signatures. Pause to show candidates and wait for approval only when the operator explicitly asks to review or compare designs before code.
