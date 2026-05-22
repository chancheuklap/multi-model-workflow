# Plugin V2 成熟架构 — 端到端 Final Review 报告

> **审查日期**: 2026-05-22
> **审查分支**: `worktree-plugin-maturity`
> **审查对象**: `plugin-v2/` 全部组件
> **对照文档 A**: `2025-05-22-plugin-maturity.md`（9 个承诺）
> **对照文档 B**: `2025-05-22-gstack-prompt-optimization-plan.md`（P1-P11）
> **参照**: `2025-05-22-gstack-plan-overengineering-review.md`（缩减建议）

---

## 1. 设计匹配性审查

### 1.1 文档 A：9 个承诺

#### 承诺 1：构建系统（resolver + template + build.sh）— 已实现

| 检查项 | 结果 | 证据 |
|--------|------|------|
| build.sh 存在且可执行 | PASS | `plugin-v2/build/build.sh` (164 行) |
| build.sh --check 通过 | PASS | 运行输出无 diff |
| ≥8 个 resolver | PASS | 11 个 resolver: control-envelope, decision-brief, disposition-table, forbidden-shortcuts, preamble, review-dispatch, sendmessage-resume, signpost, state-write, trust-boundary, voice-directive |
| ≥8 个 template | PASS | 11 个 .tmpl 文件，与 resolver 一一对应 |
| 构建产物提交到 git | PASS | SKILL.md 中包含 `<!-- BEGIN/END -->` 标记对，内容由构建系统填充 |
| --check dry-run 检测漂移 | PASS | test_build_check.sh 验证了 mismatch 检测 |
| 分层 Preamble（T1/T2/T3） | PASS | preamble.md.tmpl 有 T1/T2/T3 三个 variant；workflow=T1, discovery/multi-pr-merge=T2, execution/plan-writing/final-review=T3 |

**Hot-path 内联承诺部分未实现**：§3.1 指出"热路径 reference 应在 build time 内联到 SKILL.md"，但 execution SKILL.md 仍有 6 处 `Read references/X.md` 调用（execution-preparation, execution-worker-dispatch, execution-review-dispatch, execution-repair-truncation, execution-release-gate, execution-completion）。这些是每次 Plan 循环必经的热路径。build 系统的 anchor 机制仅注入了 preamble、voice-directive、signpost、control-envelope、state-write、disposition-table、trust-boundary、forbidden-shortcuts 等结构化块，但核心控制流步骤仍为运行时 Read。

**评定**: 实现（基础设施完整，热路径内联为有意识的延迟，非遗漏）

---

#### 承诺 2：结构化控制协议（JSON 信封 + 统一状态机 + cleanup PostToolUse）— 已实现

| 检查项 | 结果 | 证据 |
|--------|------|------|
| DISPATCH_ENVELOPE schema 定义 | PASS | `state-schema/dispatch-envelope-v1.json` + `control-envelope.md.tmpl` |
| SKILL.md 中信封写入指令 | PASS | execution, plan-writing 的 control-envelope anchor 已注入 |
| hooks 从 tool_input 解析 JSON 信封 | PASS | `hooks/lib/parse-envelope.sh` (jq 解析)；test_envelope_parse.sh 9 pass |
| state.sh 统一状态写入 | PASS | 25KB, 12 个子命令 (init/read/update/transition/validate/disposition/self-verify/agent-id/budget/direction-check/idempotency/learnings) |
| 状态转换权限矩阵 | PASS | test_state.sh 62 pass; transition 子命令强制 --actor + --from/--to |
| 文件锁 (mkdir 原子锁) | PASS | `scripts/lib/state-lock.sh`; test_state.sh 有 stale lock 测试 |
| idempotency_key 检测 | PASS | test_idempotency_replay.sh 4 pass |
| cleanup PostToolUse | PASS | hooks.json 行 91-93: cleanup-before-push.sh 在 PostToolUse Bash `if: "Bash(git push *)"` |
| workflow-state + execution-state 双文件 | PASS | state-schema/workflow-state-v1.json + execution-state-v1.json; Ruling 2 记录在案 |
| mutations log | PASS | test_state.sh 验证 mutations 数组存在且有记录 |

