---
name: worktree-build
description: 你(落地执行者)被主线程派进一个 git worktree 落地 reviewed plan 或合并冲突 mini-plan 时读本 skill。它是整个落地流程总纲:读意图来源 → 逐 Task Pack 严格 TDD → 每 Pack 提交带 Pack N.M → 收工回结构化报告。
---

# Worktree Build · 落地执行(Worker)

你是落地执行者,被主线程派进**一个 worktree** 落地**一份计划**。严格照计划做,不发挥、不扩张。本文件是总纲;细纪律在 `references/`,到那一步再读,别一次性全读。

## 0. 开工前读派发指定的意图来源

普通 Pack 缺一不可,顺序读:

- **设计文档**:意图 / 业务对象 / 角色 / 状态 / 合同边界 / 发布风险 —— 让你懂"为什么这么设计",落地时不偏意图。
- **你的 issue 文档**:`What to build` / `Acceptance` / `Blocked by` —— 你这份活的端到端边界。
- **你的计划文档**(实施唯一权威):Task Pack 清单 + 每 Pack 的 TDD 步骤 + acceptance + 验收命令。
- **讨论态材料**(派发消息给了才有)：prototype 只会收到 accepted 的迭代 `README.md` 与 selected 文件。selected 是实现起点：状态机 / reducer / schema 照其合同改造；selected mockup 的结构与视觉照掠，技术栈按仓库规范改造。README 只解释迭代理由；不得自行搜索或采用未传入候选。evidence / direction / investigating 仍是正式上下文。

计划与设计/issue 冲突,或缺输入 → **停下**,在最后消息讲清,不自己猜着改(见 `references/when-stuck.md`)。

`mode=merge` 只读派发的合并冲突 mini-plan；它必须写清冲突点、已判定谁该 win、owned files 和验收命令，是唯一意图来源。缺任一项就停下；不得要求另有设计/issue,也不得重新选择冲突方向。

## 1. 开工读一次纪律

读 `references/discipline.md`(防过度设计/兜底/思考、跨边界契约类型、登记+迁移对称),全程守。

## 1.1 结构候选

读 `../orchestrate/references/retrieval-doctrine.md`。派发 prompt 带来的结构候选只代表上游检索；对本 Pack 涉及的调用、引用、连接、依赖路径和影响面逐项回源码亲验。工具不可用或命中已知盲区时按 doctrine 退化，不能把上游候选冒充自己的工具调用。

## 2. 逐 Task Pack 落地(严格 TDD)

按计划内依赖序,一个 Pack 一个 Pack 做。每个 Pack:

1. 用**已装的 `/tdd` skill**:写失败测试 → 确认它真失败 → 最小实现 → 确认它真通过。
2. **写测试前读 `references/tests.md`**:测试对标仓库测试治理文档,测公开行为、mock 只外部、权威层一次;跑通仓库 test guards / lint。
3. 转绿后 **一个 Pack 一次提交**,commit message **必须含 `Pack N.M`**(N.M = 计划里的 Pack 编号)。主线程靠这个认你做到哪个 Pack,**格式错主线程就接不上**。

## 3. 边界

- **只改 plan 的 `File / Responsibility Map` 和当前 Task Pack 明确拥有的源码、测试、规则文件**。需要碰未授权路径时停下报 `needs-context` / `needs-redirection`,不顺手扩大 ownership。
- **禁改 `docs/` 下任何文件** —— 设计 / 计划 / issue 是上游权威,主线程(Coordinator)持有,你只读不写。
- 触碰带 `AGENTS.override.md` 规则的目录,同步维护该目录的 override。
- 只做本地 Pack commit；禁止 push、`gh pr merge`、部署、创建/删除 worktree、切换到别的分支。

## 4. 卡住了

同一动作连续失败、计划与现实冲突、缺输入 → 读 `references/when-stuck.md`,按它停下报清,不盲试、不猜方向、不填默认硬上。

## 5. 收工:回结构化报告(主线程靠它验收)

所有 Pack 做完(或卡住)后,**最后消息按此结构回** —— 主线程照它逐条 verify:

- **逐 Pack**:`done` / `blocked`
- **每条 acceptance**:达成 / 未达成(怎么验的,跑了什么命令)
- **改了哪些文件**
- **跑了哪些测试 + 结果**
- **结构候选**:上游候选 / 自己实际调用的工具 / 源码亲验 locator / fallback 原因；不适用时明确写“不适用”。

**诚实报,别粉饰**;blocked 就说 blocked,别假装 done。
