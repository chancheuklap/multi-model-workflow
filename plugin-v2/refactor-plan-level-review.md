# Refactor: Execution Review 粒度从 Pack 提升到 Plan

## 问题

当前的"设计 → 计划"阶段：

```
1 设计文档 → N 个大 Issue（垂直切片）→ N 个 Plan 文件 → 每个 Plan 内 M 个 Task Pack
```

Issue 和 Plan 是天然的"一个完整功能切片"粒度。但在执行阶段，Codex Review 却以 Pack 为粒度派发——每完成一个 Pack 就派一次 Codex Reviewer。

**粒度错配**：
- Pack 只是 Plan 内部的实施细分，单独 review 一个 Pack 看不到同 Plan 内其他 Pack 的配合关系
- 现有 Final Review 专门增加 "Cross-Pack Audit" 来补这个缝隙——恰恰说明 Pack Review 粒度不够
- 每个 Pack 都派一次 Codex Review，成本高（一个功能可能有 3 个 Plan × 4 个 Pack = 12 次 review）

## 改造目标

**Review 粒度对齐到 Plan 级别**：
- 代码落地仍以 Pack 为粒度（worker 不变）
- Codex Review 以 Plan 为粒度（同一 Plan 内所有 Pack 完成后，派发一次覆盖该 Plan 全部代码变更的 Review）

## 收益

1. **更完整的审查视野**——Reviewer 看到一个垂直切片的全貌，能发现 Pack 间的配合问题
2. **成本显著降低**——Review 次数从 Pack 数量降到 Plan 数量（通常 3-5× 减少）
3. **Final Review 瘦身**——Cross-Pack Audit 降级为 Cross-Plan Integration（Plan 内跨 Pack 已由 Plan Implementation Review 覆盖）
4. **结构更自然**——Review 粒度与"一个完整功能切片"对齐

---

## 设计决策

### 决策 1：Intra-Plan 质量保障（Pack 之间不再有 Codex Review 时，靠什么阻止"在有问题的 Pack 上继续堆积"）

**方案**：依靠 Worker 内部质量门禁 + Coordinator 检查，不在 Pack 之间插入 Codex Review。

具体保障链：
1. **Worker TDD 纪律**：每个 Pack 完成时，所有测试必须通过（Red→Green→Refactor 在 worker 内闭环）
2. **Worker 自判断**：Worker 返回 `pass` / `needs repair` / `blocked`。返回 `needs repair` 时 Coordinator 必须先解决再继续下一个 Pack
3. **Coordinator scope drift 检测**：检查 Changed files vs Owned files
4. **Open Items 即时处置**：`[out-of-scope]` / `[needs-evaluation]` / `[bug]` 在下一个 Pack 之前处置
5. **Intra-Plan Blocker 规则（新增）**：Pack N.M 返回 `needs repair` 且修复后 worker 仍报 `blocked` → 整个 Plan 停止，不继续后续 Pack

**权衡**：Worker 的 TDD + 自检 + Coordinator 检查已经是当前流程中"Pack Review 之前"就在做的事。Pack Review 额外发现的问题主要是 worker 盲区（mock 纪律、合同纪律、forbidden shortcuts）。这些问题不会因为延迟到 Plan 级别 review 而变得更难修——反而 Reviewer 有更完整的上下文来判断。

### 决策 2：命名区分

| 术语 | 所在阶段 | 审查对象 | Gate 名 |
|------|---------|---------|--------|
| **Plan Review**（已有） | Plan Writing | Plan 文档质量 | `plan-review` |
| **Plan Implementation Review**（新增） | Execution | 一个 Plan 对应的全部代码变更 | `plan-impl-review-N` |
| Final Review（已有） | Final Review | 所有 Plan 合在一起的整体实现 | `final-review-baseline-*` |

### 决策 3：Repair 归属机制

Plan Implementation Review 的 Return Contract 新增 `Affected packs` 字段：

```markdown
### Result
Plan Implementation Review 结果：
Spec compliance:
Code quality:
Contract & risk:
Critical:
  - [Pack N.M] <finding description>
Important:
  - [Pack N.M] <finding description>
Affected packs: N.1, N.3   ← 新增，Coordinator 据此路由 repair
```

Coordinator 据此路由：
- Finding 归属单个 Pack → SendMessage 给该 Pack 的原 worker（或新建同类 agent）
- Finding 涉及多个 Pack 的交互 → 按复杂度分流（Coordinator 直接修 / complex-pack-executor / code-explorer 调查）

### 决策 4：Budget 公式

**旧**：`2N + 12`（N = 总 Pack 数）
**新**：`3P + 12`（P = 总 Plan 数）

分配逻辑：
- `3P`：每个 Plan 1 次 baseline + 最多 2 次 repair re-review
- `+12` 不变：Design Review (2-4) + Plan Document Review (1) + Final Review (2) + Release Gate (≤2) + 修复余量 (3-5)

