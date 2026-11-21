# Design it twice

Use when the invoker asks for alternative interfaces to one module. Based on Ousterhout's "Design It Twice": your first interface is unlikely to be the best.

Run [arena](../../arena/SKILL.md) directly with the four requirements below. [arena](../../arena/SKILL.md) owns the two-runner seat limit (`arena runners`), parallel spawning, cross-judge, base selection, and grafting.

## 1. Ground the problem space

Build the shared grounding brief from the module's real call sites, settled constraints, and dependencies classified per [Deepening](../../codebase-dic/references/deepening.md) (`in-process`, `local-substitutable`, `remote but owned`, or `true external`). Include both [codebase-dic](../../codebase-dic/SKILL.md) vocabulary and the project's domain glossary (`GLOSSARY.md` or the context glossary from `GLOSSARY-MAP.md`) so every runner uses consistent architecture and domain terms. An optional rough, non-proposal illustrative sketch may ground the constraints inside the runner brief.

Only when the operator explicitly asked to inspect designs before code, share a plain-language problem-space summary (constraints and dependency categories, plus an illustrative sketch only if the operator asks for one) before or alongside the candidates.

## 2. Assign two contrasting design directions and runner outputs

Choose the two **design directions** that create the sharpest tension for this module's constraints, and append one direction as the last line of each runner's task (the rest of the runner prompt stays identical):

- Minimize the interface: aim for 1 to 3 entry points max. Maximise leverage per entry point.
- Maximise flexibility: support many use cases and extension.
- Optimise for the most common caller: make the default case trivial.
- Design around ports and adapters for cross-seam dependencies. Assign this direction only when the dependencies in the brief cross a seam.

Require each runner's candidate **design package** to include:

1. The **interface** (types, type signatures, and module boundaries, plus invariants, ordering constraints, and error modes).
2. A caller **usage sketch** showing how real callers use it.
3. The complexity the implementation hides behind the **seam**.
4. Dependency strategy and **adapters** per [Deepening](../../codebase-dic/references/deepening.md).
5. Trade-offs in the **design rationale**: where **leverage** is high, where it is thin, and which direction the runner followed.

## 3. Rubric and verification

Set the [arena](../../arena/SKILL.md) rubric to grade candidates on **depth** (**leverage** at the interface), **locality** (where change concentrates), **seam** placement, and dependency and **adapter** fit. Screen against the **design red flags** in [architect](../SKILL.md). In [arena](../../arena/SKILL.md) Phase F, verify the synthesized design package against the real call sites, invariants, and settled constraints.

## 4. Reporting

- **Default**: keep the synthesized code-level design package for the execution ticket or implementing agent. Report the recommendation to the operator in plain language: what changed, why the chosen or hybrid shape wins on depth, locality, and seam placement, and what trade-offs it accepts (with a diagram when helpful).
- **Opt-in review**: when the operator explicitly asked to compare candidates before code, present each candidate in turn, contrast them on depth, locality, and seam placement, and give an opinionated recommendation (or hybrid) for approval.
