---
slug: landing-orchestrator
summary: 新增编排技能与规划者 subagent：Herdr 会话内无人值守循环，跨宿主派发两级工人、复验分诊、停车 issue、失败升级，直至 frontier 排空、PR 全开好
date: 2026-08-25
branch: landing-orchestrator
spec_issue: 55
artifact_refs: []
---

# 编排技能 spec

> 三份一组中的第三份，依赖 landing-closeout（票能干净收尾）并使用 discipline-hooks（纪律送达）。架构决定见 ADR 0020（载体分配）；角色×模型矩阵、复验轮次上限、停车形态、夜间不问人等策略全部为用户在 grill 会话中的直接指定。

## Problem Statement

票拆好、能干净收尾之后，仍然没有东西驱动整批票：不能并行落地（上游 implement 文档页自认「Batch dispatch … and subagent fan-out … neither exists」）、上游关票后没有人去派发被解锁的下游票、卡住的问题会堵死单个会话。用户的目标形态很具体：白天讨论拆票，睡觉时 agent 自动落地全部票——能自动修的修完、PR 开好、卡住的决策整理成 issue——醒来只做裁决、真机测试、合并。夜间绝不允许向用户提问，也绝不允许无限修复循环（用户在旧版工作流里被两者都坑过）。

## Solution

新增编排技能（编排者 = 运行它的主会话）与规划者 subagent。编排者在 Herdr 会话里跑循环：规划一次 → 查 frontier → 认领 → 按定级把每票派给对应宿主的工人（Herdr pane + worktree）→ 工人完成后派复验者 subagent → 按判决分诊（通过则票已收尾、下游解锁；要修则回原工人限一轮；卡住则停车成 issue 并推送手机）→ 循环到 frontier 排空。角色到模型的映射放在消费仓库一张可编辑的表里。

## User Stories

1. As a 维护者, I want 睡前一条命令启动整批票的无人值守落地, so that 醒来时 PR 已开好、只剩裁决与合并
2. As a 维护者, I want 能并行的票真的并行落地, so that 整批票的墙钟时间不是串行之和
3. As a 编排者, I want 落地前由规划者产出执行计划（并行分组、每票简报、定级复核）, so that 派发不靠临场猜
4. As a 编排者, I want frontier 由 tracker 查询算出（开放、无阻塞、无认领）, so that 上游关票后下游自动进入待派队列
5. As a 编排者, I want 认领用 assignee 作为第一个写动作, so that 并行会话不会抢同一张票
6. As a 编排者, I want 按票的定级标签把票派给初级或高级工人, so that 简单票不烧贵模型、难票不砸在弱模型手里
7. As a 编排者, I want 每票一个 worktree 一个 Herdr pane, so that 并行的工人互不踩工作区
8. As a 编排者, I want Herdr 识别出工人处于 blocked 状态时读出问题并停车, so that 工人卡在提问界面不会挂死整夜
9. As a 维护者, I want 每个卡点是一张独立的决策 issue（问题/选项/后果/默认四段）挂在任务父 issue 下, so that 醒来一条命令列出全部待裁决项
10. As a 维护者, I want 只有停车才推送手机, so that 通知不被进度噪音淹没
11. As a 编排者, I want 复验不过时把发现递回原工人 agent 自动修一轮（上下文还在）, so that 修复不从零重读票
12. As a 维护者, I want 每票复验最多两次、中间夹一次自动修、到顶即停车让路, so that 永远不出现无限 review 循环
13. As a 编排者, I want 同一票连续失败后升级 advisor、仍无解则停车, so that 死磕不会烧掉整夜额度
14. As a 编排者, I want 判断工人死活只认副作用（commit、关卡状态文件、票评论）, so that 安静的长任务不被误杀、真死的不被空等
15. As a 维护者, I want 角色×宿主×模型×强度的映射放在一张我随时可改的表里, so that 调成本不用改技能
16. As a 维护者, I want 编排全程只在 Mac 本机运行、绝不触碰 Win-PC 与 ECS, so that 夜间自动化不可能碰到真机验收与生产环境

