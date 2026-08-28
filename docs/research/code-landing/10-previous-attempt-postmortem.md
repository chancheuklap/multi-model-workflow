# 上一次落地尝试的尸检（2026-08-24 → 08-25）

背景与本轮定案见 `00-synthesis.md`「第二轮之后的定案（2026-08-28）」。本文只回答「当时怎么做的、为什么失败、这次不能再犯什么」；旧实现一件都不复用，所以不列可复用件。

被删内容全部在 git 历史里，读法是 `git show ceb2c2a1^:<路径>`；下文引用被删文件时写成 `ceb2c2a1^:<路径>` 加行号。被删分支 `fix/skills-in-english` 停在 `0b026768`（`ceb2c2a1` 的 commit message 末段），引用写成 `0b026768:<路径>`。ADR 编号按 `docs/adr/README.md`「编号在本仓库以外仍会出现」翻译：当时的 0023 = 现在的 0005，当时的 0024（被删分支上的 `0024-delivery-surface-carries-only-instructions.md`）与现在的 0006 是两份不同的文件。

## 1. 时间线

从三份 ADR 到回退共 19 小时（本机时间 +0800）。主线 `dd32cf38^..ceb2c2a1` 共 50 个提交，其中 34 个属于这条流水线（11 个 merge），其余 16 个是同期无关的 diagram-design / system-map 工作（`ceb2c2a1` message「保留」段）；另有被删分支 `fix/skills-in-english` 上 10 个提交。GitHub 侧 5 张 issue（#53–#57）、2 个 PR（#58、#59）。

| 时刻 | 提交 / 事件 | 出处 |
| --- | --- | --- |
| 08-24 23:27 | `dd32cf38` ADR 0020–0022 + 根 `CONTEXT.md` 词汇表，来自 `/grill-with-docs` 会话 | commit message；Nowledge 线程「MMW V2 Landing Pipeline: ADRs, Specs, Carrier Model & Legacy Infra Discovery」U113 |
| 08-25 00:19 | `fb1d036d` ADR 0020 载体修正：复验者从无头 CLI 改为 subagent | 用户质询「复验者为什么要无头」（同线程 U166）、「你要为每一个功能寻找最合适的载体」（U168） |
| 08-25 00:50 | `e8d966c5` 三份 spec 发布为 #53 / #54 / #55（issue 创建于 00:48–00:49） | `gh issue list` |
| 08-25 00:5x–01:38 | 用户「在 herdr 派三个 cc fable 5 medium agent 去把上面三个 spec 落地……直接落地，不要再走 to-ticket」。三个工人：`994072bf`（#53，5 分钟）、`7eb1719b`+`8f21df4d`（#54，17 分钟 + 1 分钟补尾）、`4eab92f3`（#55，时长在编排者汇报里被截断） | Nowledge 线程「herdr 编排三 agent 落地 multi-model-workflow #53/#54/#55 及 tracer bullet #56/#57」U1、A53 |
| 08-25 01:54–02:05 | #53–#55 关闭；tracer bullet #56 / #57 开、跑、复验、关（01:59–02:04）；`08c1e953` 回填 | 同线程 A100–A121；issue #56 / #57 评论 |
| 08-25 02:xx | 用户「你帮我合并吧」→ PR #58、#59 合入；本机五宿主装 hook 并冒烟 | 同线程 U123、A122 |
| 08-25 13:26 | 用户要一张流程大图找断点 → 13 处 → advisor 核对后 9 处 | Nowledge 线程「mmw v2 技能流水线审查：断点、冗余与修复方案」U0、U44、U50 |
| 08-25 14:34–14:45 | `fix/pipeline-defects` 六批修 9 处，合入 `8cddac17` | `2abe188a`、`94fc6d01`、`2b2179c4`、`706ca400`、`5cb57479`、`4602a858` |
| 08-25 15:0x | 用户发现技能「全中文撰写」→ 「必须要改成全英文」→ 「技能里不写出处」 | Nowledge 线程「mmw-v2 技能英文化 + hooks 层 18 项修复 → 注入层架构性删除决策」U60、U77、U166 |
| 08-25 15:32–17:53 | 被删分支 `fix/skills-in-english` 10 个提交：英文化、ADR 0024、advisor 找出 17+1 处再修 16 处 | `a842a5db` … `0b026768` |
| 08-25 ~18:00 | 用户「Worker 和 Verifier 根本就不是同一种 Subagent……整个东西就是一滩烂泥」→「你先把那个 skill in English 这个分支整个删掉，然后再把昨天那三个 spec 落地的内容也全部删掉」 | 同线程 U236、U239 |
| 08-25 18:24 | `ceb2c2a1` 回退，77 个文件、-5345 行 | `git show ceb2c2a1 --stat` |

