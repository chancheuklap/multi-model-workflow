# Plugin v3.0.0 审计报告 — Codex GPT-5.5（Round 1）

> **审计日期**：2026-05-23
> **审计模型**：Codex GPT-5.5 X-High
> **审计范围**：plugin/ 全量功能性审计（代码逻辑 + 数据流 + 状态一致性）
> **整体评价**：深度代码审查质量高，发现多个 Opus 遗漏的关键运行时合约断裂

---

## 1. DISPATCH_ENVELOPE 协议完整性

**Verdict: FAIL**

- **确认 Bug：Parser 只支持单行 envelope，但 Skill 模板生成多行 envelope。**
  - `plugin/hooks/lib/parse-envelope.sh:14` 使用 `sed -n 's/.*<!-- DISPATCH_ENVELOPE \(.*\) -->.*/\1/p'`，仅能提取单行。
  - 实际生成的 control envelope 是多行格式（`control-envelope.md.tmpl`、`orchestrate-plan-writing/SKILL.md:151-168`、`orchestrate-execution/SKILL.md:254-271`）。
  - **影响**：所有按模板写的 dispatch 被 hook 判定为 malformed 并阻断。

- **Schema 与 Parser 验证范围不一致。**
  - `dispatch-envelope-v1.json:5-14` 要求 `protocol_version` 值为 `"1"`，`phase` 枚举限定 4 个值。
  - `parse-envelope.sh:26-32` 仅检查字段存在性，不验证枚举值或类型。

- **Schema 排除了 `multi-pr-merge` 阶段。**
  - `dispatch-envelope-v1.json:9` 的 phase 枚举不含 `multi-pr-merge`。

- **幂等性竞争风险。**
  - `validate-pack-dispatch.sh:35-40` 在加锁前先读 idempotency key。

---

## 2. 状态机设计验证

**Verdict: FAIL**

- **PASS：`state.sh` 和 `state-transition-matrix.md` 字面转换表一致。**

- **确认 Bug：`state.sh` 不支持相邻 phase 间转换。**
  - `state.sh:81-85` 只允许从 `Coordinator:workflow` 到各 phase 的跳转。
  - 不允许 `discovery → plan-writing`、`plan-writing → execution` 等。
  - **影响**：跨会话恢复无法依赖 phase 转换做阶段推进。

- **`state.sh` 向 workflow-state 写入 schema 未定义的 `packs` 字段。**
  - `state.sh:915-917`。

- **`state.sh validate` 不读 JSON Schema，用本地字段列表。**

- **Schema 定义但 `state.sh` 从未写入的字段：**
  - `review_dispositions[].reviewer_agent_id`
  - `review_effectiveness.health_warnings`

---

## 3. 构建系统完备性

**Verdict: WARNING**

- **PASS：11 对 resolver/template 一一对应。**

- **确认 Bug：行内 BEGIN anchor 不会被替换。**
  - `build.sh:104-116` 要求行去空白后精确等于 anchor marker。
  - `execution-release-gate.md:13` 和 `bug-investigation-route.md:78` 的 anchor 嵌在行内文本中。

- **`--check` 模式静默跳过不可解析的 anchor。**

- **存在无引用的 template/variant：**
  - `decision-brief` 无 anchor 引用。
  - `voice-directive` 的 `codex-reviewer` variant 无引用。
  - `trust-boundary` 的 `review` 和 `learning` variant 无引用。

---

## 4. Hook 逻辑正确性

**Verdict: FAIL**

- **确认 Bug：Codex review gate 不匹配文档化的 dispatch 命令。**
  - `hooks.json:29-31` 拦截 `Bash(*codex-companion.mjs task*)`。
  - 模板用 `node "$CODEX_SCRIPT" task ...`，展开后路径里可能不含 `codex-companion.mjs`。
  - **影响**：按模板生成的 review dispatch 可能绕过 envelope 验证。

- **commit regex 比错误提示更宽松。**
  - `enforce-pack-commit.sh:25-26` 允许无 summary。
  - `-F` 方式传入的 commit message 不被检验。

- **`guard-doc-edit.sh` 的 Coordinator/Worker 判断不可靠。**
  - 仅凭 `active-run-id` 存在与否。无活跃 workflow 时误判为 Worker。

- **确认 Bug：`track-review-budget.sh` 嵌套锁死锁。**
  - 脚本持锁后调 `state.sh direction-check trigger`，后者也请求同一锁（不可重入）。
  - 死锁被 `|| true` 吞掉，Direction Check 静默不生效。

- **确认 Bug：effort budget 统计 Bash 文本而非 Agent 工具调用。**
  - `track-effort-budget.sh:31-46` grep Bash 命令，实际 dispatch 走 Agent 工具。

- **确认 Bug：`cleanup-before-push.sh` 不检查 push 是否成功。**

---

## 5. Skill 路由和阶段衔接

**Verdict: FAIL**

- **PASS：主入口路由表覆盖 7 种类型。**

- **Phase 交接要求的状态转换不被 `state.sh` 支持。**

- **Budget 字段名不统一：**
  - `plan-gates.md:37-47` 和 `execution/SKILL.md:118-123` 写 `budget_total`。
  - `state.sh:705-710` 初始化 `budget.review_total` 和 `budget.effort_total`。

- **Plan-writer repair 的 agentId 持久化路径断裂：**
  - `state.sh agent-id set` 需要 execution-state 文件，plan-writing 阶段不存在。

- **start_commit / end_commit 合约未实现。**

---

## 6. 测试脚本审查

**Verdict: FAIL**

- **核心失效路径缺测：**
  - `test_envelope_parse.sh` 所有测试用单行 envelope，从未测试多行格式。
  - `test_gate_codex_review.sh` 用硬编码命令，不是文档化的 `$CODEX_SCRIPT` 路径。
  - `test_effort_budget_weighting.sh` 用 Bash 命令模拟，不测真实 Agent 工具路径。
  - `test_build_check.sh` 不测行内 anchor。

- **无覆盖：** push 失败 cleanup、guard-doc-edit 误判、JSON Schema 验证、并发幂等性、完整 phase 转换序列。

---

## 7. 设计可行性判断

**Verdict: FAIL（当前实现）；修复后设计模式可行**

- 核心思路（PreToolUse 门控 + PostToolUse 跟踪 + 状态文件 + envelope 元数据）在 Claude Code Plugin 架构下原理可行。
- 并发安全仅部分覆盖：大多数写操作用了 `state-lock.sh`，但幂等性 check+append 非原子，review budget 嵌套锁必死锁。
- 当前最严重的阻断问题：多行 envelope 与单行 parser 不匹配、hook trigger 无法拦截文档化的 `$CODEX_SCRIPT` 路径、formal phase 转换不被 state.sh 支持、budget 字段名分裂、cleanup 不检查 push 成功。

---

## 整体评估摘要

Plugin 的设计思路正确，组件拼图完整，但运行时合约在多处断裂。最严重的五类阻断：(1) envelope 单行 parser 与多行模板不匹配，导致所有实际 dispatch 被拒；(2) review gate 无法拦截文档化的 `$CODEX_SCRIPT` 命令；(3) formal phase 转换矩阵与 phase 文档的流程描述不一致；(4) budget 字段名在 plan-writing 和 execution 之间不统一；(5) push 失败后 cleanup hook 仍删除状态文件。测试覆盖停留在单行 fixture 和 helper 单测层面，最关键的失败路径均无覆盖。在修复这些合约断裂之前，该 Plugin 无法可靠支撑多 agent 编排。
