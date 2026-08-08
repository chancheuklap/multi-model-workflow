# Wayfinder 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW Wayfinder。当前发布技能仍位于 `mmw/skills/mmw-wayfinder/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段

第一阶段已经完成上游原文的逐段中文翻译。翻译保持上游章节顺序、方法、步骤、完成判据、例子和解释性文字，不加入 MMW 的 tracker、worktree、领域文档、报告验证、资产或人工审批关卡。

第二阶段已经形成单文件精简稿。它只应用已经确认的四项调整：删除 100K token 数字、收窄并补全 Prototype 合同、删除上游 tracker 通用安装与 fallback、把 Grilling 双重调用收敛到 `/mmw-grilling`。

第三阶段已经在 `candidate/` 形成四文件候选。共享方法保留在 `candidate/SKILL.md`；Chart the map、沿 map 推进和 MMW 收尾分别按调用分支放在 `candidate/charting.md`、`candidate/walking.md` 和 `candidate/closing.md`。候选增加 tracker 命令、research 验证与保存、产物目录、持久资产和下游技能接线。

ticket 正文只写 `Question`：`产物目录` 从 map 正文读，`issue-<编号>` 子目录由 ticket 自己的编号得到，因此建 ticket 不再需要 `gh issue edit` 回填。

会话隔离按 map 分支加任务分支处理：map 任务拥有 map 分支，每张 decision ticket 使用一条从 map 分支派生的任务分支，解决期间写下的领域 leaf、ADR 和资产提交在这条任务分支上，再交回 map 任务验证并集成。两个会话并发解 ticket 时，分开的 worktree 让冲突在合并时暴露；共用工作目录会直接互相覆盖。ADR 在任务分支上先用 `draft-<ticket 编号>-<slug>.md`，集成后由 map 任务分配正式编号。

`wayfinder:research` ticket 是 AFK：ticket 本身就是用户对这次调查的批准，所以这条路径上的 research 直接保存，不再逐张停下来询问。

收尾同时检查 open decision ticket 和 Not yet specified；剩余 fog 再次使用广度优先 grilling。路线清楚后，spec destination 把 map 名称、`产物目录` 和任务 slug 交给 `/mmw-to-spec`；非 spec destination 报告结果并结束 Wayfinding。Wayfinder 不预建 spec issue，不拆分 spec，也不建立 To Spec 回退、重开 map 或 rebase 流程。当前发布技能仍不修改。

唯一上游是：

[上游 Wayfinder `SKILL.md`](../../../vendor/mattpocock-skills/skills/engineering/wayfinder/SKILL.md)

当前文件：

- [upstream-1.2.2.zh-CN.md](upstream-1.2.2.zh-CN.md)：上游 `SKILL.md` 的中文翻译。每段用 HTML 注释标出对应的上游行号。
- [translation-audit.md](translation-audit.md)：本轮翻译使用的固定术语表，以及逐段完整性和语义检查结果。
- [simplified.zh-CN.md](simplified.zh-CN.md)：以精确翻译为基线形成的单文件精简稿。它继续保留上游行号注释，不包含 research、Invocation、worktree、资产或收尾接线。
- [candidate/](candidate/)：在精简稿外层增加 MMW 接线的四文件候选。这个目录仍不会被 `mmw skills materialize` 物化。
