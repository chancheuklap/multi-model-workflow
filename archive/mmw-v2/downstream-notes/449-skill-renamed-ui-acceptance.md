# 449-skill-renamed-ui-acceptance

## 改了什么

界面验收技能由 `drive-target` 改名为 `ui-acceptance`，技能的脚本令牌由 `<drive-target scripts>` 改为 `<ui-acceptance scripts>`。同时，`visual-parity.py` 改名为 `pixel_diff.py`，`references/runtime-environment.md` 改名为 `references/product-answers.md`。

host 的命令守卫由 `drive-target` 的 `scripts/hook.py` 搬到 `dispatch` 的 `scripts/tool-guard.py`。这项注册由 `mmw-v2/install.sh` 迁移，不是 consuming repository 自己的配置。

## 哪些产物失效

- ticket 的 `CHECK:` 或其它 agent 指令如果仍写 `<drive-target scripts>`，解析不到新技能。直接写 `~/.agents/skills/drive-target/scripts/` 的命令也同样失效。
- 代码如果按文件名导入 `visual-parity.py`，或文档指向 `references/runtime-environment.md`，需要改用新名。
- screen contract 的格式和 `.mmw/target.json` 的字段没有改变；只有它们周边引用了旧技能名、令牌或文件名的命令和说明失效。

agentflow 当前有 6 个受影响文件：`.gitignore`、`.mmw/harness/target.py`、`docs/agents/triage-labels.md`、`prototypes/hedgehog-boss-console/518/claude-design/README.md`、`prototypes/work-monitor/710/EXP/README.md` 和 `prototypes/work-monitor/710/EXP/render_evidence.py`。

## 怎么迁

1. 把 ticket、screen contract 周边的命令和 agent 指令中的 `<drive-target scripts>` 换成 `<ui-acceptance scripts>`；把 `~/.agents/skills/drive-target/scripts/` 换成 `~/.agents/skills/ui-acceptance/scripts/`。
2. 把按文件名导入的 `visual-parity.py` 换成 `pixel_diff.py`，把文档链接 `references/runtime-environment.md` 换成 `references/product-answers.md`。
3. agentflow 按上述规则更新列出的 6 个文件；其中 `.mmw/harness/target.py` 的命令常量和拒绝文案必须一起改，否则一处仍会把 agent 引回不存在的旧技能。
4. 新版 MMW 安装后运行一次 `bash mmw-v2/install.sh`，让它清除旧 `hook.py` 注册、写入 `dispatch/scripts/tool-guard.py` 注册并更新 Codex `trusted_hash`；随后运行 `bash mmw-v2/install.sh --check`，结果应包含 `HOOKS-INSTALLED` 且退出 0。Codex 可能在这次迁移后只弹出一次「hooks need review」，出现时确认一次；后续检查不应再弹出。
