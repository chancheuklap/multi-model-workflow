# Review · 审核 loop(阶段操作指南)

> 审核闸操作指南。审者 = Codex,协调验收 = Claude(你)。审题在 `references/review/`(喂 Codex)。

红线:**审者必须 Codex,不 Claude 审 Claude**;**完工靠 `exit-check` 机器核,不靠 reporter 自报审完**。

---

## 0. 选阶段(决定喂哪份 angle + loop kind)

| 审 | 触发点 | kind | angle 文件 |
|---|---|---|---|
| ① 设计审 | design pass 后 | `review` | `references/review/design.md` |
| ② 计划审 | plan pass 后 | `review` | `references/review/plan.md` |
| ③ 落地审 | 全 plan 合并后(一次) | `contract-gate` | `references/review/plan-impl.md` |
| ④ final | verify 阶段(全合并后) | `review` | `references/review/final.md` |

③ 是便宜机器合同门、不派 Codex 判断,在 build 阶段末跑一次(由 build 流程驱动,本文不展开)。本文讲 ①②④ 三个真审 loop。

## 1. 主线程:一条命令起审 → 抽清单 → 派协调帮手(①②④)

1. **一条命令起审**(把 init loop + 配审题 + 出 brief 收成一步):
   ```bash
   mmw review start --stage <design|plan|final> --source "<源意图路径/待审内容>"
   ```
   `--stage` 按当前审闸阶段(design/plan)或 verify(final);`--source` 用 `mmw where` 报的 `review_source`。它 init `kind=review` 的 loop、定好该阶段审题(`references/review/<阶段>.md` + `quartet.md`)、**打印好协调帮手 brief**。你照打印的往下走。
2. **抽覆盖清单**(判断,留你做):从设计/计划/issue/意图逐条抽"要审到什么",`source` 记从哪份文档哪行抽。客观项(② issue 数=plan 数、④ 意图逐条)标清楚:
   ```bash
   mmw loop checklist add --item "<要审到的维度>" --source "<doc:line>"   # 逐条
   mmw loop attendance --mode <attended|afk>
   ```
3. **派审核协调帮手**(Claude sub-agent,SubagentStop 受 guard-loop 看守):用 `review.sh` 打印的 brief 原样派。brief 已含派两个独立 Codex(`codex exec --sandbox read-only` 喂 quartet+角度、续接 `codex exec resume`)、亲验后 `checklist cover` / `finding add`、收敛与熔断 `surface`、清单全绿+无 Critical 前不准停。**只给 Source + 点名审题,别塞你自己的问题清单。**

## 2. 主线程:收口(协调帮手停下后)

读 `loop-state.json` 的 `pause` 和 `findings`,按情况 handoff(结论词由 Gap 决定):

- `pause != null`(surface 冒泡)→ 按 `reason` handoff `needs-redirection` / `needs-context`,交用户。
- `exit-check` = DONE 且无 accepted 缺陷 → `mmw handoff --conclusion pass`,进下一阶段。
  - **仅 ④final(verify 阶段):handoff `pass` 前先写终审报告**到 `docs/<slug>-final-review.md`(照 `mmw where` 的 `then` 钉 `--produced`),closing 阶段照单读它收口。三段:
    1. **终审结论**:verdict + 两基线各自结果(回归/意图/跨 plan;独立代码审)+ 放行的 waived 项(环境/账号 gate,带 owner)。
    2. **意图清单逐条**:最初 design + issue 提取的每条可验证 intent → 达成/未达成 + 证据(`file:line` 或测试名)。
    3. **业务语言交付摘要**(给项目负责人看,**不用技术术语**):新增能力(每条一个用户可感知的行为变化,如「用户现在可以用手机号登录,15 秒内完成」,不列函数名/文件路径/类名)· 验证证据(跑了哪些验收、什么结果)· 残余风险(已知没覆盖的、需人盯的,诚实列不藏)。
    ①②审是闸、不产文件,这条不适用。
- 有 accepted finding → 按 Gap 选结论词(`needs-repair` 是**原地返工当前阶段**;回上游别的阶段必须 `needs-redirection --to-phase <阶段>`):
  - 缺陷在**当前被审阶段**(①审=design、②审=plan,gate 的 cur_phase 就是它;④final 的代码缺陷可在 verify loop 里就地修)→ `needs-repair`,改完 handoff 重审。
  - 根因在**更上游阶段**(②审发现 design 问题、④final 撞破 plan/design)→ `needs-redirection --to-phase <design|plan|build>`,回那阶段改。
  - Direction(解错问题)→ `needs-redirection`;Context(缺输入)→ `needs-context`。
- 超熔断仍不收敛 → `mmw handoff --conclusion blocked`,带经过上报。

**Critical 必须修掉**才能让对应阶段往下走。

## 3. 守住的红线

- 审者 Codex,不用 `codex review`(走它内置提示词、绕过我们方法论),用 `codex exec` 喂我们的 quartet+angle。
- 每条 finding 引 `file:line` 原文才采信;协调帮手亲验后才 accept,主线程落 handoff 前再核承重的。
- ③ 不判断、只核合同;重判预算砸 ④final。
