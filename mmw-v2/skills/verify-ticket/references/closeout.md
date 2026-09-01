# What `--closeout` reads the draft against

You are the worker who wrote the closing comment to a file and had it refused. Every condition below is one the run checks before it posts anything; the stderr line names the first, and `--check-only` prints them all. A refused draft leaves the ticket exactly as it was — same comments, same state, same labels.

Fix the draft, or fix what the draft describes, and run it again.

- **The first line and what it commits to.** It is `ALL MET`, or `HANDOFF REQUIRED: <n> abandoned (<kinds>), <m> unmet, <k> met of <total>`, and nothing else. An `ALL MET` draft may leave no criterion unmet and may abandon none as `failed` or `stuck` — only `decision` is abandoned and still closes.
- **The `ABANDON:` lines.** Each names one of `decision`, `failed`, `stuck`, and points at a criterion the draft itself lists.
- **The ticks and their `EVIDENCE:`.** A ticked criterion whose evidence is missing or `pending` is refused, and so is a `CHECK:` continued on a bare line instead of in a fenced block.
- **Three self-runs behind every `failed`.** Counted off the ticket's own `self-run` comments; `stuck` is held to no round count at all.
- **`Counts: <k> met, <m> unmet, <n> abandoned of <total>`.** The line has to be there, it has to match the draft recounted criterion by criterion, and on a `HANDOFF REQUIRED` draft the first line's four numbers have to agree with it.
- **The newest run's own summary.** An `ALL MET` draft is refused while the newest `self-run` or `reverify` comment on the ticket summarises as `UNMET:` or `HANDOFF REQUIRED:`. Fix what that run found and run the plain `<engine> <n>` again — the newer summary is the one read — or close out as `HANDOFF REQUIRED`.
- **`VERDICT` and `Post-verdict:`.** An `ALL MET` draft needs the verifier's `VERDICT <full 40-character commit> by <model> — <one line>` on the ticket; if HEAD has moved past the commit that line names, it also needs a `Post-verdict:` line naming every commit since and where it came from.
- **The working tree and the branch.** No uncommitted changes to tracked files, and the branch contains its base — the cut point dispatch recorded in `git config branch.issue-<n>.mmw-base`, `main` when there is no record. Merge it, never rebase, because the verdict names one commit.
- **The ticket.** Still `OPEN`, and assigned to you.

`HANDOFF REQUIRED` is held to none of the `VERDICT` conditions. It claims nothing was finished, so it is the way out of anything you cannot fix yourself, including a verifier that never ran. Whether the work is any good is what the `CHECK` commands, the verifier and `code-review` decide before you write the draft.
