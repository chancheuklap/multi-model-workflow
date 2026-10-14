---
name: retro
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Retrospective capabilities

Turn problem registrations and run signals into evidence-backed proposals for the owner. A proposal is a request for a decision, not permission to implement it. This skill supplies commands and analyst instructions; the calling playbook owns their order and any session dispatch.

## Commands

Run `python3 scripts/retro.py --help` for command arguments.

- `expire <owner/repo>…` closes open lesson candidates whose last occurrence is more than 30 days old. It leaves the owner's queue, product problems, and children alone.
- `gather (--spec <n> | --ticket <n>) <owner/repo>… --out <dir>` reads GitHub events, issues, and git. Run it from the product checkout and include the product and MMW repositories. It writes one material file per nonempty angle and `context.json`, which identifies the run and gathered issue codes. It prints each material path and count.
- `apply <answer file>…` validates each answer row, checks its evidence and occurrence threshold, and writes the accepted dispositions and retrospective event. It reads `context.json` beside the first answer, or the file named by `--context`. Preserve that gather artifact rather than inventing run metadata. Follow stderr for a refused row or incomplete write.

## Analyst instructions

The session sent to sort one angle reads only its corresponding reference.

| Angle | File |
| --- | --- |
| 判断 | [references/judgement.md](references/judgement.md) |
| 环境 | [references/environment.md](references/environment.md) |
| 流程 | [references/process.md](references/process.md) |

Each answer is a table with `代号 | 结论 | 理由 | 证据 | 方案`, followed by `## Problems`. Conclusions are `merge:<target code or issue number>`, `reject`, `candidate`, or `propose`. A proposal names its repository, addition or deletion, file, and landing playbook. Each reference carries the complete answer format for the analyst that reads it.

The caller receives the material paths and counts from gather, and the issue dispositions and typed event from apply. These commands write no skills, product code, owner-managed instruction files, or external memory.
