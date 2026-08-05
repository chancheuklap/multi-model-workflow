# map 收尾

frontier 上一张 ticket 都不剩了。收尾就是把这张 map 结束掉：清算 `Not yet specified` 一节剩下的条目、把这张 map 上做出的决定各自归位、切出 spec、关掉 map issue。

本文件只在拥有 map 分支的任务中执行。`mmw task state` 必须显示当前 checkout 已绑定 map 分支；不满足时停止并让用户恢复原 map 任务。然后确认所有 decision ticket 任务结果已经通过 `mmw result verify` 并集成到 map 分支，再确认 `mmw issue frontier <map 编号>` 没有输出。Decision ticket 任务不能直接执行 map 收尾。

## 1. 清算 `Not yet specified` 剩下的条目

把 map 的 `Not yet specified` 一节剩下的条目原样列给用户看，问他里面还有没有会挡住后续工作的。

用户点出会挡路的，就用 `mmw issue create --parent <map 编号> --label wayfinder:<类型>` 建成新的 decision ticket，再用 `mmw issue link` 连好阻塞关系，然后停——处置见本文「下一步」一节。用户没点出来的原样留在 `Not yet specified` 一节里，跟着 map issue 一起关掉。

## 2. 决定各自归位

map 本身不上 Wiki，但 map 上记下的那些决定不能随任务一起消失。按类型分开落到仓库里：

| 产物 | 去哪 | 为什么 |
| --- | --- | --- |
| 按 `/mmw-domain-modeling` 的三项 ADR 判据全部成立的决定 | ADR，落点与编号方案跑 `mmw domain adr-next` 取，写法见 `/mmw-domain-modeling` | 改代码时同一次 diff 就能看见相关决定，Wiki 看不见 |
| 考察过但决定不做的方向 | `.out-of-scope/`，一个概念一个文件 | 分诊时按概念相似度查它，防止同一个需求换个说法再提一遍 |
| 谈出来的术语 | 领域文档，落点跑 `mmw domain path` 取 | 项目自己的话怎么说，要跟代码一起演进 |
| 用户走查过的 prototype 资产 | `docs/prototypes/<slug>/` | 它是逻辑决定和视觉合同的 primary source；正式实现吸收已确认决定，并移入逻辑 branch 的可移植模块 |
| 实测出来的外部事实与原始产物 | `docs/evidence/<slug>/` | 记的是外部世界的表现，spec 归档之后仍然成立。重测要花钱花时间 |
| 其余可回退的决定 | 被 spec 的 `Implementation Decisions` 吸收 | 不值得单独归档 |
| map 本身 | 关掉即止 | 它是按走过顺序记的过程日志，含死路，价值在过程中 |

这些内容都写在 map 任务分支上，随 effort 一起合回最终目标分支，中途不提前合。

走 map 的过程中该写的已经写了，这一步是补漏：逐条重读 map 的 `Decisions so far` 一节，按 `/mmw-domain-modeling` 的完整 ADR 判据重新检查。三项判据现在全部成立的，补一份 ADR。

## 3. 切出 spec

map 按**决定**组织，spec 按**能独立设计和实现的一块功能**组织。这一步把已经定好的决定重新分组，看哪些凑起来是一份做得下去的东西。**只分组，不重新讨论任何决定。**

spec 是 map 的可读综合版：map 的 `Destination` 变成 spec 的问题陈述，`Decisions so far` 里的每一条变成 spec 的 `Implementation Decisions`，`Out of scope` 原样继承。Wiki 上只留这份综合版，不留原始日志。

一组一份 spec，各建一张 issue 挂在 map 底下，正文写清楚两件事：这份 spec 交付什么，它依赖 map 的 `Decisions so far` 一节里的哪几条。spec issue 跟 decision ticket 同处一层，靠**带不带 `wayfinder:` 类型标签**区分：decision ticket 带，spec issue 不带。

切出来只有一份也照样切出去走下去，不回头重来。

解决一张 decision ticket 后也可以提前切 spec，判据见 [walking.md](walking.md) 的“判断能否提前切出 spec”一节。

## 4. 关掉 map

关掉 map issue。把第 1 步到第 3 步写下的文件提交进 map 分支。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 第 1 步用户点出还有会挡路的条目，已经建成 decision ticket | **停**：报新建了哪几张 ticket（用名字，不用编号），让用户另开一个会话认领 |
| 决定归位完、spec 切完、map issue 关掉 | **停**：报这张 map 收尾了、切出了哪几份 spec（用名字，不用编号），说明每份 spec 各开一个会话去做 |

每份 spec 使用从 map 分支派生的独立任务。spec 任务完成后交回分支名、HEAD SHA 和 map 基点 SHA，由 map 任务用 `mmw result verify` 和 `mmw result integrate` 集成。整个 effort 完成前不合回最终目标分支；map 分支是这些 spec 的汇合点。
