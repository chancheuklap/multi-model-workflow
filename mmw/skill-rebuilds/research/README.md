# Research 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW Research。当前发布技能仍位于 `mmw/skills/mmw-research/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段

第一阶段已经完成上游 `SKILL.md` 和 `agents/openai.yaml` 的逐段中文翻译。第二阶段已经建立精简稿；精简稿只移除翻译基线中的出处标注，不删改上游方法内容。第三阶段从精简稿重新建立最小接线候选；候选材料仍不参与 Plugin 运行。

## 文件

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐段中文翻译基线 |
| `translation-audit.md` | 术语选择、逐段完整性与无新增语义检查 |
| `simplified.zh-CN.md` | 移除出处标注、尚未加入 MMW 接线的精简稿 |
| `candidate/SKILL.md` | 保留上游后台委派、一手来源和单份 Markdown 报告，再加入 MMW 的派发、验证、保存和交回合同 |
| `candidate/INTERNAL.md` | 内部 research 角度特有的源码出处要求 |
| `candidate/EXTERNAL.md` | 外部 research 角度特有的一手来源要求 |

接线候选只加入当前合同要求的 `investigator` 四栏 task、主 agent 验证与综合、research 保存人工审批关卡、路径和交回合同。正式技能源保持不变，等待用户审查候选后再决定是否进入 Plugin 发布面。
