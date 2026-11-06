# MMW v5

MMW 是 Codex 和 Cursor 共用的开发工作流插件，包含技能、agent 派发工具和任务板。当前版本的源码在 `mmw-v5-cloud/`。Coordinator 和下级 agent 在云端执行工作流。

向当前宿主的 agent 发送仓库链接并说“帮我配置 MMW”：

> https://github.com/chancheuklap/multi-model-workflow

安装 agent 按下文完成宿主插件安装，保留用户的模型选择，再验证技能发现和工具执行。需要用户操作插件目录或账号设置时，先完成其余工作，再指出剩余操作。

## 安装原理

采用 [pstack](https://github.com/cursor/plugins/tree/main/pstack) 的结构，同一个插件目录提供通用 `plugin.json` 和 `.cursor-plugin/plugin.json`。Codex 和 Cursor 各自的 marketplace 清单指向这份插件。宿主负责下载、启用和更新。共享工具、默认模型配置和任务板都在 `skills/dispatch/runtime/`，属于同一个 dispatch 技能包。

```text
MMW GitHub 仓库
  ├─ Codex marketplace ── Codex 安装并登记插件 ── 对话获得 MMW 技能
  └─ Cursor marketplace ─ Cursor 安装并登记插件 ─ 对话获得 MMW 技能
                              │
                              └─ dispatch 技能包
                                  └─ runtime/：工具、默认模型配置、任务板

执行环境的 ~/.agents/models.json ── 派发工具和任务板读取模型选择
```

本地、云端、单仓库和多仓库都使用这份插件。安装范围由宿主管理；消费仓库不保存 MMW 技能、工具或模型副本。其他人 clone 消费仓库不会因此安装 MMW。

本地宿主提供技能目录时，dispatch 直接验证并使用随包 runtime。云端宿主提供技能资源 URI 时，dispatch 首次使用会读取同一技能包的清单和资源，在执行环境中还原文件并校验 SHA-256。二进制字体通过随包的 base64 文本资源还原。每份内容使用独立缓存目录，整个运行复用已经解析的版本；资源 URI 不作为本地目录使用。

## Codex

Codex CLI 的原生安装命令：

```sh
codex plugin marketplace add chancheuklap/multi-model-workflow
codex plugin add mmw-v5-cloud@mmw-v5
codex plugin list --json
```

Codex App 可通过 Plugins 目录安装已配置 marketplace 中的 **MMW v5 Cloud**。IDE 扩展当前不提供插件入口，使用 Codex App 或 CLI 安装。安装后新开对话，运行 `setup-mmw`，确认 `dispatch` 和 `research` 出现在宿主提供的技能清单中。[Codex 插件说明](https://developers.openai.com/plugins/build/plugins)。

Codex Cloud 需要在发起云端对话的宿主或工作区插件目录中导入并启用 MMW。工作区通过 GitHub 导入自定义插件时，由管理员完成目录导入和授权。[工作区插件管理](https://developers.openai.com/codex/enterprise/plugin-management)。VM 内安装一个独立 Codex CLI 的插件，不代表外层 Cloud 对话已安装。

## Cursor

在 Cursor 的 **Customize → Plugins → Browse Marketplace → Add Marketplace → Import from GitHub** 中导入：

```text
https://github.com/chancheuklap/multi-model-workflow
```

个人使用选择 **User** 范围，安装 **MMW v5 Cloud**。新开对话并运行 `setup-mmw`。这是自定义 marketplace 的导入方式；MMW 尚未作为公共目录条目上架，不能假定 `/add-plugin mmw-v5-cloud` 能直接找到它。[Cursor 插件说明](https://cursor.com/docs/plugins)。

Cursor Cloud 在任务启动时配置 marketplace 插件，同一次运行固定插件版本。官方明确说明了团队 marketplace 的云端加载；个人 GitHub marketplace 是否进入 Cloud 对话，需要在新任务的技能清单中确认。[Cursor Cloud 插件说明](https://cursor.com/help/ai-features/cloud-agents#do-cloud-agents-load-my-team-marketplace-plugins)。

## 给安装 agent：配置与验证

1. 在实际使用 MMW 的宿主安装并启用插件。确认该宿主返回 MMW 的 `dispatch`、`research` 和 `setup-mmw` 技能。云端任务检查云端对话自己的清单。
2. 读取宿主提供的 `setup-mmw` 技能，由它调用 dispatch 的 Runtime 部分解析随包工具。工具使用 Bash 和 Python 3 标准库，无需包管理器。涉及 GitHub 的工作流还需 Git 和已授权的 `gh`。setup-mmw 是可选配置检查，其他技能首次使用时也会准备工具，无需每个 Cloud agent 手动运行 setup。
3. 保留已有 `~/.agents/models.json`。首次使用派发工具时，工具按 `MMW_MODELS_JSON` 环境变量、插件默认模板的顺序创建缺失的用户文件。已有文件保持原字节，不会因插件更新而覆盖。
4. 从每个消费仓库运行解析得到的 `dispatch.sh row researcher --host codex` 或 `--host cursor`。确认读取同一用户模型文件，返回当前宿主的模型行。工具路径来自 dispatch 的 Runtime 部分，不能写死插件缓存目录。
5. 验证随包清单和工具执行成功，报告插件版本、runtime identity、技能发现结果和工具执行结果。云端验收要在新对话中从技能资源准备工具并实际派出子代理；生成派发卡片不能代替宿主启动验证。资源不可读时报告准确的 package、资源和错误。缺少云端宿主的插件导入权限时，报告具体账号操作。

## 模型设置

`~/.agents/models.json` 包含 `rows.codex` 和 `rows.cursor`。同一执行环境的所有仓库共用此文件；任务板只修改当前宿主的模型行。派发工具从消费仓库运行，模型文件始终在当前用户主目录。

独立云端 VM 不继承本机文件。要沿用个人选择，将用户模型文件的完整 JSON 保存为云端环境变量 `MMW_MODELS_JSON`。`setup-mmw` 或首次派发用该值建立用户文件。模型值不是凭据，保存在平台环境设置，无需提交消费仓库。在任务板修改后，更新平台保存的变量，使以后新 VM 继承选择。

## 更新和旧安装迁移

Codex CLI 用 `codex plugin marketplace upgrade mmw-v5` 刷新来源；Cursor 在插件目录更新 marketplace 和插件。宿主决定何时更新已安装版本。MMW 不在消费仓库锁定版本，也不在运行中的 night 切换版本。

原来的 curl 安装器、`~/.agents/skills/mmw/` 松散技能、`~/.agents/mmw/` 运行时和 `.agents/cloud-setup.sh` 已退役。迁移 agent 完成以下清理：

- 先确认原生插件已安装且能被目标对话发现，再移除上述用户目录中的旧 MMW 运行时。保留 `~/.agents/models.json` 和其他个人技能。
- 删除消费仓库中 MMW 专属的旧运行时、模型副本、准备脚本和生成的 Git 排除区块，保留项目自有文件。
- 从 Codex 保存环境的 Install script、Start skill 和 Cursor 保存环境的安装、启动配置中移除旧 MMW 准备命令和手动扫描技能的说明。保留项目依赖和服务步骤，保存并发布环境配置。
- 原来用于播种模型的 `MMW_MODELS_JSON` 继续有效。平台设置必须在对应平台保存；仓库删除准备脚本不会替用户修改已经保存的入口。

云端通过宿主插件配置交付 MMW。项目 `AGENTS.md` 无需登记安装路径。`mmw-v5/` 是历史参考，不作维护。

## 开发和发布

修改 `skills/dispatch/runtime/` 后，运行 `python3 scripts/sync-dispatch-resources.py` 更新资源清单和二进制文本资源，再运行本地检查。`--check` 只检查是否同步。插件执行无需构建步骤。

在 `dev` 分支准备版本：

```sh
python3 scripts/release-mmw-v5.py bump
```

版本准备命令同步更新资源清单中的版本。运行相关本地检查后提交到 `dev`。经 owner 授权合并并推送到 `main` 后，GitHub Actions 按提交版本创建 tag、GitHub Release 和完整的 `mmw-v5-cloud.zip`。GitHub 不运行测试、不改变版本号。同一版本号不能用于另一提交。

```sh
python3 scripts/release-mmw-v5.py package --output /tmp/mmw-v5-cloud.zip
```

ZIP 包含两份宿主清单和技能；工具、默认模型配置、任务板及其文本资源都包含在 dispatch 技能包内。打包使用已提交的资源，本地检查验证资源与原文件的版本和字节一致性。GitHub 发布让自定义 marketplace 可以取得新版，不等于公共插件目录已经审核上架。
