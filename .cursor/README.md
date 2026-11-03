# MMW v5 cloud edition

本目录是一套完整的 MMW v5 云端版本，包含全部技能、工具、任务板、模型配置及版本清单。共同专业方法和标准保留原文，涉及派发的角色、输入、通信和回报按本版工作链适配。

本版的打包和运行都只读取本目录，不需要本地版目录，也不在发布时拼装另一版的文件。

## 与本地版分开使用

- 本地版仍是 `mmw-v5/` 完整 plugin，使用本机 MMW_HOME、独立会话与原有通知链。
- 使用时在本地版与云端版中选择一套完整安装。安装云端版时，本地 Coordinator 和 Cloud Worker 都使用云端版的技能、工具与配置。
- Cursor 的云端发布包包含 `.cursor/skills/`、`.cursor/tools/`、`.cursor/board/`、`.cursor/models.json` 和版本清单。把已发布云端包解压到使用 MMW 的项目根目录，提交到项目分支并推送。本地和云端 Cursor 都从这个项目的 `.cursor/skills/` 发现技能。
- 首次安装或实际授权变更时才更新；普通开夜复用已有安装／配置。不新增版本清单或锁系统。
- 模型配置只有项目 `.cursor/models.json` 一份，Codex plugin 也读取这份项目配置。`rows.codex` 和 `rows.cursor` 分别配置各宿主的六个角色。Codex 默认全部使用 `gpt-6.1-sol`、`high`；Cursor 默认全部使用 `grok-4.7`、`high`、`256k`、fast。`inherit` 沿用宿主；填写实际原生工具支持的值。云端没有本地 CLI 扫描、runner 或模型目录缓存。

## 使用

Codex 通过本机 plugin 安装云端版 `mmw-v5-cloud`；本地会话版的 plugin 名称是 `mmw-v5`，切换前卸载它。两者从同一个 GitHub marketplace 分发，选择一套安装。

Codex：

```sh
codex plugin marketplace add chancheuklap/multi-model-workflow --ref main
codex plugin remove mmw-v5@mmw-v5
codex plugin add mmw-v5-cloud@mmw-v5
```

Cursor 使用项目安装，不安装云端 plugin。在使用项目中执行以下命令，下载已发布的云端包，安装到 Git 仓库根目录的 `.cursor/`。安装保留已有 `.cursor/models.json`，并保留其他 Cursor 文件。如先前安装过本地版 MMW plugin，先卸载它。

```sh
curl -fsSL https://raw.githubusercontent.com/chancheuklap/multi-model-workflow/main/scripts/install-mmw-v5-cloud.sh | bash
```

开发版本可从指定 GitHub 分支、tag 或 commit 安装，例如当前 `mmw-v5` 分支：

```sh
curl -fsSL https://raw.githubusercontent.com/chancheuklap/multi-model-workflow/mmw-v5/scripts/install-mmw-v5-cloud.sh | bash -s -- --ref mmw-v5
```

安装后提交并推送 `.cursor/`，让本地和云端 Cursor 使用同一份技能、工具和配置。使用项目中的 Agent 只读取 `.cursor/` 安装副本，不读取开发源目录；不把 MMW 安装到共享技能目录 `.agents/`。

技能之间按技能名调用；reference 使用相对于所在文档的 Markdown 链接。工具路径相对于技能目录解析，命令仍在使用项目的工作目录执行。例如 `dispatch` 的 `../../tools/dispatch/scripts/dispatch.sh` 相对于 `skills/dispatch/`，不相对于终端当前目录。

本地 Coordinator 在选定开夜分支调用项目的 `dispatch` 技能，管理 Issue、依赖、PR 最终正文和合并。Cloud Worker 在自己的分支写测试和代码，首次提交并推送后创建指向 NIGHT 的 draft PR；它调用 `code-review` 组织三轴审查、处理问题，再返回工作报告。Coordinator 调用 `pr` 将实施、审查处理和验证结果写入同一 PR 正文，合并到 NIGHT 后关闭 ticket，按依赖推进后续工作。任务完成报告不重复写入 Issue 评论。

Cursor 使用原生 `Task` 的 cloud 环境派发 Worker，从 Task 返回正文读取问题和报告，用 `resume` 指定原 Agent ID 继续工作。Worker 需要 Coordinator 答复时，返回问题并结束本轮；Coordinator 收到后作答并恢复同一个 Worker。Task 的 Completed 通知表示一次调用返回，ticket 是否完成取决于实际合并结果。`max_workers` 限制正在执行的 Worker 回合；等待答复时 ticket 仍归原 Worker，继续执行时使用原 Agent ID。

在 Coordinator 的使用项目目录中，解析工具绝对路径后：

```text
dispatch.sh status SPEC --into NIGHT
dispatch.sh status N --ticket --into NIGHT
models.py row junior-worker codex --at RUNTIME_COMMIT
models.py row review-axis cursor --at RUNTIME_COMMIT
models.py show --at RUNTIME_COMMIT
dispatch.sh land PR --into NIGHT --head FULL_SHA --check '项目实际验证命令'
dispatch.sh board --port 47100
```

`models.py` 使用 `python3` 调用，`dispatch.sh` 使用 Bash。board 在本地运行，沿用共同界面，展示普通 GitHub 工作记录与真实依赖／合并，不推测云端 Agent 活跃状态。配置编辑写项目文件，提交后供下一次运行使用。标签初始化由本地 Coordinator 在项目设置时运行 `tools/setup-mmw/scripts/labels.py`；不迁移私有事件。

Cursor 的本地 Task 派发 Cloud Worker、读取返回正文、resume 原 Agent 并收到答复已实测通过；Cloud Worker 并行派出三个审查代理并收到返回也已实测通过。真实代码推送和 draft PR 创建尚未实测。Codex 的云端原生派发与续做尚未实测；模型配置中的宿主名称不代表该宿主已提供对应工具。

## 开发与打包

开发仓库运行 `python3 scripts/release-mmw-v5.py package --edition cloud --output /tmp/mmw-v5-cloud.zip`。只打包同一个 HEAD 中已提交的 `mmw-v5-cloud/` 内容；不安装、不发布。main 发布在同一 Release 附上两版 ZIP，不在 GitHub 跑测试。
