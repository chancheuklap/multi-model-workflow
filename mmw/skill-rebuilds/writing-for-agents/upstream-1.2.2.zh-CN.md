# `writing-for-agents` 1.2.2 中文翻译基线

## `SKILL.md`

<!-- source: vendor/mattpocock-skills/skills/productivity/writing-for-agents/SKILL.md:1-4 -->

```yaml
---
name: writing-for-agents
description: 为 agent 编写文档。创建或编辑技能，或者修改 `AGENTS.md` 或 `CLAUDE.md` 时使用。
---
```

<!-- source: vendor/mattpocock-skills/skills/productivity/writing-for-agents/SKILL.md:6-8 -->

这是编写任何由 agent 使用的文档时所用的参考：技能、`AGENTS.md`、`CLAUDE.md`，或者通过 pointer 访问的文档。它们的封装形式不同，写法没有区别：同一组杠杆让每份文档都变得可预测，使 agent 每次采用相同的**过程**，而不是每次产生相同的输出。

正在编写的文档是技能时，读取 [`SKILL-MECHANICS.md`](SKILL-MECHANICS.md)，了解 frontmatter、invocation 选择和 router skill。

<!-- source: vendor/mattpocock-skills/skills/productivity/writing-for-agents/SKILL.md:10-18 -->

## Context pointer

**context pointer** 是 agent 上下文中保存的一项引用。它为某份不在当前上下文内的材料命名，并编码抵达该材料的条件。技能的 description 是一种 context pointer；`AGENTS.md` 中点名某份文档的一行也是同一种对象。决定 agent 何时抵达材料以及抵达是否稳定的，是 pointer 的**措辞**，不是它指向的目标。必须读取的目标如果藏在措辞薄弱的 pointer 后面，就形成 variance bug：先把措辞磨锋利；只有这样仍不能解决时，才把材料内联。

一个 pointer 完成两项工作：说明这份材料是什么，并列出应该触发访问它的**分支**。分支是文档处理的一种独立情况，因此不同运行会沿不同路径通过文档。始终加载的 pointer 中，每个词都会在每一轮消耗上下文，所以它比正文更需要严格删减：

- **把 leading word 放在最前面。** Pointer 正是在这里发挥触发作用。
- **每个分支只写一个触发条件。** 如果几个同义词只是给同一个分支换名字，那就是把同一分支写了多次；把它们收成一个，只保留真正不同的分支。
- **删除正文已经承载的身份说明。**

<!-- source: vendor/mattpocock-skills/skills/productivity/writing-for-agents/SKILL.md:20-27 -->

## 两种负荷

每增加一份文档或一个 pointer，都会消耗以下两种预算中的一种：

- **上下文负荷（context load）**：始终加载的材料对 agent 上下文窗口造成的成本。`AGENTS.md` 中的一行、技能 description，以及每轮都存在于上下文中的任何内容，无论是否触发，都会消耗 token 和注意力。
- **认知负荷（cognitive load）**：人需要承担的成本，也就是记住有哪些文档，以及何时应该读取哪一份。人就是索引。这项成本不需要降到最低；它是人类自主判断的代价。把它用在需要人类判断的地方，在不需要人类判断的地方消除它。

只能通过 pointer 抵达的材料，用 pointer 自身一行的成本换取了不占用上下文负荷。完全没有 pointer 的材料，则把全部成本放在认知负荷上。

<!-- source: vendor/mattpocock-skills/skills/productivity/writing-for-agents/SKILL.md:29-37 -->

## 信息层级

一份文档由两类内容构成：**步骤**，也就是 agent 按顺序执行的动作；以及**参考内容**，也就是按需查阅的定义、规则和事实。两类内容可以自由组合：全部是步骤，例如 recipe；全部是参考内容，例如审查规则或本技能；也可以同时包含两者。核心决定是每项内容位于**信息层级**的哪一层。这是一架按 agent 需要材料的即时程度排序的梯子：

