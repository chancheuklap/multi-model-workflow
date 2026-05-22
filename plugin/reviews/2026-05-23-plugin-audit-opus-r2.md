# Plugin v3.0.0 审计报告 — Opus 4.6（Round 2）

> **审计日期**：2026-05-23
> **审计模型**：Claude Opus 4.6
> **审计范围**：plugin/ 针对 Codex R1 发现的 6 个问题独立验证 + 补充审计 + 新发现
> **第一轮根因**：过度信任测试套件通过（297/297），未比对测试 fixture 与生产格式差异

---

## C1：多行 envelope vs 单行 parser — CONFIRMED（Severity: P0 阻断）

**生产格式**（`control-envelope.md.tmpl:6-21`，`orchestrate-execution/SKILL.md:255-270`，`orchestrate-plan-writing/SKILL.md:152-167`）：
```
<!-- DISPATCH_ENVELOPE
{ "protocol_version": "1", ... }
-->
```
三行格式：开始标记、JSON、结束标记分别在不同行。

**Parser**（`parse-envelope.sh:14`）：
```bash
sed -n 's/.*<!-- DISPATCH_ENVELOPE \(.*\) -->.*/\1/p'
```
要求 `<!-- DISPATCH_ENVELOPE`、JSON、`-->` 在同一行。多行格式无法匹配。

**测试 fixture**（`test_envelope_parse.sh:16`）：
```
'<!-- DISPATCH_ENVELOPE {"protocol_version":"1",...} -->'
```
单行格式——与模板不一致，掩盖了 bug。

**影响范围**：`validate-pack-dispatch.sh:15` 同样调用 `parse-envelope.sh`。所有 Agent dispatch（pack-executor、complex-pack-executor）和所有 Codex review dispatch 在运行时都会被阻断。这是全系统最严重的 bug。

---

## C2：gate-codex-review 的 if 条件不匹配 — CONFIRMED（Severity: P1）

**hooks.json:31** matcher：`Bash(*codex-companion.mjs task*)`
**review-dispatch.md.tmpl:11** 实际命令：`node "$CODEX_SCRIPT" task --background --prompt-file ...`

Coordinator 按模板先执行 `CODEX_SCRIPT="$(find ... codex-companion.mjs ...)"` 赋值变量，再执行 `node "$CODEX_SCRIPT" task`。Claude Code hook matcher 看到的是 LLM 发出的原始命令文本（shell 展开前），即 `node "$CODEX_SCRIPT" task ...`。该字符串不包含 `codex-companion.mjs` 子串，matcher 不会触发。

**双重失效**：即使 matcher 意外触发，`gate-codex-review.sh:12` 内部二次检查 `grep -qE 'codex-companion.*task'` 同样因命令文本中只有 `$CODEX_SCRIPT` 变量名而失败。修复需要同时改 hooks.json:31 的 matcher 和 gate-codex-review.sh:12 的 grep。

**参考修复**：`track-review-budget.sh:10` 的 grep `(codex-companion|CODEX_SCRIPT)` 已正确覆盖两种形式——应将此模式复制到 matcher 和 gate 脚本。

**影响**：review dispatch 绕过 envelope 验证门控。C1 修复后（envelope 解析正常），缺少 gate 校验意味着 targeted-re-review 等受限操作可能在不满足条件时通过。

---

## C3：Phase 转换矩阵缺少相邻 phase 跳转 — CONFIRMED（Severity: P0 阻断）

**转换矩阵**（`state.sh:72-91`）只允许 `Coordinator:workflow:<phase>` 跳转。不包含：
- `discovery` → `plan-writing`
- `plan-writing` → `execution`
- `execution` → `final-review`

**SKILL.md 指令**（`orchestrate-plan-writing/SKILL.md:12-14`，`orchestrate-execution/SKILL.md:12-14`）明确告诉 Coordinator：
```bash
state.sh transition --actor Coordinator --from "<current_phase>" --to "<next_phase>"
```
Phase 序列：`workflow → discovery → plan-writing → execution → final-review → execution_done → closed`（SKILL.md:18）。

**运行时场景**：discovery 完成后 `cursor.phase = "discovery"`。Coordinator 调用 `transition --from discovery --to plan-writing` → `transition_allowed("Coordinator", "discovery", "plan-writing")` → 矩阵中无匹配 → 被拒。