**为什么 3P 不是 2P**：Plan 级别 review 覆盖更多代码（同 Plan 内所有 Pack），findings 可能涉及多个 Pack 的交互，修复后需要更多 re-review 轮次。3P 给每个 Plan 2 次 repair 预算（与 Pack 级别的 3 轮截断一致）。

**效果对比**（以 3 个 Plan、每个 Plan 4 个 Pack 为例）：
- 旧：`2×12 + 12 = 36`
- 新：`3×3 + 12 = 21`（节省 42%）

### 决策 5：SubagentStop Hook 语义

**旧 hook 消息**（每个 worker 完成时）：
> "Coding agent completed. Next: read the review dispatch reference for this phase and follow the inline Codex review steps."

**新 hook 消息**：
> "Coding agent completed. Next: check if all packs in the current plan are done. If yes, read the review dispatch reference and dispatch Plan Implementation Review. If not, continue with the next pack in this plan."

逻辑在 Coordinator 侧，hook 只是提醒。

### 决策 6：Early Release Gate 移到 Plan 边界

**旧**：每个 Pack 通过 Pack Review 后检查该 Pack 是否触碰发布风险面。
**新**：Plan Implementation Review 通过后，检查该 Plan 中是否有任何 Pack 触碰发布风险面。

理由：Release Gate 审查需要看到完整的代码变更来判断 deploy order、rollback 安全性。Plan 级别能给出更准确的判断。

触发条件不变（migration / deploy order / rollback / manual production gate / billing / permission / runtime），只是从"per-pack after Pack Review"变为"per-plan after Plan Implementation Review"。

### 决策 7：跨 Plan 执行模型

**Plan 之间串行执行，Pack 之间可并行（与现在一致）。**

执行队列变为两级：

```
plan_queue = [Plan001, Plan002, Plan003]  ← 按 Blocked by 排序
  Plan001.pack_queue = [[1.1], [1.2, 1.3], [1.4]]  ← 内部按 Dependencies 排序
  Plan002.pack_queue = [[2.1, 2.2], [2.3]]
  Plan003.pack_queue = [[3.1], [3.2]]
```

执行流：
1. Plan001 的所有 Pack 按内部顺序执行（并行 Pack 用 worktree）
2. 所有 Pack 完成 + Git Checkpoint → 派发 `plan-impl-review-1`
3. Review 通过 → Early Release Gate（条件触发）→ 继续 Plan002
4. 重复直到所有 Plan 完成

**不做跨 Plan 并行**——复杂度增加（需要 Plan 级 worktree + 跨 Plan merge），收益有限（Plan 间通常有依赖关系）。

### 决策 8：Final Review 范围调整

**旧 Final Review 三层**：
1. Regression Sweep（全局 diff）
2. Intent Coverage（设计意图覆盖）
3. **Cross-Pack Audit**（Plan 内跨 Pack 的合同/migration/import/状态）

**新 Final Review 三层**：
1. Regression Sweep（不变——全局 diff）
2. Intent Coverage（不变——设计意图覆盖）
3. **Cross-Plan Integration**（改名+降级——只检查跨 Plan 的集成，Plan 内跨 Pack 已由 Plan Implementation Review 覆盖）

Cross-Plan Integration 检查：
- 跨 Plan 的 Pydantic model / schema_version / API 一致性
- 跨 Plan 的 migration 顺序
- 跨 Plan 的 import 关系
- 跨 Plan 的状态竞争

如果所有 Plan 之间没有共享 contract / migration / state surface，Cross-Plan Integration 降级为确认独立性的 1 行声明（与当前 Cross-Pack 降级规则一致）。

---

## Execution 循环改造（图 2 替换）

### 新流程

```
Plan Review pass
  → 读 plan Task Pack inventory
  → FOR EACH Plan（按 Blocked by 排序）:
      → FOR EACH Pack（按 Dependencies 排序，可并行）:
          → 派 worker（pack-executor / complex-pack-executor）
          → worker 返回 → Coordinator 检查
          → Open Items 处置
          → Intra-Plan Blocker 检查
          → Git Checkpoint（per-pack commit）
          → 合并并行 Pack 的 Worktree（如有）
      → 所有 Pack 完成
      → Plan Implementation Review（Codex dispatch）
      → Disposition + 修复分流
      → Early Release Gate（条件触发）
  → 所有 Plan 完成
  → Final Review
```

### 对比

| 维度 | 旧 | 新 |
|------|----|----|
| Worker 粒度 | Pack | Pack（不变） |
| Codex Review 粒度 | Pack | Plan |
| Review 次数 | N（Pack 总数） | P（Plan 总数） |
| Git Checkpoint | Per-pack after review | Per-pack before review（review 在所有 pack 后） |
| Early Release Gate | Per-pack after Pack Review | Per-plan after Plan Impl Review |
| Repair 路由 | 直接对应原 Pack worker | 通过 Affected packs 字段路由到对应 worker |
| Final Review Cross-Pack | Plan 内跨 Pack | 降级为 Cross-Plan |

---

## Plan Implementation Review Prompt 模板

Gate 名：`plan-impl-review-N`（N = plan 编号）

