# 落地后：证据、验证与评审

问题：worker 交回工作后，用什么判定「做完了，且照设计做的」——谁验、验什么、证据是什么形态、不信自报的机制是什么、偏离设计怎么被抓出来。

路径约定：参考快照的路径都相对 `docs/research/code-landing-refs/`；本仓自己的文件相对仓库根。`file:12-15` 指该文件第 12 到 15 行。

## 1. 一句话结论

我们现在的收尾（`mmw-v2/upstream/skills/engineering/implement/SKILL.md:20-25` 的三步加 `mmw-v2/upstream/skills/engineering/code-review/SKILL.md` 的两轴）全部由写码的同一个 agent 自报、自评、自勾，验收标准没有事先写下的机器可比对的预期输出，也没有任何一步把实现和 `prototypes/<task>/<issue>/UI/` 里选定的 variant 放在一起比；各家参考里最贴合我们缺口、又不需要装任何脚本的做法是 unlazy 的「每条验收标准 = `CHECK:` 命令 + `EXPECT:` 期望输出 + `EVIDENCE:` 记录」（`unlazy/references/gates.md:14-28`、`:50-53`）加 pstack 的「由不同模型家族的 verifier 重跑并给出裁决等级，CI 绿只是输入」（`pstack/skills/poteto-mode/playbooks/orchestrate.md:89-93`）。

## 2. 对照表

