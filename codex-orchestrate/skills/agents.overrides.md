# skills 规则

- Skills 是面向 coordinator 的 Codex workflow 入口。
- Skill 正文只能把 `plugin/` 当作来源说明；runtime 指令必须使用 Codex primitive。
- Phase skill 不能假设 subagent 会自动读取 hidden references。Dispatch prompt 必须包含路径或关键合同正文。
- 所有 state、review、run-summary 路径统一使用 `.codex/multi-model-workflow`。
- Workflow 顶层工作树必须创建在 Codex 运行时目录 `$HOME/.codex/worktrees/<worktree-id>/<repo-name>` 下；不得使用 repo 邻近的临时工作树目录。
