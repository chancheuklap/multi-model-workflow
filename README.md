# MMW v5

MMW v5 提供开发项目所用的技能、Agent 派发工具和任务板。当前版本是云端版，源目录是 `mmw-v5-cloud/`。Coordinator、Worker、审查轴和 verifier 都由 Cursor cloud agent 运行。

## 安装

用户只提供本仓库的 GitHub 链接并要求安装时，按当前宿主执行下面的说明。命令从用户正在开发的项目运行；只有在开发 MMW 本身时，才安装到本仓库。完成后报告实际安装的版本和位置。

Cursor 和 Codex 都在消费仓库内安装完整运行时：

| 宿主 | 安装目录 | 模型配置 |
| --- | --- | --- |
| Cursor | `.cursor/` | `.cursor/models.json` 的 `rows.cursor` |
| Codex | `.agents/` | `.agents/models.json` 的 `rows.codex` |

安装命令、配置保留规则和提交推送要求见 [AGENTS.md 的安装章节](AGENTS.md#install-the-cloud-edition)。安装器使用同一个完整 cloud 包，按 `--host cursor` 或 `--host codex` 选择目的地。Codex 从仓库的 `.agents/skills/` 发现技能，不安装全局 cloud plugin。

首次 Codex 安装且 `.agents/models.json` 不存在时，安装器带入旧 `.cursor/models.json` 的 `rows.codex`；没有旧设置才用默认值。已有目标配置保留。运行时只读自己的安装目录，设置页只编辑当前宿主的角色组。

从旧全局 Codex plugin 切换时，先执行 `codex plugin remove mmw-v5-cloud@mmw-v5`，再安装仓库副本，避免同名技能重复。

## 更新和使用

重新执行对应宿主的 [仓库安装命令](AGENTS.md#install-the-cloud-edition)，保留已有模型配置和其他项目文件，提交并推送对应安装目录。

替换正在使用的版本前，先结束它控制的 night。一次 night 始终使用同一份技能、工具和配置。

Git 和 GitHub 命令从使用项目运行。运行环境需要 Bash、Python 3、Git 和 `gh`。技能之间按名字调用，reference 使用相对于所在文档的 Markdown 链接；工具从安装目录定位。

完整工作步骤由 **dispatch** 及其角色 reference 提供。任务板通过 dispatch 启动，设置页只编辑当前安装目录的 `models.json` 和对应宿主的角色组。

## 开发和发布

在 MMW 开发仓库的 `dev` 分支准备版本号：

```sh
python3 scripts/release-mmw-v5.py bump
```

运行本次改动相关的本地检查，再提交并推送到 `dev`。`bump` 只改云端版的 plugin 清单。预发布版本递增末尾编号，稳定版本递增 patch。它不提交、不推送、不发布。

推送 `dev` 不发布。经所有者授权合并并推送到 `main` 后，GitHub Actions 按已提交版本打 tag、创建 Release，并附上宿主无关的完整 cloud ZIP。GitHub 不运行测试、不修改版本号、不回写分支。同一版本号不能用于另一提交。

在本地检查已提交版本的包：

```sh
python3 scripts/release-mmw-v5.py package --output /tmp/mmw-v5-cloud.zip
```
