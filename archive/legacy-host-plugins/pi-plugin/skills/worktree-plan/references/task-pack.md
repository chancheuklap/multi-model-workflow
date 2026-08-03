# Plan · 写 Task Pack 的方法论(写每个 pack 时读这一份)

> 把每个 small issue 写成一个 Task Pack(+ TDD 步骤 + 测试规划严谨度)。一份读完,不跳别的。**谁写计划都读这份**:develop 走 plan 阶段派的写计划工人(经 `worktree-plan` skill 读它 `references/` 下的本文);small-change / bug 走 build-a 就地写单计划的主线程。返回前自检见 `plan-self-check.md`。

每个 small issue 对应一个 Task Pack。

**Task 大小判据**:一个 task = **能携带自身测试周期、值得一个 fresh reviewer 单独过一道闸**的最小单位。setup / 配置 / 脚手架 / 文档步骤折叠进它服务的 deliverable 里;只在"reviewer 可能否决这个却放行邻居"处才切开。每个 task 以一个可独立验证的 deliverable 收尾。

## Task Pack 模板

```markdown
### Task Pack N.M: <small issue title>

**Issue:** <path or reference>
**Goal behavior:** <end-to-end behavior>
**Why this matters:** <谁受益、交付什么价值——执行者要懂价值不只懂机械>
**Owned files:** Create `path` / Modify `path:line` / Test `path`

**Verified current state:**（改既有行为时填）现状真实行为 + `file:line` + 核实日期;改一族成员之一时给 landscape 审计表（组件 × 有无 × 缺口,防隧道视野）。

**read first:** <source docs, ADRs, project rules + 项目指令链实际指向的测试规则（如有）>

**Interfaces:**
- **Consumes:** <本 pack 用到的、来自前序 pack 的东西——精确签名>
- **Produces:** <后续 pack 依赖的东西——精确函数名 / 参数与返回类型>
 （落地者只看自己这个 pack,这一块是他知道邻居 pack 名称与类型的唯一途径。）

**Contract anchors:**（触碰合同时）Owner / Provider / Consumer / Model / schema / Registry / migration / catalog / Verification
**Schema / API shapes:**（涉及数据/接口时）真实 SQL / 接口 / 请求响应形状,精确到让落地者**零设计决策**。
**Mockup specs:**（mockup 目录存在时必填）涉及页面 / 视觉规格（写具体布局颜色字体间距,不写"见 mockup"）/ 交互 / 状态变体 / 验证方式
**Do Not Touch:**（refactor / audit pack 必填）哪些看着像目标但正确、不许动——防把没坏的"修"成回归。
**Root cause:**（bug pack 必填）问题为什么存在,再谈修法。

**Acceptance criteria:**（编号、pass/fail、无主观语言;✅"30 天以上订单 4 角色全返 HTTP 410" ❌"功能正常"）
- [ ] ...

**Verification commands:** `command` → Expected: ...
**Testing pyramid:**（**用项目自己声明的测试分层**,不套陌生词汇）
| 层 | 测什么 | 数量 |

**Rollback:**（触碰数据 / 基础设施 / 共享状态时）怎么撤——哪怕"revert PR"也写明。
**Complexity:** cheap（触 1-2 文件、spec 完整）/ standard（跨模块、集成）/ capable（计费 / 权限 / migration / 跨服务）——给 build 阶段选择审查 tier 与升级谨慎度用。
**Commit boundary / Risk flags / 发布风险 / AFK·HITL / Dependencies / Out of scope:** ...
```

## Implementation Tasks（每个 step 一个动作 2-5 分钟,TDD 垂直 tracer bullet）

```markdown
#### Implementation tasks
- [ ] Step 1: 定义失败的 public-behavior 测试 — 文件 / Behavior / Key assertions / Fixtures（给真实测试代码,不写"写测试"）
- [ ] Step 2: 运行确认失败 — Run: `command` → Expected: FAIL because ...
- [ ] Step 3: 实现最小合同 — 文件 / Owner / provider / consumer / Types / fields / state transitions
- [ ] Step 4: 运行确认通过 — Run: `command` → Expected: PASS
- [ ] Step 5: Refactor（只在 GREEN 状态下）
- [ ] Step 6: Suggested commit boundary
```

**细 Task 规则**:优先从 public behavior 起（Red → Green → Refactor）;每步只做一个动作、条件 / 场景写在动作前、写运行命令和 expected result。**代码放置分区**:Pack 散文区只放 schema / API 形状（消除歧义）,不撒说明性实现片段;Implementation 步骤区**必须给完整可抄代码**（零上下文执行者要照抄,不写省略号或未定义方法）。后续 task 引用的类型 / 函数 / 字段必须前文定义或 existing code 验真;existing path 验真、新文件写 `Create`;文档 / override / registry / migration 与对应行为同 pack;不写 `similar to previous task`;DRY / YAGNI 不为 hypothetical 预建抽象。

