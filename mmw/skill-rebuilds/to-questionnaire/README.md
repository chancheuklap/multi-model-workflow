# To Questionnaire 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW To Questionnaire。当前发布技能仍位于 `mmw/skills/to-questionnaire/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段

第一阶段已经完成上游 `SKILL.md` 和 `agents/openai.yaml` 的逐段中文翻译。翻译保持只追问发送安排、收件人、信息缺口、三步完成判据和整份 questionnaire 模板，不加入 MMW 的 scratch、Grilling 回流或清理流程。

接线候选位于 `../candidate/skills/to-questionnaire/`。候选只改调用方式：上游是 user-invoked；MMW 的 `/mmw-grilling` 会调用它，所以候选必须保持 model-invoked。问卷方法和完成判据不变。

## 文件

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐段中文翻译基线 |
| `translation-audit.md` | 术语选择、逐段完整性与无新增语义检查 |
| `../candidate/skills/to-questionnaire/` | 保留上游方法，只增加 Grilling 调用合同的候选技能 |

当前发布技能保持不变。
