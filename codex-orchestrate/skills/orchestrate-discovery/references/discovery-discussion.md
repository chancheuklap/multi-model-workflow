# Discovery 讨论方法论

> **流程位置**：`orchestrate-discovery` Steps 3-6 · 完成后 → Steps 7-9（`discovery-design-document.md`）

**状态锚写入**（进入时）：`state.sh update` 写 `cursor.reference = "discovery-discussion.md"`, `cursor.step = 3`。`cursor.phase` 已由 `state.sh transition` 设为 `"discovery"`。

## Step 3：澄清意图（一问一答迭代）

核心规则：

- **一次只问一个问题**。如果一个话题需要更多探索，拆成多个问题分次问。
- **每个问题给推荐答案**。用户可以直接接受、修改、或拒绝。
- **优先多选题**。比开放式问题更容易回答。
- **能从代码/文档确认的先查证**，不问用户。发现矛盾时指出来。
- **用具体场景挑战边界**，不问抽象偏好。
- **问题必须能改变设计文档、domain docs 或验收标准**。

### 澄清维度（按输入类型选择适用项）

**新功能 / 系统性改造 / 模糊讨论**：
- 用户是谁 / 用户现在遇到什么问题 / 完成后用户能做什么
- 系统需要新增或改变什么行为 / 哪些对象、状态、权限、生命周期参与
- 成功、失败、空状态、重复提交、权限不足、并发或回滚怎么处理
- 哪些属于 / 不属于本次范围 / 如何验证完成

**Bug / wrong state / performance regression**：
- current behavior、desired behavior、reproduction / symptom
- confirmed / rejected hypotheses、root cause or suspected boundary
- regression check、user-visible target behavior
- contract / UI / permission / billing impact、out of scope
- 缺 feedback loop → 先 `diagnose` skill。Discovery 只消费 diagnose 产出的事实
- 只是已批准 design 下的实现偏离 → 返回 `READY_FOR_REPAIR`
- 出现 bad seam、shallow module、caller leakage → `improve-codebase-architecture` skill
- 修复会改变正式行为 → 必须产出或修订 design document

**Issue / backlog / existing PRD**：
- source issue / PRD / backlog path or identifier
- problem、solution、user stories、acceptance criteria
- dependencies / blocked-by、AFK / HITL、open decisions、out of scope
- 已有 problem、solution、acceptance 可直接写入 design document
- source intent 不清 → `triage` skill 或继续 Discovery 提问

**UI / UX / 截图 / 验收反馈**：
- feedback source / screenshot / test / human acceptance note
- target state、role / viewport / copy / interaction
- visual or DOM verification、acceptance criteria
- 只是偏离已批准 design / mockup → 返回 `READY_FOR_REPAIR`
- 反馈暴露 source design 缺口 → 修订 design document

## Step 4：提出方案

信息足够后，提出 2-3 个不同方案，说明 trade-off。推荐方案放第一个。以对话方式呈现。YAGNI：无情地删除未被要求的功能。

设计要点：
- **设计隔离和清晰**：把系统拆成更小的单元，明确目的、定义好的接口、可独立测试。
- **深模块优先**：用 `improve-codebase-architecture` skill 理解现有模块边界。
- **在现有代码库中工作**：先探索再提方案。遵循既有模式。

## Step 5：分段呈现设计

按段呈现，每段长度与复杂度成比例。每段呈现后问用户是否正确。覆盖：架构、组件、数据流、错误处理、测试策略。

涉及视觉判断时：`prototype` skill 验证状态模型 / UI 方向，`frontend-design` skill 生成高品质前端原型。

## Step 6：Domain Alignment（全程横向检查）

贯穿整个 Discovery 过程。触发条件：术语模糊/过载/冲突 / 新对象/状态/角色 / owner 不清 / 用户说法与代码/文档冲突 / 后续会因术语不清而拆错 / ADR 三条件同时成立。

**术语挑战**：与 CONTEXT.md 冲突时立刻指出；模糊或过载时提出精确规范术语。

**双文档写回规则**：

| 内容类型 | 写回目标 | 时机 |
|---------|---------|------|
| 稳定术语、对象关系、角色、状态 | CONTEXT.md | 确认一个写一个 |
| 术语被模糊使用 | CONTEXT.md Flagged ambiguities | 发现时立即 |
| 功能行为、接口合同、验收 | 设计文档 | 讨论充分后 |
| 架构取舍满足 ADR 三条件 | docs/adr/ | 用户确认后 |

**grill-with-docs 的角色**：不是辅助工具——是 Domain Alignment 的核心执行方式。始终用其方法论挑战术语、交叉验证代码、更新 CONTEXT.md。

---
> **下一步**：讨论充分后 → Steps 7-9（discovery-design-document.md）生成设计文档。
