# Code Review 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW Code Review。当前发布技能仍位于 `mmw/skills/mmw-review/` 和 `mmw/skills/mmw-reviewer/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段

第一阶段已经完成上游 `SKILL.md` 和 `agents/openai.yaml` 的逐行中文翻译。翻译保留 Standards 与 Spec 两条审查轴、固定点判据、代码异味基线、并行 subagent 和分轴汇总，不加入 MMW 的六道审查、角色派发、验证或人工审批关卡接线。

## 文件

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐行中文翻译基线 |
| `translation-audit.md` | 术语选择、逐行完整性与无新增语义检查 |

后续只有在用户确认精简方案后，才增加 `simplified.zh-CN.md`；只有在用户确认接线方案后，才增加 `candidate/`。
