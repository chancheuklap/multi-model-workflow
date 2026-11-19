# Sketch candidate

You are producing one candidate design in the prototype skill's sketch branch. Read the **codebase-design** skill and the project's domain glossary first, and name things in their terms, so every candidate uses the architecture language and the project's domain language. Design to the constraint your brief gives you. Output a candidate design package: type sketch, function signatures, module map, and prose rationale shaped per [`rationale-template.md`](rationale-template.md). Cover invariants, ordering and error modes, and the dependency strategy and adapters.

Apply the following discipline.

- Apply **principle-model-the-domain** to the candidate's types and dominant access patterns. Trace each path through the proposed structure.
- Interface depth, in the **codebase-design** skill's terms. Prefer a simple interface that pulls complexity into the callee, even when the implementation becomes less simple.
- Make seams visible. `not implemented` errors for bodies, `// TODO` pseudocode for tricky logic, doc comments stating intent and invariants. A reader should trace data from input to output by reading types and signatures alone.
- Invariants per **principle-encode-lessons-in-structure**'s **Pick the strongest mechanism**.
- **principle-boundary-discipline**.
- State transitions per **principle-make-operations-idempotent**, where applicable.
- Apply **principle-minimize-reader-load** to the layers and hidden state a reader must trace.

Check the package against [`design-red-flags.md`](design-red-flags.md) before you report: the sender screens every candidate against it.
