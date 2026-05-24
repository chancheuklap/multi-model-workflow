# installers 规则

- Installer 只管理 `codex-orchestrate` 拥有的文件。
- Installer 必须同时提供 dry-run 和 apply 模式。
- 安装后必须做 runtime parity verification。
- Uninstaller 只能删除本插件管理的 runtime 文件和 config entry。
- Custom agent 安装必须同时复制 `~/.codex/agents/*.toml` 并在 `~/.codex/config.toml` 写入本插件托管的 `[agents.<name>] config_file` block；不要假设 Codex 自动发现裸 TOML。
