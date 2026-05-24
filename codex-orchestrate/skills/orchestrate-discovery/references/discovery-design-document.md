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
讨论中做出的实现决策。不写具体 file path 或 code snippet（prototype snippet 例外）。

## 合同边界
涉及 API / Pydantic / DB / JSON / sync / task payload / UI action / billing / permission / runtime 时填写：
boundary type / owner / provider / consumer / Pydantic model / schema_version / registry / migration / catalog / repository / read model / verification。

## 发布风险和人工门禁
涉及 migration / billing / permission / runtime / cross-service / deploy order / rollback / manual gate 时填写。

## 测试和验收
哪些行为需要测试 / 哪些模块 / 类似测试的先例 / manual gate / visual verification / regression check。

## UI / UX 状态
mockup 目录: docs/orchestrate/mockups/<feature-slug>/ · 页面 / viewport / states / copy / interaction / 视觉允许偏差 / 验证方式。
mockup 索引: docs/orchestrate/mockups/<feature-slug>/README.md

## 失败场景和异常处理

## 不在本次范围

## Open Decisions
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
- UI/UX：有 mockup 目录（docs/orchestrate/mockups/<slug>/）/ viewport / states / interaction / visual verification

**内部一致性**：各 section 无矛盾 / 架构与功能一致 / 无歧义需求

**合同与发布**：涉及相关边界时有 Contract anchors 和发布风险面

## Step 9：用户确认

> "设计文档已写入 `docs/orchestrate/design/<feature-slug>.md`，请审阅。确认后进入 Design Review。"

---
> **下一步**：用户确认设计文档后 → Steps 10-11（design-review-angles.md）进入 Design Review。
