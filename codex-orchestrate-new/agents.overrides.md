# codex-orchestrate-new override

- `codex-orchestrate-new/` 是当前 Codex-native source。除非用户明确要求上游插件工作，不要修改 `plugin/`。
- 不要在这里发明新的 workflow 行为。改动必须能追溯到宿主迁移、合同保真、已确认的 runtime 缺口或用户明确需求。
- Runtime 指令必须使用 Codex-native executable paths、state paths、agent fields 和 review dispatch。
- Codex source 里的文档、skill、reference、agent 指令、template 和面向用户 / agent 的文字以中文为主。英文只保留必要命令、路径、协议字段、工具名、代码标识符、API 名称和不可翻译的宿主术语。
- `.codex-plugin/plugin.json` 必须通过 `"hooks": "./hooks.json"` 声明 bundled hooks。
- `architecture-draft.md` 是 Codex source architecture authority。保持它与 live source、state schema、hooks、scripts、agents 和 build templates 一致。
- 派发必须使用 `spawn_agent`、`resume_agent`、`send_input`、`wait_agent`、`close_agent` 和已注册的 TOML custom agents。
- Review work 由 `codex_reviewer` 承担。Orchestrated review references 必须使用 `.codex/multi-model-workflow/review-*`、`review-registry/`、`dispatch-review.sh`、`complete-review-dispatch.sh` 和 `record-review-disposition.sh`。
- Dispatch validation 放在 Coordinator 显式调用的 scripts 里，并且发生在 `spawn_agent` / `send_input` 之前。
- Review result bookkeeping 放在 result persistence 之后，由 `complete-review-dispatch.sh` 把 durable result file 和 exactly-once review budget increment 绑定起来。
- Review Budget 默认是硬停。只有用户明确授权继续 review 时，Coordinator 才能在 validate 和 complete 两步同时传 `--allow-over-budget --override-reason "<授权原因>"`。
- 当前 workflow state paths 是 `.codex/multi-model-workflow/*`。不要给旧 runtime 加 fallback。
- Coordinator delegation 有 ownership 语义：任务派给 subagent 后，Coordinator 不得并行重复做同一个 investigation、implementation 或 review。
- Coordinator 必须管理 subagent 生命周期：`wait_agent` 返回 final status 且结果已保存/写入 state 后立即 `close_agent`；续修先 `resume_agent` 再 `send_input`。
- Pack、review repair、plan doc 和 workflow rule 改动必须按真实完成边界及时 commit。不要把多个 pack、多个 phase 或多轮修复堆到 closing 前统一提交。
- 文档、规则、计划、prompt-only 改动只做有证明力的验证：format、build check、manifest、schema、路径链接、maturity gate 或人工可审查 diff。
