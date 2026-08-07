# `code-review` 1.2.2 中文翻译基线

## `SKILL.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/code-review/SKILL.md:1-4 -->

```yaml
---
name: code-review
description: 沿两条轴审查从一个固定点（commit、branch、tag 或 merge-base）开始的改动——Standards（代码是否遵循本仓库记录的编码标准？）和 Spec（代码是否符合来源 issue 或 spec 的要求？）。在并行 subagent 中运行两项审查，并把报告并列展示。用户想要审查 branch、PR、进行中的改动，或要求“审查从 X 开始的改动”时使用。
---
```

<!-- source: vendor/mattpocock-skills/skills/engineering/code-review/SKILL.md:6-13 -->

对 `HEAD` 与用户提供的一个固定点之间的 diff 进行双轴审查：

- **Standards**——代码是否符合本仓库记录的编码标准？
- **Spec**——代码是否忠实地实现了来源 issue 或 spec？

两条轴都由**并行 subagent**运行，使它们不会污染彼此的上下文；随后本技能汇总它们的 findings。

issue tracker 应该已经提供给你；如果缺少 `docs/agents/issue-tracker.md`，运行 `/setup-matt-pocock-skills`。

<!-- source: vendor/mattpocock-skills/skills/engineering/code-review/SKILL.md:15-23 -->

## 流程

### 1. 锁定固定点

用户所说的对象就是固定点，例如 commit SHA、branch 名称、tag、`main` 或 `HEAD~5`。如果用户没有指定，就询问用户。

只记录一次 diff 命令：`git diff <fixed-point>...HEAD`。使用三个点，使比较以 merge-base 为基准。同时通过 `git log <fixed-point>..HEAD --oneline` 记录 commit 清单。

继续之前，确认固定点能够解析（`git rev-parse <fixed-point>`），并且 diff 不为空。错误的 ref 或空 diff 应该在这里失败，不要等到两个并行 subagent 内部才失败。

<!-- source: vendor/mattpocock-skills/skills/engineering/code-review/SKILL.md:25-32 -->

### 2. 找出 spec 来源

按照以下顺序寻找来源 spec：

1. commit message 中的 issue 引用，例如 `#123`、`Closes #45` 或 GitLab `!67`。使用 `docs/agents/issue-tracker.md` 中的工作流取得内容。
2. 用户通过参数传入的路径。
3. `docs/`、`specs/` 或 `.scratch/` 下与 branch 名称或功能匹配的 spec 文件。
4. 如果没有找到任何内容，询问用户 spec 在哪里。如果用户说不存在 spec，**Spec** subagent 将跳过，并报告“没有可用的 spec”。

<!-- source: vendor/mattpocock-skills/skills/engineering/code-review/SKILL.md:34-43 -->

### 3. 找出标准来源

仓库中任何记录代码编写方式的内容都属于标准来源，例如 `CODING_STANDARDS.md` 或 `CONTRIBUTING.md`。

除了仓库记录的内容，Standards 轴始终携带下方的**代码异味基线**。这是 Fowler 在《重构》第 3 章中定义的一组固定代码异味；即使仓库没有记录任何标准，这组基线也适用。它受两条规则约束：

- **仓库规则优先。** 仓库记录的标准始终优先。如果仓库标准认可某种会被基线标记的做法，就不要报告那项代码异味。
- **始终需要判断。** 每种代码异味都是带标签的启发法，例如“可能存在 Feature Envy”，绝不是硬性违规。与此处任何标准一样，已经由工具强制执行的内容都要跳过。

每项代码异味按照“它是什么”到“如何修复”的顺序说明；把它与 diff 对照：

<!-- source: vendor/mattpocock-skills/skills/engineering/code-review/SKILL.md:45-56 -->

