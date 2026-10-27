---
name: retro
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Retrospective capabilities

Record evidence-backed analyst conclusions on problem registrations. The owner decides what to do during a separate backlog review. This skill supplies commands and analyst instructions; the calling playbook owns their order and any session dispatch.

## Commands

Run `python3 scripts/retro.py --help` for command arguments.

- `gather (--spec <n> | --ticket <n>) <owner/repo>… --out <dir>` reads GitHub events, issues, and git. Run it from the product checkout and include the product and MMW repositories. It writes one material file per nonempty angle and `context.json`, which identifies the run and gathered issue codes. It prints each material path and count.
- `apply <answer file>…` validates each answer row and its evidence, then writes one `lesson.assessed` event per accepted row on its registration. Each event preserves the conclusion, reason, evidence and plan, identifies the run and request, and records the occurrence threshold as `qualifies` without changing the conclusion. It does not close, merge, reopen, relabel, edit or transfer registrations. New problems under `## Problems` still register as `retro-signal`. The retrospective receipt counts recorded rows by conclusion, with `proposals` as a row count. It reads `context.json` beside the first answer, or the file named by `--context`. Preserve that gather artifact. Follow stderr for a refused row or incomplete write. Repeating the same command uses the material directory's `.retro-apply` plan and comment markers to finish missing writes without recording a row twice.

## Analyst instructions

The session sent to sort one angle reads only its corresponding reference.

| Angle | File |
| --- | --- |
| 判断 | [references/judgement.md](references/judgement.md) |
| 环境 | [references/environment.md](references/environment.md) |
| 流程 | [references/process.md](references/process.md) |

Each answer is a table with `代号 | 结论 | 理由 | 证据 | 方案`, followed by `## Problems`. Conclusions are `merge:<target code or issue number>`, `reject`, `candidate`, or `propose`. A proposal names its repository, addition or deletion, file, and landing playbook. Each reference carries the complete answer format for the analyst that reads it.

The caller receives the material paths and counts from gather, and the recorded-row counts and typed receipt from apply. These commands write no skills, product code, owner-managed instruction files, or external memory.
