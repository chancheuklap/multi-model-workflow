# Incremental update

A scheduled run. The maintainer is not present. You will find which `AGENTS.md` files have code changes under them since each was last committed, update only what code evidence supports, commit on a branch, and leave a report.

## What this branch never touches

Content that only the maintainer knows is not yours to change here: the root identity lines, each nested file's scope sentence, and any convention or pitfall line that no code evidence supports. If one of them looks stale, say so in the report under **Pending maintainer decisions** and leave the file line as it is. The maintainer questions in [ask.md](ask.md) are not asked on this branch.

## Before the shared steps

1. Resolve the repository root and confirm the working tree is clean: `git status --porcelain` prints nothing. A dirty tree means someone is mid-change; stop and report instead of committing on top of it.
2. Create the working branch from the current head: `git switch -c agents-md/incremental-<YYYY-MM-DD>`.
3. For every `AGENTS.md` (skipping the directories `scripts/check.sh` skips), compute its anchor and its change set:
   - anchor: `git log -1 --format=%H -- <dir>/AGENTS.md`
   - change set: `git diff --name-only <anchor>..HEAD -- <dir> | grep -v '\.md$'`
   A file whose change set is empty is skipped for the rest of the run. Write the remaining files down with their change sets; this list is the survey's scope.
4. If no file has a change set, commit nothing, delete the branch, and report "no code changes under any AGENTS.md since its last commit".

Done when the branch exists and the list of files with non-empty change sets is written down.

## Shared steps, in order

1. [survey.md](survey.md) — scoped to the change sets only; one directory group per listed file, no topic groups.
2. [additions.md](additions.md) — decide what the changes make stale and what they add.
3. [prune.md](prune.md) — cut what must not be there; run the self-check on every file you edited.
4. [verify.md](verify.md) — run the checks; commit; write the report.

## Commit and report

Commit every edited file on the branch with one message: `agents-md: incremental update <YYYY-MM-DD>`. The report goes to the conversation (or the run's output) in the diff format from [verify.md](verify.md), followed by **Pending maintainer decisions**: one line per maintainer-owned line you believe is stale, with the file, the line, and the code evidence. The maintainer merges the branch after reading.

Done when the branch holds one commit, every listed file was either edited or explicitly reported as "no change needed", and the report is written.
