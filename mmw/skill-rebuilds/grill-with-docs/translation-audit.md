# `grill-with-docs` 1.2.2 翻译审查

## 本技能术语应用

共享术语只由 [上游技能翻译共享术语](../translation-terms.md) 定义。下表记录本技能的术语应用和独有术语，不建立第二份定义。

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| `grill-with-docs`、`/grilling`、`/domain-modeling` | 保留原文 | 技能名和调用字面量 |
| session | `session` | agent 工作单位，MMW 已采用该写法 |
| plan | 计划 | 本句指一般计划，不是 MMW 的 `plan` 产物 |
| design | 设计 | 有稳定中文译名 |
| docs | 文档 | 有稳定中文译名 |
| ADR | `ADR` | 行业缩写 |
| glossary | 术语表 | 有稳定中文译名 |
| relentless | `relentless` | 上游 leading word；与 grilling 和 writing-for-agents 保持同一 token |

## 逐行完整性检查

空行只承担 Markdown 分隔，不包含待翻译文字。

| 上游行 | 本行翻译检查 |
| --- | --- |
| `SKILL.md:1` | YAML 起始分隔符已保留 |
| `SKILL.md:2` | 技能名已保留 |
| `SKILL.md:3` | relentless 访谈、使计划或设计更加明确，以及同步创建 ADR 与术语表均已保留 |
| `SKILL.md:4` | 禁止模型隐式调用已保留 |
| `SKILL.md:5` | YAML 结束分隔符已保留 |
| `SKILL.md:7` | 运行 grilling session 并使用 domain-modeling 的关系已保留 |
| `agents/openai.yaml:1` | interface 配置键已保留 |
| `agents/openai.yaml:2` | 显示名已保留 |
| `agents/openai.yaml:3` | 对设计进行 grilling 并编写文档的短描述已翻译 |
| `agents/openai.yaml:4` | policy 配置键已保留 |
| `agents/openai.yaml:5` | 禁止隐式调用已保留 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。两个上游文件的全部有效内容均有对应翻译 |
| 增写 | 无。没有加入 MMW 的领域文档、人工审批关卡或路由 |
| 曲解 | 无。`using` 译为“并使用”，没有改成先后两个独立流程 |
| 术语漂移 | 无。技能名、调用字面量和 `session` 始终使用同一写法 |
