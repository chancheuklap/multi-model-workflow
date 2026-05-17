# Discovery Input

按输入类型执行对应章节。所有类型共享同一流程结构：定位材料 → domain alignment → 判断是否需要 upstream skill → 写 design document。

## 通用步骤

1. 读项目上下文、相关文档、相关代码和近期变更。
2. 按下方输入类型提取所需字段。
3. 每轮 domain alignment 检查（见下方）。
4. 一次只问一个会改变设计的问题；能从文档和代码确认的事实先查证。
5. 信息足够后按 `design-document-contract.md` 写 design document。

## 输入类型

### 新功能 / 系统性改造 / 模糊讨论

讨论维度：用户是谁、遇到什么问题、完成后能做什么、新增或改变什么行为、哪些对象/状态/权限/生命周期参与、成功/失败/空状态/权限不足/并发/回滚处理、范围内外、如何验证完成。

需求过大时先拆成多个 design cycle。需要方案比较时提出 2-3 个方案和推荐方案。

### Bug / wrong state / performance regression

提取字段：current behavior、desired behavior、reproduction / symptom、confirmed / rejected hypotheses、root cause、regression check、contract / UI / permission / billing impact。

- 缺 feedback loop → 先用 `diagnose` 建立反馈环。
- 只是已批准 design 下的实现偏离 → 返回 `READY_FOR_REPAIR`。
- 修复会改变正式行为、合同、UI target → 必须产出 design document。
- 暴露 bad seam / repeated repair → 使用 `improve-codebase-architecture`。
- 需要模块地图 → 使用 `zoom-out`。

### Issue / backlog / existing PRD

提取字段：source issue path、problem、solution、user stories、acceptance criteria、dependencies / blocked-by、AFK / HITL、open decisions。

- PRD 是 source material，不是独立设计生成流程。
- problem / solution / acceptance 不清 → 回到"新功能"章节继续澄清。
- ready state / blocked-by 不清 → 使用 `triage`。

### UI / UX / 截图 / 验收反馈

提取字段：feedback source / screenshot、target state、role / viewport / copy / interaction、visual / DOM verification、acceptance criteria、permission / billing implications、prototype verdict。

- 只是偏离已批准 design / mockup → 返回 `READY_FOR_REPAIR`。
- 需要 UI / state 方案比较 → 使用 `prototype`。
- 暴露 architecture friction → 使用 `improve-codebase-architecture`。
- 主观反馈必须转成可验证行为、UI state 或 verification anchor。

## Domain Alignment

全程横向检查，不是独立阶段。触发条件：

- 术语模糊、与项目 glossary 冲突、同一词多义。
- 新对象 / 新状态 / 新角色 / 新 lifecycle。
- 对象 owner / writer / reader / verifier / cleanup responsibility 不清。
- UI role / permission / billing / state transition / sync ownership / runtime boundary 不清。
- 用户说法和代码 / CONTEXT / ADR / SPEC / GUIDE 冲突。
- 后续 `to-issues` 或 `plan-writing` 会因术语或边界不清而拆错。

处理方式：

1. 先查 CONTEXT / ADR / SPEC / GUIDE / code，能确认的直接写回。
2. 不能确认 → 一次问一个问题，给推荐答案，用具体场景挑战边界。
3. 用户无法当场决定 → 写入 design document 的 Open Decisions。
4. 稳定术语和对象关系 → 写入 CONTEXT.md 或 domain docs。
5. 满足 ADR 条件（hard-to-reverse + surprising + real trade-off）→ 建议 ADR。
6. 需要深度对齐时使用 `grill-with-docs`。