| | 我们现状 | unlazy | pstack | grok-bundled | swarm-forge | ponytail |
| --- | --- | --- | --- | --- | --- | --- |
| **谁验** | 写码的 agent 自己：`implement/SKILL.md:18` 调 `/code-review`，`:22` 自己评论证据并打勾。`code-review/SKILL.md:11` 两个并行 sub-agent 出报告，不裁决。 | 三层：leaf 自检 → 父级 `--reverify` 重跑 → branch 集成（`unlazy/references/orchestration.md:77-82`）。手工 gate 由驱动者亲自审并「try to refute at least one passed gate」（`orchestration.md:35`）。 | 单命令的 unit 由 worker 跑、coordinator 抽查收据；昂贵/判断型/高 blast-radius 的 unit 派专门 verifier，且「on a different model family than the worker」（`pstack/skills/poteto-mode/playbooks/orchestrate.md:19`、`:89`）。上线前每个 PR 一个独立 agent 验，「the agent that judges a change is never the one that wrote it」（`pstack/docs/guide/06-verify-and-ship.md:85`；`pstack/skills/poteto-mode/playbooks/shipping.md:7`）。 | orchestrator 只协调，不写码不评审（`grok-bundled/implement/SKILL.md:17`）；1–6 个 reviewer 子代理，含 General / Tests / Security / Plan Alignment（`implement/SKILL.md:126-133`）。 | 流水线下一角色验上一角色：`coder` → `cleaner` → `architect` → `hardender` → `QA`（`swarm-forge/README.md:43-52`）；QA「runs final user-interface verification, checks handoff consistency」（`README.md:50`）。人只在 Attention 面板批 specifier 交接和答澄清（`README.md:125`、`:137-138`）。 | 不验实现；`ponytail-review` 只看 diff 的过度工程（`ponytail/.openclaw/skills/ponytail-review/SKILL.md:47-49`）。benchmark 用 `good`/`bad` 参考件先验证打分器本身（`ponytail/benchmarks/agentic/README.md:71-72`）。 |
| **验什么** | 验收标准四条规则：外部可观察、精确值、一条一判、指明验证处（`to-tickets/SKILL.md:40-43`）；`## Seam` 指明测试层或人工检查的设备与步骤（`to-tickets/SKILL.md:120-122`、`:236`）；Testing Decisions 给测试层、目录、先例、提交前命令（`to-spec/SKILL.md:66-72`）。code-review 验「documented coding standards」与「faithfully implement the originating issue / spec」（`code-review/SKILL.md:8-9`）。 | 每个 gate 一个可观察结果；runnable gate 必须同时有 `CHECK:` 和 `EXPECT:`，manual gate 两者都无，只有一个不算（`gates.md:37`）。gate 必须「Observe the outcome directly」、只在全部断言通过后打印 success marker、跑负向对照、独立测量数字（`gates.md:97-100`）。 | 「Match the check to the change」：CLI 跑真命令、UI 在跑起来的 app 里走改动的流程、迁移回放保存的输入、存储读回写入值（`06-verify-and-ship.md:17-23`）。verification skill 的 Evidence 段要求走真实用户路径、捕捉动作和结果状态、核对副作用（`pstack/skills/create-verification-skill/SKILL.md:30`）。interrogate 的 rubric 有 Verification 一栏：「Check the real thing, not a proxy」、委派工作「does the code verify actual output artifacts, or does it trust self-reports」（`pstack/skills/interrogate/references/rubric.md:45-54`）。 | General：正确性优先于风格、边界、错误处理、跨模块副作用（`grok-bundled/shared/personas/reviewer.md:10-12`）；Plan Alignment：需求全覆盖、偏离计划、scope creep、缺项、接口是否与规定一致（`implement/SKILL.md:558-564`）；Security：只报可追溯数据流的真漏洞（`shared/personas/security-auditor.md:42-45`）。 | 交接前「Run the relevant local verification command」（`swarm-forge/swarmforge/constitution/articles/engineering.prompt:48`）；禁止自造 CRAP/DRY/mutation/coverage 代理工具（`engineering.prompt:51`）。交接审计要「trace every requirement and constraint to role-appropriate work and verification evidence, examine boundaries and failure cases」（`swarm-forge/swarmforge/handoff-protocol.md:253-256`）。 | benchmark 的三个门：correct、safe（对抗输入下不崩）、完整度（`benchmarks/agentic/README.md:65-66`、`:91-100`）。 |
| **证据形态** | 票上一条评论：分支、commit、每条验收标准「the command run and what it printed」，打勾（`implement/SKILL.md:22`）。PR 引用票（`:23`）。EXP 分支的实验才有 evidence page：header、legend、summary table、body、how it decided，「No verdict column: the page reports, the README.md judges」（`mmw-v2/upstream/skills/engineering/prototype/evidence-page.md:14-18`）。 | `EVIDENCE:` 行：resolved shell、cwd、exit status、PATH hash、匹配结果、输出的 SHA-256/字节数指纹；不存成功时的原始输出；手工 gate 记「smallest non-sensitive fact」（`gates.md:57`、`:102`）。 | `ledger.tsv` 一行一裁决，键为 PR 号 + head SHA，值域 `live-ui-verified / unit-test-verified / type-check-only / verifier-blocked / verifier-failed`（`orchestrate.md:91`）。UI 证据 = ARIA snapshot + 带 app 身份的截图；CLI 证据 = 命令、stdout、stderr、exit code；变更证据 = 再读一次存储值（`pstack/skills/create-verification-skill/references/feature-map-example/README.md:25-28`）。PR 描述固定有 `## Verification`，写「how you ran each check and its rigor」和结果，附截图/视频（`pstack/skills/poteto-mode/playbooks/opening-a-pr.md:19-21`）。裁决 `PASS / PASS+NOTES / FAIL` 发在 PR 上（`shipping.md:7`）。决策日志 TSV：ts / phase / decision / why / evidence / result，evidence 是指针不是段落（`pstack/skills/show-me-your-work/SKILL.md:13-22`）。 | 一份 `review_file`：每条 issue 有 `[来源标签]`、Severity、File `file:line`、Description、Suggestion、Status（`implement/SKILL.md:596-616`）；实现者回填 `Status: fixed` + Response 或 `wontfix` + 技术理由（`:660-669`）。安全发现附 Impact、Reproduction（`security-auditor.md:26-34`）。最终报告列轮数、按严重度和按 reviewer 的问题数（`implement/SKILL.md:958-967`）。 | 证据就是 commit：`git_handoff` 只带 `task` 和 10 位 commit 缩写，脚本校验它解析到唯一 commit（`handoff-protocol.md:131-155`、`:312-325`）；`created_at / enqueued_at / dequeued_at / completed_at` 头做审计轨迹（`handoff-protocol.md:513-540`）。 | 留在工作区里的文件本身：`git diff` 的 LOC、被执行的函数、测试是否写了（`benchmarks/agentic/README.md:8-9`、`:65-69`）。 |
| **不信自报的机制** | 无。同一个 agent 写码、跑命令、写证据、打勾、关票（`implement/SKILL.md:20-25`）。`code-review/SKILL.md:66-70` 的 Spec sub-agent 只读 diff 与 spec 文本，不跑任何东西。 | 三重：(1) runnable gate 只有「exit 0 **且** `EXPECT:` 匹配合并输出」才算过，非零退出即使输出含期望 token 也不算（`gates.md:50-55`）；(2) 打了勾但 `EVIDENCE:` 缺失或 `pending` 仍算未过（`gates.md:57`）；(3) 父级 `--reverify` 重跑每个 runnable gate 包括已勾的，`--status` 不算重验（`gates.md:59`；`orchestration.md:29-35`）。另加 `gate-lint.mjs` 在开工前抓「不可能失败的 gate」（`gates.md:106-115`）。 | 「A worker may self-report; a verifier overrides it on the same key. A new head SHA voids the row」（`orchestrate.md:91`）；「CI green is an input to a verdict, not a verdict」（同行）。blast-radius：「Don't trust your own writeup」，安全事实要靠跑真代码证明到第 4 级（`pstack/skills/blast-radius/SKILL.md:15-29`）。prove-it-works：「trust artifacts, not self-reports」（`pstack/skills/principle-prove-it-works/SKILL.md:26-27`）。「treat a confident reply without evidence as a red flag」（`06-verify-and-ship.md:15`）。决策日志收工前对照 transcript 自审，再由不同模型家族的子代理审日志（`show-me-your-work/SKILL.md:54-74`）。 | 靠角色分离：实现者和 reviewer 是不同子代理（`implement/SKILL.md:17`）；orchestrator 亲自读 `review_file` 数 `Status: open`（`:579`、`:994`）。reviewer 有 `Do NOT fix the code yourself`（`reviewer.md:23`）。对自报没有重跑机制——reviewer 读的是实现者写的 summary_file（`:386-387`）。 | `AUDIT_REQUIRED` 二次调用门：第一次合法 `git_handoff` 不入队，打印 `AUDIT_REQUIRED` 并计数；发送者必须重读完整任务与引用源、把每条需求追到证据、修完再审；只有**原样不变**的第二次调用才入队，任何改动作废上次审计（`handoff-protocol.md:248-262`；`README.md:242`）。「Passing checks alone do not establish completeness」（`handoff-protocol.md:256`）。 | 每个打分器自带 `good`/`bad` 参考件，`--selftest` 要求 good 过、bad 被抓，**之后**才花 API（`benchmarks/agentic/README.md:71-72`）；LLM judge 也要先能把故意过度工程的参考排在极简参考之上才可信（`:82-84`）。 |
| **偏离设计怎么抓** | `code-review/SKILL.md:66-70` Spec sub-agent：缺失/部分实现、scope creep、看似实现但错，每条引用 spec 原句。只读 spec 文本；`:51-58` 找 spec 的顺序里没有 prototype 目录。 | 没有「设计」概念；只有 gate 标题 vs 命令是否同义的问题，靠人审：「Approval confirms that a command may run; it does not prove that the command measures the English outcome」（`gates.md:65`）。 | 视觉：visual-parity 以 baseline 截图为 spec，image diff，非零即 fail（`pstack/skills/poteto-mode/playbooks/visual-parity.md:3-8`）。行为：feature map 列出每个用户入口，「a proof that drives one convenient entry point is incomplete when the map lists others」（`create-verification-skill/SKILL.md:36`）；跳过的入口不能报成已验（`feature-map-example/README.md:30-31`）。 | Plan Alignment Specialist：有设计文档路径时「read it in full」，查偏离、scope creep、缺项、接口不一致（`implement/SKILL.md:549-571`）。触发条件是描述里提到 design doc/plan/spec（`:156-158`）。只读文本。 | `specifier` 产出 Gherkin 验收规格，`coder` 生成 acceptance tests，`hardender` 做 Gherkin mutation（`README.md:45-49`；`engineering.prompt:27-38`）。设计偏离由规格测试抓，不是评审抓。 | 不适用（scope 明确排除正确性，`ponytail-review/SKILL.md:47-49`）。benchmark 的完整度 judge 抓「stub 冒充实现」（`benchmarks/agentic/README.md:93-96`）。 |
| **失败与放弃怎么表达** | 「A ticket with an unmet criterion stays open, with the comment saying which one and why」（`implement/SKILL.md:25`）。没有区分「验失败」「验不了」「放弃」。 | `ABANDON: <id> <reason>` 保留原 gate；`gate-check` 打印 `HANDOFF REQUIRED` 并 exit 1，即使其余全过；绝不通过父级 `ALL MET` 提升（`gates.md:128`；`unlazy/SKILL.md:32`）。leaf 状态 `WAITING / READY / IN-FLIGHT / VERIFIED / ABANDONED`（`orchestration.md:9-13`）。最终报告必须给出 met / unmet / abandoned 计数（`unlazy/SKILL.md:82`）。 | 裁决等级里 `verifier-blocked` 不是 pass，环境好了重派；`verifier-failed` 开修复 unit 而不是重验（`orchestrate.md:91`）。维护 verification skill 三种结局 `clean / changed / blocked`，blocked 必须说清卡在哪（`pstack/skills/maintain-verification-skill/SKILL.md:15-17`）。重试按失败模式分类，两次后放弃并绕开（`orchestrate.md:100`）。TIMEBOX 到期「return partial findings and stop」（`orchestrate.md:47`）。 | 没有失败终态：唯一退出是所有 reviewer 同一轮 0 issue，无轮数上限（`implement/SKILL.md:758-762`、`:998`）。争议：实现者 `wontfix` 被 reviewer 重开 → stalemate → 问用户（`:620-643`）。子代理崩溃 → 报错停止（`:1000`）。 | 被歧义/矛盾/规格冲突卡住时用 `pack_dashboard_request.sh clarify` 问操作员，不发 note（`handoff-protocol.md:193-198`）；specifier 交接可被 Reject，卡留在 specifier（`README.md:137`）。 | benchmark 层面：如果各 arm 收敛，「the benchmark says so. It is built to be able to disprove the skill's value」（`benchmarks/agentic/README.md:150-151`）。 |