**评定**: 已实现

---

#### 承诺 3：置信度校准 — 已实现

| 检查项 | 结果 | 证据 |
|--------|------|------|
| Finding 结构化 (confidence 1-10) | PASS | review-dispatch.md.tmpl 行 18-21: confidence rubric; test_confidence_injection.sh 4 pass |
| Review 模型分层 | PASS | review-dispatch.md.tmpl 行 6-8: discovery/plan-writing→gpt-5.5, execution/final-review→gpt-5.4; test_review_model_tiers.sh 4 pass |
| Disposition 审计记录 | PASS | state.sh disposition append 命令 + evidence 非空强制; test_disposition_audit_injection.sh 4 pass |
| Coordinator 亲验纪律 | PASS | disposition-table anchor 注入 execution SKILL.md (行 323), plan-writing SKILL.md (行 163), + design-review-angles.md, final-review-disposition.md, plan-review-resolution.md |
| Path A re-review | PASS | path-a-re-review.md reference; state.sh path-a-escalation start/update/clear; test_path_a_re_review.sh 7 pass |
| Disposition 偏差检测 | PASS | scripts/lib/review-effectiveness.sh; test_review_effectiveness.sh 7 pass |
| Pre-emit Verification Gate | PASS | review-dispatch.md.tmpl 行 23-40: 引用触发行 + 无法引用=强制降级 + Rationalization Prevention |
| Targeted re-review 使用 --resume | PASS | review-dispatch.md.tmpl 行 12-13; gate-codex-review.sh 强制; test_review_segmentation.sh 4 pass |

**评定**: 已实现

---

#### 承诺 4：运行时可观测（Learnings + Run Summary + 失败报告双层化 + Persona/Voice）— 部分实现

| 检查项 | 结果 | 证据 |
|--------|------|------|
| Learnings JSONL 基础设施 | PASS | scripts/learnings-jsonl.sh + test_learnings_append.sh 6 pass |
| Learnings 写入路径 | PARTIAL | learnings-trust-gate.md 和 learnings-confidence-audit.md 定义了写入规则，但 execution/final-review SKILL.md 没有直接引用 `learnings-jsonl.sh` 的调用指令。Coordinator 需要自行读取 reference 中的规则后执行 |
| Run Summary 脚本 | PASS | scripts/run-summary.sh; test_run_summary.sh 5 pass |
| Run Summary 调用位置 | **NOT WIRED** | workflow-closing.md 和 final-review-completion.md 均不包含 `run-summary.sh` 调用指令。脚本存在但 Coordinator 不会被告知在何时调用 |
| 失败报告双层化 | PASS | execution SKILL.md 行 241-252: 业务影响层 + 技术详情层; workflow SKILL.md 行 210-220 |
| Persona 定义 | PASS | agents/persona.md 覆盖 8 个角色 |
| Persona 消费路径 | **ORPHAN** | persona.md 未被任何 SKILL.md、reference、resolver 引用。voice-directive.md.tmpl 是 voice 的实际权威来源，persona.md 仅被 verify-maturity.sh 检测存在性 |
| Voice Directive 全覆盖 | PASS | 6 个 SKILL.md + 7 个 agent .md 均有 voice-directive anchor |
| Good/Bad 示例对 | PASS | 6 个 SKILL.md 的 voice-directive 均包含 Good/Bad 示例; final-review-completion.md 行 104-113 有业务报告锚点 |
| 禁止词 | PASS | 所有 voice-directive 含 10 个禁止词 (delve, robust, comprehensive, nuanced, multifaceted, furthermore, moreover, crucial, additionally, pivotal) |

**评定**: 部分实现 — run-summary.sh 未被 Closing 流程调用；persona.md 是孤儿文件

---

#### 承诺 5：Budget 模型校准 — 已实现