**附加问题**：`session-start:*:current_phase`（state.sh:90）中 `current_phase` 不是一个 phase 名称，而是字段名。此条目语义不清，且 `session-start.sh` 从未调用 `state.sh transition`，为不可达死代码。

---

## C4：budget 字段名分裂 — CONFIRMED（Severity: P1）

三层不一致：

| 来源 | 字段名 | 类型 |
|------|--------|------|
| `plan-gates.md:45` | `budget_total` | 字符串 `"3P + 12"` |
| `state.sh:705-710` budget initialize | `budget.review_total` / `budget.effort_total` | 整数 |
| `execution/SKILL.md:120` 前置检查 | `budget_total > 0` | 预期整数 |

**plan-gates.md:37-47** 展示的 JSON 格式用顶层 `budget_total` 字符串。`state.sh budget initialize` 写入 `budget.review_total`（整数）。

**调用链断裂**：plan-writing SKILL.md:192 指示 Coordinator "Read references/plan-gates.md"执行 budget 赋值。plan-gates.md 展示了一个 JSON 格式但不包含 `state.sh budget initialize` 调用指令。`workflow-infrastructure.md:135` 有正确的 CLI 调用，但 Coordinator 在 Step 12a 走的是 plan-gates.md 路径。Coordinator 是否会用 plan-gates.md 的 JSON 格式直接写文件、还是调用 state.sh CLI，取决于 LLM 推理——合约不明确。

**最坏情况**：Coordinator 按 plan-gates.md 的 JSON 写入顶层 `budget_total: "3P + 12"`（字符串公式），`execution/SKILL.md:120` 检查 `budget_total > 0` 失败（字符串非数字）。

---

## C5：track-review-budget.sh 嵌套死锁 — CONFIRMED（Severity: P1）

**锁获取链**：
1. `track-review-budget.sh:27` → `state_lock_acquire("${BUDGET_DIR}/${RUN_ID}.lock")`
2. 持锁状态下 `track-review-budget.sh:43` → `state.sh direction-check trigger`
3. `state.sh cmd_dc_trigger:767` → `acquire_lock()` → `state_lock_acquire("${STATE_BASE}/${RUN_ID}.lock")`

`STATE_BASE` = `BUDGET_DIR` = `.claude/multi-model-workflow`，`RUN_ID` 相同 → 锁路径相同。

**state-lock.sh:12** 使用 `mkdir` 互斥锁，不可重入（子进程 PID 不同）。50 次重试（state-lock.sh:25-28）后返回 exit 2。

**`|| true` 吞掉错误**（track-review-budget.sh:44）→ Direction Check 静默不触发。用户在 budget 达到 80% 时不会收到 Direction Check 提示，可能在不知情的情况下耗尽预算。

---

## C6：内联锚点不被构建系统替换 — CONFIRMED（Severity: P2）

**build.sh:110-111** 的替换逻辑：
```python
stripped = line.strip()
if stripped == begin_marker:
```
要求 `stripped` 精确等于 `<!-- BEGIN: review-dispatch -->`。

**两处内联锚点**：
- `execution-release-gate.md:13`：`**触发时**，<!-- BEGIN: review-dispatch -->`
  - stripped = `**触发时**，<!-- BEGIN: review-dispatch -->` ≠ `<!-- BEGIN: review-dispatch -->`
- `bug-investigation-route.md:78`：`Analyst 已修复代码。<!-- BEGIN: review-dispatch -->`
  - stripped = `Analyst 已修复代码。<!-- BEGIN: review-dispatch -->` ≠ `<!-- BEGIN: review-dispatch -->`

**无其他内联锚点**：全量 grep 确认其余所有 `<!-- BEGIN:` 标记均独占一行。

**影响**：这两个文件中 `review-dispatch` 模板内容不会被 build.sh 替换。但当前两处锚点之间的内容（`review-dispatch.md.tmpl` 的展开结果）已经手动写入了正确内容——意味着 `build.sh --check` 在这两个文件上实际是跳过了锚点检查。后续模板更新时这两处不会自动同步。

---

## 补充验证：第一轮 ✅ 项目

