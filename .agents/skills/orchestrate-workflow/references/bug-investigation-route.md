# Bug Investigation Route — Dispatch Templates + Flow

> **流程位置**：`orchestrate-workflow` Steps 15-18 · Route 2 Bug Investigation

## Step 15：Dispatch root_cause_analyst

```
spawn_agent({
  agent_type: "root_cause_analyst",
  description: "Bug Investigation: <bug title>",
  prompt: "
    ## 调度场景
    Bug Investigation 入口。用户报告 bug/error/regression，根因不明，从零调查。

    ## Bug report
    <paste user's bug description>

    ## Reproduction / symptoms
    <paste error log, failing test, regression description>

    ## Relevant files (if known)
    <paste file paths, modules>

    ## What has been tried
    <paste if user mentioned previous attempts>

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

Coordinator 整理 analyst report 作为 Discovery 的输入 brief：

```text
## Bug-seeded Discovery

原始 bug: <description>
Analyst findings:
- Root cause: <analyst evidence>
- Affected modules: <list>
- Excluded hypotheses: <list>
- Recommended design change: <if analyst provided>

请以此为基础进行 Discovery 讨论，不需要用户从零描述问题。
```

此时执行两项基础设施操作：
1. **更新 Scope Contract**：scope 从 bug investigation 扩大为 full design + plan + execution。更新 `.codex/multi-model-workflow/scope-<run_id>.md` 的 Source artifacts（加入 analyst report）、Editable artifacts（加入 design / plan 预期产出）和 Out of scope。
2. **创建 Budget File**（Step 6）：后续走 Formal Orchestrate 完整管线。

## Step 17：Simple Bug — Codex Review

Analyst 已修复代码。派发 Codex 验证修复正确性：

Review：派发前先读 `references/external-review-lanes.md`，按 Codex 四步协议执行。

```
spawn_agent({
  agent_type: "code_reviewer",
  description: "Bug fix review: <bug title>",
  prompt: "
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
  "
})
```

**整体 Verdict 前置检查**：如果 reviewer 返回整体 `needs context`，补充上下文后重新 dispatch，不进入 per-finding 处理。

| Verdict | 动作 |
| --- | --- |
| `pass` | Step 21（Closing） |
| `needs repair` | Coordinator 验证 finding → 路径 A（Coordinator 直接修，≤2 文件）或路径 B（新建 worker 修复）→ targeted re-review（重用 Step 17 模板，scope 缩小到修复 diff）→ 最多 2 轮 → Closing |
| `blocked` | 报告用户 |

## Step 18：Complex Bug — Worker Dispatch

Analyst 找到根因但无法修复。按 risk flags 选择 worker：

```
spawn_agent({
  agent_type: "<coding_worker | complex_coding_worker>",
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

| Worker Verdict | 动作 |
| --- | --- |
| `pass` | Codex review（同 Step 17）→ Closing |
| `needs repair` | 读 concerns；正确性问题 → send_input worker 修复；观察性意见 → 记录，进 Codex review |
| `needs context` | send_input 补充上下文给 worker |
| `blocked` | 技术阻塞：换更强模型 / 拆 scope；业务阻塞：询问用户 |

---
> **下一步**：修复通过 Codex review → Closing（`workflow-closing.md`）。root cause in design/plan → 创建 budget file + 转入 Route 1（`workflow-formal-orchestrate.md`）。
