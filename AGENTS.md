# AGENTS.md

Keep a line here only when all three tests hold:

- Reading the code, an ADR, a glossary or a script's header cannot tell an agent, or tells it too late.
- Getting it wrong is costly or cannot be undone.
- It is the owner's rule or a fact outside the repository, not an inventory of repository contents, so it stays true as the code changes.

`mmw-v5/` is the local edition; `mmw-v5-cloud/` holds cloud-specific deliverables. Shared skills are maintained only in `mmw-v5/` and copied into complete cloud release packages. Other version directories, `archive/`, `deprecated/`, `docs/research/` and `upstream/` are history or read-only. They can supply reference material when the task calls for it; they are not current working instructions. Run none of their scripts.

MMW v5 is the owner's general workflow for developing projects across consuming repositories. This repository is one of those projects and delivers the plugin itself, so the installed MMW v5 can be used to develop MMW.

The skills in this repository are deliverables, not the working instructions of an agent working on it. Use the host's installed skills. An explicit task to inspect or edit repository skills does not make those files the runtime for that task.

Keep skills atomic. Workflows come from composing skills and dispatch role references; do not repeat the surrounding workflow inside each skill. Preserve source wording when importing or combining upstream prompts; deduplicate, arrange and adapt only as needed for the assigned role and use.

No part of MMW v5 may become reliable or complete by growing more complex; that only makes it more tedious and rigid. Before fixing a break, read the whole source of the chain around it, work out what each step was meant to do and what it actually does, and look for a step that is redundant, duplicated, wrong, or costs more than it returns: such a step is deleted or reshaped, not repaired. Before fixing or adding anything, ask whether the main path already catches the failure, even later. If it does, delete the extra layer rather than add a gate, field, command, fallback or rule. A real incident alone does not justify a layer.

The task board in `mmw-v5/board/` is also a product developed in this repository. Tickets about the board run from here. Personal use; tests run locally, never in GitHub CI. GitHub Actions publishes prepared releases only.

Runtime is Bash and the `python3` standard library. No package manager, no build step for the plugin runtime.

## Self-hosting boundary

When this repository consumes MMW v5, the installed plugin used to open a night or one-ticket watch remains its runtime until that watch closes. Treat its skills, scripts, prompts, event vocabulary, relay and watchdog as one frozen version.

- Everything under ticket worktrees, merge worktrees, the main worktree, project branch and base branch is the product being changed. Never run its copy of an MMW skill or script to control, interpret, repair or finish the run that is changing it. Run installed tools from the consuming repository, resolving their paths from the installed plugin.
- Do not update, uninstall or replace the plugin, retarget its files, or change live model configuration to satisfy new code while a watch is open. A passing ticket, an already-landed dependency, a test result and an agent's judgement are not exceptions.
- Tests of changed MMW tools run in isolated test homes against fake trackers, runners and repositories. They prove the product under test; they do not authorize that product to take over the current run. Use a new installed version only for a later run, after the old watch closes and the owner authorizes the update.
- If the frozen runtime cannot finish a batch after the product under test changes a protocol, do not bridge versions by editing events, invoking the new protocol or resuming an agent under new instructions. Keep the old runtime authoritative and report the incompatibility immediately. Suspend or repair the run only through that frozen runtime; record the product defect for a later batch.

## Gotchas

- Releasing and updating installed hosts are the owner's calls. Commit completed changes on the assigned development branch; do not merge or push to `main`, publish, or update installed plugins without authorization.
- Prepare version changes on `dev` with `python3 scripts/release-mmw-v5.py bump` and run the relevant checks locally before committing. Pushing `dev` does not publish. Merging and pushing to `main` publishes the committed version as a tag, GitHub Release and plugin ZIP; GitHub does not change the version or run tests.
- The local edition is a complete plugin installed from GitHub `main`. The cloud edition is a complete published `.agents/` runtime committed to a consuming project, with only project models.json as its configuration. Do not point either edition at this development repository or update a running installation. Installation guidance lives in the edition READMEs.
- Local configuration and runtime records live outside the plugin at `~/.mmw-v5`, or the directory selected by `MMW_HOME`. Preserve them when replacing or updating plugins. Codex and Cursor share the same MMW configuration when they use the same directory.
- Never put credentials under plugin skills or scripts: the same installed plugin is used across consuming repositories.
- `.worktrees/mmw-installed` is a hand-made checkout, not a pipeline worktree. Never prune it.

Before working in a subdirectory, search it for an `AGENTS.md` and read that file in full.
