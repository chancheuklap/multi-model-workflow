# 落地前：worker 输入契约

各家参考资料把一个工作单元交给 worker agent 时，交出去的那份输入长什么样、含哪些字段、各字段怎么保证 worker 真用得上；对照我们 `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md` 的 `<issue-template>`（L106-133）差在哪。

参考快照全部在 `docs/research/code-landing-refs/`，下文路径省略这个前缀；我们自己的文件写全路径。

## 1. 一句话结论

六家里没有一家把整份 spec 交给 worker：要么由分派者裁剪后**内联**到 brief（pstack、grok），要么 brief 只留**指针**而把 worker 必读的东西压到一两份文件（unlazy 的 `GATES.md`、swarm-forge 的 commit、mattpocock 的 tickets）；我们的 `<issue-template>` 是指针派，但缺三样各家都有的东西——**写入边界**（哪些路径可改、哪些不可）、**逐条可执行的验证命令**、**回报格式（含偏离）**——而且没有任何一家（我们也没有）把 UI mockup 变成机器可检的约束，只有 pstack 用「`You see` + 截图 lane」把它变成逐条勾选的人眼验收。

## 2. 各家契约字段对照表

行是字段概念，列是来源。每格写「有/无」和出处（路径 + 标题或行号）。「—」表示该家没有对应字段。

