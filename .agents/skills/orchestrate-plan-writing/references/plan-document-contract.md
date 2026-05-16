# Plan Document Contract

本文件用于约束 plan 文档结构和 Task Pack 内部细 task。

## 1. Header

每份 plan 必须以这些字段开头：

```markdown
# <Feature Name> Implementation Plan

**Goal:** <一句话说明本 plan 交付的用户可见或系统可验证能力>
**Source design:** <path or tracker reference>
**Source issues:** <paths or tracker references>
**Execution owner:** Orchestrate Workflow
**Plan unit:** 一级章节对应 vertical large issue；Task Pack 对应 vertical small issue；细小 task 只存在于 Task Pack 内部。
**Completion gate:** Phase 0b Plan Review -> Phase A Pack Execution -> Pack Review -> Phase B Final Intent Review。
**Architecture:** <2-3 句说明实现方向、主要合同边界和数据 / 状态流>
**Tech stack:** <实际涉及的框架、服务、测试工具、运行时>
**Quality gate:** 进入 Phase 0b 前必须通过过度设计 / 设计不足自审。
```

Execution owner 必须是 Orchestrate Workflow；不要添加额外 execution handoff。

Header 后必须写：

```markdown
## Scope Check

**Subsystems:** ...
**Should split into multiple plans:** yes / no, with reason
**This plan covers:** ...
**This plan does not cover:** ...

## Source Coverage Map

| Source intent / requirement | Large issue | Small issue / Task Pack | Acceptance evidence |
| --- | --- | --- | --- |

## File / Responsibility Map

**Create:**
- `path` — responsibility

**Modify:**
- `path` — responsibility

**Test:**
- `path` — behavior covered

**Docs / rules / registry / migration / release gate:**
- `path or gate` — why it changes
```

Scope Check 和 File / Responsibility Map 是计划边界。先确认范围和文件职责，再写 Task Pack；不要用文件清单替代 vertical issue hierarchy。

如果 `Should split into multiple plans` 是 `yes`，不要继续把多个 subsystem 塞进同一份 plan。返回 `NEEDS_ISSUES` 或 `NEEDS_CONTEXT`，让上游先拆 issue / design。

## 2. Pack Brief 模板

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

**Commit boundary:** suggested commit scope, or `N/A` when parent will batch commits
**Risk flags:** normal / high-risk / production-risk / billing / permission / migration / runtime / UI / HITL
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

## 3. 细 Task 规则

细 task 是 pack 内部执行材料，不是 Orchestrate 派发单位。

每个 task 应该让没有当前聊天上下文、但具备工程能力的 worker 也能执行：

- 优先从 public behavior 检查开始；
- 每个 step 只做一个动作：定义失败测试、运行并确认失败、实现最小合同、运行并确认通过、必要 refactor、更新文档 / 门禁；
- step 应该能形成短反馈循环；如果一个 step 需要跨多个合同面或多个目录，拆成多个 step；
- 写明运行命令和 expected result；
- 改代码或测试的 step 必须写清 behavior、关键断言、输入输出、状态变化、owner / consumer、命令和 expected result；
- 只有当 source design、prototype、ADR 或 existing contract 已固定精确 shape 时，才写代码片段；
- 代码片段一旦出现，必须完整，不写省略号、伪变量或未定义方法；
- 后续 task 引用的类型、函数、方法、字段或 fixture 必须在前文定义，或在 existing code 中已验真；
- existing path 必须已验证；新文件写 `Create`；
- 文档、`agents.overrides.md` / `AGENTS.override.md`、registry、migration、read model、release gate 更新必须和对应行为放在同一个 pack；
- 不写 `similar to previous task`、`appropriate error handling`、`write tests`、`TBD`、`TODO` 或 `later`。
- 保持 DRY / YAGNI：不为未来 hypothetical slice 预建抽象；重复出现并且影响当前多个 pack 的真实复杂度，才安排 shared module / helper。
- 写清 commit boundary，但不要要求 worker 在没有用户或 parent 指令时自行 commit。

## 4. 无 Placeholder 规则

这些内容出现在 plan 中就是 plan failure，必须保存前修掉：

- `TBD`、`TODO`、`later`、`follow up`；
- `add validation`、`handle edge cases`、`appropriate error handling`、`implement logic`；
- `write tests` 但没有说明 behavior、关键断言、fixtures、命令和 expected result；
- `similar to previous pack / step`；
- 引用未定义、未验真的 type、function、method、field、fixture、endpoint、command；
- 只写最终大套测试，不写 pack-local focused command。

## 5. 验证语言

verification 必须证明 pack 行为：

- API / contract：route test、Pydantic parse / forbid-extra test、client adapter test；
- DB / migration：migration test、repository write / read model test、downgrade 或 rollback 说明；
- JSON / registry：validator test 和 unknown-field test；
- billing / permission：service test 和用户可见 gate test；
- runtime / browser / Local Agent：focused unit test，加 log evidence 或人工检查证据；
- UI / UX：DOM assertion、screenshot、responsive viewport check 或明确 manual visual gate。

不要把最终大套测试当作 pack 的唯一验证。

## 6. 保存前一致性检查

保存前用 fresh pass 检查：

- Source Coverage Map 里的每条 intent 都能指向具体 Task Pack。
- File / Responsibility Map 里的每个路径都在至少一个 Task Pack 中出现。
- 后文引用的 type、field、fixture、command 和 path 与前文一致。
- 每个 dependency 都来自 small issue blocked-by、shared contract 或真实 path / migration / release gate 冲突。
- 每个 Task Pack 的 suggested commit boundary 与 pack scope 一致。
