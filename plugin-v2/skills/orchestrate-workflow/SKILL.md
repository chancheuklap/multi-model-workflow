---
name: orchestrate-workflow
description: "正式开发流程主入口。用户给出新功能、改造、bug、design/plan/issue/PRD、UI/UX 反馈、截图、测试失败、已实现 diff，或要求实现/继续/review/验收/收尾时主动使用。Entry Gate → Infrastructure → Phase 路由 → Closing。"
---

# Orchestrate Workflow

主线程入口。Entry Gate → Infrastructure → Phase 路由 → Closing。

**Workflow 只做路由和基础设施**——不写设计、不写计划、不派 worker、不做 review。每个 phase 由对应 skill 负责。

**连续执行**：phase 之间不暂停、不汇报、不问"要不要继续"。BLOCKED 或业务决策才停。

---

## Step 1：Entry Gate

| 路线 | 输入信号 | 下一步 |
| --- | --- | --- |
| **Route 1: Formal Orchestrate** | 新功能、改造、feedback、缺 design/issue/plan、已有 design/plan 要 review/执行 | Step 2 |
| **Route 2: Bug Investigation** | bug / error log / regression / failing test，根因不明 | Step 4 → `references/bug-investigation-route.md` |
| **Route 3: Multi-PR Merge** | 多个并行 PR 需要合并审查 | Step 4 → Step 19 |

模糊输入 → 一次只问一个问题收窄。概念/事实问题 → 直接回答不进 orchestrate。

## Step 2：Within-Conversation Resume

同一对话内 phase skill 返回的 verdict → 直接路由到下一 phase（读取 `references/workflow-formal-orchestrate.md` 中的 verdict 表）。

## Step 3：Cross-Conversation Resume

→ `references/workflow-infrastructure.md`（检测活跃运行 + Source Stability + 恢复 Infrastructure）

## Steps 4-6：Infrastructure Setup

→ `references/workflow-infrastructure.md`（Scope Contract + Git Checkpoint + Budget File）

## Steps 7-14：Route 1 — Formal Orchestrate

→ `references/workflow-formal-orchestrate.md`（Discovery → Plan Writing → Execution → Final Review + 每 phase 的 verdict 路由 + Direct Repair mini-route + Budget 更新）

## Steps 15-18：Route 2 — Bug Investigation

→ `references/bug-investigation-route.md`（dispatch analyst → handle return → Codex review / worker dispatch → Closing）

## Steps 19-20：Route 3 — Multi-PR Merge

`Skill({ skill: "orchestrate-multi-pr-merge" })`。

| Multi-PR Merge Verdict | Coordinator 动作 |
| --- | --- |
| `MERGE_COMPLETE` | Closing |
| `NEEDS_DISCOVERY` | analyst 发现设计/意图冲突 → 回到 Discovery |
| `NEEDS_USER_DECISION` | 冲突解决需要用户决策 → 询问用户 → 拿到决策后重新进入 |
| `BLOCKED` | 报告用户 |

## Steps 21-24：Closing

→ `references/workflow-closing.md`（Final Verification + Push + PR + Report + Cleanup）

---

## Global Constraints

**Hard Gates**：没有验证证据不得声称完成 / 没有 design document 不跳到 plan / 每 phase review 不可跳过 / upstream 结论必须写回再继续 / 不存在非阻塞项。

**Sub-agent 隔离**：dispatch prompt 必须自足。Sub-agent 不读 SKILL.md、不读 references/。Agent frontmatter `skills:` 自动预加载指定 skill。

**Commit 纪律**：Sub-agent 不 commit。Coordinator 在 review 通过后统一提交。Design/plan repair、Task Pack、finding repair 分别提交。不 stage 非当前 scope 文件。

**禁止**：跳过 Discovery / Plan Review / Final Review / 用技术语言汇报 / 自己写生产代码 / 每 task 一个 sub-agent / 超循环上限不处理。
