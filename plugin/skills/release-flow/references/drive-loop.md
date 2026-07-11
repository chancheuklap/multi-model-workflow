# Drive Loop · 出包自愈驱动(判断层)

> SKILL 路由到这:manifest 已登记、`release init` 已起。这条路从头到尾就读这一份。
>
> **引擎持有 loop,你是它的手。** 你不「拿着循环在脑子里跑」——你每 turn **重新问引擎**「此刻在哪、完没完」,做它指的**那一件**,把结果**记回它的账**,再问。进度、下一步、完成与否全从引擎的账(`release-state.json`)算:**不靠你记忆、不由你宣布完成、不由你预跑下一步**。
>
> **afk 自驱**:一路自愈,不盯屏、不手敲。**只有引擎 surface**(P0 / 预算熔断 / 诊断不出结构化结果)才停下交人——**停不停是引擎的决定,不是你的**。

## 一 turn = 问 → 做 → 记 → 再问

不是「读一遍这 4 步照做」,是**每一 turn 从头问引擎要下一步**。你在两次 turn 之间不留状态,一切从账上来:

| | 你做 | 命令 |
|---|---|---|
| **问** | `release where` 报此刻:该跑哪个 stage、或已 SUCCESS / PAUSED。这是引擎从账上算的,不是你记的 | `release where` |
| **做** | where 报 `STAGE:<n> RUN:<argv>` → 在构建机跑这个 stage(真出包动作)→ 再跑 `manifest.diagnose` 拿 findings | 仓库执行面(agentflow=Win-PC)+ `manifest.diagnose` |
| **记** | 把 findings 如实记回账:全绿 → `release stage done`;有 failing → `release stage fail` + `release dispatch`(引擎裁决 P0/P1/P2) | `release stage done\|fail` + `release dispatch` |
| **再问** | `release round next` 让引擎进下一轮(到预算/轮次顶自动熔断 surface),然后**回到「问」** | `release round next` → `release where` |

**你从不自己判「跑完了」**——`release exit-check` 才是机器判完成(`DONE` / `NOT-DONE:stages=<剩>` / `PAUSED:<因>`,空账不算 done、状态坏不算 done)。你不宣布,引擎算。

## `release where` 报什么 → 你做哪一件

| where 回显 | 引擎在说 | 你这一 turn 做 |
|---|---|---|
| `STAGE:<n> RUN:<argv>` | 该跑 n | 跑 argv → `manifest.diagnose` → 全绿 `stage done` / 有 failing `stage fail`+`dispatch` → `round next` → 回「问」 |
| `RETRY-STAGE:<n> RUN:<argv>` | 修过了,重跑 n | 同上(引擎自愈后要你重跑,你照跑,不问为什么) |
| `SUCCESS:all stages done` | 全绿,产物就绪 | `release exit-check` 确认 `DONE` → 报用户产物位置 → `release close` |
| `PAUSED:<reason>` | 停在需要人的那一步 | `release receipt` → 把引擎攒的「已试什么+停在哪+为什么」**原样**交人。不硬闯、不替用户拍方向 |
| `FAILED-STAGE:<n>` / `CORRUPT:` | 异常态 | 停,交人(状态坏不硬往下跑) |

## 记回账:引擎裁决,你不判分级、不碰安全墙

**findings 怎么来**:你跑 `manifest.diagnose`(引擎不替你跑 stage 和 diagnose——那是你这只手的活),它吐 `{"findings":[...]}`。

- **全绿** → `release stage done --stage <n>`。
- **有 failing** → 先 `release stage fail --stage <n> --findings <诊断输出>`,再 `release dispatch --stage <n> --findings <同一份>`。**分级、修、熔断全是引擎的事**:

| dispatch 内部(引擎自己做) | 发生什么 | 你的角色 |
|---|---|---|
| **P2** 清单漂移 | 引擎跑 `manifest.derive` 从真相源单向重生消费方,stage 转待重跑 | 无——下一 turn `where` 会让你重跑 |
| **P1** 如漏包 | 引擎派 `manifest.fix_executor` 在隔离 staging 修 → path-gate 只放 editable、触 p0 即拒弃 diff → 过 `manifest.post_fix_gate` 都绿才应用+重跑 | 无——引擎隔离修,你不碰主树、不绕闸 |
| **P0** 硬约束 | 引擎写 PAUSE 停机,不自动修 | 无——下一 turn `where` 报 PAUSED,你走那分支交人 |

**你从不自己判 P0/P1/P2、从不自己改主树、从不绕 path-gate。** 只如实记 findings,引擎裁决。诊断产不出合规结果 → 引擎自己 escalate PAUSE(needs-context),你照 PAUSED 交人。

## 断点恢复 = 正常模式(不是异常处理)

这是 loop 的常态,不是意外:context 断了、隔天回来、换个人接手,**都一样**——`release where` + 账就够从任意点续。where 报此刻该做什么,`release receipt` 报 attempt_ledger(引擎已替你攒的「已试什么」)。**认账不认记忆**:别问「我记得跑到哪了」,问引擎。引擎单飞锁也不让你重开一个新 loop。

## 收尾

- **DONE** → 报用户产物在哪(stage 产物路径)+ `release close` 收束账。一趟绿零修复是正常最好情况。
- **PAUSED** → `release receipt` 精确回执原样交人;**不替用户拍方向、不硬闯**。人处置后 `release resume` 续跑,回到「问」。
- 留痕靠引擎(attempt_ledger + event_sink 落 `runtime/logs/release_loop.jsonl`),你不另攒日志。