中间修过的缺陷（都在回退前的同一天）：

| 批次 | 缺陷 | 提交 |
| --- | --- | --- |
| 上午 9 处 | `to-tickets` 不把票挂成父 issue 的 sub-issue，而编排者只从 `sub_issues` 端点取票 → 一张票都派不出去 | `706ca400` |
| | MANUAL gate 卡 Stop hook：hook 只看 `checked`，implement 又明令工人不勾人工关卡 → 撞满 6 次才放行 | `2abe188a` |
| | verifier 无处跑关卡：派发不带 worktree 路径，它第 1 步 checkout 会踩并行票；`assemble.py` 把全部 subagent 沙箱写死只读 | `94fc6d01` |
| | 停车票回不到 frontier（assignee 未摘）；停车 issue 自己会被当票派出去 | `2b2179c4` |
| | 多上游票的 worktree 只以最后关闭的上游为基，fan-in 票编不过 | `5cb57479` |
| | 人工验收无闭环、worktree 无人回收、code-review 结论无落点、定级标签语义重载 | `4602a858` |
| 下午 16 处 | 同票两败 vs 升级链三条规则打架；勾了但没证据算通过（上游三态压成两态）；关卡跑不了没有出口（上游 ABANDON 机制一处没抄）；`status: blocked` 无分支；第二轮复验两边规则不一致；停车 `Default` 字段无人执行；解除停车后重派撞车；工人不知道什么不许碰；`models.md` 没写「不同模型家族」；人工关卡没有判据；工人纪律的停止条件引用了不存在的「预算」 | `1ad91c9f`、`d543295b`、`5e8615e3`、`1eb894ff`、`84e96d89`、`0b026768` |

## 2. 当时的架构

一句话：编排者在 Herdr 会话里跑循环，把票派给别的宿主上的工人；纪律靠 hook 注入；关卡写在票正文并镜像到一个状态文件让 Stop hook 读；复验者与规划者是编排会话自己的 subagent。

