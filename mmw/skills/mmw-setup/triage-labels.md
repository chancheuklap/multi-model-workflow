# Issue 标签

两个维度，互不干涉：一张 issue 各带一个。

## 状态：这张 issue 现在够不够清楚

技能里说到某个角色时，用右列的真实标签字符串。

| 技能里的角色 | 本仓库的标签 | 含义 |
| --- | --- | --- |
| `needs-triage` | `needs-triage` | 还没评估过，不知道该不该做、怎么做 |
| `needs-info` | `needs-info` | 缺输入，等人补 |
| `ready-for-agent` | `ready-for-agent` | 当前合同已写清，可以由 agent AFK 继续 |
| `ready-for-human` | `ready-for-human` | 下一步由人承担，agent 不代替 |
| `wontfix` | `wontfix` | 决定不做 |

`ready-for-agent` 是唯一一个机器可验证的「合同足够让 agent AFK 继续」信号。它不指定下一项技能，也不豁免承接技能自己的前置条件。

不同 work item 的合同不同：已分诊 issue 或外部 PR 使用 agent brief；spec issue 使用用户批准的 spec；实现 ticket 使用验收标准，进入 `/mmw-implement` 前还必须有通过 plan 审的 plan。

`/mmw-to-spec` 只在用户批准 spec 后发布或更新 spec issue。因此，spec issue 存在且带 `ready-for-agent`，同时也是 spec 定稿人工审批关卡的通过凭据。这个附加事实不改变标签的通用含义。

## HITL 与 AFK：这件活要不要人在场

一件活只分这两种。**全 plugin 只用这两个词，不另写中文说法**——它们是一对，拆开翻译就散了。

| 词 | 展开 | 含义 | 判据 |
| --- | --- | --- | --- |
| **HITL** | human in the loop | 必须有人在对话里一来一回才做得完 | 少了那个人的回答，这件事根本没有答案 |
| **AFK** | away from keyboard | agent 自己就能做完，人不在也跑得动 | 人回来只需要看结果，不需要中途参与 |

HITL/AFK 与状态角色相关，但不等同。HITL/AFK 描述完成方式；状态角色描述 tracker 上当前由谁继续以及合同是否足够。

**HITL 的活不许 agent 替人回答。** 派一个 subagent 自问自答，得出的结论不作数。这是最容易犯、事后也最难发现的错误——产出看起来完整，只是那个人从没参与过。

**AFK 不附带把东西发出仓库的授权。** 三类动作把东西送到这个仓库之外、别人看得见也收不回的地方：`git push`、推 Wiki、往外部服务写数据。要发的内容用户还没看过就停下来，把内容原样给他看，他点头再发——发出去收不回来，缓存和索引也留着。`/mmw-closing` 第 4 步推 Wiki 之前那道确认，就是这条规矩的落点。

**issue tracker 不在这三类里。** 它是这套流程自己的工作面：建 ticket、贴 agent brief 评论、开 `needs-triage` issue、打标签、关 issue，都照各技能自己的步骤做，不为这条规矩额外增加人工审批关卡。`/mmw-to-spec` 第 7 步要求用户批准 spec，属于该技能明确规定的人工审批关卡。

人工审批关卡是「必须取得用户对指定产物或动作的明确批准，才能执行下一次流程转换」。prototype 走查、spec 定稿、安装包实测和对外发布都可以按各自技能形成关卡实例；它们使用同一个术语和批准责任。HITL/AFK、tracker 状态和验证方式不能替代人工审批关卡。

## 类型：这张 issue 是什么性质

用 GitHub 自带的 `bug` 和 `enhancement`，不另立一套词汇。

## `wayfinder:` 不属于上面两个维度

跑 `/mmw-wayfinder` 时会用到五个标签。它们既不占状态位也不占类型位，只回答「这张 issue 在那张 map 上是什么角色」。

| 标签 | 打在哪张 issue 上 |
| --- | --- |
| `wayfinder:map` | 那张 map 本身。含义是「这是一张 map，不是一件待办」 |
| `wayfinder:grilling` | decision ticket，靠跟人对谈解掉。这是默认类型 |
| `wayfinder:prototype` | decision ticket，要先跑 `/mmw-prototype` 做一个粗糙版本给用户走查 |
| `wayfinder:research` | decision ticket，派 subagent 去查一条事实就能解掉 |
| `wayfinder:task` | decision ticket，某个决定做得出来之前必须先完成的手工操作 |

map 底下的 decision ticket 照常带状态和类型。

**收尾时切出来的 spec issue 同样挂在 map 底下，但不带任何 `wayfinder:` 标签。** 这就是区分办法：带 `wayfinder:<类型>` 的是 decision ticket，不带的是 spec。

## 半路挖到的东西

做任务时发现的另一个 bug、优化机会、或超出本次范围的事：开一张新 issue，打 `needs-triage` 加对应类型标签，主流程不动。不需要「旁路发现」这类专门标签——它是一张独立 issue 这个事实，已经把「不属于本任务」说完了。
