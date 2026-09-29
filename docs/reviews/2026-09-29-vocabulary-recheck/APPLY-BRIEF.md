# Vocabulary recheck (2026-09-29): brief for each applier

The owner has approved `DECISIONS.md` beside this file. You apply it inside the files you own (your task names them), in the repository `/Users/cheuklapchan/multi-model-workflow` on branch `dev`. Four other appliers own the rest of the repository at the same time, so a file outside your ownership is not yours to edit even when a decision touches it: list it in your final message (path, line, the change) and the coordinator applies it.

## What to apply

Read `DECISIONS.md` in full, then for each row read the `verify/` row it names (and, for W rows, `verify/d.md` part 1; for new entries, part 2; for leftovers, part 3): those rows list every place the change touches, with line numbers taken on commit `e2dab1d7`. Grep again rather than trusting the line numbers; the lists can be incomplete, and every occurrence in your files is yours.

- **Renames (T rows) and sense splits (W rows):** change the prose name everywhere in your files: glossary entries, skill text, references, merge-notes, the text scripts print or build for an agent, comments and docstrings. Machine identifiers stay byte for byte (`DECISIONS.md` first paragraph). A glossary entry takes the new name as its bold line; put the old name on its `_Avoid_` line only where the old name is actually still wrong somewhere a reader will meet it (`CONTEXT-MAP.md`'s rule for `_Avoid_`).
- **Definitions corrected:** apply the wording the verify row gives. For the unverified mismatches the section names, and every other one recorded in the reason column of `candidates/*.md` for an entry in your files, open the entry's `_Home_`, confirm the mismatch yourself, and correct the definition only when the file bears it out.
- **New entries (verify/d.md part 2, outcome ENTRY or DEFINITION):** add the ones whose context is in your files, in the existing entry shape (bold name, one or two sentences, `_Avoid_` only when needed, `_Home_`), under the section whose neighbours they belong with. Write only what the `_Home_` file bears out.
- **Leftovers (verify/d.md part 3):** replace the old names in your files as the row says.
- **Not yours:** the task board page's visible strings (`mmw-v2/board/page/*.mjs` string literals and `index.html`), the design package under `prototypes/`, and `docs/specs/`: the owner's board changes go through the design pipeline separately. Code comments in `mmw-v2/board/` are the owner-of-`task-board` applier's.

## How to write

Follow `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md` for skill text (English, no em-dash in `.md` under `mmw-v2/upstream/skills/`). A file describes its subject as it is now: no "renamed from", no "formerly", no mention of this round, except in a merge-note's record of what MMW changed and why. Edit surgically: change the sentence, not the paragraph around it.

An edit to a file under `mmw-v2/upstream/` (a subtree of upstream skills) that changes wording MMW already owns keeps the matching merge-note in `mmw-v2/merge-notes/<skill>.md` true: update the entry that quotes or describes the passage. Read `mmw-v2/merge-notes/README.md` before your first such edit.

## Verify

Run, for each script or suite your edits touched, the smallest set that proves it (the repository's rule: no aggregate run): `bash mmw-v2/tests/<name>/run.sh` for a changed skill's suite, or one scenario of `bash mmw-v2/tests/dispatch/test_dispatch.sh <scenario>` for a changed `dispatch.sh` message (grep the scenarios for the function you touched). Every `run.sh` starts with the shared lints (module paths, upstream em-dashes, frontmatter); when you changed only prose, run those three directly: `python3 mmw-v2/tests/lib/check_module_paths.py`, `python3 mmw-v2/tests/lib/check_upstream_em_dashes.py`, `uv run mmw-v2/tests/lib/check_own_skill_frontmatter.py`. Report a failure with its first failing line; fix it when it is yours.

Do not commit, do not run `install.sh`, do not touch `.worktrees/`.

## Final message

The rows you applied (by `DECISIONS.md` number or verify row), the count of files changed, the new entries added, the definitions you corrected and those you left because the `_Home_` did not bear the mismatch out, the tests you ran with their result, and every change that falls outside your files (path, line, change).
