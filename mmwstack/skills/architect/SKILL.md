---
name: architect
description: "Sketch types, signatures, and module structure before code, then stay in the loop while implementation fills in. Use for /architect, 'architect this', 'design this', or non-trivial work where jumping to code would lock in the wrong shape."
---

# Architect

Before writing code, start with the real callers, contracts, dependencies and settled decisions the invoker supplies. Trace each system that evidence leaves unexplained where the gap could change the interface. Then sketch two different shapes for it (types, signatures, module boundaries) and pick the one where each piece of state has one owner, each task has one way to do it, and callers need to know least. Redesign instead of patching if workarounds repeat.

For a large or contested design, or when the invoker asks for alternative interfaces to one module, run [arena](../arena/SKILL.md) with the architect’s runners instead of sketching alone. Use the model and settings from the current host’s `architect runners` entry in `~/.agents/mmwstack-models.md` (or the supplied rule file). For alternative interfaces to one module, assign the [interface directions](references/interface-directions.md).

When the invoker assigns implementation to another agent, return the candidates, the recommended design package and the reason for the choice, then stop. If the operator asks to see the design before code, show it and wait for approval.
