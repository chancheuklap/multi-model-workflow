# Codebase Design 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW Codebase Design。当前发布技能仍位于 `mmw/skills/mmw-codebase-design/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段

第一阶段已经完成上游 `SKILL.md`、`DEEPENING.md`、`DESIGN-IT-TWICE.md` 和 `agents/openai.yaml` 的逐行中文翻译。翻译保留 deep module 词汇、依赖分类、seam 纪律、测试策略和并行设计方法，不加入 MMW 角色或流程接线。

## 文件

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐行中文翻译基线 |
| `translation-audit.md` | 术语选择、逐行完整性与无新增语义检查 |

后续只有在用户确认精简方案后，才增加 `simplified.zh-CN.md`；只有在用户确认接线方案后，才增加 `candidate/`。

## 2026-08 复审改动

用户裁定本技能完全参考上游，MMW 只做路由接线。删除了候选自行引申的判据（`SKILL.md` 与 `DEEPENING.md` 中「已经存在的单 adapter seam 是举证不足，不是错，不要拿这条去删它」），回到上游原文语义：判据只管要不要新开 seam。`DESIGN-IT-TWICE.md` 的 designer 派发段收回 `[[mmw-launch:designer:none]]` 占位块。
