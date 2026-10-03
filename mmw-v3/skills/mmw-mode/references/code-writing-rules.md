# Code-writing rules

For any step that writes or changes code: these rules hold whichever playbook the step belongs to.

- Before changing a function, grep every caller and fix the shared code once (`principles/principle-migrate-callers-then-delete-legacy-apis.md`); when what you add supersedes an existing branch, guard or file, delete it in the same commit (`principles/principle-subtract-before-you-add.md`).
- Before writing a helper, search the repository and the files the task points at for one that already exists (`principles/principle-laziness-protocol.md`).

Before you design or write non-trivial code, apply user rule 14.