| 字段概念 | 我们 `to-tickets` `<issue-template>` | pstack | unlazy | grok-bundled | swarm-forge | ponytail | mattpocock-implement-spec |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 目标一句话 | `## What to build`（`to-tickets/SKILL.md` L112-114） | `GOAL`（`pstack/skills/poteto-mode/playbooks/orchestrate.md` L41）；每 PR 标题 `## <Task as a verb phrase> (<PR id>)`（`playbooks/multi-phase-plan.md` L78） | `Scope:` 一句话（`unlazy/templates/gates-leaf.md` L5） | `- Title` / `- Description`（`grok-bundled/execute-plan/SKILL.md` L497-498，来自 `grok-bundled/design/SKILL.md` L100-104 的 PR title / Brief description） | `task:` 只有短名（`swarm-forge/swarmforge/handoff-protocol.md` L131-143）；正文固定为 `Re-read your role and constitution.` + `merge_and_process.sh`（L147-152） | — | —（读 spec 与 tickets，`mattpocock-implement-spec/SKILL.md` L19） |
| 上游来源指针 | `## Parent`（L108-110）、`## Read first`（L116-118） | `CONTEXT`「pointers to files and PRs」（`orchestrate.md` L43）；`## Appendix D. Links and reading list`（`multi-phase-plan.md` L150-152） | `Dependencies: <leaf ids that must be VERIFIED first>`（`unlazy/templates/PLAN.md` L15） | `## Context from Design Document`（`execute-plan/SKILL.md` L502-504） | `commit:`（`handoff-protocol.md` L142），上游成果就是那个 commit | — | 「context pointers: to the spec, tickets, research notes, and previous commits」（L13） |
| 上游内容内联 | 无；例外是 prototype 产出的 snippet（`to-tickets/SKILL.md` L135） | `CONTEXT`「upstream reports pasted in full when this unit depends on them, because workers cannot see siblings」（`orchestrate.md` L43-44）；`STANDING` 整份贴入（L51） | 无；`method.md` L37「Paraphrase only acceptance-relevant facts」 | 「read and include the full design doc content that pertains to this PR's scope」（L503-504） | 无；`handoffs.prompt` L46「Do not write long handoff bodies」 | — | 无；L13「Don't duplicate information already available via pointers」 |
| 写入边界（可改 / 不可改路径） | 无；反而禁止写实现文件路径（`to-tickets/SKILL.md` L135） | `SCOPE`「paths this unit may write; paths it may not; its exclusive worktree or branch」（`orchestrate.md` L42）；`- [ ] Hold the file boundaries. <PR id or class> touches only <glob>.`（`multi-phase-plan.md` L52）；`**Files.**` Edit/Create/Delete（L82-86） | `OWNS:` 仓库相对 glob，并发 leaf 之间必须不相交（`gates-leaf.md` L3、L40-41；`PLAN.md` L14、L54） | `- Files to modify`（`execute-plan/SKILL.md` L499），来自 `design/SKILL.md` L102 `Files/components affected` | 「Work only in your assigned branch or worktree」（`swarm-forge/swarmforge/constitution/articles/workflow.prompt` L6） | 「Fewest files possible」（`ponytail/.openclaw/skills/ponytail/SKILL.md` L49） | 每个 implementer 自己的 worktree 与分支（L25），无路径边界 |
| 依赖 / 阻塞边 | `## Blocked by`（L129-131） | `**Depends on.**`（`multi-phase-plan.md` L80）；`- [ ] Follow this dependency graph.`（L49-51） | `Needs:`（`PLAN.md` L48-52）与状态词表 WAITING/READY（L32-36） | `- Dependencies`（`design/SKILL.md` L103）；`PRNode.dependencies`（`execute-plan/SKILL.md` L290） | 链式角色顺序（`handoff-protocol.md` L157-171） | — | 「task graph with blocking relationships」+ frontier（L11） |
| 验收标准 | `## Acceptance criteria`（L124-127）+ 四条规则（L38-43） | `ACCEPTANCE`「checkable criteria, one per line」（`orchestrate.md` L45）；`**You see.**` 每条带 exact log line 或 screen state（`multi-phase-plan.md` L92-94） | 每条 gate `- [ ] G<n>: <observable outcome>`（`gates-leaf.md` L7-19）；作者规则 `unlazy/references/gates.md` 「## Author gates that can fail」L93-102 | 无独立字段，靠 reviewer 循环到 0 issues（`execute-plan/SKILL.md` L652-663） | specifier 产出的 Gherkin acceptance specifications（`swarm-forge/README.md` L34-35、L45-46） | — | — |
| 验证命令（怎么跑） | `## Seam` 只写测试层与目录（L120-122）；命令在 spec `## Testing Decisions`「The commands to run before committing」（`mmw-v2/upstream/skills/engineering/to-spec/SKILL.md` L72） | `VERIFY`「exact commands or the control-skill path, plus known gotchas」（`orchestrate.md` L46）；`**Verify, unit.**` `Run <command>`（`multi-phase-plan.md` L96-98）；`**Verify, live.**` 十条 lane 各带截图名与 pass predicate（L100-111） | 每条 gate 的 `CHECK:` / `EXPECT:` / `CWD:`（`gates-leaf.md` L8-16）；成功 = exit 0 且 EXPECT 匹配（`gates.md` L50-53） | 「Verify your code compiles and passes basic checks (e.g., cargo check, tsc --noEmit ...)」（`execute-plan/SKILL.md` L525-526）；persona 「Run fmt and clippy before declaring done」（`grok-bundled/shared/personas/implementer.md` L17） | constitution 的工具清单（`swarm-forge/swarmforge/constitution/articles/engineering.prompt` L27-52） | 「leaves ONE runnable check behind」（`ponytail/AGENTS.md` L30；`SKILL.md` L95-100） | — |
| 禁止事项 | 无 | `FORBIDDEN`「no gt, no rebase, no force-push, no fixes outside scope, plus unit-specific bans」（`orchestrate.md` L48） | 无独立字段；`OWNS` 之外不写 | persona 「Don't add features that weren't asked for」「Make the smallest change」（`implementer.md` L15、L18）；「never create branches, push, or interact with Graphite or gh」（`execute-plan/SKILL.md` L1226） | `handoffs.prompt` 「Do not ...」多条（L10-15、L46-48）；`workflow.prompt` L7-8 | 整份 `## Rules`（`SKILL.md` L44-52）与 `## When NOT to be lazy`（L78-89） | — |
| 时限 | 无 | `TIMEBOX`（`orchestrate.md` L47） | 默认 120 秒每条 CHECK（`gates.md` L55） | `PR_TIMEOUT` 15 分钟（`execute-plan/SKILL.md` L454-456） | — | — | — |
| 回报格式 | 无字段；`implement` 收尾三步：评论证据并打勾、push 开 PR、关票（`mmw-v2/upstream/skills/engineering/implement/SKILL.md` L20-23） | `REPORT`「status, branch, head SHA, PRs, verdict, what you actually ran, deviations, suggested follow-ups」（`orchestrate.md` L49-50） | `EVIDENCE:` 每条 gate 一行（`gates-leaf.md` L10-19）；`ABANDON:` 显式放弃（L43-47） | 「Write an implementation summary ... Include: files changed, key decisions, any deviations from the plan.」（`execute-plan/SKILL.md` L535-536）；`Status: wontfix` 带解释（`implementer.md` L19） | `git_handoff` 只带 `commit:`（`handoffs.prompt` L19-26）；提问走 `pack_dashboard_request.sh clarify`（L12-15） | 「[code] → skipped: [X], add when [Y].」（`SKILL.md` L63） | — |
| 常驻规则（每次派发都带） | 无 | `STANDING <preferences.md pasted verbatim>`（`orchestrate.md` L51）；「Every spawn and every resume carries the standing orders verbatim」（L10、L27） | 无 | `<implementer_persona_instructions>` 前置（`execute-plan/SKILL.md` L486-490）；`## User Instructions`（L511-515）；`## Past Issues to Avoid`（L261-268、L506-509） | 「Re-read your role and constitution.」是每份 handoff 正文第一行（`handoff-protocol.md` L119） | 「ACTIVE EVERY RESPONSE」（`SKILL.md` L16）；`AGENTS.md` 整份就是常驻文本 | — |
| 设计契约（类型 / 接口 / 数据形状） | 无；spec `## Implementation Decisions` 可含「The interfaces of those modules」（`to-spec/SKILL.md` L52-58），但票只按小节号指过去 | `architect` 的 type sketch 是契约（`pstack/skills/architect/SKILL.md` L55）；`feature.md` L12 delegate 时要给「named data shape and its organizing structure」；`references/rationale-template.md` `## Usage (caller's view)`（L9-11） | `## Contract` 的 `Interfaces: <signatures, schemas, formats, integration points>`（`PLAN.md` L13）；`method.md` L11「Fix contracts before fan-out」 | `## Key Decisions`（`design/SKILL.md` L108） | Gherkin spec（`README.md` L34） | — | — |
| prototype / mockup 引用 | `## Read first` 可列 prototype directories（L118）；验收值「copied from the spec or the chosen prototype artifact」（L41） | `## Appendix A. Prototype evidence`「branch, the SHA, and the artifact links」（`multi-phase-plan.md` L138-140，来源是 L6） | — | — | — | — | — |

