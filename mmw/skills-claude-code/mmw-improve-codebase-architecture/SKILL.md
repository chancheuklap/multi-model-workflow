---
name: mmw-improve-codebase-architecture
description: 扫一遍代码库找可以做深的模块，出一份候选报告让用户挑。用户没有具体需求、只说想让代码库更好维护、说某块代码难改难测时用它；诊断完发现根因是架构问题的技能也移交这里。
---

把架构上的摩擦翻出来，提成 **deepening opportunity**——把 shallow 的 module 改成 deep 的那类重构。目的是可测，以及 agent 读得懂。

**本技能不改代码。** 它的产物是一份候选报告，加一个被用户选中的方向。真正的改动走后面的主干：谈清楚、写 spec、派 `worker`。

设计词汇一律用 `/mmw-codebase-design` 定的那一套（module、interface、implementation、depth、deep、shallow、seam、adapter、leverage、locality），连同它的判据——deletion test、interface 就是测试面、一个 adapter 是假 seam 两个才是真 seam。每条建议都用这些词的原词，不要漂成「组件」「服务」「API」「边界」。

## 先读领域文档

**先读领域文档**：落点跑 `mmw domain path` 取，三种返回怎么读见 `/mmw-domain-modeling` 的「读领域文档」一节，不要停下来建。

再读你要碰的那一片的 ADR。ADR 里已经拍过板的决定，这次不重新拿出来吵。

领域文档给的是**好 seam 的名字**。`CONTEXT.md` 里定义了「订单」，你就说「订单受理这个 module」，不说「那个 FooBarHandler」，也不说「订单服务」。

## 1. 先定范围

**扫之前先定扫哪。** 最近一直在改的地方权重最高。

- 用户点了方向（某个 module、某个子系统、某个痛点），就用他点的，跳过下面的推断。
- 没点，**按 `/mmw-research` 的内部方向派一个 subagent** 翻提交历史（`git log --oneline`），交回一张热点清单——反复出现的那几个文件和目录。改动散得到处都是、没有明显热点时，才把网撒大。

定完的这一片，是下一步所有人共同的地盘。

## 2. 一个视角派一个 subagent 去扫

五个视角，一个视角一个 subagent，并行扫描。每个视角：四栏表（目标=该视角问题；读=范围路径 + 领域文档 + `/mmw-codebase-design` + ADR 路径；约束=只读；验收=摩擦点带出处）。
启动：四栏表写入 brief 文件后，Bash（`run_in_background: true`）执行 `mmw dispatch investigator --brief <brief 绝对路径>`；回执 `mode: host-tool` 时原样传入 `params` 调用对应工具。

| 视角 | 让它去看 |
| --- | --- |
| 概念散落 | 要理解一个概念，得在好几个小 module 之间来回跳吗？ |
| interface 太宽 | 哪些 module 是 shallow 的——interface 几乎和 implementation 一样复杂？ |
| 假的可测性 | 哪些纯函数是为了好测才抽出来的，但真正的 bug 藏在它们怎么被调用上（没有 locality）？ |
| seam 漏了 | 哪些互相咬死的 module 从 seam 漏了出去？ |
| 测不进去 | 哪些地方没有测试，或者隔着现在这个 interface 根本测不了？ |

**按视角分，不按范围分。** 每个 subagent 都看第 1 步定下来的整片地方，不要把它切成几块各管一段。

每份 task 给同样的路径与范围（领域文档路径、`/mmw-codebase-design` 词汇表路径、这一片的 ADR 路径、第 1 步定下的范围），只有视角那一栏不同。subagent 自己读路径。

**不要给它僵硬的打分表**，让它有机地探，记下它在哪里觉得摩擦大。

怀疑某个东西 shallow 时，用 **deletion test** 验一下：把它删掉，复杂度是会聚到一处，还是只是挪个地方？「会聚到一处」才是你要的信号。

## 3. 收回来的先验证再采信

