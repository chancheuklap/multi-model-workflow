# MMW v5

MMW 提供开发项目所用的技能、agent 派发工具和任务板。当前工作版本是 `mmw-v5-cloud/`；Coordinator、Worker、审查轴和 verifier 在云端运行。

## 安装

**给安装 agent：用户在云端环境设置对话里提供本仓库链接时，完成下面的安装和环境配置。只在当前机器装好文件，不算完成。** 从用户要开发的消费仓库运行命令；只有开发 MMW 本身时才安装到 MMW 仓库。

每次安装都下载 [GitHub 最新正式 Release](https://github.com/chancheuklap/multi-model-workflow/releases/latest) 的完整 `mmw-v5-cloud.zip`。消费仓库不锁定 MMW 版本，也不保存 MMW 的技能、工具和 board。模型配置保留在仓库，云端准备步骤随项目保存。

| 宿主 | 安装位置 | 项目模型配置 |
| --- | --- | --- |
| Codex | `.agents/` | `.agents/models.json` 中的 `rows.codex` |
| Cursor | `.cursor/` | `.cursor/models.json` 中的 `rows.cursor` |

两种宿主使用同一个完整包。安装器保留已有目标 `models.json`；首次 Codex 安装没有该文件时，带入旧 `.cursor/models.json` 的 `rows.codex`，没有旧设置才使用默认值。

### 云端环境设置

在每个需要 MMW 的消费仓库里执行对应命令。多仓库环境逐个运行，不能依赖另一个仓库或父 agent 目录中的未提交文件。

Codex：

```sh
curl -fsSL https://raw.githubusercontent.com/chancheuklap/multi-model-workflow/main/scripts/install-mmw-v5-cloud.sh | bash -s -- --host codex --cloud
```

Cursor：

```sh
curl -fsSL https://raw.githubusercontent.com/chancheuklap/multi-model-workflow/main/scripts/install-mmw-v5-cloud.sh | bash -s -- --host cursor --cloud
```

安装器会安装当前最新发布版，并写入消费仓库的云端准备配置：

检查已有环境步骤，删除旧 v5 或固定版本的安装调用，再接入新入口，保留项目其他依赖和服务的准备命令。

| 宿主 | 安装器写入的仓库配置 | 环境设置 agent 接下来必须完成的操作 |
| --- | --- | --- |
| Cursor | `.cursor/cloud-setup.sh`；在 `.cursor/environment.json` 的 `install` 和 `start` 中接入该脚本，保留已有命令和其他配置 | 将保存的云端环境的 **environment.json location** 指向该仓库的 `.cursor/environment.json`，完成并启用成功的 Build |
| Codex | `.agents/cloud-setup.sh`；在 `AGENTS.md` 中登记云端准备入口，保留原有项目指令 | 在云端环境 **Install script** 中接入 `bash .agents/cloud-setup.sh`；在 **Start skill** 中要求每个新云端任务开始工作前执行同一命令一次，保留已有安装和启动步骤，然后 Publish / Republish |

Codex 的仓库脚本和 `AGENTS.md` 是设置 agent 的入口，不是 Codex 自动执行的环境配置格式。必须实际保存平台的 Install script 和 Start skill；不要用仅作用于本地 worktree 的 `.codex` 环境配置替代。[Codex 官方环境说明](https://learn.chatgpt.com/docs/environments/cloud-environments)。Cursor 的仓库配置也必须绑定到保存的环境，文件存在本身不代表该环境正在使用它。[Cursor 官方环境说明](https://cursor.com/docs/cloud-agent/setup)。

环境准备时安装一次，让技能就绪。每个新云端任务启动时再次执行准备脚本，主动获取最新发布版，避免从环境缓存一直使用旧 MMW。继续已有任务时不重装；一个 night 使用它开始时的同一份运行时。

下载需要环境允许访问 `raw.githubusercontent.com`、`github.com` 和 GitHub Release 下载重定向使用的 `release-assets.githubusercontent.com`。安装失败应修复环境准备步骤，不把旧缓存说成已更新。

### 保存配置并验证

安装器把 MMW 自带文件登记到 Git 本地排除清单；以前已提交的对应运行时文件会退出 Git 跟踪，磁盘副本保留。它不忽略整个 `.agents/` 或 `.cursor/`，项目自己的技能和其他文件继续正常管理。

在授权分支提交并推送模型配置、生成的云端脚本，以及 Cursor 的 `environment.json` 或 Codex 的 `AGENTS.md` 改动。包含这些配置的分支须能被后续环境准备读取；模型配置须进入新 night 的基线。不要提交 MMW 安装产物，包括安装目录里的 `plugin.json`。

完成前检查：

- 安装命令成功，报告实际版本和安装目录，已有模型设置保留。
- 宿主能发现已安装的 `dispatch`、`research` 等技能，工具从该安装目录定位。
- 仓库和平台云端配置都已保存，Cursor Build 或 Codex 环境发布完成。
- 新的独立 checkout 能通过保存的准备步骤获得运行时，而不是依赖当前机器的文件。为 Coordinator 和下级 agent 使用的环境都接好此步骤。

报告已验证的结果和未验证的部分；未启动新的云端任务就不声称完成了云端实测。需要 owner 在界面完成的发布操作，应指出具体环境及剩余操作。

### 本地安装

本地主动启用 MMW 时使用同一安装器，不加 `--cloud`：

```sh
curl -fsSL https://raw.githubusercontent.com/chancheuklap/multi-model-workflow/main/scripts/install-mmw-v5-cloud.sh | bash -s -- --host codex
```

Cursor 将末尾的 `codex` 换成 `cursor`。本地安装只安装运行时和保留模型设置，不修改云端准备配置。安装后让宿主重新加载技能列表。其他人普通 clone 不会取得这批 MMW 安装产物；需要的人自行安装。

Cursor 同时发现 `.cursor/skills/` 和 `.agents/skills/`。同一 checkout 放两份同名 MMW 会带来重复技能；两种宿主各用自己的工作目录和对应配置。

## 更新和使用

重新运行安装命令会主动获取最新正式 Release，保留项目模型设置。仓库不记录待安装版本，不使用固定 tag、commit 或 `--ref`。准备新环境和启动新云端任务时自动执行；正在运行的 night 不替换运行时。

以前的全局 v5 plugin、将完整安装目录提交 Git、复制本地安装目录给云端 agent、固定版本安装均已退役，不能作为本文的替代安装方式。已用旧方法安装的消费仓库，执行新的对应安装命令迁移，并提交退出运行时跟踪的改动。

Git 和 GitHub 命令从消费仓库运行。运行环境需要 Bash、Python 3、Git、curl 和 `gh`。技能之间按名字调用，reference 使用相对于所在文档的链接；工具从安装目录定位。完整工作步骤由 **dispatch** 及其角色 reference 提供，任务板设置页只编辑当前宿主的模型配置。

## 开发和发布

在 MMW 开发仓库的 `dev` 分支准备版本号：

```sh
python3 scripts/release-mmw-v5.py bump
```

运行相关本地检查后提交并推送到 `dev`。`bump` 只改云端版的 plugin 清单，不提交、不推送、不发布。

经 owner 授权合并并推送到 `main` 后，GitHub Actions 按已提交版本创建 tag 和 GitHub Release，附上固定名称的完整 `mmw-v5-cloud.zip`，供 `releases/latest/download/mmw-v5-cloud.zip` 安装。GitHub 不运行测试、不改变版本号。同一版本号不能用于另一提交。

在本地检查已提交版本的包：

```sh
python3 scripts/release-mmw-v5.py package --output /tmp/mmw-v5-cloud.zip
```
