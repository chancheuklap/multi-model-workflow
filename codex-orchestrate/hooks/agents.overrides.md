# hooks 规则

- Hooks 必须使用 Codex lifecycle event payload 和 Codex hook 输出 schema。
- 不依赖 Claude hook `if` 表达式，也不把 Claude 子代理 payload 当成 Codex 事实。
- `SubagentStart` 只在 Codex payload 暴露 `message`、`prompt` 或 text items 时校验 DISPATCH_ENVELOPE；payload 不暴露调度正文时，只注入上下文并要求 Coordinator 已通过 `dispatch-gateway.sh` 显式校验。
- 需要顺序时，只注册一个 event dispatcher，在 dispatcher 内按固定顺序运行各 guard/helper。
- Hook 脚本必须幂等，写共享状态前必须拿锁。
- Hook manifest 固定为本目录 `hooks.json`；不要再新增根目录重复 manifest。
