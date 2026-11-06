# AGENTS.md

Keep a line here only when all three tests hold:

- Reading the code, an ADR, a glossary or a script's header cannot tell an agent, or tells it too late.
- Getting it wrong is costly or cannot be undone.
- It is the owner's rule or a fact outside the repository, not an inventory of repository contents, so it stays true as the code changes.

`mmw-v5-cloud/` is the working edition. It holds the skills, tools, board and project configuration, and packaging reads that directory. `mmw-v5/`, other version directories, `archive/`, `deprecated/`, `docs/research/` and `upstream/` stay in the tree as reference. They are not current working instructions. Run none of their scripts, and leave `mmw-v5/` unmaintained.

MMW v5 is the owner's general workflow for developing projects across consuming repositories. This repository is one of those projects and delivers the plugin itself, so the installed MMW v5 can be used to develop MMW.

The skills in this repository are deliverables, not the working instructions of an agent working on it. Use the host's installed skills. An explicit task to inspect or edit repository skills does not make those files the runtime for that task.

Keep skills atomic. Workflows come from composing skills and dispatch role references; do not repeat the surrounding workflow inside each skill. The skills are adaptations and extensions of Matt Pocock's skills, pstack, and the other reference projects under `upstream/`. Preserve source wording when importing or combining those prompts; deduplicate, arrange and adapt only as needed for the assigned role and use.

No part of MMW v5 may become reliable or complete by growing more complex; that only makes it more tedious and rigid. Before fixing a break, read the whole source of the chain around it, work out what each step was meant to do and what it actually does, and look for a step that is redundant, duplicated, wrong, or costs more than it returns: such a step is deleted or reshaped, not repaired. Before fixing or adding anything, ask whether the main path already catches the failure, even later. If it does, delete the extra layer rather than add a gate, field, command, fallback or rule. A real incident alone does not justify a layer.

The task board in `mmw-v5-cloud/board/` is also a product developed in this repository. Tickets about the board run from here. Personal use; tests run locally, never in GitHub CI. GitHub Actions publishes prepared releases only.

Runtime is Bash and the `python3` standard library. No package manager, no build step for the plugin runtime.

## Self-hosting boundary

When this repository consumes MMW v5, the installed cloud runtime used to open a night remains its runtime until that night closes. Treat its skills, scripts and prompts as one frozen version.

- Everything under ticket worktrees, merge worktrees, the main worktree, project branch and base branch is the product being changed. Never run its copy of an MMW skill or script to control, interpret, repair or finish the run that is changing it. Run the installation selected when this night opened, resolving tools from that installed runtime. That runtime remains frozen until the night closes; development source does not replace it.
- Do not update, uninstall or replace the installed runtime, retarget its files, or change live model configuration to satisfy new code while a night is open. A passing ticket, an already-landed dependency, a test result and an agent's judgement are not exceptions.
- Tests of changed MMW tools run in isolated test homes against fake trackers and repositories. They prove the product under test; they do not authorize that product to take over the current run. Use a new installed version only for a later run, after the old night closes and the owner authorizes the update.
- If the frozen runtime cannot finish a night after the product under test changes a protocol, do not bridge versions by editing the protocol or resuming an agent under new instructions. Keep the old runtime authoritative and report the incompatibility immediately. Suspend or repair the run only through that frozen runtime; record the product defect for a later night.

## Gotchas

- Releasing and updating installed hosts are the owner's calls. Commit completed changes on the assigned development branch; do not merge or push to `main`, publish, or update installed plugins without authorization.
- Prepare version changes on `dev` with `python3 scripts/release-mmw-v5.py bump` and run the relevant checks locally before committing. Pushing `dev` does not publish. Merging and pushing to `main` publishes the committed version as a tag, a GitHub Release and the cloud ZIP. GitHub does not change the version or run tests.
- Install MMW as a native plugin through the current host. The same `mmw-v5-cloud/` package serves Codex and Cursor. Keep user models in `~/.agents/models.json`; resolve tools from that installed plugin version. First installation and migration guidance lives in the root [README.md](README.md). Updating the installed Cursor copy follows [Cursor user marketplace](#cursor-user-marketplace) below.
- Never put credentials under plugin skills or scripts: the same installed plugin is used across consuming repositories.
- `.worktrees/mmw-installed` is a hand-made checkout, not a pipeline worktree. Never prune it.

## Cursor user marketplace

Cursor pins the user marketplace `mmw-v5` to one commit. `agent plugin marketplace update mmw-v5` reindexes that commit and does not move it. Adding the same URL again while `mmw-v5` is still registered also leaves the old commit. There is no Update control on the plugin card that advances it.

The published release is `origin/main`. The repository's default branch is `dev`. An add with no ref indexes `dev`, and pushing `dev` does not publish.

Update the installed Cursor plugin only after the owner asks, and only when no night is open:

```
agent plugin marketplace remove mmw-v5
agent plugin marketplace add --git-ref main https://github.com/chancheuklap/multi-model-workflow
```

Confirm `agent plugin marketplace list --format json` shows `mmw-v5` at user scope and its `gitRef` equals `origin/main`. Then install **MMW v5 Cloud** again at User scope. Removal drops the install, and the CLI cannot restore it: use `/plugins` in an interactive Cursor agent, or Customize → Plugins. Do not install from `~/.cursor/plugins/local`, and do not register a team marketplace for this.

Codex is a different pin. Update it with `codex plugin marketplace upgrade mmw-v5`.

## Install the cloud edition

Follow the root [README.md](README.md). Cloud agents receive MMW through their host's plugin installation, not a repository setup script or a copied user skill directory. A GitHub Release alone does not install or list a plugin in either host.

Before working in a subdirectory, search it for an `AGENTS.md` and read that file in full.