**垂直切片不水平切片**:
```
错误：RED: test1,test2,test3 → GREEN: impl1,impl2,impl3
正确：RED→GREEN: test1→impl1 → RED→GREEN: test2→impl2
```

**无 Placeholder 规则**（出现即 plan failure）:`TBD`/`TODO`/`later`;`add validation`/`handle edge cases`/`appropriate error handling`;`write tests` 无行为描述;`similar to Task N`;引用未定义/未验真的 type/function/field/fixture;描述做什么但没展示怎么做;只写大套测试无 pack-local focused command。

---

## 测试规划（plan 必须自带完整测试,不留到后续补）

写测试规划前先读当前插件的 `worktree-build/references/tests.md` 完整测试质量权威，再遵守目标仓库项目指令链实际指向的测试规则。

### 追覆盖
- **追承重行为**:每条变更后的验收行为、已复现回归和会产生独立可观察后果的风险路径都要有测试；没有独立合同的内部代码分支不为凑覆盖率单独加测试。
- **追任务相关场景**:只选择会改变用户结果、恢复能力、数据、权限或账务的交互边界、错误态和空/边界态，不为假想组合铺测试矩阵。

### 测试类型决策矩阵
- **E2E**:跨 3+ 组件的常见流 / mock 会掩盖真故障的集成点 / auth-payment-数据销毁。
- **EVAL**:LLM 调用 / prompt / 工具定义变更。
- **unit**:纯函数 / 无副作用 helper / 单函数边界。

### 测试质量评级
★★★ 测承重行为 + 任务相关边界/错误路径 / ★★ 只测 happy path / ★ 烟雾测试或存在性断言。plan 目标是 ★★★,别只写 ★。
**权威层(authoritative layer)**:每个行为在拥有它的那一层测一次,不为凑数加脆弱的实现细节测试,同一行为禁跨层重复断言——不追求"100% 覆盖"这种数字最大化（用项目自己声明的测试分层,别套陌生词汇）。

### 回归铁律（强制,无需问用户）
覆盖审计发现 diff 改了既有行为、既有测试没覆盖该路径、给既有调用方引入新失败模式 → 回归测试作为 **CRITICAL** 加进 plan,写明什么坏了。拿不准时先核实现有行为和影响，不凭猜测增加测试。

### 验证语言对照 + seam
- API/contract → route test / 合同类型 parse;DB/migration → migration / repository test + downgrade;JSON/登记 → validator / unknown-field test;billing/permission → service test / 用户可见 gate test;runtime/browser → focused unit + log evidence;UI/UX → DOM 断言 / screenshot / responsive / manual visual gate。
- seam 锚到设计期定下的 seam,选最高层、别增殖插桩点。

---

## Issue 质量标准

- **Verified Current State**:改既有行为前先写现状真实行为 + `file:line` + 核实日期。
- **Quantified impact**:数字不用形容词。"几个文件"→"47 文件跨 12 目录";"提升性能"→"500ms→50ms（10×）";没数就说"未知,用 X 法测"。
- **Landscape 审计表**（改一族成员之一时,防隧道视野）:

 | 组件 | 有 X | 有 Y | 缺口 |
 | --- | --- | --- | --- |

- **Testable AC**:编号、pass/fail、无主观语言。
 - ✅ "30 天以上订单对全部 4 个角色返回 HTTP 410" / "10K 行查询 <100ms（EXPLAIN ANALYZE）"
 - ❌ "功能正常工作" / "处理好边界"
- **Schema / API 形状**:真实 SQL / 接口 / 请求响应,不写伪代码——精确到让落地者零设计决策。

## 反模式（命中即修）

模糊验收（"正常工作"）/ 模糊文件引用（"auth 模块某处"）/ effort 无按组件拆 / 非平凡 scope 缺 Out of scope / 改动无 Verified current state / 一个 pack 混了流程反馈和战术修复 / 20+ 项无分级和执行顺序 / 引用未定义未验真的 type/fixture / 写 "similar to Task N" 不重复写出来 / **plan mandate 了评审会判为缺陷的东西（断言为空的测试、整段逻辑逐字复制粘贴）**。

**不合格 Pack 信号**:落地者要自决 desired behavior/文案/角色/billing/permission/schema shape;pack 只写"实现 mockup"或只给目录没拆视觉规格进 acceptance;把未验证路径/fixture/class 写成现有事实;把真实依赖隐藏成"可并行";只产 schema/helper 无 public behavior verification;需人工决策/真实账号/生产确认却标 AFK。
