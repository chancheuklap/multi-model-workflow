# Bug Investigation Route — Dispatch Templates + Flow

> **流程位置**：`orchestrate-workflow` Steps 15-18 · Route 2 Bug Investigation

## Self-Read Protocol

你是 root_cause_analyst。启动时按以下顺序执行：

1. 读 dispatch prompt 头部的 `DISPATCH_ENVELOPE`，提取 `run_id`、`bug_context`（包含 `description`、`error_log`、`file_paths[]`、`previous_attempts`）。
2. 读 `bug_context.file_paths[]` 中列出的所有相关源文件，理解 bug 所在上下文。
3. 读本文件（你正在读的这份手册），理解 Return Contract 格式与 Coordinator 处置路由。
4. 独立调查根因，遵循假设驱动流程：列假设 → 寻证据 → 排除 → 得结论。
5. 输出 Verdict，说明 Resolution、Root cause、Fix（若已修复）、Excluded hypotheses、Regression risk。

## Step 15：Dispatch root_cause_analyst

```
spawn_agent({
  agent_type: "root_cause_analyst",
  description: "Bug Investigation: <bug title>",
  prompt: "
    ## 调度场景
    Bug Investigation 入口。用户报告 bug/error/regression，根因不明，从零调查。

    ## Bug context
    读 `DISPATCH_ENVELOPE.bug_context`，该字段包含：
    - `description`: 用户报告的 bug 描述
    - `error_log`: 错误日志、失败测试、regression 描述（若有）
    - `file_paths`: 相关文件路径列表（若已知）
    - `previous_attempts`: 用户提到的已尝试修复方式（若有）

    注：`envelope.bug_context` 由 Coordinator 在派发时填入 `DISPATCH_ENVELOPE` JSON 块。

    ## Return contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    ### Result
    - Resolution: fixed / root cause found, not fixed /
      root cause in design/plan / unable to reproduce / unable to determine
    - Root cause: <evidence>
    - Fix applied: <if fixed>
    - Excluded hypotheses: <with evidence>
    - Regression risk: <what could break>
    ### Verification
    ### Open Items
  "
})
```

## Step 16：Handle Analyst Return

| Resolution | Coordinator 动作 |
| --- | --- |
| `fixed` | analyst 已修复代码（未 commit）→ Step 17（Codex review） |
| `root cause found, not fixed` | 修复超出 analyst 能力 → Step 18（派 worker 修复） |
| `root cause in design/plan` | 系统性问题 → 转入 Formal Orchestrate（Route 1）：创建 budget file → 进入 Step 7（discovery），seed with analyst report |
| `unable to reproduce` | 报告用户，附 analyst 排除路径，请求更多重现信息 |
| `unable to determine` | 报告用户，附 analyst 排除路径和已排除假设，请求协助判断方向 |

### `root cause in design/plan` → Discovery Seed

Coordinator 整理 analyst report 的 RCA findings 直接作为 Discovery Source artifact 传入 orchestrate-discovery。不创建中间 bug-seed 文件，RCA findings 报告路径直接加入 Scope Contract 的 Source artifacts。

此时执行两项基础设施操作：
1. **更新 Scope Contract**：更新 `.codex/multi-model-workflow/scope-<run_id>.md` 的 Source artifacts（加入 RCA analyst findings 报告路径）、Editable artifacts（加入 design / plan）和 Out of scope。
2. **创建 Budget File**（Step 2c）。

## Step 17：Simple Bug — Codex Review

Analyst 已修复代码。

**Read** `${MMW_PLUGIN_ROOT}/skills/_shared/review-dispatch.md` 并按其格式派发 Codex review。

Review prompt 写入 `.codex/multi-model-workflow/review-prompts/bug-fix-review.md`：

```markdown
## Scope
Review a bug fix applied by root_cause_analyst.

## Bug
<original bug description>

## Root cause
<analyst's root cause finding>

## Fix applied
<analyst's fix description + changed files>

## Review angles
- Fix addresses the stated root cause
- No regression introduced
- Tests cover the fixed behavior
- Contract integrity maintained (if applicable)

## Calibration
Targeted bug fix review — only assess fix correctness and regression risk.
Do not expand scope beyond the stated bug.

## Return Contract
### Verdict
pass / needs repair / blocked
### Evidence
### Result
### Verification
### Open Items
```

**整体 Verdict 前置检查**：如果 reviewer 返回整体 `needs context`，补充上下文后重新 dispatch，不进入 per-finding 处理。

| Verdict | 动作 |
| --- | --- |
| `pass` | Step 21（Closing） |
| `needs repair` | Coordinator 验证 finding → 路径 A（Coordinator 直接修，≤2 文件）或路径 B（新建 worker 修复）→ baseline re-review（重用 Step 17 模板，scope 缩小到修复 diff）→ 最多 2 轮 → Closing |
| `blocked` | 报告用户 |

## Step 18：Complex Bug — Worker Dispatch

Analyst 找到根因但无法修复。按 risk flags 选择 worker：

```
spawn_agent({
  agent_type: "<pack_executor | complex_pack_executor>",
  description: "Fix bug: <bug title>",
  prompt: "
    ## Bug
    <original bug description>

    ## Root cause (from analyst investigation)
    <root cause + evidence + excluded hypotheses>

    ## Fix scope
    <affected files from analyst report>

    ## Acceptance criteria
    - [ ] Root cause addressed
    - [ ] Regression tests added
    - [ ] Existing tests pass

    ## Return contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    ### Result
    - Changed files
    - Completed behavior
    ### Verification
    ### Open Items
  "
})
```

Worker 返回处理：

**Read** `${MMW_PLUGIN_ROOT}/skills/_shared/repair-routing.md` 并按其流程处理 review findings。

| Worker Verdict | 动作 |
| --- | --- |
| `pass` | Codex review（同 Step 17）→ Closing |
| `needs repair` | 读 concerns；正确性问题 → send_input worker 修复；观察性意见 → 记录，进 Codex review |
| `needs context` | send_input 补充上下文给 worker |
| `blocked` | 技术阻塞：换更强模型 / 拆 scope；业务阻塞：询问用户 |

## Coordinator 端最小职责

Coordinator 在派发 root_cause_analyst 时只需完成以下动作，其余由 analyst 自读：

1. 写 `DISPATCH_ENVELOPE`，填入 `run_id`、`phase: "bug-investigation"`、`agent_role: "root_cause_analyst"`。
2. 在 `envelope.bug_context` 中写入 `description`、`error_log`（若有）、`file_paths[]`（若已知）、`previous_attempts`（若有）。
3. 触发 `state.sh` 记录 analyst 派发状态，保存 `agentId` 以备 send_input 补充上下文。
4. 等待 analyst 返回，按 Step 16 路由表处置 Resolution。

---
> **下一步**：修复通过 Codex review → Closing（`workflow-closing.md`）。root cause in design/plan → 创建 budget file + 转入 Route 1（SKILL.md Steps 7-14）。