```markdown
## Scope
Review the implementation of Plan N: <plan title>
This plan implements Issue N: <issue title> (a vertical slice of <feature>).
All Task Packs within this plan have been executed and committed.

## Source artifacts
- Plan: docs/orchestrate/plans/<slug>/00N-*.md
- Source design: docs/orchestrate/design/<slug>.md
- Source issue: docs/orchestrate/issues/<slug>/00N-*.md
- Scope Contract: .claude/multi-model-workflow/scope-<run_id>.md

## Pack summary
| Pack | Worker verdict | Repair rounds | Changed files |
<paste per-pack summary within this plan>

## Aggregate diff
git diff <plan-start-commit>..<plan-end-commit>

## Changed files (all packs combined)
<combined file list with pack ownership>

## Contract anchors
<paste all contract anchors from all packs in this plan>

## Mockup anchors
<paste if any pack in this plan has UI work>

## Review angles (single integrated review)

### Spec Compliance
验 plan 中所有 pack 的实现是否满足要求：
- 每个 pack 的 acceptance criteria 是否满足
- 每个 pack 的 goal behavior 是否可从代码确认
- pack 之间是否有遗漏的交互行为
- 是否有 missing requirements（设计中有但代码没做到的）
- 是否有 extra/unneeded work（YAGNI）

### Code Quality
验实现是否正确、可维护：
- TDD 纪律：测试测的是 public behavior 而非 mock behavior
- Mock 纪律：mock 只用在外部边界
- 合同纪律：跨边界数据用正式 Pydantic contract
- Pack 间接口一致性：Pack A 暴露的接口是否与 Pack B 消费的一致
- Forbidden shortcuts（同现有列表）

### Cross-Pack Coherence（原 Final Review 的 Cross-Pack Audit 下沉到这里）
验同 Plan 内多个 Pack 合在一起是否协调：
- Shared contract surface：跨 pack 的 Pydantic model / schema_version / API 一致
- Migration 顺序：多个 migration 的执行顺序正确
- Import 关系：跨 pack 的 import 无循环
- 状态竞争：并发访问共享 state 安全
- UI 集成（如有）：跨 pack 的页面集成效果

如果 Plan 中所有 Pack 之间没有共享 contract / migration / state surface，
Cross-Pack Coherence 降级为确认独立性的 1 行声明。

### Contract & Risk
验高风险面是否正确处理：
- Contract anchors 闭合
- Migration / registry / catalog 完整
- 发布风险标注准确
- rollback / compatibility 考虑

## Calibration
**不要信任 worker 的报告——独立验证一切。**
只标记会导致实际问题的 issue。
措辞、风格偏好、nice-to-have 建议——不是。
除非有严重缺口，否则 approve。

## Return Contract
### Verdict
pass / blocked / needs repair / needs context
### Evidence
### Result
Plan Implementation Review 结果：
Spec compliance:
Code quality:
Cross-pack coherence:
Contract & risk:
Critical:
  - [Pack N.M] <finding>
Important:
  - [Pack N.M] <finding>
Affected packs:
低置信度观察:
Disposition required:
### Verification
### Open Items
```

---

## 修复截断（继承现有模式，适配 Plan 粒度）

每个 Plan Implementation Review 最多 **2 Worker repair round + 1 root-cause-analyst round = 3 repair round**（与现有截断规则一致）。

区别：
- Findings 通过 `Affected packs` 路由到对应 Pack 的 worker
- 多个 Pack 涉及的 finding → Coordinator 判断是否拆分或统一修复
- Targeted Re-Review 文件名：`plan-impl-review-N-repair-<round>`

---

## 涉及修改的文件清单

### 核心修改（Execution 循环重构）

| 文件 | 改动 |
|------|------|
| `orchestrate-execution/SKILL.md` | 两级循环描述（Plan → Pack） |
| `execution-pack-review-cycle.md` | 重命名为 `execution-plan-review-cycle.md`；拆分为 Pack 执行循环（Steps 4-7a）和 Plan Review 派发（Step 8） |
| `execution-review-dispatch.md` | 重写 prompt 模板从 Pack 级到 Plan 级 |
| `execution-repair-truncation.md` | 适配 Plan 粒度修复路由（Affected packs 归属） |
| `execution-completion.md` | Git Checkpoint 时机调整（per-pack commit + per-plan review） |
| `execution-preparation.md` | 构建两级执行队列（Plan → Pack） |
| `execution-release-gate.md` | 触发时机从 per-pack 改为 per-plan |
| `execution-worker-dispatch.md` | Pack Brief 增加提示："your code will be reviewed alongside packs N.1..N.M within this plan" |

### Final Review 适配

| 文件 | 改动 |
|------|------|
| `final-review-angles.md` | Cross-Pack Audit → Cross-Plan Integration；Pack Review → Plan Impl Review 引用 |
| `final-review-preconditions.md` | "所有 pack 通过 Pack Review" → "所有 Plan 通过 Plan Implementation Review" |

### 基础设施