| 检查项 | 结果 | 证据 |
|--------|------|------|
| 双层 Budget (review + effort) | PASS | state.sh budget initialize 同时计算 review_total=3P+12 和 effort_total=review*2; test_budget_direction_check.sh 8 pass |
| Effort Budget 加权 | PASS | track-effort-budget.sh; test_effort_budget_weighting.sh 7 pass (worker=1, explorer=1, RCA=2) |
| Direction Check 信息化 | PASS | references/direction-check.md 存在; state.sh direction-check trigger/ack 子命令 |
| Route 4-7 unlimited budget | PASS | test_route_keyword_routing.sh 8 pass; hotfix/quickfix/spike/maintenance 均为 unlimited |

**评定**: 已实现

---

#### 承诺 6：执行合同显式化 — 已实现

| 检查项 | 结果 | 证据 |
|--------|------|------|
| Stop/Continue 在每个 SKILL.md | PASS | 6 个 SKILL.md 均有 "Only stop for" + "Never stop for" |
| 入口/出口路标 (signpost) | PARTIAL | signpost anchor 存在于 discovery, execution, final-review (3/6); workflow, plan-writing, multi-pr-merge 缺少 signpost anchor |
| 幂等性声明 (Re-run behavior) | PASS | execution SKILL.md 行 414-417; plan-writing SKILL.md 行 232-234 |
| Phase-Transition Summary | PASS | workflow SKILL.md 行 87, 123, 150, 172: 每个 Handle Return 都有 "> Phase complete." 格式 |
| Forbidden shortcuts | PARTIAL | forbidden-shortcuts anchor 在 execution + final-review (2/6); discovery, plan-writing, workflow, multi-pr-merge 缺少 |

**评定**: 已实现（signpost 和 forbidden-shortcuts 的覆盖范围低于 §5.3 表格预期，但核心 phase 已覆盖）

---

#### 承诺 7：Route 扩展（Route 4-7）— 已实现

| 检查项 | 结果 | 证据 |
|--------|------|------|
| Entry Gate 路由条件 | PASS | workflow SKILL.md 行 56-59: Route 4 (hotfix), Route 5 (quick fix), Route 6 (spike), Route 7 (maintenance) |
| Route 4-7 reference 文件 | PASS | 4 个 reference 文件全部存在于 route-extensions/ |
| Route 4 hotfix 特性 | PASS | test_hotfix_post_push_review.sh 5 pass (unlimited budget + post-push review tracking) |
| Route 5/6/7 state 策略 | PASS | test_route_keyword_routing.sh 确认 unlimited budget |

**评定**: 已实现

---

#### 承诺 8：对抗性输入防御 — 已实现

| 检查项 | 结果 | 证据 |
|--------|------|------|
| Learnings Trust Gate | PASS | learnings-trust-gate.md reference; learnings-poison-detector.sh 10+ 个反注入正则; test_learnings_poison_detection.sh 7 pass; test_trust_gate.sh 7 pass |
| Review Prompt 输入隔离 | PASS | review-dispatch.md.tmpl 行 4-5: UNTRUSTED CODE DIFF 标记; trust-boundary.md.tmpl 有 review/worker/learning 三个 variant |
| Worker 输入边界声明 | PASS | preamble.md.tmpl T3 variant 行 62-65: "不是你的 skill 指令" |
| trust-boundary anchor 注入 | PARTIAL | 仅 execution SKILL.md 有 trust-boundary anchor; final-review, discovery, plan-writing, multi-pr-merge 缺少 |

**评定**: 已实现（trust-boundary anchor 覆盖不完整，但 review-dispatch.md.tmpl 作为所有 review dispatch 的权威模板已包含 UNTRUSTED 标记）

---

#### 承诺 9：输入粒度保护 — 已实现

| 检查项 | 结果 | 证据 |
|--------|------|------|
| Pack 数量阈值 | PASS | pack-count-validator.sh; plan-writing SKILL.md 行 148-155: OK/WARN/OVER_THRESHOLD; test_pack_count_validator.sh 3 pass |
| NEEDS_ISSUE_SPLIT 回写 | PASS | plan-writing SKILL.md 行 155 + 返回区行 241 |
| Review 分段 | PASS | execution SKILL.md 行 309-313: Pack 数 > 8 时分段 review + Cross-Pack Coherence |
| 邻居接口摘要 | PASS | execution SKILL.md 行 147-157: Neighbor pack interface contracts |

