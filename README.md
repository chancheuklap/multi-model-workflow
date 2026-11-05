# MMW v5

MMW 提供开发项目所用的技能、agent 派发工具和任务板。当前工作版本是 `mmw-v5-cloud/`；Coordinator、Worker、审查轴和 verifier 在云端运行。

在 Cursor 或 Codex 的项目对话、云端环境设置对话里发送：

> https://github.com/chancheuklap/multi-model-workflow
>
> 帮我配置 MMW。

agent 按本文完成安装、迁移、保存配置和验证。用户无需选择安装目录或复制命令。

## 安装

### 给安装 agent：完成配置

1. 确定消费仓库、当前宿主和执行环境。MMW 链接提供安装说明，只有开发 MMW 本身时才把 MMW 仓库作为消费仓库。多仓库环境使用平台选定的仓库组。
2. 检查 Bash、Python 3、Git、curl 和 `gh`，补齐缺失工具，确认能访问消费仓库。凭据保存在宿主的密钥设置中。
3. 一次安装完整 MMW，为每个消费仓库保留或创建模型配置。云端配置还需接入平台保存的安装和启动设置。
4. 清理旧安装，提交并推送项目配置，完成环境发布或 Build，执行本文的验证。保留原有依赖、服务和项目技能。

能自行解决的问题继续处理。只有目标项目无法确定、账号授权、用户持有的凭据或平台要求用户亲自点击的操作才交给用户。交接前完成其余工作，并指出具体环境和剩余操作。

### 所有环境使用相同位置

本地和云端、单仓库和多仓库都安装在执行环境用户主目录的 `~/.agents/`。`~` 指当前电脑或 VM 的用户主目录，不是文件系统根目录 `/`。

| 内容 | 位置 |
| --- | --- |
| MMW 技能 | `~/.agents/skills/mmw/` |
| MMW 工具、任务板和版本信息 | `~/.agents/mmw/` |
| 项目模型配置 | 每个消费仓库的 `.agents/models.json` |
| 云端准备入口 | 消费仓库的 `.agents/cloud-setup.sh` |

同一用户环境共用一份完整运行时，其他人 clone 消费仓库只得到项目配置。不同独立 VM 各自安装。同一 VM 的 fresh agent 共用安装，fresh 只表示全新上下文。

安装器只替换 MMW 所属目录，保留其他个人技能和项目自有技能。运行时在仓库之外，不需要 Git 排除规则，也不向项目 `AGENTS.md` 登记安装入口。

### 安装命令

从消费仓库运行当前宿主的命令，本地和云端的安装位置相同。

Codex：

```sh
curl -fsSL https://raw.githubusercontent.com/chancheuklap/multi-model-workflow/main/scripts/install-mmw-v5-cloud.sh | bash -s -- --host codex
```

Cursor：

```sh
curl -fsSL https://raw.githubusercontent.com/chancheuklap/multi-model-workflow/main/scripts/install-mmw-v5-cloud.sh | bash -s -- --host cursor
```

