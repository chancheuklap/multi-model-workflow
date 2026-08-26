# `to-spec` 1.2.2 翻译审查

## 本技能术语应用

共享术语只由 [上游技能翻译共享术语](../translation-terms.md) 定义。下表记录本技能的术语应用和独有术语，不建立第二份定义。

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

## 逐行完整性检查

空行只承担 Markdown 分隔，不包含待翻译文字。

| 上游行 | 本行翻译检查 |
| --- | --- |
| `SKILL.md:1` | YAML 起始分隔符已保留 |
| `SKILL.md:2` | 技能名已保留 |
| `SKILL.md:3` | 当前对话、spec、发布 tracker、禁止采访和只综合已讨论内容均已保留 |
| `SKILL.md:4` | 禁止模型隐式调用已保留 |
| `SKILL.md:5` | YAML 结束分隔符已保留 |
| `SKILL.md:7` | 当前对话上下文、代码库理解、生成 spec 和只综合已有知识均已保留 |
| `SKILL.md:9` | tracker 与 triage 标签词汇及 setup fallback 已保留 |
| `SKILL.md:11` | 流程标题已翻译 |
| `SKILL.md:13` | 按需探索现状、领域术语贯穿 spec 和遵守相关 ADR 均已保留 |
| `SKILL.md:15` | 勾勒测试 seam、已有优先、最高层、少 seam 和理想一个均已保留 |
| `SKILL.md:17` | 向用户确认 seam 符合预期已保留 |
| `SKILL.md:19` | 按模板写 spec、发布 tracker、添加 ready-for-agent 且无需再次 triage 已保留 |
| `SKILL.md:21` | spec-template 起始标签已保留 |
| `SKILL.md:23` | Problem Statement 标题已保留 |
| `SKILL.md:25` | 从用户角度描述问题已翻译 |
| `SKILL.md:27` | Solution 标题已保留 |
| `SKILL.md:29` | 从用户角度描述解决方案已翻译 |
| `SKILL.md:31` | User Stories 标题已保留 |
| `SKILL.md:33` | 很长的编号清单和固定格式引导已保留 |
| `SKILL.md:35` | 角色、功能和收益的 user story 格式已翻译 |
| `SKILL.md:37` | user-story-example 起始标签已保留 |
| `SKILL.md:38` | 手机银行客户、账户余额和支出决定示例已翻译 |
| `SKILL.md:39` | user-story-example 结束标签已保留 |
| `SKILL.md:41` | user story 清单极其详尽并覆盖全部方面已保留 |
| `SKILL.md:43` | Implementation Decisions 标题已保留 |
| `SKILL.md:45` | 已形成实施决定的清单及包含项引导已翻译 |
| `SKILL.md:47` | 建立或修改的 module 已翻译 |
| `SKILL.md:48` | 修改的 module interface 已翻译 |
| `SKILL.md:49` | 开发者技术澄清已翻译 |
| `SKILL.md:50` | 架构决定已翻译 |
| `SKILL.md:51` | schema 变更已保留 |
| `SKILL.md:52` | API 合同已保留 |
| `SKILL.md:53` | 具体交互已翻译 |
| `SKILL.md:55` | 禁止文件路径和代码片段及会迅速过期的理由已保留 |
| `SKILL.md:57` | prototype 片段例外、四类例子、注明来源和只保留决定密集部分均已保留 |
| `SKILL.md:59` | Testing Decisions 标题已保留 |
| `SKILL.md:61` | 已形成测试决定清单及包含项引导已翻译 |
| `SKILL.md:63` | 好测试只测外部行为而非实现细节已翻译 |
| `SKILL.md:64` | 将测试哪些 module 已翻译 |
| `SKILL.md:65` | 测试先例及代码库同类测试已翻译 |
| `SKILL.md:67` | Out of Scope 标题已保留 |
| `SKILL.md:69` | 说明 spec 范围外内容已翻译 |
| `SKILL.md:71` | Further Notes 标题已保留 |
| `SKILL.md:73` | 功能其他说明已翻译 |
| `SKILL.md:75` | spec-template 结束标签已保留 |
| `agents/openai.yaml:1` | interface 配置键已保留 |
| `agents/openai.yaml:2` | 显示名已保留 |
| `agents/openai.yaml:3` | 对话整理成 spec 的短描述已翻译 |
| `agents/openai.yaml:4` | policy 配置键已保留 |
| `agents/openai.yaml:5` | 禁止隐式调用已保留 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。两个上游文件的全部标题、正文、列表、模板和例子均有对应翻译 |
| 增写 | 无。没有加入 MMW 多入口、research、prototype 资产索引、人工审批关卡或 spec 审查 |
| 曲解 | 无。没有把综合改成重新访谈，也没有删除 seam 用户确认或 prototype 片段例外 |
| 术语漂移 | 无。`spec`、`seam`、`module`、`interface`、`user story` 和模板标题始终使用同一写法 |