1. **文件内步骤**：第一层。Agent 按顺序执行的动作。
2. **文件内参考内容**：按需查阅。它经常是一组合理的扁平同级内容，例如一项审查的每条规则都位于同一层；这种安排没有问题，也不是坏味道。
3. **披露式参考内容**：被移到单独文件，通过 context pointer 才能抵达，只在 pointer 触发时加载。它可以是同一目录中的相邻文件，也可以是位于任意位置、任何文档都能指向的外部参考。

向下移动得太少，顶层就会膨胀；移动得太多，又会藏起 agent 真正需要的材料。如何处理这项张力，就是整个决定的核心。

<!-- source: vendor/mattpocock-skills/skills/productivity/writing-for-agents/SKILL.md:39 -->

**渐进式披露（progressive disclosure）**是沿这架梯子向下移动：把内容移出主文件，放到 pointer 后面，使顶层保持清晰。它的主要目的不是节省 token，而是保护信息层级。分支是最清楚的披露判据：每个分支都需要的内容内联；只有部分分支需要的内容放到 pointer 后面。一份文档包含步骤时，本应披露的文件内参考内容会掩埋这些步骤，使 agent 是否注意到步骤近似于碰运气。这会改变行为的稳定性，不只是影响可读性。

<!-- source: vendor/mattpocock-skills/skills/productivity/writing-for-agents/SKILL.md:41 -->

**共置（co-location）**是文件内部与信息层级配套使用的方法。信息层级决定一项内容向下放多远；共置决定它到达相应层级后，与哪些内容放在一起。把一个概念的定义、规则和注意事项放在同一个标题下，不要散落到各处。这样，读取其中一项时就会连同相邻内容一起读到。判据是：文档读起来应该像一份为 agent 编写的说明；按主题分组的材料具有这种形态，散落的材料没有。共置与重复不同：重复把同一个含义写在两个位置；散落则把同一个含义拆碎到多个位置。

<!-- source: vendor/mattpocock-skills/skills/productivity/writing-for-agents/SKILL.md:43 -->

**sprawl** 是这里的失败形态：一份文档单纯地过长，即使每一行仍然有效而且没有重复。过量内容会稀释注意力；每增加一行，就多出一项必须保持相关的内容。解决方法是使用信息层级：把参考内容放到 pointer 后面，并按分支或顺序拆分，使每条路径只携带自己需要的内容。

<!-- source: vendor/mattpocock-skills/skills/productivity/writing-for-agents/SKILL.md:45-52 -->

## 步骤和完成判据

每个步骤都以一个**完成判据**结束，也就是告诉 agent 这项工作已经完成的条件。以下两个属性会让完成判据成为行为杠杆：

- **清晰度**：agent 能否判断完成与未完成？含糊边界，例如“已经形成理解”，会引发**过早完成**：步骤尚未真正完成，agent 的注意力已经滑向“把它结束”。当前完成判据之后仍然可见的步骤，也就是 **post-completion steps**，会形成向前赶的拉力；完成判据的清晰度负责抵抗这股拉力。按以下顺序防守：先把边界磨锋利，这是一项局部且低成本的修正；只有边界确实无法变得清晰，而且你已经观察到赶进度，才通过拆分顺序隐藏后面的步骤。只有跨越真正的上下文边界，例如 handoff 或 subagent 派发，隐藏才有效；内联调用仍让后续步骤留在上下文中，没有清除任何内容。
- **要求力度（demand）**：完成判据要求多少工作。“每个被修改的 model 都已经逐一交代”会迫使 agent 做足工作，“产出一份改动清单”则不会。要求力度会推动 **legwork**，也就是完成工作过程中需要进行的查找和核对。Legwork 隐含在措辞中，不需要单独写成一步，而且不受步骤边界限制：“每条规则均已应用”可以约束一组扁平参考内容，就像“每个步骤均已完成”可以约束一段顺序一样；因此，一份只有参考内容的文档仍然能够带有穷尽性要求。

最强的完成判据既可检查，又要求穷尽。

<!-- source: vendor/mattpocock-skills/skills/productivity/writing-for-agents/SKILL.md:54-59 -->

## 何时拆分

把一份文档拆成两份，会消耗两种负荷中的一种，所以只有切分确实值得时才拆：