安装器下载[最新正式 Release](https://github.com/chancheuklap/multi-model-workflow/releases/latest) 的完整 `mmw-v5-cloud.zip`。不指定仓库时，在 Git 仓库内运行会配置当前仓库；在仓库外运行只安装共享运行时。

可以在命令末尾传入多个仓库路径，一次下载并安装，为每个仓库分别保留或创建模型配置。路径由安装 agent 根据实际环境填写。

```sh
curl -fsSL https://raw.githubusercontent.com/chancheuklap/multi-model-workflow/main/scripts/install-mmw-v5-cloud.sh | bash -s -- --host codex /workspace/repo-a /workspace/repo-b
```

### 云端准备配置

首次配置云端时，在安装命令中加入 `--cloud`。该参数只生成项目准备入口并接入 Cursor 环境文件，安装位置仍是用户主目录。多仓库时一次传入整个仓库组。

```sh
curl -fsSL https://raw.githubusercontent.com/chancheuklap/multi-model-workflow/main/scripts/install-mmw-v5-cloud.sh | bash -s -- --host codex --cloud /workspace/repo-a /workspace/repo-b
```

Cursor 使用同一命令，将 `--host codex` 换成 `--host cursor`。

安装器为消费仓库写入相同的 `.agents/cloud-setup.sh`。它从最新公开安装器准备共享运行时，第一项参数是宿主，其余参数是仓库路径。未传宿主时沿用 `codex`，未传仓库时使用脚本所在仓库。这样现有 Codex 环境的 `bash .agents/cloud-setup.sh` 入口仍然有效。

保存平台配置时，每个环境接入一次准备命令。多仓库示例：

```sh
bash /workspace/repo-a/.agents/cloud-setup.sh codex /workspace/repo-a /workspace/repo-b
```

- **Codex Cloud**：将准备命令接入保存环境的 **Install script** 和新任务的 **Start skill**，保存并 **Publish** 或 **Republish**。多仓库环境使用完整仓库组的实际路径。[官方环境说明](https://learn.chatgpt.com/docs/environments/cloud-environments)。
- **Cursor Cloud**：单仓库的 `.cursor/environment.json` 已接入 `install` 和 `start`；将保存环境的 **environment.json location** 指向该文件。多仓库时在仓库组的实际安装和启动配置中接入一次准备命令，宿主填 `cursor`。保留原有依赖和服务步骤，完成并启用成功的 **Build**。[官方环境说明](https://cursor.com/docs/cloud-agent/setup)。

不要逐仓库重复安装共享运行时，也不要假定平台会自动合并多个仓库的环境文件。环境工作目录不固定时使用实际绝对路径。仓库中的准备脚本更新不会自行改变平台已保存的仓库组或启动命令；配置 agent 要核对实际保存的入口。

允许安装所需的 `raw.githubusercontent.com`、`github.com`、`release-assets.githubusercontent.com`，以及 `gh` 所需的 `api.github.com`。本机安装文件不自动复制到云端，由每个独立环境的准备步骤获取。

新任务准备时获取最新正式版。已有 night 保持开始时选定的运行时，同一 VM 的下级 agent 不重装；独立 VM 的下级 agent 沿用该 night 选定的版本，不因发布更新而改变。仓库不锁定版本。

### 技能加载和项目模型

VM 内宿主的技能扫描器与当前云端聊天的技能接口是不同入口。验证时分别检查，不能用其中一个空列表判断另一个不支持文件技能。

当 Codex 云端聊天没有同步文件技能清单时，在保存环境的 **Start skill** 中加入：

> MMW 技能位于此环境的 `~/.agents/skills/mmw/`。开始工作时读取这些技能的名称和描述，任务匹配时读取对应 `SKILL.md` 正文。MMW 工具位于 `~/.agents/mmw/`，从目标消费仓库运行。

这段说明让当前聊天读取已安装技能，不表示平台原生清单已经同步。技能目录依据见 [Codex 技能位置](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)、[Cursor 技能位置](https://cursor.com/docs/skills#skill-directories)。

每个仓库的 `.agents/models.json` 包含 `rows.cursor` 和 `rows.codex`。安装器保留已有配置；迁移时保留旧 `.cursor/models.json` 中的宿主模型行，再移除旧文件。

从目标消费仓库运行共享工具，HOST 填当前宿主 `cursor` 或 `codex`：

```sh
bash ~/.agents/mmw/tools/dispatch/scripts/dispatch.sh row researcher --host HOST
```

工具按当前 Git 仓库读取模型配置，按宿主选择模型行。模型配置进入新 night 的基线，任务板设置页只修改当前宿主的模型行。派发给 fresh agent 的任务必须明确消费仓库；接收者进入自己环境中的对应 checkout。

### 验证

- 确认 `~/.agents/mmw/plugin.json` 的版本，技能、工具和任务板完整，消费仓库内没有 MMW 运行时。
- 从各仓库分别运行已安装工具，确认读取各自项目、当前宿主的模型行，原有设置和项目技能保留。
- 重复安装和执行准备脚本，确认结果一致；用独立用户目录、独立 checkout 验证新环境可以重建。
- 核对宿主技能发现与实际加载；Codex 云端聊天和 VM 内 Codex 扫描器分别报告。不要把手动读取文件说成原生自动发现。
- 核对平台保存的安装和启动入口，确认 Codex 发布或 Cursor Build 的实际结果。

最后报告安装位置、版本、验证和环境状态。没有实际保存或发布的平台配置明确标为未完成；当前 VM 安装成功不能代替后续环境自动准备。

## 更新和迁移

重新运行安装命令获取最新正式版。安装器保留项目模型，移除旧的项目 `.agents/mmw/` 和 `.agents/skills/mmw/`、有 MMW 清单标识的旧宿主目录安装，以及 MMW 生成的 Git 排除区块。项目自有技能、规则和服务配置保留。

迁移旧平台设置时，将准备入口改为本文的用户目录安装命令，清除旧的固定版本和仓库内工具路径。旧 `AGENTS.md` 中的 MMW 安装说明由迁移 agent 精确清理，保留其他项目指令；安装器不改项目指令文件。

旧 marketplace plugin、仓库内运行时、完整安装目录提交 Git、固定 tag 和 `--ref` 安装均已退役。`mmw-v5/` 是历史参考，不作维护。

## 开发和发布

在 MMW 开发仓库的 `dev` 分支准备版本号：

```sh
python3 scripts/release-mmw-v5.py bump
```

运行相关本地检查后提交并推送到 `dev`。`bump` 只改云端版 plugin 清单，不提交、不推送、不发布。

经 owner 授权合并并推送到 `main` 后，GitHub Actions 按已提交版本创建 tag、GitHub Release 和固定名称的 `mmw-v5-cloud.zip`。GitHub 不运行测试、不改变版本号。同一版本号不能用于另一提交。

在本地检查已提交版本的包：

```sh
python3 scripts/release-mmw-v5.py package --output /tmp/mmw-v5-cloud.zip
```
