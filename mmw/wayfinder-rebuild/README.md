# Wayfinder 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW Wayfinder。当前发布技能仍位于 `mmw/skills/mmw-wayfinder/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段

第一阶段已经完成上游原文的逐段中文翻译。翻译保持上游章节顺序、方法、步骤、完成判据、例子和解释性文字，不加入 MMW 的 tracker、worktree、领域文档、报告验证、资产或人工审批关卡。

第二阶段已经形成单文件精简稿。它只应用已经确认的四项调整：删除 100K token 数字、收窄并补全 Prototype 合同、删除上游 tracker 通用安装与 fallback、把 Grilling 双重调用收敛到 `/mmw-grilling`。文档拆分、research 接线和 Invocation 接线尚未开始。当前发布技能仍不修改。

唯一上游是：

`vendor/mattpocock-skills/skills/engineering/wayfinder/SKILL.md`

当前文件：

- `upstream-1.2.2.zh-CN.md`：上游 `SKILL.md` 的中文翻译。每段用 HTML 注释标出对应的上游行号。
- `translation-audit.md`：本轮翻译使用的固定术语表，以及逐段完整性和语义检查结果。
- `simplified.zh-CN.md`：以精确翻译为基线形成的单文件精简稿。它继续保留上游行号注释，尚未加入 research、Invocation、worktree、资产或收尾接线。
