# 安装 MMW v5

使用完整的 MMW v5 发布包。Codex 和 Cursor 共用根目录的 `plugin.json`、`skills/`、`tools/` 和 `board/`。解压后保持目录关系，安装副本中不保留指向 MMW 开发仓库的链接。

以下步骤假定发布包解压在 `~/Downloads/mmw-v5`。使用其他目录时，将命令中的这个路径替换为实际路径。

## 在 Codex 中安装

1. 注册发布包自带的本地插件目录：

   ```sh
   codex plugin marketplace add "$HOME/Downloads/mmw-v5"
   ```

2. 安装插件：

   ```sh
   codex plugin add mmw-v5@mmw-v5-local
   ```

3. 在新对话中确认 MMW v5 的 `dispatch`、`code-review` 和 `write-tests` 技能可用。

Codex 从自己的插件缓存读取安装副本。开发仓库只用于制作后续版本，不参与运行。

## 在 Cursor 中安装

1. 将同一份插件包复制到 Cursor 的本地插件目录：

   ```sh
   mkdir -p "$HOME/.cursor/plugins/local"
   cp -R "$HOME/Downloads/mmw-v5" "$HOME/.cursor/plugins/local/mmw-v5"
   ```

   首次安装时，目标 `mmw-v5` 目录应不存在。更新时替换完整副本，不把新目录嵌套到旧目录中。

2. 在 Cursor 中执行 **Developer: Reload Window**。
3. 打开 **Customize**，确认 MMW v5 及其技能已加载。Enterprise 的本地插件导入需要管理员允许。

使用 Cursor CLI 时，通过已复制的插件目录启动：

```sh
agent --plugin-dir "$HOME/.cursor/plugins/local/mmw-v5"
```

## 配置和使用

首次使用时，让 Agent 将已安装插件内的 `tools/dispatch/scripts/models.py` 解析为绝对路径，执行 `python3 <该绝对路径> init`。随后调用 `dispatch` 技能打开 task board，在设置页选择 runner、各角色的模型和并行数。配置与本机运行记录默认保存在 `~/.mmw-v5`，也可由 `MMW_HOME` 指定。插件更新保留这些记录。

在需要自动执行的项目中使用插件，Git 和 GitHub 命令从该项目运行。机器需要 Bash、Python 3、Git、`gh`，以及所选 runner 和会话宿主的实际命令。

插件的技能可以由 Codex 和 Cursor 加载。当前独立会话宿主仍是配置中的 Codex 或 Claude Code；安装到 Cursor 不会新增 Cursor 派发适配器。

替换旧 v4 时，先结束旧运行，再移除旧 MMW 技能入口和旧 hook，然后启用 v5。一次运行始终使用同一份插件副本，运行期间不更新或卸载插件。

安装格式依据：[Codex 插件安装文档](https://developers.openai.com/plugins/build/plugins)、[Cursor 支持的插件格式](https://cursor.com/docs/reference/plugins)、[Cursor 本地插件安装](https://cursor.com/docs/plugins#test-plugins-locally)。
