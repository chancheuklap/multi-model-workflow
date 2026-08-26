# Final trace

**Who reads this:** the reviewer whose Goal starts with `Final trace`.

All tickets have landed on the task branch. Do not re-check each ticket's acceptance. Look at what one plan cannot see: gaps between plans, one plan breaking another, the spec's intent as a whole.

## Look

- The whole diff: did it break existing behaviour or existing callers.
- Spec and every plan: each verifiable intent is in the code. Confirmed prototype decisions and named research files the implementation depends on are used; unknowns are handled. A gap is an implementation miss, a design miss, a context miss, or something this review cannot verify — say which.
- Diff behaviour that spec and plans never asked for. Extra surface is a finding.
- Cross-plan contracts, data flow, shared state, migration order, module refs. If there is no shared surface, write one line that you confirmed independence. Still do the regression pass and the intent pass.

Plans and their self-summaries do not count. Verify.
