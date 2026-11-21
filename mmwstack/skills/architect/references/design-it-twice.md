# Design it twice

Use when the invoker asks for alternative interfaces to one module. Run [arena](../../arena/SKILL.md) directly with the four requirements below.

## 1. Ground the problem space

Build the shared grounding brief from the module's file paths, coupling details, real call sites, settled constraints, what sits behind the seam, and dependencies classified per [Deepening](../../codebase-dic/references/deepening.md) as `in-process`, `local-substitutable`, `remote but owned`, or `true external`. Include both [codebase-dic](../../codebase-dic/SKILL.md) vocabulary and the project's domain glossary (`GLOSSARY.md` or the context glossary from `GLOSSARY-MAP.md`) so every runner uses consistent architecture and domain terms. Keep any coordinator-written sketch out of the runner brief so runners explore independently.

## 2. Assign two contrasting design directions and runner outputs

Choose the two **design directions** that create the sharpest tension for this module's constraints. Tell each runner to produce a radically different interface along its assigned direction, appended as the last line of its task:

- Minimize the interface. Aim for 1 to 3 entry points max and maximize leverage per entry point.
- Maximize flexibility. Support many use cases and extension.
- Optimize for the most common caller. Make the default case trivial.
- Design around ports and adapters for cross-seam dependencies. Assign this direction only when the dependencies in the brief cross a seam.

Require each runner's candidate **design package** to include:

1. A caller **usage sketch** showing how real callers use the module.
2. A **type sketch** giving the types, type signatures, and module boundaries that realize the **interface**, including invariants, ordering constraints, and error modes.
3. The complexity the implementation hides behind the **seam**.
4. Dependency strategy and **adapters** per [Deepening](../../codebase-dic/references/deepening.md).
5. A **design rationale** covering trade-offs, where **leverage** is high or thin, rejected alternatives, and the assigned design direction.

## 3. Rubric

Set the [arena](../../arena/SKILL.md) rubric to grade candidates on **depth**, **locality**, **seam** placement, dependency and **adapter** fit, and the **design red flags** in [architect](../SKILL.md).

## 4. Reporting delta

Apply [architect](../SKILL.md)'s handoff and reporting rules, with two additions for this branch:

- Keep [arena](../../arena/SKILL.md)'s synthesis note with the synthesized code-level design package.
- When the operator explicitly requested a **design review before implementation**, share a plain-language problem-space summary of the constraints and dependency categories, present each candidate in turn, contrast them on depth, locality, and seam placement, and give an opinionated recommendation or hybrid for approval.
