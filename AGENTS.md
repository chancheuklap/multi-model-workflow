# AGENTS.md

Keep a line here only when all three tests hold:

- Reading the code, an ADR, a glossary or a script's header cannot tell an agent, or tells it too late.
- Getting it wrong is costly or cannot be undone.
- It is the owner's rule or a fact outside the repository, not an inventory of repository contents, so it stays true as the code changes.

Only `mmw-v4/` is live. `mmw-v3/`, `mmw-v2/`, `archive/`, `deprecated/`, `mmw-v4/docs/retired-skills/`, `mmw-v4/docs/retired-playbooks/`, `docs/research/` and `upstream/` are history or read-only. Treat nothing in them as fact and run none of their scripts.

The skills in this repository are deliverables, not the working instructions of an agent working on it.

No part of MMW v4 may become reliable or complete by growing more complex; that only makes it more tedious and rigid. Before fixing a break, read the whole source of the chain around it, work out what each step was meant to do and what it actually does, and look for a step that is redundant, duplicated, wrong, or costs more than it returns: such a step is deleted or reshaped, not repaired. Before fixing or adding anything, ask whether the main path already catches the failure, even later. If it does, delete the extra layer rather than add a gate, field, command, fallback or rule. A real incident alone does not justify a layer.

This repository consumes its own pipeline for one product, the task board in `mmw-v4/board/`. Tickets about the board run from here. Personal use, no CI, tests run by hand.

Runtime is bash and the `python3` standard library. No package manager, no build step.

## Self-hosting boundary

When this repository consumes its own landing pipeline, the MMW runtime for the whole run is the checkout recorded in `~/.mmw/installed-root` when the night or one-ticket watch opens. Treat that installed checkout, its skills, scripts, prompts, event vocabulary, relay and watchdog as one frozen version until the watch closes.

- Everything under the ticket worktrees, merge worktrees, main worktree, project branch and base branch is the product being changed. Never run its copy of an MMW skill or script to control, interpret, repair or finish the run that is changing it. In particular, do not call a repo-local `dispatch.sh`, `verify-ticket.py`, `events.py`, migration or replacement closeout protocol because it has just landed on the base branch.
- Do not move `.worktrees/mmw-installed`, run `install.sh`, retarget installed symlinks, change the live model configuration to satisfy new code, or otherwise make a running watch consume any part of the version it is building. A passing ticket, an already-landed dependency, a test result and an agent's judgement are not exceptions.
- Tests of the changed MMW run only in isolated test homes against fake trackers, runners and repositories. They prove the product under test; they do not authorize that product to take over the current run. The changed MMW becomes eligible to run only after the old installed MMW has closed the whole watch, the user has accepted the result, `finish` has completed, and the installed checkout is deliberately updated for a later run.
- If the frozen runtime cannot finish a batch after the product under test changes a protocol, do not bridge the versions by editing events, invoking the new protocol or resuming an agent under new instructions. Keep the old runtime authoritative and report the incompatibility immediately. Suspend or repair the run only through that frozen runtime; record the product defect for a later batch.

## Gotchas

- A change reaches no host until it is released. Releasing is the owner's call. The first promotion step is part of the work. The remaining steps run only when the owner says to release. The four promotion steps run in order:
  1. Commit on `dev`.
  2. Fast-forward `main` with `git push . dev:main`.
  3. Move the installed checkout with `git -C .worktrees/mmw-installed checkout --detach main` and confirm with `bash mmw-v4/install.sh --check`. This step waits while any watch is open, under `## Self-hosting boundary`.
  4. Push both with `git push origin dev main`.
- Run `install.sh` or `install.sh --back` only with the owner's explicit authorisation. Read-only `install.sh --check` is excepted.
- With Claude Code's Bash sandbox on, the PreToolUse hook can report `can't open file '…/dispatch/scripts/tool-guard.py'` because it cannot open the skill symlink target. The file is there and the command passes with the sandbox off. Leave the install alone.
- A credential written under any skill's `scripts/` is loaded by every repository on the machine.
- Retire unused v4 skills and playbooks by moving them to `mmw-v4/docs/retired-skills/` or `mmw-v4/docs/retired-playbooks/`. Never delete them.
- `.worktrees/mmw-installed` is a hand-made full checkout, not the pipeline's. Never prune it.
- Edit the user-level prompt in `mmw-v4/prompt/shared.md`. `~/.codex/AGENTS.md` is generated.

Before working in a subdirectory, search it for an `AGENTS.md` and read that file in full. The task board has `mmw-v4/board/AGENTS.md`.
