# Running the checks

For a step that runs the repository's tests on a change. A run that looks green but reached nothing reaches the user as a pass.

- Run only the type checks and tests the repository's own instructions (its `AGENTS.md` and the files it points to) name for the files you changed. A suite named for those files is not a full suite; running every suite at once is, and it runs only when user rule 15 allows it.
- Read what each run ran: a run that collected no test, or none that reach the changed files, has checked nothing (`principles/principle-silence-is-never-a-pass.md`).
- When the repository names no type checks or no tests for the changed files, or the named tests do not reach them, the Reply says so: nothing the repository runs has checked this change.