## 3. 各家如何解决「spec 太大 worker 用不上」

| 来源 | 指针还是内联 | 内联多少 | 谁负责裁剪 | 出处 |
| --- | --- | --- | --- | --- |
| pstack orchestrate | 两者：`CONTEXT` 默认是「pointers to files and PRs」，只有本单元**依赖**的上游 report 才「pasted in full」；`STANDING` 永远整份贴 | 依赖的上游 report 全文 + `preferences.md` 全文；其余指针 | coordinator。「a field you cannot fill is a unit you have not scoped yet」「Missing fields are a refuse-to-spawn condition」；「Size the brief to the unit」 | `orchestrate.md` L38、L43-44、L51、L54、L58；cloud worker 读不到本地 store 所以「their briefs inline what they need or point at repo paths」L19 |
| pstack multi-phase-plan | 指针。探索子代理「returns file pointers, conventions, test commands, and entry points. No inlined dumps.」；plan 每 PR 段本身就是裁剪后的输入 | 每 PR 段：Files / Build / You see / Verify 三块；阅读清单放 Appendix D | plan 作者（「You own the plan, not the code」） | `multi-phase-plan.md` L7、L78-131、L150-152、L3 |
| unlazy | 指针 + 一份小账本。leaf 只拿 `GATES.md`（`OWNS` + `Scope` + gates）；共享契约在 `PLAN.md` `## Contract` | 「Keep leaf briefs to the contract and one ledger」；「Paraphrase only acceptance-relevant facts」 | 树的作者在 fan-out 之前（「Fix contracts before fan-out」） | `unlazy/SKILL.md` L98；`method.md` L11、L37；`PLAN.md` L7-19 |
| grok execute-plan | 内联。orchestrator 读 design doc，把「the full design doc content that pertains to this PR's scope」贴进 prompt | 与本 PR 相关的全部小节，外加 `past_issues_briefing`（上限 20 条）与 `user_instructions` | orchestrator，每次 spawn 时裁 | `execute-plan/SKILL.md` L502-504、L1245、L1253、L1261 |
| swarm-forge | 极端指针。handoff 正文固定两行，任务内容全在 commit 与仓库里；coder 要的 spec 是 specifier 提交的 Gherkin 文件 | 零 | specifier（产出 Gherkin，人工 Approve 后才投递） | `handoff-protocol.md` L119-121、L593；`handoffs.prompt` L46；`README.md` L34-35、L136 |
| mattpocock-implement-spec | 指针。「Communicate primarily through context pointers ... Don't duplicate information」；探索笔记由 exploration subagent 存到仓外目录供所有 implementer 读 | 零 | to-tickets 阶段（tickets 是任务图，L11）；探索由单独的子代理做 | `mattpocock-implement-spec/SKILL.md` L13、L21 |
| ponytail | 不处理 spec 大小；处理 worker 读法：「Never lazy about understanding the problem ... Read fully, then be lazy」 | 不适用 | worker 自己 | `SKILL.md` L85-89；`AGENTS.md` L15、L30 |

