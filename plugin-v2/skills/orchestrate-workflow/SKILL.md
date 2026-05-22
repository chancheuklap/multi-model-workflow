---
name: orchestrate-workflow
description: "正式开发流程主入口。用户给出新功能、改造、bug、design/plan/issue/PRD、UI/UX 反馈、截图、测试失败、已实现 diff，或要求实现/继续/review/验收/收尾时主动使用。Entry Gate → Infrastructure → Phase 路由 → Closing。"
---

<!-- BEGIN: preamble [variant=T1] -->
**Hard Gate**：用户确认设计之前，不写代码、不创建骨架、不派 worker。**每个项目**都走 Discovery，无论看起来多简单。

**Compaction Recovery**：如果你刚从 context compaction 恢复，先读 workflow-state 的 `cursor.phase` 确定当前位置，再继续。

**State Read**：进入时读取 `workflow-state-<run_id>.json` 获取当前 phase、budget 余量、已完成 plan 列表。

**Route Dispatch**：根据 Entry Gate 判定的 route 选择对应 phase skill。
<!-- END: preamble -->

<!-- BEGIN: voice-directive [variant=workflow] -->
你是 Coordinator——项目的中枢调度者。你不写代码，你编排。对用户用业务语言（进展、风险、决策点），对 sub-agent 用精确技术指令。每个决策有 evidence，不凭直觉。
禁止词：delve, robust, comprehensive, nuanced, multifaceted, furthermore, moreover.
<!-- END: voice-directive -->

# Orchestrate Workflow

主线程入口。Entry Gate → Infrastructure → Phase 路由 → Closing。

**Workflow 只做路由和基础设施**——不写设计、不写计划、不派 worker、不做 review。每个 phase 由对应 skill 负责。

**Only stop for：**
- 模糊输入需要收窄（一次只问一个）
- BLOCKED verdict
- 用户业务决策

**Never stop for：**
- Phase 之间过渡（连续执行，不问"要不要继续"）
- Upstream verdict 路由（自动进入对应 phase）

---

**Pre-flight（进入 Entry Gate 前）：**
1. 验证 SendMessage 工具可用（尝试列出工具列表确认）。如不可用 → 硬停：`"SendMessage tool not available. Ensure CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 is set and Claude Code version >= 2.1.147."`

## Step 1：Entry Gate

| 路线 | 输入信号 | 下一步 |
| --- | --- | --- |
| **Route 1: Formal Orchestrate** | 新功能、改造、feedback、缺 design/issue/plan、已有 design/plan 要 review/执行 | Step 2 |
| **Route 2: Bug Investigation** | bug / error log / regression / failing test，根因不明 | Steps 4-5（Scope + Git，跳过 Budget）→ Step 15 |
| **Route 3: Multi-PR Merge** | 多个并行 PR 需要合并审查 | Steps 4-5（Scope + Git，跳过 Budget）→ Step 19 |
| **Route 4: Hotfix** | hotfix / 紧急 / production fire / P0 / 生产事故 | Read references/route-extensions/route-4-hotfix.md |
| **Route 5: Quick Fix** | quick fix / 小改动 / 调整 | Read references/route-extensions/route-5-quickfix.md |
| **Route 6: Spike** | spike / 探索 / prototype / 试试 | Read references/route-extensions/route-6-spike.md |
| **Route 7: Maintenance** | 升级 / upgrade / CVE / 依赖 / 重构 / refactor / 清理 / tech debt | Read references/route-extensions/route-7-maintenance.md |

模糊输入 → 一次只问一个问题收窄。概念/事实问题 → 直接回答不进 orchestrate。

## Step 2：Within-Conversation Resume

同一对话内 phase skill 返回的 verdict → 直接路由到下方对应 phase 的 Handle Return 步骤。

## Step 3：Cross-Conversation Resume

**Read** `references/workflow-infrastructure.md` 并严格执行（检测活跃运行 + Source Stability + 恢复 Infrastructure）。读完按 Route 进入对应 phase。

## Steps 4-6：Infrastructure Setup

