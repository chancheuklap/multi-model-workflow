# `writing-for-agents` 1.2.2 翻译审查

## 本技能术语应用

共享术语只由 [上游技能翻译共享术语](../translation-terms.md) 定义。下表记录本技能的术语应用和独有术语，不建立第二份定义。

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| agent | `agent` | 上游使用者名称 |
| context pointer | `context pointer` | 上游核心 leading word，没有稳定且等价的中文专名 |
| context load、cognitive load | 上下文负荷、认知负荷 | 有准确、稳定的中文译名 |
| information hierarchy | 信息层级 | 有准确中文译名 |
| step、reference | 步骤、参考内容 | 两类文档内容的固定译名 |
| disclosed reference | `disclosed reference` | 信息层级中的上游方法词，没有稳定且等价的中文专名 |
| progressive disclosure | 渐进式披露 | 有稳定中文译名 |
| co-location | 共置 | 表达相关定义、规则和注意事项放在一起 |
| sprawl | `sprawl` | 上游 leading word，没有稳定中文专名 |
| completion criterion | 完成判据 | MMW 已采用的 canonical 术语 |
| premature completion | 过早完成 | 有准确中文译名 |
| post-completion steps | `post-completion steps` | 保留上游概念名，正文同时解释其含义 |
| demand、legwork | `demand`、`legwork` | 上游方法词；保留原词并在正文定义 |
| leading word | `leading word` | 上游核心概念，保留原词 |
| negation | 否定表达 | 准确表达通过禁止语引导的写法 |
| single source of truth | 唯一事实来源 | MMW canonical 术语 |
| cache、sediment、no-op | `cache`、`sediment`、`no-op` | 上游 leading word |
| model-invoked、user-invoked | `model-invoked`、`user-invoked` | invocation 机制名称 |
| router skill | `router skill` | 上游 invocation 机制名称 |
| frontmatter、description、invocation | 保留原文 | 技能机制字面词 |

## 逐行完整性检查

空行只承担 Markdown 分隔，不包含待翻译文字。

