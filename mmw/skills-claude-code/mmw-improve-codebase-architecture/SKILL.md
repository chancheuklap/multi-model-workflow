---
name: mmw-improve-codebase-architecture
description: 扫描 deepening opportunities，生成候选报告供用户选择。用户没有具体改动，只要求提升代码库的可维护性、可测性或 agent 可导航性；某块代码难改难测；或 bug 诊断确认缺少 seam、调用方纠缠或隐藏耦合时使用。
---

把架构上的摩擦翻出来，提成 **deepening opportunity**——把 shallow 的 module 改成 deep 的那类重构。目的是可测，以及 agent 读得懂。

**本技能不改代码。** 它的产物是一份候选报告，加一个被用户选中的方向。真正的改动走后面的主干：谈清楚、写 spec、派 `worker`。

设计词汇一律用 `/mmw-codebase-design` 定的那一套（module、interface、implementation、depth、deep、shallow、seam、adapter、leverage、locality），连同它的判据——deletion test、interface 就是测试面、一个 adapter 只是假设有这条 seam 两个 adapter 才证明它真的存在。每条建议都用这些词的原词，不要漂成「组件」「服务」「API」「边界」。

## 取上下文

| 材料 | 取得方式 | 读取内容 |
| --- | --- | --- |
| 领域文档 | **先读领域文档**：按 `/mmw-domain-modeling` 的「读领域文档」处理 | **好 seam 的名字**；不要停下来建 |
| ADR | 读你要碰的那一片的 ADR | ADR 里已经拍过板的决定，这次不重新拿出来吵 |

相关 leaf 里定义了「订单」，你就说「订单受理这个 module」，不说「那个 FooBarHandler」，也不说「订单服务」。

## 1. 先定范围

**扫之前先定扫哪——YAGNI。** 把一个 module 做深，回报是让**将来**改它变容易。所以最近一直在改的地方权重最高：那里的将来最快到。反过来，一块没人碰、也看不出要碰的地方，做深了回报兑现不了，这轮别扫它。有实打实的迹象说某块马上要大改（正在谈的需求压在它上面、已经有 spec 指向它），它同样算热点，即使 `git log` 上很安静。

- 用户点了方向（某个 module、某个子系统、某个痛点），就用他点的，跳过下面的推断。
- 没点，主 agent 直接读取 `git log --oneline`，从反复出现的文件和目录整理热点。改动散得到处都是、没有明显热点时，才把网撒大。

定完的这一片，是下一步所有人共同的地盘。

## 2. 派几个 `investigator` 各自去探

派 3 到 4 个 `investigator`，**每份 task 完全一样**，都探第 1 步定下的整片地方。四栏表：目标=在这片地方找架构摩擦；读=范围路径 + 领域文档 + `docs/adr/` 下相关的 ADR + `/mmw-codebase-design`（点技能名，不给路径）；约束=只读；验收=摩擦点带出处。
派一个独立上下文的 `investigator`。它只读，不需要工作目录。
启动：后台执行 `mmw dispatch investigator`。把四栏 task 正文作为命令的标准输入。当前 task 属于 decision ticket 时，加 `--issue <当前 decision ticket 编号>`。命令返回 `mode: host-tool` 时，使用输出中的 `params` 调用对应宿主工具。

互不依赖的实例在同一条消息里一起启动，全部回来之后再汇总。
按这个方式启动，重复 3 到 4 次，几个同时跑。

**不给分工，也不给检查清单。** 让它有机地探，记下它自己在哪里觉得摩擦大。下面这五问写进每份 task，作为**起手的入口**，不是要它逐条打钩的表：

| 入口 | 往哪看 |
| --- | --- |
| 概念散落 | 要理解一个概念，得在好几个小 module 之间来回跳吗？ |
| interface 太宽 | 哪些 module 是 shallow 的——interface 几乎和 implementation 一样复杂？ |
| 假的可测性 | 哪些纯函数是为了好测才抽出来的，但真正的 bug 藏在它们怎么被调用上（没有 locality）？ |
| seam 漏了 | 哪些互相咬死的 module 从 seam 漏了出去？ |
| 测不进去 | 哪些地方没有测试，或者隔着现在这个 interface 根本测不了？ |

task 里把这句原样写给它：**这五问是入口，不是清单。撞见五问之外的摩擦照样报，不要因为「不归我这条」丢掉。**

**多样性来自各自独立的上下文，不来自分配。** 所以不要给它们切视角，也不要把范围切成几块各管一段——几个 `investigator` 看同一片地方、各走各的路，撞见的东西自然不同。

怀疑某个东西 shallow 时，用 **deletion test** 验一下：把它删掉，复杂度是会聚到一处，还是只是挪个地方？「会聚到一处」才是你要的信号。

## 3. 先去重，再逐条验证

几份报告探的是同一片地方，重叠是预期之内的，不是谁做错了。

