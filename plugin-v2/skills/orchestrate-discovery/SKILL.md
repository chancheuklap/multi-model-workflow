---
name: orchestrate-discovery
description: "缺少可 review 的设计文档时使用。与用户讨论 → 生成设计文档 → Design Review → to-issues 过渡。产出：reviewed design doc + issue hierarchy。"
---

<!-- BEGIN: signpost -->
**Phase 过渡标记**：

完成当前 phase 时，更新 workflow-state 的 cursor 和 status 锚：

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/state.sh" transition \
  --run-id "<run_id>" --actor Coordinator \
  --from "<current_phase>" --to "<next_phase>"
```

Phase 序列（formal route）：
`workflow` → `discovery` → `plan-writing` → `execution` → `final-review` → `execution_done` → `closed`

每个 phase skill 返回前必须通过 transition 写入下一个 phase。
Compaction 恢复时读取 `cursor.phase` 确定当前位置。

Phase complete. 返回 orchestrate-workflow 主循环。
<!-- END: signpost -->

# Orchestrate Discovery

模糊输入 → 与用户讨论 → 设计文档 + CONTEXT.md → Design Review → 过渡到 to-issues。

<!-- BEGIN: preamble -->
**Hard Gate**：用户确认设计之前，不写代码、不创建骨架、不派 worker。**每个项目**都走 Discovery，无论看起来多简单。

**Only stop for：**
- 需要用户确认设计方向
- 需要用户确认设计文档
- BLOCKED

**Never stop for：**
- 讨论中间环节（一问一答持续迭代）
- Design Review findings（Coordinator 直接修复，不问用户）
<!-- END: preamble -->

---

## 双文档产出

| 文档 | 定位 | 维护方式 |
|------|------|---------|
| **CONTEXT.md** | 项目级领域模型——术语表、对象关系、角色、状态 | 讨论中每确认一个术语就立即写入（通过 `grill-with-docs` 方法论） |
| **设计文档** | 本次功能的具体设计——目标、方案、行为、验收、合同 | 讨论充分后按模板一次成文 |

设计文档术语**必须**与 CONTEXT.md 一致。新术语先进 CONTEXT.md 再引用。不能只写设计不维护 CONTEXT.md。

CONTEXT.md 和 ADR 格式 → `references/discovery-formats.md`

---

## Step 1-2：探索项目上下文 + 判断 scope

读取 CLAUDE.md 及链入文档、SPEC / ADR / CONTEXT.md、agents.overrides.md、近期 commits。评估需求规模——过大则拆成独立子项目。

## Steps 3-6：与用户讨论

**Read** `references/discovery-discussion.md` 并严格执行（一问一答迭代 + 按输入类型澄清 + 提出方案 + 分段呈现 + Domain Alignment）。读完进入 Steps 7-9 生成设计文档。

**Anti-Pattern**：不要先写完所有设计再一次性呈现——按段确认，每段确认后再进入下一段。

## Steps 7-9：生成设计文档

**Read** `references/discovery-design-document.md` 并严格执行（模板 + 自检 + 用户确认）。读完进入 Steps 10-11 Design Review。

## Steps 10-11：Design Review

**Read** `references/design-review-angles.md`（2 个 baseline Codex reviewer：Design Content Review + Project Alignment Review）。通过后回到 Step 12 过渡到 to-issues。

Coordinator 亲验 findings → disposition → 直接修设计文档（不派 worker）→ targeted re-review。一轮 review + 修复。Pass 条件：两个 baseline 通过 + 无 Critical。

## Step 12：过渡到 to-issues

已有 issue hierarchy → 返回进入 plan-writing。缺 issue hierarchy → `Skill({ skill: "to-issues" })`。

## 外部 Skill

**全程使用**：`Skill({ skill: "grill-with-docs" })`（CONTEXT.md 维护）。**按需调用**：`Skill({ skill: "prototype" })` / `frontend-design` / `Skill({ skill: "improve-codebase-architecture" })` / `Skill({ skill: "zoom-out" })` / `Skill({ skill: "diagnose" })` / `Skill({ skill: "triage" })` / `Skill({ skill: "to-issues" })`。结论必须写回 design document 或 CONTEXT.md。

## 边界规则

没有 design document 前不进 plan-writing。已批准 design 下的实现偏离 → `READY_FOR_REPAIR`。已有清晰 design → `DISCOVERY_NOT_NEEDED`。

## 返回

```text
### Verdict
DISCOVERY_READY | DISCOVERY_NOT_NEEDED | READY_FOR_REPAIR | NEEDS_USER_DECISION | BLOCKED

### Design path
### Design Review
- Baseline 1 / Baseline 2 / Findings dispositioned / Repairs applied
### Discovery result
- Problem / Target behavior / Key decisions / Acceptance / Out of scope / Domain alignment / Remaining ambiguity
### Issue hierarchy
- Status: ready / needs to-issues / not applicable
### Next route
- plan-writing / to-issues → plan-writing / Direct Repair / user decision / blocked
```
