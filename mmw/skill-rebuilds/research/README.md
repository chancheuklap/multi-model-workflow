# Research 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW Research。当前发布技能仍位于 `mmw/skills/mmw-research/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段

第一阶段已经完成上游 `SKILL.md` 和 `agents/openai.yaml` 的逐段中文翻译。第二阶段已经建立精简稿；精简稿只移除翻译基线中的出处标注，不删改上游方法内容。第三阶段从精简稿建立按 agent 身份渐进加载的接线候选；候选材料仍不参与 Plugin 运行。

## 文件

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐段中文翻译基线 |
| `translation-audit.md` | 术语选择、逐段完整性与无新增语义检查 |
| `simplified.zh-CN.md` | 移除出处标注、尚未加入 MMW 接线的精简稿 |
| `candidate/SKILL.md` | 识别当前 agent 是主 agent 还是 `investigator`，只加载对应入口 |
| `candidate/MAIN.md` | 主 agent 使用的派发、验证、综合、保存和交回流程 |
| `candidate/INVESTIGATOR.md` | `investigator` 使用的方向路由和禁止再次派发规则 |
| `candidate/INTERNAL.md` | 内部 research 角度特有的源码出处要求，只供 `investigator` 读取 |
| `candidate/EXTERNAL.md` | 外部 research 角度特有的一手来源要求，只供 `investigator` 读取 |

接线候选由五份技能文件组成。主 agent 只读取 `SKILL.md` 和 `MAIN.md`。`investigator` 只读取 `SKILL.md`、`INVESTIGATOR.md` 和 task 指定的 `INTERNAL.md` 或 `EXTERNAL.md`。正式技能源保持不变，等待用户审查候选后再决定是否进入 Plugin 发布面。
