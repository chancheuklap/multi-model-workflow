# Grilling 与 Domain Modeling 上游对照调查

## 结论

MMW 已经在 `mmw-grilling` 中明确要求同时使用 `mmw-domain-modeling`。当前源码和 Codex 已安装的 0.9.0 产物都有这条要求。问题出在反方向：`mmw-domain-modeling` 可以被 Agent 单独路由，但它没有判断当前请求是否其实需要 grilling，也没有移交回 `mmw-grilling`。

Matt Pocock 上游使用三层结构：

1. `grilling` 只拥有提问方法。
2. `domain-modeling` 只拥有领域术语、场景压测、glossary 和 ADR 的维护方法。
3. `grill-with-docs` 是显式入口。它要求在一场 grilling 中使用 domain modeling。

上游的 `domain-modeling` 仍可独立运行。它也没有反向调用 grilling。上游主要靠 `grill-with-docs` 和路由说明区分“追问整个计划”与“只解决术语或 ADR”。因此，“每次调用 domain modeling 都必须同时运行 grilling”并不是上游模式。MMW 删除了这个 wrapper，把它吸收进 `mmw-grilling`。这个简化保留了正常入口的组合关系，却没有封住 Agent 直接误入 `mmw-domain-modeling` 的路径。

MMW 对 `domain-modeling` 的主体方法保留得较完整。领域文档位置、Map、ADR 编号和并行分支规则属于有仓库证据的工作流适配。当前存在六项会改变行为的偏差，其中四项是高优先级问题。

## 调查范围

| 证据 | 版本 |
| --- | --- |
| MMW 源码 | 当前 worktree |
| Codex 已安装技能 | `mmw-codex` 0.9.0 |
| 仓库内 Matt Pocock 副本 | 上游提交 `0986ebaf5d29e812162702b2633a2942c30200d2`，2026-08-06 更新 |
| Matt Pocock 当前上游 | `0986ebaf5d29e812162702b2633a2942c30200d2`，2026-08-05 核对 |

