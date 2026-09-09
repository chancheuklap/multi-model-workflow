# Closing the ticket out

`<engine>` is resolved once, the way this skill's `SKILL.md` says under `## Resolve `<engine>` once`.

The work is committed and the ticket's last comments are being written. Four runs belong to this moment.

## `--decisions`

```
<engine> <n> --decisions <file>
```

It lands a comment whose first line is `DECISIONS`. The file is two sections and no others: `Decisions I made on my own` — every such line written so far, one per line, in the shape the closing comment uses — and `Outside Owns` — the `Outside Owns:` line of the newest `self-run`, followed by one sentence per file saying which criterion could not pass without it; `None` when that line is `None`. A ticket keeps one such comment and no more: a second run is refused with `#<n> already carries a DECISIONS comment` and posts nothing. A missing or extra section is refused the same way, with the section named on stderr.

## `--touched`

```
<engine> <n> --touched
```

It lands a `TOUCHED BY #<n>` comment on each open sibling whose `## Owns` covers a file on the newest `self-run`'s `Outside Owns:` line, so the ticket that owns the file learns that somebody else wrote in it. When that line is `None` nothing is posted. It is refused with `#<n> carries no REVIEW comment` on a ticket the reviewer has not reported on yet: the review is what says whether those files should have been touched at all.

## `--draft`

```
<engine> <n> --draft <out-file>
```

Nothing lands on the ticket. The closing-comment skeleton is written to `<out-file>`, recounted from the ticket and the newest `self-run`, with `skipped:` and `Decisions I made on my own` left as `<fill>`; its `Sub-issues opened:` is this ticket's sub-issues. Fill those two before the next run — `--closeout` refuses the skeleton until they are.

## `--closeout`

```
<engine> <n> --closeout <draft>
```

It posts the draft, takes `ready-for-agent` off, and closes the ticket. A draft whose first line is `HANDOFF REQUIRED` posts and swaps `ready-for-agent` for `needs-triage`, leaving the ticket open to be judged fresh.

When it refuses, the first line of stderr counts the problems, names the first, and gives the `--check-only` command that prints them all; every problem after the first is one more line opening `also:`. A refused draft leaves the ticket exactly as it was. `--closeout <draft> --check-only` reports on a draft and changes nothing, at any time.

## What `--closeout` reads the draft against

You are the worker who wrote the closing comment to a file and had it refused. Every condition below is one `--closeout` checks against the draft before it posts the draft; the stderr line names the first, and `--check-only` prints them all. A refused draft leaves the ticket exactly as it was — same comments, same state, same labels.

Fix the draft, or fix what the draft describes, and run it again.

- **The first line and what it commits to.** It is `ALL MET`, or `HANDOFF REQUIRED: <abandoned> abandoned (<kinds>), <unmet> unmet, <met> met of <total>`, and nothing else. An `ALL MET` draft may leave no criterion unmet and may abandon none as `failed` or `stuck` — only `decision` is abandoned and still closes.
- **The `ABANDON:` lines.** Each names one of `decision`, `failed`, `stuck`, and points at a criterion the draft itself lists. No round count is asked of any kind: `failed` (it ran and did not pass) and `stuck` (it would not run) are told apart for the reader, and the reason on the line says what was tried.
- **The ticks and their `EVIDENCE:`.** A ticked criterion whose evidence is missing or `pending` is refused, and so is a `CHECK:` continued on a bare line instead of in a fenced block.
- **`Counts: <met> met, <unmet> unmet, <abandoned> abandoned of <total>`.** The line has to be there, it has to match the draft recounted criterion by criterion, and on a `HANDOFF REQUIRED` draft the first line's four numbers have to agree with it.
- **The verifier's own run.** An `ALL MET` draft is read against the newest `reverify` comment on the ticket, and never against a `self-run`. It is refused when the ticket carries no `reverify` at all, and when that run summarises as `UNMET:` or `HANDOFF REQUIRED:` — unless every criterion it left unmet is one the draft abandons as `decision`; a run is generated from the ticket body, which carries no `ABANDON:` line, so a `decision` criterion still runs and still reports unmet there. A `self-run` of your own, however new and however green, does not settle this: on 2026-09-06 #162 closed by posting one after its verifier had reported `AC1 failed`. Dispatch the verifier again, or close out as `HANDOFF REQUIRED`.
- **The criteria that run covered.** The `reverify` ledger and the ticket's current `## Acceptance criteria` must describe the same criteria: same text, same `CHECK`. A ticket may legitimately rewrite a criterion, but then what stands is a verification of a different question, and the verifier runs again. This is the other half of #162: the criterion the verifier failed was rewritten into one that passed.
- **`VERDICT`.** An `ALL MET` draft needs the verifier's `VERDICT <full 40-character commit> by <model> — <one line>` on the ticket, and that commit must be `HEAD`. What was verified independently has to be what gets merged, and there is no line you can write instead: the verifier runs after the last commit, which is why it is the last of the closing steps.
- **The review's `Missing` against a screen-contract row.** When the ticket's `## Read first` names screen-contract rows and the newest `REVIEW` comment's Spec axis reports a `Missing` that names one of them, the draft has to name that row id too — beside the commit that fixed it, or under `Sub-issues opened:`. A finding that a control calls nothing is the one this pipeline was rebuilt to stop letting through, so silence on it is a refusal.
- **The working tree and the branch.** No uncommitted changes to tracked files, and the ticket branch contains its base commit — the one dispatch recorded in `git config branch.issue-<n>.mmw-base`, `main` when there is no record. Merge it, never rebase, because the `VERDICT` names one commit.
- **The ticket.** Still `OPEN`, and assigned to you.

`HANDOFF REQUIRED` is held to none of the `VERDICT` conditions. It claims nothing was finished, so it is the way out of anything you cannot fix yourself, including a verifier that never ran. Whether the work is any good is what the `CHECK` commands, the verifier and `code-review` decide before you write the draft.

One gate comes after the draft: an accepted `ALL MET` draft still has to pass the repository's own `checks` in `.mmw/target.json` before the ticket closes. `checks` is optional and this run's to read: a list run in order at the repository root, each entry a command string held to the same bound as a `CHECK:` (`DEFAULT_TIMEOUT`, 600 s) or `{"run": "<command>", "timeout": <seconds>}` for a suite that needs longer. Any non-zero exit leaves the ticket open and posts `CHECKS FAILED` with each failed command and its last 20 lines; every exit 0 appends `CHECKS OK <n>/<n>` to the closing comment. A key that is not a list, an entry of another shape, or a file that is not JSON is `CHECKS FAILED`, not absence; a repository without the key is unchanged. `--reverify`, `--lint`, `--check-only` and a `HANDOFF REQUIRED` draft do not run them. `CHECKS FAILED` on the ticket means the draft was fine and the suite was not; fix the code, run the suite yourself, and run `--closeout` again.

## Exit codes

- `--decisions` and `--touched`: `0` posted (or, for `--touched`, nothing to post), `2` refused, with the reason on stderr and nothing posted.
- `--draft`: `0`. It writes a file and reads no condition, so there is nothing for it to refuse.
- `--closeout`: `0` the ticket is closed, `1` refused — by one of the conditions above, or by the repository's own `checks`.