### "gate-codex-review.sh 校验完备" — DOWNGRADE to WARNING

`gate-codex-review.sh` 内部逻辑（review_intent 分支：baseline/path-a-re-review/targeted-re-review/default）本身是正确的。但其前提——hook 能被触发——因 C2 不成立。校验逻辑完备但无法到达。

### "DISPATCH_ENVELOPE 协议一致" — DOWNGRADE to FAIL

字段级交叉对比：
- **模板**（control-envelope.md.tmpl）：12 个字段
- **Parser**（parse-envelope.sh:26）：检查 6 个必填字段（`protocol_version, run_id, phase, agent_role, repair_round, idempotency_key`）
- **Schema**（dispatch-envelope-v1.json）：定义 `protocol_version` 枚举值 `"1"`、phase 枚举 4 个值

Parser 不验证枚举值（只检查存在性）。Schema 的 phase 枚举不含 `multi-pr-merge`（但 SKILL.md 声明了 multi-pr-merge 阶段）。格式层面因 C1 完全断裂。

### "budget 子系统闭环" — DOWNGRADE to FAIL

完整链路审计：
1. **初始化**：`state.sh init` 写 `budget_status: "pending_plan_count"`, `review_total: null` ✓
2. **赋值**：`state.sh budget initialize --plan-count N` → 计算 `3*N+12` 写入 `budget.review_total` ✓（但 plan-gates.md 的指令格式与 CLI 不一致，见 C4）
3. **递增**：`track-review-budget.sh:30` → `jq '.budget.review_used += 1'` ✓
4. **检查**：`track-review-budget.sh:37` → 比较 `review_used >= review_total` ✓
5. **Direction Check**：`track-review-budget.sh:43` → `state.sh direction-check trigger` ✗（因 C5 死锁）

链路在第 5 步断裂。

---

## 新发现（第一轮和 Codex 均未报告）

### N1：validate-pack-dispatch.sh 也受 C1 影响（P0）

`validate-pack-dispatch.sh:15` 调用 `parse-envelope.sh` 解析 Agent tool 的 prompt。Agent dispatch 的 envelope 同样是多行格式（来自 SKILL.md 模板）。这意味着 C1 不仅阻断 review dispatch，还阻断所有 pack-executor 和 complex-pack-executor dispatch。**没有任何 Agent dispatch 能通过 hook 校验。**

### N2：plan-gates.md 与 state.sh budget initialize 调用链不闭合（P2）

`plan-gates.md:37-47` 展示的 budget 赋值格式是 JSON 字面量 `"budget_total": "3P + 12"`。`workflow-infrastructure.md:135` 有正确的 CLI 调用 `state.sh budget initialize --plan-count <N>`。但 plan-writing SKILL.md:192 指引 Coordinator 在 Step 12a "Read references/plan-gates.md" 执行赋值——该文件不包含 CLI 调用指令。两个文档的赋值方式矛盾，Coordinator 行为不可预测。

### N3：enforce-pack-commit.sh 不检查 `git commit -F` 方式（P3）

`enforce-pack-commit.sh:16-18` 只用 sed 提取 `-m "..."` 或 `-m '...'` 中的 commit message。`git commit -F <file>` 方式传入的 message 不被检验（变量 `COMMIT_MSG` 为空 → 第 21 行直接 exit 0 跳过）。hooks.json 的 `if: "Bash(git commit *)"` 能匹配 `git commit -F`，但 hook 脚本内部跳过了验证。影响较低（Worker 不太可能自发使用 -F 方式）。

---

## 整体评估

| 等级 | 数量 | 发现 |
|------|------|------|
| P0 阻断 | 2 | C1（含 N1 放大）、C3 |
| P1 严重 | 3 | C2、C4、C5 |
| P2 中等 | 3 | C6、N2、N3 |

**结论**：Plugin 设计架构完整，组件覆盖面广。但 P0 级问题（C1+N1、C3）意味着在当前代码下，**没有任何 Agent dispatch 和没有任何 phase 转换能成功执行**。整个 orchestrate 流程在运行时会在第一次 dispatch 或第一次 phase 推进时完全阻塞。修复优先级：C1 → C3 → C5 → C4 → C2 → C6。测试套件需要增加多行 envelope fixture 和完整 phase 转换序列用例。
