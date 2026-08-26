# `tdd` 1.2.2 翻译审查

## 本技能术语应用

共享术语只由 [上游技能翻译共享术语](../translation-terms.md) 定义。下表记录本技能的术语应用和独有术语，不建立第二份定义。

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| test-driven development | 测试驱动开发 | 标准中文译名 |
| red、green、red-green-refactor | `red`、`green`、`red-green-refactor` | TDD 循环阶段和用户触发字面串 |
| seam | `seam` | 与 codebase-design 词汇一致 |
| interface、implementation | `interface`、`implementation` | 与 codebase-design 词汇一致 |
| refactor、refactoring | 重构 | 标准中文译名 |
| vertical slice、horizontal slice | 垂直切片、横向切片 | 标准中文译名 |
| tracer bullet | `tracer bullet` | 上游方法词 |
| tautological | 同义反复 | 逻辑学标准中文译名 |
| mock、mocking | `mock` | 测试替身动作的行业通用词 |
| snapshot、literal | 快照、字面值 | 正统中文技术术语 |
| system boundary | 系统边界 | 标准中文译名 |

## 逐行完整性检查

空行只承担 Markdown 分隔，不包含待翻译文字。下表逐一登记其他每一行，包括全部 TypeScript 示例。

| 上游行 | 本行翻译检查 |
| --- | --- |
| `SKILL.md:1` | YAML 起始分隔符已保留 |
| `SKILL.md:2` | `name: tdd` 字面量已保留 |
| `SKILL.md:3` | 测试驱动开发、功能、bug、测试优先、red-green-refactor 和集成测试触发均已保留 |
| `SKILL.md:4` | YAML 结束分隔符已保留 |
| `SKILL.md:6` | 测试驱动开发标题已翻译 |
| `SKILL.md:8` | TDD 是 red-green、参考内容作用、四类内容、每轮全章节适用和前中查阅而非事后均已保留 |
| `SKILL.md:10` | 探索时读取可选 CONTEXT、测试名和 interface 词汇匹配领域语言、遵守相关 ADR 均已保留 |
| `SKILL.md:12` | 良好测试标题已保留 |
| `SKILL.md:14` | 经公开 interface 测行为、非 implementation、代码可全变测试不变、spec 式测试名例子和不关心内部而承受重构均已保留 |
| `SKILL.md:16` | tests 与 mocking 两个链接及用途均已保留 |
| `SKILL.md:18` | Seam 和测试位置标题已保留 |
| `SKILL.md:20` | seam 是公开测试边界、经 interface 观察不伸内部，以及测试只在 seam 不对 internal 均已保留 |
| `SKILL.md:22` | 只测预先商定 seam、写前记录并用户确认、未确认不写、无法测一切和精力落关键复杂路径而非每边界均已保留 |
| `SKILL.md:24` | 公开 interface 与测试 seam 的原始问句已保留 |
| `SKILL.md:26` | interface 形态存疑、deep 程度、seam 位置、暴露内容、使用 codebase-design 七词、共享来源和参考内容非 session 均已保留 |
| `SKILL.md:28` | 反模式标题已保留 |
| `SKILL.md:30` | implementation-coupled、三类行为、数据库旁路例和重构不改行为却破测试的识别信号均已保留 |
| `SKILL.md:31` | tautological、三类例子、按构造必过、无法不同意代码、独立唯一事实来源和三类来源均已保留 |
| `SKILL.md:32` | horizontal slicing、批量测试虚构行为、形状非用户行为、失敏、过早承诺结构，以及 vertical 一测一实现循环和 tracer bullet 学习均已保留 |
| `SKILL.md:34` | 循环规则标题已保留 |
| `SKILL.md:36` | red 先 green 后、先失败测试、仅足够代码、禁止预判和推测功能均已保留 |
| `SKILL.md:37` | 每轮一 seam、一测试、一最小 implementation 均已保留 |
| `SKILL.md:38` | 重构不属于循环、属于审查、code-review 链接和不属 red-green implementation 均已保留 |
| `mocking.md:1` | When to Mock 标题已翻译 |
| `mocking.md:3` | 只在系统边界 mock 已保留 |
| `mocking.md:5` | 外部 API 和支付电子邮件例子已保留 |
| `mocking.md:6` | 数据库有时 mock 且优先测试数据库已保留 |
| `mocking.md:7` | 时间和随机性已保留 |
| `mocking.md:8` | 文件系统有时 mock 已保留 |
| `mocking.md:10` | 不要 mock 引导已保留 |
| `mocking.md:12` | 自己的类或 module 已保留 |
| `mocking.md:13` | 内部协作者已保留 |
| `mocking.md:14` | 自己控制的一切已保留 |
| `mocking.md:16` | 为可 mock 性设计标题已保留 |
| `mocking.md:18` | 系统边界设计易 mock interface 已保留 |
| `mocking.md:20` | 第一项依赖注入已保留 |
| `mocking.md:22` | 传入外部依赖而非内部创建已保留 |
| `mocking.md:24` | 第一段 TypeScript 代码块起始已保留 |
| `mocking.md:25` | 容易 mock 注释已翻译 |
| `mocking.md:26` | 接收 paymentClient 的函数起始已保留 |
| `mocking.md:27` | paymentClient charge 调用已保留 |
| `mocking.md:28` | 函数结束已保留 |
| `mocking.md:30` | 难 mock 注释已翻译 |
| `mocking.md:31` | 内部创建依赖函数起始已保留 |
| `mocking.md:32` | StripeClient 和环境变量已保留 |
| `mocking.md:33` | client charge 调用已保留 |
| `mocking.md:34` | 函数结束已保留 |
| `mocking.md:35` | 第一段代码块结束已保留 |
| `mocking.md:37` | 第二项 SDK 风格 interface 优先于通用 fetcher 已保留 |
| `mocking.md:39` | 每外部操作具体函数而非条件通用函数已保留 |
| `mocking.md:41` | 第二段 TypeScript 代码块起始已保留 |
| `mocking.md:42` | 好例：每函数独立 mock 注释已翻译 |
| `mocking.md:43` | api 对象起始已保留 |
| `mocking.md:44` | getUser endpoint 已保留 |
| `mocking.md:45` | getOrders endpoint 已保留 |
| `mocking.md:46` | createOrder POST 与 body 已保留 |
| `mocking.md:47` | api 对象结束已保留 |
| `mocking.md:49` | 差例：mock 内部需条件逻辑注释已翻译 |
| `mocking.md:50` | 第二个 api 对象起始已保留 |
| `mocking.md:51` | 通用 fetch 函数已保留 |
| `mocking.md:52` | 第二个 api 对象结束已保留 |
| `mocking.md:53` | 第二段代码块结束已保留 |
| `mocking.md:55` | SDK 方式意味着的引导已保留 |
| `mocking.md:56` | 每 mock 一种具体返回形状已保留 |
| `mocking.md:57` | 测试设置无条件逻辑已保留 |
| `mocking.md:58` | 易看出测试执行端点已保留 |
| `mocking.md:59` | 每端点类型安全已保留 |
| `tests.md:1` | Good and Bad Tests 标题已翻译 |
| `tests.md:3` | 良好测试标题已保留 |
| `tests.md:5` | 集成风格、经真实 interface 和不 mock 内部均已保留 |
| `tests.md:7` | 第一段 TypeScript 代码块起始已保留 |
| `tests.md:8` | 好例测试可观察行为注释已翻译 |
| `tests.md:9` | 有效购物车结账测试名已翻译，异步结构已保留 |
| `tests.md:10` | createCart 已保留 |
| `tests.md:11` | cart add product 已保留 |
| `tests.md:12` | checkout 和 paymentMethod 已保留 |
| `tests.md:13` | confirmed 状态断言已保留 |
| `tests.md:14` | 测试结束已保留 |
| `tests.md:15` | 第一段代码块结束已保留 |
| `tests.md:17` | 特征引导已保留 |
| `tests.md:19` | 用户或调用方关心行为已保留 |
| `tests.md:20` | 只用公开 API 已保留 |
| `tests.md:21` | 承受内部重构已保留 |
| `tests.md:22` | 描述做什么而非如何做已保留 |
| `tests.md:23` | 每测试一项逻辑断言已保留 |
| `tests.md:25` | 不良测试标题已保留 |
| `tests.md:27` | implementation-detail test 与内部结构耦合已保留 |
| `tests.md:29` | 第二段 TypeScript 代码块起始已保留 |
| `tests.md:30` | 差例测试 implementation 注释已翻译 |
| `tests.md:31` | checkout 调 paymentService 测试名已翻译 |
| `tests.md:32` | jest mock paymentService 已保留 |
| `tests.md:33` | checkout 调用已保留 |
| `tests.md:34` | process 调用参数断言已保留 |
| `tests.md:35` | 测试结束已保留 |
| `tests.md:36` | 第二段代码块结束已保留 |
| `tests.md:38` | 危险信号引导已保留 |
| `tests.md:40` | mock 内部协作者已保留 |
| `tests.md:41` | 测试私有方法已保留 |
| `tests.md:42` | 断言调用次数或顺序已保留 |
| `tests.md:43` | 无行为变化的重构导致测试坏已保留 |
| `tests.md:44` | 测试名描述如何做而非做什么已保留 |
| `tests.md:45` | 经外部手段而非 interface 验证已保留 |
| `tests.md:47` | 第三段 TypeScript 代码块起始已保留 |
| `tests.md:48` | 差例绕过 interface 注释已翻译 |
| `tests.md:49` | createUser 保存数据库测试名已翻译 |
| `tests.md:50` | createUser Alice 已保留 |
| `tests.md:51` | 直接 SQL 查询已保留 |
| `tests.md:52` | row defined 断言已保留 |
| `tests.md:53` | 差例测试结束已保留 |
| `tests.md:55` | 好例经 interface 验证注释已翻译 |
| `tests.md:56` | createUser 可取得测试名已翻译 |
| `tests.md:57` | createUser 返回 user 已保留 |
| `tests.md:58` | getUser user.id 已保留 |
| `tests.md:59` | Alice 名称断言已保留 |
| `tests.md:60` | 好例测试结束已保留 |
| `tests.md:61` | 第三段代码块结束已保留 |
| `tests.md:63` | 同义反复测试、期望值重述 implementation 和按构造必过均已保留 |
| `tests.md:65` | 第四段 TypeScript 代码块起始已保留 |
| `tests.md:66` | 差例相同算法重算期望注释已翻译 |
| `tests.md:67` | calculateTotal 求和测试名已翻译 |
| `tests.md:68` | 两项 price 输入已保留 |
| `tests.md:69` | reduce 重算 expected 已保留 |
| `tests.md:70` | 计算结果等于 expected 断言已保留 |
| `tests.md:71` | 差例测试结束已保留 |
| `tests.md:73` | 好例独立已知字面值注释已翻译 |
| `tests.md:74` | calculateTotal 求和测试名已翻译 |
| `tests.md:75` | 输入和独立 15 断言已保留 |
| `tests.md:76` | 好例测试结束已保留 |
| `tests.md:77` | 第四段代码块结束已保留 |
| `agents/openai.yaml:1` | `interface` 字段已保留 |
| `agents/openai.yaml:2` | `display_name: "TDD"` 已保留 |
| `agents/openai.yaml:3` | 测试驱动 red-green-refactor 已保留 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。四个上游文件的每个非空行，包括全部 TypeScript 示例，都有对应译文和独立检查记录 |
| 增写 | 无。没有加入 MMW plan review、worker、审查、测试命令或人工审批接线 |
| 曲解 | 无。测试 seam 必须预先与用户商定、每轮一垂直切片、重构不属于 red-green 循环三项保持原样 |
| 术语漂移 | 无。TDD、red、green、seam、interface、implementation、重构、垂直切片和 tracer bullet 使用一致 |