| 角色 / 机制 | 载体 | 做什么 | 定义位置 |
| --- | --- | --- | --- |
| 编排者（orchestrator） | 运行 `landing-orchestrator` 技能的 Claude Code 会话，必须在 Herdr pane 里（`HERDR_ENV=1`） | 查 frontier → 认领（assignee）→ 建 worktree + pane + agent → `agent prompt --wait` 递简报 → 等事件 → 派复验者 → 分诊 → 停车或收尾 | `ceb2c2a1^:mmw-v2/skills/landing-orchestrator/SKILL.md` L26–34（前置检查）、L50–58（主循环）、L84–90（派发命令） |
| 规划者（planner） | 编排会话的 subagent，只派一次 | 从全部子票推出契约、并行分组、定级复核、每票简报定制段，贴成父 issue 评论 `## 执行计划` | `ceb2c2a1^:mmw-v2/agents/planner/body.md` L11–39 |
| 工人（worker）初级 / 高级 | Herdr 在**别的宿主**上拉起的独立会话：初级 `cursor` + `cursor-grok-4.6-high`，高级 `grok` + `grok-4.6` xhigh | 按简报五段（契约、票全文、上游产出摘录、纪律块、汇报格式）工作，走 `implement`「## Finishing a ticket」九步 | `ceb2c2a1^:docs/agents/models.md` L7–14；`ceb2c2a1^:mmw-v2/skills/landing-orchestrator/reference/brief.md` L21–51 |
| 复验者（verifier） | 编排会话的 subagent，冷启动 | 只收票号、分支、commit、worktree 路径四样；重跑每条 `CHECK:`；输出 `verdict: pass\|fail @<commit>` + 六类标签发现 | `ceb2c2a1^:mmw-v2/agents/verifier/body.md` L3、L14–20、L34–57 |
| 升级顾问（advisor） | 既有 advisor subagent | 高级工人再败后给方向 | `ceb2c2a1^:mmw-v2/skills/landing-orchestrator/SKILL.md` L159 |
| 纪律送达 | hook 层：SessionStart 注入 `discipline/worker.md`；SubagentStart 默认注入 worker 块、`agent_type` 命中 `verifier` 注入 verifier 块；Stop 读 `.mmw-ticket-state.json` 顶回未清关卡；pi 走扩展；Grok 走 `~/.grok/rules/` | 三个事件、一份共享 JSON、分流 runtime、承重句校验 `invariants.json` | `ceb2c2a1^:mmw-v2/hooks/AGENTS.md` L9–19；`ceb2c2a1^:docs/adr/0021-discipline-via-cross-host-hooks.md` L12 |
| 关卡（gate） | 票正文 `- [ ]` 条目下缩进 `CHECK:` / `EXPECT:`，通过后工人加 `EVIDENCE:`；人工项 `MANUAL: <裁决人>`；开工时镜像进 worktree 根的 `.mmw-ticket-state.json` | 双条件：exit 0 且输出含 `EXPECT` 标记 | `ceb2c2a1^:docs/adr/0022-gates-live-in-ticket-body.md` L10–12；`git diff 317c82c5 ceb2c2a1^ -- mmw-v2/upstream/skills/engineering/implement/SKILL.md` 的「## Finishing a ticket」第 1、4 步 |
| 自查 | `self-check` 技能，工人跑关卡前自己过一遍 | swarm-forge cleaner 八条 | `ceb2c2a1^:mmw-v2/skills/self-check/SKILL.md` L14–25 |
| 定级 | `to-tickets` 出票时打 `worker:junior` / `worker:senior` 标签 | 只升不降 | 同上 diff 的 `to-tickets/SKILL.md`「**Grade** each ticket」段 |
| 停车 | 每个卡点一张 `blocked:decision` issue，挂父 issue，设成该票原生 blocker | 四段 Question / Options / Consequences / Default | `ceb2c2a1^:mmw-v2/skills/landing-orchestrator/reference/parking-issue.md` L11–38 |
| 模型表 | 消费仓库 `docs/agents/models.md`，`scripts/models.py` 解析 | 六角色 → kind / model / effort | `ceb2c2a1^:docs/agents/models.md` L7–24 |
| 纪律原文存档 | `discipline-sources.md` 1298 行、35 个逐字抄录块 | ponytail 反过度构建、unlazy 反偷懒、swarm-forge 反作弊、pstack 原则备换 | `ceb2c2a1^:docs/specs/landing-closeout/discipline-sources.md` L5、L171、L288、L630 |

## 3. 失败原因

### (a) 设计错误

