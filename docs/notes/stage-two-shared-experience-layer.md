# 阶段二与阶段三：共享经验和跨夜学习闭环

日期：2026-09-14

对象：[《Project Context 调研与 MMW 方案》](https://claude.ai/code/artifact/b9520c08-eb0d-40f1-872e-228662445954?via=auto_preview)第 6 节“阶段二 · 共享经验层 · NOWLEDGE MEM 自带机制优先”、第 7 节“阶段三 · 跨夜学习”和第 9 节“决定”

性质：阶段二与阶段三共同实施前的研究结论，不修改产品代码

## 结论

来源：D01。

阶段二与阶段三作为一条反馈闭环共同实施：阶段二让 worker 在同一 task 内直接写入和取得已证实的经验；阶段三在每份 spec 的 `summary` 之后复盘 ticket event 与 `git log`，把跨 ticket 或跨 night 第二次出现的问题提议为自动检查、reviewer Rule、repository `AGENTS.md` Gotchas、repository script、MMW skill 或 `mmw-toolbox` Memory。owner 批准后的结果在后续 worker、reviewer 或检查中生效。

task root 仍按已经确认的语义解析：spec 有 native map parent 时，map 是 task root；spec 没有 map parent 时，该 standalone spec 自己就是 task root。一个 map 可以拆成多份 spec 并行执行，这些 spec 下的 worker 和 reviewer 使用同一个 task scope；standalone spec 下的全部 ticket 使用该 spec 的 task scope。task root 决定执行时谁共享经验，不限制阶段三在 repository 内识别跨 task、跨 night 的重复问题。

阶段二只有两条读取路径：

1. `dispatch.sh start <ticket> worker` 根据 GitHub native parent 得到 task root，按 task scope label 读取一次当前 task 已有的 Memory，放进 worker 的首次 prompt。
2. worker 遇到具体的非显然故障时，以实际错误、命令和组件主动做 semantic search；先搜当前 task，仍没有答案时再搜当前 repository Space 和已批准的 `mmw-toolbox`。

worker 一旦证实一条同一 task 其他 ticket 可复用的经验，就立即写入 repository Space，并带当前 task root 的 scope label。后来启动的 worker 会自动得到它；已经运行的 worker 在遇到相同问题时通过主动检索得到它。

reviewer 的首次 prompt 不放 Memory 检索结果；需要常驻的 review 经验只以 `mmw-reviewer` active Rules 注入。reviewer 独立读取 ticket、repository authority 和运行检查。这直接保留 Artifact 对 verifier/reviewer 干净上下文的设计。

不增加实时消息系统、Memory relay、retro 数据库或新的审批队列。必须立即改变其他 ticket 行为的信息继续使用现有 `contract`、`fault` 或 `decision` tracker event。retro 使用一个 script-written `spec.retroed` event 留在 spec comment 中；proposal 先进入现有 `needs-triage` 队列，owner 决定是否落入长期载体。

## 逐项设计来源

下面的编号同时标在各设计章节和 HTML 图中。`Artifact` 指本文件开头链接的《Project Context 调研与 MMW 方案》；“owner 修正”指本次讨论里已经明确的产品决定；“MMW 适配”只说明为了接入现有结构必须改哪一个接口，不增加独立机制。

| 设计 | 当前方案 | 直接来源 | 对 MMW 的精确修改 |
| --- | --- | --- | --- |
| D01 | 阶段二与阶段三共同实施 | owner 修正；Artifact 第 6、7、9 节 | 把两段设计放进同一份 spec，仍保留 `summary → retro` 的先后 |
| D02 | 每个 repository 一个 Space，只共享 `mmw-toolbox`，Default 不进入 pipeline | Artifact 第 6 节“布局”、第 9 节“Nowledge Mem 布局”；Nowledge Mem `Spaces` | 因 Nowledge Mem 当前 `strict` 不能读取 shared Space，repository Space 使用 `shared`，其 `sharedSpaceIds` 只含 `mmw-toolbox` |
| D03 | `mmw-worker`、`mmw-reviewer` Identity 与 runner 环境路由 | Artifact 2.1；Nowledge Mem `Agent identity`；现有 runner adapters | runner 设置 `NMEM_SPACE` 与 `NMEM_AGENT_ID`；Identity 只记录 provenance 和选 Rule |
| D04 | Thread 与 Working Memory 只负责跨夜宽背景 | Artifact 2.1、2.2；Nowledge Mem `Background Intelligence`、`Context` | 不建立 task Working Memory，也不让它承担同夜送达 |
| D05 | task root 为 `map if present, otherwise spec` | owner 修正；`docs/contexts/tickets/CONTEXT.md` 的 `map`、`spec`、`sub-issue`；`tree.py` 的 native parent graph | 从 spec native parent 机械解析 scope；从 map 发布 spec 时补齐 native parent 与 read-back |
| D06 | worker 启动时只读取一次当前 task Memory | Artifact 2.2“当夜由派发脚本查一次”；owner 对 title/`## Owns` 的修正 | `dispatch.sh start … worker` 把原来的 title/`## Owns`/`--time today` 改为 task scope label；不增加第二次历史 seed |
| D07 | worker 遇到具体问题时主动搜索历史经验 | Artifact 2.2“worker 也可以按技能文本自己搜”；Nowledge Mem `memories search` | `implement/SKILL.md` 指定用实际 error、command、component 搜索，不轮询 |
| D08 | worker 当场写事实与证据 | Artifact 2.1；monomind `context_capture.py` 的 capture/provenance；Augment Expert Memory 的 evidence log 与“代码可推得则不存” | 在 Artifact 的 ticket/type labels 上补 task-root 和 spec labels，以支持 map 共享与按 spec 收口 |
| D09 | reviewer 的首次 prompt 不放 Memory 检索结果；常驻经验使用 active Rules | Artifact 2.2“角色”；`research-4-theory.md` 的 `A14. 验证者用干净上下文`；Augment Review Guidelines | `start … reviewer` 不调用经验检索；长期 reviewer 行为进入 `mmw-reviewer` active Rules |
| D10 | Memory 不替代 tracker event | Artifact 2.1、第 9 节“经验不经票事件”；`events.py` 的 event fold | 经验直接写 Nowledge Mem；会改变票状态或立即唤醒 main 的信息仍走现有 event |
| D11 | 每份 spec 的 closing pass 对 Memory 做 retain / propose / deprecate | Artifact 2.3 | 按 `mmw-spec-<n>` 列出本 night 写入的 Memory；`NIGHT SUMMARY` 只加结果计数 |
| D12 | 每份 spec 在 `summary` 后自动 retro | Artifact 3.1、第 9 节“复盘” | 在现有 night runbook 中接一个 retro 命令；不等待整个 map 结束 |
| D13 | retro 的运行事实只取自 ticket event 与 `git log` | Artifact 3.1；BMAD `bmad-retrospective/workflow.md` 与 `evidence-gathering.md` 的来源规则 | spec body 只用于意图对照；过去的 `spec.retroed` event 只用于历史重复与上次行动核验；不读 Thread、Working Memory 或 Memory 补证据 |
| D14 | 每条 retro finding 有来源，并分别写本例处置与预防下一次 | Artifact 3.1；BMAD `acceptance-verdict.md` 的 dual disposition | event/commit 无法支持的 finding 丢弃，不建立额外 evidence packet 或 occurrence schema |
| D15 | 同类问题跨 ticket 或跨 night 出现第二次才提议 | Artifact 3.1；OpenAI Codex Best Practices “same mistake twice”；Augment noisy memory | 以独立 event/commit source 计次；同一事件的多条记录只算一次 |
| D16 | 先核上一轮 retro 行动项 | Artifact 3.1；BMAD `retro-document.md` | 只有实际 commit、Rule、Memory 或现行文件证据才写“已落地”，否则写“没找到证据” |
| D17 | 做一次只描述、不扩 scope 的 intent reconciliation | Artifact 3.1；BMAD Intent Alignment Auditor | 对照 `Problem Statement`、`User Stories`、`Out of Scope` 与测试实际观察的 surface |
| D18 | 从 review 结果学习 false positive 与真实缺陷 | Artifact 3.1；Augment Code Review Memory；ADR 0012 | review finding 增加 category；`stale` 增加 `invalid|fixed-elsewhere` reason |
| D19 | retro 写成 `spec.retroed` event | Artifact 3.1“由脚本写成事件的 spec 评论”；`events.py` 的 script-written event 约定 | 只增加一个 spec event；不产生 hold、relay wake 或新的 night state |
| D20 | proposal 在正确 repository 创建并先进 `needs-triage` | Artifact 3.1、第 9 节；`docs/agents/issue-tracker.md` 的 `Three label sets`、`Morning queries` | MMW/toolbox 问题开在 multi-model-workflow，consumer-local 问题留在 consumer repository；不加 layer label |
| D21 | owner 批准后才能改变长期行为 | Artifact 2.3、第 9 节 | 复用现有 triage、`to-spec`、`to-tickets`、worker、review 和 landing 流程，不建 approval state machine |
| D22 | 长期载体按问题性质选择 | Artifact 2.3；OpenAI Harness Engineering；Augment AGENTS.md/Review Guidelines；Artifact 的 toolbox Space 布局 | 仅使用 `.mmw/target.json`/check、repository script、`AGENTS.md` Gotchas、reviewer Rule、MMW skill/reference/script 或 `mmw-toolbox` Memory |
| D23 | 新增一个 retro skill 和一个脚本入口 | Artifact 3.1；`mmw-v2/upstream/skills/in-progress/retro/SKILL.md` | 复用上游七类改进目的地；脚本读取现有 tree/event/git 并写 `spec.retroed`，不建数据库 |
| D24 | 新版本不得接管正在运行的 watch | 根 `AGENTS.md` 的 `Self-hosting boundary` | 只在隔离 `MMW_HOME`、假 tracker 和临时 repository 验证，下一次安装后才生效 |

### 参考项目实现文件

- [monomind project-context `context_capture.py`](https://github.com/monomind-ai-lab/project-context/blob/72a0a22640f4577eddd615c6bd3a4dad2a6473b9/skills/project-context/scripts/context_capture.py) 与 [`context_packet.py`](https://github.com/monomind-ai-lab/project-context/blob/72a0a22640f4577eddd615c6bd3a4dad2a6473b9/skills/project-context/scripts/context_packet.py)：只采用当场 capture、provenance 和按相关上下文取回；不采用 capsule inbox、approval state、`path@commit` doctor 或文件存储层。
- [BMAD-METHOD `bmad-retrospective/workflow.md`](https://github.com/bmad-code-org/BMAD-METHOD/blob/94b6727b00c8316557828c8a8ff2a48ff60d60cc/skills/bmad-retrospective/workflow.md)、[`evidence-gathering.md`](https://github.com/bmad-code-org/BMAD-METHOD/blob/94b6727b00c8316557828c8a8ff2a48ff60d60cc/skills/bmad-retrospective/references/evidence-gathering.md)、[`acceptance-verdict.md`](https://github.com/bmad-code-org/BMAD-METHOD/blob/94b6727b00c8316557828c8a8ff2a48ff60d60cc/skills/bmad-retrospective/references/acceptance-verdict.md) 和 [`retro-document.md`](https://github.com/bmad-code-org/BMAD-METHOD/blob/94b6727b00c8316557828c8a8ff2a48ff60d60cc/skills/bmad-retrospective/references/retro-document.md)：只采用 evidence inventory、来源规则、dual disposition 与 previous-action verification；不采用 sprint-status、独立文档树或团队仪式。
- [Augment Expert Memory](https://docs.augmentcode.com/cosmos/experts-memory)、[Code Review Memory](https://docs.augmentcode.com/cosmos/experts-code-review-memory) 与 [Review Guidelines](https://docs.augmentcode.com/codereview/review-guidelines)：采用强弱信号、review 结果学习、明确 scope 和稳定长期载体；不采用其 VFS 或专有 guideline 格式。
- [Devin Session Insights](https://docs.devin.ai/product-guides/session-insights)：只作为“工作完成后从真实运行记录提出改进”的产品依据；第一版不复制 transcript 分析系统。
- [OpenAI Harness Engineering](https://openai.com/index/harness-engineering/) 与 [Codex Best Practices](https://developers.openai.com/codex/learn/best-practices)：采用“重复两次再复盘”和“能机械执行的 rule 进入 code/check”；不复制其后台 agent 或 quality-score 系统。
- [Anthropic AI-native SDLC](https://claude.com/blog/how-anthropic-secures-its-ai-native-software-development-lifecycle)：采用“发现的 bug class 必须回到长期指导”的反馈原则；不增加新的 reviewer 或 shadow mode。

## 文档覆盖范围

本文件覆盖阶段二与阶段三组成的完整闭环，而不只覆盖当前任务的检索：

1. repository Space 与 `mmw-toolbox` 的布局；
2. worker、reviewer 的 Identity 与 reviewer 的干净上下文边界；
3. task root 的解析：有 map 时使用 map，没有 map 时使用 spec；
4. worker 何时写 Memory、写什么和如何证明；
5. dispatch 如何主动把当前 task root 的经验交给 worker；
6. 已经运行的 worker 如何主动取得后来出现的经验；
7. Thread capture、Working Memory 和跨夜 retrieval；
8. reviewer 的独立性与 reviewer Rule；
9. 每夜 Memory 收口、supersede/deprecate 与 retro 的衔接；
10. retro 的触发点、event/git 证据、跨 night 聚合与缺失证据语义；
11. 上一次行动项核验、交付意图对照、review 结果学习和 proposal 格式；
12. owner 决定、长期载体及其如何回流到下一次阶段二读取；
13. 不可用时的行为、实施范围、验收与效果指标。

## 已定决定与本次更新

### 保留的阶段二决定

- 经验不是 ticket state，不写成 tracker event；agent 直接写 Nowledge Mem。
- 能用 Nowledge Mem 的 Space、Identity、Memory、Thread、Working Memory、Rule、supersede 和 deprecate 完成的部分，不另造存储或生命周期。
- 每个客户 repository 有自己的 Space；不同客户 repository 互不可见。只有 `mmw-toolbox` 可以作为所有 repository 明确批准的共享来源。
- pipeline worker/reviewer 的 Memory 与自动采集 Thread 进入 repository Space，不进入个人 Default；owner 自己的普通会话保持现状。
- 普通经验无需 owner 逐条批准。把经验变成跨 repository 内容或常驻行为，只能形成提案，由 owner 批准后执行。
- 当前流水线没有独立 verifier；阶段二只设计 main agent、worker 和 reviewer。

### 阶段二与阶段三共同实施

- 阶段二的 Memory closing pass 按 Artifact 2.3 对每条经验做 retain、propose 或 deprecate；阶段三的 retro 按 Artifact 3.1 单独分析 ticket event 与 `git log`。两者共用 proposal 与 owner approval 路径，但不把 Memory 混进 retro 的运行证据。
- 阶段三的 retro 验证上一次行动项，形成 proposal，并把 owner 批准后的改动送回下一次阶段二。它不是一个以后再补的独立模块。
- 一份 spec night 是 retro 的触发与本次证据范围；repository 是重复问题的历史聚合范围；task root 是执行时共享 Memory 的范围。三者分别回答“何时复盘”“与哪些历史比较”“当前哪些 agent 共用”，不能互相替代。
- 同一 map 的多份 spec 可以并行结束。每份 spec 各自 retro；后完成的 sibling spec 能读取先完成 spec 的 `spec.retroed` event。整个 map 不增加第二次强制 retro，也不等待所有 sibling spec 才学习。
- retro 只提出长期改动，不直接修改 Rule、`AGENTS.md`、gate、script、skill 或 `mmw-toolbox`。proposal 进入已有 `needs-triage` 队列；owner 批准后，正常发布成 spec/ticket 并按 frozen runtime 边界落地。

### 被最新事实替代的旧结论

| Artifact 或早期调查中的说法 | 最新结论 | 原因 |
| --- | --- | --- |
| 用 ticket title 与 `## Owns` 检索“本票经验” | title 与 `## Owns` 不决定共享范围 | 它们分别是切片名称与写入边界；同一 task 可能包含多份并行 spec |
| Parent spec 是一次任务的共同上下文 | task root 是 `map if present, otherwise spec` | map 是多 spec task 的顶层；standalone spec 自己是顶层 |
| `--time today` 表示当夜 | 不按日期定义 task | 夜会跨午夜，日期也不能说明两条经验属于同一个 task |
| repository 使用 `strict` 同时读取 toolbox | repository 使用 `shared`，只链接 `mmw-toolbox` | Nowledge `strict` 只读当前 Space，不能读取 shared Space |
| Context Bundle 或 Working Memory 会提供当前任务经验 | 它们只提供 Identity、Space、Rule 与 Space 级简报 | 都没有 task root、label filter 或 task query |
| reviewer 的开场 prompt 不放检索结果 | 保持 Artifact 原设计：reviewer 不接收普通 Memory 检索结果，只接收 `mmw-reviewer` active Rules | Cognition、LangChain 与 MMW review 的共同前提是 reviewer 独立重建判断 |

## 已确认事实

### MMW 当前结构

- `tree.py`、Task Board 和 tracker 文档共同定义四层 native parent graph：`map → specs → tickets → children`。
- Task Board 的 `The Night` 是一个顶层 map 及其全部 specs/tickets；没有 open map parent 的 spec 自己成为一项 task。小写 `night` 仍是 `dispatch.sh` 对一份 spec 的一次运行。
- 真实 tracker 已验证 `#384 map → #374 spec → #375 ticket`；同一个 `tree.py 384 --root map` 调用读出了 #374 下的七张 tickets。
- `dispatch.sh read_ticket()` 已经从 ticket native parent 取得 spec。`## Parent` 是给 agent 读的 spec section 指针，不是机器归属关系。
- `to-spec` 已允许一个 map 拆成多份 specs，但发布步骤尚未明确保证这些 specs 是 map 的 native children。

### Nowledge Mem 当前能力

| 能力 | 已确认行为 | 阶段二用途 |
| --- | --- | --- |
| `memories add` | 可指定 Space、Identity、unit type、labels；写入后即可检索 | worker 即时保存显式经验 |
| `memories list` | 可按一个 label 精确列出；本机重复 `--label` 实测为 OR | 列出当前 task root 或当前 spec 夜间产生的经验 |
| `memories search` | semantic + text search，约 0.5 秒；可按 label、unit type、时间和 metadata 过滤 | agent 按真实问题主动找经验 |
| `ask` | 本机一次约 130 秒 | 不进入派发路径 |
| Space | `strict` 只读当前 Space；`shared` 读取当前 Space 和显式 shared Spaces | repository 隔离并只共享 `mmw-toolbox` |
| Identity | provenance、默认 Space 与 agent Rule 的选择，不是授权，也不是 Memory 可见性过滤器 | 区分 worker/reviewer 来源与常驻 Rule |
| Thread capture | connector 在 session 结束/compact 时保存完整会话；后台可能蒸馏成 Memory | 跨夜证据与宽背景，不承担同夜保证 |
| Working Memory | 每个 Space 一份简报，早晨生成，新 Memory 后异步刷新 | session start 的宽背景 |
| Context Bundle | Identity、active Space、active Rules、Working Memory | startup 背景；不含 task retrieval |
| supersede/deprecate | supersede 保留旧条目并建立 replacement；deprecate 使其退出普通 recall | 纠正或结束经验 |
| active Rules | 编译进 Context Bundle；普通 Memory 不会自动变 Rule | owner 批准后的 reviewer/Space 常驻行为 |

### 当前安装状态

- 本机 CLI/server 是 `0.10.78`；本文只使用这个本机版本已实测的接口。
- Spaces 功能已经启用，目前只有 Default；repository Spaces、`mmw-toolbox` 和 MMW Identities 尚未建立。
- 当前只有 `default` Identity；active Rules 为 0，已有 Rule 全部是 draft。
- MMW 目前只由 `install.sh` 配置 Cursor 的 Nowledge MCP；dispatch、implement 和 runner adapter 里还没有阶段二路由。

### MMW 当前收口与 review 证据

- `mmw-v2/skills/dispatch/references/night.md` 的 `## 4. The closing pass` 要求 main agent 读取本 spec 的每张 ticket，把每个 `finding` 以 `fixed`、`stale` 或 `became-ticket` 路由；`dispatch.sh summary <spec>` 在仍有未路由 finding 时拒绝关闭 night。
- `dispatch.sh summary <spec>` 当前只生成 `NIGHT SUMMARY`、写入 `spec.closed` 并停止该 spec 的 relay。它没有 retro，也不会比较更早的 spec 或 night。
- 每个 ticket 的 comment 中已经有完整的 script-written event fold；`ticket.bounced`、`ticket.returned`、`worker.lost`、`reviewer.reported`、`child.opened`、`child.closed` 和 `ticket.checked` 足以作为第一版 process evidence，不需要先保存全部 agent transcript。
- reviewer comment 已固定分成 `Standards`、`Spec`、`Tests` 三个 axis，并将 finding 分成 `In-ticket` 与 `Out-of-ticket`。但每条汇总行只有 axis、path、line 与自由文本 claim，缺少可稳定聚合的 finding category。
- 当前 `route ... stale` 只说明 finding 在 `HEAD` 已不成立，没有区分“原 finding 本来就是误报”和“finding 曾经成立但被其他 ticket 修复”。阶段三不能把两者混成 reviewer false positive。
- `git log` 能给 closing pass 自行修复、ticket merge、proposal 后续落地和当前 base revision 提供独立证据；它不能单独说明 agent 为什么失败，所以原因仍以 event、finding body 和 review comment 为准。

### 可借鉴实现与适配结论

- BMAD-METHOD 当前 `bmad-retrospective` 的实现会读取完整 spec、全部 story、整段 diff、逐 story commit、上一次 retrospective 和可用的 session log；每个 finding 必须带来源，缺失证据必须明确缩小结论范围。MMW 采用它的 evidence inventory、previous-action verification 和“无来源不成 finding”，不采用它的独立 retrospective 文档树、sprint status 和团队讨论流程。
- Devin Session Insights 在 session 完成后按需生成可执行建议，证明“结束后分析真实轨迹”是成熟产品形态；MMW 已有更结构化的 tracker event，因此第一版不依赖完整 Thread。
- Augment Code Review 把 repository `AGENTS.md`/`CLAUDE.md` 与按 path 生效、带稳定 id 和 severity 的 review guideline 分开。MMW 采用“长期规则必须有明确载体和适用范围”，不引入 Augment 的专有配置格式。
- OpenAI 的 harness engineering 经验明确反对把全部知识堆进一个巨大 `AGENTS.md`，并主张把可执行 invariant 交给机器检查。MMW 因此只把不可从代码推得、对全 repository 通用的约束放进 `AGENTS.md`；能机械判断的 proposal 优先进入 target、judge、lint 或 script。
- mattpocock 上游 `retro/SKILL.md` 仍是针对单个 coding session 的 design notes，分类包括 Navigation、Automated checks、Coding standards、Global `AGENTS.md`、Tool economy、No-ops 和 Information access。MMW 复用这些改进目的地作为辅助分类，但分析对象改成一份 spec night 的完整 tracker evidence，并与 repository 历史比较。
- 调查过的现成方案都没有直接覆盖 MMW 的 GitHub native parent、event fold、`route` 和 frozen runtime。因此采用“扩展现有 MMW + Nowledge Mem”，不直接引入外部库，也不 fork 另一套工作流。

## Working Memory 是什么

来源：D04。

Nowledge Mem Working Memory 是每个 Space 一份、由 AI 维护的每日简报，内容是当前 focus areas、open questions 和 recent activity。

- 每天早晨生成并归档上一份；新 Memory 写入后也会异步刷新，但延迟比其他后台任务更长。
- 支持的 connector 在 session start 时通过 Context Bundle 注入它；正在运行的 session 不会收到后来刷新出的内容。
- Context Bundle 还包含 Identity、active Space 和 active Rules，但不包含“按当前 task root 搜出的 Memory”。
- shared retrieval 只扩大 Memory search 的读取范围，不合并 Working Memory。repository Space 共享 `mmw-toolbox` 后，Context Bundle 仍只带 repository Space 自己的一份 Working Memory。
- 一个 repository Space 同时运行多个 map 时，它只有一份 Working Memory，不能按 map 过滤。

因此 Working Memory 是 repository 的宽背景，不是 map 级共享经验，不是实时 scratchpad，也不是确定性的任务输入。阶段二不写它、不 patch 它，也不为每个 map 新建 Space。

这一区分由本机 `nmem 0.10.78` 的 CLI、Context Bundle、Working Memory API 和 Codex connector 源码验证。Codex connector 的 `SessionStart` 读取 Context Bundle；`UserPromptSubmit` 只注入“需要时主动搜索”的提示，不重新注入 Working Memory。

## 1. 共享地址

来源：D02、D03、D05。

一条经验的完整地址由两部分组成：

| 部分 | 值 | 作用 |
| --- | --- | --- |
| storage boundary | repository Space `owner__name` | 隔离不同客户仓库；该 Space 使用 shared retrieval，只共享读取 `mmw-toolbox` |
| task scope | `mmw-map-<map number>` | 把同一 map 下的全部 spec 放进同一个当前任务经验域 |

没有 map parent 的 standalone spec 使用 `mmw-spec-<spec number>`。

### Space 布局

| Space | 内容 | Retrieval mode | 可以读取 |
| --- | --- | --- | --- |
| repository Space `owner__name` | 该 repository 的 Memory、worker/reviewer Thread 和 Working Memory | `shared` | 自身与 `mmw-toolbox` |
| `mmw-toolbox` | owner 已批准、可以跨 repository 使用的 MMW 工具经验 | `strict` | 仅自身 |
| Default | owner 的普通跨工具会话与个人背景 | 保持现状 | 不进入 pipeline retrieval |

repository Space 的 `sharedSpaceIds` 只包含 `mmw-toolbox`。不同客户 repository 不互相链接；阶段二也不迁移 Default 的历史内容。`mmw-toolbox` 不是所有 Memory 的公共池，只接收 owner 明确批准晋升的通用经验。

不为每个 map 或 standalone spec 建 Space。那会把同一 repository 的跨任务历史切碎，要求在任务结束时搬运 Memory，并产生大量短命 Working Memory。task root 是 repository Space 内的 scope label，不是新的存储边界。

### Identity 布局

| Identity | 使用者 | 默认 Space | 作用 |
| --- | --- | --- | --- |
| `mmw-worker` | ticket worker | 不固定；dispatch 显式传入当前 repository Space | 记录 provenance，接收 worker active Rules |
| `mmw-reviewer` | ticket reviewer | 不固定；dispatch 显式传入当前 repository Space | 记录 provenance，接收 owner 批准的 reviewer active Rules |
| `default` | owner 的普通会话与非 pipeline 工作 | Default | 保持个人上下文，不由 dispatch 改写 |

Identity 不承担授权：Memory 是否可见由 active Space、retrieval mode 和 shared Spaces 决定。Identity 只回答“谁产生了这条记录”和“哪个角色的 active Rules 应进入 Context Bundle”。固定 Identity 不能把 default Space 设成“当前 repository”；本机 `nmem agents enroll` 的 `--default-space` 是一个固定 Space id，所以 pipeline 必须每次显式传 `NMEM_SPACE`。

main agent 不新建 `mmw-main` Identity，也不在 `open` 时接收 task Memory 注入。它在 closing pass 由 `dispatch.sh` 按本 spec label 读取 Memory；owner 会话的完整 Thread 不会被自动搬进客户 repository Space。

### 建立和解析

- `install.sh` 幂等建立全局的 `mmw-toolbox`、`mmw-worker` 与 `mmw-reviewer`；`install.sh --check` 只报告缺失或形状不一致。
- `dispatch.sh open <spec>` 幂等建立当前 repository Space；已有正确 Space 时不重建，但不把 Memory 注入 main prompt。
- repository Space id 是 tracker repository 的 `lowercase(owner) + "__" + lowercase(name)`；显示名保留 `owner/name`，避免两个同名 repository 冲突。
- dispatch 每次从当前 tracker repository 和 native parent graph 重新解析 Space 与 task root，不把它们缓存进 ticket body。

首次建立使用当前 `nmem 0.10.78` 已存在的接口：

```sh
nmem --json spaces create "MMW Toolbox" \
  --id mmw-toolbox --retrieval-mode strict
nmem --json agents enroll mmw-worker \
  --name "MMW Worker" --role worker
nmem --json agents enroll mmw-reviewer \
  --name "MMW Reviewer" --role reviewer

nmem --json spaces create "$REPOSITORY_SLUG" \
  --id "$NMEM_SPACE" \
  --retrieval-mode shared \
  --share-with mmw-toolbox
```

`agents enroll` 已有 create-only/no-op 语义；`spaces create` 没有同样承诺，所以 `dispatch.sh` 先 `spaces show <id>`，缺失才 create。MMW 命名空间下的 repository Space 已存在但 retrieval shape 不一致时，用 `spaces update <id> --retrieval-mode shared --share-with mmw-toolbox` 恢复固定形状；不会触碰 Default 或其他 Space。

正常路由只读 tracker graph：

```text
ticket --native parent--> spec --native parent--> map
```

`read_ticket()` 已经从 ticket 的 native parent 得到 spec。`dispatch.sh` 再读取 spec 的 native parent；parent 带 `mmw:map` 时使用 map scope，没有 parent 时使用 standalone spec scope。

真实数据已经验证这条链：GitHub `#384 → #374 → #375` 分别是 map、spec、ticket；`tree.py 384 --root map` 一次读出 `#384 → #374 → 七张 tickets`。Task Board 也用同一条 native parent graph 把“一个 map 及其全部 spec/ticket”定义为 The Night。

不使用以下内容决定共享范围：

- ticket title：只是一个工作切片的名称；
- `## Owns`：只是可写路径和并行冲突边界；
- Parent spec 正文：只描述一个 seam，不能代表同一 map 下其他并行 spec；
- semantic similarity：只能判断内容相似，不能证明两个 agent 属于同一项任务。

## 2. `dispatch.sh` 主动提供当前 task root 经验

来源：D03、D05、D06、D09。

### `dispatch.sh start <ticket> worker`

`start` 在调用 runner adapter 前完成一次当前 task 读取：

1. 从 ticket 的 native parent 得到 spec，再从 spec 的 native parent 得到 `map:<n>` 或 standalone `spec:<n>`；
2. 得到当前 repository Space；
3. 用唯一 task scope label 列出当前 task 已写入的显式 Memory；
4. 把结果放进 worker 的首次 prompt。

```sh
nmem --json memories list \
  --space "$NMEM_SPACE" \
  --label "$MMW_EXPERIENCE_SCOPE" \
  --limit 1000
```

这里只使用一个 scope label。本机实测 `memories list` 的重复 `--label` 是 OR，不是 AND；因此所有带 task scope label 的 Memory 都必须是共享经验，`mmw-experience` 只用于 worker 按具体问题搜索历史。

首次 prompt 的固定部分只包含：

```text
MMW task root: map #384
MMW task scope: mmw-map-384
Current task shared experience:
- <memory id> — <title>
  <content>
  Source: <source>

When an unexplained failure is not covered above, search with the exact error,
command and component. Verify every Memory against current repository evidence.
```

这一步不再用 ticket title、`## Owns`、`--time today` 或整份 spec 作为检索输入，也不增加第二次 historical seed。新 task 没有 scoped Memory 时结果就是 0；真正遇到问题后再按第 3 节搜索历史，避免把仅仅“可能相关”的内容预先塞给 worker。

### `dispatch.sh start <ticket> reviewer`

reviewer 不执行上述 Memory 读取，首次 prompt 不放其结果。runner 仍设置 reviewer Identity，使 Nowledge Mem 的 Context Bundle 能提供 owner 已批准的 `mmw-reviewer` active Rules，并把 connector Thread 归到当前 repository Space。

两种角色都由 runner adapter 设置：

- `NMEM_SPACE=<repository Space>`
- `NMEM_AGENT_ID=mmw-worker|mmw-reviewer`

worker 另收到 `MMW_EXPERIENCE_SCOPE`、`MMW_SPEC` 与 `MMW_TICKET`，供主动搜索和写入使用。Paseo、Orca 与 Herdr 只在各自现有 adapter 里传同一组值，不形成 host-specific 设计。

## 3. worker 主动获取后来出现的经验

来源：D07。

worker 只在一个明确时刻主动检索：命令或工具出现 ticket、repository 文档和当前 task 经验都没有解释的行为，在尝试 workaround 之前。

先查当前 task：

```sh
nmem --json memories search \
  "<exact error + command + component>" \
  --space "$NMEM_SPACE" \
  --label "$MMW_EXPERIENCE_SCOPE" \
  --limit 10
```

没有答案时，再查 repository 与 toolbox 历史：

```sh
nmem --json memories search \
  "<exact error + command + component>" \
  --space "$NMEM_SPACE" \
  --label mmw-experience \
  --limit 10
```

repository Space 的 shared retrieval 让第二次搜索同时覆盖当前 repository 与 `mmw-toolbox`，但不读取其他客户 repository 或个人 Default。行为写进 `implement/SKILL.md`；没有相关问题时不轮询。Memory 是资料，不是 authority，worker 必须用当前命令输出或 repository authority 核对后才采用。

## 4. worker 写入可复用经验

来源：D08。

worker 在以下三项都成立时立即写，不等 closeout：

1. 同一 task 的另一张 ticket 或后续 agent 可能再次遇到；
2. 已由实际命令结果或当前权威文件证实；
3. 只读 ticket 和代码不能立即得知。

写入命令是：

```sh
nmem --json memories add --stdin \
  --space "$NMEM_SPACE" \
  --agent-id "$NMEM_AGENT_ID" \
  --unit-type learning \
  --label mmw-experience \
  --label "$MMW_EXPERIENCE_SCOPE" \
  --label "mmw-spec-$MMW_SPEC" \
  --label "mmw-ticket-$MMW_TICKET" \
  --title "<searchable title>"
```

stdin 只写 Artifact 要求的事实与证据：

```text
Finding: <已证实的非显然事实>
Evidence: <命令与输出首行，或 path:line>
```

默认 unit type 是 `learning`；固定操作步骤使用 `procedure`。适合写的是不稳定测试、工具的非显然行为、环境修法和测试前提。普通实现细节、ticket 状态、未经验证的推测、用户决定、凭据和客户数据不写。Space、Identity、task/spec/ticket labels 已提供 repository、角色和工作来源，不在正文重复造 provenance schema。

同一事实发生变化时不覆写历史：新 Memory 已证实旧 Memory 错误时使用 supersede；旧经验只是不再适用时使用 deprecate。普通 repository Memory 的写入与纠正不等待 owner 批准，因为等待会使并行 agent 继续重复遇到同一问题。

## 5. 并行 spec 的实际传播

来源：D05、D06、D07、D08。

以 map `#384` 下并行的 spec A、spec B 为例：

```text
spec A worker 启动
  → dispatch 注入 label=mmw-map-384 的当前 task Memory
  → worker 证实一个非显然工具行为
  → 立即写 Memory(labels: mmw-experience, mmw-map-384)

spec B worker 稍后启动
  → native parent 同样解析为 map #384
  → dispatch 的一次 task 读取直接取得新 Memory

spec B worker 已经在运行
  → 遇到同一错误
  → 用错误、命令、组件搜索 mmw-map-384
  → 取回 spec A 的 Memory
```

另一个 map 不进入 task-scoped 列表；以后只有在 worker 遇到具体相同问题并主动查 repository 历史时，才可能按 relevance 取回这条经验。standalone spec 使用相同路径，scope 改为 `mmw-spec-<n>`。reviewer 不在这条 Memory 传播路径中。

## 6. tracker event 与 Memory 的边界

来源：D10。

Memory 只承载“怎么做、踩过什么坑、什么非显然前提已被证实”。它不承载 ticket state、依赖、`## Owns`、acceptance 结果、spec 修订或必须马上执行的指令。

当 worker A 发现的信息必须立即改变 worker B 的行为时：

- contract 不适配：现有 `contract` child；
- pipeline 本身故障：现有 `fault` child；
- 需要 owner 选择：现有 `decision` child。

relay 继续只由 tracker event 唤醒 agent。Memory 不产生 wake，也不参与 gate。

## 7. reviewer 的读取与独立性

来源：D09。

reviewer 的开场 prompt 不放 worker 或 repository Memory 的检索结果，`code-review` 也不要求 reviewer 主动搜索普通 Memory。需要常驻的 review 经验只以 owner 已批准并编译进 Context Bundle 的 `mmw-reviewer` active Rules 提供。

reviewer 仍独立读取 ticket、spec、repository authority 与 diff，并重新运行它负责的检查。worker Thread、推理、自评和“实现正确”的结论都不进入 reviewer。需要让以后每次 review 都执行的稳定方法，先由 retro 提议，owner 批准后再成为 active Rule。

这保留了 Artifact 2.2 的角色边界，也与 Cognition、LangChain 的 clean verifier context 一致。

## 8. Thread、Working Memory 与跨夜路径

来源：D03、D04、D07。

阶段二保留 Nowledge Mem 的原生跨夜链路：

```text
worker/reviewer session
  → connector 以 NMEM_SPACE 保存 Thread 到 repository Space
  → Nowledge 后台整理与异步蒸馏
  → repository Working Memory 在后续 session start 提供宽背景
  → 后续 agent 遇到具体问题时检索显式 Memory
```

这条链路负责“下一夜仍能找到”，不负责“同一夜立即广播”。同夜确定性由 worker 直接写显式 Memory、dispatch 在每次 start 精确列举、运行中 agent 按具体问题主动搜索共同保证。

完整 Thread 是事后证据，不直接塞给并行 agent。Working Memory 是整个 repository Space 的简报，可能同时包含多个 map 和 standalone spec；它只提供宽背景，不能作为 task root 检索结果。后台蒸馏即使较慢或没有发生，也不影响显式 Memory 的同夜传播。

后续 task 查历史经验时，先用具体问题在 repository Space 搜 `mmw-experience`。shared retrieval 会同时查 repository 与 `mmw-toolbox`；仍然不会查其他客户 repository 或 Default。阶段二不自建 Thread 摘要器、Working Memory patch、map Working Memory 或实时同步层。

## 9. 每夜 Memory 收口与 retro 的衔接

来源：D11、D12、D19。

小写 `night` 是 `dispatch.sh` 对一份 spec 的一次运行。closing pass 按 `mmw-spec-<n>` 列出本 spec night 写入的 Memory，逐条执行 Artifact 2.3 的三选一：

1. **retain**：仍正确、仍适用，原 Memory 保持不变；
2. **propose**：同类经验已独立出现两次以上，或一次就实际阻塞 ticket，形成长期载体 proposal；
3. **deprecate**：已有证据说明不再适用，用 Nowledge Mem deprecate 并写原因；若新事实替代旧事实，使用 supersede。

这一步只处理经验本身，不把 Memory 当作阶段三的运行证据。`dispatch.sh summary <spec>` 保持现有 ticket-state 闭合，并在 `NIGHT SUMMARY` 增加本 spec 的 `written / retained / proposed / deprecated` 计数。

`summary` 成功写入 `spec.closed` 后，同一 main agent 立即运行 retro。retro 以一个 script-written `spec.retroed` event 写在该 spec comment 中。它不改变 `spec.closed`，不持有任何 agent，也不触发 relay。

## 10. retro 的范围和证据输入

来源：D12、D13。

### 三个范围

| 范围 | 固定定义 | 作用 |
| --- | --- | --- |
| 本次复盘 | 当前刚完成的 spec night | 决定本次新增哪些 finding |
| 阶段二共享 | task root：`map if present, otherwise spec` | 决定哪些 worker 立即共用 Memory |
| 历史比较 | 当前 repository 的较早 `spec.retroed` events | 发现跨 ticket、跨 spec、跨 task 和跨 night 的重复问题 |

每份 spec 完成后各自运行一次 retro。map 内先完成的 spec 立即留下 `spec.retroed`；后完成的 sibling spec 可以把它作为 repository 历史。没有 map-level retro 或等待全部 sibling 的 gate。

### 输入及其用途

| 输入 | 来源 | 能证明什么 |
| --- | --- | --- |
| 本次完整 ticket 集合 | `tree.py <spec> --root spec` | 哪些 ticket 与 child 必须读取 |
| process 与最终结果 | 每张 ticket 的完整 event fold及其 script-written comment | bounce、return、lost、HANDOFF、finding、route、check 与最终结果 |
| 实际落地 | 本批 merge、closing-pass fix 与 base branch `git log` | 哪些改变确实进入 repository |
| 历史重复与上一轮行动 | 较早的 `spec.retroed` event 及其链接的 issue，再用 commit、Rule、Memory 或现行文件复核 | 同类问题是否已出现、已提议的预防是否真正落地 |
| 交付意图 | 当前 spec 的 `Problem Statement`、`User Stories`、`Out of Scope` | 仅用于 expected surface，不证明实现发生了什么 |

retro 的运行事实只接受 event 或 commit source。review finding 的 path、claim 与 category 来自承载 `reviewer.reported` event 的 comment；spec 只定义批准的意图。Memory、Thread、Working Memory、agent 自评和无输出推断都不能补成运行证据。

第一版不扫描阶段三启用以前的全部 closed specs，也不建立 bootstrap baseline。跨 night 计数从 `spec.retroed` 开始，避免为了追溯旧夜再造迁移、索引或缓存。读取失败的来源明确写“未检查”，不能写成“没有发生”。

## 11. retro 的分析合同

来源：D14、D15、D16、D17、D18。

### 从证据到 finding

retro 不建立独立 `occurrence` 数据层。每条 finding 直接写在 `spec.retroed` 的人可读正文中，包含：

- 支持它的 ticket event 或 commit 链接；
- 本例已经怎样处理；
- 怎样防止下一次，以及应落入哪个现有载体。

同一事件同时出现在 review comment、child 与 route 中仍只算一次。相同 path、相似标题或同一个宽类别都不能单独证明是同一原因。

### 哪些内容形成 proposal

阶段三只把跨 ticket 或跨 night 独立出现两次以上的同类问题列为 proposal candidate，范围限于 Artifact 3.1 明列的四类：

- 相同 `ticket.bounced` 原因；
- 相同 `HANDOFF REQUIRED` 原因；
- 相同 review finding category；
- 相同环境问题被重复修复。

候选必须引用两次独立的 event/commit source。一次问题即使严重，也不由 retro 推成阶段三 proposal；它按现有 fault、contract、finding 或 ticket 路径处理。Artifact 2.3 的“单次实际阻塞也可 propose”只适用于第 9 节的 Memory promotion。

### 上一次行动项

retro 先核最近一份 `spec.retroed` 中的 proposal。能指出实际 commit、active Rule、Memory id 或现行文件位置才写“已落地”；找不到这种证据就写“没找到证据”。issue 关闭本身不等于预防措施已生效。

### intent reconciliation

只做描述性对照：从 `Problem Statement` 与 `User Stories` 取得 expected surface，从 ticket checks 与实际运行证据取得 observed surface，再与 `Out of Scope` 对照。它报告一致、偏离或未验证，不自行增加功能，也不自动改 spec。

### review learning

review finding 增加一个稳定 category。`route … stale` 同时记录：

- `invalid`：finding 从一开始就不成立；
- `fixed-elsewhere`：finding 曾成立，但当前 `HEAD` 已由其他 ticket 或 closing-pass fix 修复。

同一 category 的 `invalid` 两次，提议一条 reviewer guideline；同类真实缺陷两次，提议 anti-pattern 或自动检查。`fixed-elsewhere` 不计作 false positive。category 只用于聚合，具体 proposal 仍需引用 finding 的 path、claim 与处置证据。

## 12. `spec.retroed`、proposal 与 owner 决定

来源：D19、D20、D21、D22。

### `spec.retroed` event

retro script 在 spec 上写一条现有 event 格式的 comment：

```text
NIGHT RETRO
Evidence checked: <ticket events and commit range>
Previous actions: <已落地 | 没找到证据>
Repeated problems: <two or more sourced findings, or none>
Intent reconciliation: <expected / observed / gap>
Review learning: <candidate or none>
Proposals: <issue links or none>

<!-- mmw {"v":1,"event":"spec.retroed","stage":"night","actor":"main",...} -->
```

每条 finding 的正文带 source；无 event/commit source 的内容不写。`spec.retroed` 只是可折叠、可读取的历史记录，不增加 status、hold、wake 或 gate。

### proposal issue

proposal 创建在应承担改变的 repository：MMW 或 toolbox 行为开在 multi-model-workflow，consumer-local 问题留在该 consumer repository。新 issue 加现有 `needs-triage` queue label，不加 `mmw:map/spec/ticket/child` layer label；spec event 链接 proposal，proposal 回链来源 spec 和两次独立证据。

proposal 只写 Artifact 要求的内容：本例如何处理、怎样防下一次、目标载体、来源。它不直接修改长期载体，也不阻止 night 结束。owner 批准后，需实现的改变走现有 `to-spec`、`to-tickets`、worker、review 和 landing 流程；owner 拒绝则按现有 triage 结果处理，不建立新的审批状态。

### owner 批准后的长期载体

| 问题性质 | 目的地 | 后续怎样生效 |
| --- | --- | --- |
| 可机械判断 | `.mmw/target.json`、judge、lint、ticket `CHECK:` 或 repository script | 运行或验收时直接检查 |
| repository 通用且代码无法推出 | repository `AGENTS.md` 的 Gotchas | 后续 agent 读 repository authority |
| reviewer 的稳定方法 | `mmw-reviewer` active Rule | 后续 reviewer 的 Context Bundle 注入 |
| MMW pipeline 行为 | 对应 MMW skill、reference 或 script | 新版本安装后的 night 使用 |
| 跨 repository 有用但不应强制 | `mmw-toolbox` Memory copy | repository shared retrieval 按需取得 |
| 不够稳定或不够通用 | 原 repository Memory | 保持可搜索，不升格 |

能机械执行的内容优先进入 check 或 script；只有无法从代码推得且几乎每项任务都适用的内容才进入 `AGENTS.md`。这些选择分别来自 OpenAI Harness Engineering 与 Augment 的 AGENTS.md/Review Guidelines，不扩展为新的 `CONTEXT.md`、ADR、coding-standard 层或治理系统。

### 回流到下一次阶段二

```text
worker 写/读 task Memory
  → closing pass：retain / propose / deprecate
  → summary 写 spec.closed
  → retro 写 spec.retroed，并对重复问题开 needs-triage proposal
  → owner 批准后由现有 ticket 流程落入长期载体
  → 后续 worker、reviewer 或 check 使用
  → 后续 retro 以证据判断是否仍重复
```

## 13. 必须补齐的现有结构契约

来源：D05、D18、D19、D20。

阶段二与阶段三只补五个现有接口：

1. 从 map 发布 spec 时，把 spec 创建为该 map 的 native child，并在 read-back 验证 `parent.number`；standalone spec 保持无 map parent。
2. review finding 汇总行增加稳定 category，同时保留现有 axis、path、line 和 claim。
3. `child.closed resolution=stale` 增加 `reason=invalid|fixed-elsewhere`，resolution 本身不变。
4. `events.py` 增加 `spec.retroed`；它不进入 hold、relay 或 ticket verdict。
5. retro proposal 使用现有 `needs-triage` queue 和现有 issue tracker，不增加 layer、queue 或私有审批表。

`## Sources`、map 的 `## Specs`、ticket title 和 `## Owns` 都是人可读记录或执行切片，不能替代 native parent 与 structured outcome。

## 14. 不可用时的行为

来源：D03、D13；Artifact 2.1 的 fail-open；MMW ADR 0008。

- Nowledge Mem 读取或写入失败时，worker 照常执行 ticket，输出具体失败原因；Memory 从不改变 acceptance、review 或 landing verdict。
- native parent 读不到时，不猜成 standalone spec，也不扩大到 repository scope；本次 worker 不注入或写 task-scoped Memory，并报告 routing 未完成。
- retro 的某项 event/git source 读不到时，`spec.retroed` 明确写“未检查”；不能把 unreadable 当 0，也不能用该来源形成 proposal。

这些行为只让“查询失败”和“查到 0 条”可区分，不增加 retry state、补偿事务或新的 gate。

## 15. 实施范围与顺序

来源：D23、D24，以及 D02–D22 各项对应的现有接口。

阶段二与阶段三作为一个 spec，按同一依赖链实施。

### A. Space、Identity 与现有 dispatch

1. `mmw-v2/install.sh` 幂等建立 `mmw-toolbox`、`mmw-worker` 与 `mmw-reviewer`，`--check` 只读核对。
2. 在现有 `dispatch.sh` 内增加 Nowledge helper：建立或读取 repository Space、解析 `nmem --json`、按 task/spec label 列举，并区分 unavailable 与 0 results。worker 仍直接使用 Nowledge CLI 搜索与写 Memory，不增加中间服务或新 adapter module。

### B. 阶段二读写

3. `dispatch.sh` 与现有 runner adapters 解析 native parent，设置 Space/Identity；只有 worker start 读取一次 task Memory。`summary` 加入本 spec Memory 计数。
4. `implement/SKILL.md` 增加 Artifact 2.1 的写入条件与 2.2 的主动搜索时点；`code-review` 不增加 Memory retrieval，只依赖 active Rules。
5. `to-spec/SKILL.md` 在 map 来源时创建 native child 并 read back；standalone spec 不虚构 parent。

### C. 阶段三 retro

6. `code-review` 的汇总合同增加 category；`route … stale` 增加 `invalid|fixed-elsewhere` reason。
7. `events.py` 增加一个无 hold、无 wake 的 `spec.retroed` event；night runbook 在成功 `summary` 后执行 retro。
8. 新增 `mmw-v2/skills/retro/SKILL.md` 与一个脚本入口。脚本读取当前 spec tree、ticket event、相关 `git log` 和较早 `spec.retroed`，写本次 event，并在满足重复阈值时创建 `needs-triage` proposal。它不读 Thread/Working Memory，不写长期载体。

### D. owner approval 与证明

9. 批准后的改变继续走现有 triage、`to-spec`、`to-tickets`、worker、review、closeout 和 landing；Memory copy 或 Rule activation 也在 proposal 留下实际 id。
10. 按 repository 规则更新 Tickets/Night/Memory contexts、dispatch reference、upstream merge-note 和必要的 downstream-note。
11. 测试覆盖 install、dispatch、runner、map/standalone scope、review category、stale reason、retro event、proposal repository/label 和跨 night 重复。

实现顺序是 A → B → C → D。所有验证使用隔离 `MMW_HOME`、假 tracker、临时 Git repository 和临时 Nowledge objects；当前 frozen runtime 不读取新版本。

## 16. 验收

来源：D02–D24；每条只证明上面已有设计，不增加新行为。

1. 一个 map 下两份 specs 的 workers 解析成同一 task scope；standalone spec 使用自己的 scope。
2. repository A 只能搜索自身与 `mmw-toolbox`，看不到 repository B 或 Default。
3. worker Memory 与 worker/reviewer connector Thread 进入当前 repository Space，provenance 使用各自固定 Identity。
4. spec A worker 写入 task Memory 后，稍后启动的 spec B worker 在一次 task 读取中得到它；reviewer prompt 不包含它。
5. 已运行 worker 用实际错误、命令和组件取回 current-task 或 repository/toolbox 历史 Memory；没有具体问题时不搜索。
6. reviewer 只得到 active Rules，并独立运行 acceptance/review checks。
7. 一份 spec 的 closing pass 只处理带该 spec label 的 Memory，完成 retain/propose/deprecate 并在 summary 计数。
8. `summary` 后写出一个 `spec.retroed` event；每条运行 finding 都能跳到 ticket event 或 commit。
9. 两个 specs/nights 的同因 event 在第二次形成一个 proposal candidate；同一事件的多条记录不重复计数。
10. 上一轮 proposal 只有在找到实际落地证据时显示“已落地”，否则显示“没找到证据”。
11. intent reconciliation 同时显示 spec expected surface、实际 observed surface 与 gap/未验证。
12. 两个 `stale reason=invalid` 的同类 finding 形成 reviewer guideline candidate；`fixed-elsewhere` 不算 false positive。
13. proposal 在正确 repository 创建，初始 label 为 `needs-triage`，未获 owner 批准不改变任何长期载体。
14. 隔离测试证明新闭环，而正在运行的 frozen MMW watch 从未读取新版本。

## 17. 效果指标

来源：Artifact 2.3 的 `NIGHT SUMMARY` 计数、Artifact 3.1 的 proposal 落地率、OpenAI/Augment 的重复错误反馈原则。

| 指标 | 记录位置 | 期望方向 |
| --- | --- | --- |
| worker start 实际注入的 task Memory 数 | dispatch 输出与 `NIGHT SUMMARY` | 可核对，不设数量目标 |
| 同一已知问题在一个 task 被第二名 worker 重复修复的次数 | ticket event 与 retro | 下降 |
| retro proposal 的实际落地率 | 下一次 `Previous actions` | 上升；无证据不计落地 |
| 预防措施落地后同因问题再次出现的次数 | 后续 `spec.retroed` | 下降至 0 |

不使用 ticket pass rate 证明闭环有效，因为它不能归因于 Memory 或 retro。

## 18. 明确不采纳

以下内容要么被 owner 明确否定，要么不在 Artifact 与参考项目所支持的 MMW 适配范围内：

- 阶段二、阶段三分别等待两次实施；
- 每个 map/spec 建 Space，或把 Working Memory 改成 task bus；
- 用 ticket title、`## Owns`、整份 spec 或 `--time today` 决定 task scope；
- `dispatch.sh open` 注入、worker start 的第二次 historical seed、reviewer Memory 注入；
- 用 Memory、Thread 或 Working Memory 补 retro 的运行证据；
- bootstrap 全量扫描、`occurrence` 数据层、evidence packet、proposal 去重状态机；
- 新建 retro 数据库、relay、轮询、queue 或 approval state machine；
- 自动把 Memory 或 proposal 晋升为 Rule、`AGENTS.md`、check、script、skill 或 `mmw-toolbox`；
- 把一次阶段三问题当作重复问题提案；
- 用 known false positive guideline 静默禁止 reviewer 报告；
- 让新版本 MMW 接管正在运行的 frozen watch。

## 是否需要讨论

没有需要 grill 的产品问题。owner 已明确阶段二与阶段三共同实施以及 `map if present, otherwise spec`；Artifact 已明确 worker 单次派发检索、reviewer active Rules、retro evidence、`needs-triage` 和 owner approval。其余是对现有 MMW 接口的工程适配。

## 可复查来源

- [《Project Context 调研与 MMW 方案》](https://claude.ai/code/artifact/b9520c08-eb0d-40f1-872e-228662445954?via=auto_preview)的第 5 节“实验结果”、第 6 节“阶段二”、第 7 节“阶段三”和第 9 节“决定”
- [BMAD-METHOD `bmad-retrospective` @94b6727b](https://github.com/bmad-code-org/BMAD-METHOD/tree/94b6727b00c8316557828c8a8ff2a48ff60d60cc/skills/bmad-retrospective) 的 `workflow.md`、`references/evidence-gathering.md`、`references/acceptance-verdict.md` 与 `references/retro-document.md`
- [Devin Session Insights](https://docs.devin.ai/product-guides/session-insights)
- [Augment Review Guidelines](https://docs.augmentcode.com/codereview/review-guidelines)
- [OpenAI Harness engineering](https://openai.com/index/harness-engineering/)
- [OpenAI Introducing Codex](https://openai.com/index/introducing-codex/)
- [Nowledge Mem Background Intelligence](https://mem.nowledge.co/docs/concepts/background-intelligence)
- [Nowledge Mem Spaces](https://mem.nowledge.co/docs/spaces)
- [Nowledge Mem Context](https://mem.nowledge.co/docs/ai-context)
- [Nowledge Mem CLI](https://mem.nowledge.co/docs/cli)
- `docs/agents/issue-tracker.md` 的 `Reading a tree`、`Three label sets`、`Morning queries` 与 `Wayfinding operations`
- `docs/contexts/task-board/CONTEXT.md` 的 `The Night`
- `docs/contexts/tickets/CONTEXT.md` 的 `spec`、`ticket`、`sub-issue` 与 `map`
- `docs/contexts/night/CONTEXT.md` 的 `main agent`、`closing pass`、`route`、`summary` 与 `spec.closed`
- `mmw-v2/skills/dispatch/references/night.md` 的 `## 4. The closing pass` 与 `## 5. The night is over`
- `mmw-v2/skills/dispatch/scripts/dispatch.sh` 的 `summary_spec()` 与 `route_finding()`
- `mmw-v2/skills/dispatch/scripts/status.py` 的 `summary()`、`ROUTES` 与 `routed_counts()`
- `mmw-v2/skills/verify-ticket/scripts/events.py` 的 `EVENTS`、`CHILD_RESOLUTIONS` 与 `fold()`
- `mmw-v2/upstream/skills/engineering/code-review/references/session.md` 的 `## 4. Sort every review finding into in-ticket or out-of-ticket` 与 `## 5. Write one review comment on the ticket`
- `mmw-v2/upstream/skills/in-progress/retro/SKILL.md` 的 `## Steps` 与 `### Implementation vs Review`
- `mmw-v2/skills/verify-ticket/scripts/tree.py` 的 module docstring 和 `LAYERS`
- `mmw-v2/board/board_data.py` 的 `BoardStore._read_trees()` 与 `BoardStore._spec_trees()`
- `mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md` 的 `Work through the map`
- `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md` 的 `Process`
- `mmw-v2/upstream/skills/engineering/implement/SKILL.md` 的 read-in 与 `While writing code`
- `mmw-v2/install.sh` 的八项 installed items 与 `--check`
- 本机 Nowledge Mem Codex connector `hooks/nmem-context.py` 的 `_load_startup_context()` 与 `main()`