## Implementation Decisions

**前置检查（技能第一步，任一不过即报错退出，不降级硬跑）。** `HERDR_ENV` 为 1（编排者必须在 Herdr 管理的 pane 里）；`gh` 已认证且仓库有远端；消费仓库存在 `docs/agents/models.md`；Herdr 的 agent kinds 覆盖表内宿主。Herdr 命令语法以本机 `herdr --help` 现查（其技能文件的既有指引；Herdr 尚在 0.x）。

**models.md（消费仓库 `docs/agents/`，与 issue-tracker.md 同目录同模式）。** 一张表：角色（固定左列：编排者、规划者、初级工人、高级工人、复验者、升级顾问）→ 宿主 kind、模型串、思考强度。首版取值为用户指定：编排者 CC·Opus 5·med，规划者 CC·Opus 5·high，初级工人 Cursor·Grok 4.6·high，高级工人 Grok Build·Grok 4.6·xhigh，复验者 CC·Opus 5·high，升级顾问 CC·Fable 5·med。编排技能运行时现读；用户改表即生效，不改技能。

**规划者 subagent（新 agent 定义）。** 落地开始前派发一次，输入是任务父 issue 与全部子票，输出执行计划：契约（接口、命名、工具链、约定——unlazy 契约七项裁剪到票已覆盖项之外）、并行分组（对每票从 spec 与仓库现场推出改动范围集合，保守判重叠——不确定一律串行；范围集合不写回票，票内禁路径是既有纪律）、每票定级复核、每票简报的定制段。计划以固定标题的评论写在任务父 issue 上（固定标题供下游按位置读取，ADR 0002 的既有约定）。

**派发与简报。** 每票：`herdr worktree create --branch ticket/<票号>-<slug>` → pane → `agent start ticket-<票号> --kind <models.md 宿主>` → `agent prompt --wait` 递简报。简报是封闭清单（unlazy 原则）：契约 + 票全文（含关卡）+ 该票依赖的上游产出摘录（依赖是上下文接力，不只是顺序——上游票的关键产出全文粘贴，工人看不到兄弟票）+ 纪律块（每轮重贴，防长跑指令漂移）+ 汇报格式。纪律送达按宿主能力：Grok 工人经 `--rules` 单次注入（herdr `agent start` 的 `--` 之后传原生参数）；Cursor 无单次注入参数，纪律随简报正文走；CC 侧角色由 hook 层覆盖。

**循环与状态。** 主循环：查 frontier（tracker 查询：开放、无阻塞、无认领，命令引用 issue-tracker-github.md）→ 对可并行集内每票认领（assignee）并派发 → 等待事件（Herdr `agent wait`；blocked → 读屏取问题 → 停车；done → 触发复验）→ 分诊 → 收尾或停车 → 回到查 frontier，直至 frontier 空且无在途票。完成判定只读硬状态：关卡状态文件、票的关闭状态、分支 commit；终端画面只在 blocked 时读。留痕：每票的关键决策（派给谁、判决、分诊结果、重试原因）写成该票的评论。

**复验与分诊。** 工人完成后派复验者 subagent（landing-closeout 定义的 agent；派发 prompt 带票号、分支、commit）。判决 fail 时按发现分诊：fix 类经 `herdr agent prompt <原工人名>` 递回**原工人 agent**（pane 常驻、上下文还在）自动修一轮，修完以宿主的消息续用能力唤醒**同一个复验者 subagent**做第二次复验（它记得第一轮发现，只核对是否命中）；dismiss 类记录进票评论；park 类停车。硬上限：每票复验 2 次、自动修 1 轮，到顶即停车让路。

