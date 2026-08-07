# `ask-matt` 1.2.2 中文翻译基线

## `SKILL.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/ask-matt/SKILL.md:1-5 -->

```yaml
---
name: ask-matt
description: 询问哪项技能或哪条流程适合你的情形。这是本仓库各项技能的路由器。
disable-model-invocation: true
---
```

<!-- source: vendor/mattpocock-skills/skills/engineering/ask-matt/SKILL.md:7-15 -->

# Ask Matt

你不会记住每项技能，所以直接询问。

**流程**是一条穿过各项技能的路径。多数路径沿一条**主流程**前进，两条 **on-ramp** 会并入主流程。其余内容要么独立运行，要么作为底层词汇层运行。

## 主流程：想法 → 交付

多数工作会经过这条路线。你有一个想法，并希望把它构建出来。

<!-- source: vendor/mattpocock-skills/skills/engineering/ask-matt/SKILL.md:17-26 -->

1. **`/grill-with-docs`**——通过访谈使想法更加明确。只要你**正在工作目录中工作**，就从这里开始。它有状态，会把学到的内容保留在 `CONTEXT.md` 和 ADR 中。（没有工作目录？使用 `/grill-me`，参见“独立技能”。二者运行相同的 `/grilling` 原语；只要有仓库可以留下记录，`grill-with-docs` 就是两者中能够留下书面记录的那个，因此也是更好的选择。）
2. **分支——能否在对话中解决每一个问题？** 如果某个问题需要通过可运行内容来回答，例如状态、业务逻辑或必须亲眼查看的 UI，就绕道 prototype，并在两个方向上都使用 **`/handoff`** 衔接。prototype 位于自己的目录中，这正是 `/handoff` 的用途，参见“阶段边界”：
   - 使用 **`/handoff`** 移交出去，然后基于该文件开启一个全新 session；
   - 使用 **`/prototype`**，通过一次性代码回答问题；
   - 使用 **`/handoff`** 把学到的内容移交回来，并从原始想法所在的对话中引用它。
3. **分支——这是一项跨多个 session 的构建吗？**
   - **是** → 使用 **`/to-spec`** 把当前对话转成 spec，然后使用 **`/to-tickets`** 把它拆成 tracer bullet ticket；每张 ticket 都声明自己的 **blocking edge**。使用本地 tracker 时，每张 ticket 对应 `.scratch/<feature>/issues/` 下的一个文件，由人工按照 blocker 优先的顺序处理。使用真实 tracker 时，edge 变成原生 blocking link，因此 blocker 已完成的任何 ticket 都可以被认领。为每张 ticket 分别启动 **`/implement`**，并且**每完成一张就使用 `/clear` 清空上下文**。每张 ticket 都是自包含的，因此上一张 ticket 的上下文可以丢弃。
   - **否** → 就在这里、同一个上下文窗口中使用 **`/implement`**。

   无论哪种情况，**`/implement`** 都会在内部驱动 **`/tdd`** 来构建每个 issue，一次完成一个 red-green 切片；随后在提交前运行 **`/code-review`** 来收尾，对 diff 进行双轴审查，也就是 Standards 与 Spec。只想以测试优先方式构建一项具体行为、不需要完整 spec 时，单独使用 **`/tdd`**。想要相对于一个基准点审查分支或 PR 时，单独使用 **`/code-review`**。

<!-- source: vendor/mattpocock-skills/skills/engineering/ask-matt/SKILL.md:28-32 -->

### 上下文管理

让第 1 至第 3 步处于**同一个不间断的上下文窗口**中。在 `/to-tickets` 之后再 compact 或 clear，使 grilling、spec 和 ticket 都建立在同一套思考之上。随后，每次 `/implement` 都从全新上下文开始，并以 ticket 为依据工作。

