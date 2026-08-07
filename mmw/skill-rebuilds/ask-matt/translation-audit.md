# `ask-matt` 1.2.2 翻译审查

## 本技能术语应用

共享术语只由 [上游技能翻译共享术语](../translation-terms.md) 定义。下表记录本技能的术语应用和独有术语，不建立第二份定义。

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| flow、main flow | 流程、主流程 | 使用标准中文，并保留层级 |
| on-ramp | `on-ramp` | 流程图中的上游方法词，没有稳定且等价的中文专名 |
| context window | 上下文窗口 | 标准中文译名 |
| session | `session` | 不与上下文窗口或宿主任务混同 |
| skill | 技能 | 标准中文译名 |
| harness | `harness` | 没有稳定且等价的中文译名 |
| sub-agent | `subagent` | 与仓库跨技能术语一致 |
| primary source、secondary source | 一手来源、二手来源 | 保留信息损失关系 |
| smart zone | `smart zone` | 上游链接定义的专名 |
| phase boundary | 阶段边界 | 标准中文译名 |
| decision ticket、blocking edge、frontier | `decision ticket`、`blocking edge`、`frontier` | 上游方法词 |
| paper trail | 书面记录 | 译出长期可追溯记录的含义 |

## 逐行完整性检查

空行只承担 Markdown 分隔，不包含待翻译文字。下表逐一登记其他每一行。