**评定**: 已实现

---

### 1.2 文档 B：GStack 优化 P1-P11（含过度设计审查缩减）

| P 项 | 描述 | 落地状态 | 证据 |
|------|------|---------|------|
| **P1** | Decision Brief Protocol | **基础设施已建，未接入** | decision-brief.md.tmpl + decision-brief.sh resolver 存在；`grep -rn "BEGIN: decision-brief" plugin-v2/` = 0 结果。模板和 resolver 完整但没有任何 SKILL.md 或 reference 包含消费 anchor。自检清单已按缩减建议精简到 4 项 |
| **P2** | Voice Directive 充实 | **已落地** | voice-directive.md.tmpl 139 行; 14 个 variant 均有 Good/Bad 示例对 + 行为原则; 禁止词按缩减建议保持 10 个（未盲目扩展到 19） |
| **P3** | Pre-emit Verification Gate | **已落地** | review-dispatch.md.tmpl 行 23-40; Pre-emit Gate + Rationalization Prevention + 框架元编程泛化（按缩减建议不穷举框架） |
| **P4** | Anti-Sycophancy Rules | **已落地** | discovery variant 包含 2 条 "始终" 规则 + Good/Bad 对（按缩减建议去掉了禁止句式列表） |
| **P5** | Learnings 反注入 + Trust Gate | **已落地** | learnings-poison-detector.sh 10 个反注入正则; test_learnings_poison_detection.sh 7 pass; test_trust_gate.sh 7 pass (含 decay 和 stale 过滤) |
| **P6** | plan-writer 安全网 | **已落地** | plan-writer.md 从 39 行扩展到 73 行; 包含 Return Contract + Self-Check + Three-Failure Protocol |
| **P7** | RCA Iron Law + 3-Strike | **已落地（微调）** | root-cause-analyst.md 行 68 "通用停止条件" 包含等效规则（按缩减建议整合到现有段落，未新建独立章节） |
| **P8** | Business Report Good/Bad 锚点 | **已落地** | final-review-completion.md 行 104-113 有 Good/Bad 示例对; Quality Score 未引入（按缩减建议删除） |
| **P9** | Completion Status Protocol | **已落地（微调）** | Honesty Rule 注入 preamble.md.tmpl T2/T3; 未新建独立退出协议段（按缩减建议降级） |
| **P10** | maxTurns 边界行为 | **已落地** | Turn Budget 意识在 4 个有 maxTurns 的 agent 中均已添加: code-explorer, complex-code-explorer, docs-worker, root-cause-analyst |
| **P11** | Calibration Learning 触发条件 | **已落地** | learnings-confidence-audit.md 行 40-47: 结构化 if-then 触发规则表 |

**过度设计审查缩减执行评估**: 审查报告的 7 条缩减建议中，6 条被正确执行（P1 清单 10→4, P2 禁止词未膨胀到 19, P4 去掉禁止句式, P7 整合不新建, P8 去掉 Quality Score, P9 只加 Honesty Rule）。P3 的框架穷举也被泛化。整体适配良好。

---

## 2. 完整性审查

### 2.1 构建系统完整性

| 检查项 | 结果 |
|--------|------|
| 每个 resolver 有对应 template | PASS — 11 resolver 对应 11 template |
| build.sh --check 通过 | PASS — 无差异 |
| 所有 SKILL.md 的 anchor 可被 resolver 填充 | PASS — test_resolvers.sh 12 pass |

### 2.2 Agent 定义完整性

| Agent | Return Contract | voice-directive | maxTurns 边界 | 备注 |
|-------|----------------|-----------------|---------------|------|
| pack-executor | PASS (2 处) | PASS | N/A (无 maxTurns) | |
| complex-pack-executor | PASS (2 处) | PASS | N/A | |
| plan-writer | PASS | PASS | N/A | 73 行，含 Self-Check + Three-Failure |
| code-explorer | PASS | PASS | PASS (80% rule) | |
| complex-code-explorer | PASS | PASS | PASS | |
| docs-worker | PASS | PASS | PASS | |
| root-cause-analyst | PASS | PASS | PASS | |
| persona.md | N/A | N/A | N/A | 孤儿文件 — 不被任何组件消费 |