## 3. 「实现是否照 HTML mockup 做了」：各家能给什么形态的证据

先说清我们这边的 mockup 是什么：`mmw-v2/upstream/skills/engineering/prototype/UI.md:77` 把 variant 组件放在 `prototypes/<task>/<issue>/UI/`，`UI.md:102` 要求胜出的 variant 与原因写进叶目录 `README.md`，`UI.md:116` 明说 variant 是在 prototype 约束下写的、并入时要「Rewrite it properly」。所以「照 mockup 做」的基准是叶目录里那个胜出 variant 在 `?variant=` 下渲染出来的样子，而不是一份独立 HTML 文件。

| 来源 | 证据形态 | 出处 | 对我们的适用度 |
| --- | --- | --- | --- |
| pstack visual-parity | **像素 diff**：先给现有组件各状态截图建 baseline，「No baseline, no parity claim」；逐组件用 image diff 比，「A nonzero diff is a fail; investigate the pixel delta, don't wave it through」；禁止改 harness、改 baseline、为了让 diff 过而重构组件。 | `pstack/skills/poteto-mode/playbooks/visual-parity.md:5-8` | 最强，但它假设「像素一致」是目标。我们的 variant 会被重写成生产代码（`UI.md:116`），像素级不一定该相同；要么把 diff 阈值当「需要人看」的触发器，要么只对结构性的东西（布局、层级、主要控件）截图比。 |
| pstack create-verification-skill | **截图 + ARIA snapshot，人或 LLM 看**：UI 证据「includes an ARIA snapshot and a screenshot with the app identity visible」，捕捉动作和结果状态；每个 feature 文件写「what observable end state proves it works」。 | `feature-map-example/README.md:25-26`；`create-verification-skill/SKILL.md:36` | 证明「行为对了」，不证明「长得和 mockup 一样」；ARIA snapshot 可以和 variant 的 ARIA 结构做文本 diff，这是介于像素和肉眼之间的一档。 |
| unlazy | **manual gate + 引用具体制品**：自动化证明不了的用户可见结果走 manual gate，「cite the exact artifact, location, measurement, or reviewer decision」、「keep the gate unmet if evidence is ambiguous」。 | `unlazy/references/orchestration.md:86-94`；`gates.md:102` | 只给格式不给方法；若我们有截图脚本，可写成 runnable gate。 |
| grok Plan Alignment | **LLM 读设计文档文本再读代码**：「If a design document, plan, or spec is referenced by file path in the conversation context, read it in full」，查「Whether interfaces match what was specified」。 | `grok-bundled/implement/SKILL.md:556-564` | 能读 variant 源码和 README.md 的文字结论，不看渲染结果；对「长得像不像」是间接证据。 |
| swarm-forge | **QA 角色跑 UI 验证脚本**：specifier 写「end-to-end QA procedures」，QA「converts the specifier's QA procedures into executable scripts, runs final user-interface verification」。 | `swarm-forge/README.md:45`、`:50` | 有角色、无方法；快照里没有说 QA 怎么比 UI。 |
| ponytail | 无。 | `ponytail-review/SKILL.md:47-49` | 不适用。 |
| 我们现状 | 无。`code-review/SKILL.md:51-58` 找 spec 时不找 prototype 目录；`implement/SKILL.md:10` 让实现者读「the chosen artifact of a prototype」，但收尾三步不回头比。`evidence-page.md` 只服务 EXP 分支。 | 如左 | 这就是症状「agent 无视 mockup」在流程里的位置：读过，但没有人验。 |