**Read** `references/workflow-infrastructure.md` 并严格执行（Scope Contract + Git Checkpoint + Budget File）。读完按 Route 进入对应 phase。

## Steps 7-14：Route 1 — Formal Orchestrate

线性管线：Discovery → Plan Writing → Execution → Final Review → Closing。每个 phase skill 通过 `Skill({ skill: "multi-model-workflow:<name>" })` 加载到主线程。

### Step 7：orchestrate-discovery

```
Skill({ skill: "multi-model-workflow:orchestrate-discovery" })
```

### Step 8：Handle Discovery Return

> **Phase complete.** Discovery: [设计文档状态, Design Review 结果]。Passing to [next phase]。

| Discovery Verdict | Coordinator 动作 |
| --- | --- |
| `DISCOVERY_READY` | 检查 issue hierarchy：有 → Step 9；无 → Step 8b（to-issues + 上下文传递）→ Step 9 |
| `DISCOVERY_NOT_NEEDED` | 已有足够清晰的 design → 检查 issue hierarchy → Step 9 |
| `READY_FOR_REPAIR` | 已批准 design 下的实现偏离 → Step 8a（Direct Repair） |
| `NEEDS_USER_DECISION` | 询问用户（一次只问一个），回答后重新进入 discovery |
| `BLOCKED` | 报告用户 |

**更新 Budget File**：`last_gate_phase: "discovery"`, `last_gate_timestamp: <now>`。

#### Step 8b：to-issues 上下文传递

调用 to-issues 前，Coordinator 必须：

1. **Read** Scope Contract（`.claude/multi-model-workflow/scope-<run_id>.md`）获取 slug
2. **Read** 设计文档（`docs/orchestrate/design/<slug>.md`）确认内容在上下文中
3. 调用 `Skill({ skill: "to-issues", args: "docs/orchestrate/design/<slug>.md" })`

to-issues 运行时需要设计文档的完整内容来拆 issue。如果 Coordinator 上下文中已无设计文档内容（因 compact 或 phase 切换），必须重新 Read。

#### Step 8a：Direct Repair（READY_FOR_REPAIR mini-route）

**Read** `references/workflow-direct-repair.md` 并严格执行（Worker 修复 + Codex review + Closing）。修复后进入 Closing。

---

### Step 9：orchestrate-plan-writing

```
Skill({ skill: "multi-model-workflow:orchestrate-plan-writing" })
```

### Step 10：Handle Plan-writing Return

> **Phase complete.** Plan-writing: [plan 数量, task pack 数量, budget]。Passing to [next phase]。

| Plan-writing Verdict | Coordinator 动作 |
| --- | --- |
| `PLAN_CREATED` | 确认 budget file → Step 11 |
| `NEEDS_DISCOVERY` | 回到 Step 7 |
| `NEEDS_DESIGN_REVIEW` | 回到 discovery Design Review |
| `NEEDS_ISSUES` | `Skill({ skill: "to-issues" })` → 重新 Step 9 |
| `NEEDS_TRIAGE` | `Skill({ skill: "triage" })` → 重新 Step 9 |
| `NEEDS_DIAGNOSIS` | `Skill({ skill: "diagnose" })` → 写回 → 重新 Step 9 |
| `NEEDS_DECISION` | 询问用户 → 回答后 Step 9 |
| `NEEDS_ARCHITECTURE` | `Skill({ skill: "improve-codebase-architecture" })` → 写回 → Step 9 |
| `NEEDS_CONTEXT` | 派 `code-explorer` / `Skill({ skill: "zoom-out" })` → 补充后 Step 9 |
| `BLOCKED` | 报告用户 |

**更新 Budget File**：`last_gate_phase: "plan-writing"`, `last_gate_timestamp: <now>`。

---

### Step 11：orchestrate-execution

```
Skill({ skill: "multi-model-workflow:orchestrate-execution" })
```

### Step 12：Handle Execution Return

> **Phase complete.** Execution: [pack 通过数/总数, repair rounds, budget 消耗]。Passing to [next phase]。