| 文件 | 改动 |
|------|------|
| `hooks/hooks.json` | 全面重构：SubagentStop 改为脚本 + 新增 PreToolUse Agent matcher + PostToolUse git commit matcher |
| `architecture-draft.md` | 图 2 重绘 + 预算公式 + 组件表 + 编辑同步清单 |

### Plan Writing 适配

| 文件 | 改动 |
|------|------|
| `plan-gates.md` | Budget 公式从 `2N+12` 改为 `3P+12` |

### 小计：13 个文件（另见下方"Execution 状态追踪系统"追加 6 个）

---

## Execution 状态追踪系统（新增）

### 问题：Coordinator 记忆依赖

当前 Execution 循环中，大量关键决策依赖 Coordinator 的上下文记忆。Context compaction 后这些信息丢失，Coordinator 必须靠"自觉"重新推导——但没有机制强制它这么做。

#### 决策点枚举

| 决策 | 当前靠什么 | Compaction 后可恢复？ | 改造目标 |
|------|-----------|---------------------|---------|
| 当前执行到哪个 Plan？ | Coordinator 记忆 | ❌ 需从 plan checkboxes + git log 重推导 | 文件记录 |
| 当前 Plan 中哪些 Pack 已完成？ | Coordinator 记忆 + plan checkboxes | ⚠️ Checkboxes 仅在 commit 后翻勾 | 文件记录 |
| Plan 开始时的 commit SHA（review diff 用） | **无记录** | ❌ | 文件记录 |
| Pack 的 agentId（SendMessage repair 用） | Coordinator 记忆 | ❌ | 文件记录 |
| 当前 Plan 的 repair round | Coordinator 记忆 + `-repair-N` 文件名 | ⚠️ 可从文件名推导但不可靠 | 文件记录 |
| Pre-dispatch Context Transfer 是否执行？ | 文档规定但无强制 | N/A | Hook 强制 |
| Open Items 是否已处置？ | Coordinator 记忆 + GitHub issues | ⚠️ 部分 | 文件记录 |
| Worker scope drift 是否检查？ | Coordinator 记忆 | ❌ | 文件记录 |
| "当前 Plan 所有 Pack 完成？→ 派发 Review" | Coordinator 记忆 + 计数 | ❌ | Hook 计算 + 文件记录 |
| Plan 级 review verdict | Coordinator 记忆 | ⚠️ 可从 `review-results/` 重推导 | 文件记录 |
| Worker 返回的 verdict | Coordinator 解析 Agent tool 返回 | ❌ | Worker 写盘 + Hook 读取 |

### 设计方案：Execution State File + Hook 扩展

**核心原则**：一个新状态文件 + 扩展已有 hooks，不引入新系统。所有 Execution 决策改为"从文件读"而非"从记忆取"。

#### 状态文件：`execution-state-<run_id>.json`

位置：`.claude/multi-model-workflow/execution-state-<run_id>.json`

```json
{
  "run_id": "formal-20260521-143000",
  "current_plan_id": "002",
  "plans": {
    "001": {
      "status": "review_passed",
      "start_commit": "abc1234",
      "end_commit": "def5678",
      "review_gate": "plan-impl-review-1",
      "review_verdict": "pass",
      "repair_round": 0,
      "release_gate_triggered": false,
      "expected_pack_ids": ["1.1", "1.2", "1.3", "1.4"],
      "packs": {
        "1.1": {
          "status": "committed",
          "agent_id": "agent-abc123",
          "commit_sha": "aaa1111",
          "worker_verdict": "pass",
          "open_items_processed": true,
          "scope_drift_checked": true
        },
        "1.2": {
          "status": "committed",
          "agent_id": "agent-def456",
          "commit_sha": "bbb2222",
          "worker_verdict": "pass",
          "open_items_processed": true,
          "scope_drift_checked": true
        }
      }
    },
    "002": {
      "status": "in_progress",
      "start_commit": "def5678",
      "end_commit": null,
      "review_gate": null,
      "review_verdict": null,
      "repair_round": 0,
      "release_gate_triggered": false,
      "expected_pack_ids": ["2.1", "2.2", "2.3"],
      "packs": {
        "2.1": {
          "status": "dispatched",
          "agent_id": "agent-ghi789",
          "commit_sha": null,
          "worker_verdict": null,
          "open_items_processed": false,
          "scope_drift_checked": false
        }
      }
    }
  }
}
```

**Status 枚举**：
- Plan: `pending` → `in_progress` → `review_pending` → `repairing` → `review_passed` → `release_gate_pending` → `completed` | `blocked`
- Pack: `pending` → `dispatched` → `returned` → `committed` | `blocked`

**创建时机**：`execution-preparation.md` Step 2 构建执行队列后立即创建，写入所有 Plan 和 Pack 的初始状态 + `expected_pack_ids`。`start_commit` 在每个 Plan 的第一个 Pack dispatch 前记录（`git rev-parse HEAD`）。

#### Worker 写盘机制

