# `to-tickets` 1.2.2 中文翻译基线

## `SKILL.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/to-tickets/SKILL.md:1-5 -->

```yaml
---
name: to-tickets
description: 把一份计划、一份 spec 或当前对话拆成一组 tracer bullet ticket。每张 ticket 都声明自己的 blocking edge，并发布到已配置的 tracker。本地 tracker 使用每张 ticket 一个文件，并以文字记录 edge；真实 tracker 使用原生 blocking link。
disable-model-invocation: true
---
```

<!-- source: vendor/mattpocock-skills/skills/engineering/to-tickets/SKILL.md:7-11 -->

# To Tickets

把一份计划、一份 spec 或一段对话拆成一组 **ticket**。每张 ticket 都是一个 tracer bullet 垂直切片，并声明哪些 ticket 会**阻塞**它。

issue tracker 和 triage 标签词汇应该已经提供给你；如果没有，运行 `/setup-matt-pocock-skills`。

<!-- source: vendor/mattpocock-skills/skills/engineering/to-tickets/SKILL.md:13-17 -->

## 流程

### 1. 收集上下文

使用当前对话上下文中已经存在的内容。用户通过参数传入一项引用时，例如 spec 路径、issue 编号或 URL，取得该对象，并读取它的完整正文和评论。

<!-- source: vendor/mattpocock-skills/skills/engineering/to-tickets/SKILL.md:19-23 -->

### 2. 探索代码库（可选）

如果还没有探索过代码库，就探索代码库，以理解代码当前状态。Ticket 标题和描述应使用项目领域术语表中的词汇，并遵守本次涉及范围内的 ADR。

寻找能够通过 prefactor 让实施更容易的机会。“先让改动变得容易，再完成这个容易的改动。”

<!-- source: vendor/mattpocock-skills/skills/engineering/to-tickets/SKILL.md:25-36 -->

### 3. 起草垂直切片

把工作拆成 **tracer bullet** ticket。

<vertical-slice-rules>

- 每个切片都要狭窄，但必须沿每一层切出一条**完整**路径，包括 schema、API、UI 和测试。它必须是垂直切片，**不能**是只包含某一层的横向切片
- 完成的切片能够单独演示或验证
- 每个切片的大小必须能够放进一个全新的上下文窗口
- 所有 prefactor 都应先完成

</vertical-slice-rules>

<!-- source: vendor/mattpocock-skills/skills/engineering/to-tickets/SKILL.md:38 -->

为每张 ticket 声明它的 **blocking edge**，也就是这张 ticket 开始前必须完成的其他 ticket。没有 blocker 的 ticket 可以立即开始。

<!-- source: vendor/mattpocock-skills/skills/engineering/to-tickets/SKILL.md:40 -->

**Wide refactor 是垂直切片的例外。** **Wide refactor** 是一项机械改动，例如重命名一列或重新确定一个共享符号的类型。它的 **blast radius** 会扩散到整个代码库，因此一次编辑会同时破坏成千上万个调用位置，没有任何垂直切片能够以 green 状态落地。不要强行把它塞进 tracer bullet；应按 **expand–contract** 排列。首先 expand：在旧形式旁边增加新形式，使任何内容都不会损坏。随后按 blast radius 大小分批迁移调用位置，例如每个软件包或每个目录一批；每一批都是一张独立 ticket，并被 expand ticket 阻塞。旧形式仍然存在，因此 CI 可以在批次之间保持 green。最后 contract：确认没有调用方剩下后删除旧形式；这张 ticket 被每一张迁移批次 ticket 阻塞。如果连各个批次都无法单独保持 green，就保留这个顺序，但让这些批次共用一条集成分支，并让它们全部阻塞最后一张“集成并验证”ticket；只有在最后一张 ticket 上才承诺 green。

<!-- source: vendor/mattpocock-skills/skills/engineering/to-tickets/SKILL.md:42-56 -->

