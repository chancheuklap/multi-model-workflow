# Prototype 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW Prototype。当前发布技能仍位于 `mmw/skills/mmw-prototype/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段

第一阶段已经完成上游 `SKILL.md`、`LOGIC.md`、`UI.md` 和 `agents/openai.yaml` 的逐行中文翻译。翻译保留 logic 与 UI 两条分支、共同规则、可移植 logic module、引导式走查、UI 子形态、variant switcher、用户反馈迭代和一手来源留存，不加入 MMW prototype 资产接线。

第二阶段已经形成单文件精简稿。它只应用已经确认的调整：把 prototype 改为持续迭代的仓库资产；允许后端脚本、Logic HTML 和 UI/UX 在同一份 prototype 中连续演进；按是否需要用按钮驱动状态模型选择最小后端脚本或 Logic HTML；只在 UI 结构方向未定时生成多个变体；允许达到项目质量要求的可移植内容被直接复用；删除外部系统取证分支、固定三状态字面量和单独的人工审批关卡。

第三阶段已经在 `candidate/` 形成三文件候选。`candidate/SKILL.md` 负责每轮问题、资产路径、后端分支和 Logic HTML 的手动调用接线；`candidate/UI.md` 负责 UI/UX 形态、按需变体和前后端对应；`candidate/capture.md` 负责保存用户原话、选中产物、否定约束和下游输入。Logic HTML 和普通记录可视化都先询问用户；用户确认后手动调用 `/wait-what`，完成结果再交回此前等待的 Prototype 流程。当前发布技能仍不修改。

## 文件

| 文件 | 作用 |
| --- | --- |
| [upstream-1.2.2.zh-CN.md](upstream-1.2.2.zh-CN.md) | 上游 1.2.2 的逐行中文翻译基线 |
| [translation-audit.md](translation-audit.md) | 术语选择、逐行完整性与无新增语义检查 |
| [simplified.zh-CN.md](simplified.zh-CN.md) | 以精确翻译为基线形成的单文件精简稿，不包含 MMW 路径、worktree、调用方回传或宿主动作 |
| [candidate/](candidate/) | 在精简稿外层增加 MMW 接线的三文件候选；不会被 `mmw skills materialize` 物化 |

当前发布技能保持不变。
