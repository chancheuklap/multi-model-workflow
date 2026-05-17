# Plan Contract

本文件定义 plan 文档结构、issue→pack 映射规则和 Task Pack 格式。

## Issue → Pack 映射

| source artifact | plan artifact |
| --- | --- |
| source design / SPEC / PRD | plan 的 source of truth |
| vertical large issue | plan 一级章节 |
| vertical small issue | 一个 Task Pack |
| issue acceptance criteria | Task Pack acceptance criteria |
| issue blocked-by | Task Pack dependencies |
| issue out of scope | Task Pack out of scope |

映射不成立时（缺 large/small issue、small issue 不能独立验证）→ 返回 `NEEDS_ISSUES`。

只处理用户明确提供或 parent 确认的 issue。Design / SPEC 中提到的其它 issue 最多作为 read-only context。

## Plan Header

```markdown
# <Feature> Implementation Plan

**Goal:** <一句话用户可见或系统可验证能力>
**Source design:** <path>
**Source issues:** <paths>
**Execution owner:** Orchestrate Workflow
**Plan unit:** 一级章节 = large issue；Task Pack = small issue；细 task 只在 pack 内部。
**Completion gate:** Phase 0b → Phase A → Pack Review → Phase B → release gate (if triggered)
**Architecture:** <2-3 句实现方向和主要合同边界>
**Tech stack:** <实际涉及的框架、服务、测试工具>

## Scope Check
**Subsystems:** ...
**Should split:** yes/no + reason
**Covers:** ...
**Does not cover:** ...

## Source Coverage Map
| Source intent | Large issue | Task Pack | Acceptance evidence |
| --- | --- | --- | --- |

## File / Responsibility Map
**Create:** `path` — responsibility
**Modify:** `path` — responsibility
**Test:** `path` — behavior
**Docs / registry / migration / gate:** `path` — why

## 发布风险和人工门禁
| 风险面 | Task Pack | Risk flag | 提前 review | Phase B 证据 | Manual gate owner |
| --- | --- | --- | --- | --- | --- |
```

Should split = yes 时不继续硬塞，返回 `NEEDS_ISSUES` 或 `NEEDS_DISCOVERY`。

## Task Pack 模板

```markdown
### Task Pack N.M: <small issue title>

**Issue:** <path or reference>
**Goal behavior:** <end-to-end behavior>
**Owned files:** Create: ... / Modify: ... / Test: ...
**Read first:** <source docs, ADRs, mockups>
**Contract anchors:** owner / provider / consumer / model / schema_version / registry / migration / verification
**Mockup anchors:** path / viewport / states / interaction / visual verification
**Acceptance criteria:** - [ ] ...
**Verification:** `command` → expected result
**Commit boundary:** <scope>
**Risk flags:** normal / high-risk / production-risk / billing / permission / migration / runtime / HITL
**发布风险:** <风险面 / N/A>
**AFK / HITL:** ...
**Dependencies:** ...
**Parallel safety:** ...
**Out of scope:** ...

#### Implementation tasks
- [ ] Step 1: Define failing public-behavior test in `...`
  - Behavior / assertions / fixtures
- [ ] Step 2: Run `...` → Expected: FAIL because ...
- [ ] Step 3: Implement minimal contract in `...`
  - Owner / provider / consumer / types / state transitions
- [ ] Step 4: Run `...` → Expected: PASS
- [ ] Step 5: Refactor only if GREEN stays GREEN
- [ ] Step 6: Commit boundary: `...`
```

## Pack 规则

**必须**：
- Vertical slice，完成后能 demo 或独立验证。
- 每个细 task 让没有聊天上下文的 worker 也能执行。
- 改代码的 step 写清 behavior / assertions / command / expected result。
- existing path 已验真；新文件标 `Create`。
- 后文引用的 type / field / fixture / command 前文已定义或已验真。
- 文档 / agents.overrides.md / registry / migration / release gate 更新和行为放同一 pack。

**串行边界**（默认同 pack 或串行）：
- 同一文件 / shared contract / Pydantic model
- 同一 DB migration / repository / read model
- 同一 JSON registry / billing / permission / runtime / release gate

**禁止**：
- Placeholder: TBD / TODO / later / defer / similar to previous
- `write tests` / `add validation` / `handle edge cases` / `implement logic` 无具体内容
- 引用未验真的 type / function / fixture / command
- 大段生产代码（除非来自 source design / prototype / ADR / existing contract 固定的精确 shape）
- 横切 pack: all backend / all frontend / all tests / all schema