| 上游行 | 本行翻译检查 |
| --- | --- |
| `SKILL.md:1` | YAML 起始分隔符已保留 |
| `SKILL.md:2` | `name: ask-matt` 字面量已保留 |
| `SKILL.md:3` | 询问技能或流程、适配当前情形和仓库技能路由器均已保留 |
| `SKILL.md:4` | `disable-model-invocation: true` 已保留 |
| `SKILL.md:5` | YAML 结束分隔符已保留 |
| `SKILL.md:7` | `Ask Matt` 标题已保留 |
| `SKILL.md:9` | 不记得所有技能时直接询问已保留 |
| `SKILL.md:11` | 流程定义、主流程、两条 on-ramp 和其他内容独立或位于底层均已保留；没有纠正上游所写的数量 |
| `SKILL.md:13` | 主流程的 idea 到 ship 方向已译为“想法到交付” |
| `SKILL.md:15` | 多数工作经过、从想法到构建均已保留 |
| `SKILL.md:17` | grill-with-docs 访谈、工作目录触发、有状态、两个持久文档、无目录 fallback、共享 grilling 原语、书面记录和有仓库时更优均已保留 |
| `SKILL.md:18` | 对话能否解决、三类可运行答案、prototype 绕行、双向 handoff、独立目录和阶段边界理由均已保留 |
| `SKILL.md:19` | handoff 移出和基于文件开启全新 session 已保留 |
| `SKILL.md:20` | prototype 使用一次性代码回答问题已保留 |
| `SKILL.md:21` | handoff 移回所得认识并由原始想法对话引用已保留 |
| `SKILL.md:22` | 是否跨多个 session 的分支问题已保留 |
| `SKILL.md:23` | 是分支中的 to-spec、to-tickets、tracer bullet、blocking edge、两类 tracker、blocker 优先、原生 link、可认领判据、逐 ticket implement、逐次 clear 和上下文可丢弃均已保留 |
| `SKILL.md:24` | 否分支在同一上下文窗口直接 implement 已保留 |
| `SKILL.md:26` | 两种分支都由 implement 内部驱动 tdd、逐 red-green 切片、code-review 双轴收尾、提交时点，以及单独使用 tdd 和 code-review 的条件均已保留 |
| `SKILL.md:28` | `Context hygiene` 译为“上下文管理” |
| `SKILL.md:30` | 第 1 至 3 步保持同一窗口、to-tickets 前不 compact 或 clear、三阶段共享思考，以及每次 implement 从 ticket 和新上下文开始均已保留 |
| `SKILL.md:32` | smart zone、约 15 万 token、推理敏锐范围、to-tickets 前接近上限、禁止退化推进和最近阶段边界 compact 均已保留 |
| `SKILL.md:34` | `On-ramps` 方法标题已保留 |
| `SKILL.md:36` | 起始情形产生工作并并入主流程的定义已保留 |
| `SKILL.md:38` | bug 与请求堆积进入 triage、经过角色、产出 agent-ready issue 和 implement 后续认领均已保留 |
| `SKILL.md:40` | triage 只处理非自己创建的原始 issue、三类例子和禁止 triage to-tickets 产物均已保留 |
| `SKILL.md:42` | 损坏进入 diagnosing-bugs、三类困难 bug、先取得会因本 bug 变成 red 的 tight 单命令反馈循环、拒绝过早理论、回归测试修复和无 seam 时移交架构改进均已保留 |
| `SKILL.md:44` | 巨大模糊 effort、两个例子、单 session 上限、wayfinder 认知负担、道路不可见、共享 map、decision ticket、逐张解决、决定而非交付物、清雾、与 grilling 的边界和禁止用于范围明确功能均已保留 |
| `SKILL.md:46` | map 清晰后移交而不构建、在 to-spec 并入、归并关联决定、正常进入 to-tickets 与 implement、禁止直接循环及小型 effort 例外均已保留 |
| `SKILL.md:48` | `Codebase health` 译为“代码库健康” |
| `SKILL.md:50` | 非功能工作而是维护已保留 |
| `SKILL.md:52` | 空闲时运行、适合 agent 操作、deepening opportunity、选择后产生想法、在 grilling 进入主流程、勘察与工作台关系均已保留 |
| `SKILL.md:54` | `Vocabulary underneath` 译为“底层词汇” |
| `SKILL.md:56` | 两份模型调用 reference、位于其他技能底层、各自词汇唯一事实来源、词语问题时直接用或由上层技能引入均已保留 |
| `SKILL.md:58` | domain-modeling、明确领域语言、三类动作、grill-with-docs 驱动和保持 CONTEXT 术语表干净均已保留 |
| `SKILL.md:59` | codebase-design 的七个词、module 形状、小 interface 承载大量行为、干净 seam，以及 tdd 和架构改进使用均已保留 |
| `SKILL.md:61` | `Phase boundaries` 译为“阶段边界” |
| `SKILL.md:63` | 阶段定义、三个例子、两阶段边界、五个选项和这是 map 中最模糊决定均已保留 |
| `SKILL.md:65` | Continue 的留在原处、零成本和零损失均已保留 |
| `SKILL.md:66` | clear 在当前内容与下一步无关时清空窗口已保留 |
| `SKILL.md:67` | handoff 的可移植 Markdown、四项窄条件和可移植性收益均已保留 |
| `SKILL.md:68` | Subagent 的严格范围 task、独立窗口和返回报告均已保留 |
| `SKILL.md:69` | compact 压缩、初始化新 session、默认但位于树底部而非首选均已保留 |
| `SKILL.md:71` | reference 链接、有序树、五个问题、分支理由、一手来源成本、只有不能 Continue 才考虑其他选项、边界时点和阶段中途仅继续或拆 subagent 均已保留 |
| `SKILL.md:73` | `Standalone` 译为“独立技能” |
| `SKILL.md:75` | 完全位于主流程之外已保留 |
| `SKILL.md:77` | grill-me 同访谈、无状态、无本地保存、无 CONTEXT、无工作目录条件、四类内容、有目录时改用 grill-with-docs 和后者严格更优均已保留 |
| `SKILL.md:78` | grilling 原语、round、frontier、事实和决定责任、两个入口、三个内部调用方和仅在无需包装时直接使用均已保留 |
| `SKILL.md:79` | resolving-merge-conflicts、merge 或 rebase、逐 hunk、按双方一手意图而非选行、完成操作、禁止 abort、独立及冲突中使用均已保留 |
| `SKILL.md:80` | prototype 小型一次性程序、两个问题例子、一次性约束不等于销毁、答案进入真实代码、prototype 作为一手来源保留在指定分支并由实施 issue 指向，以及两类使用时机均已保留 |
| `SKILL.md:81` | research 委托后台 agent 阅读、一手来源、带引用 Markdown、并行继续工作、产物进入 grilling 和提供材料但不取代思考均已保留 |
| `SKILL.md:82` | to-questionnaire 的外部知识阻塞、供他人填写、grill-me 反向形式、采访发送对象和所需结果、问题对准缺口及回流两项技能均已保留 |
| `SKILL.md:83` | wizard 只用于人类步骤、五类例子、交互 Bash、打开 URL、捕获值、写入两类位置、避免重复解释、模型调用时点、agent 能做则自己做和确需人类的边界均已保留 |
| `SKILL.md:84` | wait-what 的纠正目的、任意技能中途、补上下文、直白语言、CONTEXT 词汇、事后作用和 grilling 事前预防均已保留 |
| `SKILL.md:85` | teach 跨 session 学习和当前目录有状态工作区已保留 |
| `SKILL.md:86` | writing-for-agents 的 agent 文档 reference 和三类对象均已保留 |
| `SKILL.md:88` | `Precondition` 译为“前置条件” |
| `SKILL.md:90` | setup 的首次工程流程时点、三项配置、其他技能假设和自定义 tracker 支持均已保留 |
| `PHASE-BOUNDARIES.md:1` | `Phase boundaries` 标题已保留 |
| `PHASE-BOUNDARIES.md:3` | 阶段定义、三个例子、有意模糊和主观结束语均已保留 |
| `PHASE-BOUNDARIES.md:5` | 边界定义、唯一决策位置、阶段中途继续或拆 subagent，以及中途 compact 丢失思路均已保留 |
| `PHASE-BOUNDARIES.md:7` | 五种选项标题已保留 |
| `PHASE-BOUNDARIES.md:9` | 表头 Option 与 What it does 已翻译 |
| `PHASE-BOUNDARIES.md:10` | 表格分隔行已保留 |
| `PHASE-BOUNDARIES.md:11` | Continue 留在 session 且完全不切换上下文已保留 |
| `PHASE-BOUNDARIES.md:12` | clear 清空窗口并从零开始已保留 |
| `PHASE-BOUNDARIES.md:13` | handoff 编写可移植 Markdown 并可在任意位置初始化 session 已保留 |
| `PHASE-BOUNDARIES.md:14` | Subagent 使用独立窗口并返回报告已保留 |
| `PHASE-BOUNDARIES.md:15` | compact 压缩上下文并以摘要初始化新 session 已保留 |
| `PHASE-BOUNDARIES.md:17` | `The tree` 译为“决策树” |
| `PHASE-BOUNDARIES.md:19` | 边界上从上到下判断和第一个是获胜均已保留 |
| `PHASE-BOUNDARIES.md:21` | Continue 问题、两个为是的条件、一手来源、smart zone、15 万 token、grilling 到 implementation 案例、需要逐字推理而非摘要，以及只有答案为否才考虑其他选项均已保留 |
| `PHASE-BOUNDARIES.md:23` | context 是否无关、三类可丢弃内容、clear、最低成本、零时间、归还窗口和旧 session 可恢复均已保留 |
| `PHASE-BOUNDARIES.md:25` | 错误成本单向、清除相关上下文丢失原因和重读 diff 无法取回均已保留 |
| `PHASE-BOUNDARIES.md:27` | handoff 问题、适用范围窄和只有四种情形已保留 |
| `PHASE-BOUNDARIES.md:29` | 切换新 harness 和 Claude 到 Codex 示例已保留 |
| `PHASE-BOUNDARIES.md:30` | 移动到新目录或仓库已保留 |
| `PHASE-BOUNDARIES.md:31` | 发送给同事已保留 |
| `PHASE-BOUNDARIES.md:32` | 阶段中途分出旁支且不打断当前工作已保留 |
| `PHASE-BOUNDARIES.md:34` | 清单是完整条件、可移植性、文件移动和无移动则不需要均已保留 |
| `PHASE-BOUNDARIES.md:36` | AFK 问题、无需引导的范围、subagent、当前 session 不变和自动审查案例均已保留 |
| `PHASE-BOUNDARIES.md:38` | 否则 compact、四项落点条件、经常落在这里、传入指令示例和摘要保留下一阶段内容均已保留 |
| `PHASE-BOUNDARIES.md:40` | compact 默认但非首选、位于底部的成本与精度理由，以及摘要压平决定造成自信错误均已保留 |
| `PHASE-BOUNDARIES.md:42` | 一手来源和二手来源标题已保留 |
| `PHASE-BOUNDARIES.md:44` | 除 Continue 外都把实际 session 的一手来源变成摘要二手来源，以及取舍形状已保留 |
| `PHASE-BOUNDARIES.md:46` | 来源、信息、噪声和可用空间四列表头已保留 |
| `PHASE-BOUNDARIES.md:47` | 表格分隔行已保留 |
| `PHASE-BOUNDARIES.md:48` | 一手来源 Continue 的完整、多噪声和少空间已保留 |
| `PHASE-BOUNDARIES.md:49` | 二手来源 compact 与 handoff 的有损、少噪声和多空间已保留 |
| `PHASE-BOUNDARIES.md:51` | 问题 1 优先和仅在留下成本更高时接受有损均已保留 |
| `PHASE-BOUNDARIES.md:53` | 这些事项都需要判断的标题已保留 |
| `PHASE-BOUNDARIES.md:55` | 非客观、包含判断、同边界可有不同结果，以及依次在边界而非中途提问的价值均已保留 |
| `agents/openai.yaml:1` | `interface` 字段已保留 |
| `agents/openai.yaml:2` | `display_name: "Ask Matt"` 已保留 |
| `agents/openai.yaml:3` | 寻找正确技能或工作流已保留 |
| `agents/openai.yaml:4` | `policy` 字段已保留 |
| `agents/openai.yaml:5` | `allow_implicit_invocation: false` 已保留 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。三个上游文件的每个非空行都有对应译文和独立检查记录 |
| 增写 | 无。没有加入 MMW 入口、角色、CLI、tracker、worktree 或宿主物化接线 |
| 曲解 | 无。主流程、on-ramp、独立技能和阶段边界决策树的先后与完成关系保持原样 |
| 术语漂移 | 无。流程、阶段边界、session、上下文窗口、subagent、一手来源和二手来源使用一致 |
