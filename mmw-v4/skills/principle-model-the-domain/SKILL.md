---
name: principle-model-the-domain
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Model the Domain

Encode the real domain in a data structure instead of scattering it across conditionals. A structure that matches the domain makes invalid states unrepresentable and deletes branches. Choosing it at write time is cheap. Recovering it later reads as a refactor and gets deferred.

Before writing logic, define the core types and trace the dominant access patterns. Choose structures that fit those paths. Each increment lands a coherent abstraction or deepens one, rather than spreading a new capability across callers as special-case coordination.

Reach for:

- A state machine instead of scattered booleans, phases, or lifecycle checks.
- A typed model instead of loose parameters or repeated shape assumptions.
- A map, registry, lookup table, or discriminated union instead of branching spread across files.
- A reducer or command/event model instead of ad hoc state mutations.
- A module organized around one body of domain knowledge instead of a sequence such as load, validate, transform, and save. Execution order is not ownership.
- A small module boundary that gathers repeated behavior, ownership, or invariants.
- A queue, cache, index, graph, tree, or normalized collection where the access pattern calls for it.
- Any other structure that fits. When none fits, work out what the code must never allow and how the data gets read, then find the structure that encodes exactly that.

Do not force an abstraction. Prefer boring code if the current shape is already clear, local, and unlikely to grow. Be skeptical of an abstraction that adds indirection without removing branches, duplicated rules, invalid states, or lifecycle risk.

The sign that you skipped this is a new feature that grows an existing if/else chain by one more branch, or a second boolean that must stay in sync with the first. Temporal decomposition is another sign. Phase-named modules repeat the same domain rules across steps.

**In a diff:**

- The same logic shape in more than one place is extracted when a change to one copy would have to change the other. Similar statements alone do not justify an abstraction.
- A data structure that does not match the dominant access patterns: choose one that does.
- New one-off conditionals inserted into a flow that was not about them: move the logic into the helper, module, state machine or table it belongs to.
- A generic or magic mechanism that hides a simple data-shape assumption, where direct code would do: write the direct, boring version.
- Feature Envy, a function that reaches into another object's data more than its own: move it onto that data.
- Data Clumps, the same few fields or parameters travelling together: bundle them into one type.
- Repeated Switches, the same `switch` or if-cascade on the same type in more than one place: replace them with one map or one polymorphic call both sites share.
- Shotgun Surgery, one logical change scattered as edits across many files: gather what changes together into one module.
- Divergent Change, one module edited for several unrelated reasons: split it so each part changes for one reason.
- Refused Bequest, a subclass or implementer that ignores most of what it inherits: drop the inheritance and compose.
