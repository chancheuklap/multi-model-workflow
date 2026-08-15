---
name: mmw-to-plan
description: 为已发布 spec 的 tracer bullet ticket 按批次编排 plan。spec 和 tickets 已发布、下一步要写 plan 时使用；`$mmw:mmw-implement` 关票解锁新批次后也回到这里。
---

开始前，遵守目标仓库 `AGENTS.md` 的领域上下文规则。

把 ticket 写成 plan，供后面派 `worker` 照着落地。

**批次**指某一时刻还没有 `ready-for-agent` 标签、而且现在就写得出 plan 的那些 open tracer bullet ticket。

一张 ticket 现在写不写得出 plan，看一件事：**写它的 plan 要知道上游的哪些情况，那些情况 spec 的 `## Cross-Plan Contract Anchors` 给了没有。** 给了就现在写；只有等上游代码做出来才知道的，这一轮排除，进下一批。

plan 不写行号，路径和符号名由 `worker` 开工时回到源码确认。所以下游 plan 不必等上游 ticket 落地——它要的接口形状、字段和取值，那一节里都有。ticket 之间的阻塞关系决定谁先**实现**，不决定谁先**写 plan**。

多数 spec 的 ticket 一个批次就写完了。有第二批时与 `$mmw:mmw-implement` 交替推进：它关票之后，还没有标签的 ticket 就是下一批。

批次成员资格看两件事：有没有 `ready-for-agent` 标签，以及现在写不写得出 plan。plan 文件写出来了没有不参与判定。中断后重入时，已有 plan 文件但没有标签的 ticket 重新走验证、审查和打标签。

**你不写 plan。** 写作全部下放给 `planner`，一张 ticket 一个。你的职责是定批次、划合同边界、派发、验证、发起审查。

## 前置条件

三件事必须满足，缺一件就停下说清是哪一件。

| 检查 | 怎么查 |
| --- | --- |
| 你在一条任务分支上 | `git symbolic-ref --quiet --short HEAD` 有输出，且不在主检出里；不满足就停下，说明当前没有任务分支，无法继续 |
| spec 已定稿并过了人工审批关卡 | 运行 `mmw artifact path spec`。输出文件存在。对应的 spec issue 已发布并带着 `ready-for-agent` |
| ticket 已发布 | `mmw issue children <spec issue 编号>` 列得出这批 ticket；列不出先跑 `$mmw:mmw-to-tickets` |

`<spec issue 编号>` 由调用方移交时给你。没有这个编号就停下，说明缺少哪项输入。

## 1. 定本批次

| 上下文 | 何时读取 | 读取范围 | 不读取 | 向下传递 |
| --- | --- | --- | --- | --- |
| spec | 首个批次 | 问题、方案、实现决定、合同边界和测试 seam | 其他 spec | spec 路径 |
| spec | 后续批次 | 只读 `## Cross-Plan Contract Anchors` | spec 其余各节 | spec 路径 |
| ticket | 首个批次 | 全部 ticket 的目标、验收、阻塞关系和 plan 路径 | 其他 spec 的 ticket | ticket 编号和 plan 路径 |
| ticket | 后续批次 | 只读本批次 ticket | 已经写过 plan 的 ticket | ticket 编号和 plan 路径 |
| 产物引用 | ticket 有 `## 产物引用` 时 | 当前 ticket 实际需要的条目 | 其他 ticket 的条目 | 原样传递 |
| prototype | ticket 引用时 | 索引、选中产物、明确相关的走查或长期证据 | 整个产物目录、无关过程材料 | 产物引用；没有写「无 prototype 资产」 |
| research | ticket 引用时 | research 索引和当前 ticket 使用的精确文件 | research 的上级目录、subagent 原始报告 | 产物引用；没有写「无 research」 |

prototype 索引字段不完整时回 `$mmw:mmw-prototype` 补齐。

读取当前 ticket 的 `## 产物引用`。缺少这节时停止，说明缺少 ticket 声明。把当前 ticket 的条目原样写进 `planner` task 的「读」栏。该节写 `无` 时也把 `无` 写进 task。

- `## Problem Statement`
- `## Solution`
- `## Implementation Decisions`
- `## Contract Boundaries`
- `## Testing Decisions` 中的 seam 清单表

**只读，作为派发时给 `planner` 的上下文**，不在这里展开写作。

用 `mmw issue children <spec issue 编号>` 取全部 ticket，读出各自要做什么和被谁阻塞。还没有 `ready-for-agent` 的 open ticket 是候选，逐张问一遍：

**写这张的 plan，要知道上游的哪些情况？那些情况在 `## Cross-Plan Contract Anchors` 里找得到吗？**

| 答案 | 怎么办 |
| --- | --- |
| 找得到 | 进本批次。上游代码还没写也不要紧，`planner` 照那一节写 |
| 找不到，只有上游代码做出来才知道 | 排除，进下一批 |

