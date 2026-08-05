# Multi-Model Workflow

多模型工作流（Multi-Model Workflow，MMW）是一套面向软件开发 agent 的完整工作流。它把需求澄清、调查、设计、计划、实现、审查、集成和发布连接成一条可验证的交付路径。

## 设计机制

MMW 把判断与动作分开：`mmw/skills/` 定义每一步何时发生、完成条件是什么；`mmw/cli/` 负责 worktree、issue、领域文档、Wiki 和结果集成等机械动作。

同一套技能语义会按宿主物化。Codex App 是主运行面：写入代码的角色在独立后台 Worktree 任务中执行；调查、计划、设计和审查使用隔离的原生 subagent。每份报告都要回到当前源码或运行结果验证，验收通过后才会集成。

`.mmw.json` 保存目标仓库的模型、标签和路径合同。issue tracker 保存工作状态，领域文档保存共同语言，GitHub Wiki 保存已经交付的设计。技能不复制这些项目事实，只在需要时通过 `mmw` 读取。

## 通过两张图理解 MMW

README 只说明设计机制。技能之间的触发条件、产物、人工审批关卡和 Codex Worktree 边界都放在下面两张图中。

### 完整工作流

[![MMW 完整工作流](docs/assets/mmw-workflow-overview.svg)](docs/assets/mmw-workflow-overview.svg)

[打开全尺寸图](docs/assets/mmw-workflow-overview.svg)

### `mmw-wayfinder` 工作流

[![mmw-wayfinder 工作流](docs/assets/mmw-wayfinder-workflow.svg)](docs/assets/mmw-wayfinder-workflow.svg)

[打开全尺寸图](docs/assets/mmw-wayfinder-workflow.svg)

需要缩放和平移时，克隆仓库后直接在浏览器打开 [`mmw-skill-map.html`](mmw-skill-map.html)。
