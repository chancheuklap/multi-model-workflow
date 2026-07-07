# Review · 审核 loop(阶段操作指南)

> 审核闸操作指南。审者 = 无头 CLI(①② Codex;④final Codex+Claude 双模型),协调验收 = Claude(你)。审查方法 + 各 stage 角度单源在已装的 **`worktree-review` skill**(审者自己读;不给审者任何 plugin 内路径)。plugin 侧只留 `plan-impl.md`(③合同门,Claude 机器核)与本文(Claude 编排)。

红线:**写者≠验者**(①②产物是 Claude 写的→审者必须 Codex;④产物是 Codex 写的→双模型都可审);**完工靠 `exit-check` 机器核,不靠 reporter 自报审完**。

---

## 0. 选阶段(决定 stage + loop kind)

**三个产出阶段各被引擎强制审一次,触发方式统一**:design/plan/build 的产物 `pass` 后,引擎(`routes.review_gates` map)把阶段冻住、强制进审闸——`mmw where` 直接吐出 `review_start=mmw review start --stage <X>`,你照跑,不自己猜 stage。审查角度由 Codex 侧 `worktree-review` skill 按 stage 自取(下表只给 stage 对应哪路视角)。

| 审 | 触发点(引擎强制) | stage | kind | Codex 审查角度(worktree-review skill) |
|---|---|---|---|---|
| ① 设计审 | design pass → 引擎审闸 | `design` | `review` | 轴A 设计内容 / 轴B 项目对齐 |
| ② 计划审 | plan pass → 引擎审闸 | `plan` | `review` | 轴A 覆盖与质量 / 轴B 合规与交叉验证 |
| ④ final | build pass → 引擎审闸 | `final` | `review` | 基线1 回归+意图+跨plan / 基线2 独立代码审计;**develop 按风险自动分档**(review.sh 机器判,不用你选):全 plan 无 `Complexity: capable` 且 diff ≤ 阈值(默认 800 改动行,env `REVIEW_TIER_DIFF_MAX` 覆盖)→ **2 审者**(基线1 Codex / 基线2 Claude,跨模型互补);有 capable 或 diff 大或判不出数据(fail-closed)→ **双模型 2×2 = 4 审者**(每视角 Codex + Claude 各一,prompt 同一段、方法论同源 worktree-review skill);**small-change/bug = 1×Codex 一肩挑两视角**(diff 小) |

另有 **③ 落地合同门**:不是引擎审闸,是 build **内部**机器合同检查——全 plan 合并后、build handoff 前跑一次(`--stage plan-impl`,`kind=contract-gate`,不派 Codex),由 build 流程驱动(build-b B5),本文只讲 ①②④ 三个引擎审闸 loop。

## 1. 主线程:一条命令起审 → 抽清单 → 派协调帮手(①②④)

1. **一条命令起审**(把 init loop + 配审题 + 出 brief 收成一步):
   ```bash
   mmw review start --stage <design|plan|final> --source "<源意图路径/待审内容>"
   ```
   **直接用 `mmw where` 吐的 `review_start` 整行**(stage 与 `--source` 都填好了:design 闸→design、plan 闸→plan、build 闸→final)。它 init `kind=review` 的 loop、定好该阶段 stage 与两路视角(审查方法+角度在 Codex 侧 `worktree-review` skill,派发只传 stage + Source)、**打印好协调帮手 brief**。你照打印的往下走。
2. **抽覆盖清单**(判断,留你做):从设计/计划/issue/意图逐条抽"要审到什么",`source` 记从哪份文档哪行抽。客观项(② issue 数=plan 数、④ 意图逐条)标清楚:
   ```bash
   mmw loop checklist add --item "<要审到的维度>" --source "<doc:line>"   # 逐条
   mmw loop attendance --mode <attended|afk>
   ```
3. **派审核协调帮手**(Claude sub-agent,SubagentStop 受 guard-loop 看守):prompt 只给一句「读 `.claude/multi-model-workflow/review-brief.md` 照做」——brief 由 `review start` 机器生成落盘(派审者/留痕/亲验/收敛熔断全在里面),不过主线程 context。**别塞你自己的问题清单、别给审者 plugin 内路径。**

   **每个审都留痕(①②④ 都要,不只 ④)**:协调帮手把**全部审者的结构化 findings 原样落盘**到 `docs/reviews/<slug>-<stage>.md`(不重写、不摘要),亲验后把每条的 verdict/处置(accepted / rejected / duplicate / needs-evidence)就近标在该条下,文末写一句总 verdict。主线程收口只**读这份文档的 verdict 段**。留痕是过程产物:已被 `docs/.gitignore` 忽略,随 worktree 删,不进 git 历史。

## 2. 主线程:收口(协调帮手停下后)

读 `loop-state.json` 的 `pause` 和 `findings`,按情况 handoff(结论词由 Gap 决定):

- `pause != null`(surface 冒泡)→ 按 `reason` handoff `needs-redirection` / `needs-context`,交用户。
- `exit-check` = DONE 且无 accepted 缺陷 → `mmw handoff --conclusion pass`,进下一阶段。
  - **仅 ④final(build 审闸):handoff `pass` 前先写终审报告**到 `docs/<slug>-final-review.md`(照 `mmw where` 的 `then` 钉 `--produced`),closing 阶段照单读它收口。三段:
    1. **终审结论**:verdict + 两基线各自结果(回归/意图/跨 plan;独立代码审)+ 放行的 waived 项(环境/账号 gate,带 owner)。
    2. **意图清单逐条**:最初 design + issue 提取的每条可验证 intent → 达成/未达成 + 证据(`file:line` 或测试名)。
    3. **业务语言交付摘要**(给项目负责人看,**不用技术术语**):新增能力(每条一个用户可感知的行为变化,如「用户现在可以用手机号登录,15 秒内完成」,不列函数名/文件路径/类名)· 验证证据(跑了哪些验收、什么结果)· 残余风险(已知没覆盖的、需人盯的,诚实列不藏)。
    ①②审是闸、不产文件,这条不适用。
- 有 accepted finding → 按 Gap 选结论词(`needs-repair` 是**原地返工当前阶段**;回上游别的阶段必须 `needs-redirection --to-phase <阶段>`):
  - 缺陷在**当前被审阶段**(①审=design、②审=plan、④final=build,gate 的 cur_phase 就是它;④final 的代码缺陷在 build 审闸 loop 里就地修)→ `needs-repair`,改完 handoff 重审。
  - 根因在**更上游阶段**(②审发现 design 问题、④final 撞破 plan/design)→ `needs-redirection --to-phase <design|plan|build>`,回那阶段改。
  - Direction(解错问题)→ `needs-redirection`;Context(缺输入)→ `needs-context`。
- 超熔断仍不收敛 → `mmw handoff --conclusion blocked`,带经过上报。

**Critical 必须修掉**才能让对应阶段往下走。

## 3. 守住的红线

- ①②审者必须 Codex(设计/计划是 Claude 写的,不 Claude 审 Claude);④final 产物是 Codex 写的,双模型(Codex + Claude)都可审且互为交叉。不用 `codex review`(走它内置提示词、绕过我们方法论),一律 `codex exec` / `claude -p`,prompt 指向已装的 `worktree-review` skill(按 stage 审)——审查方法本体单源在那,不给审者 plugin 内路径。
- 每条 finding 引 `file:line` 原文才采信;协调帮手亲验后才 accept,主线程落 handoff 前再核承重的。
- ③ 不判断、只核合同;重判预算砸 ④final。