- **Mysterious Name**——函数、变量或类型的名称没有揭示它的作用或保存的内容。→ 重命名；如果想不出诚实的名称，说明设计含混不清。
- **Duplicated Code**——相同的逻辑形状出现在本次改动的多个 diff 区块或文件中。→ 提取共享形状，并从两处调用它。
- **Feature Envy**——一个方法访问另一个对象的数据多于访问自身的数据。→ 把方法移到它所依恋的数据上。
- **Data Clumps**——相同的几个字段或参数总是一起传递，说明一个类型正等待诞生。→ 把它们组合成一个类型，并传递这个类型。
- **Primitive Obsession**——用 primitive 或字符串代替一个值得拥有自身类型的领域概念。→ 给这个概念一个自己的小型类型。
- **Repeated Switches**——本次改动中，对同一类型执行的同一个 `switch` 或 `if` 级联反复出现。→ 用多态替代，或让两处共用一张映射表。
- **Shotgun Surgery**——一项逻辑改动迫使你在 diff 中分散编辑许多文件。→ 把一同变化的内容集中到一个 module。
- **Divergent Change**——因为几个互不相关的原因编辑同一个文件或 module。→ 拆分它，使每个 module 只因一个原因而改变。
- **Speculative Generality**——为了 spec 中不存在的需求增加抽象、参数或 hook。→ 删除它；重新内联，直到真实需求出现。
- **Message Chains**——调用方不应依赖的长链式导航，例如 `a.b().c().d()`。→ 把遍历隐藏在第一个对象的一个方法后面。
- **Middle Man**——一个 class 或函数主要只是继续委托。→ 移除它，直接调用真正的目标。
- **Refused Bequest**——一个 subclass 或 implementer 忽略或覆写了所继承内容的大部分。→ 放弃继承，改用组合。

<!-- source: vendor/mattpocock-skills/skills/engineering/code-review/SKILL.md:58-74 -->

### 4. 并行派出两个 subagent

发送一条包含两次 `Agent` 工具调用的消息。两次都使用 `general-purpose` subagent。

**Standards subagent task**——包含：

- 完整的 diff 命令和 commit 清单。
- 第 3 步找到的标准来源文件清单，**再加上完整粘贴的第 3 步代码异味基线**。这个 subagent 无法通过其他方式访问该基线。
- task：“在相关位置按文件或 diff 区块报告：(a) diff 违反已记录标准的每一处位置，并引用该标准，包括文件和规则；(b) 发现的任何基线代码异味，写出名称并引用 diff 区块。区分硬性违规和判断项。已记录标准的违反可以是硬性违规，但基线代码异味始终是判断项，而且仓库记录的标准优先于基线。跳过工具已经强制执行的内容。控制在 400 个词以内。”

**Spec subagent task**——包含：

- diff 命令和 commit 清单。
- spec 的路径或取得的正文。
- task：“报告：(a) spec 要求但缺失或只完成一部分的需求；(b) diff 中没有被要求的行为，也就是 scope creep；(c) 看起来已经实施，但实施方式似乎错误的需求。每项 finding 都要引用对应的 spec 行。控制在 400 个词以内。”

如果缺少 spec，就跳过 Spec subagent，并在最终报告中注明这一点。

<!-- source: vendor/mattpocock-skills/skills/engineering/code-review/SKILL.md:76-80 -->

### 5. 汇总

在 `## Standards` 和 `## Spec` 标题下展示两份报告。可以原样展示，也可以轻微整理。**不要**合并 findings，也不要重新排序；两条轴是有意分开的，参见“为何使用两条轴”。

最后用一行作结：写出每条轴的 finding 总数，以及每条轴**内部**最严重的问题（如有）。不要从两条轴之间选出一个唯一最严重的问题；分开两条轴就是为了防止这种重新排序。

<!-- source: vendor/mattpocock-skills/skills/engineering/code-review/SKILL.md:82-89 -->

## 为何使用两条轴

一项改动可以通过其中一条轴，却无法通过另一条轴：

- 代码遵守所有标准，却实现了错误的内容 → **Standards 通过，Spec 失败。**
- 代码完全实现 issue 的要求，却违反项目约定 → **Spec 通过，Standards 失败。**

分开报告可以防止一条轴掩盖另一条轴。

## `agents/openai.yaml`

<!-- source: vendor/mattpocock-skills/skills/engineering/code-review/agents/openai.yaml:1-3 -->

```yaml
interface:
  display_name: "Code Review"
  short_description: "沿 Standards 和 Spec 两条轴审查 diff"
```
