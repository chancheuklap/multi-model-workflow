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

## 逐行完整性检查

空行只承担 Markdown 分隔，不包含待翻译文字。

| 上游行 | 本行翻译检查 |
| --- | --- |
| `SKILL.md:1` | YAML 起始分隔符已保留 |
| `SKILL.md:2` | 技能名已保留 |
| `SKILL.md:3` | 三类讨论对象、毫不松懈、压力测试和 grill 触发语均已保留 |
| `SKILL.md:4` | YAML 结束分隔符已保留 |
| `SKILL.md:6` | 持续访谈、共同理解和决定依赖形成设计树均已保留 |
| `SKILL.md:8` | 按轮、frontier 定义、整轮提问、编号、推荐答案和等待均已保留 |
| `SKILL.md:10` | 问题格式引导已翻译 |
| `SKILL.md:12` | 代码块起始已保留 |
| `SKILL.md:13` | 问题编号、标题、正文、多段落和多选项占位均已保留 |
| `SKILL.md:15` | 推荐答案占位已翻译 |
| `SKILL.md:16` | 代码块结束已保留 |
| `SKILL.md:18` | 回答重塑树、推进 frontier、重新计算及依赖未决问题推迟均已保留 |
| `SKILL.md:20` | 事实与决定责任、派 subagent、局部等待及其余 frontier 立即提问均已保留 |
| `SKILL.md:22` | frontier 为空、遍历全部分支、无静默假设和用户确认后行动均已保留 |
| `agents/openai.yaml:1` | interface 配置键已保留 |
| `agents/openai.yaml:2` | 显示名已保留 |
| `agents/openai.yaml:3` | 逐轮问题压力测试的短描述已翻译 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。两个上游文件的全部有效内容均有对应翻译 |
| 增写 | 无。没有加入领域文档、MMW Research 触发边界或人工审批关卡 |
| 曲解 | 无。没有把整轮 frontier 缩成一次一个问题，也没有让事实调查阻塞全部提问 |
| 术语漂移 | 无。设计树、`frontier`、轮、事实、决定和共同理解始终使用同一写法 |
