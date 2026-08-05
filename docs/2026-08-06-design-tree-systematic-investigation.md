# Design Tree 系统调查

## 结论

Matt Pocock 上游的设计树（design tree）是一场 grilling 会话内部使用的决定依赖模型。每个节点是一项由用户作出的决定。节点之间的关系表示后续决定依赖哪些前置决定。Agent 根据已解决的前置条件，判断现在可以诚实提出哪些问题。

设计树不是领域模型、ADR、实施 ticket 或 Wayfinder map。上游没有把它保存为文件，也没有提供建图算法。它是一套要求 Agent 在问答过程中持续维护的认知模型。

设计树、frontier 和 round 共同构成当前上游的默认提问方法。设计树负责保持决定依赖和分支完整性。每轮默认提出整个 frontier。官方文档允许用户通过全局指令覆盖为“一次一个问题”，但这项偏好不构成另一套方法，也不改变 MMW 应当继承的默认行为。

MMW 当前没有完整引入设计树。`mmw-grilling` 只保留了“沿着决定之间的依赖关系逐支推进”。它没有规定整轮 frontier、事实调查对依赖分支的阻塞、答案后的 frontier 重算、依赖误判后的分支重开、遍历完成和最终共同理解确认。上游没有定义正式节点状态，MMW 也不应自行补一套状态机。

## 上游副本状态

本次调查先按仓库合同更新了 `vendor/mattpocock-skills/`。Git subtree 先从上游提交 `2ab958093e83e0ec752e6c1c5932da465bf23e0c` 更新到 `0986ebaf5d29e812162702b2633a2942c30200d2`，定稿前再更新到 `8b36d4fb2635b3c21998dcd8144439c9e5ba7302`。最终仓库合并提交是 `0126774715560481b09e5459293708607e2e5260`。

