# Workflow Orchestration

这个上下文定义一项工作如何获得稳定身份、隔离目录和分支边界。它不定义各技能内部的业务步骤。

## Language

**MMW 任务（MMW task）**：
绑定到一个任务分支和一个任务 worktree 的持久工作单元。普通交付通常一份 spec 一个 MMW 任务；Wayfinding map、decision chain 和并行结果各自使用独立 MMW 任务。
_Avoid_: 对话、主线程、临时会话

**slug**：
一项普通任务的稳定标识，形状是 `<类型>-<短语>`。宿主分支命名空间、日期和 issue 编号不属于 slug。
_Avoid_: 分支名、worktree 目录名、任务编号

**任务 worktree**：
宿主为一个 MMW 任务准备的隔离 checkout。worktree 的物理目录不参与任务身份判断。
_Avoid_: 仓库副本、任务目录

**任务分支**：
绑定当前 MMW 任务并承载该任务全部持久提交的 Git branch。主 agent 只在当前任务分支的 worktree 中工作。
_Avoid_: 主分支、目标仓库默认分支

**结果分支**：
subagent 在独立结果 worktree 中完成一项派发后交回的 Git branch。主 agent 必须按分支名、HEAD SHA 和基点 SHA 验证后才能集成。
_Avoid_: 临时分支、subagent 分支

**基点**：
一次结果派发开始时任务分支的提交 SHA。它界定结果 diff，并参与结果验证。
_Avoid_: merge-base、起始分支名

**路线**：
`/mmw-start` 根据请求选择的下一项 MMW 技能。路线只决定流程入口，不改变任务范围。
_Avoid_: 方案、实现路径

**handoff**：
把当前对话压缩成另一位 agent 可继续使用的上下文文档。handoff 不改变 MMW 任务、任务分支或交付状态。
_Avoid_: 报告、任务归档
