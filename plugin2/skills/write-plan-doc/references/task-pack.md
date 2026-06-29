# Task Pack + Implementation Tasks 写法（写 pack 那一刻读全文）

每个 small issue 对应一个 Task Pack。测试 / Issue 质量 / 反模式细则见 `plan-rigor.md`。

**Task 大小判据**：一个 task = **能携带自身测试周期、值得一个 fresh reviewer 单独过一道闸**的最小单位。setup / 配置 / 脚手架 / 文档步骤折叠进它服务的 deliverable 里；只在"reviewer 可能否决这个却放行邻居"处才切开。每个 task 以一个可独立验证的 deliverable 收尾。

## Task Pack 模板

```markdown
### Task Pack N.M: <small issue title>

**Issue:** <path or reference>
**Goal behavior:** <end-to-end behavior>
**Why this matters:** <谁受益、交付什么价值——执行者要懂价值不只懂机械>
**Owned files:** Create `path` / Modify `path:line` / Test `path`

**Verified current state:**（改既有行为时填）现状真实行为 + `file:line` + 核实日期；改一族成员之一时给 landscape 审计表（见 plan-rigor.md）。

**Read first:** <source docs, ADRs, project rules>

**Interfaces:**
- **Consumes:** <本 pack 用到的、来自前序 pack 的东西——精确签名>
- **Produces:** <后续 pack 依赖的东西——精确函数名 / 参数与返回类型>
  （落地者只看自己这个 pack，这一块是他知道邻居 pack 名称与类型的唯一途径。）

**Contract anchors:**（触碰合同时）Owner / Provider / Consumer / Model / schema / Registry / migration / catalog / Verification
**Schema / API shapes:**（涉及数据/接口时）真实 SQL / 接口 / 请求响应形状，精确到让落地者**零设计决策**。
**Mockup specs:**（mockup 目录存在时必填）涉及页面 / 视觉规格（写具体布局颜色字体间距，不写"见 mockup"）/ 交互 / 状态变体 / 验证方式
**Do Not Touch:**（refactor / audit pack 必填）哪些看着像目标但正确、不许动——防把没坏的"修"成回归。
**Root cause:**（bug pack 必填）问题为什么存在，再谈修法。

**Acceptance criteria:**（编号、pass/fail、无主观语言；正反例见 plan-rigor.md）
- [ ] ...

**Verification commands:** `command` → Expected: ...
**Testing pyramid:**（**用项目自己声明的测试分层**，不套陌生词汇）
| 层 | 测什么 | 数量 |

**Rollback:**（触碰数据 / 基础设施 / 共享状态时）怎么撤——哪怕"revert PR"也写明。
**Complexity:** cheap（触 1-2 文件、spec 完整）/ standard（跨模块、集成）/ capable（计费 / 权限 / migration / 跨服务）——给派 tdd-executor 选模型与升级谨慎度用。
**Commit boundary / Risk flags / 发布风险 / AFK·HITL / Dependencies / Out of scope:** ...
```

## Implementation Tasks（每个 step 一个动作 2-5 分钟，TDD 垂直 tracer bullet）

```markdown
#### Implementation tasks
- [ ] Step 1: 定义失败的 public-behavior 测试  — 文件 / Behavior / Key assertions / Fixtures（给真实测试代码，不写"写测试"）
- [ ] Step 2: 运行确认失败  — Run: `command` → Expected: FAIL because ...
- [ ] Step 3: 实现最小合同  — 文件 / Owner / provider / consumer / Types / fields / state transitions
- [ ] Step 4: 运行确认通过  — Run: `command` → Expected: PASS
- [ ] Step 5: Refactor（只在 GREEN 状态下）
- [ ] Step 6: Suggested commit boundary
```

**细 Task 规则**：优先从 public behavior 起（Red → Green → Refactor）；每步只做一个动作、写运行命令和 expected result。**代码放置分区**：Pack 散文区只放 schema / API 形状（消除歧义），不撒说明性实现片段；Implementation 步骤区**必须给完整可抄代码**（零上下文执行者要照抄，不写省略号或未定义方法）。后续 task 引用的类型 / 函数 / 字段必须前文定义或 existing code 验真；existing path 验真、新文件写 `Create`；文档 / override / registry / migration 与对应行为同 pack；不写 `similar to previous task`；DRY / YAGNI 不为 hypothetical 预建抽象。

**垂直切片不水平切片**：
```
错误：RED: test1,test2,test3 → GREEN: impl1,impl2,impl3
正确：RED→GREEN: test1→impl1 → RED→GREEN: test2→impl2
```

**验证规划**：plan 让实现自带测试、不留后续补——追覆盖 / 决策矩阵 / 质量评级 / 回归铁律 / 验证语言对照 / seam 全在 `plan-rigor.md`，按它规划，本文件不复述。

**无 Placeholder 规则**（出现即 plan failure）：`TBD`/`TODO`/`later`；`add validation`/`handle edge cases`/`appropriate error handling`；`write tests` 无行为描述；`similar to Task N`；引用未定义/未验真的 type/function/field/fixture；描述做什么但没展示怎么做；只写大套测试无 pack-local focused command。

**不合格 Pack 信号**：落地者要自决 desired behavior/文案/角色/billing/permission/schema shape；pack 只写"实现 mockup"或只给目录没拆视觉规格进 acceptance；把未验证路径/fixture/class 写成现有事实；把真实依赖隐藏成"可并行"；只产 schema/helper 无 public behavior verification；需人工决策/真实账号/生产确认却标 AFK。完整反模式（含"别 mandate 评审会判缺陷的东西"）见 `plan-rigor.md`。