## 4. 验证阶梯：三家放在一起比

| | unlazy 双条件 gate | pstack 验证阶梯 + blast-radius 五级 | grok「0 issues 才退出」 |
| --- | --- | --- | --- |
| 判定单位 | 每条 gate：`CHECK:` 进程 exit 0 **且** `EXPECT:` 匹配合并输出（`gates.md:50-53`）。 | 每个 PR head SHA 一行裁决：`live-ui-verified > unit-test-verified > type-check-only`，`verifier-blocked` / `verifier-failed` 是非 pass（`orchestrate.md:91`）。每个「安全事实」再按五级：1 你说的 → 2 指到 `file:line` → 3 走过失败路径证明到不了 → 4 跑了真代码 → 5 在跑起来的 app 里复现（`blast-radius/SKILL.md:23-27`）。 | 整个 diff：所有 reviewer 同一轮报 0 issue（含 nit）才退出（`implement/SKILL.md:760-762`）。 |
| 可自动化程度 | 最高。runnable gate 完全机器判；manual gate 明确标出来，混不进去（`gates.md:37`）。gate 质量也能 lint（`:106-115`）。 | 中。裁决等级由 verifier agent 写，但每级对应的证据形态是机器可留存的（截图、ARIA、命令输出）；五级里第 4 级「A script or test that calls the real code and fails loud」是可重跑的（`blast-radius/SKILL.md:26`、`principle-prove-it-works/SKILL.md:31`）。 | 低。「0 issue」由 LLM reviewer 判，判断标准在 persona 文本里（`reviewer.md`），结果可数但不可重现。 |
| 代价 | 开工前要为每条验收标准写出命令和期望输出（`unlazy/SKILL.md:12`）；需要能「Emit a success-only marker」的脚本（`gates.md:98`）。没有脚本的项目要先写脚本。 | 需要一个能驱动 app 的 verification skill（`06-verify-and-ship.md:29-39`）和第二个模型家族；pstack 自己承认 ceremony 要按 unit 大小收缩，「A verifier agent whose entire product would be rerunning one command is ceremony」（`orchestrate.md:89`）。 | 无上限循环（`implement/SKILL.md:998`），每轮全体 reviewer 重跑；争议靠 stalemate 上报（`:620-631`）。本仓记忆里有明确教训：reviewer 权限必须限定在票的验收门与 spec 业务对齐，超范围的发现只记录不阻塞，否则无限修/审循环（Nowledge Mem 记忆 `456d6f5e-4eae-4512-a0f4-acffcc5edd86`「Reviewer must not self-set pass criteria in agent-in-the-loop workflows」）。 |
| 抓什么类型的错 | 「说做了其实没做」「命令跑失败但输出里有 ok」「勾了但没证据」「环境不同复现不了」（`gates.md:55-57`；`orchestration.md:84`）。抓不到「命令和标题不同义」（`gates.md:95`）。 | 「CI 绿但行为错」「改了 SHA 裁决失效」（`orchestrate.md:91`；`shipping.md:9`）；「写得头头是道但没跑过」（`blast-radius/SKILL.md:17`）。 | 代码质量、测试覆盖、安全、计划对齐四类文本可见的问题（`implement/SKILL.md:126-133`）。抓不到「测试其实没跑」——reviewer 读的是实现者的 summary（`:386-387`）。 |
| 失败终态 | `ABANDON` → `HANDOFF REQUIRED` exit 1（`gates.md:128`）。 | `verifier-blocked` / `verifier-failed`；`blocked` 结局（`orchestrate.md:91`；`maintain-verification-skill/SKILL.md:17`）。 | 无；只有 stalemate 问用户（`implement/SKILL.md:636-643`）。 |

