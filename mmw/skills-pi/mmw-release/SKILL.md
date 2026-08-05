---
name: mmw-release
description: 把已经改完并通过终审的代码出成正式安装包，失败时由 release engine 诊断并自动修复。用户说要出包、要打包、要发某个产品的新版本时用它；终审过了、这次改动碰了带 release adapter 的产品时也移交这里。
---

把这次改动影响到的每个产品出成安装包，出到可以交给用户去装为止。

release engine 是确定层：状态机、把失败分成三级、路径护栏、同根因熔断、预算熔断全在 `mmw release` 里。**你是判断层**：认这次要出哪几个产品、读状态执行 release engine 给出的动作、诊断 release engine 无法判断的暂停。你不判分级，不绕护栏，不自建第二个执行器。

## 1. 前置条件

四项都满足才开工，缺一项就停下来说清是哪一项。

| 检查 | 怎么查 |
| --- | --- |
| 终审跑过，采信的 findings 都修完并复审通过 | `.reviews/` 里有终审报告；采信项各自有对应的修复提交 |
| 工作区干净 | `git status --porcelain` 是空的。release engine 拒绝把自动修复混进你没提交的改动里 |
| 这个仓库配了出包 | `mmw` 的配置里有 `paths.release`，且仓库里能找到至少一份 release adapter（下一步） |
| 你在已绑定的任务 worktree 里 | `mmw task state` 输出以 `bound` 开头 |

**没有 release adapter 不是失败。** 有 spec 的任务移交 `/mmw-closing`。只有 agent brief、没有 spec 的任务直接交回用户集成。

## 2. 认这次要出哪几个产品

release adapter 由仓库自己登记，一个产品一份，文件名以 `.release-adapter.json` 结尾。先列出全部：

```bash
grep -rl '"product"' --include='*.release-adapter.json' .
```

再判断这次要出哪几个：**看这次改动碰了哪些路径**（`git diff --name-only <本次任务的第一个提交>^..HEAD`），对照每份 release adapter 里 `build_target.desktop_dir` 与 `asset_roots` 声明的范围。碰到了就要出。

判不准就问用户，不要漏出一个——漏了的那个产品，用户装到的还是旧代码。

按这个形状亮一次清单，**不等回应直接往下走**：

```
| 产品 | release adapter | 这次为什么要出它 |
```

## 3. 一个产品一轮，按 driving.md 驱动

对第 2 步定下的每个产品，依次：

```bash
mmw release init --manifest <release adapter 的绝对路径>
```

然后读 [driving.md](driving.md) 整份，照它驱动到安装包就绪。**驱动合同只有那一份**，本文不复述。

一个产品收束（`mmw release close`）之后再起下一个。不要同时起两个——状态文件一个仓库只有一份。

## 4. 核对几个包是不是同一份代码

出完全部产品之后做这一步。**出一个产品的过程中 release engine 可能自动修复并产生新提交**，于是先出的那个产品的包，用的已经不是最终代码了。

```bash
git rev-parse HEAD
cat "$(git rev-parse --path-format=absolute --git-common-dir | xargs dirname)"/<.mmw.json 的 paths.release>/delivered/*.json
```

交付记录落在**主仓库根**，不在当前这棵任务 worktree 里——它比对的是几次出包之间的 commit，worktree 收尾就删，落在树里的记录活不过一次任务。

每份交付记录里的 `source_commit` 都等于当前 HEAD，才算这批包是同一份代码。

有对不上的：那个产品重出一遍（回第 3 步，只重出对不上的那些）。重出之后再核对一次——重出的过程可能又产生新提交。

**混着不同 commit 的包一个都不能交给用户。** 他装上去会发现两个产品的行为对不上，而且查不出原因。

## 5. 交给用户实测

安装包在哪，只从 release engine 状态输出里读，不按目录约定猜。状态输出没记路径就如实说「状态输出没有记安装包路径」。

把这些交给用户：出了哪几个产品、每个包在哪、这批包对应哪个 commit。

**这是安装包实测的人工审批关卡。** 批准对象是这批安装包及其对应 commit，批准人是用户，通过凭据是用户明确报告安装和目标行为实测通过，并明确批准这批安装包。通过后才走下一步；不通过就按他报的问题回 `/mmw-implement` 修，修完重走终审和本技能。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 第 1 步查出这个仓库没配出包，而且有 spec | **移交**：`/mmw-closing`。这次任务不出包 |
| 第 1 步查出这个仓库没配出包，而且只有 agent brief | **停**：报告这次任务不出包、当前分支 HEAD 和验证证据。分支已就绪，交回用户集成 |
| 第 5 步用户实测通过，而且有 spec | **移交**：`/mmw-closing`，把 spec 与 plan 归档、分支交回他合并 |
| 第 5 步用户实测通过，而且只有 agent brief | **停**：报告安装包、对应 commit 和用户实测结论。任务没有 spec，不走 `/mmw-closing`；分支已就绪，交回用户集成 |
| 第 5 步用户报了问题 | **移交**：`/mmw-implement`，把他报的现象和复现步骤带过去。修完要重走终审 |
| 第 4 步有产品的 commit 对不上 | **自己继续**：只重出对不上的那几个，回第 3 步 |
| 驱动中 release engine 报了 `PAUSED:needs-redirection` | **停**：把 release engine 状态输出原样给用户，说清卡在哪个产品的哪个 release stage、已经试过什么。不要自己 `resume` |
| 驱动中 release engine 报了 `PAUSED:needs-context` | **自己继续**：按 [driving.md](driving.md) 的「自己处理：缺信息的暂停」办。同一个根因处理两次仍不成才停下并交给用户 |
| 第 1 步工作区不干净 | **停**：列出没提交的文件。release engine 拒绝把自动修复混进它们里面，这是防止你的改动被自动提交带走 |
| 第 1 步终审没跑，或还有采信的 findings 没修完 | **停**：说清缺哪一样。回 `/mmw-implement` 第 7 步发起终审，或按 `/mmw-review` 第 7 步复审 |
| 第 2 步判不准这次要出哪几个产品 | **停**：把全部产品和这次改动碰的路径列给用户，让他点 |
