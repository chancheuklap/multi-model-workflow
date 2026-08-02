# Axis — Correctness

Does this code actually work?

Standards asks whether the code is written the way this repo writes code. Spec asks whether it does what was asked. Neither asks whether it is *right*. Here the code is written by a headless worker and no human has read it line by line, so that question needs an axis of its own.

**Do not read the spec, the tickets, or any summary the author wrote.** This axis is worth having only because it arrives with no prior framing. Read the diff as an unfamiliar body of code and judge it on its own terms.

## Brief

Audit the diff with fresh eyes:

- **Correctness** — logic errors, off-by-one, null and undefined, type mismatches, boundary conditions.
- **Security** — injection, auth bypass, data leaks, insecure defaults.
- **Second-order failure** — when A fails, does B hold? Propagation, retry, rollback.
- **Integration and regression** — cross-file coordination; does the change break an existing caller?
- **Error paths** — empty states, failure branches, races, anything the tests don't reach.
- **Shortcuts around the project's own machinery** — a weakly-typed bare structure crossing a boundary that has a real contract; something externally referenceable added without being registered; data validation or migration bypassed; behaviour tested somewhere other than the layer that owns it. Each is a finding on sight, and worth saying loudly when it touches data, permissions, billing, runtime, or release.
- **Release risk** — migration and deploy ordering, up/down symmetry, whether there is a way back, billing and permission invariants, breaking API changes.

Trust nothing the code says about itself. Verify against what it does. Look outside the diff only to chase a risk you can name — do not wander. Under 400 words.