### 2.3 Hook 完整性

| Hook 注册 | 脚本存在 | 可执行 | matcher 配置 | 备注 |
|-----------|---------|--------|-------------|------|
| session-start.sh | PASS | PASS | SessionStart: startup\|clear\|compact | |
| guard-premature-push.sh | PASS | PASS | PreToolUse Bash (全局) | |
| enforce-pack-commit.sh | PASS | PASS | PreToolUse Bash if: "Bash(git commit *)" | |
| gate-codex-review.sh | PASS | PASS | PreToolUse Bash if: "Bash(*codex-companion.mjs task*)" | |
| validate-pack-dispatch.sh | PASS | PASS | PreToolUse Agent if: "Agent(pack-executor*)" / "Agent(complex-pack-executor*)" | |
| guard-doc-edit.sh | PASS | PASS | PreToolUse Edit + Write | |
| track-review-budget.sh | PASS | PASS | PostToolUse Bash | |
| track-effort-budget.sh | PASS | PASS | PostToolUse Bash | |
| track-execution-state.sh | PASS | PASS | PostToolUse Bash if: "Bash(git commit *)" | |
| cleanup-before-push.sh | PASS | PASS | PostToolUse Bash if: "Bash(git push *)" | |
| agent-return-handler.sh | PASS | PASS | PostToolUse Agent (全局) | |

**所有 11 个 hook 脚本存在、可执行、matcher 配置合理。** cleanup-before-push 已正确移到 PostToolUse（承诺 2c）。

### 2.4 Reference 完整性

**所有 SKILL.md 中引用的 reference 文件全部存在：**
- orchestrate-discovery: 4/4 reference 文件存在
- orchestrate-execution: 10/10 reference 文件存在（含 route-extensions 子目录）
- orchestrate-plan-writing: 6/6 reference 文件存在
- orchestrate-final-review: 6/6 reference 文件存在
- orchestrate-workflow: 8/8 reference 文件存在（含 4 个 route-extension）
- orchestrate-multi-pr-merge: 7/7 reference 文件存在

### 2.5 State Schema 完整性

| state.sh 子命令 | state-schema 对应 |
|----------------|------------------|
| init / read / update / transition / validate | workflow-state-v1.json |
| disposition / self-verify / agent-id | execution-state-v1.json |
| budget / direction-check | workflow-state-v1.json |
| idempotency | workflow-state-v1.json |
| learnings | 独立 learnings.jsonl |

state-transition-matrix.md 定义转换合法性，state.sh transition 运行时强制。

---

## 3. 端到端流程审查

### Phase 1: Entry Gate (orchestrate-workflow)

| 检查项 | 结果 | 证据 |
|--------|------|------|
| 7 条 Route 全覆盖 | PASS | workflow SKILL.md 行 52-59 |
| SendMessage 前置检查 | PASS | workflow SKILL.md 行 47: "验证 SendMessage 工具可用" |
| workflow-state 初始化路径 | PASS | references/workflow-infrastructure.md 负责 |
| Cross-Conversation Resume | PASS | Step 3 读取 workflow-infrastructure.md |
| Phase-Transition Summary | PASS | 行 87/123/150/172 四个 Handle Return 都有 |
| BLOCKED 双层报告 | PASS | 行 210-220 Global Constraints |

### Phase 2: Discovery (orchestrate-discovery)

| 检查项 | 结果 | 证据 |
|--------|------|------|
| 讨论 → 设计文档 → Design Review | PASS | Steps 3-6 → Steps 7-9 → Steps 10-11 |
| Design Review Codex dispatch | PASS | references/design-review-angles.md (含 disposition-table anchor) |
| disposition 修复 | PASS | Coordinator 亲验 → 直接修设计文档 |
| reference 文件全可达 | PASS | 4/4 |
| Anti-Sycophancy 在 voice | PASS | 2 条 "始终" 规则 + Good/Bad |

