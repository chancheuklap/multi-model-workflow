# 上游技能翻译共享术语

本文件是 `mmw/skill-rebuilds/` 当前翻译批次的跨技能术语依据。它只服务候选重建材料，不进入 MMW Plugin 发布面。各技能的 `translation-audit.md` 只记录本技能如何应用这些术语，以及本技能独有的术语，不再自行决定共享写法。

## 共享写法

| 上游原词 | 采用写法 | 类型 | 依据 |
| --- | --- | --- | --- |
| agent、sub-agent | `agent`、`subagent` | 角色词 | MMW Agent Context；`sub-agent` 统一为仓库 canonical 拼写 `subagent` |
| session、context window | `session`、上下文窗口 | 工作单位与容量 | 两者是不同概念，不互相替换 |
| skill | 技能 | 通用术语 | 稳定中文译名；技能名字面量继续保留英文 |
| spec、prototype、research | `spec`、`prototype`、`research` | MMW 产物与方法词 | MMW 交付工作流 Context |
| issue、ticket、issue tracker | `issue`、`ticket`、`issue tracker` | tracker 对象 | 三种对象不混称 |
| task、brief、agent brief | `task`、`brief`、`agent brief` | 派发说明与 tracker 合同 | MMW `task` 是四栏表；上游普通 brief 不改成 `task`；`agent brief` 是固定产物名 |
| module、interface、implementation | 保留英文原词 | Codebase Design 核心词汇 | 上游要求准确使用；普通动词 implementation 仍译为“实现” |
| depth、deep、shallow、seam、adapter、leverage、locality | 保留英文原词 | Codebase Design 核心词汇 | 上游要求准确使用 |
| test surface | `test surface` | Codebase Design 方法词 | 没有稳定且等价的中文专名 |
| tight、red、green、red-capable | 保留英文原词 | leading word与测试状态 | Writing for Agents 明确使用的 leading word；TDD 复用相同状态词 |
| relentless、relentlessly | `relentless` | leading word | Writing for Agents 用它强化执行强度；跨 Grilling 技能保持同一 token |
| sharpen | 使对象更加明确 | 普通动词 | 使用直接中文；不写“磨锋利”或“磨清楚” |
| frontier | `frontier` | leading word | 各技能可以定义不同 frontier 对象，但拼写保持一致 |
| claim | tracker 动作写 `claim`；事实陈述写“断言” | 多义词 | 根据对象区分，不把 tracker 动作与 research 断言混同 |
| finding | 审查对象写 `finding`；research 写“调查结论”；诊断写“发现” | 多义词 | 三种产物不同，不强行合并 |
| primary source、secondary source | 一手来源、二手来源 | 资料来源 | 稳定中文译名 |
| completion criterion | 完成判据 | 方法词 | MMW 已采用的 canonical 术语 |
| shared understanding | 共同理解 | 方法词 | MMW 交付工作流 Context |
| judgement call | 需要判断的事项 | 判断性质 | 使用完整中文，不压缩成“判断项”或“判断题” |
| HITL、AFK | `HITL`、`AFK` | 行业缩写 | 保留英文缩写 |
| leading word、context pointer | `leading word`、`context pointer` | Writing for Agents 方法词 | 没有稳定且等价的中文专名 |

## 字面量规则

技能名、角色名、命令、字段、标签、状态字面量、代码标识符，以及被其他文档按字面名称引用的标题，保留上游原文。普通英文词只有在没有稳定中文译名，或者承担 leading word 作用时才保留。

固定模板内的 `_Avoid_`、`Wayfinding operations`、`Triage labels`、`Domain docs`、`Triage Labels`、`Prior requests`、`PRs as a request surface` 和 `MRs as a request surface` 按字面保留。引用方与目标标题必须完全一致。

## 检查判据

同一英文词可以因语义不同采用不同写法，但审计必须写清它指向的对象。不同英文词不能因为中文相近而合并为一个方法概念。每次修改任一翻译基线后，都要搜索本文件中的共享词，并打开命中位置判断语义，不能只统计词频。