- **按顺序拆分**：当一连串步骤中，后面的 post-completion steps 会诱使 agent 草率完成眼前步骤时，拆开这段步骤。让后续步骤暂时不可见，可以促使 agent 为当前任务完成更多 legwork。也要警惕反方向：合并多个顺序，会让每一步都看见后面的步骤，从而引发过早完成。
- **按 invocation 拆分**：这是技能专有的方法，见 [`SKILL-MECHANICS.md`](SKILL-MECHANICS.md)。

<!-- source: vendor/mattpocock-skills/skills/productivity/writing-for-agents/SKILL.md:61-72 -->

## Leading word

**leading word** 是一个已经存在于模型预训练中的紧凑概念，agent 在运行文档时用它思考，例如 _lesson_、_fog of war_、_tracer bullets_。把它作为 token 重复，而不是把定义句子重复，会逐渐形成一项分布式定义，并用最少 token 固定整片行为，因为它会调用模型已经学到的先验。你也可以自创词语并清楚定义，但自造词没有先验可调用；预训练词免费提供的内容，自造词必须花费定义 token 才能补上。因此，优先寻找已有词语。

Leading word 会在两个位置起固定作用。在正文中，它固定**执行**：每次出现这个词，agent 都会调用同一种行为；在扁平参考内容中，它会把注意力集中到需要寻找的某一类对象。在 pointer 中，它固定 **invocation**：当同一个词同时存在于 prompt、文档和代码库中时，agent 会把这组共享语言与对应材料联系起来，从而更稳定地抵达材料。

主动寻找能够用 leading word 重构的地方。一组在三个位置反复写出的三项描述，或者一条用整句含糊指向一个概念的 pointer，都应该收成一个 token：

- “快速、确定、低开销”改成 _tight_，例如一个 _tight_ loop。
- “一个你相信的 loop”改成 _red_。一个含糊关卡会变成二元且可观察的状态：loop 会因这个 bug 变成 _red_，或者不会。

这样会同时得到两项收益：token 更少，agent 也得到一个更锋利的挂钩来组织思考。假定每份文档都带有可以由 leading word 消除的重复表述；主动找出它们。

<!-- source: vendor/mattpocock-skills/skills/productivity/writing-for-agents/SKILL.md:74 -->

**否定表达（negation）**是与这项杠杆相邻的失败形态。使用禁止语引导行为，会把被禁止的行为带入上下文，使它变得**更容易**出现，而不是更少出现。让人“不要想一头大象”，上下文中就只剩下大象；否定词只是一个薄弱修饰语，压不住被强烈激活的概念，所以禁令读到一半会像是在要求执行那件事。应当提示**正面目标**：直接写目标行为，例如“写单行注释”，使被禁止的行为根本不进入表述。只有无法用正面目标表达的硬护栏，才值得保留禁止语；即使如此，也要同时写明正面目标，使注意力落在应该做什么上。

<!-- source: vendor/mattpocock-skills/skills/productivity/writing-for-agents/SKILL.md:76-81 -->

## 删减

- 每个含义都只保留一个**唯一事实来源**，也就是一个权威位置，使行为只需要在一个地方修改。**重复**把同一个含义放在多个位置，会增加维护成本和 token，并把这个含义在信息层级上的显著程度抬到超过其真实级别。它恰好是 leading word 的意外反面：leading word 有意重复一个 token，绝不重复含义。
- **环境**也是一种唯一事实来源，例如 `package.json` script、配置文件、目录结构和 `--help` 输出。重述环境的文档是一份 **cache**，也就是一次查询的副本；只有原查询成本很高时，这份副本才值得占用负荷。只 cache agent 无法通过查看环境找到的内容：没有写下来的约定、选择某个方案的理由，或者配置不会说明的陷阱。把单文件或单命令查询留在环境中；直接查询环境不会像文档副本那样过期。
- 逐行检查**相关性**：这一行是否仍然影响文档所做的工作？一行内容可能因为从未影响任务而失去相关性，例如纯粹说明或本应披露的分支；也可能因为行为或外部世界变化而过期。较短的文档更容易保持相关。没有删减纪律时，默认结果是 **sediment**：因为增加内容让人觉得安全、删除内容让人觉得危险，过期层会不断沉积，直到必须钻过这些沉积才能找到仍然有效的内容。
- 逐句寻找 **no-op**：如果一条指令只是要求模型执行它默认就会执行的行为，这条指令只消耗负荷，不会产生作用。判据是：与模型默认行为相比，这句话是否改变行为？这个判据取决于模型，不取决于读者。两个人对 no-op 有分歧，实际上是在对模型默认行为有分歧；应通过运行文档解决，不应只靠讨论。一个句子如果没有作用，就删除整句，不要只修剪几个词。这个判据也会衡量 leading word：如果某个词弱到无法改变默认行为，例如模型本来就大致会“认真”，那么换一种技巧也没有用；应改用更强的词，例如 _relentless_。

