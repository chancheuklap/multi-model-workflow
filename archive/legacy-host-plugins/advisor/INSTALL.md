# 安装 advisor

`advisor.md` 正文与宿主无关,四家共用同一份,差异只在 frontmatter 字段名。`model` 一律取本宿主可得的最强档,推理档位拉满。

| 宿主 | 落点 | frontmatter 差异 |
| --- | --- | --- |
| Claude Code | `.claude/agents/advisor.md` 或 `~/.claude/agents/advisor.md` | 原样可用(`model` / `effort` / `tools` 列表) |
| Factory Droid | Custom Droid 定义目录 | `tools` 按 Droid 工具名改写,只保留读文件那一个 |
| pi | `agents-roster/`,经 `render_agent_prompts.py` 渲染 | 模型与档位按花名册字段写法 |
| Cursor | `~/.cursor/agents/advisor.md` | `model` 写成 `id[effort=high]`;`is_background` 留空 |

给 advisor 的工具只留读文件那一个。给了检索工具它会变成第二个工人,输出从判据变成判决。

## 验收判据

1. frontmatter 能被目标宿主解析。
2. advisor 出现在宿主的 agent 列表里——仅 YAML 能解析不算装成。
3. 传一个不存在的路径试一次:必须只回「读不到」并停住,不得给出任何建议。
