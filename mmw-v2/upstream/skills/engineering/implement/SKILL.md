---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec or tickets.

Before writing any code, read yourself in: the ticket in full, comments included; then follow its **Parent** to the spec and read that in full; then every prototype and research artifact linked from the spec's **Sources**, each through to its conclusion; then the ADRs and the domain glossary covering the area you're touching. Then say in one sentence which **seam** this ticket is tested at, and start.

Use /tdd where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, use /code-review to review the work.

Commit your work to the current branch.
