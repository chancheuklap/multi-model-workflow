# `to-spec` 1.2.2 翻译审查

## 固定术语

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| spec | `spec` | 上游产物词与 MMW canonical 术语 |
| issue tracker、triage、`ready-for-agent` | 保留原文 | tracker 对象、动作和标签字面量 |
| synthesis | 综合 | 表达整理已有内容，不重新访谈 |
| domain glossary | 领域术语表 | 领域驱动设计中的准确中文表达 |
| ADR | `ADR` | 行业缩写 |
| seam | `seam` | Codebase Design 的 leading word |
| module、interface | `module`、`interface` | Codebase Design 的 leading word |
| user story | `user story` | 软件产品设计中的常用原词 |
| schema、API、reducer、prototype、demo | 保留原文 | 技术对象和上游产物词 |
| prior art | 先例 | 指代码库中可参考的既有同类测试 |
| external behavior | 外部行为 | 有稳定中文译名 |

## 逐段完整性检查

| 上游位置 | 结论 |
| --- | --- |
| `SKILL.md:1-9` | 当前对话、发布 tracker、只综合不采访、代码库理解和 setup fallback 均已保留 |
| `SKILL.md:11-17` | 探索现状、领域术语、ADR、已有 seam 优先、最高 seam、最少 seam 和用户确认均已保留 |
| `SKILL.md:19` | 按模板写 spec、发布 tracker、添加 `ready-for-agent` 和免除再次 triage 均已保留 |
| `SKILL.md:21-41` | Problem、Solution、长编号 User Stories、固定格式、示例和极其详尽的覆盖要求均已保留 |
| `SKILL.md:43-57` | 七类 Implementation Decisions、禁止文件路径和代码片段，以及 prototype 代码片段例外均已保留 |
| `SKILL.md:59-65` | 好测试、外部行为、module 范围和测试先例均已保留 |
| `SKILL.md:67-75` | Out of Scope 与 Further Notes 均已保留 |
| `agents/openai.yaml:1-5` | 展示信息和禁止隐式调用的 policy 均已保留 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。两个上游文件的全部标题、正文、列表、模板和例子均有对应翻译 |
| 增写 | 无。没有加入 MMW 多入口、research、prototype 资产索引、人工审批关卡或 spec 审查 |
| 曲解 | 无。没有把综合改成重新访谈，也没有删除 seam 用户确认或 prototype 片段例外 |
| 术语漂移 | 无。`spec`、`seam`、`module`、`interface`、`user story` 和模板标题始终使用同一写法 |
