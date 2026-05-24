# AGENTS.md

## 作用域

本文件给 Codex 在本仓库工作时使用。它只记录稳定边界、入口和验收规则；具体实现细节以 `README.md`、相关源码和 `codex-orchestrate/**/agents.overrides.md` 为准。

## 目录边界

| 路径 | 归属 | Codex 规则 |
| --- | --- | --- |
| `plugin/` | Clockwork 维护和使用的 plugin 源码 | 只读参考。可以用来对照结构、行为和迁移意图，但不能修改、格式化、构建、安装或把变更落到这里。 |
| `codex-orchestrate/` | Codex Orchestrate 源码 | Codex 的主工作区。skills、agents、hooks、scripts、state schema、build、manifest 的改动都应落在这里。 |
| `.agents/plugins/marketplace.json` | repo-local Codex marketplace | 只在 Codex 插件入口变化时改，默认 source path 必须指向 `./codex-orchestrate`。 |
| `docs/orchestrate/`、`atomic-codex-orchestrate-replication-plan.md` | 设计、计划、验收材料 | 改变流程、合同、验收口径或发布判断时同步更新。 |

## 工作规则

- 开工先确认改动属于 Codex Orchestrate，而不是 Clockwork plugin。
- 需要参考 `plugin/` 时只读必要文件；不要把 `plugin/` 当成 Codex runtime 真相。
- 从 `plugin/` 对照迁移时，必须翻译成 Codex-native 路径、hooks、subagent、state 和安装合同，不能保留旧宿主兼容兜底。
- 改 `codex-orchestrate/` 子目录时，同时检查同级或上级 `agents.overrides.md` 是否需要更新。
- 每个有意义的变更单独提交；不要把无关主题塞进同一个 commit。

## 验证入口

按改动面选择最小但真实的验证。涉及 Codex Orchestrate 行为时优先使用：

```bash
bash codex-orchestrate/build/build.sh --check --plugin-dir codex-orchestrate
bash codex-orchestrate/scripts/run-all-tests.sh
bash codex-orchestrate/scripts/verify-maturity.sh
uv run --with pyyaml --no-project \
  python ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  codex-orchestrate
```
