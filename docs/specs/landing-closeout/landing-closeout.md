---
slug: landing-closeout
summary: implement 补完成步骤、to-tickets 产验收关卡与定级、新增自查技能与复验者 subagent，让一张票能无人值守地干净收尾
date: 2026-08-25
branch: landing-closeout
spec_issue: 53
artifact_refs: []
---

# 落地收尾与验收关卡 spec

> 这份 spec 来自 2026-08-24 至 25 的一次 `/grill-with-docs` 访谈，访谈之前有一轮对四个参考项目（swarm-forge、pstack、unlazy、ponytail）的系统调研。全部架构决定已落 ADR 0020–0022 与根 `CONTEXT.md` 词汇表；纪律原文逐字存档在本目录 `discipline-sources.md`。本 spec 是三份一组中的第一份，另两份是纪律注入层（discipline-hooks）与编排技能（landing-orchestrator）。

## Problem Statement

用户把一个功能讨论清楚、拆成带阻塞关系的票之后，落地阶段完全靠人手工驱动。上游 implement 技能的文档页自己承认了两个断点：跑完不关票（frontier 永不推进）、不开 PR（「There is no configuration flag and no PR mode」）；第三个断点由技能正文顺序推得——它在 commit 之前调用 review，而 code-review 只比对已提交的 diff，因此无内容可审。更深一层：票的验收条目停留在散文里，agent 说「做完了」时没有任何机器可判的依据；也没有一个没看过实现过程的角色来复核这个声明——用户在旧版工作流里被「reviewer 总能挑出错、自设标准导致过度设计」坑过，明确要求复验必须锚定在票内既定判据上。

## Solution

让「一张票」成为可以干净收尾的单元：拆票时验收条目就被磨利成可判定的关卡（能跑的带检查命令与期望输出，跑不了的显式标为人工项）；工人做完先用自查技能过一遍自己的活，逐条跑关卡留下证据；然后自动收尾——commit 引用票号、推票分支、开 PR、关票，下游的票经 GitHub 原生阻塞关系自动解锁。一个冷启动的复验者 subagent（非作者）重跑全部关卡、对照 spec 复核声明，判决绑定 commit 写进票的评论。全部改动都是技能与 subagent 定义层面的 Markdown，不引入新运行时。

## User Stories

1. As a 维护者, I want 拆票时验收条目自动带上可跑的检查命令与期望输出, so that 「做完」有机器可判的定义而不是 agent 的自述
2. As a 维护者, I want 写不成命令的验收条目被显式标为人工项并指定裁决人, so that 机器判不了的部分不被假装覆盖
3. As a 维护者, I want 拆票时每张票带上初级/高级定级标签, so that 派工时不同难度的票走不同的工人与模型
4. As a 维护者, I want 票之间的阻塞关系用 GitHub 原生依赖建立而不是正文文字, so that 上游关票时下游自动变为无阻塞、机器可查询
5. As a 工人 agent, I want 票本身就是完整的工作简报（含关卡与参考物链接）, so that 我不需要去别处拼装上下文
6. As a 工人 agent, I want 一份自查清单技能在交活前过一遍自己的产出, so that 低级问题在复验之前就被我自己清掉
7. As a 工人 agent, I want 勾选关卡时必须附上检查输出的决定性片段, so that 我的完成声明自带证据
8. As a 维护者, I want implement 在完成时自动 commit（引用票号）、推票分支、开 PR、关票, so that 我回来时只需要测试与合并
9. As a 复验者 agent, I want 冷启动、只拿到票号与分支, so that 我的判断不被实现过程的叙事污染
10. As a 复验者 agent, I want 重跑全部关卡而不是采信工人写的证据, so that 伪造或过期的证据被抓住
11. As a 复验者 agent, I want 一条铁律禁止我自设通过标准、超出票范围的发现只记录不阻塞, so that 我不会像旧版 reviewer 那样把流程拖进过度设计
12. As a 维护者, I want 复验判决绑定「票号 + commit」写进票的评论, so that 代码再变时旧判决自动失效、审计有据
13. As a 维护者, I want 复验发现用一行一条、带位置与替代物的格式书写, so that 每条发现都能被机械执行而不是疑问句
14. As a 维护者, I want 手动开两个窗口跑两张有依赖的真实票来验证全流程, so that 编排循环开建之前地基已被证实
15. As a 维护者, I want 四家参考项目的纪律原文逐字存档在 spec 目录, so that 将来替换纪律来源时有原件可对

## Implementation Decisions

**验收关卡格式（写进 to-tickets 的票模板，ADR 0022）。** 票的验收小节仍是 `- [ ]` 条目列表；可跑条目在其下缩进两行 `CHECK:`（无交互命令）与 `EXPECT:`（期望出现在输出中的成功标记），完成时由工人在条目下追加 `EVIDENCE:` 行（检查输出的最小决定性片段）。通过判定是双条件：进程退出码为 0 且输出含 EXPECT 标记。人工条目不写 CHECK/EXPECT，改写一行 `MANUAL: <裁决人>`。关卡写法遵守存档 `discipline-sources.md` 第 2 章「Author gates that can fail」中与可跑检查相关的五条（意译）：直接观测结果物、成功标记只在全部断言通过后打印、否定断言先过正例、给定数字独立测量、证据取最小决定性输出。

**定级与阻塞边（写进 to-tickets）。** 拆票时为每票打 `worker:junior` 或 `worker:senior` 标签，用户批准拆分时顺手校准；运行中只升不降（升级策略属编排 spec）。阻塞关系必须用 GitHub 原生依赖 API 建立，具体命令引用本仓 `docs/agents/issue-tracker.md` 的「Wayfinding operations」一节（ADR 0023 过继后已落位），不再允许写成正文 `Blocked by:` 文字。两处改动都写 merge-note（to-tickets 是上游技能）。

