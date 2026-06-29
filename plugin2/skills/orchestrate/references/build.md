# Build · 自循环落地(阶段操作指南)

> 主线程进 build 阶段加载本文。落地 = loop engineering 的 `kind=execution` 实例:派一个 Claude 帮手按对齐好的计划自驱 TDD,看守 hook 保证做完才停。机制全貌见 `plugin2/design/loop-engineering.md`(单源)。

阶段目标:把 ②计划审过的 plan **完整落地、不偏离设计**。这是用户放权自主跑的阶段——对齐在前(design/plan 审过),执行在此放手。

**红线:**
- 帮手(worker)**只改代码、不碰 `docs/`**(设计/计划是上游权威,executor 禁改)。
- **每个 Pack 一次提交**,commit message 含 `Pack N.M`(record-step hook 据此记步完成;不写就不记、看守会顶回)。
- **afk 放权只动软停**:缺输入 / 方向疑(surface)永远停下抛你;merge/deploy 永远要人批(guard-redline,在收尾不在这)。

---

## 1. 进 + 起落地 loop

`flow.sh where` → `prev_outputs` = plan 阶段钉的 plan 目录。读该目录的 plan 文档拿 Task Pack 清单 + 依赖序。然后起 loop、把 Pack 展开成步账:

```bash
bash "${SCRIPTS}/loop.sh" init --kind execution
bash "${SCRIPTS}/loop.sh" attendance --mode <attended|afk>          # 放权跑设 afk
bash "${SCRIPTS}/loop.sh" step add --id <N.M> --desc "<Pack N.M 标题>"   # 逐 Pack,id 用 Pack 号 N.M
```

多份 plan:按 plan 间依赖序,一份一份过(每份:落地 loop → ③合同门)。互不依赖的 plan 可并行派 worker(共享工作树,Pack 号不撞)。

## 2. 派落地 worker(tdd-executor,后台)

派 `tdd-executor`(`subagent_type: "tdd-executor"`,`run_in_background: true`),给它(且只给它)这份 plan 需要的:

> Source:plan 文档路径 + Global Constraints。按 plan 内依赖序逐个 Task Pack 落地,严格 TDD:**写失败测试 → 确认真失败 → 最小实现 → 确认真通过 → 提交**。
> **每个 Pack 一次提交,message 含 `Pack N.M`**(进度靠它记)。只改代码,**不碰 `docs/`**。
> 停下规则(不自己问用户,抛回主线程):有合理默认的判断 → `loop.sh softstop --question ... --at-step <N.M> --default <你的默认>`;真缺输入 / 怀疑方向错 → `loop.sh surface --kind <needs-context|needs-redirection> --question ... --at-step <N.M>`。
> 全 Pack 做完再停;没做完想停会被看守顶回来续。

worker 自驱期间:提交 → record-step hook 自动记 `step done`;`guard-loop`(SubagentStop)在 steps 没全 done 时 `exit 2` 顶它回去续。

## 3. 暂停怎么处理(放权与盯防的融合)

| worker 写了 | attended(你在) | afk(放权) |
|---|---|---|
| `softstop`(有默认的判断) | loop-state `pause` → 你 `AskUserQuestion` → `loop.sh resume` → `SendMessage` 把答复续给同一帮手(context 原封) | worker 自决 + 写 `decisions` 留痕,继续(不偷跳) |
| `surface`(缺输入/方向疑) | 永远停 → 抛你拍 | 同左,**afk 也停** |

续接靠 `SendMessage` 续**同一**帮手(零重读),不重派、不重做已提交的 Pack。

## 4. ③ 合同门(每份 plan 落完)

一份 plan 全 Pack 提交后,起便宜合同门(不派 Codex 判断):

```bash
bash "${SCRIPTS}/review.sh" start --stage plan-impl --source "<plan 目录>"
```

按打印提示:列待提交 Pack(`step add`)+ 跨 plan 合同清单(`checklist add`)→ 逐条机器核合同兑现(`checklist cover`)→ 全齐 `exit-check` DONE。合同不达 → 回本 plan 落地(落地自己的轮上限);合同根上错 → 升级。

## 5. 钉产出 → handoff

全部 plan 落地 + ③门过后:

```bash
bash "${SCRIPTS}/flow.sh" handoff --conclusion pass --produced "<分支提交范围,如 base..HEAD>"
```

→ flow advance 到 verify(④终审 loop)。落地中途撞破设计/计划(根因在上游)→ `--conclusion needs-repair`(回 plan)或 `needs-redirection`(方向,交用户);卡死或超轮上限 → `blocked`。

## 6. 守住的红线

- worker 不改 `docs/`;每 Pack 一提交且 message 带 `Pack N.M`,否则看守顶回。
- 完工靠 steps 全 done(看守机器核),不靠帮手自报"做完了"。
- afk 只放软停;surface 永远停;merge/deploy 永远要人批(收尾阶段的 guard-redline)。
