# Wizard 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW Wizard。当前发布技能仍位于 `mmw/skills/wizard/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段

第一阶段已经完成上游 `SKILL.md`、`template.sh` 和 `agents/openai.yaml` 的逐行中文翻译。翻译保留人工流程限定、精确路径、固定 wizard library、阶段 helper、静态验证和临时产物边界，不加入 MMW scratch 或任务接线。

## 文件

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐行中文翻译基线 |
| `translation-audit.md` | 术语选择、逐行完整性与无新增语义检查 |

后续只有在用户确认精简方案后，才增加 `simplified.zh-CN.md`；只有在用户确认接线方案后，才增加 `candidate/`。

## 2026-08 复审改动

vendor 已同步上游 1.2.3。候选跟进删除时间预估：`template.sh` 换为 1.2.3 版（无 `TOTAL_MINUTES`，`stage` 只接名称，进度按阶段数；保留候选原有的 shellcheck SC2034 抑制注释），`SKILL.md` 相应改为「把 `TOTAL_STAGES` 设成实际阶段数」。
