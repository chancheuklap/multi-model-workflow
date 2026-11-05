# MMW v5

MMW 提供开发项目所用的技能、agent 派发工具和任务板。当前工作版本是 `mmw-v5-cloud/`；Coordinator、Worker、审查轴和 verifier 在云端运行。

在 Cursor 或 Codex 的项目对话、云端环境设置对话里，发送：

> https://github.com/chancheuklap/multi-model-workflow
>
> 帮我配置 MMW。

安装 agent 按本文完成安装、保存配置和验证。命令、参数和平台设置由 agent 处理。

## 安装

### 给安装 agent：接手配置全过程

用户提供本仓库链接并说“帮我配置 MMW”，就是让你执行本文。按顺序完成：

1. 从当前会话确定消费仓库。消费仓库是用户要开发的项目；MMW 链接提供安装说明，只有开发 MMW 本身时才安装到 MMW 仓库。云端环境选中了多个消费仓库时，逐个配置。
2. 从当前运行宿主确定 Cursor 或 Codex。云端环境设置对话、或用户明确要求配置云端时，执行[云端配置](#云端配置)。普通本地项目对话执行[本地安装](#本地安装)。只有目标项目或环境无法从会话确定时，才向用户询问。
3. 检查 Bash、Python 3、Git、curl 和 `gh`，补齐缺失工具。确认 `gh` 能访问消费仓库。通过宿主的环境设置保存所需凭据，凭据留在密钥设置中。
4. 执行对应安装命令，按[保存并验证](#保存并验证)提交并推送仓库配置。配置云端时，再通过宿主的环境配置工具或设置界面保存安装和新任务启动步骤，完成 Build 或发布环境，让后续独立 agent 能使用保存的配置。
5. 完成[安装验证](#保存并验证)，最后报告实际结果。执行中能自行解决的问题继续处理；只有账号授权、用户持有的凭据、平台要求用户亲自点击的操作才交给用户。交接时先完成其余工作，再指出具体环境和剩余操作。

下面的命令和平台步骤供你执行，无需让用户复制命令或另写一段安装提示词。

### 云端配置

从消费仓库运行当前宿主的命令。安装器下载[最新正式 Release](https://github.com/chancheuklap/multi-model-workflow/releases/latest)，并生成仓库的云端准备配置。

Codex：

```sh
curl -fsSL https://raw.githubusercontent.com/chancheuklap/multi-model-workflow/main/scripts/install-mmw-v5-cloud.sh | bash -s -- --host codex --cloud
```

Cursor：

```sh
curl -fsSL https://raw.githubusercontent.com/chancheuklap/multi-model-workflow/main/scripts/install-mmw-v5-cloud.sh | bash -s -- --host cursor --cloud
```

检查已有环境步骤，移除旧 v5 或固定版本的安装调用，保留项目其他依赖和服务的准备命令。随后完成当前宿主的平台设置：

#### Codex Cloud

安装器写入 `.agents/cloud-setup.sh`，并在 `AGENTS.md` 中登记准备入口。在当前云端环境的设置中：

1. 在 **Install script** 中加入 `bash .agents/cloud-setup.sh`，从对应消费仓库执行。
2. 在 **Start skill** 中写明：每个新任务开始工作前，在对应消费仓库执行 `bash .agents/cloud-setup.sh` 一次。
3. 保留已有安装和服务启动步骤，保存配置，完成 **Publish** 或 **Republish**。

多仓库环境在每个消费仓库执行各自的准备脚本。平台保存的 Install script 和 Start skill 才会供后续任务使用；仓库的 `AGENTS.md` 记录入口，`.codex` 本地 worktree 环境配置不能代替云端设置。[Codex 官方环境说明](https://learn.chatgpt.com/docs/environments/cloud-environments)。

#### Cursor Cloud

安装器写入 `.cursor/cloud-setup.sh`，并把准备脚本接入 `.cursor/environment.json` 的 `install` 和 `start`，保留已有命令和其他配置。在当前云端环境的设置中：

1. 将 **environment.json location** 指向消费仓库的 `.cursor/environment.json`。
2. 多仓库环境在环境的安装和启动命令中，接入每个消费仓库的 `bash .cursor/cloud-setup.sh`，从对应仓库执行。
3. 保存环境，完成并启用成功的 **Build**。检查保存的个人或团队环境实际使用了本次配置。

Cursor 使用保存的环境配置，只有文件绑定生效后，仓库的 `environment.json` 才会被读取。[Cursor 官方环境说明](https://cursor.com/docs/cloud-agent/setup)。

环境准备时安装一次，让技能就绪。每个新云端任务启动时再次执行准备脚本，主动获取最新发布版，避免从环境缓存一直使用旧 MMW。继续已有任务时不重装；一个 night 使用它开始时的同一份运行时。

通过平台的网络设置允许安装所需的 `raw.githubusercontent.com`、`github.com`、`release-assets.githubusercontent.com`，以及 `gh` 所需的 `api.github.com`。准备脚本下载固定名称的最新发布包 `mmw-v5-cloud.zip`，每个独立 agent 的环境都从自己的准备步骤获得运行时。

### 本地安装

从消费仓库运行当前宿主的命令。

Codex：

```sh
curl -fsSL https://raw.githubusercontent.com/chancheuklap/multi-model-workflow/main/scripts/install-mmw-v5-cloud.sh | bash -s -- --host codex
```

Cursor：

```sh
curl -fsSL https://raw.githubusercontent.com/chancheuklap/multi-model-workflow/main/scripts/install-mmw-v5-cloud.sh | bash -s -- --host cursor
```

本地命令安装最新发布版，保留模型设置，不改云端配置。安装后让宿主重新加载技能列表。其他人普通 clone 不会取得 MMW 安装产物；需要的人自行安装。

### 保存并验证

两种宿主安装同一个完整包，各自读取安装目录中的模型配置：

| 宿主 | 安装位置 | 项目模型配置 |
| --- | --- | --- |
| Codex | `.agents/` | `.agents/models.json` 中的 `rows.codex` |
| Cursor | `.cursor/` | `.cursor/models.json` 中的 `rows.cursor` |

安装器保留已有目标 `models.json`。首次 Codex 安装缺少该文件时，带入旧 `.cursor/models.json` 的 `rows.codex`；没有旧设置才使用默认值。Cursor 同时发现 `.cursor/skills/` 和 `.agents/skills/`，两种宿主各用自己的工作目录，避免同名技能重复。

安装器把 MMW 自带文件登记到 Git 本地排除清单；以前已提交的对应运行时文件会退出 Git 跟踪，磁盘副本保留。项目自己的技能和其他文件继续正常管理。

在授权分支提交并推送模型配置。云端配置还要提交生成的准备脚本，以及 Cursor 的 `environment.json` 或 Codex 的 `AGENTS.md` 改动。让后续环境准备能读取包含配置的分支，模型配置进入新 night 的基线。MMW 技能、工具、board 和安装目录里的 `plugin.json` 留在本地，不提交运行时或版本锁定文件。

完成前验证：

- 从安装目录的 `plugin.json` 读取实际版本，确认已有模型配置保留。
- 在宿主的技能列表确认 `dispatch`、`research` 已加载，运行已安装的派发工具，确认读取当前宿主的模型配置。
- 云端配置须确认平台保存了安装和启动设置，Cursor Build 或 Codex 环境发布成功，并用独立 checkout 验证已提交的准备脚本能重新安装。Coordinator 和下级 agent 使用的环境都需要此配置。

最后简短报告安装位置、实际版本、验证结果，以及云端环境是否已经发布。仅安装当前机器的文件不算完成云端配置。尚未启动新的云端任务时，明确云端任务实测未进行。确有用户才能完成的操作时，报告具体剩余操作。

## 更新和使用

重新运行安装命令会主动获取最新正式 Release，保留项目模型设置。仓库不记录待安装版本，不使用固定 tag、commit 或 `--ref`。准备新环境和启动新云端任务时自动执行；正在运行的 night 不替换运行时。

以前的全局 v5 plugin、将完整安装目录提交 Git、复制本地安装目录给云端 agent、固定版本安装均已退役，不能作为本文的替代安装方式。已用旧方法安装的消费仓库，执行新的对应安装命令迁移，并提交退出运行时跟踪的改动。

Git 和 GitHub 命令从消费仓库运行。技能之间按名字调用，reference 使用相对于所在文档的链接；工具从安装目录定位。完整工作步骤由 **dispatch** 及其角色 reference 提供，任务板设置页只编辑当前宿主的模型配置。

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
