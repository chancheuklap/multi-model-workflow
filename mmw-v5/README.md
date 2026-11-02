# 安装和发布 MMW v5 本地版

这里是完整的本地独立会话版本；`mmw-v5-cloud/` 是另一套完整的云端版本。两套目录都包含全部技能。除 dispatch 外，其余技能文件保持一致；派发技能和运行脚本各用自己的实现。两个发布包分别只打包各自目录，不在打包时拼装技能。

MMW v5 本地版从 GitHub 的 `main` 分支分发。Codex、Cursor 安装同一份插件，包含 `skills/`、`tools/` 和 `board/`。宿主读取自己的安装副本；Agent 在使用 MMW 时不读取 MMW 开发仓库。

## 从 GitHub 安装到 Codex

```sh
codex plugin marketplace add chancheuklap/multi-model-workflow --ref main
codex plugin add mmw-v5@mmw-v5
```

更新插件源并安装其中的版本：

```sh
codex plugin marketplace upgrade mmw-v5
codex plugin add mmw-v5@mmw-v5
```

重启宿主，在新对话中确认 `dispatch`、`code-review` 和 `write-tests` 可用。插件源必须指定 `main`；本仓库的默认分支是 `dev`。

## 从 GitHub 安装到 Cursor

注册插件源：

```sh
agent plugin marketplace add https://github.com/chancheuklap/multi-model-workflow --git-ref main
```

然后打开 **Customize → Plugins**，从 `mmw-v5` 插件源安装 MMW v5。注册来源不会自动安装插件。本机 Cursor CLI 没有独立的非交互插件安装命令。

重新索引来源：

```sh
agent plugin marketplace update mmw-v5
```

在 Customize 中更新插件，重载窗口后确认实际安装版本。个人 GitHub 导入存在固定旧提交的已知问题，来源刷新成功不能代替安装版本确认。Teams、Enterprise 的 GitHub 插件源可以配置 Auto Refresh；个人安装不承诺自动升级。见 [Cursor 更新说明](https://cursor.com/docs/plugins#keep-plugins-up-to-date)和[个人导入问题](https://forum.cursor.com/t/add-plugin-github-imports-can-get-stuck-on-stale-plugin-versions/163895)。

## 从旧本地包切换

先结束正在运行的 night。Codex 旧来源名是 `mmw-v5-local`，切换前移除旧安装，避免重复技能：

```sh
codex plugin remove mmw-v5@mmw-v5-local
```

Cursor 先将旧 MMW v5 本地副本移出 `~/.cursor/plugins/local/`，重载窗口，再安装 GitHub 来源。保留 `~/.mmw-v5` 中的模型配置和运行记录。

## 本地发布包

GitHub Release 的 ZIP 是完整插件包，供本地或离线安装；从 GitHub 插件源安装不需要 ZIP。解压后的 `mmw-v5` 目录含独立的 `mmw-v5-local` 插件源，也可完整复制到 Cursor 的 `~/.cursor/plugins/local/mmw-v5`，随后重载窗口。保持目录关系，不保留指向开发仓库的链接。

Cursor CLI 也可以通过已安装的完整本地副本启动：

```sh
agent --plugin-dir "$HOME/.cursor/plugins/local/mmw-v5"
```

## 准备和发布版本

以下命令只在维护 MMW 的开发仓库中运行；安装副本不包含发布脚本。

准备一次发布时，在 `dev` 上运行一次：

```sh
python3 scripts/release-mmw-v5.py bump
MMW_BASE_REF=origin/main scripts/check
```

`bump` 同步修改本地 portable、Cursor 清单与云端清单的版本号。预发布版本递增末尾编号，例如 `5.0.0-beta.2 → 5.0.0-beta.3`；稳定版本递增 patch。它不提交、不推送、不发布。Agent 在本地检查通过后，将版本变更与本次代码一起提交、推送到 `dev`。

推送 `dev` 不触发发布。合并并推送到 `main` 后，`.github/workflows/release-mmw-v5.yml` 自动按已经提交的版本打 tag、创建 GitHub Release，并附上本地 plugin 与云端项目运行包两份 ZIP。云端不改版本号、不回写分支、不创建版本 PR、不运行测试。

发版任务只打包该提交中的插件文件；已用于另一提交的版本号不能再次发布。需要新版本时先回到 `dev` 准备版本号。

如需在本地检查已提交版本的 ZIP：

```sh
python3 scripts/release-mmw-v5.py package --output /tmp/mmw-v5.zip
```

## 配置和使用

首次使用时，让 Agent 将已安装插件内的 `tools/dispatch/scripts/models.py` 解析为绝对路径，执行 `python3 <该绝对路径> init`。随后调用 `dispatch` 技能打开 task board，在设置页选择 runner、各角色的模型和并行数。配置与本机运行记录默认保存在 `~/.mmw-v5`，也可由 `MMW_HOME` 指定。插件更新保留这些记录。

在需要自动执行的项目中使用插件，Git 和 GitHub 命令从该项目运行。机器需要 Bash、Python 3、Git、`gh`，以及所选 runner 和会话宿主的实际命令。

插件的技能可以由 Codex 和 Cursor 加载。当前独立会话宿主仍是配置中的 Codex 或 Claude Code；安装到 Cursor 不会新增 Cursor 派发适配器。

替换旧 v4 时，先结束旧运行，再移除旧 MMW 技能入口和旧 hook，然后启用 v5。一次运行始终使用同一份插件副本，运行期间不更新或卸载插件。

安装格式依据：[Codex 插件安装文档](https://developers.openai.com/plugins/build/plugins)、[Cursor 支持的插件格式](https://cursor.com/docs/reference/plugins)、[Cursor CLI 插件源命令](https://cursor.com/docs/cli/changelog)。
