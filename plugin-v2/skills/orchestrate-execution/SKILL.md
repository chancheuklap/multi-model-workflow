---
name: orchestrate-execution
description: "Phase A 执行。由 orchestrate-workflow coordinator 在 Phase 0b 通过后调用。逐 pack 派 worker → pack review → 修复循环。内部 phase skill，不由用户直接触发。"
---

# Orchestrate Execution (Phase A)

Phase 0b 通过后进入。逐 pack 循环：派 worker → Pack Review → 通过则检查 release gate → 下一 pack；needs repair 则验证 finding → 修复分流 → targeted re-review → 回到通过判定。全部 pack pass → orchestrate-final-review。

## Flow

```
Step 1: Read references/pack-dispatch.md.
        Per-pack worker dispatch.
        Read ${CLAUDE_PLUGIN_ROOT}/references/custom-agents.md for agent selection.
        When contract boundary touched: also read ${CLAUDE_PLUGIN_ROOT}/references/contract-boundary.md.
        Record returned agentId for potential SendMessage follow-up.

Step 2: Worker returns.
        Read references/pack-review.md.
        Dispatch 1 baseline codex-reviewer per pack.
        Read ${CLAUDE_PLUGIN_ROOT}/references/dispatch-primitives.md for Return Contract + Finding Shape.
        Read ${CLAUDE_PLUGIN_ROOT}/references/review-budget.md for budget check.

Step 3: Receive pack review.
        Disposition each finding.
        Repair per dispatch-primitives.md 修复归属.
        Each pack: max 3 repair rounds.
        第 2 轮 targeted re-review 仍 needs repair → 截断 worker 循环：
          dispatch root-cause-analyst (Agent tool, 始终新建).
          Route by analyst Result.Resolution:
            - fixed → targeted re-review (消耗第 3 轮).
            - root cause found, not fixed → 用 analyst findings 重新 dispatch worker (消耗第 3 轮).
            - root cause in design/plan → 写回 design doc / plan, re-enter Phase 0a/0b.
            - unable to determine → BLOCKED, 报告用户附排除路径.

Step 4: For parallel packs.
        Read references/worktree-merge.md.
        Coordinator merges worktrees sequentially.
        Resolve conflicts. Run full test suite post-merge.

Step 5: All packs pass → route to orchestrate-final-review.
        For non-pass outcomes — backflow and upstream skills (Skill tool; write back before continuing):
        - design / domain gap → Skill: orchestrate-discovery → 写回 design document
        - architecture friction / bad seam → Skill: improve-codebase-architecture → 写回 design doc / plan anchors
        - unknown root cause (read-only) → Agent: complex-code-explorer
        - bug needs reproduction / hypothesis → Skill: diagnose → 写回 bug brief / design doc
        - terminology / domain conflict → Skill: grill-with-docs → 写回 domain docs + design document
```

## Worker Dispatch

用 Agent tool 调度 `pack-executor`（普通 pack）或 `complex-pack-executor`（高风险 pack）。Prompt 包含 Pack Brief 完整字段（见 `dispatch-primitives.md`）+ pack 中所有 task 完整文本 + 上下文。**记录返回的 agentId**——后续复杂修复需要用 SendMessage 继续该 agent。

处理状态：
- **pass** → Pack Review。
- **needs repair** → 正确性问题先处理；观察性意见记下继续。
- **needs context** → SendMessage 继续原 worker，补充上下文（fallback: 新建同类 worker）。
- **blocked** → 技术阻塞自主解决（拆 pack / 进入 repair 循环）。业务阻塞询问用户。

## Parallel Dispatch

2+ 独立 pack 可并行执行：

- **并行 pack**：Agent tool call 中添加 `isolation: "worktree"`，每个 worker 在独立 worktree 中工作。返回含 worktree path 和 branch name。
- **顺序 pack**：不使用 worktree 隔离，worker 直接在当前分支工作。
- 全部返回后：逐个 `git merge <worktree-branch> --no-ff` → 解决冲突 → 跑完整测试验证。冲突则新建 targeted-repair agent 修复。
- 逐个跑 Pack Review。

## Release Gate

Pack Review 通过后，只在 early release gate 触发时追加 `codex:codex-rescue --model gpt-5.5`。多个相邻 high-risk packs 同一风险面合并一次。Early release gate 触发条件见 `review-budget.md`。

## 进度

每 2-3 个 pack 完成后一行 FYI。
