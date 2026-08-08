# Grilling 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW Grilling。当前发布技能仍位于 `mmw/skills/mmw-grilling/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段

第一阶段已经完成上游 `SKILL.md` 和 `agents/openai.yaml` 的逐段中文翻译。第二阶段的精简稿与翻译基线逐字一致，没有删改上游方法。第三阶段在 `../candidate/skills/mmw-grilling/` 中加入已经确认的 Domain Modeling、事实调查、prototype、questionnaire、人工审批关卡和下游移交接线。当前发布技能仍未修改。

## 文件

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐段中文翻译基线 |
| `translation-audit.md` | 术语选择、逐段完整性与无新增语义检查 |
| `simplified.zh-CN.md` | 与翻译基线逐字一致的精简层 |
| `../candidate/skills/mmw-grilling/` | 在精简层基础上增加最小 MMW 接线的候选技能 |

候选内容经过用户批准后，才进入 `mmw/skills/mmw-grilling/`。
