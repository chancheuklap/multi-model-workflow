# Issue 标签

两个维度，互不干涉：一张 issue 各带一个。

## 状态：这张 issue 现在够不够清楚

技能里说到某个角色时，用右列的真实标签字符串。

| 技能里的角色 | 本仓库的标签 | 含义 |
| --- | --- | --- |
| `needs-triage` | `needs-triage` | 还没评估过，不知道该不该做、怎么做 |
| `needs-info` | `needs-info` | 缺输入，等人补 |
| `ready-for-agent` | `ready-for-agent` | 已写清楚，可以直接派工人无人值守跑 |
| `ready-for-human` | `ready-for-human` | 必须人做，不派工人 |
| `wontfix` | `wontfix` | 决定不做 |

**派工人前必须是 `ready-for-agent`。** 这是唯一一个机器可核的「够清楚了」信号，无人值守时靠它挡住模糊 issue。

## 类型：这张 issue 是什么性质

用 GitHub 自带的 `bug` 和 `enhancement`，不另立一套词汇。

## `wayfinder:map` 不属于上面两个维度

跑 `wayfinder`（把 effort 画成一张决策 map 的技能）时，那张 map issue 打 `wayfinder:map`。它既不占状态位也不占类型位，只是「这张 issue 是一张 map，不是一件待办」的记号。map 底下的 decision ticket 照常带状态和类型。

## 半路挖到的东西

做任务时发现的另一个 bug、优化机会、或超出本次范围的事：开一张新 issue，打 `needs-triage` 加对应类型标签，主流程不动。不需要「旁路发现」这类专门标签——它是一张独立 issue 这个事实，已经把「不属于本任务」说完了。