**问题**：`SubagentStop` hook 不包含 subagent 返回文本（只有 `agent_id` / `agent_type` / `transcript_path`）。`PostToolUse` on `Agent` 是否包含结构化返回文本未确定。

**方案**：在 Pack Brief Return Contract 中增加一条指令——Worker 完成后将 verdict 写入约定路径：

```text
Return contract:
  ### Verdict
  pass / blocked / needs repair / needs context
  ### Evidence
  ...

  ## Durable return（必须在最终 verdict 之前执行）
  写入 `.claude/multi-model-workflow/pack-returns/<pack-id>.json`：
  {
    "pack_id": "<N.M>",
    "verdict": "<pass | blocked | needs repair | needs context>",
    "changed_files": ["<path1>", "<path2>"],
    "open_items": [{"tag": "<out-of-scope|needs-evaluation|bug>", "summary": "..."}],
    "concerns": "<如有>"
  }
```

**为什么让 Worker 写盘**：
- Worker 是唯一知道自己 verdict 和 changed files 的实体
- 写入约定路径后，任何 hook 或后续 Coordinator（包括 compaction 后的）都能读取
- 不依赖 Coordinator 解析 Agent tool 返回值

#### Hook 修改清单

| Hook | 事件 | 改动 | 触发条件 |
|------|------|------|---------|
| **`session-start.sh`** | `SessionStart` | 扩展：检测 `execution-state-*.json` → 输出当前进度概要 | 有活跃 execution state |
| **`track-review-budget.sh`** | `PostToolUse` Bash | 扩展：检测 `codex-companion result` 且 gate 为 `plan-impl-review-N` → 写入 `plans[N].review_verdict` | Review 结果返回时 |
| **新 hook：`track-execution-state.sh`** | `PostToolUse` Bash + `if: "Bash(git commit*)"` | 解析 commit message `Pack N.M:` 格式 → 更新 `packs[N.M].commit_sha`、`packs[N.M].status = committed`。首个 Pack 时记录 `plans[N].start_commit` | Git commit 后 |
| **`SubagentStop` hook** | `SubagentStop` | 扩展：读 `pack-returns/<pack-id>.json` → 更新 execution state → 计算当前 Plan 完成度 → 输出精确指令 | Worker 完成时 |
| **新 hook：`validate-pack-dispatch.sh`** | `PreToolUse` Agent + `if: "Agent(pack-executor*) OR Agent(complex-pack-executor*)"` | 检查 execution state：当前 Pack 的前置 Pack 是否已 committed → 阻止乱序 dispatch | Worker dispatch 前 |

#### Hook 详细设计

##### 1. `session-start.sh` 扩展

在现有行为覆盖规则输出之后，追加 execution state 检测：

```bash
# Execution state recovery
BUDGET_DIR=".claude/multi-model-workflow"
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"
if [ -f "$RUN_ID_FILE" ]; then
  RUN_ID=$(cat "$RUN_ID_FILE")
  STATE_FILE="${BUDGET_DIR}/execution-state-${RUN_ID}.json"
  if [ -f "$STATE_FILE" ]; then
    CURRENT_PLAN=$(jq -r '.current_plan_id' "$STATE_FILE")
    PLAN_STATUS=$(jq -r ".plans[\"${CURRENT_PLAN}\"].status" "$STATE_FILE")
    TOTAL_PACKS=$(jq "[.plans[].expected_pack_ids | length] | add" "$STATE_FILE")
    DONE_PACKS=$(jq '[.plans[].packs | to_entries[] | select(.value.status == "committed")] | length' "$STATE_FILE")
    echo ""
    echo "# 6. Execution state recovery"
    echo "- Current plan: ${CURRENT_PLAN} (${PLAN_STATUS})"
    echo "- Progress: ${DONE_PACKS}/${TOTAL_PACKS} packs committed"
    echo "- Re-read execution-state-${RUN_ID}.json before continuing"
  fi
fi
```

##### 2. `track-execution-state.sh`（新 hook）

