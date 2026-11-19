# 472-skill-renamed-design-pages

## 改了什么

技能由 `claude-design-blocks` 改名为 `design-pages`。脚本 `selector_check.py` 改名为 `check_editable_selectors.py`。测试入口改为 `mmw-v2/tests/design-pages/run.sh`，并接受 `-k <pattern>`。

## 哪些产物失效

- ticket 的 `CHECK:` 或其它 agent 指令如果仍写 `claude-design-blocks`，或调用 `~/.agents/skills/claude-design-blocks/`，解析不到新技能。
- 代码或文档如果按文件名调用 `selector_check.py`，需要改用 `check_editable_selectors.py`。
- screen contract 的格式和 `.mmw/target.json` 的字段没有改变。

agentflow 当前有 2 个受影响文件：`tests/guards/test_work_monitor_handoff_scenes.py` 和 `prototypes/hedgehog-boss-console/518/claude-design/README.md`。

## 怎么迁

1. 把技能名 `claude-design-blocks` 换成 `design-pages`；把 `~/.agents/skills/claude-design-blocks/` 换成 `~/.agents/skills/design-pages/`。
2. 把 `selector_check.py` 换成 `check_editable_selectors.py`。
3. agentflow：`tests/guards/test_work_monitor_handoff_scenes.py` 只把技能名 `claude-design-blocks` 换成 `design-pages`；`prototypes/hedgehog-boss-console/518/claude-design/README.md` 把 `selector_check.py` 换成 `check_editable_selectors.py`，把技能名 `claude-design-blocks` 换成 `design-pages`。两处里指向 `export_scene_data.py` 的命令和测试字符串按 #473 的 `*-handoff-package-by-pull.md` 迁，不要写成 `~/.agents/skills/design-pages/scripts/export_scene_data.py`：同一批次会把该脚本移出技能目录。
4. 新版 MMW 安装后，host 的 symlink 指向 `design-pages`；旧名 symlink 由 `install.sh` 当作残留摘掉。
