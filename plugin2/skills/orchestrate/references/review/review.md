# Review · 审核 loop(阶段操作指南)

> 审核闸操作指南。审者 = Codex,协调验收 = Claude(你)。审题在 `references/review/`(喂 Codex)。

红线:**审者必须 Codex,不 Claude 审 Claude**;**完工靠 `exit-check` 机器核,不靠 reporter 自报审完**。

---

## 0. 选阶段(决定喂哪份 angle + loop kind)

| 审 | 触发点 | kind | angle 文件 |
|---|---|---|---|
| ① 设计审 | design pass 后 | `review` | `references/review/design.md` |
| ② 计划审 | plan pass 后 | `review` | `references/review/plan.md` |
| ③ 落地审 | 每个 plan 全 Pack 提交后 | `contract-gate` | `references/review/plan-impl.md` |
| ④ final | verify 阶段(全合并后) | `review` | `references/review/final.md` |

③ 是便宜合同门、不派 Codex 判断,①②④ 是真审 loop——本文下面分别讲。

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
- 有 accepted finding → 按 Gap 选结论词:Implementation/Design/Plan 缺陷→`needs-repair`(回对应阶段修,改完 handoff 重审);Direction→`needs-redirection`;Context→`needs-context`。
- 超熔断仍不收敛 → `mmw handoff --conclusion blocked`,带经过上报。

**Critical 必须修掉**才能让对应阶段往下走。

## 3. ③ 便宜合同门(contract-gate,不派 Codex)

③ 跟 TDD 每步验重叠,只查跨 plan 合同兑现,降成机器门:

```bash
mmw review start --stage plan-impl --source "<plan 目录>"   # init kind=contract-gate
mmw loop step add --id <pack-id> ...           # 待提交的 pack(record-step hook 提交即标 done)
mmw loop checklist add --item "<跨 plan 合同>" --source <plan:line>
# 逐条机器核合同兑现 → checklist cover;全 Pack 提交 + 合同全 cover → exit-check DONE
```

合同不达 → 回落地阶段(落地自己的 2 轮);合同根上错 → 升级。不开 Codex 判断 loop。

## 4. 守住的红线

- 审者 Codex,不用 `codex review`(走它内置提示词、绕过我们方法论),用 `codex exec` 喂我们的 quartet+angle。
- 每条 finding 引 `file:line` 原文才采信;协调帮手亲验后才 accept,主线程落 handoff 前再核承重的。
- ③ 不判断、只核合同;重判预算砸 ④final。