第二种最常见的是整体验收类 ticket：它要写的是全部功能做出来以后，界面和流程实际长什么样，那不是合同给得了的。

判不准时留在本批次。`planner` 探代码发现材料对不上，会交回 `needs-context`，那时再挪。

**一张 ticket 一份 plan 一个 `planner`**；不在本批次的 ticket 这一轮不碰。本批次为空而仍有 open ticket 时，说明它们都已被认领，或者都在等上游代码做出来——报告各张状态并停下。

本批次每张 ticket 的 `## Plan` 一节写出完整的 `mmw artifact path plan --sub <两位编号>-<ticket短名>.md` 命令。逐份运行它，取得每份 plan 的落点。编号照抄，不自己重排。ticket 正文没有这一节时，按依赖顺序自己编号。被阻塞的排在阻塞它的后面。

**轻量验证现状**：用检索确认 spec 涉及的落点目录和关键路径真实存在，够你判断派几个 `planner`、各管哪张 ticket 就行。深度探代码由 `planner` 各自做，你不抢着探全。

术语或验收标准不清楚，回 `$mmw:mmw-to-spec` 改；架构假设跟代码现实对不上，先弄清楚再派。

## 2. 把合同落到 plan 头上

**这一步只在首次进入本技能时做**，后续批次沿用同一节。spec 里已有 `## Cross-Plan Contract Anchors` 一节就跳过。全部 ticket 只产出一份 plan 时也跳过。

在 spec 里新增一节 `## Cross-Plan Contract Anchors`，**不改已有的 `## Contract Boundaries`**。

从 `## Contract Boundaries`、`## Implementation Decisions` 两节和 ticket 的依赖关系判断有没有跨 plan 的连接面——共享文件、共享模块、共享数据结构，或者一份 plan 产出、另一份 plan 消费的接口。有就写进刚新增的 `## Cross-Plan Contract Anchors`，**一次把全部 ticket 的都写完**：

- **文件归属**：哪份 plan 可以碰哪些共享文件。一个文件一个归属方。
- **跨 plan 接口**：按 plan 编号写清谁提供、谁消费（比如「01 提供鉴权令牌接口，02 消费」），并写出确切的字段名、签名、状态名、路由名和数值。

**这些值全部来自 spec。** ticket 的验收标准里已经逐字定死的精确值（数字、文案、状态名、字段名）照抄进来。

spec 里确实没有、必须看了代码才知道的，那一格留空，并写明缺的是什么。`planner` 探代码时会拿这一格交 `needs-context`，那时由你补齐。先填一个猜的值，两边就会一起错下去。

这一节是这些字段的**权威副本**。plan 只引用条目名，不再抄一份（见 `$mmw:mmw-planner` 的 `plan-body.md`）：抄成两份就要改两处，代码一变，两处都会跟代码对不上。

没有跨 plan 连接面就在这一节写明「无跨 plan 共享合同」。

这一节随 spec 进入 `planner` 的上下文：`planner` 不许认领别份 plan 归属的文件。

## 3. 派 `planner`

本批次一张 ticket 一个 `planner`。按 **四栏表**（目标 / 读 / 约束 / 验收）填写：

| 栏 | 本角色填写 |
| --- | --- |
| 目标 | 为 ticket `#<编号>` 写 plan。运行 ticket `## Plan` 一节的完整 `mmw artifact path plan --sub <两位编号>-<ticket短名>.md` 命令。把输出路径写进这一栏。`planner` 只认 task 里给的这一个落点 |
| 读 | 列出 spec 与当前 ticket 的精确路径，并原样传递当前 ticket 的产物引用。`planner` 自己运行 `mmw artifact path` 解析。方法论不用列——`planner` 自带 `$mmw:mmw-planner` |
| 约束 | 只写该 plan 文件；不提交；不认领 `## Cross-Plan Contract Anchors` 划给别人的文件；不写其他 plan 的正文 |
| 验收 | plan 文件存在且可被抽验；`## Acceptance` 覆盖 ticket `#<编号>` 的全部验收（详见 issue，不抄正文） |

派一个 `planner`，它在**当前任务 worktree** 里写 plan 文件，不另开分支。
启动：按名称调用 Codex 原生 subagent `mmw-planner`，task 传四栏表全文；该 subagent 使用当前工作树，不另开结果树。互不依赖的实例在同一条消息中并行启动，全部完成后再汇总。

派出 subagent 后，主 agent 不得执行与该 subagent task 重叠的 research、实现或审查。没有明确不重叠的协调工作时，立即等待 subagent 交回报告；报告交回后只按 `$mmw:mmw-verifying-agent-output` 验证关键断言，不重做整个 task。

**当前任务 worktree 的绝对路径**：`git rev-parse --show-toplevel`。

同一条消息里并行启动本批次的全部 `planner`。批次内的 ticket 之间可以有阻塞关系——那决定谁先实现，不决定谁先写 plan。`planner` 使用当前任务 worktree，不建独立 worktree，不提交。每个 `planner` 只写自己的 plan 文件。

