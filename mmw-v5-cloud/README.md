# MMW v5 cloud edition

本目录是一套完整的 MMW v5 云端版本，包含全部技能、工具、任务板、模型配置及版本清单。共同专业方法和标准保留原文，涉及派发的角色、输入、通信和回报按本版工作链适配。

本版的打包和运行都只读取本目录，不需要本地版目录，也不在发布时拼装另一版的文件。

## 与本地版分开使用

- 本地版仍是 `mmw-v5/` 完整 plugin，使用本机 MMW_HOME、独立会话与原有通知链。
- 使用时在本地版与云端版中选择一套完整安装。安装云端版时，本地 Coordinator 和 Cloud Worker 都使用云端版的技能、工具与配置。
- 云端发布包包含 `.agents/skills/`、`.agents/tools/`、`.agents/board/`、`.agents/models.json` 和发布包本身的 `plugin.json`。把已发布云端包安装到使用 MMW 的项目，提交到项目分支并推送。
- 首次安装或实际授权变更时才更新；普通开夜复用已有安装／配置。不新增版本清单或锁系统。
- 模型配置只有项目 `.agents/models.json` 一份。`inherit` 沿用宿主；填写实际原生工具支持的 model／effort。云端没有本地 CLI 扫描、runner 或模型目录缓存。

## 使用

本地 Coordinator 在选定开夜分支调用项目的 `dispatch` 技能；它负责全部 GitHub 操作。Cloud Worker 使用自己的分支和 Git 权限，直接交回问题、提交、审查与验证证据。三轴 Reviewer 使用共同 `code-review` 技能。

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

原生云端启动、父子返回／继续、三级 Agent 树和 Git 推送能力需在 Codex／Cursor 实际环境分别验收。本版本的提示词与机械工具不会用虚构工具名或新 relay 伪造宿主支持。此目录的落地不表示已完成账户级云端验收。

## 开发与打包

开发仓库运行 `python3 scripts/release-mmw-v5.py package --edition cloud --output /tmp/mmw-v5-cloud.zip`。只打包同一个 HEAD 中已提交的 `mmw-v5-cloud/` 内容；不安装、不发布。main 发布在同一 Release 附上两版 ZIP，不在 GitHub 跑测试。