1. **hook 事件定位错位。** ADR 0021 L8 给 hook 层的存在理由是「Claude Code 上会话级注入的上下文不进 Task 派生的 subagent」。但按 ADR 0020 L12，工人是 Herdr 在 Cursor / Grok Build 上拉起的**独立会话**，不是编排会话的 subagent；编排会话的 subagent 只有规划者、复验者、顾问。结果：`ceb2c2a1^:mmw-v2/hooks/mmw-activate.js` L12 把角色写死 `const role = 'worker'`，本机每一个 Claude Code 会话都被注入工人纪律；`mmw-subagent.js` L50–53 默认 `inject('worker')`，每一个 subagent 都被当成工人；三个事件里只有 Stop（靠 `.mmw-ticket-state.json` 自我定位）位置是对的。出处：Nowledge 记忆「MMW 架构：Worker 是独立 CC 会话而非 Subagent，Hook 事件定位因此错位」；线程「mmw-v2 技能英文化…」U236、A238。这是用户下删除令的直接触发点。
2. **同一份纪律放在两个家。** verifier 的纪律同时写在它的 `body.md` 和 hook 注入块 `discipline/verifier.md`，而后者的全部内容是 swarm-forge 的 Clojure 工具护栏（`ceb2c2a1^:mmw-v2/hooks/discipline/verifier.md` L9、L13：`crap4clj`、Gherkin manifests），与 `verifier/body.md` L24「Modify any file… you do not write」直接冲突。用户原话：「Verifier 他自己的那个 Agent 文档不就是放他纪律最好的地方吗？为什么还有第二个地方去放纪律？」（同线程 U230）。记忆「Subagent 纪律只写自身定义文件，hook 注入层不得重复」。
3. **Stop hook 是关卡进票正文的补丁。** ADR 0022 决定关卡写在票正文，Stop hook 只能读本地文件，于是 `discipline-hooks.md` L41 要求 implement 开工时把关卡快照写进 `.mmw-ticket-state.json`，票正文与状态文件要同步维护——ADR 0022 L10 自己反对的「两处必然漂移」原样回来了。状态文件契约又要 landing-closeout 与 discipline-hooks 两份 spec 共享（`ceb2c2a1^:mmw-v2/hooks/AGENTS.md` L34）。
4. **规则互相打架、上限只在散文里。** 同票失败的处理有三条规则同时适用（pstack 原话「两次失败即弃单」、自家的「初级两败→高级」、写死的入口「初级」），拆票时就定为高级的票永远见不到 advisor（`1ad91c9f` message）。「每票复验最多 2 次」纯自然语言，脚本里一行都没有，编排者要整夜自己记（同线程 A207「纯自然语言，脚本里一行都没有」）。停车 issue 的 `Default` 字段没有任何一步读它（`84e96d89` message）。
5. **载体一开始就选错，改了一次还没改对。** ADR 0020 首版让复验者走无头 CLI，被用户一句「复验者为什么要无头」推翻（`fb1d036d`）；修正版仍然让 hook 层按「subagent = 工人」建模，直到最后一小时才被用户点破（3.a.1）。

### (b) 步子太大

1. **一夜落三份 spec，没有一张真实票。** 用户指令「直接落地，不要再走 to-ticket」（线程「herdr 编排三 agent 落地…」U1），三个 Fable 5 medium 工人各用十几分钟交出 `994072bf` / `7eb1719b` / `4eab92f3`，合计新增 77 个文件、5345 行（`ceb2c2a1 --stat`）。编排者「看一遍它的改动」即合回 main（同线程 A25–A27）。
2. **验收只到机械自证，从没跑过真活。** 三份 spec 的 Testing Decisions 分别要求双票 tracer bullet（`ceb2c2a1^:docs/specs/landing-closeout/landing-closeout.md` L58）、每宿主冒烟（`discipline-hooks.md` L49）、单票穿行 → 依赖对 → 过夜批三档（`landing-orchestrator.md` L63）。实际做到的：tracer bullet #56 / #57 是两张改 spec 一行措辞、同步 issue 正文的文档票（issue #56 / #57 body「## What to build」），不是代码票；五宿主冒烟只问「上下文里有没有 `MMW DISCIPLINE ACTIVE` 这一行」（同线程 A78–A88）；`landing-orchestrator` 从未在 Herdr 里跑过一次主循环，`reference/manual-acceptance.md` 全部条目停在 `- [ ]`。
3. **spec 自己写的门槛没有执行。** `discipline-hooks.md` L39：「条目入选与后续增删都要过探针实测门槛，实测时对照组必须显式隔离常驻注入」——一次都没做。记忆「文本忠实≠效果达成：agent 技能必须过探针实测门槛」把这条记为核心教训。
4. **人没有逐一验收，结果看不懂。** 工人在 spec 没说清的地方自己拿了六个主意（code-review 挪到 commit 后、Grok 另装 hook 文件、`--host` 参数、复验 fail 先 reopen、`gates.md` 出处……），用户看到时的反应是「全部看不懂，到底影响什么，需要我注意什么，与原来的计划有什么不同」（同线程 U54）。
5. **修复本身也在滚雪球。** 08-25 上午 13 处 → 撤 3 降 2 → 9 处修完；下午再出 17+1 处；用户：「我感觉我已经对这一摊东西越来越失控了」（线程「mmw-v2 技能英文化…」U230）、「你做的这么烂，我怎么敢拿这套东西去跑啊？跑不需要时间的吗？不需要 token 的吗？」（U177）。修复是在没有一次真实运行反馈的情况下靠读代码找的。

### (c) 抄参考时走样

