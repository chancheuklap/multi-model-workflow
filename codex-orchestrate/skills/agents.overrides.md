# skills 规则

- Skills 是面向 coordinator 的 Codex workflow 入口。
- Skill 正文只能把 `plugin/` 当作来源说明；runtime 指令必须使用 Codex primitive。
- Phase skill 不能假设 subagent 会自动读取 hidden references。Dispatch prompt 必须包含路径或关键合同正文。
- 所有 state、review、run-summary 路径统一使用 `.codex/multi-model-workflow`。
