# Build · 就地 TDD 落地(small-change / bug)

> 落地阶段 · 主线程自己写代码,**不派 Codex、不开子 worktree**(已在任务 worktree 内)。
> `prev_outputs`:small-change 无上游产物;bug 带 investigate 钉的根因报告(`docs/investigating/<slug>.md`)。
> 红线:验收吃**跑测试 / 读 diff 的 ground truth**,不吃自述;afk 只放软停,真缺输入 / 方向疑必停;push/deploy 要人批(收尾阶段;本地 merge 不拦)。

## A1. 判改动面 → 要不要先写一份单计划

| 改动面 | 怎么做 |
|---|---|
| **定点小改 / 单文件单点修** | 跳过计划,直接 A2 逐步 TDD。 |
| **跨多文件 / 多步骤** | 先写**一份单计划**理清 Task Pack:主线程读完 `${SKILL_DIR}/references/plan/task-pack.md`(Task Pack 模板 + TDD 步骤一份),落 `docs/plans/<slug>/001-<slug>.md`(**主线程自己写,不派 plan-writer、不进 ②计划审**——bug/小改无审闸),再按 Pack 逐个 TDD。 |

## A2. 逐步 TDD(用 `/tdd`)

**起不起 loop 看改动面**(spec:真小改不进 loop):

| 改动面 | loop |
|---|---|
| **真一两处的小改**(single-change) | **不起 loop**,直接 TDD 改完提交 → A3 handoff。 |
| **多步**(bug 定点修跨多文件 / A1 的单计划) | 起 execution loop 记步账,逐步走完再 handoff:`mmw loop init --kind execution` → `mmw loop attendance --mode afk` → 每步 `mmw loop step add --id <N.M> --desc "<标题>"`。 |

每步严格 TDD(**测试按仓库测试治理文档的分层 + 写作规范写**——定位 TESTING.md / AGENTS.md 测试节 / tests 规则,找不到才用通用 TDD 纪律;跑通仓库自己的 test guards / lint):

- **bug 定点修**:先按根因报告写一条**复现失败测试**(没复现就先复现,这步等于坐实根因)→ 最小修 → 测试转绿 → 提交。
- **small-change**:写失败测试 → 最小实现 → 转绿 → 提交。
- 主线程在任务 worktree 内提交,**commit message 含 `Pack N.M`**——起了 loop 时 `record-step` hook 据此自动标 step done(没起 loop 则无需,直接提交)。一步一提交。

## A3. 收口 → handoff

改完测试全绿(起了 loop 的话 `mmw loop exit-check` = DONE)后:

```bash
mmw handoff --conclusion pass --produced "<分支提交范围,如 base..HEAD>"
```

→ build 产物通过,**引擎强制进 ④终审闸**(`mmw where` 会吐 `review_start` 直接起审,审过再 handoff pass 才到 closing)。修着撞出超范围问题 → `mmw spinoff` 登记,别就地扩;根因其实是系统性设计级(要重做设计 / 拆计划)→ 原地升级完整设计路 `mmw task escalate --to develop`(worktree 不重开、已查成果留着,游标回 investigate 带设计意图重查),升级前先一句话告诉用户。

## 守住的红线

- 验收吃跑测试 / 读 diff 的 ground truth,不吃自述。就地 TDD 是 Claude 自写自验(无独立 checker,偏弱),适用面就是小改 / 定点修——重型落地该走 develop 的 Codex 写 + Claude 独立审。
- afk 只放软停;真缺输入 / 方向疑 / 合并红线必停。
