# agents 规则

- Agent 文件是 Codex custom agent TOML 模板。
- 每个 agent 必须定义 `name`、`description`、`developer_instructions`。
- 使用 Codex 可用字段：`model`、`model_reasoning_effort`、`sandbox_mode`、`skills.config`、`nickname_candidates`；不要保留 Claude frontmatter。
- 普通 worker / explorer 使用 `gpt-5.3-codex` + `xhigh`。
- 高级 worker / explorer 使用 `gpt-5.5` + `high`。
- `plan_writer` 和 `root_cause_analyst` 使用 `gpt-5.5` + `xhigh`。
- 不使用 `gpt-5.4-mini`。
- Agent 指令必须从 `plugin/agents/*.md` 的正文机械迁移，保留原有纪律、模式、return contract 和 voice-directive，只替换必要的 Codex host API。
