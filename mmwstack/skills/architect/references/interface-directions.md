# Interface directions

Use when the invoker asks for alternative interfaces to one module. Give each runner one direction as the last line of its task. The rest of the runner prompt stays identical.

- Minimize the interface: aim for 1 to 3 entry points max. Maximise leverage per entry point.
- Maximise flexibility: support many use cases and extension.
- Optimise for the most common caller: make the default case trivial.
- Design around ports and adapters for cross-seam dependencies. Assign it only when the dependencies in the brief cross a seam.

Spawn one runner per assigned direction, at least three, taking models in turn from the `architect runners` line. Each runner names its direction in its rationale.

Give each runner the same real call sites and constraints. Each candidate design package includes a usage sketch and function signatures. Explain the consequences for callers, the interface's invariants, ordering and error modes, and the complexity the implementation hides. When the design substitutes a dependency at a seam, state the dependency's category and the adapters it needs, per [Deepening](../../codebase-dic/references/deepening.md).