派发返回的 `session:` 或 `handle:` 行是这个 `planner` 的恢复句柄。记下来，第 4 步与 ② plan 审的修复都用它。

## 4. 验证返回

每个 `planner` 交回 `pass` 之后，验证 plan 文件存在，元数据块的 `ticket` 等于当前 ticket 编号且 `artifact_refs` 键存在，ticket 的每条验收都能映射到 `## Acceptance`，再抽验至少一条源码依据。读取文件并检索源码，不认「我写完了」。

**再问一次「有没有多」。** 上面各项问的都是有没有漏，只往一个方向使劲，plan 就会越写越长。抽读 `## Constraints` 和 `## Contracts and Seams` 两节，看有没有这三样：

- 整段复制 spec 的内容，而不是只留影响本 ticket 的那几条。
- 超出 `plan-body.md` 允许范围的实现代码。允许的只有 spec 已确定的公开合同、数据形状，以及文字表达不了的关键算法。
- `plan-body.md` 模板之外的小节，或者跨 plan 接口抄了字段全文而不是引用锚点条目名。

有就发回原 `planner` 删掉再交。这一条判的是内容，不看行数——plan 该多长由这张 ticket 决定。

接受 `pass` 前运行 `mmw artifact check`。命令非零时把当前 plan 的错误交回该 `planner` 修复。命令通过后才接受 `pass`。

失实就把修复说明发回原 `planner` 续跑：
这个宿主没有续跑通道：按对应的启动动作重派新实例，task 正文带上原 task 全文、原报告全文和本轮修复指令。

交回 `needs-context` 的，补齐它点名的材料之后重派。交回 `needs-repair` 的，它指的是 spec 或 ticket 本身有错：要改的内容会变更用户已批准的验收标准、spec 决定或 blocking edge 时，**停下**，把 `planner` 交回的证据交给用户，取得批准后再修对应材料；只有不改变已批准语义的笔误级修正可以直接修。修完带上修正后的材料重派。

交回 `needs-redirection` 的，把它说的哪里可疑、建议怎么重新框定原样交给用户，不要自己改 spec 绕过去。已落地批次保留在任务分支。

同一份 plan 返修三轮还没过：报是哪一份、卡在哪里、三轮各自改了什么，让用户定。

## 5. 验证边界

**本批次只有一份 plan 时跳过本步**：没有别人可以认领，也没有第二方对接。

本批次有多份 plan 时，对着第 2 步写好的 `## Cross-Plan Contract Anchors` 验证两件事。入口是每份 plan 的 `## Change Map`、`## Contracts and Seams`，以及 `planner` 报告里的 `Cross-plan touchpoints`：

- 有没有 `planner` 认领了别人归属的文件。
- 提供方和消费方引用的锚点条目名一致，各自的实施步骤跟那个条目里的字段对得上。

对不上就把差异说明发回原 `planner` 续跑修那一份，句柄失效时重派。

`planner` 报告的 `Cross-plan touchpoints` 指出锚点本身写错或缺一条时，改 spec 的那一节，然后把改动发给受影响的每个 `planner`。锚点是权威副本，改它就要让引用它的 plan 跟上。

## 6. 发起 ② plan 审

**本批次 plan 都验证过、边界也验证完之后，发起一次审查，批内不逐份发起。** 按 `$mmw:mmw-review` 走。传给它本批次每张 ticket 的 plan 类别内细分。逐份运行 `mmw artifact path plan --sub <两位编号>-<ticket短名>.md`。再传这份 spec 的精确路径、全部 ticket 编号，以及本批次 plan 引用的 prototype `README.md`、选中产物、research `README.md` 和精确文件。没有的项目写「无」。

**首个批次**的审查材料里额外注明：本轮覆盖质量审执行 spec 到 ticket 集合的覆盖扫描。后续批次不写这一句。

## 7. 提交

本批次 plan 文档和 spec 的 `## Cross-Plan Contract Anchors` 改动分两次提交。`planner` 不提交，改动一直是未暂存的，由你统一收。

## 8. 标记本批次 ticket 就绪

本批次 plan 全部通过 ② plan 审，而且第 7 步完成后，给本批次每张 ticket 幂等添加 `ready-for-agent`：

```bash
gh issue edit <ticket 编号> --add-label ready-for-agent
```

命令非零时说明这张没打上，重跑那一张。命令通过就是打上了，不再回头读一遍确认。

`ready-for-agent` 表示 ticket 的 plan 已经通过 ② plan 审。`Blocked by` 和 `mmw issue frontier` 继续决定哪张 ticket 已经无阻塞并且可以认领；只有进入 frontier 的 ticket 才能派 `worker`。

本批次 plan 过审、提交，且本批次 ticket 都带 `ready-for-agent` 之后，报告本批次已就绪。问用户：开始实现，还是到这里停。`$mmw:mmw-implement` 关票解锁新批次后会回到本技能。