### 4. 询问用户

以编号清单展示拟议的拆分。每张 ticket 展示：

- **Title**：简短的描述性名称
- **Blocked by**：必须先完成哪些其他 ticket；没有则明确说明
- **What it delivers**：这张 ticket 会让哪项端到端行为可用

向用户询问：

- 粒度是否合适，是太粗还是太细？
- blocking edge 是否正确，也就是每张 ticket 是否只依赖真正阻挡它开始的 ticket？
- 是否应该合并某些 ticket，或者进一步拆分？

持续调整，直到用户批准这份拆分。

<!-- source: vendor/mattpocock-skills/skills/engineering/to-tickets/SKILL.md:58-67 -->

### 5. 把 ticket 发布到已配置的 tracker

发布已经批准的 ticket。具体**方式**取决于 `/setup-matt-pocock-skills` 配置的 tracker。无论哪种 tracker，ticket 本身都相同；只有 blocking edge 的表达形态不同：

- **本地文件**：在 `.scratch/<feature-slug>/issues/<NN>-<slug>.md` 下为每张 ticket 写一个文件。从 `01` 开始，按依赖顺序编号，blocker 在前。每个文件的 `Blocked by` 列出它依赖的 ticket 编号和标题。使用下方的单 ticket 文件模板；每个文件只放一张 ticket，绝不合并到一个文件。
- **真实 issue tracker，例如 GitHub 或 Linear**：按依赖顺序发布，每张 ticket 对应一个 issue，blocker 在前，使每张 ticket 的 blocking edge 能够引用真实标识符。平台提供原生 blocking 或 sub-issue 关系时使用原生关系；否则，把每张 ticket 的 `Blocked by` 设为阻塞它的 issue。除非收到其他指示，否则添加 `ready-for-agent` triage 标签；这些 ticket 的构造方式已经使 agent 可以直接认领。

沿 **frontier** 工作，也就是所有 blocker 都已完成的 ticket。对于纯线性链，这意味着从上到下依次处理。

**不要**关闭或修改任何 parent issue。

<!-- source: vendor/mattpocock-skills/skills/engineering/to-tickets/SKILL.md:69-82 -->

<local-ticket-template>

# <NN> — <Ticket title>

**What to build:** 从用户角度说明这张 ticket 会让哪项端到端行为可用；不要写成逐层实施清单。

**Blocked by:** 写出阻挡这张 ticket 的 ticket 编号和标题，或者写 `None — can start immediately`。

**Status:** ready-for-agent

- [ ] 验收判据 1
- [ ] 验收判据 2

</local-ticket-template>

<!-- source: vendor/mattpocock-skills/skills/engineering/to-tickets/SKILL.md:84-103 -->

<issue-template>

## Parent

引用 tracker 上的 parent issue。如果来源不是已有 issue，就省略这个章节。

## What to build

从用户角度说明这张 ticket 会让哪项端到端行为可用；不要写成逐层实施。

## Acceptance criteria

- [ ] 判据 1
- [ ] 判据 2

## Blocked by

- 引用每张 blocking ticket，或者写 `None — can start immediately`。

</issue-template>

<!-- source: vendor/mattpocock-skills/skills/engineering/to-tickets/SKILL.md:105 -->

无论使用哪一种形态，都不要写入具体文件路径或代码片段，因为它们很快就会过期。例外：如果 prototype 产生的一段代码比文字更精确地编码了某项决定，例如状态机、reducer、schema 或类型形状，就把它内联，并简短注明它来自 prototype。只保留决定信息密集的部分；不要放入可运行 demo，只放重要片段。

## `agents/openai.yaml`

<!-- source: vendor/mattpocock-skills/skills/engineering/to-tickets/agents/openai.yaml:1-5 -->

```yaml
interface:
  display_name: "To Tickets"
  short_description: "把一份计划拆成 tracer bullet ticket"
policy:
  allow_implicit_invocation: false
```
