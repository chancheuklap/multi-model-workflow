# mmw-v2/agents

自研 subagent。不负责技能。

## 关键约定

- `body.md` 是正文，`agent.json` 是 name、description 与五宿主各自的模型和工具；`mmw-v2/agents/<名>/out/` 是装配成品，进 git。description 写给主线程（何时派、prompt 装什么），`body.md` 写给 subagent（怎么答）。全部 subagent 都只读（`assemble.py` 把 cursor 的 `readonly`、codex 与 grok 的 sandbox 写死为只读）。
- 改 `body.md` 或 `agent.json` 后先跑 `python3 mmw-v2/agents/assemble.py`，再跑 `bash mmw-v2/install.sh --check`；宿主读的是那个 `out` 目录。
- `agent.json` 五个宿主键（`claude`、`cursor`、`codex`、`grok`、`pi`）缺一不可；只有 `claude` 和 `pi` 需要 `tools` 字段。grok 一家出两个成品：`grok.md` 进 `~/.grok/agents/`，`grok.role.toml` 进 `~/.grok/roles/`。

## 陷阱

- `body.md` 里不能出现 `'''`，`assemble.py` 会直接报错而不是生成坏的 `codex.toml`。
- `assemble.py` 不删 out 目录里的旧文件；源不再产出的文件报「多余」并退出 1，人工删。
