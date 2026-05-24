# dispatch 规则

- Dispatch scripts 是 Task Pack worker 执行的强制入口。
- 写代码的 Task Pack 必须使用 managed git worktree 和 durable pack return。
- `worktree-exec.sh` 必须读取 `agents/<agent_role>.toml`，并把 model、reasoning effort、sandbox、developer instructions 和 enabled skills 注入 `codex exec`。
- `worktree-exec.sh` 必须保存 Codex `thread_id`；worktree repair 必须通过 `worktree-resume.sh` 调用 `codex exec resume <thread_id>`，不得重开 worker 伪装成恢复。
- Replacement dispatch 必须带 exception code、原始上下文和已记录原因。
