# Codex Agent Templates

Sync templates to `~/.codex/agents/`:

```bash
bash codex/agents/sync-agents.sh --dry-run
bash codex/agents/sync-agents.sh --apply
```

## Agents

| Agent | Model | Sandbox | Role |
| --- | --- | --- | --- |
| `coding_worker` | gpt-5.3-codex | workspace-write | 普通 Task Pack / 测试修复 / 局部重构 |
| `complex_coding_worker` | gpt-5.5 | workspace-write | 高风险 Task Pack（migration / billing / auth / permission / runtime / shared contract） |
| `code_reviewer` | gpt-5.4 | read-only | Baseline review（design / plan / pack / final intent） |
| `release_reviewer` | gpt-5.5 | read-only | Release-risk gate（数据 / 权限 / 账务 / 迁移 / 部署 / 回滚） |
| `code_explorer` | gpt-5.3-codex | read-only | 窄范围文件 / 符号 / 调用链查询 |
| `complex_code_explorer` | gpt-5.4 | read-only | 多模块调查 / root-cause investigation |
| `docs_worker` | gpt-5.4 | workspace-write | 低风险文档整理 / issue 文案草稿 |

## Key Contracts

- Sub-agent 不读 Orchestrate SKILL.md 或 references。Parent dispatch prompt 必须自足。
- 所有 sub-agent 按 parent dispatch 指定的 Return Contract 返回。Routing 是 coordinator 的职责，sub-agent 只报告 Verdict。
- Return Contract 和 Finding Shape 的权威定义在 `orchestrate-workflow/references/dispatch-primitives.md`。

## Repair Routing（Coordinator 视角）

Codex reviewer 返回 findings 后，coordinator（Claude Code 主线程）按修复分流规则处理：

| 场景 | Coordinator 动作 |
| --- | --- |
| Phase 0（Design / Plan）finding | Coordinator 直接修复（Design / Plan 是它写的） |
| Phase A/B 简单 finding（≤ 2 文件、意图明确） | Coordinator 直接修复 |
| Phase A/B 复杂 finding | SendMessage 给原 Claude Code worker（保留实现上下文）；不可用时新建同类 worker |
| 根因不明 | 新建 root-cause-analyst |

Codex reviewer 不需要知道修复由谁执行——只需按 Finding Shape 格式报告问题。
