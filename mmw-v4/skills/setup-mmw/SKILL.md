---
name: setup-mmw
description: Set a repository up for MMW's landing pipeline, or check one already set up. Use when MMW is to work in a repository for the first time, or when a label, an ignored directory, the repository's checks or its TESTING.md is missing.
---

# Set up MMW

Sets a repository up for the landing pipeline: everything the pipeline needs once per repository, checked, created where this skill can create it, and reported where only the owner can act. It hands back what changed between the check before and the check after, what it wrote and created, and what is still missing with who has to act. Re-running it is safe, so it is also the check-up of a repository already set up: `scripts/check.py` writes nothing, and every write below keeps what is already there.

What you write here is read at the moment of acting by every playbook that publishes or triages an issue, by every script that puts a label on one, and by every worker and reviewer that works in this repository. A wrong command or a wrong line is repeated by each spec, ticket and night after it, without an error. So make each file true of this repository rather than filling in a template: check a command against the repository before you write it down.

The machine is set up once by the toolbox's own install, not here: `scripts/check.py` reports its rows and changes nothing on the machine.

## Steps

1. **Check.** From the repository root, run `python3 scripts/check.py` of this skill. It prints one line per item, `ok`, `missing`, `note` or `unchecked`, under the layers `repository` and `machine`, then `SETUP OK` or `SETUP INCOMPLETE <n> missing`.
   Done when you hold its table.
2. **Stop if the tracker is not GitHub.** The pipeline's store is GitHub Issues with sub-issues and issue dependencies, reached through `gh`; nothing else works. When the `tracker` row or the `sub-issues and dependencies` row is `missing`, tell the owner what the row says to do, set up nothing, and stop.
   Done when both rows are `ok`, or `sub-issues and dependencies` is `unchecked` because the repository has no issue yet.
3. **Create the labels.** Run `python3 scripts/labels.py`. It creates every label of the pipeline the repository lacks, with the colour and description `verify-ticket.py` defines, and leaves the ones the repository has as they are. `verify-ticket.py` also creates a label it needs on first use, but a playbook's own `gh issue edit --add-label` does not, and fails on a label the repository lacks.
   Done when it printed `LABELS OK <n>`.
4. **Ignore the pipeline's directories.** Add `.worktrees/` and `.scratch/` to the root `.gitignore` when the `.gitignore` row says they are not ignored: ticket worktrees are cut under the first, and the logs of the acceptance criteria's and `scripts/check`'s runs are written under the second.
   Done when `git check-ignore` reports both as ignored.
5. **Give the repository its `scripts/check`.** The dispatch skill runs its default tier on every ticket's merge result before the ticket lands, and once before a night opens, and it is the one check a commit made with `--no-verify` still passes through; a repository without one gets no ticket opened or landed. When the table says `scripts/check` is missing or not executable, run the Set up code checkers playbook (the `mmw-mode` skill's `playbooks/set-up-code-checkers.md`): it wraps the commands the repository already runs, and commits and pushes its own change.
   Done when Set up code checkers is done, or the table showed nothing for it to do.
6. **Write `TESTING.md`.** When `TESTING.md` is missing at the repository root, write it from what the tests do now, in seven sections: where the tests live and which layers there are; how one is run; which external boundaries are stubbed and how; how a test puts the system into a state it needs; traps; which test groups a change needs, as one sentence pointing at the map in `scripts/check`, the map's only copy; and the tests written a way that looks wrong on purpose, with why. Each line states a fact the code already shows, with a file that shows it, never a rule for what a good test is; a repository with no tests says so in one line. Its readers are whoever writes a spec or a ticket, whose seam draws on it, and the review's Tests axis. A file already there stays as it is: a fact of how the tests run changes in the same commit as the change that makes it true.
   Done when `TESTING.md` exists.
7. **Commit and push.** Commit every file steps 4 and 6 wrote, and nothing a check run left behind, in one commit on the branch checked out, and push it: ticket worktrees are cut from `origin`, so a file only on this machine is one no worker reads. A push the remote refuses goes into the reply with its reason.
   Done when the commit is on `origin`, or the reply says why it is not.
8. **Check again.** Run `python3 scripts/check.py` again.
   Done when you hold its second table.

**Reply:** the second table's summary line; each item that changed between the two tables; what was written and created; when step 5 ran Set up code checkers, each tier's measured total and each existing command it could not wrap, with its first failing line; each row still `missing` or `note`, with who acts on it: the owner for a GitHub setting or a branch rule, the toolbox's install for a `machine` row; and the commit and branch of step 7.
