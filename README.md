# MMW v5

MMW v5 提供开发项目所用的技能、Agent 派发工具和任务板。当前版本是云端版，源目录是 `mmw-v5-cloud/`。Coordinator、Worker、审查轴和 verifier 都由 Cursor cloud agent 运行。

## 安装

用户只提供本仓库的 GitHub 链接并要求安装时，按当前宿主执行下面的说明。命令从用户正在开发的项目运行；只有在开发 MMW 本身时，才安装到本仓库。完成后报告实际安装的版本和位置。

### Cursor

使用项目级安装，本地和云端 Cursor 共用仓库根目录的 `.cursor/`。安装命令、配置保留规则和提交推送要求见 [AGENTS.md 的安装章节](AGENTS.md#install-the-cursor-cloud-edition)。

### Codex

通过本机 plugin 安装。首次注册 GitHub 插件源时，明确指定 `main`；本仓库的默认分支是 `dev`。

```sh
codex plugin marketplace add chancheuklap/multi-model-workflow --ref main
codex plugin add mmw-v5-cloud@mmw-v5
```

插件源已经注册时，使用下文的更新操作。

模型配置只有项目的 `.cursor/models.json` 一份，Codex plugin 也读取这份配置。项目还没有该文件时，从已安装 plugin 内的 `models.json` 复制到项目的 `.cursor/models.json`。已有文件保留。各宿主的角色写在 `rows.codex` 与 `rows.cursor` 里，模型和参数以文件为准。

## 更新和使用

- **Codex：**执行 `codex plugin marketplace upgrade mmw-v5`，再执行 `codex plugin add mmw-v5-cloud@mmw-v5`。开启新对话，确认技能和实际版本。
- **Cursor：**重新执行 [项目安装命令](AGENTS.md#install-the-cursor-cloud-edition)，保留已有模型配置和其他 Cursor 文件，提交并推送项目里的 `.cursor/`。

替换正在使用的版本前，先结束它控制的 night。一次 night 始终使用同一份技能、工具和配置。

Git 和 GitHub 命令从使用项目运行。运行环境需要 Bash、Python 3、Git 和 `gh`。技能之间按名字调用，reference 使用相对于所在文档的 Markdown 链接；工具从安装目录定位。

完整工作步骤由 **dispatch** 及其角色 reference 提供。任务板通过 dispatch 启动，设置页编辑项目 `.cursor/models.json`。

## 开发和发布

在 MMW 开发仓库的 `dev` 分支准备版本号：

```sh
python3 scripts/release-mmw-v5.py bump
```

运行本次改动相关的本地检查，再提交并推送到 `dev`。`bump` 只改云端版的 plugin 清单。预发布版本递增末尾编号，稳定版本递增 patch。它不提交、不推送、不发布。

推送 `dev` 不发布。经所有者授权合并并推送到 `main` 后，GitHub Actions 按已提交版本打 tag、创建 Release，并附上云端 `.cursor/` 运行包 ZIP。GitHub 不运行测试、不修改版本号、不回写分支。同一版本号不能用于另一提交。

在本地检查已提交版本的包：

```sh
python3 scripts/release-mmw-v5.py package --output /tmp/mmw-v5-cloud.zip
```