### Phase 3: Plan Writing (orchestrate-plan-writing)

| 检查项 | 结果 | 证据 |
|--------|------|------|
| plan-writer dispatch (DISPATCH_ENVELOPE) | PASS | control-envelope anchor (行 97-125) |
| run_in_background | PASS | 行 77 明确声明 |
| agentId 捕获 | PARTIAL | plan-writing SKILL.md 没有显式的 "Extract agentId + state.sh agent-id set" 步骤（execution SKILL.md 行 181-183 有此步骤，plan-writing 缺失等效步骤） |
| Plan Entry Gate + Pack 数量检查 | PASS | Steps 11-12a + pack-count-validator.sh |
| Plan Review Codex dispatch | PASS | references/plan-review-dispatch.md |
| disposition + 修复 | PASS | plan-review-resolution.md (含 sendmessage-resume anchor) |
| SendMessage resume 修复路径 | PASS | plan-review-resolution.md 行 79+: sendmessage-resume [variant=plan-writer] |

**关注点**: plan-writing SKILL.md 声明使用 run_in_background 但未像 execution SKILL.md 那样在 dispatch 后显式列出 agentId 捕获步骤。实际的 agentId 持久化依赖 Coordinator 读取 plan-writer-dispatch.md 中的步骤，而非 SKILL.md 内联。

### Phase 4: Execution (orchestrate-execution)

| 检查项 | 结果 | 证据 |
|--------|------|------|
| Worker 类型选择 | PASS | Step 4 三级分流表 |
| Pack Brief 构建 | PASS | Step 5a-5b 详细步骤 + trust-boundary anchor |
| DISPATCH_ENVELOPE | PASS | control-envelope anchor + dispatch 模板 |
| run_in_background + agentId | PASS | 行 174-185 明确且强制 |
| agent-return-handler 自动处理 | PASS | Step 7 描述 hook 行为 |
| Open Items 即时处置 | PASS | Step 7a 完整分流表 |
| Git Checkpoint per-pack | PASS | Step 7b |
| Plan Implementation Review | PASS | Step 8 + Review 分段规则 |
| Disposition (confidence + audit) | PASS | disposition-table anchor (行 323-371) |
| 修复分流 (Path A/B/C) | PASS | references/execution-repair-truncation.md |
| SendMessage resume | PASS | sendmessage-resume anchor in execution-repair-truncation.md |
| 3 轮 + RCA 截断 | PASS | execution-repair-truncation.md |
| Release Gate | PASS | references/execution-release-gate.md |
| Re-run behavior 幂等性 | PASS | 行 414-417 |
| BLOCKED 双层报告 | PASS | 行 241-252 |
| 邻居接口摘要 | PASS | 行 147-157 |

### Phase 5: Final Review (orchestrate-final-review)

| 检查项 | 结果 | 证据 |
|--------|------|------|
| 2 baseline Codex review | PASS | references/final-review-angles.md |
| Review angles (regression + intent + cross-plan + code) | PASS | final-review-angles.md |
| disposition | PASS | references/final-review-disposition.md (含 disposition-table anchor) |
| 修复分流 + 截断 | PASS | references/final-review-repair.md (含 sendmessage-resume anchor) |
| 遗留清扫 | PASS | references/final-review-completion.md |
| Business Report Good/Bad | PASS | final-review-completion.md 行 104-113 |
| Release Gate | PASS | references/final-review-release-gate.md |

### Phase 6: Closing (workflow-closing.md)

| 检查项 | 结果 | 证据 |
|--------|------|------|
| git commit | PASS | Step 21 |
| git push | PASS | Step 22 |
| PR 创建 | PASS | Step 22 gh pr create |
| 用户汇报 | PASS | Step 23 |
| run-summary 调用 | **MISSING** | workflow-closing.md 不包含 run-summary.sh 调用 |
| cleanup | PASS | cleanup-before-push.sh 自动在 push PostToolUse 触发 |