```bash
#!/usr/bin/env bash
# PostToolUse hook for Bash tool (if: "Bash(git commit*)").
# Detects Pack commits and updates execution-state file.
set -euo pipefail

INPUT=$(cat)
EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_response.exit_code // 0' 2>/dev/null)
if [ "$EXIT_CODE" != "0" ]; then exit 0; fi

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
STDOUT=$(echo "$INPUT" | jq -r '.tool_response.stdout // empty' 2>/dev/null)

# 从 commit message 中提取 Pack ID (格式: "Pack N.M: ...")
PACK_ID=$(echo "$COMMAND" | grep -oP 'Pack \K[0-9]+\.[0-9]+' | head -1)
if [ -z "$PACK_ID" ]; then exit 0; fi

PLAN_ID=$(echo "$PACK_ID" | cut -d. -f1)
# 零填充 Plan ID 以匹配 state file key 格式
PLAN_KEY=$(printf "%03d" "$PLAN_ID")

BUDGET_DIR=".claude/multi-model-workflow"
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"
if [ ! -f "$RUN_ID_FILE" ]; then exit 0; fi

RUN_ID=$(cat "$RUN_ID_FILE")
STATE_FILE="${BUDGET_DIR}/execution-state-${RUN_ID}.json"
if [ ! -f "$STATE_FILE" ]; then exit 0; fi

COMMIT_SHA=$(git rev-parse HEAD 2>/dev/null || echo "unknown")

# 更新 pack status 和 commit_sha
jq --arg plan "$PLAN_KEY" --arg pack "$PACK_ID" --arg sha "$COMMIT_SHA" '
  .plans[$plan].packs[$pack].status = "committed" |
  .plans[$plan].packs[$pack].commit_sha = $sha |
  # 如果是该 Plan 的首个 commit，记录 start_commit
  if .plans[$plan].start_commit == null then
    .plans[$plan].start_commit = $sha
  else . end |
  # 更新 end_commit
  .plans[$plan].end_commit = $sha
' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"

# 计算进度
DONE=$(jq --arg plan "$PLAN_KEY" '[.plans[$plan].packs | to_entries[] | select(.value.status == "committed")] | length' "$STATE_FILE")
TOTAL=$(jq --arg plan "$PLAN_KEY" '.plans[$plan].expected_pack_ids | length' "$STATE_FILE")

jq -n --arg msg "[multi-model-workflow] Pack ${PACK_ID} committed (${DONE}/${TOTAL} in Plan ${PLAN_KEY})." \
  '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $msg}}'
exit 0
```

**start_commit 逻辑说明**：首个 Pack commit 时 `plans[N].start_commit` 为 null，hook 将其设为该 commit 的 SHA。但这记录的是"首次 commit 后的 SHA"，而非"首次 commit 前的 SHA"。Review diff 需要的是"Plan 开始前的状态"。

**修正**：`start_commit` 应在 Plan 进入 `in_progress` 时记录（`execution-preparation.md` 中 Coordinator 开始执行该 Plan 前）。Hook 只负责更新 `end_commit`。因此 `start_commit` 的写入时机是：

```
Coordinator 开始 Plan N 的第一个 Pack dispatch 之前：
  git rev-parse HEAD → 写入 plans[N].start_commit
  plans[N].status = in_progress
```

这一步写入 SKILL reference（`execution-preparation.md`），不靠 hook——因为它发生在 dispatch 之前，hook 无法提前触发。

##### 3. `SubagentStop` hook 扩展

```bash
# 替换当前的纯 echo 消息
#!/usr/bin/env bash
set -euo pipefail

INPUT=$(cat)
AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // empty' 2>/dev/null)

# 只处理 coding worker
if ! echo "$AGENT_TYPE" | grep -qE 'pack-executor|complex-pack-executor'; then
  exit 0
fi

BUDGET_DIR=".claude/multi-model-workflow"
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"
if [ ! -f "$RUN_ID_FILE" ]; then
  echo "[multi-model-workflow] Coding agent completed. No active run — cannot determine next step." >&2
  exit 0
fi

RUN_ID=$(cat "$RUN_ID_FILE")
STATE_FILE="${BUDGET_DIR}/execution-state-${RUN_ID}.json"
if [ ! -f "$STATE_FILE" ]; then
  echo "[multi-model-workflow] Coding agent completed. No execution state file — read execution-preparation.md." >&2
  exit 0
fi

# 读取 worker 的 durable return（如果存在）
AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // empty' 2>/dev/null)
CURRENT_PLAN=$(jq -r '.current_plan_id' "$STATE_FILE")

# 在 pack-returns/ 中查找该 agent 对应的 pack return
RETURN_FILE=""
for f in "${BUDGET_DIR}/pack-returns/"*.json; do
  [ -f "$f" ] || continue
  RETURN_FILE="$f"
  break  # 处理最新的未消费 return
done

if [ -n "$RETURN_FILE" ]; then
  PACK_ID=$(jq -r '.pack_id' "$RETURN_FILE")
  VERDICT=$(jq -r '.verdict' "$RETURN_FILE")
  
  # 更新 execution state
  PLAN_KEY=$(printf "%03d" "$(echo "$PACK_ID" | cut -d. -f1)")
  jq --arg plan "$PLAN_KEY" --arg pack "$PACK_ID" --arg verdict "$VERDICT" --arg agent "$AGENT_ID" '
    .plans[$plan].packs[$pack].worker_verdict = $verdict |
    .plans[$plan].packs[$pack].agent_id = $agent |
    .plans[$plan].packs[$pack].status = "returned"
  ' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
fi

# 计算当前 Plan 完成度
COMMITTED=$(jq --arg plan "$CURRENT_PLAN" \
  '[.plans[$plan].packs | to_entries[] | select(.value.status == "committed")] | length' "$STATE_FILE")
EXPECTED=$(jq --arg plan "$CURRENT_PLAN" \
  '.plans[$plan].expected_pack_ids | length' "$STATE_FILE")

if [ "$COMMITTED" -eq "$EXPECTED" ] && [ "$EXPECTED" -gt 0 ]; then
  MSG="All ${EXPECTED} packs in Plan ${CURRENT_PLAN} are committed. NEXT: dispatch Plan Implementation Review. Read execution-review-dispatch.md for the prompt template. Plan diff range: $(jq -r --arg p "$CURRENT_PLAN" '.plans[$p].start_commit' "$STATE_FILE")..$(jq -r --arg p "$CURRENT_PLAN" '.plans[$p].end_commit' "$STATE_FILE")"
else
  NEXT_PACK=$(jq -r --arg plan "$CURRENT_PLAN" \
    '.plans[$plan].expected_pack_ids as $ids | .plans[$plan].packs | to_entries | map(.key) as $done | ($ids - $done)[0] // "none"' "$STATE_FILE")
  MSG="Pack completed (${COMMITTED}/${EXPECTED} in Plan ${CURRENT_PLAN}). NEXT: process Open Items → scope drift check → Git Checkpoint → continue with Pack ${NEXT_PACK}."
fi

echo "[multi-model-workflow] ${MSG}" >&2
exit 0
```

