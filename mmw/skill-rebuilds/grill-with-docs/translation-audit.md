# `grill-with-docs` 1.2.2 翻译审查

## 固定术语

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| `grill-with-docs`、`/grilling`、`/domain-modeling` | 保留原文 | 技能名和调用字面量 |
| session | `session` | agent 工作单位，MMW 已采用该写法 |
| plan | 计划 | 本句指一般计划，不是 MMW 的 `plan` 产物 |
| design | 设计 | 有稳定中文译名 |
| docs | 文档 | 有稳定中文译名 |
| ADR | `ADR` | 行业缩写 |
| glossary | 术语表 | 有稳定中文译名 |
| relentless | 毫不松懈 | 保留持续追问、不能过早结束的强度 |

## 逐段完整性检查

| 上游位置 | 结论 |
| --- | --- |
| `SKILL.md:1-5` | 技能名、description 和 `disable-model-invocation: true` 均已保留；description 中访谈强度、目标和同时创建文档三层含义均已翻译 |
| `SKILL.md:7` | `/grilling` session 与在其中使用 `/domain-modeling` 的关系均已保留 |
| `agents/openai.yaml:1-5` | `display_name`、`short_description` 和禁止隐式调用的 policy 均已保留；字段名与布尔字面量未翻译 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。两个上游文件的全部有效内容均有对应翻译 |
| 增写 | 无。没有加入 MMW 的领域文档、人工审批关卡或路由 |
| 曲解 | 无。`using` 译为“并使用”，没有改成先后两个独立流程 |
| 术语漂移 | 无。技能名、调用字面量和 `session` 始终使用同一写法 |