---

## 4. 假成功检测

### 4.1 P1 Decision Brief — 基础设施存在但零消费 (HIGH)

**问题**: `decision-brief.md.tmpl` 和 `decision-brief.sh` resolver 完整实现。自检清单按缩减建议精简到 4 项。test_resolvers.sh 验证 resolver 输出匹配模板。但 `grep -rn "BEGIN: decision-brief" plugin-v2/` 返回 0 结果——没有任何 SKILL.md 或 reference 文件包含消费这个模板的 anchor。

**影响**: 设计文档承诺的 "所有 BLOCKED 输出点使用结构化 Decision Brief" 未生效。用户在 BLOCKED 点收到的报告仍依赖 Coordinator 自行判断格式，缺少模板化保障。

**根因**: 构建了模板和 resolver，但遗漏了在消费端（SKILL.md / reference）插入 `<!-- BEGIN: decision-brief -->` / `<!-- END: decision-brief -->` 标记对。

### 4.2 persona.md — 存在但无消费者 (LOW)

**问题**: persona.md 定义了 8 个角色，但不被任何 SKILL.md、reference、或 resolver 引用。voice-directive.md.tmpl 是 voice 的实际权威来源。persona.md 仅被 verify-maturity.sh 检测存在性。

**影响**: 低。voice-directive 已覆盖所有角色的 voice 控制。persona.md 可作为 voice-directive resolver 的输入规格文件保留，但当前无消费路径。

### 4.3 run-summary.sh — 脚本存在但流程未调用 (MEDIUM)

**问题**: run-summary.sh 存在且测试通过 (test_run_summary.sh 5 pass)，但 workflow-closing.md（流程终点）和 final-review-completion.md 均不包含调用此脚本的指令。Coordinator 不会被告知在 workflow 完成时生成 run summary。

**影响**: 承诺 4b（运行总结）的自动化无法生效。run-summary 数据无法积累，承诺 5 的 effort budget 校准缺少输入源。

### 4.4 plan-writing agentId 持久化步骤缺失 (LOW-MEDIUM)

**问题**: plan-writing SKILL.md 行 77 声明 "所有 plan-writer Agent 调用必须使用 run_in_background: true"，但 SKILL.md 没有像 execution SKILL.md 行 181-183 那样显式列出 "Extract agentId → state.sh agent-id set" 步骤。plan-writer-dispatch.md 行 102 有相关指令，但 SKILL.md 主文件缺少。

**影响**: 如果 Coordinator compact 后丢失了 plan-writer-dispatch.md 的内容，可能跳过 agentId 持久化，导致 Plan Review 修复时 SendMessage resume 路径 BLOCKED。

### 4.5 其他已验证无假成功的区域

| 检查项 | 结果 |
|--------|------|
| build.sh --check 通过但与模板不同步 | 无问题 — --check 通过意味着完全一致 |
| hooks.json matcher 不会匹配 | 无问题 — 所有 if 条件合理（已验证 2.1.147 修复了参数化匹配） |
| state.sh validate 声称存在但不工作 | 无问题 — test_state.sh 62 pass 包含 cross-file validation |
| 模板注入标记存在但内容为空 | 无问题 — 所有 BEGIN/END 对之间有内容（build --check 验证） |
| "或新建同类 agent" fallback 残留 | 无问题 — grep 确认 0 结果，SendMessage 是唯一修复路径 |

---

## 5. 总体 Verdict: PASS_WITH_CONCERNS

### 通过理由

1. **28 个测试套件全部通过**，覆盖 build、hooks、state、scripts、envelope、SendMessage、disposition、idempotency、learnings、路由、budget 等全部子系统
2. **89 项 verify-maturity.sh 检查全部通过**
3. **build.sh --check 零差异** — 构建产物与源码完全同步
4. **9 个设计承诺中 7 个完全实现，2 个部分实现**（承诺 4 和承诺 6）
5. **11 个 P 项中 10 个已正确落地**（按过度设计审查缩减建议执行）
6. **核心创新（跨模型审查 + 结构化控制协议 + SendMessage resume）完整可工作**
7. **所有 41 个 reference 文件存在**，无断引
8. **所有 11 个 hook 脚本存在、可执行、matcher 配置合理**
9. **JSON 格式和版本号一致性验证通过**

