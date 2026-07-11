# multi-model-workflow

## plugin/ 双宿主(Claude + Droid)

`plugin/` 是 Claude Code 与 Droid 共用的编排 plugin 源码权威(版本以 `plugin/.claude-plugin/plugin.json` 为准)。

| 宿主 | 安装入口 | 状态平面 | 写码工人 | 审者 |
| --- | --- | --- | --- | --- |
| Claude Code | `.claude-plugin/marketplace.json` → `./plugin` | `.claude/multi-model-workflow/` | `mmw worker` → codex CLI | brief 内 codex/claude 无头 CLI |
| Droid | `.factory-plugin/marketplace.json` → `./plugin` | `.factory/multi-model-workflow/` | `mmw worker` → Task `pack-executor` | Task `reviewer-*` droids |

宿主由脚本自动判定(`plugin/scripts/lib/host.sh`):`MMW_HOST` 显式 > `DROID_PLUGIN_ROOT` > 默认 claude。合同:`plugin/skills/orchestrate/references/control/host-contract.md`。

```bash
# Claude: 按既有 marketplace / 本地 plugin 安装
# Droid: droid plugin install multi-model-workflow@mmw-droid(或把本仓库加为 marketplace,source=./plugin)
bash plugin/scripts/mmw.sh help
export MMW_HOST=droid   # 可选
for t in plugin/scripts/tests/test_*.sh; do bash "$t" || exit 1; done
```

Custom Droids 在 `plugin/droids/`。hooks matcher 为 `Bash|Execute`。

## Codex 是 plugin 里的一个工人,不是独立 plugin

Claude 宿主下,写计划 / 落地 / 审查派给 Codex CLI 无头执行。Codex 不需要独立 plugin,只需把 plugin 内那几个软链 skill 装进它自动扫描的 hub `~/.agents/skills/`:

```bash
for s in worktree-build worktree-plan worktree-review; do
  ln -sfn "$(pwd)/plugin/skills/$s" ~/.agents/skills/$s
done
```

改 `plugin/skills/` 即时生效(软链、无 cache)。

## 项目规范

`AGENTS.md`(Droid 直接读,Claude 经 `CLAUDE.md` 导入)。