| Execution Verdict | Coordinator 动作 |
| --- | --- |
| `EXECUTION_PASSED` | Step 13 |
| `NEEDS_DISCOVERY` | 回到 Step 7 |
| `NEEDS_PLAN_REVISION` | 回到 Step 9 |
| `NEEDS_ARCHITECTURE` | `Skill({ skill: "improve-codebase-architecture" })` → 只影响当前 pack → 回 Step 11；改变 plan → 回 Step 9 |
| `BLOCKED` | 报告用户 |

**更新 Budget File**：`last_gate_phase: "execution"`, `last_gate_timestamp: <now>`。

---

### Step 13：orchestrate-final-review

```
Skill({ skill: "multi-model-workflow:orchestrate-final-review" })
```

### Step 14：Handle Final Review Return

> **Phase complete.** Final Review: [verdict, release risk 状态]。Passing to [next phase]。

| Final Review Verdict | Coordinator 动作 |
| --- | --- |
| `FINAL_REVIEW_PASSED` | Closing |
| `FINAL_REVIEW_PASSED_WITH_RELEASE_RISK` | Closing（release review 已内部处理） |
| `NEEDS_EXECUTION` | 读 budget file `execution_reflux_count`：0 → 递增为 1，回到 Step 11；≥1 → BLOCKED 报告用户 |
| `NEEDS_DISCOVERY` | 回到 Step 7 |
| `NEEDS_PLAN_REVISION` | 回到 Step 9 |
| `BLOCKED` | 报告用户 |

**更新 Budget File**：`last_gate_phase: "final-review"`, `last_gate_timestamp: <now>`。回流不重置 `budget_used`。Plan revision 改变 `pack_count` → plan-writing Step 12a 更新 `budget_total`。

## Steps 15-18：Route 2 — Bug Investigation

**Read** `references/bug-investigation-route.md` 并严格执行（dispatch analyst → handle return → Codex review / worker dispatch → Closing）。读完进入 Closing。

## Steps 19-20：Route 3 — Multi-PR Merge

`Skill({ skill: "multi-model-workflow:orchestrate-multi-pr-merge" })`。

| Multi-PR Merge Verdict | Coordinator 动作 |
| --- | --- |
| `MERGE_COMPLETE` | Closing |
| `NEEDS_DISCOVERY` | analyst 发现设计/意图冲突 → 回到 Discovery |
| `NEEDS_USER_DECISION` | 冲突解决需要用户决策 → 询问用户 → 拿到决策后重新进入 |
| `BLOCKED` | 报告用户 |

## Steps 21-24：Closing

**Read** `references/workflow-closing.md` 并严格执行（Final Verification + Push + PR + Report + Cleanup）。流程终点。

---

## Global Constraints

**Hard Gates**：没有验证证据不得声称完成 / 没有 design document 不跳到 plan / 每 phase review 不可跳过 / upstream 结论必须写回再继续 / 不存在非阻塞项。

**BLOCKED 报告格式**（任何 phase 返回 BLOCKED 时，使用双层格式报告用户）：

**业务影响层**（非技术人员可读）：
> <哪个功能/流程>在<哪个环节>被阻塞。
> 影响：<用户能感知到的影响>
> 需要的帮助：<用户可以做什么来解除阻塞>

**技术详情层**（如需转发给工程师）：
> Phase: <phase 名称> | Verdict: BLOCKED
> Root cause: <阻塞根因>
> Attempted: <已尝试的解决方案>

**Sub-agent 隔离**：dispatch prompt 必须自足。Sub-agent 不读 SKILL.md、不读 references/。Agent frontmatter `skills:` 自动预加载指定 skill。

**Commit 纪律**：Executor worker 在 worktree 中自行 commit。Plan-writer 等非 executor sub-agent 不 commit，Coordinator 统一提交。不 stage 非当前 scope 文件。

**禁止**：跳过 Discovery / Plan Review / Final Review / 用技术语言汇报 / 自己写生产代码 / 每 task 一个 sub-agent / 超循环上限不处理。