1. **抄过来后未接线。** `to-tickets` 只连阻塞边不挂 sub-issue，`landing-orchestrator` 只从 `sub_issues` 端点取票，「中间这一步两个技能都没写，落地流水线一张票都派不出去」（`706ca400`）。verifier「派发只给票号、分支、commit，它第 1 步就得 checkout——踩掉并行票的工作树」（`94fc6d01`）。pstack `gates.md` 的 `Default` 字段照抄，其消费者没抄（`84e96d89`）。unlazy stop hook 的 ABANDON / handoff 机制「14 处引用，我们一处都没抄」（`5e8615e3`）。pstack「Escalation」只抄了否定面「Never reaches the human」，肯定面四类（含「a standing order that contradicts observed reality」）整段没抄（线程「mmw-v2 技能英文化…」A185 A1；advisor 在 U199 确认）。unlazy「Manual gates」四条「一条都没落地」（`0b026768`）。
2. **抄的时候静默削弱。** unlazy `gateState` 三态（没勾 / 勾了无证据 / 勾了有证据）压成两态，`evidence` 字段从头到尾没被读过，「工人写 `{"checked":true, "evidence":null}` 就能收工」；而「勾选不算数、证据才算数」写在 ADR 0022、implement 第 4 步、to-tickets 关卡写法、verifier 发现规则四处（`d543295b`）。hooks 层的 JS 文件头声称「精确修改」，但原件从未存档，直到最后一天才第一次拉原件比对（同线程 A187–A198）。
3. **文本忠实 ≠ 效果达成。** 纪律块经逐字校验「49 行 100% 逐字」（同线程 A135），承重句校验 14/14 全绿——但注入给了错的人（3.a.1），verifier 块的两句在本仓零命中（advisor 发现 6），工人块引用的 unlazy 停止条件说「预算花完」而全流程没有任何地方给预算（`0b026768`）。用户裁决：「对齐上游不是目的，是手段」「不要把这些技能文档做成上游的说明书和技能本身落地的说明书」（U154）。
4. **抄成了说明书而不是技能。** `landing-orchestrator` 的 SKILL.md 与五份 reference 用中文写，每段标「逐字取自 X @commit」，另有 `reference/sources.md` 逐段台账；`self-check` 与 verifier 正文带「quoted verbatim from… commit b933d68」（`8dc8b35a`）。用户：「像一个目录一样，居然会去标注哪一段引用之哪里，简直多此一举」（U77）、「你到底明不明白我们现在是在做技能不是在做引用说明书」（U107）、「技能里不写出处」（U166）。
5. **半译与自造词。** 自称逐字的引用块内发现七处半译（`0b026768:docs/adr/0024-delivery-surface-carries-only-instructions.md` L17）；中文词汇表让英文 subagent 把「编排者」叫成 `dispatcher`——正是 `CONTEXT.md` `_Avoid_` 里列的「调度器」（`a842a5db`）；「discipline block」「同票两败」「第三次复验」等自造词让用户「根本就看不懂」（U202）。

## 4. 用户的原话裁决，与本轮定案对照

