# Codex Orchestrate

`codex-orchestrate/` 是 `plugin/` 这套 Claude Code 编排插件的 Codex 原生复刻源码。

运行合同：

- Codex 插件 manifest：`.codex-plugin/plugin.json`
- Coordinator skills：`skills/orchestrate-*`，并包含 `skills/codex-review`
- Codex custom agents：`agents/*.toml`，安装时同步注册到 `~/.codex/config.toml` `[agents.<name>]`
- Agent 人设源：`agents/persona.md`
- Codex plugin hook manifest：`hooks/hooks.json`
- Hook 源码：`hooks/*.sh`
- 持久状态：`.codex/multi-model-workflow`
- Worktree 执行和恢复：`scripts/dispatch/worktree-exec.sh` / `scripts/dispatch/worktree-resume.sh`；运行时读取 `agents/<agent_role>.toml` 并注入 model、reasoning、sandbox、developer instructions 和 enabled skills，修复时通过 `codex exec resume <worker_thread_id>` 回到原 worker thread
- Native Codex Review：`scripts/review/review-lane.sh`
- 安装与 parity 验证：`installers/`

当前 package 不依赖旧 repo 根目录的 `codex/` 实现；旧实现只保留在 `archive/2026-05-24-codex-pre-atomic/` 供审计。

## 模型路由

| 角色 | 模型 | reasoning |
| --- | --- | --- |
| `pack_executor` | `gpt-5.3-codex` | `xhigh` |
| `code_explorer` | `gpt-5.3-codex` | `xhigh` |
| `docs_worker` | `gpt-5.3-codex` | `xhigh` |
| `complex_pack_executor` | `gpt-5.5` | `high` |
| `complex_code_explorer` | `gpt-5.5` | `high` |
| `plan_writer` | `gpt-5.5` | `xhigh` |
| `root_cause_analyst` | `gpt-5.5` | `xhigh` |
| 文档 review | `gpt-5.5` | `xhigh` |
| 代码 / final / integration / release-risk review | `gpt-5.4` | `xhigh` |

`gpt-5.4-mini` 不用于本 workflow。

## 验证

```bash
bash codex-orchestrate/scripts/run-all-tests.sh
bash codex-orchestrate/scripts/verify-maturity.sh
bash codex-orchestrate/build/build.sh --check --plugin-dir codex-orchestrate
uv run --with pyyaml --no-project \
  python ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  codex-orchestrate
```

## 安装

Source 覆盖审计完成后再安装；安装脚本会复制 agent TOML、注册 `[agents.<name>] config_file`，并做 parity 验证。
安装后还要在新 Codex session 里 review/trust plugin hook definitions，并确认 SessionStart 输出 `codex-orchestrate` runtime active。

```bash
bash codex-orchestrate/installers/install.sh --user --apply
bash codex-orchestrate/installers/verify-runtime-parity.sh --user
```