三者不互斥：unlazy 解决「一条验收标准怎么算过」，pstack 解决「谁来判、判到什么等级」，grok 解决「评审意见怎么闭环」。

## 5. 缺口清单：对照 implement 收尾三步 + code-review

必须补的：

1. **证据由写码者自报，没有任何人重跑。** `implement/SKILL.md:22` 让同一个 agent 写证据并打勾。unlazy 要父级 `--reverify` 重跑每个 runnable gate、「`--status` alone is not re-verification」（`unlazy/references/orchestration.md:29-35`）；pstack 要 verifier 在不同模型家族、「A worker may self-report; a verifier overrides it on the same key」（`orchestrate.md:19`、`:91`）。
2. **验收标准没有事先写下的期望输出。** `implement/SKILL.md:22` 的「the command run and what it printed」是事后自由文本，`to-tickets/SKILL.md:40-43` 的四条规则要求精确值但没要求写成可比对的命令+输出。unlazy 每条 runnable gate 必须开工前就有 `CHECK:` + `EXPECT:`（`gates.md:37`；`unlazy/SKILL.md:12`），且 `gate-lint` 在开工前抓写得不可能失败的 gate（`gates.md:106-115`）。
3. **没有验证等级词汇，勾就是勾。** 一个 `[x]` 分不出「跑了 UI」「跑了单测」「只过了类型检查」。pstack 的 `ledger.tsv` 用 `live-ui-verified / unit-test-verified / type-check-only / verifier-blocked / verifier-failed`，且「Behavioral work needs better than `type-check-only`」（`orchestrate.md:91`）。
4. **实现从不被拿回去和 prototype 的胜出 variant 比。** `code-review/SKILL.md:51-58` 找 spec 的顺序里没有 `prototypes/` 目录；Spec 轴的 brief（`:66-70`）只比 spec 文本。pstack visual-parity 用 baseline 截图 + image diff（`visual-parity.md:5-8`）；退一步，create-verification-skill 的 ARIA snapshot + 截图（`feature-map-example/README.md:26`）。
5. **失败、验不了、放弃是同一句话。** `implement/SKILL.md:25` 只说「stays open, with the comment saying which one and why」。unlazy 用 `ABANDON: <id> <reason>` 保留原 gate、`HANDOFF REQUIRED` 退出码 1、报告必须给 met/unmet/abandoned 计数（`gates.md:128`；`unlazy/SKILL.md:82`）；pstack 分 `verifier-blocked`（环境）与 `verifier-failed`（代码）两种非 pass（`orchestrate.md:91`）。