这项规则的限制是 **[smart zone](https://www.aihero.dev/ai-coding-dictionary/smart-zone)**：模型仍然能够敏锐推理的窗口范围；在先进模型上大约为 15 万 token。如果 session 在 `/to-tickets` 之前已经接近这个范围，不要在能力退化后继续推进。应在最近的阶段边界使用 `/compact`，然后继续，参见“阶段边界”。

<!-- source: vendor/mattpocock-skills/skills/engineering/ask-matt/SKILL.md:34-46 -->

## On-ramps

一种会产生工作、随后并入主流程的起始情形。

- **Bug 和请求不断堆积** → 使用 **`/triage`**。它让 issue 依次经过 triage 角色，并产出 agent-ready issue，随后由 **`/implement`** 认领。

  Triage 只用于**并非由你创建**的 issue，例如 bug 报告、传入的功能请求，以及任何未经处理就到来的内容。`/to-tickets` 产生的 ticket 已经是 agent-ready，因此**不要 triage 它们**。

- **某项内容损坏了** → 使用 **`/diagnosing-bugs`**。它用于困难问题，例如第一眼无法解决的 bug、间歇性 flake，或在两个已知良好状态之间悄然引入的回归。它在取得一个 **tight 反馈循环**之前拒绝提出理论；这个反馈循环是一条已经会因为**当前** bug 变成 red 的命令。随后，它用回归测试完成修复。如果事后分析发现真正的问题是缺少能够锁定该 bug 的合适 seam，就移交给 **`/improve-codebase-architecture`**。

- **一项巨大且模糊的工作，例如全新项目或大型功能构建；它太大，无法放进一个 session** → 使用 **`/wayfinder`**，这是这里认知负担最高的流程。如果从当前位置到目的地的道路尚不可见，它会在 issue tracker 上绘制由 **decision ticket** 组成的**共享 map**，然后逐张解决；它产出的是**决定，不是交付物**，直到迷雾退去、道路变得清晰。**`/grill-with-docs`** 用来明确能够放进一个 session 的想法，wayfinder 则用于一个 session 无法容纳的想法。wayfinder 更慢、信息密度也更高，因此只在这种情形下使用，绝不用于范围明确的功能。

  map 清晰后，**它会移交，不会构建**。在 **`/to-spec`** 处并入主流程；`/to-spec` 会把 map 中彼此关联的决定归并成一份可构建的计划，随后照常使用 `/to-tickets` 和 `/implement`。从 map 直接循环进入 `/implement` 会跳过这次归并，并丢掉相互关联的细节。只有当这项工作后来证明确实很小时，才直接进入 `/implement`。

<!-- source: vendor/mattpocock-skills/skills/engineering/ask-matt/SKILL.md:48-59 -->

## 代码库健康

这不属于功能工作，而属于维护。

- **`/improve-codebase-architecture`**——只要有空闲时间就运行它，使代码库继续适合 agent 操作。它会找出 **deepening opportunity**；选择其中一项会**产生一个想法**，你可以在 `/grill-with-docs` 处把它带入主流程。它是一项找出候选项的勘察；下方的 **`/codebase-design`** 是设计选中候选项的工作台。

## 底层词汇

两份由模型调用、运行在其他技能**底层**的 reference；每份 reference 都是自身词汇的唯一事实来源。当问题在于**用词**而非流程时，直接使用它们；也可以让上方技能自行引入它们。

- **`/domain-modeling`**——使项目的**领域**语言更加明确：质疑一个含混的术语、解决一个承担多种含义的词，例如用 `account` 表示三种事物，或把难以逆转的决定记录为 ADR。这是 `/grill-with-docs` 主动推动的实践，用于使 `CONTEXT.md` 保持为干净的术语表。
- **`/codebase-design`**——用于设计 module **形状**的 deep module 词汇，包括 module、interface、depth、seam、adapter、leverage 和 locality：在干净的 seam 上，用较小的 interface 承载大量行为。`/tdd` 和 `/improve-codebase-architecture` 都使用这套词汇。

<!-- source: vendor/mattpocock-skills/skills/engineering/ask-matt/SKILL.md:61-71 -->

## 阶段边界

**阶段**是 session 内的一段工作，例如 grilling、实施或 QA。在两个阶段之间的**边界**上，你有五种选项；在它们之间作选择，是整张 map 中最模糊的决定：

- **继续**——留在原处。没有成本，也没有损失。
- **`/clear`**——当这里的内容对下一步毫无影响时，清空窗口。
- **`/handoff`**——编写一个可移植的 Markdown 文件。它的范围很窄：只用于**新的 harness**、**新的目录**、**同事**，或在**阶段中途**分出一项旁支任务。它带来的价值是可移植性。
- **Subagent**——把一项范围严密的 task 发送到自己的窗口，并取回报告。
- **`/compact`**——压缩当前上下文，并用压缩结果为一个全新 session 提供初始内容。它是位于决策树底部的**默认选项**，不是最先考虑的选项。

阅读 [PHASE-BOUNDARIES.md](PHASE-BOUNDARIES.md)，查看有序决策树、五个问题、每个分支背后的理由，以及一手来源成本为何要求先判断**能否继续**。只有不能继续时，才考虑其他选项。在边界上作出决定。阶段中途要么继续，要么把余下工作拆给 subagent。

<!-- source: vendor/mattpocock-skills/skills/engineering/ask-matt/SKILL.md:73-90 -->

## 独立技能

完全位于主流程之外。

- **`/grill-me`**——与 `/grill-with-docs` 相同的 **relentless 访谈**，但它**没有状态**：不在本地保存任何内容，也不构建 `CONTEXT.md`。当你**没有在工作目录中工作**时使用，例如明确一份计划、一项设计、一段文字，或任何底下没有仓库的内容。如果你位于工作目录中，改用 `/grill-with-docs`；它运行相同的访谈并留下书面记录，因此严格来说是更好的选择。
- **`/grilling`**——访谈原语本身：多轮访谈、frontier、事实由 agent 负责，决定由你负责。`/grill-me` 和 `/grill-with-docs` 是两个具名入口；`/triage`、`/wayfinder` 和 `/improve-codebase-architecture` 都在内部运行它。只有当你想要不带任何包装的访谈时，才直接使用它。
- **`/resolving-merge-conflicts`**——逐个 conflict hunk 处理进行中的 merge 或 rebase。它依据追溯到双方一手来源的**意图**解决冲突，不是选择某些代码行；随后完成当前操作。它绝不运行 `--abort`。该技能独立运行，位于所有流程之外；当你已经处于冲突中时使用。
- **`/prototype`**——用一个小型一次性程序回答一个设计问题，例如这个状态模型感觉是否正确，或这个 UI 应该是什么样子。一次性是对代码编写方式的约束，不是销毁代码的承诺。答案会融入真实代码，prototype 本身则作为**一手来源**保留在从 `main` 分出的 `prototype/<name>` 分支上，并由实施 issue 指向它。它是主流程第 2 步中的绕行路径；任何设计问题难以在文字中确定时，也可以使用它。
- **`/research`**——把阅读工作委托给一个**后台 agent**：它根据**一手来源**调查一个问题，随后在仓库中留下带引用的 Markdown 文件。它阅读时，你可以继续工作。它产生的文件应在 `/grill-with-docs` 处被带入主流程。research 为思考提供材料，不取代思考。
- **`/to-questionnaire`**——当阻挡你的内容不在你的脑中或代码库中，而在**另一个人的脑中**时，它会编写一份问卷供对方填写。它是 `/grill-me` 的反向形式：它不会就主题采访你，而会就**发送行为**采访你，包括要发给谁、需要对方返回什么；然后把问题对准信息缺口。返回的内容可作为 `/grill-with-docs` 或 `/to-spec` 的材料。
- **`/wizard`**——用于只有**人类**才能执行的步骤，例如配置基础设施、设置凭证或 CI secret、在不熟悉的第三方 dashboard 中完成点击操作，或运行一次性 migration 或 cutover。它会生成一份交互式 Bash 脚本，打开每个 URL、捕获每个值，并把值写入 `.env` 和 GitHub secret。这样，该流程就不再需要你每次都向 agent 重新解释。它由模型调用，因此 agent 一遇到只有你能越过的障碍就会使用它。如果 agent 自己能够执行，就应该自己执行；本技能只用于确实需要人类参与的地方。
- **`/wait-what`**——用于纠正一条没有被理解的消息。在对话中途、任何其他技能内部使用它，agent 会补上你缺少的上下文，用直白语言和 `CONTEXT.md` 中的词汇重新说明刚才的内容。它在问题发生后起作用；`/grill-with-docs` 是事前预防方式，因为尽早商定的共享语言能够从一开始就阻止术语障碍出现。
- **`/teach`**——使用当前目录作为有状态工作区，跨多个 session 学习一个概念。
- **`/writing-for-agents`**——用于编写 agent 消费文档的 reference，包括技能、`AGENTS.md` 和它们指向的文档。

## 前置条件

**`/setup-matt-pocock-skills`**——在第一次运行工程流程前使用它，配置其他技能所假定的 issue tracker、triage 标签和文档布局。自定义 issue tracker 也可以使用。

## `PHASE-BOUNDARIES.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/ask-matt/PHASE-BOUNDARIES.md:1-5 -->

# 阶段边界

**阶段**是 session 内的一段工作，例如 grilling、实施或 QA。这个定义有意保持模糊：当你认为“好，这部分完成了”时，一个阶段就结束了。

**阶段边界**是两个阶段之间的间隙，也是唯一应该作出这项决定的位置。在阶段中途，无需作决定；继续工作，或者把剩余工作拆给 subagent。在阶段中途 compact 会让 agent 丢失思路。

<!-- source: vendor/mattpocock-skills/skills/engineering/ask-matt/PHASE-BOUNDARIES.md:7-15 -->

## 五种选项

| 选项 | 作用 |
| --- | --- |
| **继续** | 留在当前 session，完全不切换上下文。 |
| **`/clear`** | 清空上下文窗口，从零开始。 |
| **`/handoff`** | 编写一个可移植的 Markdown 文件，并在任意位置用它初始化一个 session。 |
| **Subagent** | 把 task 发送到自己的上下文窗口，并取回报告。 |
| **`/compact`** | 压缩当前上下文，并用摘要初始化一个全新 session。 |

<!-- source: vendor/mattpocock-skills/skills/engineering/ask-matt/PHASE-BOUNDARIES.md:17-25 -->

## 决策树

在边界上从上到下依次判断。第一个“是”就是结果。

**1. 你能在当前 session 中继续吗？** 两种情况会使答案为“是”：下一个阶段需要把当前阶段作为**一手来源**；或者剩余 [smart zone](https://www.aihero.dev/ai-coding-dictionary/smart-zone) 足以容纳下一个阶段，在大约 15 万 token 的范围内。Grilling → 实施是标准的“是”：实施需要逐字取得推理过程，不是推理摘要。继续没有成本，也没有损失，因此先判断能否继续；只有答案为“否”时，才考虑其他选项。

**2. 当前上下文与下一步无关吗？** 当前 session 中的一切，包括探索、决定和走过的弯路，是否都可以丢弃？如果是，使用 **`/clear`**。这是决策树中成本最低的动作：不需要时间，并会归还整个窗口。`/clear` 也不是终止操作，旧 session 仍然可以恢复。

错误选择的成本是单向的。清除**相关**上下文会丢失已构建内容背后的**原因**，无论怎样重新阅读 diff 都无法找回这些原因。

<!-- source: vendor/mattpocock-skills/skills/engineering/ask-matt/PHASE-BOUNDARIES.md:27-40 -->

**3. 你需要移交吗？** `/handoff` 的适用范围很窄。只有处于以下情形时才需要它：

- 切换到**新的 harness**，例如从 Claude 切换到 Codex；
- 移动到**新的目录**或仓库；
- 把工作发送给**同事**；
- 或者在不打断当前工作的前提下，分出一项在**阶段中途**发现的旁支任务。

以上清单就是完整的适用条件。`/handoff` 带来的价值是**可移植性**，也就是一个可以移动的文件。如果没有任何内容需要移动，就不需要它。

**4. 这项 task 能够 AFK 完成吗？** 它的范围是否足够严格，使你离开键盘、无法提供引导时仍能运行？如果是，把它发送给 **subagent**，并让当前 session 保持不变。自动审查是标准案例：agent 阅读 diff 并报告；执行期间不需要你参与。

**5. 否则，使用 `/compact`。** 上下文相关、harness 相同、目录相同，而且你需要继续参与；决策树会落在这里，而且经常落在这里。向它传入一条指令，例如 `/compact we're going to QA this area`，使摘要保留下一个阶段需要的内容。

`/compact` 是**默认选项，不是最先考虑的选项**。它位于底部，因为上方四个问题的成本更低或精度更高。如果一开始就使用它，失败形态是：全新 session 对一项已经被摘要压平的决定形成自信但错误的理解。

<!-- source: vendor/mattpocock-skills/skills/engineering/ask-matt/PHASE-BOUNDARIES.md:42-55 -->

## 一手来源与二手来源

除了**继续**以外，每个动作都会把**一手来源**变成**二手来源**：实际发生的 session 被它的摘要取代。取舍始终具有相同形状：

| 来源 | 信息 | 噪声 | 可用空间 |
| --- | --- | --- | --- |
| 一手来源（继续） | 完整 | 多 | 少 |
| 二手来源（`/compact`、`/handoff`） | 有损 | 少 | 多 |

这就是为什么问题 1 排在最前面。只有当留下的成本高于收益时，才付出有损代价。

## 这些都需要判断

这些问题不是客观问题。每个问题都带有判断，同一个边界在不同日期可能得到两个不同答案。价值在于**依次**提出这些问题，并且在边界上提出，而不是在工作中途提出。

## `agents/openai.yaml`

<!-- source: vendor/mattpocock-skills/skills/engineering/ask-matt/agents/openai.yaml:1-5 -->

```yaml
interface:
  display_name: "Ask Matt"
  short_description: "寻找正确的技能或工作流"
policy:
  allow_implicit_invocation: false
```