本调查最初以仓库原有的 `2ab958093e83e0ec752e6c1c5932da465bf23e0c` 副本为基线。仓库随后通过 Git subtree 更新到 `0986ebaf5d29e812162702b2633a2942c30200d2`。`grill-with-docs`、`domain-modeling` 和问题上限规则没有变化。`grilling` 的提问协议发生了变化。[上游比较](https://github.com/mattpocock/skills/compare/2ab958093e83e0ec752e6c1c5932da465bf23e0c...0986ebaf5d29e812162702b2633a2942c30200d2)

## 上游如何搭配两个技能

### 三层职责

| 层 | 职责 | 入口性质 |
| --- | --- | --- |
| `grilling` | 建立设计树，解决决定之间的依赖，向用户提决定，自己调查事实 | Agent 或用户都可调用 |
| `domain-modeling` | 挑战含糊术语，用边界场景压测，检查代码与用户说法，随谈随写 glossary，按高门槛写 ADR | Agent 或用户都可调用 |
| `grill-with-docs` | 运行 grilling，并在同一场会话中应用 domain modeling | 只允许用户显式调用 |

wrapper 的完整指令只有一句：“运行 `/grilling`，使用 `/domain-modeling`”。它没有要求启动两个独立 Agent，也没有规定先后顺序。它表达的是同一场设计会话中的方法组合（上游 `skills/engineering/grill-with-docs/SKILL.md:2-7`；[当前上游文件](https://github.com/mattpocock/skills/blob/0986ebaf5d29e812162702b2633a2942c30200d2/skills/engineering/grill-with-docs/SKILL.md)）。

上游说明把两者的边界写得很清楚：计划本身需要被追问时使用 grilling；词语、术语或架构决定本身有问题时可以单独使用 domain modeling。`grill-with-docs` 负责让一次有代码库的 grilling 留下 glossary 和 ADR 记录（上游 `docs/engineering/grill-with-docs.md:13-33`、`docs/engineering/domain-modeling.md:19-42`）。

### 当前上游的 grilling 已经更新

更新前的仓库副本要求“一次只问一个问题”。当前仓库副本改为按设计树的 frontier 分轮提问：同一轮可以问多个前置条件已经解决的问题；仍未解决依赖的问题留到下一轮。需要查环境事实时派 subagent，只暂停依赖该事实的分支。结束条件是 frontier 为空，并由用户确认已经形成共同理解（`vendor/mattpocock-skills/skills/productivity/grilling/SKILL.md:6-22`；[当前上游 grilling](https://github.com/mattpocock/skills/blob/0986ebaf5d29e812162702b2633a2942c30200d2/skills/productivity/grilling/SKILL.md)）。

这项变化没有改变两个技能的组合方式。它改变了 grilling 的执行协议。

### 上游明确拒绝问题数量上限

当前上游明确规定 grilling 不设最大问题数。固定上限会提前截断复杂问题，也无法区分“问题确实未定”与“Agent 在重复提低价值问题”。用户可以随时要求停止或收尾（上游 `.out-of-scope/question-limits.md:1-14`；[当前上游文件](https://github.com/mattpocock/skills/blob/0986ebaf5d29e812162702b2633a2942c30200d2/.out-of-scope/question-limits.md)）。

## MMW 当前如何搭配

MMW 在 2026-08-02 删除了 `grill-with-docs`，因为它的正文只有一条组合指令。提交 `47e799df` 把 wrapper 的行为吸收进 grilling，并把新需求入口从 wrapper 改到 `mmw-grilling`。

当前 `mmw-start` 把新需求和已有需求的改进路由到 `mmw-grilling`（`mmw/skills/mmw-start/SKILL.md:29-38`）。当前 `mmw-grilling` 明确规定两项技能默认成对运行，并要求开问时立即调用 `mmw-domain-modeling`（`mmw/skills/mmw-grilling/SKILL.md:35-39`）。Codex 已安装的 0.9.0 产物含有同一条要求。

因此，“MMW 完全没有告诉 Agent 两项技能要一起使用”与当前文件不符。准确问题如下：

- 正常从 `mmw-start` 或 `mmw-grilling` 进入时，组合关系已经写明。
- Agent 直接路由到 `mmw-domain-modeling` 时，没有任何反向判断或移交规则。
- `mmw-start` 与 `mmw-domain-modeling` 的 description 会在“新需求涉及领域术语或 ADR”时同时匹配。当前合同没有消除这条重叠路由。

## 完整度判断

### 已保留的上游方法

| 方法 | MMW 状态 | 出处 |
| --- | --- | --- |
| 挑战 glossary 中的冲突用词 | 保留 | `mmw/skills/mmw-domain-modeling/SKILL.md:68-70` |
| 收紧含糊或重载词 | 保留 | `mmw/skills/mmw-domain-modeling/SKILL.md:72-74` |
| 用具体边界场景压测领域关系 | 保留 | `mmw/skills/mmw-domain-modeling/SKILL.md:76-78` |
| 对照代码与用户说法 | 保留 | `mmw/skills/mmw-domain-modeling/SKILL.md:80-82` |
| 术语定下后立即更新 glossary | 保留，但受 `none` 规则限制 | `mmw/skills/mmw-domain-modeling/SKILL.md:84-88` |
| glossary 不含实现细节 | 保留 | `mmw/skills/mmw-domain-modeling/SKILL.md:86-88` |
| ADR 必须同时满足三个条件 | 保留 | `mmw/skills/mmw-domain-modeling/SKILL.md:90-98` |

### 有正式依据的 MMW 定制

| 定制 | 判断 | 依据 |
| --- | --- | --- |
| 领域文档位置不写死 | 合理适配 | `mmw domain path`、`mmw domain dirs` 和 `.mmw.json` 共同定义落点 |
| 多 bounded context 使用 Map 与命名 leaf | 合理适配 | `mmw domain map-init`、`mmw domain check` 及受管 Map 规则 |
| 并行 Wayfinder 分支先写 ADR 草稿名 | 合理适配 | 避免多个分支同时分配正式 ADR 编号 |
| 开问前用 `mmw-research` 查现状 | 合理扩展 | 把上游“事实由 Agent 调查”接到 MMW 的可验证调查流程 |
| 决定需要实物或真实运行证据时转 `mmw-prototype` | 合理扩展 | MMW 为原型和真实环境取证定义了独立完成判据 |
| 谈定后进入 `mmw-to-spec` | 合理适配 | 把共同理解接到 MMW 的 spec、审查和人工审批关卡 |

### 已确认的偏差和不一致

| 优先级 | 问题 | 判断 |
| --- | --- | --- |
| 高 | `mmw-domain-modeling` 单独误触发后不会回到 grilling | wrapper 删除后留下的路由缺口。上游也不要求 domain modeling 反向调用 grilling，但上游保留显式 `grill-with-docs` 入口和清晰路由说明；MMW 的自动入口重叠更容易暴露这个问题。 |
| 高 | MMW 仍要求一次只问一个问题 | 相对 2026-08-05 当前上游已经落后。当前上游按 frontier 分轮提问，并允许不相互依赖的问题在同一轮出现。 |
| 高 | MMW 固定 15 轮上限 | 这不是普通工作流定制。它直接违背上游明确的 out-of-scope 决定。仓库中没有独立的长期合同证明 MMW 必须固定为 15 轮。 |
| 高 | grilling 对 ADR 的摘要只保留“难以回退” | `mmw-grilling` 说难以回退的决定定下就写 ADR（`mmw/skills/mmw-grilling/SKILL.md:37-39`）；`mmw-domain-modeling` 要求三个条件同时成立（`mmw/skills/mmw-domain-modeling/SKILL.md:90-98`）。前者会让 Agent 过量写 ADR。 |
| 中 | `none` 形态下的文档写入合同没有闭合 | `mmw-grilling` 要求术语定下就写 leaf；`mmw-domain-modeling` 又规定被其他技能顺带调用时不创建领域文档（`mmw/skills/mmw-domain-modeling/SKILL.md:23-30`）。没有 leaf 时，Agent 无法同时满足两条指令。上游 `grill-with-docs` 则明确保证首个术语定下时按需创建 glossary。 |
| 中 | 完成判据从“全部分支解决并由用户确认”改成“spec 模板各节能回答” | 有 MMW 下游流程依据，但语义不完全相同。模板可填写不证明没有静默假设。当前上游用 frontier 为空检查整棵设计树，并保留用户确认。 |

## 最终判断

MMW 不是漏掉了两个技能的组合关系。MMW 把上游 wrapper 的组合关系放进了 `mmw-grilling`，而且写得比旧上游更明确。真正的问题是组合关系只有单向入口，无法纠正 `mmw-domain-modeling` 的误路由。

`domain-modeling` 的核心方法没有被大幅删减。主要风险来自 wrapper 被吸收后的边界处理，以及后来加入的局部摘要和限制。15 轮上限、ADR 单条件摘要、`none` 形态写入冲突都不是上游方法的忠实延伸。当前上游新增的 frontier 分轮协议也尚未进入 MMW。
