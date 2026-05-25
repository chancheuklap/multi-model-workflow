# multi-model-workflow

本仓库保存两套边界清楚的编排系统：

- `plugin/`：Claude Code plugin 源码，也是行为蓝本。
- `codex-orchestrate/`：Codex 原生插件复刻源码。

旧 Codex 实现已经归档到 `archive/2026-05-24-codex-pre-atomic/`，不再作为当前 runtime 依据。

## Codex 当前权威

| 层级 | Source | Runtime |
| --- | --- | --- |
| Plugin manifest | `codex-orchestrate/.codex-plugin/plugin.json` | 安装后缓存：`~/.codex/plugins/cache/multi-model-workflow/multi-model-workflow/3.6.2/` |
| Skills | `codex-orchestrate/skills/` | plugin cache skills |
| Custom agents | `codex-orchestrate/agents/*.toml` | `~/.codex/agents/*.toml` + `~/.codex/config.toml` `[agents.<name>]` |
| Hooks | `codex-orchestrate/hooks.json`、`codex-orchestrate/hooks/*.sh` | plugin cache hooks |
| Review lane | `codex-orchestrate/skills/codex-review/SKILL.md`、`codex-orchestrate/scripts/validate-review-dispatch.sh`、`codex-orchestrate/scripts/record-review-dispatch.sh`、`codex-orchestrate/scripts/complete-review-dispatch.sh` | plugin cache skill + scripts |
| Worktree execution | `codex-orchestrate/scripts/dispatch/` | plugin cache scripts |
| State schema | `codex-orchestrate/state-schema/` | plugin cache schemas |

不要重建 `.agents/skills/orchestrate-*`，也不要从归档 `codex/` 推导当前行为。

## 运行形态

```text
orchestrate-workflow
  -> orchestrate-discovery
  -> orchestrate-plan-writing
  -> orchestrate-execution
  -> orchestrate-final-review
  -> orchestrate-workflow closing
```

Route 2 处理未知根因 bug。Route 3 处理多 PR merge。`codex-review` skill 作为 review lane 入口保留。

## 验证

```bash
bash codex-orchestrate/scripts/run-all-tests.sh
bash codex-orchestrate/scripts/verify-maturity.sh
bash codex-orchestrate/scripts/validate-plugin-contract.sh codex-orchestrate
bash codex-orchestrate/build/build.sh --check --plugin-dir codex-orchestrate
```

如果当前系统级 `validate_plugin.py` 拒绝 `.codex-plugin/plugin.json` 的 `hooks` 字段，不要为了通过旧 validator 删除 hooks。Codex Orchestrate 的 manifest 必须声明 `"hooks": "./hooks.json"`；此时以 `verify-maturity.sh`、`run-all-tests.sh` 和 build check 作为 source 验证。

## 安装

Source 覆盖审计完成后再执行安装；不要用安装动作替代复刻验收。
本仓库通过 repo-local marketplace 暴露 `codex-orchestrate/`，入口是 `.agents/plugins/marketplace.json`。
安装后还要在新 Codex session 里 review/trust plugin hook definitions，并确认 SessionStart 输出 `codex-orchestrate` runtime active。

```bash
codex plugin marketplace list
codex plugin list --marketplace multi-model-workflow
codex plugin add multi-model-workflow@multi-model-workflow
rsync -ain --delete codex-orchestrate/ ~/.codex/plugins/cache/multi-model-workflow/multi-model-workflow/3.6.2/
bash codex-orchestrate/scripts/verify-runtime-parity.sh codex-orchestrate
```