| 上游行 | 本行翻译检查 |
| --- | --- |
| `SKILL.md:1` | YAML 起始分隔符已保留 |
| `SKILL.md:2` | 技能名已保留 |
| `SKILL.md:3` | agent 文档及技能、AGENTS、CLAUDE 三类触发范围已保留 |
| `SKILL.md:4` | YAML 结束分隔符已保留 |
| `SKILL.md:6` | 三类 agent 文档、封装差异、相同写法和过程可预测性均已保留 |
| `SKILL.md:8` | 技能文档要读取 mechanics 文件及三类内容已保留 |
| `SKILL.md:10` | Context pointer 标题已保留 |
| `SKILL.md:12` | 定义、两个例子、措辞决定抵达和 variance bug 修法均已保留 |
| `SKILL.md:14` | pointer 的两项职责、branch 定义和严格删减原因均已保留 |
| `SKILL.md:16` | leading word 前置规则已保留 |
| `SKILL.md:17` | 每分支一个触发条件及合并同义词已保留 |
| `SKILL.md:18` | 删除正文已承载身份说明已翻译 |
| `SKILL.md:20` | 两种负荷标题已翻译 |
| `SKILL.md:22` | 每份文档和 pointer 消耗一种预算已保留 |
| `SKILL.md:24` | 上下文负荷定义、例子和 token 与注意力成本均已保留 |
| `SKILL.md:25` | 认知负荷、人是索引、人类自主判断及投入边界均已保留 |
| `SKILL.md:27` | pointer 材料与无 pointer 材料的负荷交换已保留 |
| `SKILL.md:29` | 信息层级标题已翻译 |
| `SKILL.md:31` | 步骤与参考两类内容、三种组合和信息层级定义均已保留 |
| `SKILL.md:33` | 文件内步骤为第一层且按顺序执行已翻译 |
| `SKILL.md:34` | 文件内参考按需查阅、合理扁平同级内容不是坏味道已保留 |
| `SKILL.md:35` | disclosed reference、单独文件、pointer 条件加载和外部范围均已保留 |
| `SKILL.md:37` | 向下太少与太多的张力已翻译 |
| `SKILL.md:39` | 渐进式披露、保护层级、分支判据和步骤被掩埋的 variance 风险均已保留 |
| `SKILL.md:41` | 共置定义、同标题归组、文档判据及与重复和散落区别均已保留 |
| `SKILL.md:43` | sprawl 定义、注意力问题及按层级、分支或顺序拆分的修法均已保留 |
| `SKILL.md:45` | 步骤和完成判据标题已翻译 |
| `SKILL.md:47` | 每步以完成判据结束及两项属性引导已保留 |
| `SKILL.md:49` | 清晰度、过早完成、后续步骤拉力、修正顺序和真实上下文边界均已保留 |
| `SKILL.md:50` | demand、两个例子、legwork、非步骤约束及参考穷尽性均已保留 |
| `SKILL.md:52` | 最强判据同时可检查和穷尽已翻译 |
| `SKILL.md:54` | 何时拆分标题已翻译 |
| `SKILL.md:56` | 拆分消耗负荷且只在值得时执行已翻译 |
| `SKILL.md:58` | 按顺序拆分、隐藏后续步骤、促进 legwork 和合并反向风险均已保留 |
| `SKILL.md:59` | 按 invocation 拆分及 mechanics 引用已保留 |
| `SKILL.md:61` | Leading words 标题已保留 |
| `SKILL.md:63` | leading word 定义、三个例子、分布式定义、预训练先验和自造词成本均已保留 |
| `SKILL.md:65` | 正文固定执行、参考聚焦对象和 pointer 固定 invocation 均已保留 |
| `SKILL.md:67` | 主动用 leading word 重构及两类候选段落已保留 |
| `SKILL.md:69` | tight 替代三项描述的示例已保留 |
| `SKILL.md:70` | red 替代含糊关卡及二元可观察状态示例已保留 |
| `SKILL.md:72` | 减少 token、强化思考挂钩和主动找重复表述均已保留 |
| `SKILL.md:74` | 否定表达失败机制、大象例子、正面目标和硬护栏例外均已保留 |
| `SKILL.md:76` | 删减标题已翻译 |
| `SKILL.md:78` | 唯一事实来源、重复成本、显著性和与 leading word 的区别均已保留 |
| `SKILL.md:79` | 环境唯一事实来源、cache 判据、应缓存内容和单查询留给环境均已保留 |
| `SKILL.md:80` | 逐行相关性、两类失效、短文优势和 sediment 形成机制均已保留 |
| `SKILL.md:81` | no-op 判据、模型相对性、运行验证、整句删除和强 leading word 修法均已保留 |
| `SKILL-MECHANICS.md:1` | 技能机制标题已翻译 |
| `SKILL-MECHANICS.md:3` | 技能专有分支、三项机制和其余内容归 SKILL 通用参考均已保留 |
| `SKILL-MECHANICS.md:5` | Invocation 标题已保留 |
| `SKILL-MECHANICS.md:7` | 两种调用选择及两种负荷取舍已翻译 |
| `SKILL-MECHANICS.md:9` | model-invoked 的可达性、pointer 成本、共享参考归属和配置机制均已保留 |
| `SKILL-MECHANICS.md:10` | user-invoked 的仅人调用、零上下文负荷、认知负荷和配置机制均已保留 |
| `SKILL-MECHANICS.md:12` | 仅 agent 或其他技能必须抵达时选择 model invocation 已保留 |
| `SKILL-MECHANICS.md:14` | 两个 user-invoked 技能共享参考应移到技能外普通文件已保留 |
| `SKILL-MECHANICS.md:16` | 按 invocation 拆分标题已翻译 |
| `SKILL-MECHANICS.md:18` | 独立 leading word、真实 prompt 触发、其他技能抵达和成本判据均已保留 |
| `SKILL-MECHANICS.md:20` | Router skills 标题已保留 |
| `SKILL-MECHANICS.md:22` | router skill 解决认知负荷、只提示不能触发及原因均已保留 |
| `agents/openai.yaml:1` | interface 配置键已保留 |
| `agents/openai.yaml:2` | 显示名已保留 |
| `agents/openai.yaml:3` | 编写供 agent 使用文档的短描述已翻译 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。三个上游文件的标题、正文、列表、例子和完成判据均有对应翻译 |
| 增写 | 无。没有加入 MMW 的输出规范、宿主物化或项目技能目录规则 |
| 曲解 | 无。渐进式披露没有被缩写成 token 优化；拆分仍要求真实分支、顺序或独立 invocation |
| 术语漂移 | 无。context pointer、两种负荷、信息层级、完成判据、leading word 和 invocation 机制均使用固定写法 |
