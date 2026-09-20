# 491-skill-renamed-write-screen-contract

## 改了什么

技能由 `align-screens` 改名为 `write-screen-contract`。格式文档由 `references/contract-format.md` 改名为 `references/screen-contract-format.md`。lint 脚本由 `scripts/lint_contract.py` 改名为 `scripts/lint_screen_contract.py`。`extract_skeleton.py` 从 `ui-acceptance/scripts/` 移到本技能的 `scripts/`。`--tools` 改为覆盖：两个脚本从自身位置找到同在 `skills/` 下的 `ui-acceptance/scripts/`。

## 哪些产物失效

- ticket 的 `CHECK:` 或其它 agent 指令如果仍写 `align-screens`，或调用 `~/.agents/skills/align-screens/`，解析不到新技能。
- 代码或文档如果按文件名调用 `lint_contract.py`，或指向 `references/contract-format.md`，需要改用新名。
- 代码如果按路径调用 `ui-acceptance/scripts/extract_skeleton.py`，需要改到 `write-screen-contract/scripts/extract_skeleton.py`。
- screen contract 的格式和 `.mmw/target.json` 的字段没有改变；target trees 随 screen contract 一起，本次不因改名而失配。

本仓库作为 consuming repository：任务板合同本身不改。点名旧技能的 `prototypes/board-orchestration/task-board/UI/README.md` 已在本票改。合同文件的字段迁移在 #448。

agentflow 当前有 3 个受影响文件：`prototypes/work-monitor/710/EXP/README.md` 与 `prototypes/work-monitor/710/EXP/contract.yaml` 仍写 `align-screens`；`prototypes/hedgehog-boss-console/518/claude-design/README.md` 仍调用 `~/.agents/skills/drive-target/scripts/extract_skeleton.py`。工作监控合同本身的迁移另开。

## 怎么迁

1. 把技能名 `align-screens` 换成 `write-screen-contract`；把 `~/.agents/skills/align-screens/` 换成 `~/.agents/skills/write-screen-contract/`。
2. 把 `lint_contract.py` 换成 `lint_screen_contract.py`，把 `references/contract-format.md` 换成 `references/screen-contract-format.md`。
3. 把 `extract_skeleton.py` 的调用从 ui-acceptance 的 `scripts/` 改到 write-screen-contract 的 `scripts/`。`lint_screen_contract.py` 与 `extract_skeleton.py` 不再必须带 `--tools`；需要指向另一份 ui-acceptance 脚本时再传 `--tools`。
4. agentflow：`prototypes/work-monitor/710/EXP/README.md` 与 `contract.yaml` 把 `align-screens` 换成 `write-screen-contract`；`prototypes/hedgehog-boss-console/518/claude-design/README.md` 把 `~/.agents/skills/drive-target/scripts/extract_skeleton.py` 换成 `~/.agents/skills/write-screen-contract/scripts/extract_skeleton.py`。
5. 新版 MMW 安装后，host 的 symlink 指向 `write-screen-contract`；旧名 symlink 由 `install.sh` 当作残留摘掉。
