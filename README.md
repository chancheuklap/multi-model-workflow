# multi-model-workflow

本仓库保存同一套编排思想的两个源码入口：

- `plugin/`：上游插件源码和行为蓝本，只读对照。
- `codex-orchestrate-new/`：Codex 原生 plugin 源码权威。

当前 Codex runtime 只以 `codex-orchestrate-new/` 为 source；旧源码树不得作为当前行为依据。

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

Custom agent TOML 是 sub-agent 必需 skill 的注册面。执行、根因、计划和审查 agent 必须用 `[[skills.config]]` 绑定各自必需的 skill，并在 `developer_instructions` 的 `Skill 调用` 段写明何时调用；不要依赖父线程、全局 hook 或自然语言提示隐式传递。

当前必需绑定：

| Agent | Required skills |
| --- | --- |
| `pack_executor` | `ponytail`, `tdd`, `diagnose`, `prototype`, `frontend-testing-debugging` |
| `complex_pack_executor` | `ponytail`, `tdd`, `diagnose`, `improve-codebase-architecture`, `prototype`, `frontend-testing-debugging` |
| `root_cause_analyst` | `ponytail`, `diagnose`, `tdd` |
| `plan_writer` | `ponytail`, `improve-codebase-architecture` |
| `codex_reviewer` | `ponytail-review` |
| `codex_planning_reviewer` | `ponytail`, `improve-codebase-architecture` |
| `complex_code_explorer` | `improve-codebase-architecture` |

## 验证

```bash
bash codex-orchestrate-new/build/build.sh --check --plugin-dir codex-orchestrate-new
bash codex-orchestrate-new/scripts/run-all-tests.sh
bash codex-orchestrate-new/scripts/verify-maturity.sh codex-orchestrate-new
bash codex-orchestrate-new/scripts/validate-plugin-contract.sh codex-orchestrate-new
bash codex-orchestrate-new/scripts/verify-agent-skill-bindings.sh codex-orchestrate-new
```

如果系统级 validator 拒绝 `.codex-plugin/plugin.json` 的 `hooks` 字段，不代表本仓库 manifest 错误。Codex Orchestrate 的 manifest 必须声明 `"hooks": "./hooks.json"`；此时以 build check、run-all-tests、verify-maturity 和本仓库 plugin contract validator 作为 source 验证。

## 安装

Source 覆盖审计完成后再执行安装；不要用安装动作替代复刻验收。

本仓库通过 repo-local marketplace 暴露 `codex-orchestrate-new/`，source 入口是 `.agents/plugins/marketplace.json`。当前机器上的 Codex CLI marketplace discovery 可能不会自动列出 repo-local marketplace；`codex plugin marketplace list` 或 `codex plugin add` 不能作为完整安装证明。

完整 runtime 生效必须同时满足：

1. Codex app runtime 按 `.agents/plugins/marketplace.json` 安装 plugin，且版本化 cache 与 `codex-orchestrate-new/` 一致。
2. 7 个 custom agent TOML 已同步到 `~/.codex/agents/`，并写入 `~/.codex/config.toml`。
3. Bundled hooks 已在新的 Codex session 中 review/trust，hook trust records 已持久化。
4. 新 session 的 SessionStart 输出当前 plugin root、active run 和 hook context。

Agent 同步和 runtime parity 验证：

```bash
bash codex-orchestrate-new/agents/sync-agents.sh --apply --update-config
bash codex-orchestrate-new/scripts/verify-runtime-parity.sh codex-orchestrate-new
```

Runtime parity 会检查 `~/.codex/agents/*.toml` 与 source TOML 一致、必需 skill binding 存在，以及本机能解析到 Ponytail、TDD、diagnose、architecture、prototype 和 frontend testing skills。
