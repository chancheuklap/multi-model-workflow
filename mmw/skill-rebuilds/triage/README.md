# Triage 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW Triage。当前发布技能仍位于 `mmw/skills/mmw-triage/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段

第一阶段已经完成上游 `SKILL.md`、`AGENT-BRIEF.md`、`OUT-OF-SCOPE.md` 和 `agents/openai.yaml` 的逐行翻译。翻译保留类别角色与状态角色、PR 差异、验证、grilling、agent brief、needs-info 和拒绝请求知识库，不加入 MMW 接线。

## 文件

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐行中文翻译基线 |
| `translation-audit.md` | 术语选择、逐行完整性与无新增语义检查 |

后续只有在用户确认精简方案后，才增加 `simplified.zh-CN.md`；只有在用户确认接线方案后，才增加 `candidate/`。
