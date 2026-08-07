# `codebase-design` 1.2.2 翻译审查

## 固定术语

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| module、interface、implementation | `module`、`interface`、`implementation` | 上游要求精确使用的核心词汇 |
| depth、deep、shallow | `depth`、`deep`、`shallow` | 同一组深度概念，不另造中文近义词 |
| seam、adapter、leverage、locality | `seam`、`adapter`、`leverage`、`locality` | 上游要求精确使用的核心词汇 |
| deepening | `deepening` | 方法名称及过程统一使用原词 |
| port | `port` | Ports & Adapters 中的固定角色词 |
| test surface | 测试表面 | 保留测试只能跨 interface 观察的含义 |
| internal seam、external seam | `internal seam`、`external seam` | 不与 module 的外部边界混同 |
| sub-agent | `subagent` | 与仓库跨技能术语一致 |
| brief | `task` | 按仓库已确认的派发说明术语统一 |

## 逐行完整性检查

空行只承担 Markdown 分隔，不包含待翻译文字。下表逐一登记其他每一行，包括图形和代码示例。

| 上游行 | 本行翻译检查 |
| --- | --- |
| `SKILL.md:1` | YAML 起始分隔符已保留 |
| `SKILL.md:2` | `name: codebase-design` 字面量已保留 |
| `SKILL.md:3` | deep module 共享词汇、interface 设计改进、deepening opportunity、seam 位置、可测试性、AI 可导航性和其他技能引用场景均已保留 |
| `SKILL.md:4` | YAML 结束分隔符已保留 |
| `SKILL.md:6` | `Codebase Design` 标题已保留 |
| `SKILL.md:8` | deep module 定义、小 interface、干净 seam、通过 interface 测试、适用范围和三个受益目标均已保留 |
| `SKILL.md:10` | `Glossary` 译为“术语表” |
| `SKILL.md:12` | 要求准确用词、四个禁止替代词和一致语言目的均已保留 |
| `SKILL.md:14` | Module 的 interface 与 implementation 定义、规模无关、四类例子和三个避免词均已保留 |
| `SKILL.md:16` | Interface 是调用方必须知道的一切、六类内容、两个避免词和过窄原因均已保留 |
| `SKILL.md:18` | Implementation 的内部定义、与 Adapter 区分、两个大小反例和按 seam 话题选词均已保留 |
| `SKILL.md:20` | Depth 是 interface leverage、行为与学习量关系、deep 和 shallow 两端定义均已保留 |
| `SKILL.md:22` | Feathers 出处、无需原地编辑即可改变行为、interface 所在位置、位置与内容两项决定区分，以及禁止 boundary 原因均已保留 |
| `SKILL.md:24` | Adapter 是 seam 上满足 interface 的具体对象、描述角色而非实质均已保留 |
| `SKILL.md:26` | Leverage 是 depth 给调用方的能力回报，以及 N 个调用位置和 M 个测试均已保留 |
| `SKILL.md:28` | Locality 是维护者所得集中性、四类集中内容和一次修复处处生效均已保留 |
| `SKILL.md:30` | deep 与 shallow 对比标题已保留 |
| `SKILL.md:32` | deep module 等于小 interface 加大量 implementation 已保留 |
| `SKILL.md:34` | deep module 图形代码块起始已保留 |
| `SKILL.md:35` | 图形上边框已保留 |
| `SKILL.md:36` | Small Interface 及方法少、参数简单注释已保留 |
| `SKILL.md:37` | 图形分隔线已保留 |
| `SKILL.md:38` | implementation 空白区域已保留 |
| `SKILL.md:39` | Deep Implementation 及隐藏复杂逻辑注释已保留 |
| `SKILL.md:40` | implementation 空白区域已保留 |
| `SKILL.md:41` | 图形下边框已保留 |
| `SKILL.md:42` | deep module 图形代码块结束已保留 |
| `SKILL.md:44` | shallow module 等于大 interface 加少量 implementation 及避免要求已保留 |
| `SKILL.md:46` | shallow module 图形代码块起始已保留 |
| `SKILL.md:47` | 图形上边框已保留 |
| `SKILL.md:48` | Large Interface 及方法多、参数复杂注释已保留 |
| `SKILL.md:49` | 图形分隔线已保留 |
| `SKILL.md:50` | Thin Implementation 及只做透传注释已保留 |
| `SKILL.md:51` | 图形下边框已保留 |
| `SKILL.md:52` | shallow module 图形代码块结束已保留 |
| `SKILL.md:54` | 设计 interface 时提出问题的引导已保留 |
| `SKILL.md:56` | 减少方法数量的问题已保留 |
| `SKILL.md:57` | 简化参数的问题已保留 |
| `SKILL.md:58` | 隐藏更多内部复杂性的问题已保留 |
| `SKILL.md:60` | `Principles` 译为“原则” |
| `SKILL.md:62` | Depth 属于 interface、内部可由小型可 mock 可替换部分组成、不属于 interface、internal seam 与 external seam 均已保留 |
| `SKILL.md:63` | 删除检验、删除 module、复杂性消失代表透传、复杂性在 N 个调用方重现代表发挥价值均已保留 |
| `SKILL.md:64` | interface 是测试表面、调用方与测试跨同一 seam，以及越过 interface 测试说明形状可能错误均已保留 |
| `SKILL.md:65` | 一个 adapter 对应假设 seam、两个对应真实 seam，以及只有确实变化才引入均已保留 |
| `SKILL.md:67` | 为可测试性设计标题已保留 |
| `SKILL.md:69` | 良好 interface 让测试自然已保留 |
| `SKILL.md:71` | 接收依赖而非创建依赖的第一项原则已保留 |
| `SKILL.md:73` | 第一段 TypeScript 代码块起始已保留 |
| `SKILL.md:74` | 可测试注释已翻译 |
| `SKILL.md:75` | 接收 `paymentGateway` 的函数示例字面量已保留 |
| `SKILL.md:77` | 难测试注释已翻译 |
| `SKILL.md:78` | 内部创建依赖的函数起始已保留 |
| `SKILL.md:79` | 创建 `StripeGateway` 的代码字面量已保留 |
| `SKILL.md:80` | 函数结束大括号已保留 |
| `SKILL.md:81` | 第一段代码块结束已保留 |
| `SKILL.md:83` | 返回结果而非产生副作用的第二项原则已保留 |
| `SKILL.md:85` | 第二段 TypeScript 代码块起始已保留 |
| `SKILL.md:86` | 可测试注释已翻译 |
| `SKILL.md:87` | 返回 Discount 的函数示例字面量已保留 |
| `SKILL.md:89` | 难测试注释已翻译 |
| `SKILL.md:90` | 返回 void 的函数起始已保留 |
| `SKILL.md:91` | 修改 cart 总额的副作用代码已保留 |
| `SKILL.md:92` | 函数结束大括号已保留 |
| `SKILL.md:93` | 第二段代码块结束已保留 |
| `SKILL.md:95` | 小表面积、方法越少测试越少、参数越少设置越简单均已保留 |
| `SKILL.md:97` | `Relationships` 译为“关系” |
| `SKILL.md:99` | Module 恰好一个 Interface 及其面向调用方和测试的含义已保留 |
| `SKILL.md:100` | Depth 属于 Module 并相对 Interface 衡量已保留 |
| `SKILL.md:101` | Seam 是 Module Interface 所在位置已保留 |
| `SKILL.md:102` | Adapter 位于 Seam 并满足 Interface 已保留 |
| `SKILL.md:103` | Depth 为调用方产生 Leverage、为维护者产生 Locality 已保留 |
| `SKILL.md:105` | `Rejected framings` 译为“不采用的表述” |
| `SKILL.md:107` | Ousterhout 行数比定义、奖励填充问题和改用 depth-as-leverage 均已保留 |
| `SKILL.md:108` | TypeScript interface 或 public method 的过窄表述，以及调用方必须知道全部事实均已保留 |
| `SKILL.md:109` | Boundary 与 DDD bounded context 重叠，以及改用 seam 或 interface 均已保留 |
| `SKILL.md:111` | `Going deeper` 译为“深入阅读” |
| `SKILL.md:113` | 按依赖 deepening module 集合、DEEPENING 链接和三项内容均已保留 |
| `SKILL.md:114` | 探索备选 interface、DESIGN-IT-TWICE 链接、并行 subagent、截然不同设计和三个比较维度均已保留 |
| `DEEPENING.md:1` | `Deepening` 标题已保留 |
| `DEEPENING.md:3` | shallow module 集合、安全 deepening、依赖前提和四个假定词汇均已保留 |
| `DEEPENING.md:5` | 依赖分类标题已保留 |
| `DEEPENING.md:7` | 评估候选项时分类依赖，以及分类决定跨 seam 测试方式均已保留 |
| `DEEPENING.md:9` | 第一类 In-process 译为“进程内” |
| `DEEPENING.md:11` | 纯计算、in-memory 状态、无 I/O、始终可 deepening、合并 module、直接经新 interface 测试和无需 adapter 均已保留 |
| `DEEPENING.md:13` | 第二类 Local-substitutable 译为“可在本地替代” |
| `DEEPENING.md:15` | 本地测试替代物、两个例子、存在时可 deepening、测试套件中运行替代物、internal seam 和 external interface 无 port 均已保留 |
| `DEEPENING.md:17` | 第三类 Remote but owned 和 Ports & Adapters 已保留 |
| `DEEPENING.md:19` | 自有跨网络 service、两个例子、seam 上 port、deep module 拥有逻辑、transport 注入、测试与 production adapter 均已保留 |
| `DEEPENING.md:21` | 建议句中的 port、production HTTP adapter、测试 in-memory adapter、逻辑集中和跨网络部署均已保留 |
| `DEEPENING.md:23` | 第四类 True external 和 Mock 已保留 |
| `DEEPENING.md:25` | 不受控第三方 service、两个例子、外部依赖作为注入 port 和测试 mock adapter 均已保留 |
| `DEEPENING.md:27` | Seam 纪律标题已保留 |
| `DEEPENING.md:29` | 一个与两个 adapter 判据、至少两者才引入 port、production 加 test 典型组合，以及单 adapter 只是间接层均已保留 |
| `DEEPENING.md:30` | internal 与 external seam、各自位置和禁止因测试而暴露 internal seam 均已保留 |
| `DEEPENING.md:32` | 测试策略“替换，不要叠加”已保留 |
| `DEEPENING.md:34` | deepened interface 测试存在后旧 shallow unit test 变成浪费并删除均已保留 |
| `DEEPENING.md:35` | 在 deepened module interface 写新测试和 interface 是测试表面均已保留 |
| `DEEPENING.md:36` | 通过 interface 断言可观察结果而非内部状态已保留 |
| `DEEPENING.md:37` | 测试承受内部 refactor、描述行为而非 implementation，以及随 implementation 改变代表越过 interface 均已保留 |
| `DESIGN-IT-TWICE.md:1` | `Design It Twice` 标题已保留 |
| `DESIGN-IT-TWICE.md:3` | 用户探索备选 interface、选定 deepening 候选、并行 subagent 模式、Ousterhout 出处和首个想法通常非最佳均已保留 |
| `DESIGN-IT-TWICE.md:5` | SKILL 链接和五个词汇均已保留 |
| `DESIGN-IT-TWICE.md:7` | `Process` 译为“流程” |
| `DESIGN-IT-TWICE.md:9` | 第 1 步界定问题空间已保留 |
| `DESIGN-IT-TWICE.md:11` | 派发前为选定候选编写面向用户说明已保留 |
| `DESIGN-IT-TWICE.md:13` | 新 interface 必须满足的约束已保留 |
| `DESIGN-IT-TWICE.md:14` | 依赖、所属分类和 DEEPENING 链接已保留 |
| `DESIGN-IT-TWICE.md:15` | 粗略说明性代码草图、让约束落地、并非提案而是具体化方法均已保留 |
| `DESIGN-IT-TWICE.md:17` | 向用户展示后立即进入第 2 步，以及用户阅读思考和 subagent 并行均已保留 |
| `DESIGN-IT-TWICE.md:19` | 第 2 步派出 subagent 已保留 |
| `DESIGN-IT-TWICE.md:21` | Agent 工具、并行至少三个 subagent 和每个产出截然不同 interface 均已保留 |
| `DESIGN-IT-TWICE.md:23` | 每个 subagent 独立技术 task 的四项内容、与用户说明独立和不同设计约束均已保留 |
| `DESIGN-IT-TWICE.md:25` | Agent 1 的 1 至 3 个入口上限和每入口 leverage 最大化均已保留 |
| `DESIGN-IT-TWICE.md:26` | Agent 2 的灵活性、许多使用场景与扩展均已保留 |
| `DESIGN-IT-TWICE.md:27` | Agent 3 的最常见调用方和默认情况简单化均已保留 |
| `DESIGN-IT-TWICE.md:28` | 可选 Agent 4 的 Ports & Adapters 和跨 seam 依赖均已保留 |
| `DESIGN-IT-TWICE.md:30` | task 同时包含 SKILL 和 CONTEXT 词汇，以及架构与领域命名一致目的均已保留 |
| `DESIGN-IT-TWICE.md:32` | 每个 subagent 输出引导已保留 |
| `DESIGN-IT-TWICE.md:34` | Interface 输出的 type、method、parameter、invariant、顺序和错误模式均已保留 |
| `DESIGN-IT-TWICE.md:35` | 调用方使用示例已保留 |
| `DESIGN-IT-TWICE.md:36` | implementation 在 seam 后隐藏的内容已保留 |
| `DESIGN-IT-TWICE.md:37` | 依赖策略、adapter 和 DEEPENING 链接已保留 |
| `DESIGN-IT-TWICE.md:38` | leverage 高低位置的取舍已保留 |
| `DESIGN-IT-TWICE.md:40` | 第 3 步展示并比较已保留 |
| `DESIGN-IT-TWICE.md:42` | 依次展示、用户逐一理解、文字比较和 depth、locality、seam placement 三个维度均已保留 |
| `DESIGN-IT-TWICE.md:44` | 给出自己的最强设计建议与理由、可选混合方案、明确判断和不要菜单均已保留 |
| `agents/openai.yaml:1` | `interface` 字段已保留 |
| `agents/openai.yaml:2` | `display_name: "Codebase Design"` 已保留 |
| `agents/openai.yaml:3` | deep module 设计词汇已保留 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。四个上游文件的每个非空行，包括图形与代码示例，都有对应译文和独立检查记录 |
| 增写 | 无。没有加入 MMW 角色、审查、worktree、tracker 或宿主接线 |
| 曲解 | 无。deep module 定义、依赖分类、seam 纪律、替换测试和 Design It Twice 的并行比较顺序保持原样 |
| 术语漂移 | 无。module、interface、implementation、depth、seam、adapter、leverage、locality 和 deepening 使用一致 |
