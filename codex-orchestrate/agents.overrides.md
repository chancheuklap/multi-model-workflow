# codex-orchestrate override

- `codex-orchestrate/` 是本 workflow 的 Codex-native source。除非为了 Codex 执行必须改造，否则要保留从蓝本迁移来的 phase、gate、state、review、worker 和 closing 合同。
- 不要在这里发明新的 workflow 行为。改动必须能追溯到宿主迁移、合同保真或已确认的 runtime 缺口。
- Runtime 指令必须使用 Codex-native executable paths、state paths、agent fields 和 review dispatch。不要留下旧宿主 compatibility fallback 或双宿主入口。
- Codex source 里的文档、skill、reference、agent 指令、template 和面向用户 / agent 的文字以中文为主。英文只保留必要的命令、路径、协议字段、工具名、代码标识符、API 名称和不可翻译的宿主术语。
- Codex source text 不要描述旧宿主 tool-name labels；直接表达需要执行的 Codex 动作。
- `.codex-plugin/plugin.json` 必须通过 `"hooks": "./hooks.json"` 声明 bundled hooks，确保 runtime installation 能加载 hook manifest。
- 声称 plugin 可用之前，必须让 source、installed plugin cache、custom agent runtime 和 user config 的 parity 可验证。
- Ad-hoc review skills 必须通过 `spawn_agent` 和 `wait_agent` 派发原生 `codex_reviewer` subagent；不要增加外部 review runners。
- Orchestrated review references 必须使用 `.codex/multi-model-workflow/review-*`、`review-registry/`、reviewer `.agent-id` files、`spawn_agent`、`send_input` 和 `wait_agent`；不要描述 job-id polling。
- Dispatch validation 放在 Coordinator 显式调用的 scripts 里，并且发生在 `spawn_agent` / `send_input` 之前；这些 scripts 可以 gate prompt envelope，但不能执行 review，也不能替代 subagents。
- Review result bookkeeping 放在 dispatch 和 result persistence 之后由 Coordinator 显式调用的 scripts 里；`record-review-dispatch.sh` 记录真实 reviewer agent，`complete-review-dispatch.sh` 把 durable result file 和 exactly-once review budget increment 绑定起来。
- Coordinator delegation 有 ownership 语义：任务派给 subagent 后，Coordinator 不得并行重复做同一个 investigation、implementation 或 review。只能做不重叠的协调工作，然后等待 assigned agent。除非用户取消任务或正式 workflow 已经到达真实 BLOCKED 状态，不要 interrupt、close 或 pressure running agents 要求 partial output。
- 当前 workflow state paths 是 `.codex/multi-model-workflow/*`。不要把新的 runtime 指令写到旧宿主 state paths。
- Worktree 指令必须具体且可执行：在 `${CODEX_HOME:-$HOME/.codex}/worktrees/<4-hex-id>/<repo-name>` 下用 `git worktree add -b` 创建 Git worktree，不使用 UI-only steps、pseudo tools 或自定义根目录。创建 worktree 前不要切换 main repository branch。
- `architecture-draft.md` 是 Codex source architecture authority。保持中文，并保留足够细节，能审计 workflow routes、state files、document artifacts、subagents、hooks、scripts、tests 和 Codex-specific runtime rulings。
- Architecture documentation 必须反映当前 runtime/source tree。不要为了让 architecture draft 看起来一致而改 runtime contracts、state machines、templates、hooks 或 agent dispatch 行为；runtime behavior changes 需要独立 commit 和 end-to-end evidence。
