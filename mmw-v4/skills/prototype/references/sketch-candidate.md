# Sketch candidate

You are producing one candidate design in the prototype skill's sketch branch. Read the **codebase-design** skill and the project's domain glossary first, and name things in their terms, so every candidate uses the architecture language and the project's domain language. Design to the constraint your brief gives you. Output a candidate design package: type sketch, function signatures, module map, and prose rationale shaped per [`rationale-template.md`](rationale-template.md). Cover invariants, ordering and error modes, and the dependency strategy and adapters.

Apply the following discipline.

- Data structures first. Get the core types right and the code becomes obvious. Trace each dominant access pattern through the proposed structure. If the answer is "we'll add a map / index / cache later," the structure is wrong.
- Interface depth, in the **codebase-design** skill's terms. Prefer a simple interface that pulls complexity into the callee, even when the implementation becomes less simple.
- Make seams visible. `not implemented` errors for bodies, `// TODO` pseudocode for tricky logic, doc comments stating intent and invariants. A reader should trace data from input to output by reading types and signatures alone.
- Encode invariants in types: hard-to-misuse types > runtime checks > prose comments, per **principle-encode-lessons-in-structure**.
- Validate at boundaries, trust types inside, per **principle-boundary-discipline**. Business logic as pure functions. The shell stays thin.
- Idempotent state transitions where applicable, per **principle-make-operations-idempotent**. Ask what happens if the operation runs twice or crashes halfway.
- Short call chains. If tracing the flow needs more than three files, flatten the hierarchy, per **principle-laziness-protocol** and **principle-minimize-reader-load**.

Check the package against [`design-red-flags.md`](design-red-flags.md) before you report: the sender screens every candidate against it.