| 裁决（原话） | 出处 | 本轮定案 | 对照 |
| --- | --- | --- | --- |
| 「A 轮不允许无缘无故地停下来或者在自动化的过程中问我问题」「绝对不可以无限循环、无限 review。两次 review 就已经非常难受」 | grill 线程 U119 Q4、Q7；记忆「夜间自动化工作流两条硬禁令」 | `00-synthesis.md`「第二轮之后的定案」：verifier「只审一次……不复审」；「这轮明确不动的」把提问出口留待后补 | 一致，且比当时的「2 次复验夹 1 次自动修」（U126 Q14）更紧。08-26 记忆「落地流程：审核只一次，禁止复审循环」是新裁决 |
| 「不管你问 reviewer 多少次，他总能给出错误……最后必定导致过度设计过度防御，我已经在让 codex 做 reviewer 的旧版 mmw 里吃过大亏」 | grill 线程 U154 QC；记忆「Reviewer must not self-set pass criteria」 | 「谁来判」行：verifier brief「只给验收标准原文、SHA、Seam、FORBIDDEN、REPORT，不给 diff/spec/prototype」；「这轮明确不动的」拒绝 grok「0 issues 才退出」 | 一致 |
| 「要对不同参考里都有的相似设计进行比较，要么多选一，要么组合起来，目前我觉得多选一可能更稳妥」 | grill 线程 U152 | 「三份报告共同推荐、无分岔的改法」首句「每条只取一家（既定原则）」 | 一致 |
| 「应抄尽抄」「对于参考项目里的内容应抄尽抄，只做精确修改，不得重新简写改写曲解原意」 | grill 线程 U126 Q16；herdr 线程 U1 | ponytail 行：「措辞写成动作 + 票字段；『逐字复制』改为保留骨架只换对象；用第一张真实票穿行验证」 | **冲突，已被本轮定案覆盖**。上次的教训（3.c.3）正是逐字复制不等于有效；`07` §7.3 记录了这两条记忆相抵，定案取「保留骨架只换对象」 |
| 「只有 hooks 是最稳的，其他的全靠 agent 自觉」 | grill 线程 U119 Q1 | ponytail 行「无 hook、无插件（ADR 0003）」；定案没有 hook 层 | **冲突，已被用户自己的后续裁决覆盖**：U236「几乎所有对话都会注入 worker 这个角色指令，我真的感觉整个东西就是一滩烂泥」→ U239 删除 |
| 「技能里不写出处」；交付面只放指令、一律英文、不写落地记录 | 线程「mmw-v2 技能英文化…」U166；`0b026768:docs/adr/0024-…` L8；记忆「交付面内容纪律」 | `00-synthesis.md` 未提 | **仍有效但定案未写**。本轮改 `implement` / `to-tickets` 正文时同样适用 |
| 「你要为每一个功能寻找最合适的载体」「目前看起来没办法做成 agent 的只有工人对不对」 | grill 线程 U168 | 「Worker 与 verifier 是谁」行：Worker 是 Herdr 拉起的独立会话，verifier 是编排会话自己的只读子代理 | 一致 |
| 「不能随意去开新 agent，要在需要继承上下文的时候复用已经开好的 agent」 | grill 线程 U132 | 「verifier 次数」行：没过的 worker 修并自跑填证据 | 一致（工人 pane 常驻即复用）；verifier 不复审所以不再有「续用同一个复验者」 |
| 角色模型表：规划者 cc opus5 high、初级工人 cursor grok 4.6 high、高级工人 grok build grok 4.6 xhigh、复验者 cc opus5 high、升级顾问 cc fable 5 medium、编排者 cc opus5 medium | grill 线程 U131 | `06` §3 只写「能选模型时选一个和自己不同的」；定案没有模型表、没有初级/高级 | **未承接**，见第 6 节 |
| 「我明明已经为 Agent 准备好……UI Mockup，但是每一次落地，最后都会发现 Agent 完全就没有去参考」 | grill 线程 U12 | 根因表第 3 行 + 「UI 验收」两档自动判定 | 一致；上次只在 `verifier/body.md` L10 写了一句散文「open every design reference」 |
| 「卡住 Agent 的决策就用 GitHub Issue 记录下来……等我醒了再讨论解决」「也要学习现在父子 issue 的模式，一个任务一个专门收集卡点的父 issue」 | grill 线程 U119 Q4、U126 Q13 | 「失败词汇」行：`HANDOFF REQUIRED` 不关票、`ready-for-agent → ready-for-human`；「写码中发现契约装不下」→ spec 下开 sub-issue 带 `needs-triage` | 一致，形态从「停车 issue 四段」换成「sub-issue + 标签」 |
| 「用户裁定『暂时来看可以』」——关卡写在票正文 | `ceb2c2a1^:docs/adr/0022-…` L25 | 「`CHECK:`/`EXPECT:`/`EVIDENCE:`」行：加；`MANUAL:` 不过半 | 一致；本轮没有状态文件镜像 |
| 「落地严重偏离时从原型推倒重来而非修补」「只有一份涵盖全部内容的过大 spec，导致实现与 mockup/设计严重偏离」 | 记忆 `0a868042`、`1a1b1583`（08-27） | 「spec 怎么进票」行：只给指针不抄；`implement` 只读 `Parent` 指名的小节 | 一致 |

## 5. 这次不能再犯的