**失败、升级与存活。** 失败分类处理（蓝本 pstack liveness）：资源类失败缩小范围重派、网络类原样重试、工具类换模型重试（初级→高级即定级升级，只升不降）、未知重试一次；同票两败弃单绕开并停车记录；升级链：初级两败→高级接手→高级再败→advisor（现有 subagent）→仍无解→停车。存活判定只认副作用（commit 出现、关卡状态文件变化、票评论更新）；Herdr 的 unknown 状态不算死亡证据。整夜绝不向用户提问；停车与循环终止各推送一条通知——经编排者宿主的推送通知能力（按能力描述；本机该能力已启用）。

**停车 issue。** 每卡点一张，标签 `blocked:decision`，挂任务父 issue 为父；正文固定四段：问题、选项、各选项后果、不裁决时的默认（格式蓝本是 pstack `pstack/skills/poteto-mode/scripts/orch/store.ts` @46125561 的 `renderGates` 渲染器，`gates.md` 是它生成的产物，不是文件；加「后果」段）。停车不阻塞循环，该票让路。

**边界。** 单仓库；跨仓库依赖出现即停车。绝不触碰 Win-PC 与 ECS（agentflow 三机拓扑，夜间自动化只在 Mac）。合并 PR 永远不做（远端合并需用户明确授权，是放开 push 时保留的边界）。

## Testing Decisions

外部可观察行为，分三档递进验收：①单票穿行——一张真实小票全程无人工介入跑到 PR 开好，检查项与 landing-closeout 的 tracer bullet 相同再加「全程无提问」；②依赖对——两张有原生阻塞关系的票，上游收尾后下游被自动派发（frontier 查询的可观察输出）；③过夜批——一批真实票跑整夜，晨检清单：PR 数、停车 issue 数、每票评论里的决策留痕完整、无一次向用户提问。停车路径用一张故意含未决问题的票触发，验证 issue 四段、父子挂接、推送各就位。复验轮次上限用一张故意修不好的票验证「2 次到顶即停车」。herdr 控制类命令的断言基于其 JSON 输出字段；读屏仅限 blocked 时取问题文本这一处。

## Out of Scope

- 跨仓库编排；cloud agent 派发（Herdr 后续能力，另行评估）
- 自动合并；babysit/watch-pr 式 PR 看护（仓库无 CI，暂无看护对象）
- 度量自动化（探针法作为纪律入选门槛写在 discipline-hooks，不在此建跑批工具）
- models.md 之外的成本控制（预算计量、额度告警）

## Sources

- ADR 0020（Herdr 派发工人、CC 内角色走 subagent）；ADR 0022（判决与关卡语义）；根 `CONTEXT.md`
- **五 CLI 无头调用矩阵：本目录附件 `headless-cli-matrix.md`**（本机取证记录；herdr 能力以本机 `herdr --help` 现查）；图形化全景见调研 artifact <https://claude.ai/code/artifact/280359df-e0fb-445c-81c6-9bd6882ecd35> 第 9 章
- 循环蓝本：**本目录附件 `unlazy-orchestration-blueprint.md` 与 `unlazy-method-blueprint.md`**（unlazy <https://github.com/Leonxlnx/unlazy> @754d9a6 两份 reference 的逐字副本：driver loop、简报封闭清单、契约七项）；失败处理蓝本：pstack <https://github.com/cursor/plugins> `pstack/skills/poteto-mode/playbooks/orchestrate.md` 的 liveness 一节（@46125561）；frontier/认领实现：`docs/agents/issue-tracker.md`「Wayfinding operations」与 wayfinder 技能的既有用法
- 消费仓库现状（agentflow）：三机拓扑约束、`ready-for-agent` 流转先例、无 CI 的验收现实——2026-08-24 现场探查

## Further Notes

Herdr 的 `agent prompt --wait` 等待的是生命周期稳定态而非单轮完成，长任务的完成信号以硬状态为准，这也是「只认副作用」的原因之一。规划者对改动范围的推断是并行安全的关键假设，首个过夜批之前应在依赖对验收中刻意安排一对「看似无关实则同文件」的票检验保守性。agentflow 的 `docs/ui-qa-wiring/` 缺件是 UI 票复验一致性检查的前提，属消费仓库落地清单，随首批真实票补齐。