设计树随上游 1.2.0 发布。当前上游版本是 1.2.2；1.2.1 和 1.2.2 没有继续修改 grilling 方法。[1.2.0 发布记录](https://github.com/mattpocock/skills/releases/tag/v1.2.0)

## 设计树的模型

### 核心对象

| 对象 | 上游含义 | 谁负责 |
| --- | --- | --- |
| 决定节点 | 用户必须选择或确认的一项设计决定 | 用户回答，Agent 不得代答 |
| 依赖关系 | 一个决定只有在另一个决定解决后才能提出 | Agent 判断和维护 |
| 事实调查 | 文件、代码或环境可以回答的问题 | Agent 或调查 subagent |
| frontier | 所有前置条件已经解决的决定集合 | Agent 根据当前理解判断 |
| round | 一次向用户提出的整个 frontier | Agent 提问，用户回答 |
| 共同理解确认 | 所有分支访问完后，用户确认理解一致 | 用户作最终确认 |

上游技能用一句话定义设计树：“每个决定分支出依赖它的决定。”随后用 frontier 约束可提问的节点（`vendor/mattpocock-skills/skills/productivity/grilling/SKILL.md:6-8`）。

### 状态变化

| 事件 | 状态变化 | 后续动作 |
| --- | --- | --- |
| 用户回答一个决定 | 该决定解决；答案可能产生新分支，也可能改变已有分支 | 重算可提问的决定 |
| 一个决定仍依赖本轮未回答的问题 | 该决定继续等待 | 放到后续轮次 |
| 一个分支需要环境事实 | 调查结果成为该分支未解决的前置条件 | 派 subagent；继续询问其他可提问分支 |
| 后续答案暴露本轮问题其实相互依赖 | 受影响分支重新打开 | 下一轮重新询问 |
| 没有可提问或待调查的分支 | 设计树遍历完成 | 请求用户确认共同理解 |
| 用户没有确认共同理解 | 会话仍未完成 | 继续澄清，不得开始实施 |

当前上游要求每轮答案都重塑设计树，并重新计算 frontier。它还要求事实调查只阻塞依赖该事实的分支（`vendor/mattpocock-skills/skills/productivity/grilling/SKILL.md:18-22`）。

### 完成判据

上游把完成拆成两关：

1. frontier 为空，全部分支已经访问，没有静默假设。
2. 用户确认双方已经形成共同理解。

第一关检查设计覆盖面。第二关保留用户的决定权。Agent 不得在第一关之后直接开始写代码（`vendor/mattpocock-skills/skills/productivity/grilling/SKILL.md:22`）。

## 上游没有定义什么

设计树不是形式化图模型。上游文档明确说明，frontier 来自 Agent 判断，并非程序计算。上游没有定义以下内容：

| 缺失项 | 影响 |
| --- | --- |
| 初始根节点和首批节点的生成算法 | 不同 Agent 可能得到不同的第一轮问题 |
| 节点标识、边类型和持久化格式 | 无法在会话之间可靠恢复同一棵树 |
| 环检测和一致性检查 | 循环依赖只能由 Agent 在对话中识别 |
| 调查结果返回后的正式状态迁移 | Agent 需要自行判断哪些分支被解锁 |
| 用户拒绝最终确认后的固定流程 | Agent 只能继续找出理解差异 |
| 同轮问题误判依赖的自动保护 | 用户需要指出问题，Agent 再重开分支 |

上游把同轮依赖误判列为已知限制。官方说明没有宣称已经消除这个问题（`vendor/mattpocock-skills/docs/productivity/grilling.md:31`）。

## 与其他上游技能的关系

| 技能 | 负责内容 | 是否保存设计树 |
| --- | --- | --- |
| `grilling` | 设计树、决定依赖、frontier、事实与决定的分工、完成确认 | 否 |
| `grill-me` | 给用户提供纯 grilling 入口 | 否 |
| `grill-with-docs` | 在 grilling 中同时运行 domain modeling | 否 |
| `domain-modeling` | 维护 glossary；用具体场景压测术语；按高门槛记录 ADR | 否 |
| `research` | 调查并记录带出处的事实 | 否 |
| `triage` | 把模糊 issue 问到可处理，并保存分诊结果 | 否 |
| `wayfinder` | 用 issue tracker 保存跨会话 effort map，并在决定 ticket 内运行 grilling | 否 |
| `to-questionnaire` | 把已知问题写成给他人回答的静态问卷 | 否 |

上游只有 `grilling` 拥有设计树方法。`grill-with-docs` 只写明“运行 grilling，并使用 domain-modeling”（`vendor/mattpocock-skills/skills/engineering/grill-with-docs/SKILL.md:7`）。`domain-modeling` 保存问答产生的长期领域结论，不保存问题依赖结构。

Wayfinder 解决另一种尺度的问题。它把大 effort 的决定拆成持久 issue，并在每张决定 ticket 内运行 grilling。设计树服务单次会话。Wayfinder map 服务多个会话和多个工作分支。两者可以嵌套，不能互相替代。

## 设计树与按轮提问的关系

上游 1.2.0 把 grilling 从“一次一个问题”改为“一次询问整个 frontier”。该变更的目标是减少交互轮次，同时保留决定依赖。官方 PR 以约十三个问题压缩到约三轮为例。[上游 PR #593](https://github.com/mattpocock/skills/pull/593)

社区随后提出两类反馈：批量问题增加阅读和回答负担；设计树与 frontier 仍有价值。相关讨论建议保留设计树，同时恢复逐题交互。[上游 issue #663](https://github.com/mattpocock/skills/issues/663)

当前官方文档确认逐题交互是正式支持的偏好。用户可以在全局规则中要求 grilling 一次只问一个问题。文档仍保留设计树、依赖判断和分支重算（`vendor/mattpocock-skills/docs/productivity/grilling.md:45-55`）。

因此，设计树规定“哪些问题现在有资格提出”。交互偏好规定“每次实际提出几个合格问题”。这两个选择应当分别评估。

## MMW 当前状态

### 已经存在的相关行为

`mmw-grilling` 已经要求 Agent：

- 区分事实和决定。
- 一次问一个问题。
- 沿决定依赖逐支推进。
- 优先解决其他决定等待的前置决定。
- 为每个问题给出推荐答案。
- 在能动手之前不实施。

这些规则覆盖了设计树的一部分意图（`mmw/skills/mmw-grilling/SKILL.md:8-33`）。

### 没有引入的行为

| 上游设计树行为 | MMW 状态 | 后果 |
| --- | --- | --- |
| 明确维护全部决定分支 | 未定义 | Agent 容易只跟随当前对话分支 |
| 判断当前可提问节点集合 | 未定义 | 只规定前置决定优先，没有可检查的当前状态 |
| 用户答案后重算分支 | 未定义 | 新答案是否影响旧问题取决于 Agent 临场判断 |
| 调查只阻塞下游分支 | 部分存在 | MMW 开问前集中调查，问答中的零散事实由主 Agent 查；没有并行分支状态 |
| 误判依赖后重开分支 | 未定义 | 已问过的问题可能静默失效 |
| 遍历全部分支且没有静默假设 | 未定义 | 当前主要用 spec 模板是否可填写作为完成标准 |
| 用户确认共同理解 | 未定义为最终关卡 | “能动手”可能由 Agent 单方面判断 |

### MMW 中的两种 frontier

MMW 已经把 `frontier` 定义为 issue tracker 中 open、无阻塞、无人认领的子 issue。`mmw issue frontier` 可以实际查询这个持久状态（`mmw/skills/mmw-wayfinder/map-anatomy.md:87-91`）。

| 对比项 | grilling 的 frontier | MMW tracker 的 frontier |
| --- | --- | --- |
| 元素 | 用户决定 | issue tracker 中的 ticket |
| 前置条件 | 相关决定和事实已经解决 | 所有阻塞 ticket 已关闭 |
| 状态保存 | Agent 会话上下文 | issue tracker |
| 计算方式 | Agent 判断 | CLI 查询远端结构 |
| 生命周期 | 一场 grilling | 多任务、多分支、跨会话 |

两者共享“当前可推进的边缘”这一抽象，但运行合同不同。上游本身同时使用这两个尺度的 frontier，没有为它们改名。MMW 只需在各自技能的上下文中写清元素和生命周期，不应另造“设计树 frontier”或“ticket frontier”等正式术语。

## 对 MMW 的准确判断

MMW 已经吸收了设计树的一个局部原则：按决定依赖逐支推进。它没有吸收设计树作为完整 grilling 状态模型，也没有吸收上游的完成判据。

MMW 应恢复上游默认的整轮 frontier 提问，同时补齐分支发现、答案后的重算、分支重开和共同理解确认。用户明确要求逐题时，普通的用户指令可以覆盖每轮展示数量；设计树和 frontier 方法仍保持不变。

设计树也不改变 grilling 与 domain modeling 的职责。grilling 管问题和决定之间的依赖。domain modeling 管已经形成的领域术语、关系和长期架构决定。两项技能一起运行时，domain modeling 消费设计树产生的结论，但不拥有或保存设计树。

## 证据边界

本报告把官方技能正文、官方文档、合入 PR 和发布记录作为行为依据。PR 与 issue 中的个人体验只作为使用反馈，没有当成已确认缺陷。

当前上游没有更完整的设计树规格、持久化格式或实现代码。报告中关于“认知模型”和“会话内状态”的表述，是根据官方明确声明“不计算图”以及仓库中不存在持久化合同得出的解释。
