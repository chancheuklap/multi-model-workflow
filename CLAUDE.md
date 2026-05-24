# CLAUDE.md

## 边界

本仓库同时保存 Claude Code 版和 Codex 版编排系统：

- `plugin/` 是 Claude Code plugin 源码，也是 Codex 复刻的行为蓝本。
- `codex-orchestrate/` 是 Codex 原生插件复刻源码。
- 旧 Codex 实现已经归档在 `archive/2026-05-24-codex-pre-atomic/codex/`。

Claude Code 侧工作默认只改 `plugin/`。除非用户明确要求更新 Codex 复刻，否则不要改 `codex-orchestrate/`。

## Claude Plugin 结构

```text
plugin/
├── .claude-plugin/plugin.json
├── skills/orchestrate-*/
├── skills/codex-review/
├── agents/*.md
├── hooks/
├── build/
├── scripts/
├── state-schema/
└── architecture-draft.md
```

改 Claude plugin 架构前先读 `plugin/architecture-draft.md`。

## Codex 复刻结构

```text
codex-orchestrate/
├── .codex-plugin/plugin.json
├── skills/
├── agents/*.toml
├── hooks.json
├── hooks/
├── scripts/
├── state-schema/
├── build/
└── architecture-draft.md
```

Codex 侧必须使用 Codex 原生能力：plugin manifest、自定义 agent TOML、Codex hooks、native Codex Review、`.codex/multi-model-workflow` 状态路径。

## 构建系统

`plugin/` 和 `codex-orchestrate/` 都使用 `build/templates/*.tmpl` + resolver 注入锚点内容。

规则：

- 改 `.tmpl` 后跑对应 package 的 `build.sh --apply`。
- 改锚点外正文不需要 apply。
- 直接改锚点内内容会被下一次 apply 覆盖，必须同步到模板。

## 常用命令

```bash
# Claude plugin
bash plugin/build/build.sh --check --plugin-dir plugin
bash plugin/scripts/run-all-tests.sh
bash plugin/scripts/verify-maturity.sh

# Codex 复刻
bash codex-orchestrate/scripts/run-all-tests.sh
bash codex-orchestrate/scripts/verify-maturity.sh
bash codex-orchestrate/build/build.sh --check --plugin-dir codex-orchestrate
bash codex-orchestrate/installers/install.sh --user --apply
bash codex-orchestrate/installers/verify-runtime-parity.sh --user
```

## 硬规则

- 不要把归档 `archive/2026-05-24-codex-pre-atomic/codex/` 当成当前 Codex 行为。
- 不要重建 `.agents/skills/orchestrate-*`。
- Codex baseline review 默认走 native Codex Review，不默认走 Claude。
- Worker 在 worktree 里不拥有正式文档；正式文档由 Coordinator 主线程处理。
