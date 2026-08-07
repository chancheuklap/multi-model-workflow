# `grilling` 1.2.2 翻译审查

## 固定术语

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| grilling、grill | `grilling`、`grill` | 技能名与触发语字面词 |
| relentlessly | 毫不松懈 | 保留不能过早停止访谈的强度 |
| design tree | 设计树 | 有准确、稳定的中文表达 |
| frontier | `frontier` | 上游 leading word，也是 MMW canonical 术语 |
| round | 轮 | 有稳定中文译名 |
| prerequisite | 前置决定、前置条件 | 根据对象分别指已经确定的决定和正在探索的事实；不混同为 blocking edge |
| sub-agent | `subagent` | MMW canonical 术语，含义未改变 |
| shared understanding | 共同理解 | MMW canonical 术语 |
| fact、decision | 事实、决定 | 保留双方责任边界 |

## 逐段完整性检查

| 上游位置 | 结论 |
| --- | --- |
| `SKILL.md:1-4` | 三类访谈对象、压力测试和 `grill` 触发语均已保留 |
| `SKILL.md:6` | 毫不松懈的访谈、共同理解和决定之间的设计树依赖均已保留 |
| `SKILL.md:8` | frontier 定义、整轮提出、编号、推荐答案和等待用户回答均已保留 |
| `SKILL.md:10-16` | 问题模板中的编号、标题、正文、多段落、多选项和推荐答案均已保留 |
| `SKILL.md:18` | 每轮重塑设计树、重新计算 frontier，以及仍有本轮依赖的问题推迟到后续轮次均已保留 |
| `SKILL.md:20` | 事实由 agent 查、决定由用户作、调查只阻塞依赖分支和其余 frontier 立即继续均已保留 |
| `SKILL.md:22` | frontier 为空、每个分支已访问、无静默假设和用户确认共同理解四项完成条件均已保留 |
| `agents/openai.yaml:1-3` | 展示名称和短描述均已保留 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。两个上游文件的全部有效内容均有对应翻译 |
| 增写 | 无。没有加入领域文档、MMW Research 触发边界或人工审批关卡 |
| 曲解 | 无。没有把整轮 frontier 缩成一次一个问题，也没有让事实调查阻塞全部提问 |
| 术语漂移 | 无。设计树、`frontier`、轮、事实、决定和共同理解始终使用同一写法 |
