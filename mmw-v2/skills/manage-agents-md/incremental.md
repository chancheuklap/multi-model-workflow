# Incremental update

Branch: **incremental**. A scheduled run; the maintainer is not present. When you are done, a branch holds one commit that brings every `AGENTS.md` with code changes under it back in line with the code, and a report says what changed and what waits for the maintainer.

## What stays untouched on this branch

Some lines exist only because the maintainer said so: the identity lines at the top of the root file, the scope sentence at the top of each nested file, and any convention or pitfall that no code evidence supports. Those are **maintainer-owned**. On this branch you read them and leave them; when one looks stale, it goes into the report under **Pending maintainer decisions** with the evidence, and the line stays as it is.

## Set up

1. Resolve the repository root with `git rev-parse --show-toplevel`. Confirm the working tree is clean: `git status --porcelain` prints nothing. A dirty tree means someone is mid-change; stop and report instead of committing on top of it.
2. Create the working branch from the current head: `git switch -c agents-md/incremental-<YYYY-MM-DD>`.
3. Make a scratch directory outside the repository (`mktemp -d`) and keep its path.
4. For every `AGENTS.md` the `find` in [SKILL.md](SKILL.md) lists, compute its anchor and its change set:
   - anchor: `git log -1 --format=%H -- <dir>/AGENTS.md`
   - change set: `git diff --name-only <anchor>..HEAD -- <dir> | grep -v '\.md$'`
   Save the files whose change set is not empty, each with its change set, as `scope.md` in the scratch directory. A file with an empty change set is out of this run.
5. If `scope.md` is empty: delete the branch, report "no code changes under any AGENTS.md since its last commit", and stop.

Done when the branch exists and `scope.md` lists every `AGENTS.md` that has code changes under it.

Next: [survey.md](survey.md).