##### 4. `track-review-budget.sh` 扩展

在现有的 budget 追踪逻辑之后，追加 execution state 更新：

```bash
# 追加到现有逻辑末尾（budget_used 递增之后）
# 如果是 Plan Implementation Review 的结果，更新 execution state
GATE=$(echo "$COMMAND" | grep -oP 'plan-impl-review-\K[0-9]+' | head -1)
if [ -n "$GATE" ]; then
  STATE_FILE="${BUDGET_DIR}/execution-state-${RUN_ID}.json"
  PLAN_KEY=$(printf "%03d" "$GATE")
  if [ -f "$STATE_FILE" ]; then
    jq --arg plan "$PLAN_KEY" --arg gate "plan-impl-review-${GATE}" '
      .plans[$plan].review_gate = $gate |
      .plans[$plan].status = "review_pending"
    ' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
  fi
fi
```

Review verdict 写入由 Coordinator 在 Disposition 后执行（需要人工判断 accepted/rejected），不由 hook 自动写入——hook 只标记"review 已提交"。

##### 5. `validate-pack-dispatch.sh`（新 PreToolUse hook）

```bash
#!/usr/bin/env bash
# PreToolUse hook for Agent tool.
# Validates pack dispatch preconditions against execution state file.
set -euo pipefail

INPUT=$(cat)
PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // empty' 2>/dev/null)

# 从 dispatch prompt 中提取 Pack ID
PACK_ID=$(echo "$PROMPT" | grep -oP 'Pack:?\s*\K[0-9]+\.[0-9]+' | head -1)
if [ -z "$PACK_ID" ]; then exit 0; fi

PLAN_ID=$(echo "$PACK_ID" | cut -d. -f1)
PLAN_KEY=$(printf "%03d" "$PLAN_ID")

BUDGET_DIR=".claude/multi-model-workflow"
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"
if [ ! -f "$RUN_ID_FILE" ]; then exit 0; fi

RUN_ID=$(cat "$RUN_ID_FILE")
STATE_FILE="${BUDGET_DIR}/execution-state-${RUN_ID}.json"
if [ ! -f "$STATE_FILE" ]; then exit 0; fi

# 检查：该 Pack 的 Dependencies 中所有前置 Pack 是否已 committed
# （Dependencies 在 execution state 创建时已写入——如果 state 中该 pack 已存在但 status 不是 pending，说明正在重复 dispatch）
CURRENT_STATUS=$(jq -r --arg plan "$PLAN_KEY" --arg pack "$PACK_ID" '.plans[$plan].packs[$pack].status // "pending"' "$STATE_FILE")
if [ "$CURRENT_STATUS" != "pending" ] && [ "$CURRENT_STATUS" != "null" ]; then
  echo "[multi-model-workflow] WARNING: Pack ${PACK_ID} status is '${CURRENT_STATUS}', not 'pending'. Verify this is intentional (e.g., repair re-dispatch)." >&2
fi

# 检查：start_commit 是否已记录（首个 Pack dispatch 前 Coordinator 应已记录）
START=$(jq -r --arg plan "$PLAN_KEY" '.plans[$plan].start_commit // "null"' "$STATE_FILE")
if [ "$START" = "null" ]; then
  echo "[multi-model-workflow] WARNING: Plan ${PLAN_KEY} has no start_commit recorded. Record git rev-parse HEAD before dispatching first pack." >&2
fi

exit 0
```

**注意**：此 hook 只发出 WARNING（stderr），不阻断（exit 0）——阻断 Agent 调用风险太高，可能破坏合法的 repair re-dispatch。

#### Coordinator 侧写入点（文档约束，不靠 Hook）

某些状态只有 Coordinator 能写入——hook 无法代劳。这些写入点作为**必须步骤**写入对应的 reference 文档：

