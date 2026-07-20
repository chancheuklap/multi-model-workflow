# Review · 审核(阶段操作指南)

> 审核操作指南。**主线程直接派审者**;审查方法 + 各 stage 角度单源在已装的 **`worktree-review` skill**。plugin 侧只留 `plan-impl.md`(③合同门)与本文(编排)。
>
> 谁审 / 几路视角 / 模型档,全由 `mmw review start` 机器生成进 brief——**照 brief 派即可**,本文不复制派发矩阵(免漂移)。
>
> **审不记账**:没有覆盖清单登记、没有轮账。收口看产物——findings 原样落盘留痕文件,亲验标处置,文末写总 verdict;审闸 pass 时引擎只核「留痕文件在且含 verdict」(报告在 = 审真跑过,这是写者≠审者的证据面);质量与 Critical 处置是你的判断,机器不数你的动作。

红线:**写者≠验者**(设计/计划作者与审者模型不同家)。

---

## 0. 触发方式

| 审 | 触发 | stage | 视角 |
|---|---|---|---|
| 设计预审 | design 自检过后**agent 自起**(不是闸;结果给用户参考,人闸是 `/approve-design`) | `design` | 轴A 设计内容 / 轴B 项目对齐 |
| ② 计划审 | plan pass → 引擎审闸(phase 冻住,`mmw where` 吐 `review_start` 照跑) | `plan` | 轴A 覆盖与质量 / 轴B 合规与交叉验证 |
| ④ final | build pass → 引擎审闸(同上) | `final` | 基线1 回归+意图+跨plan / 基线2 独立代码审计;**审者数 review.sh 机器判**:small-change/bug=1 · develop=2 或 4(按 Complexity / diff) |

另有 **③ 落地合同门**:build 内部机器合同检查(`--stage plan-impl`,不派审者)——anchors 节为空脚本直接放行;有实体合同由 build 流程驱动(build-b B5)人工核,方法论在 `plan-impl.md`。

## 1. 一条命令起审 → 直接派审者

1. ```bash
   mmw review start --stage <design|plan|final> --source "<源意图路径/待审内容>"
   ```
   审闸内直接用 `mmw where` 吐的 `review_start` 整行(stage 与 `--source` 都填好)。它出**派发指南**(`状态平面/review-brief.md`),你照打印的往下走。
2. **直接派审者**:读 brief 按「派审者」段派(Claude 会话内 sub-agent / Codex 后台 CLI),审者各自干净 context 并行起、读 `worktree-review` skill 出结构化 findings。**别给审者 plugin 内路径、别塞你自己的问题清单。**
3. **留痕(收口的硬核)**:全部审者的结构化 findings **原样落盘**到 `docs/reviews/<slug>-<stage>.md`(不重写、不摘要);亲验后每条的 verdict/处置就近标在该条下,文末写一句总 verdict。收口只回读 verdict 段,findings 全文压在留痕里、不长驻主线程 context。留痕是过程产物(docs/.gitignore 已忽略,随 worktree 删)。

## 2. 收回亲验 + 处置(裁判权在你,不在审者)

审者是劳动力不是信源,也**不是放行权人**。你的工作不是转发 findings,是逐条裁判后只把 `accepted` 送去修。

### 2.1 先坐实,再裁判
对每条 finding:
1. 自己 Read/grep/跑坐实 locator;引不出 `file:line` → 降置信或 `needs-evidence`/`rejected`,不 accept。
2. 对照 design / issue / plan 范围,标它是不是本轮 scope。
3. 过下面四问,再写处置(处置词见 2.2)。**禁止**未亲验就 accept;禁止把审者原文原样转给工人。

### 2.2 处置四问(每条必过)
1. **是不是过度设计 / 过度考虑?** 为假想未来留的抽象、纯品味、无当前用户路径、"可以更优雅但现状可维护"→ 倾向 `waived` 或 `rejected`,不进返工。
2. **不修的真实后果有多严重?** 谁在什么场景下受伤(用户可见坏行为 / 数据钱权限 / 发布不可逆)?说不清受伤面 → 不能当 Critical/承重 Important accept。
3. **边际收益多大?** 修完是否改变用户可见行为或承重风险,还是只让报告更好看?收益只在品味 → `waived`。
4. **现在修是否值得?** 是否必须占用本轮返工预算?能否 spinoff / 开 issue / 写进终审 waived 清单带 owner?第 2 轮起还要多问:**相对上轮,这条新增了什么承重风险?** 说不清增量 → 默认不 accept。