可以后补的：

1. **code-review 没有「Verification」这一栏。** 两轴都不问「有没有测试、测的是行为还是实现、委派工作是不是只信了自报」。pstack rubric 的 Verification 段（`pstack/skills/interrogate/references/rubric.md:45-54`）。
2. **code-review 的发现没有状态，没有闭环。** `code-review/SKILL.md:74-78` 只汇总，之后没有 fixed/wontfix。grok 的 `Status: open → fixed / wontfix` + Response（`implement/SKILL.md:660-669`）；但闭环必须有界（见 §4 的记忆条目）。
3. **交接前没有自审。** implement 三步直接从 commit 跳到评论。unlazy「Audit the final report」要在报告前重读原请求、重测每个数字（`unlazy/SKILL.md:80-82`）；swarm-forge 的 `AUDIT_REQUIRED` 二次调用门（`handoff-protocol.md:248-262`）。
4. **PR 正文没有固定的证据段。** `implement/SKILL.md:23` 只要求引用票。pstack `## Verification` 段要写「how you ran each check and its rigor」和每项结果，附截图/视频（`opening-a-pr.md:19-21`）；shipping 把 `PASS / PASS+NOTES / FAIL` 裁决贴在 PR 上「so the record outlives the chat」（`shipping.md:7`）。
5. **无人看守时没有可回看的决策轨迹。** pstack `decisions.tsv` 每行 ts/phase/decision/why/evidence/result，收工前对照 transcript 自审，再由另一模型家族出「Attention」段（`show-me-your-work/SKILL.md:13-22`、`:54-74`）。

