# 抄写来源与精确修改清单

技能正文里凡是引用参考项目的段落都逐字复制原件，只做 spec 点名的精确修改。本文件逐处列出，供复核。

## 原件

| 原件 | commit | 本仓库副本 |
| --- | --- | --- |
| unlazy `references/orchestration.md` | 754d9a6 | `docs/specs/landing-orchestrator/unlazy-orchestration-blueprint.md`（已 diff 确认逐字一致） |
| unlazy `references/method.md` | 754d9a6 | `docs/specs/landing-orchestrator/unlazy-method-blueprint.md`（已 diff 确认逐字一致） |
| pstack `pstack/skills/poteto-mode/playbooks/orchestrate.md` | 46125561 | 无副本；引用段落见下 |
| pstack `pstack/skills/poteto-mode/scripts/orch/store.ts` `renderGates` | 46125561 | 无副本；格式见 `parking-issue.md` |

## 抄进了哪里、改了什么

### SKILL.md「主循环」— unlazy「Rolling dispatch」代码块

原文：

```text
while an unverified leaf remains:
  dispatch each READY leaf whose ownership is claimed
  wait for the next leaf to return
  reverify that leaf and review its manual evidence
  append status and update its declared state
  promote each WAITING leaf whose Needs are all VERIFIED
```

修改（只换角色名与命令，逐处）：

1. `an unverified leaf remains` → `frontier 非空或有在途票`（leaf → 票；unverified → 未收尾）
2. `dispatch each READY leaf whose ownership is claimed` → `对 frontier 里每张票：认领（assignee），然后派发`（READY = frontier；ownership is claimed = `gh issue edit <n> --add-assignee @me`）
3. `wait for the next leaf to return` → `herdr agent wait <工人名>`（等 blocked / done）
4. `reverify that leaf and review its manual evidence` → `派复验者 subagent`
5. `append status and update its declared state` → `把判决与分诊结果写成票评论`
6. `promote each WAITING leaf whose Needs are all VERIFIED` → `回到查 frontier`（原生阻塞边随上游关票自动解除，不需要手工 promote）

紧随其后的一句原样保留：「Do not invent a dependency during dispatch.」后半句 `Add it to PLAN.md, correct the affected states, and record the change.` → `停车成 issue`（本仓库没有 PLAN.md；跨票依赖出现即停车）。

### SKILL.md「主循环」— unlazy「Driver loop」第 3、4、5、6 条

- 第 3 条「Claim every concurrent leaf」：保留「A refused claim means the split is not safe for concurrent dispatch. Change the plan or run the work sequentially; never bypass the refusal.」；`gate-check.mjs --claim` 命令 → `gh issue edit <n> --add-assignee @me`；refused claim 的本仓库含义 = 认领时发现已有 assignee。
- 第 4 条：全文抄进 `reference/brief.md`，映射见该文件。
- 第 5 条「Verify each return independently」：`--status alone is not re-verification.` 保留；`gate-check.mjs --reverify` → 派复验者 subagent；「try to refute at least one passed gate」保留为复验者的既有行为（verifier body 已含）。
- 第 6 条：`Mark the leaf VERIFIED, promote newly unblocked leaves from WAITING to READY, and dispatch them without waiting for unrelated in-flight leaves.` → leaf VERIFIED = 票关闭；promote = 原生阻塞边自动解除；「dispatch them without waiting for unrelated in-flight leaves」原样保留。

### SKILL.md「失败、升级与存活」— pstack「Liveness and failure」全节

七条 bullet 逐字复制，修改逐处：

1. 第 1 条：`the ledger, units.tsv, gh, pushed branches, the cloud agent's status in the Cursor dashboard` → `关卡状态文件 .mmw-ticket-state.json、票评论、gh、分支上的 commit、herdr agent get`；`Transcript mtime is not liveness.` 之后加一句 `Herdr 的 unknown 状态也不是死亡证据。`
2. 第 2 条：`a synthetic postmortem row in the inbox` → `一条票评论`。
3. 第 3 条：`respawn with smaller scope`、`retry as-is`、`retry on a different model`、`retry once` 原样；`retry on a different model` 的本仓库含义 = 初级→高级（定级升级，只升不降）；`Two retries, then abandon the unit and replan around it.` → `同票两败弃单绕开并停车记录`（弃单 = 停车 issue + 让路）。
4. 第 4 条（zombie）：原样；`fresh unit` → `新一轮复验`。
5. 第 5 条（stop line）：`write a stop line at the top of the standing orders` → `终止循环并推送通知`（本仓库没有 standing orders 文件）。
6. 第 6 条（bound infra retries）：原样；`write a terminal handoff to durable state` → `写成任务父 issue 的评论`。
7. 第 7 条（after a Cursor restart）：`After a Cursor restart: local agents are dead, cloud work is not.` → `编排会话重启后：Herdr pane 里的工人仍在，看 herdr agent list`；`Re-read the standing orders and units.tsv, recompute the frontier, reattach cloud work by PR and branch rather than agent id` → `重读 models.md 与父 issue 上的计划评论，重查 frontier，按票号与分支重接工人`；后半句关于 sub-coordinator 与 store lock 的内容删除（本仓库没有这两样）。

### SKILL.md「停车」与 `reference/parking-issue.md` — pstack「Escalation」与 gates.md 格式

- 「Escalation」第 1 段的 `Park each as a gates.md entry before asking, and route work around it.` 与第 2 段「Never reaches the human: … When in doubt, act and log; deferring is the measured failure mode.」逐字保留；`gates.md entry` → 停车 issue；`the human` 的「asking」在本仓库 = 推送一条通知，整夜不问。
- gates.md 格式：`renderGates` 的输出形状原样；加 `- Consequences:` 一行。

### 规划者 `body.md` — unlazy「Contract checklist」七项与「Driver loop」第 1 条

- 七项逐字复制；每项后标「进契约」或「票已覆盖：<由什么覆盖>」。裁剪结果：进契约的是 interfaces and schemas、toolchain/shell/working-directory、error and compatibility conventions，加 spec 点名的 naming（unlazy method 规则 3 原句里有 naming）。
- 第 1 条「Plan before fan-out」：`Fix interfaces, naming, toolchain, dependencies, and exact ownership before dispatch.` 原样；`.unlazy/<scope>/PLAN.md` 等文件 → 父 issue 上的固定标题评论。
- 「Do not let two concurrent leaves own the same path. If shared work cannot be separated, make it an earlier dependency or a dedicated integration leaf.」原样，leaf → 票。
