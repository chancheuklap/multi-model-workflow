# Custom Agents

## Agent Roles

| 场景 | subagent_type | model（prompt 中指定） |
| --- | --- | --- |
| baseline review (design/plan/pack/final) | `codex:codex-rescue` | GPT-5.4 |
| release-risk gate | `codex:codex-rescue` | GPT-5.5 |
| plan 写作（design + issues → plan） | `plan-writer` | claude-opus-4-7[1m] |
| 普通 Task Pack / 普通 repair | `pack-executor` | sonnet |
| 高风险 Task Pack / 高风险 repair | `complex-pack-executor` | opus |
| 多模块调查 / unknown root cause (只读) | `complex-code-explorer` | opus |
| 窄范围代码问题 | `code-explorer` | sonnet |
| repair round 2 仍失败 / Bug Investigation 入口 / Multi-PR 系统性冲突 | `root-cause-analyst` | claude-opus-4-7[1m] |
| 低风险文档整理 | `docs-worker` | sonnet |

## 通信架构

Hub-and-spoke。Sub-agent 之间不直接通信。SendMessage 需要 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`；未设时退化为新建 agent。

| 路径 | 机制 | 时序 |
| --- | --- | --- |
| Design Review finding | coordinator 直接修设计文档 | — |
| Plan Review finding — 框架性 | coordinator 直接修 plan | — |
| Plan Review finding — Task Pack 内容 | SendMessage 原 plan-writer；未启用时新建 plan-writer | SendMessage 异步；Agent 同步 |
| Plan 写作（首次） | Agent 派发 plan-writer | 同步 |
| Execution / Final Review — 简单 finding（≤ 2 文件、意图明确） | coordinator 直接修 | — |
| Execution / Final Review — 复杂 finding | SendMessage 原 worker；未启用时新建同类 agent | SendMessage 异步（等通知），Agent 同步 |
| codex:codex-rescue | 每次全新 task | 同步 |
| root-cause-analyst | 始终新建 | 同步 |

**上下文连续**：同一 pack 内 review → 修复用 SendMessage（保留上下文）；plan review 修订用 SendMessage 复用 plan-writer（保留 design + issue 上下文）；跨 pack / 新问题用 Agent 新建。SendMessage 后等通知再继续，不串同步逻辑。