## 6. 候选改法（≤5 条，一个议题只取一家）

| # | 议题 | 取自 | 做法 | 出处 | 互斥 |
| --- | --- | --- | --- | --- | --- |
| A | 每条验收标准怎么算过 | unlazy | `to-tickets` 出票时，每条验收标准下面带缩进的 `CHECK:`（一条能跑的命令）和 `EXPECT:`（success-only 的子串或 `/regex/`）；写不出命令的标成 manual 并写明看什么制品。`implement` 收尾时每条填 `EVIDENCE:`：exit status、匹配结果、输出指纹；exit 非零或 `EXPECT:` 不匹配就不打勾。 | `gates.md:14-28`、`:37`、`:50-57`、`:97-102` | 与 grok 的「reviewer 报 0 issue 即通过」互斥：A 把通过定义在票上，不在 reviewer 手里。 |
| B | 谁来判、判到什么等级 | pstack | `implement` 收尾三步之前插一个 verifier 子代理，模型家族与 worker 不同，只读，重跑票上每条 `CHECK:` 并在票评论写一行裁决：`live-ui-verified / unit-test-verified / type-check-only / verifier-blocked / verifier-failed`，键为 commit SHA；worker 自报的勾被 verifier 的行覆盖；换 SHA 裁决作废。 | `orchestrate.md:19`、`:89-91`；`shipping.md:7`、`:9` | 与 unlazy 的「父级 `--reverify`」互斥——两者都是「第二个人重跑」，选一种表述；B 选 pstack 是因为它给了裁决词汇，unlazy 的重跑需要装它的脚本。 |
| C | 实现是否照 mockup 做了 | pstack | 票的 `## Read first` 指向 `prototypes/<task>/<issue>/UI/` 时，verifier 在 `?variant=<胜出>` 和实现页各截一组同状态截图，做 image diff；非零 diff 不判 fail，而是把 diff 图和两张原图贴到票评论，让 `Seam` 里命名的人看；一致的才由 verifier 直接判。 | `visual-parity.md:5-8`；`UI.md:77`、`:102`、`:116` | 与 grok Plan Alignment 的「LLM 读设计文本判对齐」互斥。C 把「像素级必须一致」放宽为「diff 触发人看」，因为 `UI.md:116` 要求重写。 |
| D | 失败、验不了、放弃怎么写 | unlazy | 票评论里未过的标准保留原文，下面加 `ABANDON: <criterion-id> <reason>`；有任何 `ABANDON:` 的票不关，评论首行写 `HANDOFF REQUIRED`，末尾给 met / unmet / abandoned 三个数。 | `gates.md:128`；`unlazy/SKILL.md:32`、`:82` | 与 B 的 `verifier-blocked / verifier-failed` 部分重叠：若采 B，D 只保留 `ABANDON:` 语义（worker 主动放弃），verifier 的两种非 pass 归 B。 |
| E | 交接前自审 | swarm-forge | `implement` 在写票评论之前加一步：重读票全文与 `Read first` 每一项，把每条验收标准追到对应的 `EVIDENCE:`，列出边界与失败路径各查了什么；第二遍原样不变才允许进入收尾三步。不装脚本，靠技能正文要求「第二遍」。 | `handoff-protocol.md:248-262`；`README.md:242` | 与 unlazy「Audit the final report」（`unlazy/SKILL.md:80-82`）互斥，两者同一议题。 |

未取 grok「0 issues 才退出」的原因：本仓记忆 `456d6f5e-4eae-4512-a0f4-acffcc5edd86` 明确禁止无界修/审循环，reviewer 只能对票的验收门和 spec 业务对齐判定；grok 自己的 stalemate 机制（`implement/SKILL.md:620-643`）也证明这种循环需要人兜底。

## 7. ponytail 探针法：作为「技能改动验收工具」的最小做法

这是离线测量技能文本效果的方法，不是运行时门禁。适用场景：改了 `implement/SKILL.md` 收尾段或 `to-tickets/SKILL.md` 的验收标准规则后，想知道 worker 的行为有没有真的变。

