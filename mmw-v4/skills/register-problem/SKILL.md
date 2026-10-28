---
name: register-problem
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Register a problem

Record a problem you cannot fix in the work at hand. The registration gives the retrospective evidence to check and the owner a problem to decide on. Without evidence and cost, it becomes a queue of opinions rather than work someone can take on.

A worker holding a ticket uses the verify-ticket skill's `scripts/verify-ticket.py --sub-issue` for that ticket's product problems. This skill handles the other problems.

## Decide whether to register

Register only when all three hold:

- The problem caused a cost: time, an error, rework, or an owner's correction.
- You cannot fix it in the work at hand. It is outside that work's scope, or the fix needs the owner's decision.
- You can point at evidence: a file and line, a command and output, an event, an issue, or a commit link.

Leave out problems already fixed in this work, one-off problems that cannot recur, and personal preferences.

Before handing work back, ask yourself:

- 判断: Was I corrected, or did I claim completion without verifying the work?
- 环境: Did I spend a long time finding a file or command, or fail to obtain information I needed?
- 流程: Was the skill or workflow I followed wrong, incomplete, or ineffective?

## Register where the fix belongs

The repository holding what needs to change owns the registration. MMW skills, playbooks, and scripts belong in the MMW repository. Product code and the product repository's glossary and ADRs belong in the product repository.

Verification-tool problems specific to one product's environment tool or `verify-<product>` are registered in the product repository; problems shared by similar products are registered in MMW.

1. Search first with `python3 <this skill's directory>/scripts/register.py find <keywords>`. For another target repository, pass `--repo <owner/repo>`. Read the matches before choosing a problem code. Different wording can describe the same problem.
   Done when you have checked the matches and reused the existing code where the problem is the same.
2. Write a file with `## Problem` and six fields: 问题代号, 角度, 发生了什么, 证据, 代价, 该谁修. Use a lower-case hyphenated English phrase of at most 80 characters for 问题代号. Use 判断, 环境, or 流程 for a lesson, or 产品 for a product problem. Keep the angle in the body, without an angle label. You may add one suggested direction.
   Done when all six fields identify one problem and its evidence, cost, and responsible repository.
3. Run `python3 <this skill's directory>/scripts/register.py add <file>` from the repository where the problem occurred. Pass `--repo <owner/repo>` for the repository that owns the fix. When registering an occurrence on a ticket, pass `--ticket <n>` to record that ticket and read its parent spec. Use `--source owner-correction` for an owner's correction, `--source stall` for a stall, or `--source retro-signal` for evidence found during the retrospective. Ordinary discoveries need no source flag. Follow stderr when a write is incomplete, and rerun the same command to finish it.
   Done when the command exits 0 and names the issue it opened or appended to. Return that issue to the caller. If the command cannot complete, return its reason with the evidence rather than claiming a registration exists.

Example:

```text
## Problem

问题代号：test-compares-empty-lists
角度：判断
发生了什么：看板设置页的测试按一个不存在的字段过滤，一直在比较两个空列表；测试无论看板显示什么都会通过。
证据：mmw-v4/tests/board/local-config.test.mjs:193；修复提交 e57dca072
代价：看板少显示一个角色时，没有任何测试会报错
该谁修：MMW 仓库
建议：做成检查（加）：一个测试如果没比较到任何东西，就判失败
```

A second occurrence with the same cause reuses this code, even in another ticket. It belongs on the same issue rather than in a new registration.
