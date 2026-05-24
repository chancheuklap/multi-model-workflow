# tests 规则

- Tests 必须使用 Codex-shaped fixtures 覆盖 hook、review lane 和 state contract。
- Tests 必须能在不全局安装 plugin 的情况下运行。
- Smoke tests 验证 behavior contract，不只检查文件是否存在。
- Worker dispatch tests 必须覆盖 DISPATCH_ENVELOPE 校验、agent_id 持久化和 send_input/resume_agent 恢复合同。
- Hook manifest 测试只验证 `hooks/hooks.json`；根目录不再保留重复 `hooks.json`。
