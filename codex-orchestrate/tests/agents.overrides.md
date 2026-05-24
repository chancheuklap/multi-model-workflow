# tests 规则

- Tests 必须使用 Codex-shaped fixtures 覆盖 hook 和 dispatch。
- Tests 必须能在不全局安装 plugin 的情况下运行。
- Smoke tests 验证 behavior contract，不只检查文件是否存在。
- Worktree dispatch tests 必须覆盖 agent TOML 注入、thread_id 持久化和 `worktree-resume.sh` 的 dry-run 恢复路径。
- Hook manifest 测试只验证 `hooks/hooks.json`；根目录不再保留重复 `hooks.json`。
