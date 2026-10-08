# Coding standards

The rules the review applies to every change in this repository. The Standards axis applies `## Code` and the Tests axis applies `## Tests`. Where the landing pipeline's terms come from, see `CONTEXT-MAP.md`.

The author of a change does not read this file. Writing the change already takes more context than anything else in the work, and the review has room to spare, so the rules are applied where they are read: here, against the diff. A rule here is a judgement the diff shows. A violation with a fixed shape (a banned call, an import form, a file location) is a check that fails, not a row. A row is added, changed or removed only through a retro proposal the owner approved.

Name each finding by its rule and quote the lines it is about. Every rule is a judgement call. **Details** names where the reasoning and the examples are.

## Code

| Rule | A finding when the diff | Details |
| --- | --- | --- |
| Old path kept | adds a path that does the job of an existing branch, guard, helper or file, and leaves the old one, or a caller still on it, in place | **principle-migrate-callers-then-delete-legacy-apis** |
| Fix at one caller | fixes a defect at the one caller that met it, while the shared code it comes from still hands it to the other callers | **principle-migrate-callers-then-delete-legacy-apis** |
| Unexplained addition | adds a file, a dependency or a configuration entry, and neither the change nor its author's recorded decisions say why the existing one was not enough | **principle-laziness-protocol** |
| Lost safeguard | simplifies away a security check, error handling that prevents data loss, accessibility, or anything the request explicitly asked for | **principle-laziness-protocol** |
| Silent pass | lets a check, a guard or a script that verified nothing (no file matched, no case ran, a source could not be read) report success | **principle-a-check-must-be-able-to-fail** |
| Narrating comment | adds a comment that restates the code or narrates steps (`// Phase 1: add cards`), where only a non-obvious why earns a comment | the `mmw-mode` skill's `## Comments` |
| History in a file | writes into a file, a comment or a docstring what changed ("now", "previously", "no longer"), not what is true of its subject | **principle-files-describe-the-present** |
| Foreign file in a skill | puts into `mmw-v3/skills/<name>/`, which is symlinked whole into every host, a file the agent holding the skill neither reads nor runs; only `SKILL.md`, reference files and `scripts/<…>` belong there | `mmw-v3/skills/README.md` |
| Procedure outside a playbook | writes how a task is done anywhere but a playbook of the `mmw-mode` skill, or a routing section into a `SKILL.md` other than `mmw-mode`'s | `check-interfaces.py` refuses the routing section |
| Fixed path | has a script find a neighbour other than from its own resolved location, or name an absolute path other than a fixed user-level location (`~/.mmw`, `~/.agents/skills`, `~/.claude/skills`) or one the run made with `mktemp`; a fixed name under `/tmp` is one | |
| Runner command outside its adapter | runs a runner's own command anywhere but its adapter `mmw-v3/skills/dispatch/scripts/runners/<runner>.sh`, or picks a runner other than the one `models.py runner` selects (its last step is a default) | |
| Incomplete refusal | adds a refusal without the three parts `refusal.py` builds (what happened, with one checkable fact; why; what to do next), a refusal (exit 2) that has already changed something, a next step the reader cannot take, or a flag that passes over a missing sibling script where an incomplete checkout should be reported | `refusal.py`; ADR 0008 for a check that verified nothing |
| Unmeasured header | records in a script header a host's or a runner's behaviour (a hook payload, a liveness tolerance) from documentation, not as a dated, version-pinned measurement from a real run | |
| Unearned defence | adds a defence no real run needed, or one whose reason names no run (an issue number or a dated measurement), or keeps one that guards a path normal input does not reach; a deleted defence states its residual risk once | |
| Model selection outside models.json | writes which host, model and reasoning effort a role runs on anywhere but `~/.mmw/models.json` (under `MMW_HOME` when set) through `models.py config`, or, for the task board, other than in that file under the same lock with the same atomic replace; has `install.sh` do more than write the defaults once and add a missing role's row; records the current selection in `roles.json` or `hosts.json`, or puts either file in a consuming repository; has `dispatch.sh` resolve a row other than through `models.py` | `mmw-v3/skills/dispatch/references/editing-models.md` |
| Unlisted machine state | keeps under `~/.mmw` anything beyond `models.json`, `boards.json` (each consuming repository's main-checkout path and its task board's fixed port; `dispatch.sh board` writes it, `supervisor.py` reads it) and `state/<owner>__<name>/` (one 0700 directory per repository for every file the relay, the watchdog and the turn guard keep, and not one byte of ticket state), or reads `MMW_HOME` other than through `home()` in `statedir.py` | |
| Ticket state outside its events | keeps a ticket's state anywhere but the fold of the `<!-- mmw {...} -->` blocks in its comments, in comment-id order; has a model type an event; writes an event without checking its fields; has a reader refuse more than a block it cannot read or an event the vocabulary does not have, or assume a field is present; reads a fact from another event than the one that records it, or falls back to another; has an agent poll, or the night keep a clock, where the relay should turn a ticket event into a wake | ADR 0034; `docs/contexts/night/how-it-works.md` |
| Landing off the merge worktree | merges, checks or pushes a landing anywhere but the persistent detached worktree `.worktrees/merge-<branch>` on `origin/<base branch>`; turns a conflict or a red check into anything but `ticket.bounced` for triage, or touches the base branch on one; merges a night back other than through `dispatch.sh finish <spec>` after the owner accepts it, or into the repository's default branch | `docs/contexts/night/how-it-works.md` |
| Hand-shaped Memory entry for Cursor | writes the `nowledge-mem` entry of `~/.cursor/mcp.json` other than from `nmem config mcp show --host cursor` with the `type` field removed (`cursor-agent` reads only `url` and `headers` and skips the whole server when `type` is present, so a worker runs without memory tools and says nothing), or touches the file's other servers | `mmw-v3/install.sh` header comment |

## Tests

| Rule | A finding when a case in scope | Details |
| --- | --- | --- |
| Cannot fail | would still pass if every function it imports returned `undefined`; for a behaviour the change keeps, does not observe that behaviour. Ask this first: it is the finding whatever else the case is | **principle-a-check-must-be-able-to-fail** |
| Tautological | expects a value restated from the implementation, so it passes by construction | the `tdd` skill's `tests.md`, **Tautological tests** |
| Implementation-coupled | mocks internal collaborators, tests private methods, or asserts call counts or order, so a refactor that keeps the behaviour breaks it | `tests.md`, **Implementation-detail tests** |
| Side channel | verifies through external means (a database read, a file the code writes) where the interface shows the result | `tests.md`, the red flag "Verifying through external means instead of interface" |
| Named for the how | has a name that says how the code works, not what it does | `tests.md`, the red flag "Test name describes HOW not WHAT" |
| Over-mocked | mocks something the repository can run, not a system boundary | the `tdd` skill's `mocking.md`, its "Don't mock" list |
| Only the happy path | covers the ordinary input only, while the code has an edge, a boundary or an error path the requested behaviour depends on; the finding names that path and what should happen on it | |
| Pins wording | asserts the wording of prose no program reads (a skill's text, a document, a message nothing parses), where the request fixes no such text word for word; it fails each time the text improves and proves nothing about behaviour | |
| Unasked test | is committed although no criterion names it and the repository keeps no test of this kind for this kind of change, or adds more than one focused case for one stated behaviour | |
