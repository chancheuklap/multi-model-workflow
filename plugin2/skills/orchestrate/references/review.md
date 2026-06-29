# Review · 审核 loop(阶段操作指南)

> 主线程进审核闸时加载本文。审 = loop engineering 的 `kind=review` 实例,载体换成 Codex 审者 + Claude 协调帮手。机制全貌见 `plugin2/design/review-loop.md`(单源,这里不复述);审题在 `references/review/`(喂 Codex,本文不复述)。

红线:**审者必须 Codex,不 Claude 审 Claude**;**完工靠 `exit-check` 机器核,不靠 reporter 自报审完**。

---

## 0. 选阶段(决定喂哪份 angle + loop kind)

| 审 | 触发点 | kind | angle 文件 |
|---|---|---|---|
| ① 设计审 | design pass 后 | `review` | `references/review/design.md` |
| ② 计划审 | plan pass 后 | `review` | `references/review/plan.md` |
| ③ 落地审 | 每个 plan 全 Pack 提交后 | `contract-gate` | `references/review/plan-impl.md` |
| ④ final | verify 阶段(全合并后) | `review` | `references/review/final.md` |

③ 是便宜合同门,不派 Codex 判断(见 §3);①②④ 是真审 loop(§1–§2)。

## 1. 主线程:抽清单 → 起 loop → 派协调帮手(①②④)

1. **抽覆盖清单**(你有源文档 context,这步你做):从设计/计划/issue/意图逐条抽出"要审到什么",`source` 记从哪份文档哪行抽的。客观项(② issue 数=plan 数、④ 意图逐条)能机器核的标清楚。
   ```bash
   bash "${SCRIPTS}/loop.sh" init --kind review
   bash "${SCRIPTS}/loop.sh" checklist add --item "<要审到的维度>" --source "<doc:line>"   # 逐条
   bash "${SCRIPTS}/loop.sh" attendance --mode <attended|afk>
   ```
2. **派审核协调帮手**(Claude sub-agent,SubagentStop 受 guard-loop 看守)。给它这份简报(只给 Source + 点名 references,**别塞你自己的问题清单**):

   > 你是审核协调帮手,跑一台 `kind=review` 的审核 loop,不自己写结论也不自己改产物。
   > **Source**:〔源意图路径(design/issue/意图)+ 待审内容/diff〕。
   > **派两个独立 Codex 审者**(①②③=轴A+轴B;④=基线1+基线2),单条消息并行起、各自干净 context,每个跑:
   > `codex exec -C . --sandbox read-only - < <prompt>`,`run_in_background: true`;prompt = 点名让它读 `references/review/quartet.md` + `references/review/<阶段>.md` 的〔轴A/基线1〕+ 给 Source。Codex 侧没装本 skill 就把那两段拼成自包含 prompt。续接用 `codex exec resume <id>`。
   > **收回后亲验**:每条 finding 自己 Read/grep/跑坐实(Codex 是劳动力不是信源),引不出 `file:line` 原文 = 降置信。坐实一个覆盖维度就 `loop.sh checklist cover --item <i> --evidence <file:line>`;真 finding `loop.sh finding add --severity <C/I/M> --confidence <1-10> --locator <file:line>`。
   > **收敛**:两视角跑完追一轮没新高置信 finding = 收敛;`round` 到阶段上限(①②=2,④=1-2)还没收敛 → `loop.sh surface --kind needs-redirection --question "<审不收敛/卡在哪>"`。
   > **方向疑 / 缺输入**(需用户拍)→ `loop.sh surface`,别自己当产物缺陷修。
   > 清单全绿 + 无开口 Critical 前 `guard-loop` 不让你停;做完再停。

## 2. 主线程:收口(协调帮手停下后)

读 `loop-state.json` 的 `pause` 和 `findings`,按情况 handoff(结论词由 Gap 决定):

- `pause != null`(surface 冒泡)→ 按 `reason` handoff `needs-redirection` / `needs-context`,交用户。
- `exit-check` = DONE 且无 accepted 缺陷 → `flow.sh handoff --conclusion pass`,进下一阶段。
- 有 accepted finding → 按 Gap 路由(详 `review-loop.md` §5)选结论词:Implementation/Design/Plan 缺陷→`needs-repair`(回对应阶段修,改完 handoff 重审);Direction→`needs-redirection`;Context→`needs-context`。
- 超熔断仍不收敛 → `flow.sh handoff --conclusion blocked`,带经过上报。

**Critical 必须修掉**才能让对应阶段往下走。

## 3. ③ 便宜合同门(contract-gate,不派 Codex)

③ 跟 TDD 每步验重叠,只查跨 plan 合同兑现,降成机器门:

```bash
bash "${SCRIPTS}/loop.sh" init --kind contract-gate
bash "${SCRIPTS}/loop.sh" step add --id <pack-id> ...           # 待提交的 pack(record-step hook 提交即标 done)
bash "${SCRIPTS}/loop.sh" checklist add --item "<跨 plan 合同>" --source <plan:line>
# 逐条机器核合同兑现 → checklist cover;全 Pack 提交 + 合同全 cover → exit-check DONE
```

合同不达 → 回落地阶段(落地自己的 2 轮);合同根上错 → 升级。不开 Codex 判断 loop。

## 4. 守住的红线

- 审者 Codex,不用 `codex review`(走它内置提示词、绕过我们方法论),用 `codex exec` 喂我们的 quartet+angle。
- 每条 finding 引 `file:line` 原文才采信;协调帮手亲验后才 accept,主线程落 handoff 前再核承重的。
- ③ 不判断、只核合同;重判预算砸 ④final。
