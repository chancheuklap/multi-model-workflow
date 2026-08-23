# Verify and report

All branches. Two things close the work: the mechanical checks pass, and the report says what changed.

## Checks

From the repository root:

```bash
bash "$(dirname <path of this skill's SKILL.md>)/scripts/check.sh" .
```

The path of `SKILL.md` is the one your host loaded this skill from. The script judges only what a machine can: the root `AGENTS.md` exists and is within 150 lines; every `AGENTS.md` has a `CLAUDE.md` beside it made of `@` lines, one of them `@AGENTS.md`; every backticked path with a slash exists; every `<important if="...">` closes; the root carries the subdirectory sentence; no `AGENTS.override.md` remains. It prints one line per failure and exits non-zero. Fix every line it prints and run it again until it prints `ok`.

Verify exact paths and commands exist. The script covers paths. Commands you verify yourself: run each one a file names, or read the script it invokes, and fix the line when it fails.

## Report

The report goes into the conversation (or the scheduled run's output), never into a file in the repository.

**create** — the files written with their line counts, and the maintainer answers that became lines.

**rewrite** — the two lists from the end of `destinations.md`:

```
What was removed and why:
- <rule or section> — <reason>

What was NOT removed:
- All commands kept (<count>)
- <rule kept on the maintainer's confirmation>
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

followed by **Pending maintainer decisions**: one line per maintainer-owned line that looks stale, per empty pair, and per new pair awaiting its scope sentence — each with the file, the line, and the code evidence. The maintainer merges the branch after reading.

Done when `check.sh` prints `ok`, every command in every file you wrote or edited has been verified, and the report is written. On the incremental branch, done also requires the one commit on the branch.
