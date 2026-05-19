# CLAUDE.md

多模型开发工作流系统。当前 Codex runtime 是主权威；Claude plugin 源只作为上游形态或兼容来源。

## 当前 Codex Source

- `.agents/skills/orchestrate-workflow/`
- `.agents/skills/orchestrate-discovery/`
- `.agents/skills/orchestrate-plan-writing/`
- `.agents/skills/orchestrate-execution/`
- `.agents/skills/orchestrate-final-review/`
- `.agents/skills/orchestrate-multi-pr-merge/`
- `codex/agents/*.toml`
- `codex/hooks/`
- `codex/skills/`
- `codex/reviewers/`

旧 Codex V1 已归档到 `archive/2026-05-20-codex-v1/`。

## Runtime Pipeline

```text
Entry Gate
  -> Discovery + Design Review
  -> to-issues
  -> Plan Writing + Plan Review
  -> Execution + Pack Review + Repair + Early Release Gate
  -> Final Review + Tail Sweep + Final Release Gate
  -> Closing
```

Bug route 先派 `root_cause_analyst`。Multi-PR route 进入 `orchestrate-multi-pr-merge`。

## Runtime Rules

- Runtime 文件只写可执行指令，不写迁移背景或来源说明。
- Sub-agent dispatch 必须自足；custom agent 不依赖它看不到的 `SKILL.md` 或 reference。
- Agent 定义是角色行为权威；dispatch template 只写本次场景信息。
- Baseline review 用 `code_reviewer`；release-risk supplement 用 `release_reviewer`。
- Claude cross-model review 需要按 `orchestrate-workflow/references/external-review-lanes.md` 选 lane。订阅额度路径优先用 `codex/reviewers/claude-subscription-review.sh`，并固定调用 `claude-opus-4-7` + `--effort high`；`claude -p` 是 Agent SDK / Extra Usage fallback，必须显式授权。
- 运行态 scope / budget 文件在 `.codex/multi-model-workflow/`。
- 改 Codex source 后同步 user-level runtime 并用 diff 验证。

## Sync

```bash
bash codex/skills/install-orchestrate-runtime.sh --user --apply
bash codex/agents/sync-agents.sh --apply --update-config
bash codex/hooks/install-hooks.sh --apply
```

## Verification

```bash
bash -n codex/skills/install-orchestrate-runtime.sh
bash -n codex/agents/sync-agents.sh
bash -n codex/hooks/install-hooks.sh
bash -n codex/hooks/cleanup-run-state.sh
bash -n codex/reviewers/claude-subscription-review.sh
bash -n codex/reviewers/claude-review.sh
python3 -m json.tool codex/hooks/hooks.json >/dev/null
rg -n "codex-rescue|SendMessage|Agent tool|CLAUDE_PLUGIN_ROOT|\\.claude/multi-model-workflow" .agents/skills codex
```

## Historical Sources

- `plugin-v2/` is the Claude Code Plugin V2 source that shaped the current Codex runtime.
- `plugin/` is the older Claude plugin compatibility tree.
- `archive/2026-05-20-codex-v1/` preserves the previous Codex source.

Do not use historical sources to infer live Codex behavior.
