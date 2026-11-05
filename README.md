# MMW v5

MMW 提供开发项目所用的技能、agent 派发工具和任务板。当前工作版本是 `mmw-v5-cloud/`；Coordinator、Worker、审查轴和 verifier 在云端运行。

在 Cursor 或 Codex 的项目对话、云端环境设置对话里发送：

> https://github.com/chancheuklap/multi-model-workflow
>
> 帮我配置 MMW。

agent 按本文完成安装、保存配置和验证。用户无需复制命令或提供安装参数。

## 安装

### 给安装 agent：完成配置

1. 确定用户要开发的消费仓库和当前宿主。MMW 链接提供安装说明，只有开发 MMW 本身时才把 MMW 仓库作为消费仓库。多仓库环境逐个配置。
2. 检查 Bash、Python 3、Git、curl 和 `gh`，补齐缺失工具，确认能访问消费仓库。所需凭据保存在宿主的密钥设置中。
3. 已有旧项目级安装时，先执行[更新和迁移](#更新和迁移)中的清理，保留模型设置。普通本地项目对话执行[本地安装](#本地安装)；云端环境设置对话或用户要求配置云端时，执行[云端配置](#云端配置)。
4. 提交并推送仓库配置，让环境准备能读取包含配置的分支，再完成云端平台的 Build 或发布。执行[验证](#验证)，最后报告实际结果。

能自行解决的问题继续处理。只有目标项目无法确定、账号授权、用户持有的凭据或平台要求用户亲自点击的操作才交给用户；交接前完成其余工作，并指出具体环境和剩余操作。

### 安装位置

Cursor 和 Codex 使用相同的安装布局。本地安装在用户目录 `~/.agents/`；云端安装在各自隔离仓库的 `.agents/`。`~` 表示本机用户主目录。

| 内容 | 位置 |
| --- | --- |
| 本地 MMW 技能 | `~/.agents/skills/mmw/` |
| 本地 MMW 工具、任务板和版本信息 | `~/.agents/mmw/` |
| 云端 MMW 技能 | 消费仓库的 `.agents/skills/mmw/` |
| 云端 MMW 工具、任务板和版本信息 | 消费仓库的 `.agents/mmw/` |
| 当前项目的模型配置 | 消费仓库的 `.agents/models.json` |

两家宿主都发现用户级和项目级 `.agents/skills/` 下的技能。MMW 安装在独立的 `mmw/` 目录中，更新会替换 MMW 目录，清除已退役的安装文件，其他个人技能和项目自有技能保留。[Codex 技能位置](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)、[Cursor 技能位置](https://cursor.com/help/customization/skills)。

本地运行时在消费仓库之外，安装器不修改 `.gitignore`。云端只在 `.gitignore` 排除 `/.agents/mmw/` 和 `/.agents/skills/mmw/` 两个固定目录，新增文件自动覆盖。两种安装方式都不修改项目的 `AGENTS.md`。

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

安装器下载[最新正式 Release](https://github.com/chancheuklap/multi-model-workflow/releases/latest) 的完整 `mmw-v5-cloud.zip`，安装到用户目录，并为当前项目保留或创建模型配置。本机安装供不同项目共用；其他人 clone 消费仓库不会获得这份安装。

### 云端配置

从每个消费仓库运行当前宿主的命令。

Codex：

```sh
curl -fsSL https://raw.githubusercontent.com/chancheuklap/multi-model-workflow/main/scripts/install-mmw-v5-cloud.sh | bash -s -- --host codex --cloud
```

Cursor：

```sh
curl -fsSL https://raw.githubusercontent.com/chancheuklap/multi-model-workflow/main/scripts/install-mmw-v5-cloud.sh | bash -s -- --host cursor --cloud
```

安装器在当前隔离仓库的 `.agents/` 中安装 MMW，并写入 `.agents/cloud-setup.sh`。该脚本供后续独立环境自行安装，不复制本机的安装文件。提交模型、准备脚本和两条目录排除规则后，通过宿主的环境配置工具或设置界面完成平台配置：

- **Codex Cloud**：在平台的 **Install script** 中接入 `bash .agents/cloud-setup.sh`；在 **Start skill** 中要求每个新任务工作前执行同一命令一次。多仓库环境从每个消费仓库执行各自脚本。保留原有步骤，保存并 **Publish** 或 **Republish**。[官方环境说明](https://learn.chatgpt.com/docs/environments/cloud-environments)。
- **Cursor Cloud**：安装器已将准备脚本接入 `.cursor/environment.json` 的 `install` 和 `start`。将保存环境的 **environment.json location** 指向该文件；多仓库环境在安装和启动步骤中接入各仓库的准备脚本。保留已有依赖和服务配置，完成并启用成功的 **Build**。[官方环境说明](https://cursor.com/docs/cloud-agent/setup)。

自动准备由平台保存的安装和启动设置负责。项目 `AGENTS.md` 不承担 MMW 安装或环境配置登记。

通过平台网络设置允许安装所需的 `raw.githubusercontent.com`、`github.com`、`release-assets.githubusercontent.com`，以及 `gh` 所需的 `api.github.com`。本机用户技能不会自动复制到云端；Coordinator 和下级 agent 的每个独立环境都需执行自己的准备步骤。

每个新云端任务启动时主动获取最新发布版，避免一直沿用缓存。继续已有任务时不重装；一个 night 使用开始时选定的同一份运行时。

### 模型配置和工具

`.agents/models.json` 留在消费仓库，包含 `rows.cursor` 和 `rows.codex`。安装器保留已有配置；首次创建时带入旧 `.cursor/models.json` 中已有的宿主模型行，没有旧设置才使用默认值。

工具从对应安装目录定位，从消费仓库运行。云端使用项目的 `.agents/mmw/tools/dispatch/scripts/dispatch.sh`；本地例如：

```sh
bash ~/.agents/mmw/tools/dispatch/scripts/dispatch.sh row researcher --host HOST
```

HOST 由 agent 填入当前宿主 `cursor` 或 `codex`。模型命令和任务板按宿主选择模型行，按当前消费仓库读取配置，不从全局运行时目录读取项目设置。模型配置进入新 night 的基线，任务板设置页只修改当前宿主的模型行。

### 验证

- 从对应安装目录的 `mmw/plugin.json` 读取实际版本，在宿主技能列表确认 `dispatch`、`research` 已发现。
- 从消费仓库运行已安装工具，确认读取该项目、该宿主的模型行。已有模型选择和项目自有文件保留。
- 仓库只提交模型和云端准备配置。安装命令不改 `AGENTS.md`；本地不改 `.gitignore`，云端只用固定目录规则。
- 云端配置须确认平台设置已保存，Cursor Build 或 Codex 环境发布成功。使用独立 checkout 和独立用户目录验证保存的准备脚本能重新安装。

最后报告实际安装位置、版本、验证结果和环境发布状态。未启动真实云端任务时，说明云端任务实测未进行。仅在当前机器装好文件不算完成云端配置。

## 更新和迁移

重新运行安装命令主动获取最新正式 Release，保留项目模型设置。仓库不锁定运行时版本，已运行的 night 不替换运行时。

迁移旧项目级安装时，清理仓库 `.agents/`、`.cursor/` 中 MMW 提供的技能、工具、board、版本文件，以及 MMW 生成的 Git 排除区块和 `AGENTS.md` 准备说明。项目自有技能、规则、服务启动配置保留；模型设置按用户要求保留或重置。仓库只保存模型和云端准备配置。

旧宿主 marketplace plugin、本地按项目复制运行时、完整目录提交 Git、固定 tag 或 `--ref` 安装均已退役。

## 开发和发布

在 MMW 开发仓库的 `dev` 分支准备版本号：

```sh
python3 scripts/release-mmw-v5.py bump
```

运行相关本地检查后提交并推送到 `dev`。`bump` 只改云端版的 plugin 清单，不提交、不推送、不发布。

经 owner 授权合并并推送到 `main` 后，GitHub Actions 按已提交版本创建 tag 和 GitHub Release，附上固定名称的 `mmw-v5-cloud.zip`。GitHub 不运行测试、不改变版本号。同一版本号不能用于另一提交。

在本地检查已提交版本的包：

```sh
python3 scripts/release-mmw-v5.py package --output /tmp/mmw-v5-cloud.zip
```
