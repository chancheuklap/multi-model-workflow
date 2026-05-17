# Plan Contract

本文件定义 plan 文档结构、issue→pack 映射规则和 Task Pack 格式。

## Issue → Pack 映射

| source artifact | plan artifact |
| --- | --- |
| source design / SPEC / PRD | plan 的 source of truth 和 coverage checklist |
| 用户明确提供或 Orchestrate parent 明确确认的 vertical large issue | plan 一级章节 |
| parent large issue 文档内已记录的 vertical small issue | 一个 Task Pack |
| issue acceptance criteria | Task Pack acceptance criteria |
| issue blocked-by | Task Pack dependencies |
| issue out of scope | Task Pack out of scope |
| issue AFK / HITL | Task Pack AFK / HITL 和 risk flags |

映射不成立时（缺 large/small issue、small issue 不能独立验证）→ 返回 `NEEDS_ISSUES`。本 skill 可以写出建议拆分提示，但不能把建议拆分直接当成正式 Task Pack。

只处理用户明确提供或 parent 确认的 issue。Design / SPEC 中提到的其它 issue 最多作为 read-only context，不进入 plan source、Task Pack inventory 或 coverage map。

AgentFlow 使用 GitHub Issues 时，small issue hierarchy 的第一落点是 parent large issue 文档。确认写入 parent issue 后，再由后续流程上传或同步到 GitHub Issue。不要因为要拆 small issue 就创建新的本地 issue 文档；只有用户明确要求或项目规则指定本地 issue 文件路径时，才创建 standalone issue 文档。

如果小 issue 不能独立验证，返回 `NEEDS_ISSUES`，建议用 `to-issues` 继续拆小。不要按文件类型、前后端层、schema / test / implementation 阶段、团队分工来拆。

## Plan Header

```markdown
# <Feature> Implementation Plan

**Goal:** <一句话用户可见或系统可验证能力>
**Source design:** <path or tracker reference>
**Source issues:** <paths or tracker references>
**Execution owner:** Orchestrate Workflow
**Plan unit:** 一级章节 = large issue；Task Pack = small issue；细 task 只在 pack 内部。
**Completion gate:** Phase 0b → Phase A → Pack Review → Phase B → release gate (if triggered)
**Architecture:** <2-3 句实现方向、主要合同边界和数据/状态流>
**Tech stack:** <实际涉及的框架、服务、测试工具、运行时>
**Quality gate:** 进入 Phase 0b 前必须通过过度设计 / 设计不足自审。

## Scope Check
**Subsystems:** ...
**Should split into multiple plans:** yes / no, with reason
**This plan covers:** ...
**This plan does not cover:** ...

## Source Coverage Map
| Source intent / requirement | Large issue | Small issue / Task Pack | Acceptance evidence |
| --- | --- | --- | --- |

## File / Responsibility Map
**Create:** `path` — responsibility
**Modify:** `path` — responsibility
**Test:** `path` — behavior covered
**Docs / rules / registry / migration / release gate:** `path or gate` — why it changes

## 发布风险和人工门禁
| 风险面 | Source issue / Task Pack | Risk flag | 提前 review | Phase B 证据 | Manual gate owner |
| --- | --- | --- | --- | --- | --- |
```

Execution owner 必须是 Orchestrate Workflow；不要添加额外 execution handoff。

Scope Check 和 File / Responsibility Map 是计划边界。先确认范围和文件职责，再写 Task Pack；不要用文件清单替代 vertical issue hierarchy。

Should split = yes 时不继续硬塞，返回 `NEEDS_ISSUES` 或 `NEEDS_DISCOVERY`。

## Task Pack 模板

```markdown
### Task Pack N.M: <small issue title>

**Issue:** <path or issue reference>
**Goal behavior:** <end-to-end behavior>
**Owned files / responsibilities:**
- Create: `path`
- Modify: `path`
- Test: `path`

**Read first:**
- <source docs, ADRs, project rules, mockups>

**Contract anchors:**
- Owner:
- Provider:
- Consumer:
- Model / schema:
- Registry / migration / catalog:
- Verification:

**Mockup anchors:**
- Path:
- Viewport:
- States:
- Interaction:
- Visual verification:

**Acceptance criteria:**
- [ ] ...

**Verification commands:**
- `command`
- Expected: ...

**Commit boundary:** <one atomic commit scope; adjacent packs may share it only when they are reviewed as one boundary>
**Risk flags:** normal / high-risk / production-risk / billing / permission / migration / runtime / UI / HITL
**发布风险:** <风险面 / N/A>
**AFK / HITL:** ...
**Dependencies:** ...
**Parallel safety:** ...
**Out of scope:** ...

#### Implementation tasks
- [ ] Step 1: Define the failing public-behavior test in `...`
  - Behavior:
  - Key assertions:
  - Reused or new fixtures:
- [ ] Step 2: Run `...`
  Expected: FAIL because ...
- [ ] Step 3: Implement the minimal contract in `...`
  - Owner / provider / consumer:
  - Types, fields, state transitions or API shape:
  - Compatibility / migration notes:
- [ ] Step 4: Run `...`
  Expected: PASS
- [ ] Step 5: Refactor only if GREEN remains GREEN; run `...`
- [ ] Step 6: Suggested commit boundary: `...`
```

