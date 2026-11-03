# MMW v5

MMW v5 提供开发项目所用的技能、Agent 派发工具和任务板，有两套完整版本，选择其中一套安装：

| 版本 | 工作方式 | 源目录 |
| --- | --- | --- |
| 云端版 | 本地 Coordinator 配合 Cloud Workers | `mmw-v5-cloud/` |
| 本地版 | 本机独立会话，通过 runner 派发和接收结果 | `mmw-v5/` |

## 安装云端版

如果用户只提供本仓库的 GitHub 链接并要求安装 v5 cloud，按当前宿主执行下面的安装说明。命令从用户正在开发的项目运行；只有在开发 MMW 本身时，才安装到本仓库。完成后报告实际安装的版本和位置。

### Cursor

使用项目级安装，本地和云端 Cursor 共用仓库根目录的 `.cursor/`。**安装命令、配置保留规则和提交推送要求统一见 [AGENTS.md 的安装章节](AGENTS.md#install-the-cursor-cloud-edition)**，避免在多处重复维护同一条命令。

如已安装本地版 MMW plugin，先在 **Customize → Plugins** 卸载它，再安装云端版。

### Codex

通过本机 plugin 安装。首次注册 GitHub 插件源时，明确指定 `main`；本仓库的默认分支是 `dev`。

```sh
codex plugin marketplace add chancheuklap/multi-model-workflow --ref main
codex plugin add mmw-v5-cloud@mmw-v5
```

如果插件源已经注册，使用下文的更新操作。若正在从本地版切换，先执行 `codex plugin remove mmw-v5@mmw-v5`。

云端版模型配置只有使用项目的 `.cursor/models.json` 一份，Codex plugin 也读取这份配置。首次使用且项目没有该文件时，从已安装 plugin 内的 `models.json` 复制到项目的 `.cursor/models.json`，保留已有配置。`rows.codex` 与 `rows.cursor` 分别配置各宿主的六个角色，具体模型及参数以文件为准。

## 安装本地版

本地版是包含全部技能、工具和任务板的完整 plugin。宿主使用自己的安装副本，不读取 MMW 开发仓库。

### Codex

首次注册插件源后安装本地版：

```sh
codex plugin marketplace add chancheuklap/multi-model-workflow --ref main
codex plugin add mmw-v5@mmw-v5
```

若正在从云端版切换，先执行 `codex plugin remove mmw-v5-cloud@mmw-v5`。

### Cursor

注册插件源：

```sh
agent plugin marketplace add https://github.com/chancheuklap/multi-model-workflow --git-ref main
```

然后打开 **Customize → Plugins**，从 `mmw-v5` 插件源安装 `mmw-v5`。注册来源不会自动安装插件；本机 Cursor CLI 没有独立的非交互 plugin 安装命令。

首次使用时，从已安装 plugin 内定位 `tools/dispatch/scripts/models.py`，执行 `python3 <脚本路径> init`，再调用 **dispatch** 打开任务板，选择 runner、模型和并行数。本地版配置和运行记录保存在 `~/.mmw-v5`，或 `MMW_HOME` 指定的位置。

本地版的独立会话宿主仍是配置中的 Codex 或 Claude Code；安装到 Cursor 不会新增 Cursor 独立会话派发适配器。

## 更新和使用

- **Codex plugin：**执行 `codex plugin marketplace upgrade mmw-v5`，再用对应版本的 `codex plugin add` 命令更新安装。开启新对话，确认技能和实际版本。
- **Cursor 云端版：**重新执行 [项目安装命令](AGENTS.md#install-the-cursor-cloud-edition)，保留已有模型配置和其他 Cursor 文件，提交并推送项目安装副本。
- **Cursor 本地版：**执行 `agent plugin marketplace update mmw-v5`，再在 Customize 中更新 plugin、重载窗口并确认实际版本。来源刷新成功不能代替安装版本确认。

替换或更新正在使用的版本前，先结束该版本控制的运行。保留模型配置和运行记录；一次运行始终使用同一份技能、工具和配置。

Git 和 GitHub 命令从使用项目运行。运行环境需要 Bash、Python 3、Git、`gh`，以及本地版所选 runner 和宿主的实际命令。技能之间按名字调用，reference 使用相对于所在文档的 Markdown 链接；工具从安装目录定位。

完整工作步骤由 **dispatch** 及其角色 reference 提供。任务板通过 dispatch 启动；云端版设置页编辑项目 `.cursor/models.json`，本地版设置页编辑本机配置。

本地版 Release ZIP 可离线安装：解压后的 `mmw-v5/` 是完整 plugin，也包含独立的 `mmw-v5-local` 插件源；Cursor 可将其放入 `~/.cursor/plugins/local/mmw-v5/` 后重载窗口。保持包内目录关系，不保留指向开发仓库的链接。

## 开发和发布

两套源目录都包含完整技能和运行工具，分别从自己的目录打包，不在打包时拼装另一套版本。修改技能时保留共同专业方法；派发相关内容按版本适配。

在 MMW 开发仓库的 `dev` 分支准备版本号：

```sh
python3 scripts/release-mmw-v5.py bump
```

运行本次改动相关的本地检查，再提交并推送到 `dev`。`bump` 同步修改两版的 plugin 清单；预发布版本递增末尾编号，稳定版本递增 patch。它不提交、推送或发布。

推送 `dev` 不发布。经所有者授权合并并推送到 `main` 后，GitHub Actions 按已提交版本打 tag、创建 Release，并附上本地 plugin ZIP 和云端 `.cursor/` 运行包 ZIP。GitHub 不运行测试、不修改版本号、不回写分支；同一版本号不能用于另一提交。

如需在本地检查已提交版本的包：

```sh
python3 scripts/release-mmw-v5.py package --output /tmp/mmw-v5.zip
python3 scripts/release-mmw-v5.py package --edition cloud --output /tmp/mmw-v5-cloud.zip
```
