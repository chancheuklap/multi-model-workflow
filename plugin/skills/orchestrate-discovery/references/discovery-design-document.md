# 设计文档生成 + 自检

> **流程位置**：`orchestrate-discovery` Steps 7-9 · 完成后 → Steps 10-11（`design-review-angles.md`）

## Step 7：写 design document

信息足够且用户确认设计方向后，写入 `docs/orchestrate/design/<feature-slug>.md`（feature slug 从 Scope Contract 读取）。按以下模板写。

```markdown
# <功能 / 问题> 设计文档

## 背景和问题
从用户视角描述当前问题、触发场景和为什么需要解决。

## 目标结果
完成后用户或系统能稳定做到什么。

## 用户场景
actor / action / benefit。覆盖 happy path、失败、空状态、权限不足、重复提交、并发、回滚。
场景列表必须广泛覆盖功能的所有方面。

## 方案设计
产品行为、系统行为、数据流、UI 状态、接口形状、错误处理。

### 业务对象、角色和状态
涉及的对象、owner、writer、reader、verifier、状态、生命周期和关键关系。

### 实现决策
讨论中做出的实现决策。不写具体 file path 或 code snippet（prototype snippet 例外——例外类型仅限：state machine / reducer / schema / type shape）。

## 合同边界
涉及 API / Pydantic / DB / JSON / sync / task payload / UI action / billing / permission / runtime 时填写：
boundary type / owner / provider / consumer / Pydantic model / schema_version / registry / migration / catalog / repository / read model / verification。

## 发布风险和人工门禁
涉及 migration / billing / permission / runtime / cross-service / deploy order / rollback / manual gate 时填写。

## 测试和验收
哪些行为需要测试 / 哪些模块 / 类似测试的先例 / manual gate / visual verification / regression check。

## UI / UX 状态
mockup 目录: docs/orchestrate/mockups/<feature-slug>/
mockup 索引: docs/orchestrate/mockups/<feature-slug>/README.md

**Mockup 是可视化设计文档，与文字设计文档地位平等。** 此 section 必须把每个 mockup 拆解为可验收的行为描述：

| 页面 / 组件 | Mockup 文件 | Viewport | 视觉规格 | 交互行为 | 状态变体 | 验证方式 |
| --- | --- | --- | --- | --- | --- | --- |
| <名称> | <文件路径> | <尺寸> | <布局/颜色/字体/间距等从 mockup 提取的具体规格> | <点击/hover/输入等交互> | <空状态/加载/错误/成功等> | <截图对比/DOM 断言/视觉回归> |

不能只写"见 mockup 目录"——必须把 mockup 的视觉信息提取为文字描述，让后续 issue 和 plan 可以直接引用。

## 失败场景和异常处理

## 不在本次范围

## Open Decisions

## Review History

| Round | Verdict | Reviewer | 重点建议 | 已知 gotcha | 日期 |
| --- | --- | --- | --- | --- | --- |
| 1 | pass | codex-gpt-5.5 | <重点建议摘要> | <gotcha 列表> | 2026-05-28 |

（append-only，每轮 design review 通过后追加一行；plan-writer 读取此 section 了解审查共识，避免重复犯错）

## Cross-Plan Contract Anchors

跨 Plan 共享的合同 / 接口 / 文件所有权（**前移自独立 cross-plan-contract-map.md，统一在 design.md 内维护，单一源**）。

| Surface | 类型 (Pydantic/API/DB/migration/registry) | Owner Plan | Provider Plan | Consumer Plan(s) | 关键字段/路径 |
| --- | --- | --- | --- | --- | --- |
| ... | ... | ... | ... | ... | ... |

（plan-writer 写 Pack 时 Read 本 section 同步 Contract anchors；Coordinator 在 Plan Review / Final Review 时以本 section 为权威）

## Business Summary Inputs

每个 Plan 完成后追加一段，描述该 Plan 交付的业务能力（用户/产品语言，不写实现细节）。供 final-reviewer 起草业务汇报草稿。

### Plan 001 — <Plan title>
- 新增能力：<对用户可见的功能描述>
- 验证证据：<截图 / 测试通过 / 用户场景>
- 残余风险：<已知边界 / 后续改进>
```

**要求**：使用项目正式术语 / 不写只在聊天中才能理解的句子 / 不用 TODO/TBD / 不写 Task Pack 或 worker 指令。

## Step 8：自检

**内容完整性**：
- [ ] 无 TODO / TBD / placeholder
- [ ] 不和 CONTEXT.md / PROJECT / SPEC / ADR / 代码事实冲突
- [ ] 每个目标行为都能转成验收或测试
- [ ] 对象 / 状态 / 合同有 owner / writer / reader / verifier
- [ ] 没有混入 implementation plan / Task Pack
- [ ] 每个保留元素都有明确理由（YAGNI）

**按输入类型检查**：
- Bug：有 current / desired behavior / reproduction / regression check
- Issue：有 source / acceptance / dependencies / AFK-HITL
- Feedback：有 target state / role / copy / interaction / verification
- UI/UX：有 mockup 目录（docs/orchestrate/mockups/<slug>/）且每个 mockup 已拆解为具体视觉规格表（页面×viewport×状态×交互×验证方式），不是只写目录路径

**内部一致性**：各 section 无矛盾 / 架构与功能一致 / 无歧义需求

**合同与发布**：涉及相关边界时有 Contract anchors 和发布风险面

**Schema 完整性**：
- [ ] `## Review History` section 存在（即使首版为空表头）
- [ ] `## Cross-Plan Contract Anchors` section 存在（替代独立 cross-plan-contract-map.md 文件）
- [ ] `## Business Summary Inputs` section 存在（每 Plan 完成后由 Coordinator 追加）

## Step 9：用户确认

> "设计文档已写入 `docs/orchestrate/design/<feature-slug>.md`，请审阅。确认后进入 Design Review。"

---
> **下一步**：用户确认设计文档后 → Steps 10-11（design-review-angles.md）进入 Design Review。