**implement 的完成步骤（替换正文末句「Commit your work to the current branch」；步骤序列是本 spec 的净新决策，其中关卡留证一步承接 ADR 0022 的「勾选不算数、证据才算数」）。** 顺序：既有的「开写之前先读」段不动（并由 discipline-hooks spec 钉为承重句）→ 实现 → 调用自查技能 → 逐条跑关卡、勾选并附 EVIDENCE → commit message 引用票号（这同时满足上游 code-review 按 commit 引用找 spec 的前提）→ 创建并推送票分支（命名 `ticket/<票号>-<slug>`）→ 开 PR（正文链接票）→ 关票。写 merge-note。

**自查技能（新技能，`mmw-v2/skills/`）。** 工人在跑关卡之前对自己的产出过一遍清单；清单内容取存档第 3 章 swarm-forge cleaner 的八条局部清理项（名字、内聚、局部耦合、重复、复杂度、测试可读性、过期注释、死代码），每条保留原文的边界限定（不改行为、不动架构）。它是技能不是 subagent：自查的价值在于同一个 agent 带着实现上下文自我反省。

**复验者 subagent（新 agent 定义，`mmw-v2/agents/`，ADR 0020）。** 冷启动，派发 prompt 只带票号、分支、commit。body 定义身份与边界：重跑全部关卡（不采信 EVIDENCE 行）、对照票与其 Parent spec 复核业务对齐、UI 票按票内引用的设计参考物检查一致性；never 清单：不修改任何文件、不自设票外的通过标准、超出票范围的发现只记录不计入判决。输出契约两部分：判决行（`verdict: pass|fail @<commit>`，由派发方写进票评论）与发现列表（行格式 `位置: 标签 问题. 替代物.`，格式借自 ponytail-review 并注明标签集按本流程重定义；零发现时输出固定句收尾）。装配走既有 `assemble.py`，注意其两个已知坑：body 内不能出现三连单引号、五宿主键必须给全（grok 一家两份产物）。

**纪律来源存档。** 已完成的 `discipline-sources.md`（1298 行、35 个抄录块、逐块行数校验，另经独立脚本核对原文子串完整出现）随本 spec 落在 `docs/specs/landing-closeout/`，各章标注启用状态；工人纪律按主题单源：反过度构建取第 1 章 ponytail、反偷懒取第 2 章 unlazy v1、反作弊取第 3 章 swarm-forge 护栏；第 4 章 pstack 原则整体不启用、存档备换。本 spec 只落存档与出处约定，纪律的送达机制属 discipline-hooks spec。

## Testing Decisions

好测试只看外部可观察行为。本 spec 的最高接缝是**票的可观察状态**，不新增代码接缝：一张票跑完后，用 `gh` 能查到票已关闭、阻塞下游的依赖已解除、票分支存在且 commit 引用票号、PR 已开、票正文关卡逐条勾选且带 EVIDENCE、复验判决评论存在且绑定 commit。

验收方式是 tracer bullet：在真实仓库拆两张有依赖关系的小票，手动开两个会话按新 implement 跑完上游票，观察下游票经原生依赖自动变为无阻塞，再跑下游票与复验者。关卡格式本身用一正一反例自证（一条会诚实失败的关卡 + 一条断言恒真的坏关卡，确认判定分别为过与不过）——这是 ponytail「量具先自证」门槛在本 spec 的最小应用。技能文本无自动化测试先例可循（仓库现有 tests 只覆盖脚本），不为散文建 runner；机械校验只判机器能判的事实，此为仓库既有边界。

## Out of Scope

- 纪律的 hook 送达、Stop 完成拦截、承重句机械校验（discipline-hooks spec）
- 编排循环、规划者、models.md、停车 issue、失败重试、herdr 派发（landing-orchestrator spec）
- 跨仓库依赖；CI；visual-parity 像素比对；pstack 原则的启用
- 自动合并 PR（合并始终由人做；远端合并仍需明确授权）

## Sources

- 设计对话与全部裁决：2026-08-24/25 grill 会话；调研综述 artifact <https://claude.ai/code/artifact/280359df-e0fb-445c-81c6-9bd6882ecd35>
- ADR 0020（载体分配）、0022（关卡进票正文）；根 `CONTEXT.md`（术语）
- 纪律原文存档：本目录 `discipline-sources.md`（含各来源仓库 commit）。四家上游仓库地址：swarm-forge <https://github.com/unclebob/swarm-forge>（main @7c1d1c9，six-pack 分支 @b933d68）；pstack <https://github.com/cursor/plugins> 的 `pstack/`（@46125561）；unlazy <https://github.com/Leonxlnx/unlazy>（v1 @baf39ef，main @265fbd5）；ponytail <https://github.com/DietrichGebert/ponytail>（@2ed6c52）
- 被修改的上游技能：`mmw-v2/upstream/skills/engineering/{to-tickets,implement}/SKILL.md` 及各自 merge-note
- GitHub 原生依赖命令：`docs/agents/issue-tracker.md`（种子出处 `mmw-v2/upstream/skills/engineering/setup-matt-pocock-skills/issue-tracker-github.md`）

## Further Notes

上游文档页对断点的自认原文在调研 artifact 第 1 章逐条给出出处（「neither exists」「no PR mode」出自 implement 文档页；「no auto-dispatch mode」出自 to-tickets 文档页）。复验铁律的动机是用户在旧版 MMW 用 codex 做 reviewer 的实际教训：无限 review 必然产出发现，唯一的止损是把判据锚死在票内。复验上限（2 次复验夹 1 次自动修）与升级链属编排 spec，但复验者 body 不得包含与之冲突的自主循环。