1. 没有一张真实代码票从头跑到尾之前，不合任何技能改动进 main——上次 77 个文件全靠机械自证与两张文档票验收（3.b.2；`landing-closeout.md` L58 的 tracer bullet 从未对代码票执行）。
2. 纪律句子写进正文后，用第一张真实的票跑一遍看效果；真票跑出具体问题时，再针对那一句做有句/没句的对照实验（`07` §8 的四个探针可作对照实验的种子）——上次 spec 自己写了实测门槛（`discipline-hooks.md` L39）却一次没跑（记忆「文本忠实≠效果达成」）。
3. 一次只落一份 spec、一组机制，落完人手验一遍再下一份——上次一夜三份、次日 9 + 16 处修复、用户「越来越失控」（U230）。
4. 抄任何机制时先列出它在原项目里的消费者，消费者不抄就不抄这段——`Default` 字段（`84e96d89`）、sub-issue 端点（`706ca400`）、ABANDON（`5e8615e3`）都是抄了产出端漏了消费端。
5. 上游的判定逻辑（三态、双条件、负控制）逐条对照原件复核，原件先存档再改——`d543295b` 三态压两态，hooks JS 原件直到最后一天才第一次比对。
6. 技能正文不写出处、不写落地记录、不带自己的验收清单，一律英文——U107、U166、`0b026768:docs/adr/0024-…` L8。
7. 每个角色的纪律只写在它自己的定义文件里，不建第二份送达通道——U230、记忆「Subagent 纪律只写自身定义文件」。
8. 每条规则写下之前先问「谁在什么时候读它、读到后做什么」，没有读者的规则不写——`Default` 字段、规划者 `Undecided` 行（`84e96d89`「编排者从来不读」）、「每票复验 2 次」的散文计数器（A207）。
9. 工人的每一个自主裁决在合并前逐条给用户看，用它背后的功能说人话，不用自造词——U54「全部看不懂」、U202「一大堆名词我根本就看不懂」。
10. 任何「对齐上游」的改动都以「这条流水线真正跑的是什么」为准，不为还原度补回本仓不可能发生的分支——`08856fb1`「restack mechanics 与 CI flake triage 两类在本仓库不可能发生」、U154「对齐上游是手段」。

## 6. 上次做了、这次定案里没有的