ponytail 的做法（`ponytail/benchmarks/agentic/README.md`）：
- 单元是「一个 headless 会话在种子工作区里编辑」，打分只看留下的文件，不看对话（`:8-9`）。
- baseline 是「没有这个技能的真实 agent」，差异才归因于技能（`:23-24`）。
- 每个打分器带 `good`/`bad` 参考件，`--selftest` 要求 good 过、bad 被抓，之后才花钱（`:71-72`）；`bad` 是「happy path 正确、对抗输入下不安全」的懒版本，正是二元正确性门会放过的那种（`:60-61`）。
- 工作区保留，度量改了用 `--rescore` 离线重算（`:134-139`）。
- 隔离教训：SessionStart hook 在每个 arm 都触发，baseline 偷偷跑了技能，结果作废（`:169-172`）。

我们的最小版本（不装 ponytail 任何脚本，本仓没有 CI、测试手工跑，见 `AGENTS.md` 首段）：

1. 种子：一个小仓库快照 + 一张按 `to-tickets/SKILL.md:106-133` 模板写好的票，票的 `Read first` 指向一个 `prototypes/<task>/<issue>/UI/` 叶目录。
2. 两个 arm：现行 `implement/SKILL.md` vs 改后的；各跑 2–4 次 headless 会话，只允许写文件。
3. 打分器是确定性的文件检查，每个先用 `good`/`bad` 参考件自检：票评论里每条验收标准是否有 `CHECK:` / `EXPECT:` / `EVIDENCE:` 三行；`EVIDENCE:` 的 exit status 与「打勾」是否一致；PR 正文有无 `## Verification` 段；评论里有无引用叶目录 README.md 里胜出 variant 的名字。
4. 「照 mockup 做了」这一项没法确定性判，学 ponytail 的 judge：固定模型、温度 0、公开 rubric、每个分数必须点名具体构件；先用「故意无视 mockup」和「照做」的两个参考件自检，judge 排序对了才用（`:74-84`）。
5. 隔离：每个 arm 用独立的技能目录和设置来源，确认 baseline 会话里没有加载新技能（`:169-172` 的教训）。

## 8. 未读或未确定的事项

- 未读：`unlazy/templates/`、`unlazy/references/parallel.md`、`dispatch.md`、`method.md`、`token-economy.md`、`SECURITY.md`；`gates.md:65` 引用的完整威胁模型在 `SECURITY.md`。
- 未读：`pstack/skills/poteto-mode/playbooks/babysit.md`、`autonomous-run.md`、`feature.md`、`eval.md`（`eval.md` 从 README 描述看是「blinded 测技能改动」，和 §7 可能重叠，值得对照）；`control-ui` / `control-cli` 不在快照里（`pstack/README.md:229-235`），visual-parity 的「image diff on the matching surface via the control skill」（`visual-parity.md:8`）具体怎么做没看到。
- 未读：`grok-bundled/shared/personas/implementer.md`、`grok-bundled/pr-babysit/`、`execute-plan/`、`design/`。
- 未读：swarm-forge 的角色提示 `roles/QA.prompt` 等和 `handoffs.prompt`、`workflow.prompt`；README.md:50 说 QA 做 UI 验证，方法在角色提示里。
- 未读：`ponytail/benchmarks/agentic/run.py`、`judge.py`、`complete.py`、`tasks.py` 与 `results/2026-06-18-agentic.md`；§7 的 judge 细节来自 README 描述。
- 未读：`mattpocock-implement-spec/`（不在本阶段分配范围内）。
- 未确定：任务描述说的「HTML UI mockup」与 `prototype/UI.md:77` 描述的「variant 组件放在叶目录、在真实路由上用 `?variant=` 渲染」是否是同一个东西；若实际产出是独立 HTML 文件，§3 与候选 C 的截图基准要改成直接打开该文件。
- 未确定：宿主能否截图和做 image diff。技能列表里有 `playwright-cli`，但本文没有查它的能力；候选 C 依赖这一点。
- 未确定：候选 A 要求每条验收标准配 `CHECK:` 命令，`to-spec/SKILL.md:66-72` 的 Testing Decisions 只给测试层和命令，没给「每条标准一个命令」的粒度；是否要在 `to-spec` 就要求，属于第一阶段（落地前）的议题。
- 未确定：unlazy 的 `EVIDENCE:` 记录 PATH hash 和输出指纹（`gates.md:57`）是它的脚本算的；我们不装脚本时，`EVIDENCE:` 该记到什么粒度只能手写约定。
