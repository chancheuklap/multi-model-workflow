# Spec content

**Who reads this:** the reviewer whose Goal starts with `Spec content`.

Does this spec stand: is the problem thought through, is it complete enough to implement, will it land?

Report what is **missing**, **extra**, or **misunderstood**.

## Look

Answer the direction questions in the shared reviewer skill before consistency. Wrong problem: `needs-redirection`. Do not complete a spec aimed at the wrong problem.

- Every user-visible behaviour has a goal you can pass or fail. Not "a good experience".
- The core flow works. Failure, empty, edge, and concurrency are covered.
- Structure for a future nobody asked for.
- UI and data shapes are specified enough to implement, not "see that directory".
- Spec text absorbed the confirmed prototype decisions and research facts the task named. Rejected variants are constraints, not current design.

## Always report

Core intent that cannot be tested; goals so vague a planner must guess; UI that is only a folder; a whole key scene missing; a new business object with no owner.

This spec will be split into tickets and given to a `worker` who cannot ask the user. **Build from it — do you get the right thing?** That is the only bar.
