# CLAUDE.md

## 边界

本仓库有两套系统。Claude Code 只管 `plugin/`（当前活跃的 Claude Code Plugin 源码）。

**禁区**（除非用户明确指令，否则不读不改）：
- `.agents/` — Codex skill source
- `codex/` — Codex agent/hook/sync source
- `archive/` — 历史归档

## 前置条件

Plugin 启动时 `session-start.sh` 会检查以下条件，缺任意一项发一条 stderr 告警后继续（SessionStart 钩子无法阻断会话，且提前退出会废掉脚本末尾的 workflow 断点恢复注入）：
- 环境变量 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` 已设置
- `jq` 和 `python3` 在 PATH 中
- Claude Code 版本 ≥ 2.1.147

## Plugin 结构

```
plugin/
├── .claude-plugin/plugin.json   # 插件清单（版本号在这）
├── skills/orchestrate-*/        # phase skill（每个含 SKILL.md + references/）
├── agents/*.md                  # sub-agent 定义
├── hooks/                       # hooks.json + hook 脚本 + lib/
├── build/                       # 构建系统（resolver + template），详见 build/README.md
├── scripts/                     # state.sh + 工具脚本 + lib/
├── state-schema/                # JSON schema 定义
└── architecture-draft.md        # 架构权威文档
```

## 架构权威

改动 plugin 结构前必读：[`plugin/architecture-draft.md`](plugin/architecture-draft.md)

## 构建系统

Skill 和 Agent 的 `.md` 文件中有 `<!-- BEGIN: xxx -->` / `<!-- END: xxx -->` 锚点，内容由 `build/templates/*.tmpl` 模板统一管理。

**规则**：
- 改了模板（`.tmpl`）→ 必须跑 `bash plugin/build/build.sh --apply --plugin-dir plugin`
- 改了锚点之外的 SKILL.md 内容 → 不需要跑构建
- 直接改锚点内的内容 → 立即生效但下次 `--apply` 会被覆盖；事后必须把改动同步到 `.tmpl` 源文件

详细的锚点约定、新增 resolver 步骤、紧急修复路径见 [`plugin/build/README.md`](plugin/build/README.md)。

## 版本号同步

改版本号时必须同时更新两处，保持一致：
- `plugin/.claude-plugin/plugin.json` → `version`
- `.claude-plugin/marketplace.json`（仓库根目录）→ `plugins[0].version`

## 硬规则

- `docs/orchestrate/plans/` 下有未勾选任务（`- [ ]`）时，`git push` 和 `gh pr create` 会被 hook 阻断
- `git merge --squash` 被禁止，必须用 `--no-ff`
- Worker agent（在 worktree 中运行）不能修改 `docs/` 下的文件，只有 Coordinator 可以

## 常用命令

```bash
# 构建检查（模板内容与文件是否一致）
bash plugin/build/build.sh --check --plugin-dir plugin

# 构建应用（模板内容写入文件）
bash plugin/build/build.sh --apply --plugin-dir plugin

# 全量测试
bash plugin/scripts/run-all-tests.sh

# 成熟度验证（构建+测试+schema+结构 全面检查）
bash plugin/scripts/verify-maturity.sh

# JSON 格式验证
python3 -m json.tool plugin/.claude-plugin/plugin.json >/dev/null
python3 -m json.tool plugin/hooks/hooks.json >/dev/null

# 版本号一致性
diff <(jq -r .version plugin/.claude-plugin/plugin.json) \
     <(jq -r '.plugins[0].version' .claude-plugin/marketplace.json)
```

## 修改后检查清单

| 改了什么 | 需要跑什么 |
|---------|-----------|
| `build/templates/*.tmpl` | `build.sh --apply` → `build.sh --check` |
| `hooks/*.sh` 或 `scripts/*.sh` | `run-all-tests.sh` |
| `hooks/hooks.json` | `python3 -m json.tool` 验证格式 |
| `plugin.json` 版本号 | 同步更新 `marketplace.json` → `diff` 验证 |
| 任何改动（提交前） | `verify-maturity.sh` |

https://github.com/mattpocock/skills/tree/main/skills/engineering

https://github.com/pbakaus/impeccable/tree/main

https://github.com/garrytan/gstack

https://github.com/obra/superpowers