| 写入时机 | 写入什么 | 写到哪个 reference |
|---------|---------|-------------------|
| `execution-preparation.md` Step 2 之后 | 创建 `execution-state-<run_id>.json`，填入所有 Plan 和 Pack 初始状态 | execution-preparation.md |
| 每个 Plan 首个 Pack dispatch 之前 | `plans[N].start_commit = git rev-parse HEAD`、`plans[N].status = in_progress`、`current_plan_id = N` | execution-preparation.md（新 Step 2b） |
| Worker 返回后 Coordinator 处理 Open Items | `packs[N.M].open_items_processed = true` | execution-pack-review-cycle.md Step 7a |
| Worker 返回后 Coordinator 检查 scope drift | `packs[N.M].scope_drift_checked = true` | execution-pack-review-cycle.md Step 7 |
| Plan Implementation Review 提交后 | `plans[N].status = review_pending` | execution-review-dispatch.md |
| Disposition 完成后 | `plans[N].review_verdict = pass/needs repair`、`plans[N].status` 更新 | execution-review-dispatch.md 或 repair-truncation.md |
| Repair round 开始 | `plans[N].repair_round += 1`、`plans[N].status = repairing` | execution-repair-truncation.md |
| Plan 完成（review pass + release gate） | `plans[N].status = completed`、`current_plan_id` 更新为下一个 Plan | execution-completion.md |

#### 状态文件读取点（Compaction Recovery 用）

| 读取时机 | 读什么 | 触发者 |
|---------|--------|--------|
| Session start / compact | 当前 Plan + 进度 | `session-start.sh` hook |
| 进入 execution phase | 全量读取，确定从哪里继续 | Coordinator（`execution-preparation.md`） |
| Worker dispatch 前 | `plans[N].start_commit`（确认已记录） | `validate-pack-dispatch.sh` hook |
| Worker 返回后 | `packs[N.M].agent_id`（repair SendMessage 用） | Coordinator |
| Plan Implementation Review 构造 prompt 时 | `plans[N].start_commit`..`plans[N].end_commit`（diff 范围）| Coordinator |
| Repair routing | `packs[N.M].agent_id` + `plans[N].repair_round` | Coordinator |
| Final Review 前置条件检查 | 所有 Plans 的 `status == completed` | Coordinator |

#### `cleanup-before-push.sh` 扩展

`execution-state-<run_id>.json` 和 `pack-returns/` 目录纳入清理范围——它们随 `.claude/multi-model-workflow/` 目录一起删除（现有行为已覆盖）。

#### Direct Repair mini-route

不受此改造影响。Direct Repair 不创建 Budget File，也不创建 execution-state file（与现有 "no budget file" 规则一致）。

#### `hooks.json` 新结构

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|clear|compact",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh\"",
            "timeout": 5
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"${CLAUDE_PLUGIN_ROOT}/scripts/guard-premature-push.sh\""
          },
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/scripts/cleanup-before-push.sh\""
          }
        ]
      },
      {
        "matcher": "Agent",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/validate-pack-dispatch.sh\"",
            "if": "Agent(pack-executor*)"
          },
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/validate-pack-dispatch.sh\"",
            "if": "Agent(complex-pack-executor*)"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/track-review-budget.sh\"",
            "timeout": 10
          },
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/track-execution-state.sh\"",
            "if": "Bash(git commit*)",
            "timeout": 10
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "matcher": "pack-executor|complex-pack-executor",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/subagent-stop-handler.sh\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### 涉及修改的文件（追加）

| 文件 | 改动 |
|------|------|
| `hooks/hooks.json` | 新增 PreToolUse Agent matcher、PostToolUse git commit matcher、SubagentStop 改为脚本 |
| `hooks/session-start.sh` | 追加 execution state recovery 输出 |
| `hooks/track-review-budget.sh` | 追加 Plan Impl Review gate → execution state 更新 |
| `hooks/track-execution-state.sh`（新建） | Git commit 后更新 pack status |
| `hooks/subagent-stop-handler.sh`（新建） | 替代原有 echo；读 worker return → 更新 state → 计算完成度 → 输出精确指令 |
| `hooks/validate-pack-dispatch.sh`（新建） | Worker dispatch 前检查前置条件 |
| `execution-worker-dispatch.md` | Pack Brief 增加 Durable Return 指令（Worker 写 verdict 到 `pack-returns/`） |
| `execution-preparation.md` | 新增 Step 2a（创建 execution-state）+ Step 2b（Plan start_commit 记录） |

**总计文件数更新**：原 13 个 + 新 6 个 = 19 个文件。

---

## 不改的部分

- Worker agent 定义（`pack-executor.md` / `complex-pack-executor.md`）——行为不变（Durable Return 写盘通过 Pack Brief 指令实现，不改 agent 定义）
- Plan writer agent 定义——不涉及执行阶段
- Discovery / Plan Writing skill 主体——不涉及执行阶段
- `guard-premature-push.sh`——逻辑不变
- `cleanup-before-push.sh`——逻辑不变（`execution-state-*.json` 和 `pack-returns/` 在 `.claude/multi-model-workflow/` 下，已被现有删除逻辑覆盖）
