# state-schema 规则

- Schema 定义 hooks、dispatch scripts 和 coordinator skills 共同使用的 durable state contract。
- 新 runtime JSON 文件成为 gate 的一部分之前，必须先有 schema。
- worktree-exec worker 必须记录 `worker_thread_id` / `worker_job_file`，让 repair 可以通过 `codex exec resume <thread_id>` 回到原 worker context。
- 同一版本内的 schema 修改必须保持兼容；不兼容时创建新的 `*-vN.json`。
