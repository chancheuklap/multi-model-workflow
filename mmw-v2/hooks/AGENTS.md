# mmw-v2/hooks

跨宿主纪律注入层：MMW 的第三类交付物（spec `docs/specs/discipline-hooks/discipline-hooks.md`，决定见 ADR 0021）。三类事件——开场注入、subagent 注入、完成拦截——由 `install.sh` 装进五个宿主。零第三方依赖，只用 Node 内置模块。

## 文件

| 文件 | 干什么 | 原件 |
| --- | --- | --- |
| `mmw-hooks.json` | 共享 hook JSON，Claude 与 Codex 同 schema；`${MMW_HOOKS_ROOT}` 由 `install.sh` 换成本目录绝对路径，并给每条命令加 `--host <宿主>` | ponytail `hooks/claude-codex-hooks.json` |
| `mmw-activate.js` | SessionStart：注入 `discipline/worker.md` | ponytail `hooks/ponytail-activate.js` |
| `mmw-subagent.js` | SubagentStart：默认注入工人块；`agent_type` 命中 `MMW_VERIFIER_MATCHER`（默认 `verifier`）注入复验者块；`MMW_SUBAGENT_MATCHER` 可限定只注入哪些 agent 类型 | ponytail `hooks/ponytail-subagent.js` |
| `mmw-stop.mjs` | Stop：worktree 根有 `.mmw-ticket-state.json` 且有 `kind` 不为 `manual` 的 `checked:false` gate 就顶回；同一会话连续 6 次顶回而关卡集合无变化则放行；文件缺失、解析失败、stdin 超时一律放行 | unlazy `scripts/stop-hook.mjs` |
| `lib/state.mjs` | Stop 用的 sha256、原子写、文件锁；状态落在被拦仓库的 `.mmw-hook-state.json` 与 `.mmw/locks/` | unlazy `scripts/lib/gates.mjs` |
| `mmw-runtime.js` | 分流：按 `--host` 与环境变量判宿主，输出各家的 JSON 形状 | ponytail `hooks/ponytail-runtime.js` |
| `mmw-instructions.js` | 按角色读 `discipline/<role>.md` | ponytail `hooks/ponytail-instructions.js` |
| `discipline/worker.md`、`discipline/verifier.md` | 注入正文；每条逐字取自 `docs/specs/landing-closeout/discipline-sources.md`，条目后一行写出处 | — |
| `pi-extension/` | pi 扩展：`before_agent_start` 返回追加了工人块的系统提示 | ponytail `pi-extension/index.js` |
| `check-invariants.js` + `invariants.json` | 承重句校验：清单里每条短语逐字存在于每个权威位置；`install.sh --check` 顺带跑 | ponytail `scripts/check-rule-copies.js` |
| `hooks-config.py` | 给 `install.sh` 用：把三条 hook 合并进宿主配置文件、只读比对、摘退役条目 | — |

原件 commit：ponytail @2ed6c52，unlazy @265fbd5。改原件只做 spec 点名的精确修改，每处在文件头注释列出。

## 命令

| 命令 | 干什么 |
| --- | --- |
| `bash mmw-v2/hooks/tests/run.sh` | 跑全部测试（注入形状、完成拦截正反例、承重句自证、临时根安装） |
| `node mmw-v2/hooks/check-invariants.js` | 只跑承重句校验 |

## 关键约定

- 注入内容只增删 `discipline/*.md`，且每条要带存档出处；改承重句先改 `invariants.json`，否则 `--check` 先红。
- `invariants.json` 里 `files` 为空、带 `pending` 的条目是占位，校验只报告不判红；权威位置落地后填入短语与路径。
- 每个脚本都要 fail-open：stdin 读取带超时、任何异常都放行。Stop 的判定物契约（`.mmw-ticket-state.json` 的字段）与 landing-closeout 的 implement 共享，改一边要改另一边。人工关卡（`kind: "manual"`）由裁决人清，不属于工人的收尾条件，拦截不计入它。
- 宿主判定：Grok 给 hook 进程设 `GROK_HOOK_EVENT`，优先；其余靠 `install.sh` 写进命令行的 `--host`。用户级 hook 下 Codex 与 Cursor 不设可辨识的环境变量。

## 陷阱

- Cursor 的 stop 响应只有 `followup_message`，没有 `decision`；Grok 的 SessionStart / SubagentStart 是被动事件，输出不进模型（开场靠 `~/.grok/rules/` 的规则文件）。
- Grok 对 `~/.claude/settings.json`、`~/.cursor/hooks.json` 的兼容扫描在本机是关的（`[compat.*] hooks = false`），所以 `install.sh` 另给 `~/.grok/hooks/` 写一份。
- 测试里用 fifo 模拟「stdin 永不关闭」；脚本必须在 1 秒内自己退出，否则宿主会话冻死（ponytail #443）。