## `SKILL-MECHANICS.md`

<!-- source: vendor/mattpocock-skills/skills/productivity/writing-for-agents/SKILL-MECHANICS.md:1-3 -->

# 技能机制

这是 [`writing-for-agents`](SKILL.md) 中技能专有的分支：文档成为技能时会发生哪些变化，也就是 frontmatter、invocation 选择和 router skill。其他所有写作方法都在 `SKILL.md` 的通用参考中。

<!-- source: vendor/mattpocock-skills/skills/productivity/writing-for-agents/SKILL-MECHANICS.md:5-14 -->

## Invocation

有两个选项，它们在两种负荷之间作出取舍：

- **model-invoked** 技能保留 `description`，因此 agent 可以自行触发它，其他技能也能抵达它。用户仍然可以输入技能名：model invocation 始终**包含**用户主动调用；description 只增加 agent 发现，不会移除用户调用。Description 是技能顶层的 context pointer，被迫始终加载；它用永久的上下文负荷换取可发现性。如果一个 model-invoked 技能的内容全部是参考内容，它也可以成为共享参考内容的单一归属位置：另一个技能能够调用它，因此多个技能需要的参考内容可以只保存一份。机制是省略 `disable-model-invocation`，并编写一条面向模型、包含各触发分支的 description；`SKILL.md` 中的 pointer 写作规则全部适用。
- **user-invoked** 技能会使 description 脱离 agent 的可达范围：只有人输入技能名才能调用它，其他技能不能抵达它。它不产生上下文负荷，但会产生认知负荷，因为人必须作为索引记得它存在。机制是设置 `disable-model-invocation: true`；description 改为面向人，只保留单行概要，删除触发条件清单。

只有 agent 必须自行抵达某个技能，或者另一个技能必须抵达它时，才选择 model invocation。如果技能只会被人手动调用，就把它设为 user-invoked，使它不产生上下文负荷。

两个 user-invoked 技能共同需要的参考内容不能放在其中任意一个技能里：两者都没有可供模型发现的 description，因此除了人以外，任何对象都无法让一个技能抵达另一个。把共享内容移到技能系统之外的普通文件，使任何技能都能通过外部 reference 指向它。

<!-- source: vendor/mattpocock-skills/skills/productivity/writing-for-agents/SKILL-MECHANICS.md:16-18 -->

## 按 invocation 拆分

这是拆分方法中的 invocation 分支；按顺序拆分的方法位于 `SKILL.md`。出现一个应该自行触发技能的独立 leading word，而且这个触发词确实会出现在 prompt 中，或者另一个技能必须抵达它时，把它拆成独立的 model-invoked 技能。新增的始终加载 description 会产生上下文负荷，所以只有确实需要独立抵达时，这项成本才值得。

<!-- source: vendor/mattpocock-skills/skills/productivity/writing-for-agents/SKILL-MECHANICS.md:20-22 -->

## Router skill

user-invoked 技能多到人无法记住时，累积的认知负荷由 **router skill** 解决：用一个 user-invoked 技能列出其他技能，以及分别应该在何时使用，使人只需要记住一个技能。Router skill 只能提示，不能触发这些技能：user-invoked 技能没有可供模型发现的 description，所以只有人能抵达它们。

## `agents/openai.yaml`

<!-- source: vendor/mattpocock-skills/skills/productivity/writing-for-agents/agents/openai.yaml:1-3 -->

```yaml
interface:
  display_name: "Writing for Agents"
  short_description: "编写供 agent 使用的文档"
```