`N/A` 只能用于确实不适用的字段，不能用来绕过上下文缺口。

## 不合格 Pack 信号

- worker 必须自行决定 desired behavior、文案、角色、视觉层级、billing meaning、permission meaning、schema shape 或 helper placement。
- pack 只写"实现 mockup"，但没有 states、viewport、interaction 和 visual verification。
- 把未验证路径、fixture、class、command、endpoint 写成现有事实。
- 把真实依赖隐藏成"可以并行"。
- 只产出 schema 或 helper，没有 owner、consumer 和 public behavior verification。
- 需要人工决策、真实账号、生产确认或人工验收，却标成 AFK。

## 细 Task 规则

细 task 是 pack 内部执行材料，不是 Orchestrate 派发单位。每个 task 让没有当前聊天上下文、但具备工程能力的 worker 也能执行：

- 优先从 public behavior 检查开始。
- 每个 step 只做一个动作：定义失败测试、运行并确认失败、实现最小合同、运行并确认通过、必要 refactor、更新文档 / 门禁。
- step 应该能形成短反馈循环；如果一个 step 需要跨多个合同面或多个目录，拆成多个 step。
- 写明运行命令和 expected result。
- 改代码或测试的 step 必须写清 behavior、关键断言、输入输出、状态变化、owner / consumer、命令和 expected result。
- 只有当 source design、prototype、ADR 或 existing contract 已固定精确 shape 时才写代码片段。
- 代码片段一旦出现，必须完整，不写省略号、伪变量或未定义方法。
- 后续 task 引用的类型、函数、方法、字段或 fixture 必须在前文定义或在 existing code 中已验真。
- existing path 必须已验证；新文件写 `Create`。
- 文档、`agents.overrides.md`、registry、migration、read model、release gate 更新必须和对应行为放在同一个 pack。
- 不写 `similar to previous task`、`appropriate error handling`、`write tests`、`TBD`、`TODO` 或 `later`。
- 保持 DRY / YAGNI：不为未来 hypothetical slice 预建抽象；重复出现并且影响当前多个 pack 的真实复杂度，才安排 shared module / helper。
- 写清 commit boundary；worker 不自行 commit，parent 在 review 通过后提交。

## 串行边界

默认同 pack 或串行：

- 同一文件或模板。
- 同一 Pydantic model、shared contract、client contract。
- 同一 DB migration tree、repository、read model。
- 同一 JSON registry 或 validator。
- billing、wallet、chargeable action。
- permission、auth、runtime、browser takeover。
- deployment、rollback、release gate。
- 同一 UI action contract 或 mockup state。

允许并行的 pack 必须能独立验证，并且不会竞争同一 contract surface。

## 无 Placeholder 规则

这些内容出现在 plan 中就是 plan failure，必须保存前修掉：

- `TBD`、`TODO`、`later`、`defer`。
- `add validation`、`handle edge cases`、`appropriate error handling`、`implement logic`。
- `write tests` 但没有说明 behavior、关键断言、fixtures、命令和 expected result。
- `similar to previous pack / step`。
- 引用未定义、未验真的 type、function、method、field、fixture、endpoint、command。
- 只写最终大套测试，不写 pack-local focused command。

## 验证语言

verification 必须证明 pack 行为：

- API / contract：route test、Pydantic parse / forbid-extra test、client adapter test。
- DB / migration：migration test、repository write / read model test、downgrade 或 rollback 说明。
- JSON / registry：validator test 和 unknown-field test。
- billing / permission：service test 和用户可见 gate test。
- runtime / browser / Local Agent：focused unit test，加 log evidence 或人工检查证据。
- UI / UX：DOM assertion、screenshot、responsive viewport check 或明确 manual visual gate。

不要把最终大套测试当作 pack 的唯一验证。

## 保存前一致性检查

保存前用 fresh pass 检查：

- Source Coverage Map 里的每条 intent 都能指向具体 Task Pack。
- File / Responsibility Map 里的每个路径都在至少一个 Task Pack 中出现。
- "发布风险和人工门禁"覆盖所有 production-risk / billing / permission / migration / runtime / manual gate 风险，并说明提前 review 或 Phase B final gate。
- 后文引用的 type、field、fixture、command 和 path 与前文一致。
- 每个 dependency 都来自 small issue blocked-by、shared contract 或真实 path / migration / release gate 冲突。
- 每个 Task Pack 的 suggested commit boundary 与 pack scope 一致。

## 上游 Route Payload

需要交回 `to-issues` 时，返回这组信息给 Orchestrate：

```text
Upstream route: to-issues
Source design:
Parent large issue:
Issue recording target:
Why current issue boundary is insufficient:
Suggested vertical slices:
  1. Title:
     Type: AFK / HITL
     Blocked by:
     User stories / acceptance:
这些 slices 只是建议；必须等 to-issues 运行并写回 parent large issue 文档后，才能成为正式 issue / Task Pack。
```