我们现状：指针派。票的 `## Read first` 是「the source material behind the sections named under Parent ... The implementer reads these and nothing else from the spec's Sources」（`to-tickets/SKILL.md` L118），但 `implement` L10 又要求「follow Parent to the spec and read that in full」——所以 worker 实际读的是**整份 spec**，`Read first` 只裁了 Sources 没裁 spec 本身。这就是「spec 很大，worker 用不上」的直接原因。

## 4. 各家如何把 prototype / mockup 变成 worker 必须遵守的约束

| 来源 | 有无明确机制 | 机制 | 出处 |
| --- | --- | --- | --- |
| pstack multi-phase-plan | 有，人眼验收级 | plan 之前先跑 `playbooks/prototype.md` 定版式，「Keep the branch, the SHA, and the screenshots for Appendix A」；每 PR 的 `**You see.**` 写「exact log line or screen state」；`**Verify, live.**` 十条 lane 各有「Save <slug>.png. Pass when <predicate>」；改交互的 PR 走 `**Review gate.**`，operator 看截图和视频后才合 | `multi-phase-plan.md` L6、L92-94、L100-111、L120-124、L138-140 |
| pstack prototype 剧本 | 有交接、无约束 | 结论「Hand the chosen direction to Feature (or architect for the shape) for the real build」，并要求「Say plainly that the prototype is throwaway」；决定与截图是产出，但没规定 Feature 怎么被它绑住 | `pstack/skills/poteto-mode/playbooks/prototype.md` L12、L14 |
| pstack visual-parity | 有，机器验收级，但场景是「让 X 与 Y 完全一致」 | 「The baseline is the spec; you do not touch it」；先建截图回归 harness，逐组件 image diff，「A nonzero diff is a fail」；禁改 harness、禁改 baseline、禁为过 diff 重构组件 | `pstack/skills/poteto-mode/playbooks/visual-parity.md` L3、L5-6、L8 |
| unlazy | 无直接机制；可承载 | 一条 gate 可以是 manual（无 CHECK/EXPECT，L18-19）；「Review consequential manual gates by risk」 | `gates-leaf.md` L18-19；`gates.md` L101 |
| grok-bundled | 无 | 设计文档只有 `## PR Plan` 与 `## Key Decisions`；没有视觉产物字段 | `design/SKILL.md` L100-108 |
| swarm-forge | 有，但对象是行为不是视觉 | specifier 的 Gherkin 经人工 Approve 后成为 coder 的输入，coder 要过「generated acceptance tests」；QA 角色「runs final user-interface verification」 | `README.md` L34-35、L50、L136 |
| ponytail、mattpocock-implement-spec | 无 | — | — |

我们现状：`prototype/SKILL.md` 规则 6 要求「link the leaf directory from the ticket as an asset」并「fold the validated decision into the real code ... with the prototype as reference」（`mmw-v2/upstream/skills/engineering/prototype/SKILL.md` L26）；`UI.md` 步骤 6 说「Fold the winner into the real code, rewritten to production standard」（`mmw-v2/upstream/skills/engineering/prototype/UI.md` L102）。`to-tickets` 的验收规则 2 要求精确值「copied from the spec or the chosen prototype artifact」（L41），`implement` L10 要读「the chosen artifact of a prototype」。也就是：**我们有「读它」的要求，没有「产出必须长得像它」的检查**——没有 pstack 的 `You see` 逐条截图，也没有 visual-parity 的 baseline diff。而且 `UI.md` 第 2 步要求变体用「The project's component library / styling system」（L51），winner 是可以直接改写成产品代码的组件，不是死图；但 mockup 若是独立 HTML（`prototypes/<task>/<issue>/UI/` 下的静态页），没有任何一处说 worker 交付要与它比对。

## 5. 对照我们 `<issue-template>` 的缺口清单

