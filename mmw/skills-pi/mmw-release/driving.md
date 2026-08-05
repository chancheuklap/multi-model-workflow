# 驱动一个产品出包

`/mmw-release` 第 3 步读这一份。到这里时这个产品的循环已经起好，或者上一次的循环还留在那儿可以续。

**release engine 持有循环，你执行它给出的动作。** 进度、下一步、修复次数和完成状态全由 release engine 计算。不从会话记忆续跑，不自己挑下一个 release stage，不在 release receipt 之外另记一份「已经试过什么」。

## 状态表：`where` 说什么就做什么

每一轮先跑：

```bash
mmw release where
```

只处理这一次的输出，不预判下一步：

| 回显 | 做什么 | 要不要交回判断 |
| --- | --- | --- |
| `STAGE:<名字>` 或 `RETRY-STAGE:<名字>` | `mmw release stage run --stage <名字>`。release engine 自己展开参数、路由远端构建、跑诊断、按退出码写结果并记录 ReleaseFinding 产物 | 不用 |
| `SUCCESS:all stages done` | `mmw release exit-check` 必须回 `DONE`，然后 `mmw release close` | 不用。`exit-check` 不是 `DONE` 却报成功，说明 release engine 出错，别宣布成功 |
| `PAUSED:needs-context` | 看本文「自己处理：缺信息的暂停」。这不是终点 | 处理两次仍不成才停下并交给用户 |
| `PAUSED:needs-redirection` | 读 `mmw release receipt`，原样交用户 | 要。这是人工审批关卡：批准对象是 release receipt 记录的暂停原因和续跑影响，批准人是用户，通过凭据是用户明确批准按该影响续跑，通过后才允许 `mmw release resume` |
| `CORRUPT:` / `FAILED-STAGE:` / `NO-STAGES:` | 读 `mmw release receipt`，不运行 release stage，不 `resume` | 要 |
| 别的输出，或命令本身报错 | 不猜状态，不重新 `init` | 要，带上原始输出 |

跑完一个 release stage 立刻重新问一次 `where`，直到状态表给出终态。**不要每问一次就停下来跟用户汇报一句**，那是把连续的机械动作切成几十轮对话。

## 一个 release stage 失败之后

`stage run` 失败时 release engine 已经在内部跑完诊断并分好级了。看 `where`：

- 报 `PAUSED` —— release engine 已经把它拦下来了，读状态输出，别派修。
- 报 `RETRY-STAGE` —— 跑一次 `mmw release dispatch --stage <名字>`，让 release engine 按分级裁决怎么修。ReleaseFinding 产物由 release engine 从 release receipt 读回，你不用猜路径。
- `dispatch` 之后 `where` 仍是 `STAGE` 或 `RETRY-STAGE` —— 跑一次 `mmw release round next`，然后回到状态表重跑那个 release stage。

`round next` 记的是「已经处理过一次」，不是「跑过一个 release stage」。全绿走完不消耗轮次。

**你不判 P0、P1、P2**，不改工作树，不绕路径护栏，不自建第二个执行器。ReleaseFinding 分级和自动修复提交属于 release engine。人工审批关卡由主 agent 执行：主 agent 取得用户批准，并在通过后运行 `mmw release resume`。

## 自己处理：缺信息的暂停

`PAUSED:needs-context` 是 release engine 缺信息、机械判不了，需要你补判断。**能自己解决的不要等人。**

1. `mmw release receipt` 读已经试过什么；从最近一次记录里的日志位置读 release engine 日志、构建机回传的日志和 ReleaseFinding 原文。
2. 自己诊断根因。判断依据要能引用日志原文，不猜。
3. 能处理就处理：改代码、改配置照常提交到当前分支（你是主 agent，路径护栏只约束 release engine 派出的自动修复，不约束你正常的开发提交）；环境类问题（网络、构建机忙）等一等或者把环境修好。
4. 处理完运行 `mmw release resume` 续跑。HEAD 变了 release engine 会自动全量重验。
5. **同一个根因处理两次仍不成，或者根因涉及计费、合同、受保护路径、需要用户决定的业务问题，停下来写清楚并交给用户。** 不无限打转。

## 收尾

- `SUCCESS` 不等于口头成功。只有 `mmw release exit-check` 回 `DONE` 才能说安装包就绪，随后 `mmw release close` 收束。
- 安装包路径只从刚跑完那个 release stage 的输出或产物记录里读。状态输出没记路径就如实说「状态输出没有记安装包路径」，不要按目录约定猜一个。
- `close` 会留下一份交付记录（产品名加出包时的 commit），`/mmw-release` 第 4 步靠它核对几个包是不是同一份代码。**不要手工删它。**
- `CORRUPT`、`FAILED-STAGE`、`NO-STAGES` 一律不运行下一个 release stage，不自动 `resume`。release receipt 是「已经试过什么」的唯一事实来源，原样交用户判断。
