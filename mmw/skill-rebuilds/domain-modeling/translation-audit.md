# `domain-modeling` 1.2.2 翻译审查

## 固定术语

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| domain model | 领域模型 | 领域驱动设计标准中文译名 |
| ubiquitous language | 通用语言 | 领域驱动设计标准中文译名 |
| context | `context` | 不与 session 上下文混同，也不擅自补成 bounded context |
| glossary | 术语表 | 标准中文译名 |
| canonical term | 规范术语 | 表达被选定的统一用词 |
| decision | 决定 | 与 ADR 记录的实际选择一致 |
| implementation | `implementation` | 与 codebase-design 核心词汇一致 |
| lazy、lazily | 按需 | 表达首次需要时才创建 |
| lock-in | `lock-in` | 行业通用词，不误缩成依赖 |
| event sourcing、event-sourced | `event sourcing`、采用 `event sourcing` | 保留架构模式名称 |

## 逐行完整性检查

空行只承担 Markdown 分隔，不包含待翻译文字。下表逐一登记其他每一行，包括目录树和模板。

| 上游行 | 本行翻译检查 |
| --- | --- |
| `SKILL.md:1` | YAML 起始分隔符已保留 |
| `SKILL.md:2` | `name: domain-modeling` 字面量已保留 |
| `SKILL.md:3` | 构建明确领域模型、领域术语、通用语言、架构决定和其他技能维护场景均已保留 |
| `SKILL.md:4` | YAML 结束分隔符已保留 |
| `SKILL.md:6` | `Domain Modeling` 标题已保留 |
| `SKILL.md:8` | 设计时主动构建、质疑术语、构造边界场景、结晶即写入、仅读取不属于本技能、任何技能可读和改变而非消费边界均已保留 |
| `SKILL.md:10` | 文件结构标题已保留 |
| `SKILL.md:12` | 多数仓库单 context 已保留 |
| `SKILL.md:14` | 第一棵目录树代码块起始已保留 |
| `SKILL.md:15` | 根目录已保留 |
| `SKILL.md:16` | 根 CONTEXT 文件已保留 |
| `SKILL.md:17` | docs 目录已保留 |
| `SKILL.md:18` | adr 子目录已保留 |
| `SKILL.md:19` | 第一份 ADR 示例已保留 |
| `SKILL.md:20` | 第二份 ADR 示例已保留 |
| `SKILL.md:21` | src 目录已保留 |
| `SKILL.md:22` | 第一棵目录树结束已保留 |
| `SKILL.md:24` | 根 CONTEXT-MAP 判定多 context 和 map 指向位置均已保留 |
| `SKILL.md:26` | 第二棵目录树代码块起始已保留 |
| `SKILL.md:27` | 根目录已保留 |
| `SKILL.md:28` | 根 CONTEXT-MAP 文件已保留 |
| `SKILL.md:29` | docs 目录已保留 |
| `SKILL.md:30` | 系统级决定的 adr 目录及注释已保留 |
| `SKILL.md:31` | src 目录已保留 |
| `SKILL.md:32` | ordering 目录已保留 |
| `SKILL.md:33` | ordering CONTEXT 已保留 |
| `SKILL.md:34` | ordering context 专属 adr 及注释已保留 |
| `SKILL.md:35` | billing 目录已保留 |
| `SKILL.md:36` | billing CONTEXT 已保留 |
| `SKILL.md:37` | billing adr 目录已保留 |
| `SKILL.md:38` | 第二棵目录树结束已保留 |
| `SKILL.md:40` | 按需创建、只有内容才写、首次术语创建 CONTEXT、首次 ADR 创建目录均已保留 |
| `SKILL.md:42` | session 期间标题已保留 |
| `SKILL.md:44` | 对照术语表质疑标题已保留 |
| `SKILL.md:46` | 用户用词冲突时立即指出，以及 cancellation 的 X 与 Y 问句均已保留 |
| `SKILL.md:48` | 明确含混语言标题已保留 |
| `SKILL.md:50` | 含混或多义词、提出规范术语和 account、Customer、User 示例均已保留 |
| `SKILL.md:52` | 讨论具体场景标题已保留 |
| `SKILL.md:54` | 领域关系压力测试、构造边界场景和迫使用户明确概念边界均已保留 |
| `SKILL.md:56` | 与代码交叉检查标题已保留 |
| `SKILL.md:58` | 用户陈述时检查代码、发现矛盾时呈现，以及 Order 整体与部分取消问句均已保留 |
| `SKILL.md:60` | 就地更新 CONTEXT 标题已保留 |
| `SKILL.md:62` | 术语解决时立即更新、不批量积攒、发生时记录和格式链接均已保留 |
| `SKILL.md:64` | CONTEXT 完全排除 implementation、禁止三种用途和仅作为术语表均已保留 |
| `SKILL.md:66` | 谨慎提议 ADR 标题已保留 |
| `SKILL.md:68` | 只有三项全满足才提议已保留 |
| `SKILL.md:70` | 难逆转和未来改主意成本均已保留 |
| `SKILL.md:71` | 无上下文令人意外和未来读者疑问均已保留 |
| `SKILL.md:72` | 真实取舍、确有备选和具体选择理由均已保留 |
| `SKILL.md:74` | 任一缺失就跳过和 ADR 格式链接均已保留 |
| `ADR-FORMAT.md:1` | ADR 格式标题已保留 |
| `ADR-FORMAT.md:3` | docs/adr 位置、连续编号和两个文件名示例均已保留 |
| `ADR-FORMAT.md:5` | 首次需要 ADR 时才按需创建目录已保留 |
| `ADR-FORMAT.md:7` | 模板标题已保留 |
| `ADR-FORMAT.md:9` | Markdown 模板代码块起始已保留 |
| `ADR-FORMAT.md:10` | 决定简短标题占位符已翻译 |
| `ADR-FORMAT.md:12` | 1 至 3 句、context、决定和原因三个问题均已翻译 |
| `ADR-FORMAT.md:13` | 模板代码块结束已保留 |
| `ADR-FORMAT.md:15` | ADR 可单段、价值在记录决定事实与原因而非填章节均已保留 |
| `ADR-FORMAT.md:17` | 可选章节标题已保留 |
| `ADR-FORMAT.md:19` | 仅在真实增值时加入和多数 ADR 不需要均已保留 |
| `ADR-FORMAT.md:21` | Status frontmatter、四个字面状态和重新审视时用途均已保留 |
| `ADR-FORMAT.md:22` | Considered Options 只在拒绝选项值得记住时加入已保留 |
| `ADR-FORMAT.md:23` | Consequences 只在非明显下游影响需指出时加入已保留 |
| `ADR-FORMAT.md:25` | 编号标题已保留 |
| `ADR-FORMAT.md:27` | 扫描最大现有编号并加一已保留 |
| `ADR-FORMAT.md:29` | 何时提议 ADR 标题已保留 |
| `ADR-FORMAT.md:31` | 三项必须全满足已保留 |
| `ADR-FORMAT.md:33` | 难逆转和未来改主意成本均已保留 |
| `ADR-FORMAT.md:34` | 无上下文令人意外、未来读代码和更强疑问措辞均已保留 |
| `ADR-FORMAT.md:35` | 真实取舍、确有备选和具体选择理由均已保留 |
| `ADR-FORMAT.md:37` | 易逆转、并不意外、无真实备选三种跳过理由和显然做法引语均已保留 |
| `ADR-FORMAT.md:39` | 符合条件内容标题已保留 |
| `ADR-FORMAT.md:41` | 架构形状、monorepo、event-sourced write model 和 Postgres read projection 两例均已保留 |
| `ADR-FORMAT.md:42` | context 间集成、Ordering、Billing、domain event 和非同步 HTTP 均已保留 |
| `ADR-FORMAT.md:43` | lock-in 技术、四类例子、非所有 library 和更换需一季度门槛均已保留 |
| `ADR-FORMAT.md:44` | 边界范围、Customer data 所有权、其他 context 仅 ID 引用和 no 与 yes 同等价值均已保留 |
| `ADR-FORMAT.md:45` | 有意偏离、手写 SQL 非 ORM、合理读者会假定相反和防止后续误修均已保留 |
| `ADR-FORMAT.md:46` | 代码不可见约束、AWS 合规和 200ms partner contract 两例均已保留 |
| `ADR-FORMAT.md:47` | 非明显拒绝备选、GraphQL 与 REST、细微理由和六个月后重复提议均已保留 |
| `CONTEXT-FORMAT.md:1` | CONTEXT 格式标题已保留 |
| `CONTEXT-FORMAT.md:3` | 结构标题已保留 |
| `CONTEXT-FORMAT.md:5` | Markdown 模板代码块起始已保留 |
| `CONTEXT-FORMAT.md:6` | Context 名称占位符已翻译 |
| `CONTEXT-FORMAT.md:8` | 一两句 context 定义及存在理由占位符已翻译 |
| `CONTEXT-FORMAT.md:10` | Language 标题译为“语言” |
| `CONTEXT-FORMAT.md:12` | Order 术语示例已保留 |
| `CONTEXT-FORMAT.md:13` | 一两句术语描述占位符已翻译 |
| `CONTEXT-FORMAT.md:14` | Avoid 和 Purchase、transaction 已保留 |
| `CONTEXT-FORMAT.md:16` | Invoice 术语示例已保留 |
| `CONTEXT-FORMAT.md:17` | 交付后向 customer 发送付款请求的定义已翻译 |
| `CONTEXT-FORMAT.md:18` | Avoid 和 Bill、payment request 已保留 |
| `CONTEXT-FORMAT.md:20` | Customer 术语示例已保留 |
| `CONTEXT-FORMAT.md:21` | 下订单的人或组织定义已翻译 |
| `CONTEXT-FORMAT.md:22` | Avoid 和 Client、buyer、account 已保留 |
| `CONTEXT-FORMAT.md:23` | 模板代码块结束已保留 |
| `CONTEXT-FORMAT.md:25` | 规则标题已保留 |
| `CONTEXT-FORMAT.md:27` | 明确主张、同概念多词、选最佳和其余列 Avoid 均已保留 |
| `CONTEXT-FORMAT.md:28` | 定义最多一两句、定义是什么而非做什么均已保留 |
| `CONTEXT-FORMAT.md:29` | 只含项目 context 特有术语、三类通用概念例子、大量使用也不加入、增加前二分问题和只有前者加入均已保留 |
| `CONTEXT-FORMAT.md:30` | 自然集群时副标题分组和单一紧密领域可用扁平清单均已保留 |
| `CONTEXT-FORMAT.md:32` | 单与多 context 仓库标题已保留 |
| `CONTEXT-FORMAT.md:34` | 多数仓库的单 context 和根 CONTEXT 已保留 |
| `CONTEXT-FORMAT.md:36` | 多 context、根 CONTEXT-MAP 列 context、位置和关系均已保留 |
| `CONTEXT-FORMAT.md:38` | Context Map 模板代码块起始已保留 |
| `CONTEXT-FORMAT.md:39` | Context Map 标题已保留 |
| `CONTEXT-FORMAT.md:41` | Contexts 标题已保留 |
| `CONTEXT-FORMAT.md:43` | Ordering 路径、接收和跟踪 customer order 已保留 |
| `CONTEXT-FORMAT.md:44` | Billing 路径、生成 invoice 和处理 payment 已保留 |
| `CONTEXT-FORMAT.md:45` | Fulfillment 路径、仓库拣货和发货已保留 |
| `CONTEXT-FORMAT.md:47` | Relationships 标题已保留 |
| `CONTEXT-FORMAT.md:49` | Ordering 到 Fulfillment、OrderPlaced、发出消费和开始拣货均已保留 |
| `CONTEXT-FORMAT.md:50` | Fulfillment 到 Billing、ShipmentDispatched、发出消费和生成 invoice 均已保留 |
| `CONTEXT-FORMAT.md:51` | Ordering 与 Billing 双向关系及共享两个 type 均已保留 |
| `CONTEXT-FORMAT.md:52` | Context Map 模板代码块结束已保留 |
| `CONTEXT-FORMAT.md:54` | 技能推断适用结构已保留 |
| `CONTEXT-FORMAT.md:56` | 有 CONTEXT-MAP 时读取寻找 context 已保留 |
| `CONTEXT-FORMAT.md:57` | 只有根 CONTEXT 时单 context 已保留 |
| `CONTEXT-FORMAT.md:58` | 两者皆无时首个术语解决后按需创建根 CONTEXT 已保留 |
| `CONTEXT-FORMAT.md:60` | 多 context 时推断当前主题归属，不明确则询问已保留 |
| `agents/openai.yaml:1` | `interface` 字段已保留 |
| `agents/openai.yaml:2` | `display_name: "Domain Modeling"` 已保留 |
| `agents/openai.yaml:3` | 构建并明确领域模型已保留 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。四个上游文件的每个非空行，包括目录树和模板，都有对应译文和独立检查记录 |
| 增写 | 无。没有加入 `mmw domain path`、leaf、MMW ADR 路径或其他 MMW 接线 |
| 曲解 | 无。主动维护与只读消费的边界、即时写入和 ADR 三项门槛保持原样 |
| 术语漂移 | 无。领域模型、通用语言、context、术语表、规范术语、决定和 implementation 使用一致 |
