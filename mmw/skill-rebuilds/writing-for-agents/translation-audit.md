# `writing-for-agents` 1.2.2 翻译审查

## 固定术语

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| agent | `agent` | 上游使用者名称 |
| context pointer | `context pointer` | 上游核心 leading word，没有稳定且等价的中文专名 |
| context load、cognitive load | 上下文负荷、认知负荷 | 有准确、稳定的中文译名 |
| information hierarchy | 信息层级 | 有准确中文译名 |
| step、reference | 步骤、参考内容 | 两类文档内容的固定译名 |
| progressive disclosure | 渐进式披露 | 有稳定中文译名 |
| co-location | 共置 | 表达相关定义、规则和注意事项放在一起 |
| sprawl | `sprawl` | 上游 leading word，没有稳定中文专名 |
| completion criterion | 完成判据 | MMW 已采用的 canonical 术语 |
| premature completion | 过早完成 | 有准确中文译名 |
| post-completion steps | `post-completion steps` | 保留上游概念名，正文同时解释其含义 |
| demand、legwork | 要求力度、`legwork` | `demand` 使用中文解释；`legwork` 保留 leading word并在正文定义 |
| leading word | `leading word` | 上游核心概念，保留原词 |
| negation | 否定表达 | 准确表达通过禁止语引导的写法 |
| single source of truth | 唯一事实来源 | MMW canonical 术语 |
| cache、sediment、no-op | `cache`、`sediment`、`no-op` | 上游 leading word |
| model-invoked、user-invoked | `model-invoked`、`user-invoked` | invocation 机制名称 |
| router skill | `router skill` | 上游 invocation 机制名称 |
| frontmatter、description、invocation | 保留原文 | 技能机制字面词 |

## 逐段完整性检查

| 上游位置 | 结论 |
| --- | --- |
| `SKILL.md:1-8` | 技能触发范围、不同封装共享写法、过程可预测性和技能专有 reference 均已保留 |
| `SKILL.md:10-18` | context pointer 定义、措辞决定触发、variance bug、两项职责和三条 pointer 删减规则均已保留 |
| `SKILL.md:20-27` | 上下文负荷、认知负荷、人作为索引和 pointer 的成本交换均已保留 |
| `SKILL.md:29-43` | 两类内容、三层信息层级、渐进式披露、共置和 `sprawl` 均已保留 |
| `SKILL.md:45-52` | 完成判据的清晰度、要求力度、过早完成、post-completion steps、真实上下文边界、legwork、可检查和穷尽均已保留 |
| `SKILL.md:54-59` | 按顺序与按 invocation 两种拆分，以及合并顺序导致过早完成的反向风险均已保留 |
| `SKILL.md:61-74` | leading word 的预训练先验、两种固定作用、两个重构例子、双重收益和否定表达均已保留 |
| `SKILL.md:76-81` | 唯一事实来源、重复、环境、cache、相关性、sediment 和 no-op 均已保留 |
| `SKILL-MECHANICS.md:1-14` | 技能专有范围、model-invoked 与 user-invoked 的发现方式、两种负荷和共享 reference 归属均已保留 |
| `SKILL-MECHANICS.md:16-18` | 按 invocation 拆分的两个触发条件和上下文负荷判据均已保留 |
| `SKILL-MECHANICS.md:20-22` | router skill 解决认知负荷、只能提示和不能触发均已保留 |
| `agents/openai.yaml:1-3` | 展示名称和短描述均已保留 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。三个上游文件的标题、正文、列表、例子和完成判据均有对应翻译 |
| 增写 | 无。没有加入 MMW 的输出规范、宿主物化或项目技能目录规则 |
| 曲解 | 无。渐进式披露没有被缩写成 token 优化；拆分仍要求真实分支、顺序或独立 invocation |
| 术语漂移 | 无。context pointer、两种负荷、信息层级、完成判据、leading word 和 invocation 机制均使用固定写法 |
