# Final fresh

**Who reads this:** the reviewer whose Goal starts with `Final fresh`.

Read only the diff. Do not read spec, plan, or anyone's wrap-up — ignore them if they are in Read. Audit the diff as unfamiliar code.

## Look

- Correctness: logic, off-by-one, null, types, bounds.
- Security: injection, auth bypass, leaks, unsafe defaults.
- Second-order failure: when A dies, does B still stand — propagation, retry, rollback.
- Integration and regression: cross-file fit; an existing caller now broken.
- Error paths: empty, failure, races, and what tests cannot reach.
- Tests added or changed: they prove behaviour at a public seam, with expected values independent of the implementation, mocks only at this repo's confirmed boundaries. Also the repo `TESTING.md` layout and commands.
- Release: data-model change with matching up and down migration and order; a way to undo; billing and permission invariants; new ports, commands, billable actions, capabilities registered; a breaking interface negotiated.

The shared red lines matter here: weak structures across a boundary, no registry, bypassed validation or migration.

Read code outside the diff only for a risk you can name. Do not wander.
