# CLAUDE.md

## 边界

本仓库有两套系统。Claude Code 只管 `plugin/`（当前活跃的 Claude Code Plugin 源码）。

**禁区**（除非用户明确指令，否则不读不改）：
- `.agents/` — Codex skill source
- `codex/` — Codex agent/hook/sync source
- `archive/` — 历史归档

## 架构权威

改动 plugin 结构前必读：[`plugin/architecture-draft.md`](plugin/architecture-draft.md)

涵盖：全局流程（三条路线）、Execution 循环、Multi-PR Merge、状态文件链、文档产物链、Review 派发机制、修复截断规则、Budget 预算、Scope Contract、跨会话恢复、组件汇总（Skill / Agent / Hook）、返回值路由表。

## Plugin 结构

```
plugin/
├── .claude-plugin/plugin.json   # 插件清单（版本号在这）
├── skills/orchestrate-*/        # 六个 phase skill
├── agents/*.md                  # 八个 sub-agent 定义
├── hooks/                       # hooks.json + 11 个 hook 脚本
├── build/                       # 构建系统（11 resolver + 11 template）
├── scripts/                     # state.sh + learnings + run-summary + 验证脚本
└── state-schema/                # JSON schema 定义
```

## 版本号同步

改版本号时必须同时更新两处，保持一致：
- `plugin/.claude-plugin/plugin.json` → `version`
- `.claude-plugin/marketplace.json`（仓库根目录）→ `plugins[0].version`

## 验证

```bash
# plugin.json 格式
python3 -m json.tool plugin/.claude-plugin/plugin.json >/dev/null

# hooks.json 格式
python3 -m json.tool plugin/hooks/hooks.json >/dev/null

# 版本号一致性
diff <(jq -r .version plugin/.claude-plugin/plugin.json) \
     <(jq -r '.plugins[0].version' .claude-plugin/marketplace.json)
```
