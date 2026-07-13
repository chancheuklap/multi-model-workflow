# multi-model-workflow

## plugin/ Claude Code

`plugin/` 是 Claude Code 编排 plugin 的源码权威(版本以 `plugin/.claude-plugin/plugin.json` 为准)。

安装入口为 `.claude-plugin/marketplace.json`，状态平面为 `.claude/multi-model-workflow/`，worktree 根为 `.claude/worktrees/`。写计划和写码工人使用 Codex CLI，审查使用 Codex 与 Claude 会话内 sub-agent。

```bash
bash plugin/scripts/mmw.sh help
for t in plugin/scripts/tests/test_*.sh; do bash "$t" || exit 1; done
```

## Codex 是 plugin 里的一个工人,不是独立 plugin

写计划 / 落地 / 审查派给 Codex CLI 无头执行。Codex 不需要独立 plugin,只需把 plugin 内那几个软链 skill 装进它自动扫描的 hub `~/.agents/skills/`:

```bash
for s in worktree-build worktree-plan worktree-review; do
  ln -sfn "$(pwd)/plugin/skills/$s" ~/.agents/skills/$s
done
```

改 `plugin/skills/` 即时生效(软链、无 cache)。

## 项目规范

`AGENTS.md` 经 `CLAUDE.md` 导入。