subagent 交回的东西按 `/mmw-verifying-agent-output` 逐条验证。它说某个 module 是 shallow 的，你自己打开那几个文件，确认 interface 真的和 implementation 一样宽；它说某处耦合漏出了 seam，你自己找到那几行。验证不出来的不进报告。

## 4. 出报告

写一个自包含的 HTML 文件，落系统临时目录：从 `$TMPDIR` 取，取不到退回 `/tmp`（Windows 上是 `%TEMP%`），文件名 `architecture-review-<时间戳>.html`，每次跑一份新的。然后打开它——macOS `open`、Linux `xdg-open`、Windows `start`——把绝对路径告诉用户。

每个候选一张卡片：涉及哪些文件、现在这个结构在哪里造成摩擦、改成什么样、好处（用 locality 和 leverage 说，以及测试会怎么变好）、一张 before/after 图、一个推荐强度徽章（`Strong`、`Worth exploring`、`Speculative`）。结尾一节 **Top recommendation**：你会先做哪一个，为什么。

**跟 ADR 打架的候选**：只有摩擦真的大到值得重开那份 ADR 才提，提就在卡片里标明白（例如「与 ADR-0007 矛盾——但值得重开，因为……」）。不要把 ADR 禁掉的重构一条条列出来。

完整的 HTML 骨架、几种图的画法和风格要求见 [HTML-REPORT.md](HTML-REPORT.md)。

**这一步不要提 interface 方案。** 报告写完就停下来问用户：想深入看哪一个？

## 5. 用户挑中之后再建 worktree

挑中之前不建 worktree，扫描全程只读。

挑中了就定 slug，跑 `mmw task new <slug> "<原话加这张卡片的标题>"`，再用宿主的工作目录切换工具进到它输出的那个路径（Claude Code 是 `EnterWorktree`，pi 是 `enter_worktree`；这一步脚本做不了，只有宿主工具做得到）。类型固定用 `refactor`，短语取被选中那个 module 的名字，例如 `refactor-order-intake`。

## 6. 就这一个候选谈下去

跑 `/mmw-grilling` 把决定树跟用户走一遍：约束、依赖、做深之后这个 module 什么形状、seam 后面藏什么、哪些测试还活着。谈清楚之后它会回到本技能收尾。

`/mmw-grilling` 自带 `/mmw-domain-modeling`，通用的那部分不用你再交代。这里只补三条本技能特有的：

- **给做深后的 module 起的名字不在 `CONTEXT.md` 里**，就把这个词加进去（多 context 的仓库：加进 `mmw domain path` 在 map 模式下为本次范围指出的那份 `CONTEXT.md`）。
- **用户否掉这个候选**，提议写一份 ADR，话这么说：「要不要记成 ADR，免得下次架构走查又提一遍？」只在这个理由是未来的人真需要、否则同一件事会被重复提议时才提；一次性的理由（「现在不值得做」）和不言自明的理由跳过。
- **想看看这个 module 还能有哪几种 interface**，跑 `/mmw-codebase-design`，用它的 DESIGN-IT-TWICE。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 验证过的候选写成报告，已经打开给用户看 | **停**：挑哪一个是要人拍板的事。报出了几个候选、你推荐哪一个、为什么 |
| 用户挑中一个 | **自己继续**：走第 5 步建 worktree，再到第 6 步开谈 |
| 谈到用户要先看见几种 interface 才判得下来 | **自己继续**：跑 `/mmw-codebase-design` 的 DESIGN-IT-TWICE，比完回第 6 步接着谈 |
| `/mmw-grilling` 谈清楚了，回到本技能 | **移交**：`/mmw-to-spec`，把这张卡片的内容和谈出来的结论一起带过去 |
| 扫完一个值得做的都没有 | **停**：明说这一片现在没有值得做的 deepening opportunity，列出你扫了哪些方向。不要为了交差凑几个 `Speculative` 出来 |
| 用户看完报告说都不做 | **停**：不要追加提议，也不要把 worktree 建起来 |