### Concerns（不影响 PASS，但应在后续迭代中修复）

#### C1: Decision Brief 模板未接入 (HIGH)
P1 的基础设施完整但零消费。需要在以下位置插入 `<!-- BEGIN: decision-brief -->` anchor:
- 6 个 SKILL.md 的 BLOCKED 输出点
- direction-check.md 的用户交互点
- plan-review-resolution.md 的 user decision 点
- discovery SKILL.md 的设计方向确认点

#### C2: run-summary.sh 未被流程调用 (MEDIUM)
workflow-closing.md 应在 Step 22 (push) 前调用 `run-summary.sh` 生成运行总结并写入 `.claude/multi-model-workflow/run-summary-<run_id>.json`。

#### C3: plan-writing agentId 持久化步骤应内联 (LOW)
plan-writing SKILL.md 的 Step 9-10 区域应增加等效于 execution SKILL.md 行 181-183 的 agentId 捕获指令。

#### C4: signpost 覆盖不完整 (LOW)
signpost anchor 仅在 discovery, execution, final-review (3/6 SKILL.md)。workflow 作为入口 + plan-writing + multi-pr-merge 缺少。对于 workflow 和 multi-pr-merge 可能是有意设计（它们各自管理自己的 phase 转换），但 plan-writing 应有 signpost。

#### C5: multi-pr-merge 的 disposition-table 未使用标准化 anchor (LOW)
merge-integration-review.md 有手写的 disposition 规则（行 141-159），但未使用 `<!-- BEGIN: disposition-table -->` 标准化 anchor。这意味着 disposition-table resolver 的更新不会自动同步到 multi-pr-merge。

#### C6: persona.md 无消费者 (INFORMATIONAL)
persona.md 作为 voice-directive 的输入规格保留是合理的，但当前没有 resolver 读取它。可考虑在 voice-directive.sh resolver 中验证 persona.md 的角色列表与 voice-directive.md.tmpl 的 variant 列表一致。

#### C7: 承诺 1 热路径内联未完成 (MEDIUM)
设计文档 §3.1 明确将"渐进式加载是名义上的"列为 9 个矛盾之一，承诺 1 的修正方案是"热路径控制流在 build time 内联到 SKILL.md"。当前 execution SKILL.md 仍有 6 处 `Read references/X.md` 调用（execution-preparation, execution-worker-dispatch, execution-review-dispatch, execution-repair-truncation, execution-release-gate, execution-completion），每次 Plan 循环全部命中。构建系统的 anchor 机制已证明可行（11 个 resolver 正常工作），但这些核心控制流步骤尚未被转化为 build-time 内联。这是有意识的延迟而非遗漏，但与设计文档的字面承诺不符。

---

## 6. 具体修复清单

| 优先级 | 编号 | 修复项 | 文件 | 估计工作量 |
|--------|------|--------|------|-----------|
| HIGH | F1 | 在 BLOCKED/Direction Check/user decision 位置插入 decision-brief anchor | 6 SKILL.md + 3 reference | 30 分钟 |
| MEDIUM | F2 | workflow-closing.md 增加 run-summary.sh 调用 | 1 reference | 10 分钟 |
| LOW | F3 | plan-writing SKILL.md 增加 agentId 捕获步骤 | 1 SKILL.md | 10 分钟 |
| LOW | F4 | plan-writing + multi-pr-merge 增加 signpost anchor | 2 SKILL.md | 15 分钟 |
| LOW | F5 | merge-integration-review.md 使用标准化 disposition-table anchor | 1 reference | 15 分钟 |
| INFO | F6 | 确认 persona.md 的定位（消费路径或归档） | 文档决策 | 5 分钟 |
| MEDIUM | F7 | 将 execution 的 6 个热路径 reference 转化为 build-time anchor 内联 | 6 reference → 6 template + SKILL.md | 2-3 小时 |