### 2.3 处置词(就近标在该条下)
| 处置 | 含义 | 驱动返工? |
|---|---|---|
| `accepted` | 事实成立 + 本轮值得修 | 是 |
| `rejected` | 事实不成立 / 证据不足 / 误读 | 否(写一句理由) |
| `duplicate` | 与另一条重复 | 否(指向保留条) |
| `needs-evidence` | 可能成立但未坐实 | 否;补证前不修不争 |
| `waived` | 可能成立,但过度设计 / 低 ROI / 超 scope / 非 blocking | 否;理由必填,可 `mmw spinoff` 或记入终审 waived |

硬纪律:
- **只有 `accepted` 能驱动 `needs-repair`**。
- **Critical**:必须 `accepted`,或有理 `rejected`/`waived`(waive Critical 必须写清「为何不构成放行风险」)。
- **Minor / blocking=no**:默认 `waived` 或 spinoff,不默认 accept。
- **Important**:四问后仍承重才 accept;否则 waived 并写理由。
- 多审者重复报同一点:合并为一条处置,别让工人修两次。

### 2.4 收口结论词
- **无开口 Critical**(已修或有理 reject/waive,留痕看得见)且无未修 `accepted` → `mmw handoff --conclusion pass`(引擎核留痕在且含 verdict)。
- 有 `accepted` 缺陷 → 按 Gap 选结论词:
  - 缺陷在**当前被审阶段**(②审=plan、④final=build)→ `needs-repair`,改完 handoff 重审。**④final 的代码缺陷**:`mmw where` 指回 build(build-b 有返修入口),照 accepted 的 `file:line`+remediation 派全新写码工人定点修,修完 handoff pass 重进 ④;**复审 brief 会带上轮留痕,新审者只验修复+回归**。
  - 根因在**更上游**(②审发现 design 问题、④final 撞破 plan/design)→ `needs-redirection --to-phase <design|plan|build>`(涉已确认设计的改动,改完请用户 `/approve-design` 重新确认)。
  - Direction(解错问题)→ `needs-redirection`;Context(缺输入)→ `needs-context`。
- **不要**因为还剩 Nit/waived 就 needs-repair。放行标准:**整体在变好且无未处置 Critical / 无未修 accepted 承重项**,不是完美。

### 2.5 打转与轮次天花板(引擎强制,你要会读)
- **指纹守卫**:`needs-repair` 时引擎比对本轮与上一轮留痕的 **accepted** findings 指纹;连续实质重合 → `GUARD=repair-fingerprint-repeat`(afk/attended 交人,unattended 硬停)。被指打转先想「修错地方还是不该 accept」,别原样再修。
- **绝对轮次**:审闸返工时 `repair_count` 超过 `loop_guards.max_repair_rounds`(默认 3)→ `GUARD=repair-round-cap`,交人或硬停。到顶后亮:已 accepted 未收敛项 / 已 reject·waive 项 / 建议(放行带 risk / 缩 scope / 回 design),**不要**再问"要不要再修一轮"。
- 收敛:无新高置信 **accepted** = 收敛;反复不收敛 → 交人,别硬磨。

### 2.6 ④final 报告
pass 前先写 `docs/<slug>-final-review.md`(照 `mmw where` 的 `then` 钉 `--produced`),三段:终审结论(verdict + 两基线结果 + **waived 项带 owner 与理由**)· 意图清单逐条(达成/未达成 + 证据)· **业务语言交付摘要**(新增能力/验证证据/残余风险,不用技术术语)。

## 3. 守住的红线

- 写者≠验者:设计预审与④用 Codex+Claude 跨模型、②计划审用 Claude(计划是 Codex 写的)。不用 `codex review`(内置提示词绕过方法论)。prompt 一律指向已装 `worktree-review` skill。
- 每条 finding 引 `file:line` 原文才采信;主线程亲验 + 四问后才 accept。
- ③ 不判断、只核合同;重判预算砸 ④final。
- 审者给证据,你给放行;你不是审者的传声筒。