**先去重**：指向同一个 module、同一条 seam 的条目合成一条，把各份报告给的出处并进去——几个人独立撞见同一处摩擦，这件事本身就是它成立的证据，合并时记下来。换了个说法其实是同一件事的，也算重复。

**再逐条验证**：合并后的每条按 `/mmw-verifying-agent-output` 走。它说某个 module 是 shallow 的，你自己打开那几个文件，确认 interface 真的和 implementation 一样宽；它说某处耦合漏出了 seam，你自己找到那几行。验证不出来的不进报告。

## 4. 出报告

写一个自包含的 HTML 文件，落系统临时目录：从 `$TMPDIR` 取，取不到退回 `/tmp`（Windows 上是 `%TEMP%`）。文件名是 `architecture-review-<时间戳>.html`，每次跑一份新的。

生成后打开文件：macOS 使用 `open`，Linux 使用 `xdg-open`，Windows 使用 `start`。把绝对路径告诉用户。

**这份报告以图为主，不是以文字为主。** 每个候选的 before/after 图承担主要说明责任，文字只在旁边收口。一张图要配一段话才看得懂，就把图重画，不要把话写长。

每个候选一张卡片：

| 字段 | 内容 |
| --- | --- |
| 涉及文件 | 涉及哪些文件 |
| 当前摩擦 | 现在这个结构在哪里造成摩擦 |
| 目标结构 | 改成什么样 |
| 收益 | 用 locality 和 leverage 说明好处，以及测试会怎么变好 |
| before/after 图 | 整张卡片的重心，两列并排 |
| 推荐强度 | `Strong`、`Worth exploring` 或 `Speculative` |

结尾一节 **Top recommendation**：你会先做哪一个，为什么。

**跟 ADR 打架的候选**：只有摩擦真的大到值得重开那份 ADR 才提，提就在卡片里标明白（例如「与 ADR-0007 矛盾——但值得重开，因为……」）。不要把 ADR 禁掉的重构一条条列出来。

完整的 HTML 骨架、几种图的画法和风格要求见 [HTML-REPORT.md](HTML-REPORT.md)。

**这一步不要提 interface 方案。** 报告写完就停下来问用户：想深入看哪一个？

## 5. 用户挑中之后确认任务分支

挑中之前只读。挑中后再定任务分支名。类型固定用 `refactor`。短语取被选中 module 的名字。例如 `refactor-order-intake`。任务目标写用户原话和卡片标题：

先确认当前仓库位置。判定从上到下，命中一行就停。

| 情况 | 怎么判断 | 你做什么 |
| --- | --- | --- |
| 不在 git 仓库里 | `git rev-parse --is-inside-work-tree` 失败 | 向用户索取目标仓库路径。拿到路径后进入该仓库，再重新判断 |
| 在主检出里 | `git rev-parse --path-format=absolute --git-dir` 等于 `--git-common-dir` | 停下，请用户用当前宿主开一棵工作树再开会话 |
| 没有分支 | `git symbolic-ref --quiet --short HEAD` 为空 | 按上文已定的任务分支名运行 `git switch -c <完整任务分支名>` |
| 已有任务分支 | 上面都不成立 | 用当前分支 |


## 6. 就这一个候选谈下去

跑 `/mmw-grilling`，用它的设计树把这些内容跟用户走一遍：约束、依赖、做深之后这个 module 什么形状、seam 后面藏什么、哪些测试还活着。谈清楚之后它会回到本技能收尾。

`/mmw-grilling` 自带 `/mmw-domain-modeling`，通用的那部分不用你再交代。这里只补三条本技能特有的：

- **给做深后的 module 起的名字不在相关 leaf 里**，就把这个词加进去。单 context 仓库加进仓库根 `CONTEXT.md`；有 Context Map 的加进 Map 为本次范围登记的那个 leaf。
- **用户否掉这个候选**，按 `/mmw-domain-modeling` 的完整 ADR 判据决定是否提议记录。三项判据缺一项就不写。
- **想看看这个 module 还能有哪几种 interface**，跑 `/mmw-codebase-design`，用它的 DESIGN-IT-TWICE。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 验证过的候选写成报告，已经打开给用户看 | **停**：挑哪一个是要人拍板的事。报出了几个候选、你推荐哪一个、为什么 |
| 用户挑中一个 | **自己继续**：走第 5 步确认任务分支，再到第 6 步开谈 |
| 谈到用户要先看见几种 interface 才判得下来 | **自己继续**：跑 `/mmw-codebase-design` 的 DESIGN-IT-TWICE，比完回第 6 步接着谈 |
| `/mmw-grilling` 谈清楚了，回到本技能 | **移交**：`/mmw-to-spec`，把这张卡片的内容和谈出来的结论一起带过去 |
| 扫完一个值得做的都没有 | **停**：明说这一片现在没有值得做的 deepening opportunity，列出你扫了哪些方向。不要为了交差凑几个 `Speculative` 出来 |
| 用户看完报告说都不做 | **停**：不要追加提议，也不要进入第 5 步 |
