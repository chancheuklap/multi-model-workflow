# multi-model-workflow

本仓库保存同一套编排思想的两个源码入口：

- `plugin/`：上游插件源码和行为蓝本，只读对照。
- `codex-orchestrate-new/`：Codex 原生 plugin 源码权威。

旧 Codex 实现保留在 `codex-orchestrate/`，只作为迁移前版本参考，不再作为当前 runtime 依据。更早的旧实现归档在 `archive/2026-05-24-codex-pre-atomic/`。

## Codex 当前权威

| 层级 | Source | Runtime |
| --- | --- | --- |
| Plugin manifest | `codex-orchestrate-new/.codex-plugin/plugin.json` | 安装后缓存：`~/.codex/plugins/cache/multi-model-workflow/multi-model-workflow/<version>/` |
| Skills | `codex-orchestrate-new/skills/` | plugin cache skills |
| Custom agents | `codex-orchestrate-new/agents/*.toml` | `~/.codex/agents/*.toml` + `~/.codex/config.toml` `[agents.<name>]` |
| Hooks | `codex-orchestrate-new/hooks.json`、`codex-orchestrate-new/hooks/*.sh` | plugin cache hooks |
| Review dispatch | `codex-orchestrate-new/skills/_shared/review-dispatch.md`、`codex-orchestrate-new/scripts/dispatch-review.sh`、`codex-orchestrate-new/scripts/complete-review-dispatch.sh` | plugin cache skills + scripts |
| Execution | `codex-orchestrate-new/skills/orchestrate-execution/`、`codex-orchestrate-new/agents/pack_executor.toml`、`codex-orchestrate-new/agents/complex_pack_executor.toml` | Codex custom agents |
| State schema | `codex-orchestrate-new/state-schema/` | plugin cache schemas |

不要重建 `.agents/skills/orchestrate-*`，也不要从归档 `codex/` 或旧 `codex-orchestrate/` 推导当前行为。

## 运行形态

```text
orchestrate-workflow
  -> orchestrate-discovery
  -> orchestrate-plan-writing
  -> orchestrate-execution
  -> orchestrate-final-review
  -> orchestrate-workflow closing
```

`orchestrate-workflow` 是 coordinator 入口。Formal work 依次走 discovery、plan writing、execution、final review 和 closing。Light、direct-repair、bug-investigation、multi-pr-merge 由 `routes-v1.json` 管理。

Codex 派发使用：

- `spawn_agent`
- `resume_agent`
- `send_input`
- `wait_agent`
- `close_agent`

Review 统一派 `codex_reviewer`；执行按 Plan risk 派 `pack_executor` 或 `complex_pack_executor`。

## 验证

```bash
bash codex-orchestrate-new/build/build.sh --check --plugin-dir codex-orchestrate-new
bash codex-orchestrate-new/scripts/run-all-tests.sh
bash codex-orchestrate-new/scripts/verify-maturity.sh codex-orchestrate-new
bash codex-orchestrate-new/scripts/validate-plugin-contract.sh codex-orchestrate-new
```

如果系统级 validator 拒绝 `.codex-plugin/plugin.json` 的 `hooks` 字段，不代表本仓库 manifest 错误。Codex Orchestrate 的 manifest 必须声明 `"hooks": "./hooks.json"`；此时以 build check、run-all-tests、verify-maturity 和本仓库 plugin contract validator 作为 source 验证。

## 安装

Source 覆盖审计完成后再执行安装；不要用安装动作替代复刻验收。

本仓库通过 repo-local marketplace 暴露 `codex-orchestrate-new/`，入口是 `.agents/plugins/marketplace.json`。

```bash
codex plugin marketplace list
codex plugin list --marketplace multi-model-workflow
codex plugin add multi-model-workflow@multi-model-workflow
bash codex-orchestrate-new/scripts/verify-runtime-parity.sh codex-orchestrate-new
```

安装后还要在新的 Codex session 里 review/trust plugin hook definitions，并确认 SessionStart 输出当前 plugin root、active run 和 hook context。
