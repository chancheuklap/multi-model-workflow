# Coding standards

The rules the review applies to every change in this repository. The Standards axis applies `## Code` and the Tests axis applies `## Tests`.

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

### Skills and scripts

- A skill directory `mmw-v2/skills/<name>/` is symlinked whole into every host, so it holds only what the agent holding the skill reads or runs: `SKILL.md`, reference files, `scripts/<…>`.
- A script finds its neighbours from its own resolved location. The only absolute paths it names are fixed user-level locations (`~/.mmw`, `~/.agents/skills`, `~/.claude/skills`) and paths the run made itself with `mktemp`, never a fixed name under `/tmp`.
- A script takes a text anchor, or a path into another skill's directory, only through `locations.py` (`mmw-v2/skills/mmw/scripts/locations.py`).
- A command is written so that running it again after an interrupt yields the same result (**principle-make-operations-idempotent**). Mode `## Re-entry` step 1, "The pipeline's commands are written to be run again", depends on this.
- A runner's own commands live only in its adapter `mmw-v2/skills/mmw/scripts/runners/<runner>.sh`, whose `# MMW_USES:` header is the authoritative list of what it calls. The selected runner is whatever `models.py runner` selects (its last step is a default).
- Every refusal has the three parts `refusal.py` builds: what happened, with one checkable fact; why; what to do next. A check that could verify nothing says so instead of reading like a pass (ADR 0008). Script headers record dated, version-pinned measurements from real runs (each host's hook payload, each runner's liveness tolerance) rather than claims from documentation.

### State and configuration

- Which host, model and reasoning effort each agent runs on is written only in `~/.mmw/models.json` (under `MMW_HOME` when set), through `models.py config`; the task board writes the same file, under the same lock, with the same atomic replace. The first `install.sh` writes the defaults and later runs leave an existing JSON alone. `mmw-v2/skills/mmw/hosts.json` records how each host starts and the first-install defaults, never the current selection. Neither file ever sits in a consuming repository. `dispatch.sh` resolves the row through `models.py` and hands it to the selected runner's adapter.
- `~/.mmw` holds two more things: `boards.json` (each consuming repository's main-checkout path → its task board's fixed port; `dispatch.sh board` writes it, `supervisor.py` reads it) and `state/<owner>__<name>/` (one 0700 directory per repository holding every file the relay, the watchdog and the turn guard keep, and not one byte of ticket state). The canonical reader of `MMW_HOME` is `home()` in `statedir.py`.
- A ticket's state is the fold of the `<!-- mmw {...} -->` blocks in its comments, in comment-id order. Every event is posted by a script; a model types none. Agents wake each other through the relay, which turns ticket events into wakes: nobody polls, and the night has no clock.
- Landing is done on `origin/<base branch>`: `advance`, `land` and `reverify` merge, check and fast-forward push inside the persistent detached worktree `.worktrees/merge-<branch>`; a conflict or a red check becomes `ticket.bounced` for triage and leaves the base branch untouched. The base branch is cut from a project branch recorded in `spec.opened.project`; after the user accepts the night, `dispatch.sh finish <spec>` merges it back. Merging into the repository's default branch is not MMW's job.
- The `nowledge-mem` entry in `~/.cursor/mcp.json` belongs to `install.sh`: its content comes from `nmem config mcp show --host cursor` with the `type` field removed, because `cursor-agent` reads only `url` and `headers` and skips the whole server when `type` is present (the symptom: a worker silently without memory tools). Other servers in the file are left as they are; a hand edit of this entry is overwritten at the next install and reported by `--check` first.

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