| # | 缺什么 | 哪家有 | 出处 |
| --- | --- | --- | --- |
| G1 | 票不裁 spec：`Read first` 只裁 Sources，`implement` 仍读 spec 全文 | grok「the full design doc content that pertains to this PR's scope」内联；pstack `CONTEXT` 指针 + 依赖 report 全文 | `execute-plan/SKILL.md` L502-504；`orchestrate.md` L43-44 |
| G2 | 无写入边界：可改哪些路径、不可改哪些路径；模板反而禁止实现路径（L135） | unlazy `OWNS:`；pstack `SCOPE` 与 `Hold the file boundaries` | `gates-leaf.md` L3、L40-41；`orchestrate.md` L42；`multi-phase-plan.md` L52 |
| G3 | 验收条目不带命令：`Seam` 只到目录，命令在 spec `Testing Decisions` L72，worker 得自己回 spec 找 | unlazy 每条 gate `CHECK:`/`EXPECT:`/`CWD:`；pstack `VERIFY` 与 `Run <command>` | `gates-leaf.md` L8-16；`orchestrate.md` L46；`multi-phase-plan.md` L98 |
| G4 | UI 票的验收没有「看到什么」和截图：mockup 只被列在 `Read first` | pstack `**You see.**` 与 `Verify, live` lane（截图名 + pass predicate）；visual-parity 的 baseline diff | `multi-phase-plan.md` L92-94、L100-111；`visual-parity.md` L3-8 |
| G5 | 无禁止事项字段：不能 rebase、不能改 scope 外、不能加没要的功能，全靠 worker 自觉 | pstack `FORBIDDEN`；grok persona 「Don't add features that weren't asked for」；ponytail `## Rules` | `orchestrate.md` L48；`implementer.md` L18；`ponytail/.openclaw/skills/ponytail/SKILL.md` L44-52 |
| G6 | 无回报格式：`implement` L22 要评论证据，但没要求写「偏离了什么」「跳过了什么」「建议后续」 | pstack `REPORT`（含 deviations、suggested follow-ups）；grok summary「any deviations from the plan」；architect「Deviations from the sketch are signal worth surfacing」 | `orchestrate.md` L49-50；`execute-plan/SKILL.md` L536；`pstack/skills/architect/SKILL.md` L57 |
| G7 | 无常驻规则通道：`to-tickets` 与 `implement` 都没有「每次派发都带上这段」的位置 | pstack `STANDING`；grok persona + `--instructions` + `Past Issues to Avoid`；swarm-forge 「Re-read your role and constitution.」 | `orchestrate.md` L27、L51；`execute-plan/SKILL.md` L102、L261-268、L486-490；`handoff-protocol.md` L119 |
| G8 | 无 worker 提问出口：票没说「卡住了往哪问」，无人看守时只能猜 | swarm-forge `pack_dashboard_request.sh clarify`；pstack `gates.md` 停车人类 gate；grok `Status: needs-user-input` | `handoffs.prompt` L12-15；`orchestrate.md` L32、L107；`design/SKILL.md` L208 |
| G9 | 无接口 / 数据形状契约字段：票只按小节号指向 spec `Implementation Decisions` | unlazy `Interfaces:`；pstack `feature.md` 派单必带「named data shape and its organizing structure」；architect type sketch 作为契约 | `PLAN.md` L13；`feature.md` L12；`pstack/skills/architect/SKILL.md` L55 |
| G10 | 无时限 | pstack `TIMEBOX`；grok 15 分钟超时 | `orchestrate.md` L47；`execute-plan/SKILL.md` L454-456 |

G1-G4 直接对应用户报告的三个症状（spec 用不上、自我发挥、无视 mockup）；G5-G10 是无人看守的前提，这轮只记录。

## 6. 候选改法（≤5 条，每条只取一家）

