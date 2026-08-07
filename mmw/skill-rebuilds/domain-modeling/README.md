# Domain Modeling 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW Domain Modeling。当前发布技能仍位于 `mmw/skills/mmw-domain-modeling/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段

第一阶段已经完成上游 `SKILL.md`、`ADR-FORMAT.md`、`CONTEXT-FORMAT.md` 和 `agents/openai.yaml` 的逐行中文翻译。翻译保留领域词汇维护、代码交叉检查、即时更新、ADR 三项门槛和单 context 与多 context 文件形态，不加入 MMW 领域路由接线。

## 文件

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐行中文翻译基线 |
| `translation-audit.md` | 术语选择、逐行完整性与无新增语义检查 |

后续只有在用户确认精简方案后，才增加 `simplified.zh-CN.md`；只有在用户确认接线方案后，才增加 `candidate/`。