| 上次的东西 | 本轮 | 为什么 / 是不是漏了 |
| --- | --- | --- |
| hook 层（三事件、分流 runtime、pi 扩展、Grok 规则文件、`invariants.json`） | 无（`07` 行「无 hook、无插件（ADR 0003）」） | 不做，理由是 3.a.1：工人不是编排会话的 subagent，SessionStart / SubagentStart 送不到工人；Stop 拦截依赖状态文件镜像（3.a.3）。本轮由票的 `CHECK:` + verifier 重跑承担「关卡未清不许收工」 |
| `.mmw-ticket-state.json` 状态文件 | 无 | 不做，它只为 Stop hook 存在 |
| 规划者 planner subagent（契约、并行分组、定级复核、简报定制段） | 无 | 「契约」由 `to-spec` 的 Implementation Decisions / Testing Decisions 承担，「并行分组」由 `Owns:` 加 Blocked by 边在出票时解决（`04` §5「并发重叠在出票时人眼比对」）。**未漏**，但「上游票的关键产出全文粘贴进下游简报」（`brief.md` L9「依赖是上下文接力，不只是顺序」、L35–37 第 3 段）在本轮没有对应物——定案说「票本身；不另写派发词」，下游票读上游产出靠 `Read first` 指针 |
| `self-check` 技能（swarm-forge cleaner 八条） | 无 | 不做。分岔 4「交接前自审」在 `00-synthesis.md`「需要决定的分岔」第 4 条列出（swarm-forge 二次调用 vs unlazy「Audit the final report」），定案表未写结论。**可能是漏项**：定案里 worker 自跑 `CHECK:` 之外没有自审步骤 |
| 定级 `worker:junior` / `worker:senior` + `docs/agents/models.md` 六角色模型表 | 无 | 未承接（第 4 节倒数第 5 行）。本轮 worker 由 Herdr 启动，「可在任一宿主」，选哪个宿主哪个模型没有写在定案里。**是漏项**，至少要定「每票派给谁」写在哪 |
| `landing-orchestrator` 主循环（frontier 查询、认领、`herdr agent wait`、失败分类、升级链、终止报告） | 定案只写「Worker 是 Herdr 拉起的独立会话……按阻塞关系决定启动顺序」 | 编排循环本身在「这轮明确不动的」（无人看守相关留待后补）。不是漏，是刻意缩到「一张票能干净收尾」这一层——正是上次 `landing-closeout.md` L37 User Story 14 要求先证明、却没证明的地基 |
| 停车 issue（`blocked:decision`、四段模板、原生 blocker 回程） | `HANDOFF REQUIRED` + `ready-for-human`；契约装不下 → sub-issue `needs-triage` | 形态换了，功能保留 |
| 根 `CONTEXT.md` 落地流水线词汇表（frontier、gate、brief、grading、worker、verifier、verdict、planner、orchestrator、parking、escalation） | 无；`AGENTS.md`「Domain docs」说根 `CONTEXT.md` 尚未建立 | 上次词汇表是中文，导致 `dispatcher` 漂移（3.c.5）。本轮新词（`Owns`、`CHECK`、`EVIDENCE`、`ABANDON`、`HANDOFF REQUIRED`、`VERDICT` 等级）散在五份报告里，没有一处集中定义——**可能是漏项** |
| `discipline-sources.md` 逐字存档 + `check-upstream-drift.py` | `docs/research/code-landing-refs/` 参考快照 | 功能相同（原件留在维护面），保留 |
| `implement`「## Finishing a ticket」九步（状态文件 → 实现 → self-check → 跑关卡 → commit → review → push → PR → 关票） | 收尾五步：code-review（≤2 轮）→ 最终 SHA 重验 → `VERDICT` 评论 → push/PR → 关票或 HANDOFF（`06` §8.1） | 骨架相同，去掉状态文件与 self-check，加 verifier 与失败词汇 |
| 「复验 fail 时先 `gh issue reopen`（否则下游会在修复期间被派发）」 | 未提 | 本轮 verifier 在关票前跑（收尾五步顺序），票未关就不会解锁下游，问题不再存在 |
| 「不同模型家族」写进 `models.md` | `06` §3「Claude Code 只能选 Anthropic 内模型」，正文只写「能选模型时选一个和自己不同的」 | 承接为软要求 |

## 7. 未读 / 未确定

- grill 线程「MMW V2 Landing Pipeline…」242 条消息只读了用户发言（60 条），助手侧的方案演变与 claim-checker 两轮修正没有读；调研 artifact `280359df-e0fb-445c-81c6-9bd6882ecd35`（三份 spec 的 Sources 都指向它）没有读。
- 三个工人收到的简报原文（`scratchpad/brief-53.md` 等，herdr 线程 A11–A12）在临时目录里，已不存在；工人「在 spec 没说清楚的地方自己拿的主意」只有编排者转述（A55）。
- hooks 层的测试（`ceb2c2a1^:mmw-v2/hooks/tests/`）、`landing-orchestrator/tests/run.sh`、`scripts/models.py` 没有读；本文对「验收只到机械自证」的判断基于 spec Testing Decisions 与线程记录，不是测试内容本身。
- ponytail / unlazy 的 JS 原件没有拉下来比对，「三态压两态」等结论取自 `d543295b` 与线程 A191–A192 的记录。
- 「审核只一次，禁止复审循环」（记忆 `4d2c0a13`，08-26）出自哪个会话没有查到；它与 grill 线程 U126 Q14「2 次复验、中间夹 1 次自动修」冲突，本文按时间取后者为现行裁决。
- 五宿主冒烟的 Codex 一步需要在信任对话框按 `t`（herdr 线程 A100）——本轮若再装任何宿主级配置，这类一次性人工动作要先列出来；本文没有核对其他宿主是否也有。
- ADR 0020 首版（`dd32cf38:docs/adr/0020-workers-dispatch-via-herdr.md`）与修正版的差异只看了 `git show fb1d036d`；首版否决「宿主内 subagent」的理由（「角色到模型的映射要求初级工人、高级工人、复验者各在不同宿主的模型上」）在修正版被删，本文未追溯这条约束是否还在别处成立。
