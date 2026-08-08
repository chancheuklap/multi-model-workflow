# Prototype 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW Prototype。当前发布技能仍位于 `mmw/skills/mmw-prototype/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段

第一阶段已经完成上游 `SKILL.md`、`LOGIC.md`、`UI.md` 和 `agents/openai.yaml` 的逐行中文翻译。翻译保留 logic 与 UI 两条分支、共同规则、可移植 logic module、引导式走查、UI 子形态、variant switcher、用户反馈迭代和一手来源留存，不加入 MMW prototype 资产接线。

第二阶段已经形成单文件精简稿。它只应用已经确认的调整：把 prototype 改为持续迭代的仓库资产；允许后端脚本、Logic HTML 和 UI/UX 在同一份 prototype 中连续演进；按是否需要用按钮驱动状态模型选择最小后端脚本或 Logic HTML；只在 UI 结构方向未定时生成多个变体；允许达到项目质量要求的可移植内容被直接复用；把外部系统取证分支移出本技能、删除固定三状态字面量和单独的人工审批关卡。

第三阶段已经在 `../candidate/skills/mmw-prototype/` 形成四文件候选。`../candidate/skills/mmw-prototype/SKILL.md` 负责每轮问题、资产路径、后端工作面和共同规则；`../candidate/skills/mmw-prototype/LOGIC.md` 负责 Logic HTML；`../candidate/skills/mmw-prototype/UI.md` 负责 UI/UX 形态、按需变体和前后端对应；`../candidate/skills/mmw-prototype/capture.md` 负责保存用户原话、选中产物、否定约束和下游输入。

prototype 的作用是把一个还很松的想法磨清楚。想法磨清楚之后，承载它的后端脚本、接口合同、状态模型和界面 mockup 就是下游可以直接参考或复用的内容，因此 prototype 保存进仓库供下游按精确路径引用。可复用的依据是想法已经被走查磨清楚，不是这份代码的工程完备度：候选明确不写测试、不写当前问题用不到的错误处理、不做抽象，并要求文件名、目录名、页面标题和路由一眼看得出这是 prototype。

Logic HTML 是 prototype 自己的一个工作面，方法写在 `../candidate/skills/mmw-prototype/LOGIC.md`，不再绕经 `/wait-what`。反过来，用户看不懂一套业务逻辑时可以调 `/wait-what`，由它移交 `/mmw-prototype`。当前发布技能仍不修改。

外部系统取证已经移交 `/mmw-research`（见 `mmw/skill-rebuilds/research/candidate/EVIDENCE.md`）。分界是**验的是谁**：prototype 验我们自己要写的那套东西成不成立，判据是用户走查；取证验外部世界既有的表现，判据是事先写死的通过判据加实测数据。`../candidate/skills/mmw-prototype/SKILL.md` 第 1 节的适用性判断表里有一行把这类问题直接转出去。

## 文件

| 文件 | 作用 |
| --- | --- |
| [upstream-1.2.2.zh-CN.md](upstream-1.2.2.zh-CN.md) | 上游 1.2.2 的逐行中文翻译基线 |
| [translation-audit.md](translation-audit.md) | 术语选择、逐行完整性与无新增语义检查 |
| [simplified.zh-CN.md](simplified.zh-CN.md) | 以精确翻译为基线形成的单文件精简稿，不包含 MMW 路径、worktree、调用方回传或宿主动作 |
| [candidate/](../candidate/skills/mmw-prototype/) | 在精简稿外层增加 MMW 接线的三文件候选；不会被 `mmw skills materialize` 物化 |

当前发布技能保持不变。
