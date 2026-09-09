# Incremental update

Situation: **incremental**. A scheduled run; the user is not present. When you are done, a branch holds one commit that brings every `AGENTS.md` with code changes under it back in line with the code, and a report says what changed and what waits for the user.

## What stays untouched in this situation

Some lines exist only because the user said so: the identity lines at the top of the root file, the purpose line at the top of each nested file, and any convention or gotcha whose evidence in today's survey list is `user` or absent. Those are **user-owned**. In this situation you read them and leave them; when one looks stale, it goes into the report under **Pending user decisions** with the evidence, and the line stays as it is.

## Set up

1. Resolve the repository root with `git rev-parse --show-toplevel`. Confirm the working tree is clean: `git status --porcelain` prints nothing. A dirty tree means someone is mid-change; stop and report instead of committing on top of it.
2. Create the working branch from the current head: `git switch -c agents-md/incremental-<YYYY-MM-DD>`.
3. Make a scratch directory outside the repository (`mktemp -d`) and keep its path. Write `situation.md` there, holding the single word `incremental`; the shared steps read it to send you on. Write `inputs.md` beside it: under `## Other tools' instruction files` list `.cursor/rules/`, `.cursorrules`, `.github/copilot-instructions.md`, `GEMINI.md` if they exist, else `none`; the headings `## Commands found in old files` and `## Imports found in old CLAUDE.md files` say `none`.
4. Confirm the repository is already in this skill's format: the listing command in [../SKILL.md](../SKILL.md) lists a root `AGENTS.md` and no `AGENTS.override.md`. If either fails, the repository has not been through the create or rewrite situation: delete the working branch, report "run the rewrite situation by hand first", and stop.
5. For every `AGENTS.md` the listing command lists, compute its anchor and its change set:
   - anchor: `git log -1 --format=%H -- <dir>/AGENTS.md`
   - change set: `git diff --name-only <anchor>..HEAD -- <dir> | grep -v '\.md$'`
   Save the files whose change set is not empty, each with its change set, as `scope.md` in the scratch directory. A file with an empty change set is out of this run. The root file's change set is the whole repository's, nested files' changes included: a change under a nested directory can bear on a root rule too.
6. If `scope.md` is empty: delete the branch, report "no code changes under any AGENTS.md since its last commit", and stop.

The commit on the branch is made at the end, in [verify.md](verify.md), after the checks pass.

Done when the branch exists, `situation.md` is in the scratch directory, and `scope.md` lists every `AGENTS.md` that has code changes under it.

Next: [survey.md](survey.md).
