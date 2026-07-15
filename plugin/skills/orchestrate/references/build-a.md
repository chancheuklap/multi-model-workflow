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
| **多步**(bug 定点修跨多文件 / A1 的单计划) | 起 execution loop 记步账,逐步走完再 handoff:`mmw loop init` → 每步 `mmw loop step add --id <N.M> --desc "<标题>"`。 |

每步严格 TDD(循环用已装 `/tdd` skill)。测试的资格线按下面权威(与 Codex 工人、终审同一份单源);仓库有测试薄层 TESTING.md 的,目录分层 / 外部接缝 / 权威源以薄层为准:

<!-- BEGIN: test-quality -->
**测试写作权威(plugin 随身携带,任何仓库生效;仓库薄层 TESTING.md 只补本仓库事实——目录分层/外部接缝清单/权威源指针/套件门控——不覆盖本节):**

- 测试名 = 一句业务行为陈述(如「激活码重放被拒绝」),不复述函数名。
- 每测试一个逻辑断言(一个行为事实,可含多行字段核对)。
- 断言对象 = 外部可观察事实:优先系统读接口,其次 HTTP 响应 / 文件产物 / 账本行 / CLI stdout;禁断言内部调用序列、私有函数、源码文本。
- mock 只在外部供应商接缝(网络 / 时钟 / 三方服务;本仓库哪些边界算外部看薄层);自家模块 / 服务之间禁 mock——桩和真实现会漂移,绿测试掩盖真断裂。
- 每个行为在拥有它的权威层测一次,禁跨层重复断言,不为凑覆盖率加脆弱测试。
- 测试数据经真实 producer 路径构造(共享 builder),禁手搓 producer 形状的第二份拷贝。
- 修 bug 的回归测试写进对应业务域文件,禁新建 fix_xxx 文件。
- 价格 / 文案 / 枚举不硬编码进断言,从权威源读取后对比(权威源指针看薄层)。
- 行为退役时测试同提交删;skip 存活超过一个迭代 = 删。
- 生产代码禁为测试留 seam(`_for_test` 类后门);可测试性靠依赖注入与返回结果式接口。
- 跑通仓库自己的 test guards / lint / 类型检查——它们绿是机器底线,但绿 ≠ 测得对。

**禁止形态(写了就是缺陷,验收/审查一律打回):**

| 禁止 | 为什么 | 替代 |
| --- | --- | --- |
| 源码文本 grep 断言(读源码/文档找字面量、私有符号子串) | 改名即误红、绕开字面量即漏判,双向失效;锁的是实现不是行为 | 调真函数/真命令断外部可观察结果;结构需要断言用 AST/结构化解析 |
| 逐字锁 UI 文案 / 文档 prose | 润色即假红;prose 不是合同 | 断语义键 / 状态枚举;文案从单源读取后比对 |
| 字段全集 / 默认值 / 枚举镜像断言 | 把合同 schema 抄成第二份,改一处要改两处 | 走正式契约类型 + producer→consumer 真链路 |
| 文档计数断言(某 .md 含 N 个词 / 清单 M 条) | 文档润色即假红 | 不断文档;事实从代码权威源读 |
| 墓碑路径清单(retired 文件逐一 not-exists / archive 逐一 exists) | 清单静默腐烂,整理即红 | 只断顶级目录该在 / 不该在;import 回流交行为测试天然报错 |
| 「测试测测试」meta-gate(断某 suite 清单含某测试文件名) | 套件成员从目录推导,登记表无存在理由 | 删 |
| per-file allowlist(硬编码生产文件路径清单做豁免 / 必备) | 与布局强耦合,条目静默失效 | 结构化遍历 + 结构化例外条件 |
| mock 自家服务 / 自家接缝打桩 | 桩与真实现漂移,绿测试掩盖真断裂 | 自家接缝走真代码,mock 只在外部供应商接缝 |

**准入问题(每个新测试进仓前必答):这个测试守的是哪个用户旅程 / 哪笔钱 / 哪份数据?坏了哪个用户当天受伤?答不出 = 没资格进仓。**
<!-- END: test-quality -->

TDD 两式:

- **bug 定点修**:先按根因报告写一条**复现失败测试**(没复现就先复现,这步等于坐实根因)→ 最小修 → 测试转绿 → 提交。
- **small-change**:写失败测试 → 最小实现 → 转绿 → 提交。
- 主线程在任务 worktree 内提交,**commit message 含 `Pack N.M`**——起了 loop 时 `record-step` hook 据此自动标 step done(没起 loop 则无需,直接提交)。一步一提交。

## A3. 收口 → handoff

改完测试全绿(起了 loop 的话 `mmw loop status` 步账走完)后:

```bash
mmw handoff --conclusion pass --produced "<分支提交范围,如 base..HEAD>"
```

→ build 产物通过,**引擎强制进 ④终审闸**(`mmw where` 会吐 `review_start` 直接起审,审过再 handoff pass 才到 closing)。修着撞出超范围问题 → `mmw spinoff` 登记,别就地扩;根因其实是系统性设计级(要重做设计 / 拆计划)→ 原地升级完整设计路 `mmw task escalate --to develop`(worktree 不重开、已查成果留着,游标回 investigate 带设计意图重查),升级前先一句话告诉用户。

## 适用面

就地 TDD 是 Claude 自写自验(无独立 checker,偏弱),适用面就是小改 / 定点修——重型落地该走 develop 的 Codex 写 + Claude 独立审。
