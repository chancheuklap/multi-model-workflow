# Verify and report

All situations. Two things close the work: the mechanical checks pass, and the report says what changed. `<scripts>` below is resolved in [../SKILL.md](../SKILL.md), **Resolve `<scripts>` once**.

## Checks

From the repository root:

```bash
bash <scripts>/check.sh .
```

The script judges only what a machine can: the root `AGENTS.md` exists and is within the limit it sets; every `AGENTS.md` has a `CLAUDE.md` beside it made of `@` lines, one of them `@AGENTS.md`; every backticked path with a slash exists; every `<important if="...">` closes; the root carries the subdirectory sentence; no `AGENTS.override.md` remains. It prints one line per failure and exits non-zero. Fix every line it prints and run it again until it prints `ok`. A failure whose cause is that this repository cannot satisfy it is a pass: write that cause down and stop there. Two failures reach that — a root file already over the limit with nothing left to move into a directory's file (it prints `<path>: <n> lines, limit is <limit>`), and a backticked path that a clean checkout does not hold (a generated file, a file the repository ignores). A placeholder path is not one of them: `check.sh` skips a backticked token carrying `<…>`.

Verify exact paths and commands exist. The script covers paths. Commands you verify yourself: run each one a file names, or read the script it invokes, and fix the line when it fails.

## Report

The report goes into the conversation (or the scheduled run's output), never into a file in the repository.

**create** — the files written with their line counts, and the user's answers that became lines. Then **Defects found**: every survey entry of type defect, one line each with its evidence.

**rewrite** — the two lists from the end of `destinations.md`, then **Defects found** as above:

```
What was removed and why:
- <rule or section> — <reason>

What was NOT removed:
- All commands kept (<count>)
- <rule kept on the user's confirmation>
```

**incremental** — first commit every edited file on the branch with the message `agents-md: incremental update <YYYY-MM-DD>`. Then one block per changed file, from `changes.md`:

```
### Update: ./path/to/AGENTS.md

**Why:** [one-line reason]

```diff
+ [the addition - keep it brief]
- [the line removed]
```
```

followed by **Pending user decisions**: one line per user-owned line that looks stale, per empty pair, and per new pair awaiting its purpose line — each with the file, the line, and the code evidence. The user merges the branch after reading.

Done when `check.sh` prints `ok`, every command in every file you wrote or edited has been verified, and the report is written. In the incremental situation, done also requires the one commit on the branch.
