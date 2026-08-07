# Wayfinder 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW Wayfinder。当前发布技能仍位于 `mmw/skills/mmw-wayfinder/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段

第一阶段已经完成上游原文的逐段中文翻译。翻译保持上游章节顺序、方法、步骤、完成判据、例子和解释性文字，不加入 MMW 的 tracker、worktree、领域文档、报告验证、资产或人工审批关卡。

第二阶段已经形成单文件精简稿。它只应用已经确认的四项调整：删除 100K token 数字、收窄并补全 Prototype 合同、删除上游 tracker 通用安装与 fallback、把 Grilling 双重调用收敛到 `/mmw-grilling`。

第三阶段已经在 `candidate/` 形成四文件候选。共享方法保留在 `candidate/SKILL.md`；Chart the map、走完整张 map 和 MMW 收尾分别按调用分支放在 `candidate/charting.md`、`candidate/walking.md` 和 `candidate/closing.md`。候选只增加已经确认的 tracker、research、worktree、产物路径和下游移交接线。收尾以不存在 open decision ticket 为判据，不把 frontier 为空误作 map 已完成。当前发布技能仍不修改。

唯一上游是：

[上游 Wayfinder `SKILL.md`](../../../vendor/mattpocock-skills/skills/engineering/wayfinder/SKILL.md)

当前文件：

- [upstream-1.2.2.zh-CN.md](upstream-1.2.2.zh-CN.md)：上游 `SKILL.md` 的中文翻译。每段用 HTML 注释标出对应的上游行号。
- [translation-audit.md](translation-audit.md)：本轮翻译使用的固定术语表，以及逐段完整性和语义检查结果。
- [simplified.zh-CN.md](simplified.zh-CN.md)：以精确翻译为基线形成的单文件精简稿。它继续保留上游行号注释，不包含 research、Invocation、worktree、资产或收尾接线。
- [candidate/](candidate/)：在精简稿外层增加 MMW 接线的四文件候选。这个目录仍不会被 `mmw skills materialize` 物化。
