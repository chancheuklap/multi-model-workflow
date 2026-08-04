# 驱动一个产品出包

`/mmw-release` 第 3 步读这一份。到这里时这个产品的循环已经起好，或者上一次的循环还留在那儿可以续。

**引擎持有循环，你是它的手。** 进度、下一步、修复次数、成没成，全由引擎的状态算出来。不从会话记忆续跑，不自己挑下一个阶段，不另记一份「已经试过什么」的账。

## 状态表：`where` 说什么就做什么

每一轮先跑：

```bash
mmw release where
```

只处理这一次的输出，不预判下一步：

| 回显 | 做什么 | 要不要交回判断 |
| --- | --- | --- |
| `STAGE:<名字>` 或 `RETRY-STAGE:<名字>` | `mmw release stage run --stage <名字>`。引擎自己展开参数、路由远端构建、跑诊断、按退出码写结果并记 findings | 不用 |
| `SUCCESS:all stages done` | `mmw release exit-check` 必须回 `DONE`，然后 `mmw release close` | 不用。`exit-check` 不是 `DONE` 却报成功，那是引擎出错，别宣布成功 |
| `PAUSED:needs-context` | 看本文「自己处置：缺信息的那类暂停」。这不是终点 | 处置两次仍不成才交人 |
| `PAUSED:needs-redirection` | 读 `mmw release receipt`，原样交用户 | 要。这是保护性暂停：碰了受保护路径、熔断、预算烧完，都不许自己续 |
| `CORRUPT:` / `FAILED-STAGE:` / `NO-STAGES:` | 读 `mmw release receipt`，不跑阶段、不 `resume` | 要 |
| 别的输出，或命令本身报错 | 不猜状态，不重新 `init` | 要，带上原始输出 |

跑完一个阶段立刻重新问一次 `where`，直到状态表给出终态。**不要每问一次就停下来跟用户汇报一句**，那是把连续的机械动作切成几十轮对话。

## 一个阶段失败之后

`stage run` 失败时引擎已经在它内部跑完诊断并分好级了。看 `where`：

- 报 `PAUSED` —— 引擎已经把它拦下来了，读状态输出，别派修。
- 报 `RETRY-STAGE` —— 跑一次 `mmw release dispatch --stage <名字>`，让引擎按分级裁决怎么修（findings 它自己从账本读回，你不用管在哪）。
- `dispatch` 之后 `where` 仍是 `STAGE` 或 `RETRY-STAGE` —— 跑一次 `mmw release round next`，然后回到状态表重跑那个阶段。

`round next` 记的是「已经处置过一次」，不是「跑过一个阶段」。全绿走完不消耗轮次。

**你不判 P0、P1、P2**，不改工作树，不绕路径护栏，不自建第二个执行器。分级、修复提交、人工门禁都属于引擎。

## 自己处置：缺信息的那类暂停

`PAUSED:needs-context` 是引擎缺信息、机械判不了，需要你补判断。**能自己解决的不要等人。**

1. `mmw release receipt` 读已经试过什么；从最近一次记录里的日志位置读引擎日志、构建机回传的日志和 findings 原文。
2. 自己诊断根因。判断依据要能引用日志原文，不猜。
3. 能处置就处置：改代码、改配置照常提交到当前分支（你是主 agent，路径护栏只约束引擎派出的自动修复，不约束你正常的开发提交）；环境类问题（网络、构建机忙）等一等或者把环境修好。
4. 处置完 `mmw release resume` 续跑。HEAD 变了引擎会自动全量重验。
5. **同一个根因处置两次仍不成，或者根因涉及计费、合同、受保护路径、要用户拍板的业务决定 —— 停下来写清楚交人。** 不无限打转。

## 收尾

- `SUCCESS` 不等于口头成功。只有 `mmw release exit-check` 回 `DONE` 才能说安装包就绪，随后 `mmw release close` 收束。
- 安装包路径只从刚跑完那个阶段的输出或产物记录里读。状态输出没记路径就如实说「状态输出没有记安装包路径」，不要按目录约定猜一个。
- `close` 会留下一份交付记录（产品名加出包时的 commit），`/mmw-release` 第 4 步靠它核对几个包是不是同一份代码。**不要手工删它。**
- `CORRUPT`、`FAILED-STAGE`、`NO-STAGES` 一律不跑下一个阶段、不自动 `resume`。状态输出里的记录是「已经试过什么」的唯一来源，原样交用户判断。
