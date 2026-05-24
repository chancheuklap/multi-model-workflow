# Plugin v3.0.0 审计报告 — Opus 4.7（Round 1）

> **审计日期**：2026-05-23
> **审计模型**：Claude Opus 4.7
> **审计范围**：plugin/ 全量端到端功能性审计
> **整体评价**：审计质量不足——过度依赖测试套件通过作为正确性证据，遗漏了多个关键运行时合约断裂

---

## 1. Hook 系统完整性

### hooks.json 注册一致性

**✅ Matcher/if 条件正确**

hooks.json 注册了 3 个事件类别下的 11 个 hook（SessionStart: 1, PreToolUse: 5, PostToolUse: 5），所有 matcher 和 `if` 条件的语法都是正确的。

**✅ Hook 间无执行顺序依赖冲突**

同一 matcher 下的多个 hook 按注册顺序执行。PreToolUse Bash 中 guard-premature-push 先于 enforce-pack-commit 先于 gate-codex-review，顺序合理。

**⚠️ session-start.sh 前置检查**

缺少 `git` 可用性检查。实际影响低（Claude Code 本身依赖 git）。

---

## 2. 状态机一致性

### ❌ state.sh validate 字段覆盖不完整

Schema 声明 19 个 required 字段，`cmd_validate` 只检查 11 个。缺失 8 个：`current_phase`, `execution_reflux_count`, `last_gate_phase`, `last_gate_timestamp`, `pending_direction_check`, `pending_post_push_reviews`, `plan_writer_agent_id`, `started_at`。

### ❌ execution-state schema 与 SKILL.md 描述不一致

execution-state schema 的 plan 层级只定义了 `packs`，但 SKILL.md 多处引用 `start_commit`、`end_commit`、`status`、`review_verdict`、`release_gate_triggered`、`current_plan_id`。

### ⚠️ `cmd_plans_add` 写入 `packs: {}` 到 workflow-state

违反 Ruling 2（pack 数据只属于 execution-state）。

### ⚠️ transition matrix 中 `session-start:*:current_phase` 不可达

session-start.sh 从不调用 `state.sh transition`。

### ✅ 转换矩阵与文档一致

### ✅ budget 子系统闭环

---

## 3. 构建系统

### ✅ Resolver 和 Template 完全配对（11 对 11）
### ✅ build.sh --check 通过
### ⚠️ decision-brief 无消费锚点
### ✅ 所有 variant 引用都存在于 template 中

---

## 4. Skill 和 Agent 的衔接

### ✅ orchestrate-workflow 路由覆盖完整（7 条路由）
### ✅ DISPATCH_ENVELOPE 协议一致

### ❌ SKILL.md 声称 `validate-pack-dispatch.sh` 检查 `start_commit`，实际不检查

### ❌ SKILL.md 声称 `track-execution-state.sh` 写入 `plans[N].end_commit`，实际不写

---

## 5. 安全和防御机制

### ❌ guard-doc-edit.sh 误阻断非 workflow 场景

无活跃 workflow 时用户编辑 `docs/` 会被错误阻断。

### ✅ guard-premature-push.sh 逻辑正确
### ✅ learnings-poison-detector.sh 7 种检测有效
### ✅ gate-codex-review.sh 校验完备

---

## 6. 测试覆盖

### ✅ 28 个测试套件全部通过（297 断言）
### ⚠️ verify-maturity.sh 89 项中 2 项失败（R3-21 设计文档引用）

### ⚠️ 缺少测试覆盖的关键路径

- cleanup-before-push.sh 推送失败行为
- guard-doc-edit.sh 非 workflow 场景
- track-effort-budget.sh 的实际触发路径
- review-effectiveness.sh 边界条件

---

## 7. 边界条件和失败模式

### ❌ cleanup-before-push.sh 在推送失败时删除全部状态

不检查 push 退出码。

### ❌ track-effort-budget.sh 是死代码

注册在 PostToolUse Bash 上，但 Agent dispatch 走 Agent 工具。

### ⚠️ state-lock.sh 的并发竞态（低概率）
### ⚠️ validate-pack-dispatch.sh 的 idempotency 竞态（低风险）
### ⚠️ Worker 崩溃时无自动恢复

---

## Coordinator 批注

**本轮审计的关键遗漏**（由 Codex GPT-5.5 独立审计发现，经 Coordinator 验证确认）：

1. **C1 多行 envelope vs 单行 parser** — 模板生成多行格式，parser 只匹配单行。所有实际 dispatch 会被阻断。Opus 标为"✅ 协议一致"，实际是最严重的 bug。
2. **C3 Phase 转换矩阵缺少相邻 phase 跳转** — `discovery→plan-writing` 等不被允许。Opus 标为"✅ 矩阵与文档一致"，只做了字面对比未验证覆盖性。
3. **C4 budget 字段名分裂** — `budget_total` vs `budget.review_total`。Opus 标为"✅ budget 闭环"。
4. **C5 review budget 嵌套死锁** — `track-review-budget.sh` 持锁调 `state.sh direction-check trigger` 再获同锁。Opus 未检查。
5. **C2 gate-codex-review 的 if 条件可能不匹配** — 模板用 `$CODEX_SCRIPT` 变量，hook 匹配 `codex-companion.mjs` 字面量。Opus 标为"✅ 校验完备"。
6. **C6 内联锚点不被构建系统替换** — 2 处。Opus 标为"✅ 构建通过"。

**根因**：Opus 过度信任测试套件通过（297/297）作为正确性证据，未深入验证测试 fixture 与生产格式的差异。
