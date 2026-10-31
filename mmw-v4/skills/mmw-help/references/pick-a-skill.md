# Pick a skill

The default answer is to describe the task and let the mode route it. Name a skill directly when the user wants more or less of something than the playbook gives. Read the skill before you recommend it, and give one example prompt.

| The user wants to | Skill |
|---|---|
| Know how code works now, or where new code should live | `how` |
| Know why code is shaped this way, or where a number came from | `why` |
| Understand a change or subsystem, explained plainly | `teach` |
| Have a question investigated against primary sources | `research` |
| Know what a small diff could break outside itself | `blast-radius` |
| Use the shared words for module design: depth, seam, adapter | `codebase-design` |
| Get several designs of one brief, merged into the best one | `arena` |
| Settle a UI design through a runnable prototype and owner iteration | Design a UI playbook |
| Construct UI candidates or answer a logic, implementation or code-shape question with code | `prototype` |
| Examine the expert approach, your real goal, constraints and an outside check, with conclusions returned for your decision | `sharpen` |
| Have a plan stress-tested one question at a time | `grilling` |
| Settle the project's terms or record a decision | `domain-modeling` |
| Have a diff read on four axes by eyes that did not write it | `code-review` |
| Get a second opinion on one decision, on a stronger model | `advisor` |
| Send a worker to a ticket, run a night, or change a role's model | `dispatch` |
| Run one ticket's acceptance criteria and close it | `verify-ticket` |
| Resolve a merge or rebase conflict | `resolving-merge-conflicts` |
| Write, review, diagnose or audit tests, including TDD | `test-audit` |
| Apply TypeScript rules to `.ts` or `.tsx` work | `typescript-best-practices` |
| Strip comments before review, using a reviewer that didn't write them | `no-comments` |
| Clean AI tells out of prose | `unslop` |
| Write docs, a README, a PR description, or a commit message to a standard | `technical-writing` |
| Re-pitch the last reply in words or with `visual` as one page; catch up with `ketchup`; align on your goal with `in-your-own-words`, then wait for confirmation | `wait-what` |
| Draw a diagram or a page that explains something | `diagram-design` |
| Build an install package from the current branch | `exe-release` |
| Drive and inspect a CLI or TUI to prove a change | `control-cli` |
| Drive and inspect a browser, Electron or web UI to prove a change | `control-ui` |
| Give agents a scripted way to drive the app and prove behavior | `create-verification-skill` |
| Find affected features or, on request, reconcile the full product feature map and checks | `maintain-verification-skill` |
| Prepare one change's UI acceptance from its actual baseline | `prepare-ui-acceptance` |
| Establish a formal check for an important rule in real code | `create-formal-verification-skill` |
| Reconcile an existing formal check with code changes | `maintain-formal-verification-skill` |
| Vet a performance number before reporting or acting on it | `benchmark-checklist` |
| Write or edit a skill, a playbook or a reference to the set's standards | the Authoring or modifying a skill playbook |
| Register a problem that cannot be fixed in the current work | `register-problem` |
| Gather and sort a run's problems into proposals for the owner | `retro` |
| Stop agents from repeating the same mistakes in this repo | `correct` |
| Find their way around MMW | `mmw-help` |

If a skill in the installed set is missing from the table, read its frontmatter and opening lines. For principle-* skills, read [Playbooks and principles](playbooks-and-principles.md).

Close calls:

- `how` explains what the code does. `why` explains the reasons. `teach` runs one or both and explains the result plainly.
- The **prototype** skill's sketch branch stops at the sketch and hands it back. It writes no implementation.
- `code-review` reviews the diff. `blast-radius` looks for breakage outside the diff and proves the one fact that makes the change safe.