| # | 改法 | 取自哪一家 | 出处 | 与其他条的关系 |
| --- | --- | --- | --- | --- |
| C1-A | `## Read first` 之外新增一节，把本票 `Parent` 指名的 `Implementation Decisions` 小节**原文内联**进票；`implement` 改成读票内联段 + `Testing Decisions` + `Out of Scope`，不再读 spec 全文 | grok execute-plan | `execute-plan/SKILL.md` L502-504「read and include the full design doc content that pertains to this PR's scope」 | 与 C1-B 互斥 |
| C1-B | 保持指针，但把 `implement` L10 的「read that in full」改成只读 `Parent` 指名的小节、`Testing Decisions`、`Out of Scope`；spec 其余部分不读 | mattpocock-implement-spec | `mattpocock-implement-spec/SKILL.md` L13「Don't duplicate information already available via pointers」 | 与 C1-A 互斥；A/B 分岔点是「票是否自足」——无人看守跨宿主派发时 A 更稳（worker 拿到票就够），B 改动最小 |
| C2 | 新增 `## Owns`：本票可写的仓库相对 glob，一行一条；并发票之间不相交；同批其余路径视为不可写。相应把 L135 的路径禁令改成「不写实现文件路径，`Owns` 的 glob 除外」 | unlazy | `gates-leaf.md` L3、L40-41；`PLAN.md` L14、L54 | 独立。另一家可选项是 pstack `SCOPE`+`FORBIDDEN`（`orchestrate.md` L42、L48），与 C2 互斥，这轮不取 |
| C3 | UI 票的验收条目改成 pstack 形状：每条写「看到什么」（exact screen state）+ 要保存的截图名 + pass predicate；`## Read first` 里 prototype 条目必须指到 leaf `README.md` 的 verdict 与选中的变体文件，并在 `## Seam` 里写「human check：对照 `prototypes/<task>/<issue>/UI/<winner>` 逐条看」 | pstack multi-phase-plan | `multi-phase-plan.md` L92-94、L100-111、L138-140 | 独立。另一家可选项是 pstack visual-parity 的 image diff（`visual-parity.md` L3-8），需要截图回归 harness，重；与 C3 互斥，这轮不取 |
| C4 | 新增 `## Standing`：一份仓库级常驻规则文件的路径（本地宿主）或全文（远端 / 无文件系统宿主），每张票都带，`implement` 开工前先读 | pstack orchestrate | `orchestrate.md` L27、L51、L54（「Local spawns may reference the standing-orders file by store path; verbatim paste is for cloud spawns」） | 独立。该文件的**内容**是否用 ponytail `AGENTS.md`（`ponytail/AGENTS.md` L1-32）是另一议题，不在本条 |
| C5 | `implement` 收尾评论（L22）加两行固定项：「Deviations from the ticket」与「Skipped」，没有就写 None | grok execute-plan | `execute-plan/SKILL.md` L535-536「Include: files changed, key decisions, any deviations from the plan」 | 独立 |

没有列入的：G3 的 `CHECK:`/`EXPECT:` 逐条命令（unlazy）——它和 C2 同源可以一起收，但它牵动第二阶段「落地中怎么验」，留给下一份研究；G8 提问出口和 G10 时限属于无人看守议题。

## 7. 未读或未确定的事项

1. swarm-forge 快照里没有各角色的 role prompt 目录（`swarm-forge/swarmforge/` 下只有 `constitution/`、`handoff-protocol.md`、`scripts/`），specifier 交给 coder 的 Gherkin 文件长什么样、放在哪，只从 `README.md` L34-35 与 `engineering.prompt` L27-52 推断。
2. grok-bundled 的 `implement/SKILL.md`、`pr-babysit/SKILL.md`、`shared/personas/design-doc-writer.md` 未读；`execute-plan` L1084 说 memory 协议以 `implement` 为准。
3. pstack 的 `autopilot-full.md`、`autopilot-stack.md`、`opening-a-pr.md`、`skills/swarm/SKILL.md`、`control-ui` 未读；`multi-phase-plan.md` L100 的十条 live lane 依赖它们，C3 若采用截图 predicate，需要确认我们的宿主怎么截图。
4. unlazy 的 `references/dispatch.md`、`parallel.md`、`orchestration.md`、`token-economy.md` 未读；`OWNS` 的 claim / release 协议在 `parallel.md`（`gates.md` L132），C2 只取「声明不相交」这一层。
5. 未确定：我们的 worker 到底是谁。`mattpocock-implement-spec/SKILL.md` L25 说每票一个 implementer subagent，但 mmw-v2 的 `implement` 是一个技能而不是 spawn prompt——目前没有任何一处定义「派发一张票时给子代理的那段文字」。C1-A 与 C4 都默认「票本身就是 brief」，这个前提要先定。
6. 未确定：`to-tickets/SKILL.md` L135 的路径禁令与 C2 的 `Owns` 冲突怎么解——本文只提出改措辞，没查上游最近是否动过这一句（见 `mmw-v2/merge-notes/to-tickets.md` L14）。
