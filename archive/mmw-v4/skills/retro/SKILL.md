---
name: retro
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Retrospective capabilities

Record evidence-backed analyst conclusions on problem registrations. The owner decides what to do during a separate backlog review. This skill supplies commands and analyst instructions; the calling playbook owns their order and any session dispatch.

## Commands

Run `python3 scripts/retro.py --help` for command arguments.

- `gather (--spec <n> | --ticket <n>) <owner/repo>… --out <dir>` reads GitHub events, issues, and git. Run it from the product checkout and include the product and MMW repositories. It writes one material file per nonempty angle and `context.json`, which identifies the run and gathered issue codes. It prints each material path and count.
- `backlog <owner/repo>… --out <dir>` reads every open `mmw:lesson` in the distinct repositories. It writes `<dir>/backlog.json` as a list of objects with `repo`, `number`, `problem` (the `## Problem` text), `occurrences`, `assessments` (all `lesson.assessed` payloads), and `merged` (the latest `lessons.merged` payload, or null). It prints `BACKLOG <count> open, <n> assessed since last merge`. The second count includes only assessments after each registration's own latest merge, in GitHub comment order. Registrations without a merge contribute all their assessments. This command makes no GitHub writes.
- `merge-apply <decisions.json>` applies the owner's approved backlog decisions. The JSON object has a nonempty `batch` string and a `decisions` list. Each item has `lesson` as `owner/repo#number`, `decision` as `closed`, `merged:owner/repo#number`, or `kept`, and a nonempty `reason`. Closing uses `not planned`; merging copies occurrences to the destination and closes the source as a duplicate; keeping changes no issue state. Every item receives a `lessons.merged` event with the decision and batch, and its reason in the comment. A merge destination must be open and cannot itself be closed or merged in the same batch. Registration identity is case-insensitive. The whole file is checked before writes. Rerun the same file after an incomplete write; tracker events prevent duplicate occurrence and decision comments, and closed issues are not closed again. A changed decision needs a new batch. This command runs only after the owner approves the decisions, as Merging the lesson backlog requires.
- `apply <answer file>…` validates each answer row and its evidence, then writes one `lesson.assessed` event per accepted row on its registration. Each event preserves the conclusion, reason, evidence and plan, identifies the run and request, and records the occurrence threshold as `qualifies` without changing the conclusion. It does not close, merge, reopen, relabel, edit or transfer registrations. New problems under `## Problems` still register as `retro-signal`. The retrospective receipt counts recorded rows by conclusion, with `proposals` as a row count. It reads `context.json` beside the first answer, or the file named by `--context`. Preserve that gather artifact. Follow stderr for a refused row or incomplete write. An answer with no recordable row, such as an empty table or rows that name no registration, still writes the receipt with zero recorded rows and lists each unrecorded row in it; an answer with no analysis table, or whose rows and new problems are all refused, writes nothing and exits 2. Repeating the same command uses the material directory's `.retro-apply` plan and comment markers to finish missing writes without recording a row twice.

## Analyst instructions

The session sent to sort one angle reads only its corresponding reference.

| Angle | File |
| --- | --- |
| 判断 | [references/judgement.md](references/judgement.md) |
| 环境 | [references/environment.md](references/environment.md) |
| 流程 | [references/process.md](references/process.md) |

Each answer is a table with `代号 | 结论 | 理由 | 证据 | 方案`, followed by `## Problems`. Conclusions are `merge:<target code or issue number>`, `reject`, `candidate`, or `propose`. A proposal names its repository, addition or deletion, file, and landing playbook. Each reference carries the complete answer format for the analyst that reads it.

The caller receives the material paths and counts from gather, and the recorded-row counts and typed receipt from apply. These commands write no skills, product code, owner-managed instruction files, or external memory.
