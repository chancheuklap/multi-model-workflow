# Code-writing rules

For any step that writes or changes code: these rules hold whichever playbook the step belongs to.

- Before changing a function, grep every caller and fix the shared code once (**principle-migrate-callers-then-delete-legacy-apis**); when what you add supersedes an existing branch, guard or file, delete it in the same commit (**principle-subtract-before-you-add**).
- Before writing a helper, search the repository and the files the task points at for one that already exists (**principle-laziness-protocol**).

Before you design or write non-trivial code, apply `shared.md` rule 14.
