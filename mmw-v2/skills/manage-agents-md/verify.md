# Verify and report

Two things close the work: the mechanical checks pass, and the report says what changed.

## Checks

Run, from the repository root:

```bash
bash <this skill's directory>/scripts/check.sh .
```

It judges only what a machine can: the root file is within 150 lines; every `AGENTS.md` has a `CLAUDE.md` beside it made of `@import` lines including `@AGENTS.md`; every backticked path with a slash exists; every `<important if="...">` closes; the root carries the subdirectory sentence; no `AGENTS.override.md` remains. It prints one line per failure and exits non-zero. Fix every line it prints and run it again until it prints `ok`.

Verify exact paths and commands exist. The script covers paths; commands you verify yourself: run each one the file names, or read the script it invokes, and fix the line if it fails.

## Report

The report goes into the conversation, not into any file in the repository.

**After a create**: the list of files written with their line counts, and the maintainer answers that became lines.

**After a rewrite**, the two lists from [migrate.md](migrate.md):

```
What was removed and why:
- <rule or section> — <reason>

What was NOT removed:
- All commands kept (<count>)
- <rule kept on the maintainer's confirmation>
```

**After an incremental update**, one block per changed file:

```
### Update: ./path/to/AGENTS.md

**Why:** [one-line reason]

```diff
+ [the addition - keep it brief]
- [the line removed]
```
```

followed by **Pending maintainer decisions**, one line each: file, the line, and the code evidence that makes it look stale.

Done when `check.sh` prints `ok`, every command in every file was verified, and the report is written.
