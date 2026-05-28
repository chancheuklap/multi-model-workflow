# Issue 002 — 合同与状态机层清理（Contracts & State）

## What to build

把 plugin 的"合同 + 状态机 + Worker Loop 机制"层做系统级清理，覆盖本轮影响最大的几个删除 + 合同重写：

- **删除 Path A 自修分叉**（决策 3）：移除 Path A 概念；所有修复一律走 Path B SendMessage；删除 `state.sh path-a-escalation` 子命令。
- **删除 doc-patch 系统 + Coordinator checkbox toggle 权威规则**（决策 4 / Alignment Review C3 闭合）：
  - 删除 `guard-plan-doc-patch.sh` + `scripts/lib/doc-patch-apply.sh` + `plan-return-v1.json` 的 `doc_patch_path` 字段
  - 修改 `agent-return-handler.sh`：不再暂存 doc-patch.diff，输出 NEXT 指令"Coordinator 须 Edit per_pack[*].status=committed 的 Pack checkbox"
  - 删除 worker-loop.md.tmpl 的"写 doc-patch.diff"步骤
  - **新增权威规则**：Coordinator Edit 的 source-of-truth = `plan-return.per_pack[*]` where `status == committed`；在 `orchestrate-execution/SKILL.md` Step 14 + `plan-review-resolution.md` 写入此规则
- **删除 bug-seed-file 中间文档**（决策 5）：RCA findings 直接进 Discovery；移除 scope contract 中 `bug_seed_path` 可选字段。
- **删除 state.sh agent-context-check + worker-loop segment 5 双路径重写**（决策 6 / Alignment Review C4 闭合）：
  - 删除 `state.sh agent-context-check` 子命令 + 18 处 Worker Loop 内调用
  - worker-loop.md.tmpl segment 5 必须包含两条路径：(a) 正常路径 `packs_in_session += 1`；(b) 启动 / Compaction recovery 路径 从 `execution-state.plans[plan_id].packs[*].status=="committed"` 计数作为初值
- **state.sh 死命令 + scripts/lib 清理**（决策 7 / Alignment Review C2 修正后）：
  - state.sh 删除 `business-summary` / `plans` / `path-a-escalation` 子命令；**保留** `idempotency check/append`
  - 删除 `scripts/lib/review-effectiveness.sh`；合并 `learnings-jsonl.sh` + `learnings-poison-detector.sh`
  - **review_effectiveness 真实 7 处 consumer 清理**：workflow-state-v1.json L10/L83 / state.sh L170/L347 / 2 个 hook test fixtures / test_review_effectiveness.sh 整文件 / learnings-confidence-audit.md L44 / verify-maturity.sh L73 / architecture-draft.md 相关章节
- **删除 Targeted Re-review 机制（全局，本轮 token 经济最大单项）**（决策 13）：
  - 删除 dispatch-envelope-v1.json 的 `review_intent` enum 中 `targeted-re-review` 值
  - 删除 review-dispatch.md.tmpl 的 `[variant=targeted-re-review]` 子模板（**必须在 D1 canonical 抽取之前完成**——执行顺序见决策 1）
  - 删除 plan-gates.md / SKILL.md 中所有 targeted-re-review 描述
  - **review budget 公式 `3P + 12` → `2P + 6`**：`2P` = 每 Plan 2 次（Plan Review + Plan Impl Review）；`+6` = Design Review 2 + Final Review 2 + Release Gate 1 + Multi-PR Integration Review 1
  - 修复后处置改为 Coordinator 自验闭合（grep + Read 验证修复点已落地），不再 reviewer 闭合复审
  - 极端失败走 `root-cause-analyst` 路径

完成本 issue 后：plugin 的合同基线（schema / state / Worker Loop 机制 / review 闭合方式）符合 token economy 目标；下游 Issue 003 才能在已清理的合同上做 phase 级压缩。

## Small issues

<!-- PENDING: plan-writer 将在 plan-writing 阶段补全小 issue 拆分 -->

## Blocked by

- **001 (Infrastructure)** — D13 删 Targeted Re-review 必须先于 D1 canonical 抽取完成（决策 1 与决策 13 执行顺序声明），且 D7 review_effectiveness 删除需要 D1 完成后的 canonical reference 引用基线
