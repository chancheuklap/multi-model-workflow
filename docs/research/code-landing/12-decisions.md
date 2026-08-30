# 落地定案全记录（2026-08-28）

**本文是全部定案的唯一登记处。** `00-synthesis.md` 只做调查汇总，蓝图页 `11-target-pipeline.html` 只画流程并指向本文编号；两处都不复述定案内容。改定案只改本文。

每条记录：当时的现状、摆出的选项、用户的裁决与原话、最终结论、落到哪个文件。编号按讨论块分组：P = 通用原则；0 = 昨晚三轮调查后的定案（标明今天是否沿用）；A 票的形态、B 收尾与复查、C 写码纪律、D UI 基线与工具、E 派发、F 落地、G 按机制用途复查、H Herdr 与自动化。票和 spec 引用定案时用这套编号。

用户要求：讨论时重新说明上下文、用直白中文、不用自造词；每次定案立刻登记并提交。

除了 B7 记的 code-review 方法论扩充（以后只改 `code-review` 技能，见 `#60` Out of Scope）与 F1 记的第一张真实的票（待用户定，`#75` AC1），全部议题已定；改动顺序是 `#60` 的十一节，已拆成 `#61`–`#75` 十五张票。

## 块 0 · 昨晚三轮调查后的定案（2026-08-27 夜 → 08-28 凌晨）

原在 `00-synthesis.md` 的「第一轮之后已定的事」「第二轮之后的定案」「第三轮之后的定案」「每票派给谁」四张表，搬到这里；每条标明今天是否沿用。

### 0.1 第一轮之后已定的事

| 议题 | 决定 | 今天 |
| --- | --- | --- |
| agent 开工拿到的输入 | 票本身；不另写派发词 | 沿用；E1 定派发词 = 技能名 + 票号 |
| spec 怎么进票 | 只给指针，不抄；`implement` 只读 `Parent` 指名的小节 + Testing Decisions + Out of Scope，不读 spec 全文 | 沿用 |
| UI 原型的路径 | `prototype` 出一版满意的 mockup → 上传 Claude Design 精修（沿用 claude-design-blocks 技能）→ 下载回叶子目录，下载回来的文件是基线 | 沿用；D1 定 claude-design-blocks 改输入；D5 加交接包 README 与 DESIGN.md |
| 实现与基线怎么比 | 按场景 × 窗口截图逐像素比对；差异非零不判失败，把基线、实现、diff 三张图贴到票上给人看 | **被 0.2「UI 验收」覆盖**：没过即 failed，不交人 |
| 写码中发现契约装不下 | 继续做，在 spec 下开 sub-issue 记录 | 沿用 |
| code-review 之后 | 修与票的验收标准或 spec 决策相关的发现，其余开 sub-issue；最多两轮，第二轮仍有票内发现则不关票 | **被 B2 覆盖**：一轮、修一轮、不复审 |

### 0.2 第二轮之后的定案

| 议题 | 决定 | 今天 |
| --- | --- | --- |
| Worker 与 verifier 是谁 | Worker 是 Herdr 拉起的独立会话（可在任一宿主），每票一个 worktree，按阻塞关系决定启动顺序；verifier 是编排会话自己的只读子代理。「票即输入」= Herdr 启动 worker 时喂的提示词 | worker 部分沿用；verifier 父会话**被 0.3 覆盖**（运行 implement 的会话派） |
| `Owns:` | 加；路径外改动记在收尾评论 `Outside Owns:` 行，不开 sub-issue | 沿用；A2 定起点与两档 |
| `CHECK:`/`EXPECT:`/`EVIDENCE:` | 加；写不出命令的标 `MANUAL:`，不过半 | 判据沿用（A5）；`MANUAL:` 这个写法**被 I2 取代** |
| verifier 次数 | 只审一次。worker 自跑 → verifier 一次 → 没过的 worker 修并自跑填证据 → 关票；不复审 | 沿用；B2 定它在 code-review 之前 |
| ponytail | 收：grep 每个调用方修共用处；写 helper 前先在仓库与 Read first 的 prototype 找现成；加文件/依赖/配置前说出已有的为何不够；安全与「票里明确要求的东西」不许简化；收尾 `skipped: [X], add when [Y]`。不收：原生控件替代自绘、先交懒版本再问、`demo()` 自检、`ponytail:` 注释、交互模式段。措辞写成动作 + 票字段；「逐字复制」改为保留骨架只换对象；用第一张真实的票跑一遍验证 | 沿用；C1 定不做对照实验 |
| UI 验收 | 两档自动判定：ARIA 树（去 Claude Design 运行时包裹）diff 必须为零；同场景同窗口截图差异像素 ≤ 3%（默认，Testing Decisions 可改）。没过即 `failed`，worker 修；不产生 `decision`；工具把 ARIA 树变了的那几行印在 `DIFF` 底下，截图落在 `--out` 供人按需打开。不用 `accepted-diffs.json` | 沿用；阈值**被 0.3 改为 1%** |
| 失败词汇 | `ALL MET` 关票；`HANDOFF REQUIRED` 不关票、`ready-for-agent → ready-for-human`；`ABANDON: AC<n> <failed|blocked|impossible|decision> <理由>`；sub-issue 带 `needs-triage`；开工 `--add-assignee @me` | 沿用；B6 定 decision 也贴 ready-for-human |

### 0.3 第三轮之后的定案

| 议题 | 决定 | 今天 |
| --- | --- | --- |
| verifier 的父会话 | 运行 `implement` 的那个会话（worker）派 verifier 子代理；主 agent 作为 coordinator 只读票上的 `VERDICT` 行。不能派子代理时按 `06` §6 降级为 `self-reported` | 沿用 |
| 交接前自审 | 采 unlazy「Audit the final report」：写收尾评论前重读票全文与 `Read first` 每项，把每条验收标准追到 `EVIDENCE:`，`Counts:` 重数后填；不做 swarm-forge 二次调用 | 沿用 |
| UI 验收阈值 | ARIA 树 diff = 0；像素 ≤ 1%（Testing Decisions 可改）；工具自带负控制，负控制不过则不信任本次结果 | 沿用 |
| 新词定义 | 进入 spec 阶段时由 `grill-with-docs`/`domain-modeling` 建根 `CONTEXT.md`，全英文术语（`Owns`、`CHECK`/`EXPECT`/`EVIDENCE`、`MANUAL`、`ABANDON` 四个 kind、`ALL MET`/`HANDOFF REQUIRED`、`VERDICT` 五级） | 沿用；落地 spec 里建 |
| 技能正文纪律（沿用上次裁决） | 一律英文；不写出处、不写落地记录；每个角色的纪律只写在它自己的定义文件里 | 沿用 |
| 落地节奏（沿用尸检 §5） | 一次一份 spec、一组机制；没有一张真实代码票从头跑到尾不合 main；抄机制先列消费者 | 沿用；F1 定用虚构票逐处测 |

### 0.4 每票派给谁

沿用上次的角色表数值，只取本轮存在的角色；表放消费仓库 `docs/agents/`，主 agent 派发时选初级或高级（白天与用户定好），不写进票、不打定级标签。

| 角色 | 宿主 kind | 模型串 | 思考强度 | 今天 |
| --- | --- | --- | --- | --- |
| 初级工人 | cursor | cursor-grok-4.6-high | high | 沿用；E1 定完整启动命令 |
| 高级工人 | grok | grok-4.6 | xhigh | 沿用 |
| 复验者（worker 会话的只读子代理） | 与 worker 同宿主 | 该宿主里与 worker 不同的模型（`06` §6） | high | 沿用 |
| 编排者（自动化阶段再用） | claude | opus | medium | 沿用 |
| reviewer 会话 | claude | opus | — | **今天新增**（B7） |

规划者、升级顾问本轮没有对应角色，不列。

## 通用原则（讨论中由用户裁定，覆盖多条）

### P0. 角色：主 agent 是谁，用户是谁

- 用户原话（2026-08-28 晚）：「出票的不是人类，是使用了 to-ticket 的主 agent。白天的时候主 agent 通过 mmw v2 前半段一系列技能与我讨论调查研究确定一系列参考资料和 spec、ticket，晚上主 agent 作为 coordinator 指挥其他一系列 agent subagent 工作。目前主 agent 就是 claude code 里的 agent。」
- 结论：**主 agent** = Claude Code 里的那个会话，全天只有它一个：白天用 wayfinder / grill-with-docs / research / prototype / to-spec / to-tickets 与用户讨论、出 spec、出票；晚上作为 coordinator，按 `docs/agents/models.md` 经 Herdr 起 worker（cursor / grok 会话），等票的状态。**用户**只讨论、拍板、改 `models.md` 里的安排、早上看票；用户不出票、不做票。**worker** 永远是主 agent 派出的 cursor / grok 会话，不存在「白天用户自己在 Claude Code 里做一张票」的场景。verifier 是 worker 的子代理；reviewer 会话是 worker 经 Herdr 起的 Claude Code 会话。
- 更正范围：此前所有文档里「白天你手工做票」「白天用户在 Claude Code 里直接 `/code-review`」「白天手工、夜间派发同一份流程」的说法作废；「出票的人」= 主 agent；`models.md` 的读者 = 主 agent（起 worker）与 `implement`（起 reviewer 会话）。
- 测试时的例外：落地 spec #60 第 1–10 节用虚构票测技能时，由我（本会话，即主 agent）临时扮演 worker 直接跑 `implement` 等技能，只为验技能文本；真实流程里主 agent 不做票。
- 落点：本文各处、蓝图页、#60。


### P1. 子代理只收此刻才知道的信息；票是唯一的事实存放处；不转述

- 触发：讨论 B3 时，我按 `06-independent-verifier.md` §8.2 说 verifier 的 brief 要由 worker 粘贴 AC 原文、CHECK/EXPECT、Seam、commit、分支、worktree、禁令、汇报格式。
- 用户原话：「为什么票里都有的东西……还需要 worker 再去向 verifier 转述一次，这是在任何步骤里都不应该的，之所以用文档把事实和状态记录下来就是不需要 agent 再去转述，不然肯定会漏」「既然 verifier 是 worker 的 subagent，最终 commit 号 + 分支 + worktree 路径都不需要转述，两者本来就在同一个 commit/分支/worktree 工作」「verifier 的禁令和汇报格式，包括它的工作方式和流程同样不需要 worker 转述，直接写在 verifier 的配置文件里就可以。所有 subagent 形式的 agent 都应该这样去设计，只有像 worker 这样的跨 harness agent 才需要被现场传递信息，但是传递的只能是实时变化的信息，固定的信息应该做成技能让 agent 调用」
- 结论：子代理的 prompt 只含票号（和起点 commit 这类此刻才知道的值）；动作、禁令、汇报格式写在子代理自己的定义文件；任何 agent 要票上的信息自己 `gh issue view`；跨宿主的 worker 派发词只有「技能名 + 票号」。
- 按此要改的地方（当时列出的清单）：① verifier brief → 只有票号，其余进 `mmw-v2/agents/verifier/body.md`；② verifier 的结果由它自己 `gh issue comment` 写到票上，worker 之后读票；③ `code-review` 两个子代理的 prompt 现在粘 smell baseline 全文、标准文件、spec 全文——固定内容要挪出 prompt（后来定为三个 reference 文件，见 B7）；④ `06` §8.2「粘贴原文而不是让它读票」及其 pstack 理由「workers cannot see siblings」作废——那是云端 worker 读不到本地的场景，我们的子代理在同一 worktree、有 `gh`；⑤ 现有 `ui-evaluator` agent 同样要求把评估问题逐字粘进 prompt，违反此原则，但 ui-qa 本轮不接入，只登记；⑥ worker 派发（`09` §2.2）已符合，不改；⑦ ponytail 五句、Owns 核对、读法收窄已在 `implement` 正文，不改。
- 落点：本文；蓝图页步 9、步 10 详情。

### P2. 措辞：用直白中文，不用自造词；「穿行」「探针」「UI 票」都不用

- 用户原话：「太多自创的词汇和说法，我看不懂」「不要用这么奇怪的词汇行不行，就用直白的中文不可以吗」「根本就不存在独立的 UI 票，你根本就没有看过 to ticket 技能，ticket 都是纵切的」
- 结论：说「用真实的票跑一遍」不说「穿行」；说「有句/没句的对照实验」不说「探针」；票是纵切的，一张票贯穿数据、接口、界面，只有「UI 验收标准」没有「UI 票」。今天写进 `00-synthesis.md` 与蓝图页的措辞已按此改。
- 落点：本文；`10-previous-attempt-postmortem.md` §5 第 2 条改写。

### P3. 提问前先把牵涉的原件读完，不凭报告转述发问

- 触发：B8 讨论时我按 `05` 报告的转述描述 `gate-check.mjs`；用户问「在问我问题之前，你自己是否已经充分去读过上面提到的所有东西」。我承认没读原件，读完 `gate-check.mjs`（894 行）、`lib/gates.mjs`、`references/gates.md`、`SECURITY.md`、`check-supervisor.mjs` 并在 scratchpad 实测后，选项被重摆（见 B8）。
- 之后每条提问前都先读原件：C1 前读 ponytail 规则正文与对照实验结果文件；D1 前读 `claude-design-blocks/SKILL.md`；D3 前读 `support.js parseDataProps` 与 `mkharness.py`；E1 前跑五个宿主 CLI 的 `--help`。

### P4. 不加标签、不改既有标签含义

- 用户原话：「尽可能不要再增加标签了，现在项目仓库 agentflow 里的 GitHub 标签已经够乱了甚至需要再清理一次留下真正合法的标签」
- 落点：B6。

### P5. 讨论进度与定案必须完整登记，页面要一眼能看到

- 用户原话：「先讨论到这里，你登记一下进度」「我们讨论这么久的结论你到底都更新保存到哪里去了，artifact 看起来没有什么变化」「我发现在文档和 artifacts 里对讨论内容的登记非常简略模糊，你回顾对话历史，尽可能登记完整」
- 事故：蓝图页一直发布的是主仓库目录下一份误写的旧拷贝，worktree 里的 17 个提交内容没有上线。已改为发布 worktree 的文件到同一网址，线上版与本文逐条核对过。主仓库目录下的两份残留由用户丢弃。
- 落点：本文；蓝图页第 0.5 节。

### P6. 词表按「英文正名 + 中文正名」两栏；票一律用正名

- 触发：#66 原来只收十一个词。把 #60 与 23 张子票的正文和评论全读一遍收词（六个子代理并行，原始 369 条），去重归一后 94 条，分十四组。
- 收出来的漂移（同一件事在票上有好几个名）：main agent 又叫编排者、coordinator、orchestrator、落地 agent；worker 又叫工人；`[fixture]` 票又叫虚构票；基线目录又叫基线；三个测试层名时带「层」时不带；交接包又叫开发交接包；账本又叫临时账本。上次落地正是词表是中文导致 `dispatcher` 漂移（`10-previous-attempt-postmortem.md` §6 表末行）。
- 摆的选项：A 每条给英文正名，定义里附中文正名，`_Avoid_` 收两边的变体；B 严格全英文，那 31 条只有中文名的各造一个英文名。
- 用户裁决：「A。你要把整个 #60 和子 issue 重写」。
- 结论：
  - 根 `CONTEXT.md` 每条写英文正名，定义里括注中文正名，`_Avoid_` 列两边真的在票上出现过的变体（格式见 `mmw-v2/upstream/skills/engineering/domain-modeling/CONTEXT-FORMAT.md`）。
  - **要不要中文正名的判据**：一个概念本身就是一个固定字符串（`ALL MET`、`CHECK:`、`--preflight`、`VERDICT`、`PARITY OK`）时，那个字符串就是它唯一的名，不另起中文名；一个概念是角色或做法（main agent、读法收窄、收尾七步、三个测试层）时，英文与中文各一个正名。
  - 这条覆盖 0.3「新词定义」行里的「全英文」：`CONTEXT.md` 主体仍是英文，中文正名只作为词条内的括注。
  - #60 与全部 23 张子票的**正文**改到正名上；**评论不动**——评论是当时发生了什么的记录，改它等于改史。
- 连带（收词时核出的两处事实错误，一并改掉）：
  - **证据页已经不存在**。#65 的 AC11 整条撤销，证据页在 `dda5a01e` 删掉，`--out` 现在只落每场景每窗口的 `baseline`/`impl`/`diff` 三张 png 与 ARIA 树。#60 第 2 节、#63、#69 里把未跟踪产出物叫「证据页」的地方都要改。
  - **`phase=stalled` 是死词**。写它的是 `hook.py stop`，而 #64 把那道 Stop gate 整个拿掉并入 #87，现在没有任何东西写它。实际取值六个，全部由 `verify-ticket.py` 写：`selfcheck`、`verify`（#62 AC12）、`implement`、`closed`、`handoff`、`closeout-rejected`（#63 AC16）。#87 里的 `agent_prompt_stalled` 是 Herdr 自己的返回值，与它无关。
- 落点：#66 的收词清单与验收标准；#60 及 23 张子票正文的用词；原始采集与归一表贴在 #66 的评论里。

## 块 A · 票的形态

### A1 验收标准的编号与人工项的写法（**「不过半」被 I6 取消，编号沿用**）

- 现状：`to-tickets/SKILL.md` `<issue-template>` 的验收标准是 `- [ ] Criterion 1` 两行打勾清单，无编号；worker 做完自由文本写证据、自己打勾。
- 已定（昨晚）：每条标准出票时带 `CHECK:`（能跑的命令）、`EXPECT:`（只在成功时打印的那句）、`EVIDENCE:`（做完填）；写不出命令的标人工；人工项不过半。
- 待定细节与选项：① 编号——unlazy 要求显式 id（行号不稳定），`05` §8.1 用 `AC<n>`；② 人工项——unlazy 是「CHECK/EXPECT 都不写」靠脚本识别，我们无脚本，`05` §8.1 自造 `MANUAL: <谁> <看哪个制品>` 一行；③「不过半」是硬规则还是提醒。
- 建议：`AC<n>` 出票时编、不重排；明写 `MANUAL:` 行；过半为出票硬规则，回 `/to-spec` 补测试层（夜里跑的票人工项 agent 跑不了，过半的票出了也白出）。
- 用户裁决：「都可以」。
- 结论：三条全采。
- 后续：`MANUAL:` 这个写法被 I2 取代，「不过半」被 I6 取消；只剩「`AC<n>` 出票时编、不重排」还活着。
- 落点：`to-tickets` 模板与 Read back。

### A2 `Outside Owns:` 的 diff 起点；Owns 的两档规则

- 现状：昨晚定票加 `## Owns`（允许改的目录 glob）；收尾跑 `git diff --name-only <起点>..HEAD -- . ':(glob,exclude)<每条 glob>'` 列出范围外改动，非空则收尾评论逐条说明（`04` §3、§7.4）。
- 待定：起点取 A `git merge-base main HEAD` 自动算，还是 B 开工时记进票。
- 用户先质疑范围本身：「为什么要限定票允许改的范围，不会导致中途额外发现的问题的堆积和代码质量的下降吗？既然参考了 unlazy 的做法，为什么不思考是否使用它的脚本呢？」
- 回答要点：范围不是「一律不许碰」，是两档——为过本票 AC 不得不改的范围外文件照改并在收尾评论 `Outside Owns:` 说明；与 AC 无关的顺手改动不改、开 sub-issue。判据：不改它本票哪条 AC 过不了。目的是让票外改动可见（上次尸检里工人「自己拿了六个主意」用户看不懂）。堆积会堆在 sub-issue 里早上分诊；质量由 tdd、code-review、verifier 管，范围不拦第一档。unlazy 的 `OWNS` 脚本只做并发加锁、从不检查实际改了哪里（`04` §2.4），用不上；它的 `gate-check.mjs` 跑验收标准值得考虑——留到 B8 讨论。
- 用户裁决：「A」。
- 结论：起点 `git merge-base main HEAD`，不记进票（每票一个 worktree、按阻塞关系串行开工，分支都从 main 开）；两档规则确认。
- 落点：`implement` 收尾段。

### A3 `CHECK:` 不许自己去找它验的是哪个对象

- 触发：#61 关票后核 #62 的 AC，发现 AC4、AC6、AC13 三条的 `CHECK:` 里各有一段 `n=$(gh issue list --state open --search "[fixture] in:title -spec" --json number --jq '.[0].number')`，用来找 #61 交付的那张虚构票。实测这条搜索取到的是 **#61 自己**——#61 的标题里也有 `fixture`，而 #61 的正文恰好也含 `## Owns`、`(new)`、四条以上 `AC<n>`、`MANUAL:`、`visual-parity.py`、`uv run pytest`，于是 #61 自己的 AC7（同一条搜索）在虚构票根本不存在时也会打勾——一条不可能失败的检查。#61 的那两条已在关票前改成按标题前缀用 `jq` 挑。
- 摆出的选项：① 标题前缀 + `jq` 精确挑（#61 已用）；② 测试台里放一个 `tickets.json` 记住虚构票号，`CHECK:` 从它读；③ 票号写死。
- 用户裁决：先否掉 ①——「那你能保证以后所有应该被搜到的票也按固定的前缀开头吗」；再否掉 ②——「你现在要考虑的不仅仅是如何通过这次的测试，而是要构建一个以后都通用的方法，你推荐的选项 1 是通用的方法吗？」；最后给出判据：「我们现在所搭建的测试和测试方法就应该按照改造完全落地以后的工作流来搭建呀」。
- 结论：**`CHECK:` 不得搜索或推断它要作用的对象。** 对象要么是**这张票自己**——落地后 worker 的常态，票号从派发词 `implement #<n>`、`dispatch.sh` 注入的 `$MMW_TICKET`、分支名 `issue-<n>` 三处都拿得到，worker 从不搜自己的票号；要么在票上**按编号指名**——一个具体的号（票引用票号本来就是常态，蓝图页示例 AC7「与 #540 决议第 3 条一致」、#77 的 AC3 都是）。禁止的是「搜出来取第一个」。要一批运行时才产生的对象时，从指名的锚点顺 GitHub 原生关系导出（`gh api repos/{owner}/{repo}/issues/<spec>/sub_issues`），不全库搜索。
- 这条与 `05-runnable-acceptance-gates.md` §3.1 那七条作者规则同类：防的都是**一条可能验错东西、或者不可能失败的检查**。
- 落点：#68（`to-tickets` 第 3 步的验收标准规则，新增 AC11）与 #60 第 3 节同一处；#62 的 AC4、AC6、AC13、#61 的 AC6 与 AC7 都按编号指名（`77`、`76`）；#68 的 AC8 与 #75 的 AC2 从 `gh api repos/{owner}/{repo}/issues/<spec>/sub_issues` 顺关系取，集合为空时本条判不过——否则循环跑零次仍会打印成功标记，又是一条不可能失败的检查；`[fixture]` 的 #77、#78 挂在 #76 名下，这条路径才取得到东西。

### A4 `CHECK:` 与 `EXPECT:` 的写法由脚本判，不由出票的 agent 记

- 触发：#63 落地后自跑，16 条标准里 12 条报 unmet，而它们的测试全是绿的。查出三处不符，都在票的正文里，spec、测试台、`verify-ticket.py` 都没错：
  - `EXPECT: /OK$/` 判不出 `python3 -m unittest` 打印的 `OK`。`gate-check.mjs:586` 把 CHECK 的完整输出（stdout 接 stderr）交给 JavaScript 正则，命令的输出末尾带换行，JS 的 `$` 不匹配换行前的位置。这条标准**永远不可能过**。全库扫出 16 条：#62 的 AC5、AC7、AC12，#64 七条，#65 六条。#62 那三条当时是我看着输出手工判的，结论对，但判的人不该是我（#60 US6）。
  - #63 的 AC8 关掉 #77，AC9 需要 #77 开着却不自己重开；AC3 与 AC15 各 `git checkout -B` 切了分支不切回。`gate-check.mjs:661-674` 按账本顺序一条一条跑（`--jobs` 默认 1），每条一个独立 shell、cwd 固定为仓库根（`:638-640`）——`cd` 到不了别人，分支、票、工作区却是共享的，`--reverify` 还会把每条再跑一遍。全批 15 张票里 9 条 CHECK 会改共享状态，分布在 #61、#63、#65、#67、#71，不是虚构票特有的。
  - #63 的 AC12 要「一个从上游 `validate-plan.py` 的 docstring 例子改来的环用例」，而那个文件的 docstring 里没有例子。
- 摆出的选项：把 EXPECT 的正则写法与 CHECK 的副作用写成两条出票规则，落进 #68；或者靠 `--lint` 抓。
- 用户裁决：「不应该由我来拆定，要看脚本和在那个地方工作的 agent 需要什么」——判据是脚本与 agent 的需要，不是选项偏好。
- 结论：按这个判据分两路。
  - **脚本判得准的，不写规则。** `$` 没有 `m` 标志一定错，`verify-ticket.py --lint` 静态判得出，报 `dollar-without-m`（ERROR，退出 1），发现里直接给出改法 `/^OK$/m`。出票的 agent 不必记住 JS 正则的冷知识，它在 Read back 那一步照着改即可。
  - **脚本判不准的，写规则。** 一条 CHECK 改共享状态不一定错（#61 起 `http.server` 是必须的），对错在顺序，静态看不出。规则：**一条 `CHECK:` 自带它需要的前置状态，并把改过的状态还原；不依赖前一条留下什么。**理由不是整洁，是 `--reverify` 本来就要把每条再跑一遍。`--lint` 另报 `shared-state`（WARN，不改退出码），列出会改分支或改票的 CHECK 供核对。
  - 连带查出第三处：`gate-lint.mjs:129` 的 `manual-gate` 对每一条 `MANUAL:` 都报 warn，`--strict` 下 warn 即退出 1，所以只要票有一条人工项，「`--lint` 报出的发现改到没有」就永远做不到——与 #60 US3（允许人工项，不过半）冲突。改成：**ERROR 改到没有；WARN 逐条看过，留下的在收尾评论里说明为什么留。**
- 与 A3 同类：A3 防的是「一条可能验错东西的检查」，A4 防的是「一条不可能过的检查」和「一条被前一条弄坏的检查」。三条都是出票时写坏、夜里才发作的。
- 落点：`verify-ticket.py` 的 `lint_expectations` 与 `lint_check_effects`（提交 `b69d201f`）；#68 与 #60 第 3 节加 CHECK 自带前置那一条、改 Read back 的收敛判据；#62、#64、#65 的 16 条 EXPECT 已改；#63 的 AC3、AC9、AC15 已自带前置并还原。

### A5 `MANUAL:` 的判据是「这条标准的读者是谁」（**写法被 I2 覆盖，判据沿用**）

- 触发：#63 原来的 AC12（对照上游读两个函数）与 AC13（读拒绝文案）都写着 `MANUAL: 用户`，但它们判的是**代码对不对**和 **agent 读到的话够不够用**——读者都是 agent。两条改成可跑的 CHECK 之后 #63 是 18/18 无人工项。#69 又犯了同一个错：AC4 判 `body.md` 里有没有出处引用、有没有要求 worker 转述（三项都能 grep），AC7、AC8 读的是主 agent 手上就有的子代理报告，AC9 的记录本来就是主 agent 写的——四条却都标了 `MANUAL: 用户`，收尾时按 H6 开成四张 sub-issue 交给用户。
- 用户原话：「为什么要开那么多 issue 给我去做，明明你自己可以去验证的」。
- 结论：**写 `MANUAL:` 之前先问这条标准的读者是谁。** 判代码对不对、判 agent 读到的话够不够用、判一份 agent 自己拿得到的报告——读者都是 agent，写成 CHECK；写不出命令但 agent 读得了的，由主 agent 读完把结论写成一条票评论，不开 sub-issue。`MANUAL: 用户` 只留给读者确实是人的：真实宿主会话里的行为观察、界面好不好用、票读起来像不像真票、一句只有用户能拍的决定。
- 与 H6 的关系：H6 定的是「没人填 EVIDENCE 的 `MANUAL:` 开成 sub-issue、票不停」，那是**已经确认读者是人**之后的走法；本条管的是上一步，防的是把本来该自己做的事切成 issue 丢给用户。与 H8 也不同：H8 管「人要读的制品必须在 GitHub 网页上打得开」，本条管「这件事该不该给人读」。
- 静态判不准（「读起来像不像真票」与「这段话 agent 够不够用」在词面上没有区别），所以按 A4 的分路写成出票规则，不进 `--lint`。
- `MANUAL:` 的第三种写法：`MANUAL: 主 agent <读什么>`。读者是 agent 但写不出命令时用它，主 agent 读完把结论写成一条票评论并自己填 `EVIDENCE:`，所以收尾时它不会落到 H6 的 sub-issue 里。三种写法的分工：能跑命令 → `CHECK:`；agent 读得了 → `MANUAL: 主 agent`；读者确实是人 → `MANUAL: 用户`。
- 已按此扫过全批（2026-08-29）：十一张开着的票里 22 条 `MANUAL: 用户` 改成 `MANUAL: 主 agent`、1 条改成 `CHECK:`（#64 的 AC12，与 #63 AC13 同法，断言 `tests/test_hook.py` 里一个具名测试类）；开着的票上只剩 6 条 `MANUAL: 用户`，都是读者确实是人的——#65 AC11（工具印出差异的文本，`0.2`）、#66 AC7（`models.md` 的安排是用户的）、#73 AC9 与 #75 AC6（早上的网页入口，H8）、#73 AC10 与 #75 AC7（收尾评论与「我自己拿的主意」那段给人读）。每张票的人工项都不过半。
- 已关的票不动：#61 的两条、#62 的两条留在原样，其中 #62 的 AC9（读 `SKILL.md`）按本条本该是 `MANUAL: 主 agent`，但票已关且已判过，不追改。
- 落点：#68（`to-tickets` 第 3 步的验收标准规则）与 #60 第 3 节同一处；#64–#75 十一张票的 23 条已改；#69 的四条已由主 agent 自己验完，#80–#83 四张 sub-issue 各带结论关掉。

## 块 B · 收尾与复查

### B1 verifier 与 code-review 的区别、是否合并

- 用户提问：「verifier 和 code review 有什么区别，我认为他就应该是 code review 的执行者」。
- 回答：code-review 是两个只读子代理拿 diff 对照编码规范（Standards）和 spec（Spec），不跑命令；verifier 拿票上每条 `CHECK:` 在最终 commit 上跑，判「退出码 0 且输出匹配」，不给 diff/spec，不评代码。合并的代价：评审引出修改→commit 变→VERDICT 作废；主观发现与客观判定混在一个脑子里。
- 结论：不合并；两者都是子代理。

### B2 顺序改为先验后审；code-review 只一轮

- 用户看蓝图页步 8–10（code-review → 自跑 → verifier）后裁决：「verifier 放在 code review 后面，是完全错误的，设想如果 verifier 发现漏掉内容，又要返工给 worker，worker 改完还要不要再次 code review 呢，这是资源浪费，所以就应该先在 worker 那个 agent 里直接派一个 subagent verify，没问题了再交给 code review，另外，code review 只能审一轮，然后 worker 修一轮，不再复审」。
- 结论：步 8 worker 自跑 CHECK → 步 9 verifier（worker 会话内派）→ 没过 worker 修并自跑、不派第二次 → 步 10 code-review 一轮、worker 修一轮、不复审（覆盖昨晚「≤2 轮」）。连带：修完在最终 commit 上再自跑 CHECK 填 EVIDENCE；VERDICT 行照实绑 verifier 验过的那个 commit。
- 落点：蓝图页步 8–10 重排；`implement` 收尾段。

### B3 verifier 每票都派

- 现状分歧：定案序列字面是每票都派；`06` §5.2 建议只对四类票派（有 MANUAL 或验界面 / 无人看守 / Owns 触及迁移、鉴权、对外接口、共用路径 / CHECK 要起 app 或 DB），依据 pstack「重跑一条命令的 verifier 是仪式」。
- 用户追问 verifier 做哪些工作、四类票从哪来。回答后用户裁决：「根本不用去给票分类型，每一个票都很重要，都会直接影响落地效果，不存在难易轻重」。
- 结论：每票都派，不分类。

### B4 verifier 的工作内容（定义文件要写的）

- 输入：票号（P1）。它自己 `gh issue view` 读 AC 的 CHECK/EXPECT/MANUAL 与 Seam；`git rev-parse HEAD` 取 commit；与 worker 同一 worktree。
- 动作：`git status --porcelain` 一次（贴报告）→ 每条 CHECK 原样跑（后来定为经 `/verify-ticket --reverify`，见 D5）→ MANUAL 条目不跑只标「人工，未跑」→ 再 `git status --porcelain` 一次，两次都空才算没动东西 → 自己 `gh issue comment` 写 `VERDICT <commit> <等级> by <模型> — 一句话` + 每条 AC 一行（id、退出码、匹配与否、输出前 200 字）。
- 等级五选一：`live-ui-verified`（在跑起来的界面走过流程且全过）/ `unit-test-verified`（命令全过，没起界面）/ `type-check-only`（只有类型检查过；有行为改动的票不算过）/ `verifier-blocked`（命令起不来）/ `verifier-failed`（跑了但至少一条没过）。
- 不做：不改仓库文件、不 commit、不修、不提新标准、不评代码质量、不看多做少做。
- 可以做（B5）：动环境。

### B5 `verifier-failed` / `verifier-blocked` 之后

- `verifier-failed`：worker 修并自跑填 EVIDENCE，不派第二次，继续进 code-review（随 B2 定）。
- `verifier-blocked`：我建议交人（HANDOFF blocked）。用户裁决：「缺依赖、端口被占、没凭据、要真机 我没看出这里面有哪一个问题是 verifier 自己解决不了的，根本就不需要问人也不需要问其他 agent。没凭据是什么意思」。「没凭据」= 验收命令要用的密钥或连接串没设。
- 结论：verifier 不改仓库文件但可以动环境（装依赖、换端口、从项目配置找连接串）；先自修环境再跑；仍起不来才写 `verifier-blocked`，由 worker 修环境后自跑，与 failed 同路；不触发 HANDOFF。

### B6 `decision` 类 HANDOFF 的标签（**落点被 I3 覆盖**）

- 现状：五个标签（`needs-triage`、`needs-info` 等报告者、`ready-for-agent`、`ready-for-human` 需人实现、`wontfix`）。四种 ABANDON kind 里 `failed / blocked / impossible` 贴 `ready-for-human` 语义吻合；`decision`（只等一句话）贴哪个。
- 选项：A 也贴 `ready-for-human`；B 改 `needs-info` 含义；C 加第六个标签。
- 用户裁决：「A 尽可能不要再增加标签了……」（P4）。
- 结论：`ready-for-human`；kind 靠收尾评论 `ABANDON:` 行第二个词区分。

### B7 code-review 的形态、谁派、跑在哪、方法论

- 形态：用户否决「做成 `mmw-v2/agents/` 下两个 subagent 定义」，裁决：「这种情况就应该把 code review 技能做成一个 skill.md 加三个 reference，对应派发 reviewer 的 agent……和两种 reviewer，利用 skill.md 去路由」。结论：`code-review/SKILL.md` 只路由；`references/dispatch.md`（派发者：取起点 commit、票号、收两份报告、分票内/票外）、`references/standards-reviewer.md`（brief + smell baseline）、`references/spec-reviewer.md`；派发 prompt 只给起点 commit + 票号；报告由 reviewer 评论到票上（P1）。
- 谁派：用户「我还不清楚到底是主 agent 派发还是 worker 派发，我倾向主 agent」。我建议 worker 会话派（review 发现要 worker 修；主 agent 派会引出 `09` §5.4 的握手问题——worker 停下等主 agent 读评论再把结果 prompt 回去）。当时我误以为「白天用户自己做票」是一种场景，P0 已更正。用户裁决：「worker 派，在 implement 技能里加一段派发方式就行」。
- 跑在哪：用户「如果 reviewer 由 worker 去派，那 reviewer 不能够是 worker 的 subagent，这是因为 reviewer 所使用的模型必须足够强，目前我的手上只有 Claude code 里的 opus 5 有资格做 reviewer，但 worker 已经确定是 cursor 或 grok build 里的 agent，所以 worker 要用 herdr 调用 Claude code 派发 reviewer」。结论：worker 经 Herdr 起一个 Claude Code 会话，派发词 `code-review <起点 commit> #<票>`，该会话再派两个 reviewer 子代理。前提：worker 在 Herdr pane 里（主 agent 经 Herdr 起的 worker 天然满足）。
- 方法论：用户问「code review 阶段的步骤与方法论是否已经确定是只用现役的 code-review 技能还是要从参考资料里再加入」。回答：没定；`03` §5 列了三样参考里有的（pstack rubric Verification 一栏、grok 发现闭环 `Status: fixed/wontfix`、grok 四人格）。用户裁决：「暂时先这样问题不大，因为后期需要加内容也只是修改 code review 技能就行」。结论：暂用现役两轴；方法论扩充留到以后，只改 `code-review` 技能（`#60` Out of Scope 已列）。

### B8 验收标准怎么跑、怎么判：vendor unlazy `gate-check.mjs`

- 起因：A2 时用户问为何不考虑 unlazy 的脚本。
- 先读原件再实测（P3）。实测（副本放 scratchpad；`05` §10）：① 接受任意路径的账本文件，不要求 `.unlazy/` 或 `GATES.md`——账本可每次从 `gh issue view` 的 AC 段派生到临时文件，跑完贴回票评论，没有第二份要维护的文件（上次「两处漂移」不再存在）；② 我们的票格式原样能解析：`AC1:` 编号、缩进 CHECK/EXPECT/EVIDENCE、`MANUAL:` 行静默当人工项、其他标题忽略，报 `4 gates`；③ 双条件正确：`echo ok; exit 3` 判 FAIL；④ `--reverify` 把已过的也重跑，汇总 `previously met reverified`；⑤ 代价：Node ≥ 16、6 个文件约 2000 行（MIT）、默认超时 120 秒；另有一套批准机制，落地时去掉了（G5）。
- 选项：A 手写约定（agent 自判）；B vendor `gate-check.mjs`，账本从票派生；C 自写 python 跑器。建议 B。
- 用户裁决：「B」。
- 结论：vendor；worker 步 8 与 verifier 步 9 都用（后来包进 `verify-ticket` 技能，D5）；`05` §7 手写 EVIDENCE 格式作废。

### B9 code-review 的 Spec 轴不看基线

- 选项：A 不给基线，照不照基线全交给 visual-parity 那条 AC；B Spec 轴 brief 加 Read first。
- 用户裁决：「A。我想知道的是这个 visual parity 工具由谁去跑」。回答：它是某条 AC 的 `CHECK:`，worker 写码期间迭代跑、步 8 自跑、步 9 verifier 重跑，三次都不需要人。
- 结论：A。

## 块 C · 写码纪律

### C1 ponytail 五句写进 `implement` 后怎么验证

- 五句（昨晚定）：改函数前 grep 每个调用方、修共用处；写 helper 前先在仓库与 Read first 找现成；加文件/依赖/配置前说出已有的为何不够；安全、数据不丢失、无障碍与票里明确要的不许简化；收尾写 `skipped: [X], add when [Y]`。不收：原生控件替代自绘、先交懒版本再问、`demo()` 自检、`ponytail:` 注释、模式切换。
- 证据（读原件 `benchmarks/results/2026-06-22-issue-245-217-comprehension.md`）：第 1 句在 Sonnet/Opus 上 1/6→6/6，且同一意思写成散文 0/3、写成动作 6/6；第 2 句两臂都 1.0 测不出；其余三句没测过。
- 分歧：`10` §5 第 2 条要求「每句入正文前做有句/没句两臂对照实验」；定案表写「用第一张真实的票跑一遍」。
- 建议：用真实的票跑一遍；不做对照实验（只 5 句、写错代价是删掉、第 1 句已有强证据、搭测试台投入不成比例）。
- 用户裁决：用真实的票跑一遍，「但是不要用这么奇怪的词汇」（P2）。
- 结论：先写进正文，用第一张真实的票跑一遍；真票跑出具体问题再针对那一句做对照实验。`10` §5 第 2 条已改写。

## 块 D · UI 基线与工具

### D1 prototype 产物怎么进 Claude Design；`claude-design-blocks` 要改

- 我先错误地把「prototype 产物形态」当分岔重问（A 导出静态 HTML / B 改 prototype 直接产 HTML / C 在 Claude Design 从零画）。用户：「这个问题以前不是澄清过了吗，你有没有看过最新的 prototype 技能，我记得会用一个东西把 mockup 挂进真实代码里面，然后落地时再删掉挂载点呀。我还说过我的工作流是先 prototype 定形然后上传 claude design 精修然后下载回本地做参考呀」。
- 事实：`prototype/UI.md` 步 3、步 6——变体组件放叶子目录 `prototypes/<task>/<issue>/UI/`，真实页面只有挂载点，落地时删挂载点留叶子目录；流程已定：prototype 定形 → 上传 Claude Design 精修 → 下载回叶子目录做基线。
- 剩下的机械细节：`claude-design-blocks` 第 1 步读「mockup 的 HTML 和 JavaScript」，第 2 步「CSS 原样复制、从 JS 抽数据」；我们的输入是框架组件。用户问「那 claude-design-blocks 技能要不要改呢」。
- 结论：`prototype` 不改。`claude-design-blocks` 改第 1、2 步：输入若是叶子目录的框架组件，源码读组件文件（状态、交互），CSS 与 DOM 取自真实页面 `?variant=<胜出>` 的渲染结果，数据从组件 props 抽。它现在只在 `~/.claude/skills/`，收进 `mmw-v2/skills/`；用户提醒「这个技能只有 claude code 用得上」——正文开头按能力判断「需要 claude-design 的 MCP 工具（`get_claude_design_prompt`、`DesignSync`、`render_preview`），没有就停下说明」，不写宿主名（`AGENTS.md` 约定）。

### D2 `CHECK:` 的命令与 `EXPECT:` 从哪来

- 第一版提议：`to-spec` Testing Decisions 每层加「跑单个用例的命令 + 成功输出」。用户问：「关键是这个测试由谁去跑，还有为什么需要告诉 agent 如何去跑，agent 自己找不到方法吗？参考资料里面是怎样做的。这个 check 的用法不是已经在 [B8] 做出规定了吗」。
- 回答：谁跑——worker 步 8、verifier 步 9，用 B8 的 gate-check（B8 定「怎么跑怎么判」，本条定「命令由谁写、从哪来」）；参考资料里都是出票的人写命令不是做票的人写（unlazy 写账本者派活前写 CHECK；pstack coordinator 在 brief 的 VERIFY 字段写 exact commands），理由是验收命令是标准的一部分，开工前定死；agent 自己找得到，`to-tickets` 第 2 步本来就探索仓库。信息是按项目固定的，不该进每份 spec。
- 第二版提议：不改 `to-spec`，命令放消费仓库 `AGENTS.md` 的 Commands 表；用户接受但追问「TESTING.md 怎么写。看看参考资料是否有」。查证：参考资料没有 TESTING.md 模板（mattpocock 上游只在 `to-spec` Sources 提一句；unlazy 把 test commands 放每次计划的 Contract 段；pstack 探索子代理临时回报；swarm-forge 按语言写死工具清单）；我们自己的 `manage-agents-md/write.md` 规则「Prefer file-scoped test commands」已把 AGENTS.md Commands 表当家。给了 Commands 表例子（`uv run pytest tests/api/test_projects.py::test_duplicate_name -q`、`pnpm vitest run src/library/Library.test.tsx -t "empty state"` 等）。
- 用户追问：「Commands 表会不会变成穷举」「关于 command 表这个东西我觉得你还是要好好思考，其实他和 [D4] 里两个脚本是一样的，思考到底哪几步用它谁用它，就知道它应该放在哪里」「我还是没搞懂 [D2] 你到底打算怎么做」。
- 第三版（最终）：这条命令只被写一次——步 4 `to-tickets` 写 CHECK；之后步 7 worker 跑单测、步 8/9 跑 gate-check，读的都是票上那行。出票时需要的信息 spec Testing Decisions 已给（层、目录、先例、提交前命令），看先例文件就知道框架。所以**不改 `to-spec`、不建 TESTING.md、不给 `AGENTS.md` 加规矩**；`to-tickets` 正文加一句「CHECK 从 Testing Decisions 的层与先例推出；EXPECT 把先例跑一次抄成功那行」。举例：AC「重名返回 409」→ Testing Decisions 说 API 层 `tests/api/`、先例 `projects.create.test.ts`、`pnpm vitest run` → 打开先例见 vitest → `CHECK: pnpm vitest run tests/api/projects.create.test.ts -t "duplicate name returns 409"` → 跑先例见末行 `Tests  3 passed (3)` → `EXPECT: /Tests\s+\d+ passed/`。Commands 表不会穷举：`manage-agents-md` 只写 `--help` 看不出的命令、根文件 150 行上限、一层一行。
- 用户裁决：「[D2] 接受」（第二版时）；第三版是对「怎么做」的澄清，用户未再异议。

### D3 非默认场景的基线怎么产

- 现状：Claude Design 里场景是组件的 `scenario` 属性，靠 Tweaks 面板切，不是网址参数；实验只比了默认场景。
- 读原件：`support.js parseDataProps` 从 `<script data-props>` 读 props；`claude-design-blocks/scripts/mkharness.py` 生成一页 `<dc-import name="<组件>" scenario="{{cur}}">` 由 `<select>` 驱动。
- 结论：visual-parity 为每个场景生成一页只含 `<dc-import name scenario="<场景>">` 的包装页，放临时目录、引用下载回来的组件文件，离线渲染截 `#dc-root`；基线文件不动；场景列表随基线放叶子目录。做工具时验证一次写死 `scenario` 属性能生效。
- 用户：「[D3] 你说的有点复杂，我的理解就是把 claude design 里面的场景切换在本地再转换实现一次是吗。如果是的话听起来可行」→「[D3] 没问题」。

### D4 两个脚本放哪；新技能 `verify-ticket`

- 我先提三条路（A 塞进技能目录 / B `mmw-v2/tools/` + 软链 `~/.agents/tools/` / C 复制进消费仓库），建议 B。用户：「应该放进相应的技能里，技能本身就可以放脚本啊。你先说清楚到底在哪几步哪些 agent 会使用这两样东西，思考有没有必要专门造新技能去使用这两样东西」。
- 用途表：`gate-check.mjs`——步 8 worker、步 9 verifier；visual-parity——步 7 worker 迭代、步 8/9 作为某条 AC 的 CHECK 被 gate-check 调起。步 8 与步 9 流程完全一样（取票 → 跑 → 贴回），只差 `--reverify`，现在要在 `implement` 正文和 verifier 定义文件写两遍。
- 结论：新自有技能 `mmw-v2/skills/verify-ticket/`：`scripts/gate-check/`（vendor 6 文件）+ `scripts/visual-parity.py`；正文一段「`gh issue view` 取 AC 段 → 临时账本 → `gate-check [--reverify]` → 更新后的账本评论到票」；`implement` 步 8 写 `/verify-ticket #n`，verifier 定义文件写 `/verify-ticket #n --reverify`；UI 验收标准的 CHECK 写 `uv run ~/.agents/skills/verify-ticket/scripts/visual-parity.py …`（gate-check 用 `/bin/sh` 跑，`~` 展开；`install.sh` 已把技能软链到 `~/.agents/skills`）。不放 `implement/scripts/`（上游 subtree 拉更新要解冲突；verifier 也用）。
- 用户裁决：「那就先造一个新技能试试看」。

### D5 Claude Design 的两样产出进流程

- 用户贴了在 Claude Design 里的两段问答：①「开发交接包」= 可下载 zip，README（概述；声明 HTML 是设计参考要在自己技术栈重建；高保真声明；逐屏布局、组件位置尺寸、色值、字体、圆角、阴影、hover/active/focus、逐字文案；交互与行为；状态管理；设计 token；资源清单；文件索引）+ 全部 `.dc.html`；②DESIGN.md = 纯文本设计系统，上传 Claude Design「Create new design system」一次性搭出色板、字体、组件、UI kit，之后每个界面自动守系统；放进仓库让 Claude Code 等宿主当上下文。
- 建议：①随基线下载进叶子目录，票 `Read first` 指向它，`to-tickets` 写 AC 精确值与逐字文案从它抄（规则 2「copied from the chosen prototype artifact」）；②精修前用技能表里已有的 `create-design-md` 从消费仓库生成 DESIGN.md，上传建 design system；同一份放进消费仓库、`AGENTS.md` External References 指一行；每项目一次。
- 用户裁决：「都进」。

## 块 E · 派发

### E1 派发前提

- 我第一版列「三样前提」：worktree 由 `herdr worktree create` 建、`gh` 已登录、权限放开；并跑 `--help` 核出参数：claude `--permission-mode {acceptEdits,auto,bypassPermissions,manual,dontAsk,plan}`、`-n`、`--model`；grok `--permission-mode {default,acceptEdits,auto,dontAsk,bypassPermissions,plan}`、`--always-approve`、`-m`、`--reasoning-effort`、`--worktree=<名>`；cursor-agent `--force`/`--yolo`、`--trust`、`--model 'x[effort=high]'`、`-w <名>`、`--worktree-base`；codex `-a never`、`-s`；pi `--name`、`--session-id`。
- 用户纠正：「你没查清楚，cursor 和 grok 应该都可以从新 worktree 启动。gh 登录与否这个为啥要给，肯定是提前在电脑里登录好的呀」；三条裁决「1. 全部放行 2. 可以 3. 表可以单独放，关键是怎么去读它」；随后「我不会去读 docs/agents/models.md，我只会修改优化它里面的 agent 和模型安排」。
- 结论：worktree 由宿主自己开（`cursor-agent -w issue-<n> --worktree-base main`、`grok --worktree=issue-<n>`），Herdr pane 开在仓库根，不用 `herdr worktree create`；权限全部放行（cursor `--force --trust`；grok/claude `--permission-mode bypassPermissions`）；Herdr 名 `issue-<n>`（正则不许数字开头），claude/pi 同时 `-n`，cursor/grok 只有 Herdr 一侧有名；`gh` 一次性登好不算前提；角色表 `docs/agents/models.md` 每行「角色 → 宿主 → 完整启动命令」，读者是主 agent（起 worker 时抄 worker 行）和 `implement`（起 reviewer 会话时抄 reviewer 行），读法是 `AGENTS.md` `## Agent skills` 段加「### Roles … See docs/agents/models.md」（与 issue-tracker 同机制），用户只改表里的安排、不读它。**表的位置与形状后来被 E2 覆盖**（消费仓库里没有 `mmw-v2/`，启动命令与模型是这台机器的安排，不跟项目走）；本条其余部分沿用。
- 补充（写落地 spec 时发现）：Herdr 名在活着的 agent 里必须唯一，同一票的 worker 已占 `issue-<n>`，worker 起的 reviewer 会话用 `issue-<n>-review`；cursor 的模型串是 `cursor-grok-4.6-high`（effort 烧在 slug 里，`cursor-agent models` 无裸 `cursor-grok-4.6`）；grok 要加 `--worktree-ref main`（缺省从当前 HEAD 开，A2 的起点算法要求从 main 开）。
- 角色表数值（昨晚定、今天沿用）：初级 worker cursor `cursor-grok-4.6` effort high；高级 worker grok `grok-4.6` xhigh；reviewer 会话 claude opus；verifier 同宿主不同模型写在 `agents/verifier/agent.json`；编排者 claude opus medium（自动化阶段再用）。**verifier 那一格与「编排者进表」被 E2 覆盖**：四个 subagent 的模型进同一张表，编排者不进表。

### E2 一张表管每一个被派出去的 agent；表随技能走（覆盖 E1 的表位置与形状）

- 触发：用户读 #66 后问「为什么 verifier 不在 `docs/agents/models.md` 里，这张表应该要管新 mmw v2 里所有的 agent，除了 coordinator 因为他是我直接在 cli 里通过选择决定的」。
- 现状的两处毛病：① E1 把 verifier 的模型放在 `mmw-v2/agents/verifier/agent.json`，用户改模型安排要开两处文件，而 `agent.json` 不在他会打开的路径上；② E1 把角色表放消费仓库 `docs/agents/`，可技能是软链装到 `~/.agents/skills` 与 `~/.claude/skills` 的，装出去以后 agent 在项目 X 里跑，读得到的只有项目 X 的 cwd 和顺着软链读到的技能目录——项目 X 里没有 `mmw-v2/`，那份表得有人手抄过去，而启动命令（`cursor-agent -w issue-<n> …`）没有一个字是跟项目走的。
- 我摆的三个选项：① `models.md` 第二张表 + `assemble.py` 读它；② 第二张表只当索引，第三列写「见 `agent.json`」；③ 三列改四列混在一张表。用户选 ①、收四个 agent 全部（`verifier`、`advisor`、`claim-checker`、`ui-evaluator`）；随后指出「表一表二」的切法本身是错的——「这个技能有两个功能：教 agent 怎么调用其他 agent；定义所有 agent 的配置」。
- 用户原话（配置这一半）：「能够通过修改 models.md 去改变整个 mmw v2 的 agent 配置。实现方法就是一个新 reference 用自然语言告诉 agent 修改前要去电脑里确认某个 agent harness 的 agent 文件存放位置以及正确的模型名写法。assemble.py 的作用只是给不同 agent harness 写好 agent 配置文档格式以及一套默认的配置。」「assemble.py && install.sh 是 agent 出场前在 mmw 仓库跑的，后续通过 dispatch 技能是直接修改运行时直接生效，不需要重新安装。」
- 结论：
  - `models.md` 一张表，一行一个 `(agent, 宿主)`，五列「agent | 宿主 | 模型 | 思考强度 | 启动参数」。会话角色（`junior-worker`、`senior-worker`、`reviewer`）各一行，启动参数用 `{model}` / `{effort}` / `{n}` 占位，由 `dispatch.sh` 替换——换模型只改「模型」列。四个 subagent 各按五个宿主一行，启动参数列写 `—`（不经 Herdr）。第五列不写 harness 的程序名：`herdr agent start --kind` 按「宿主」列决定跑哪个程序，`--` 后面只收参数；写进去就是同一件事说两遍，改了宿主忘了改它，表就开始说假话而照常运行。
  - **`orchestrator` 不入表**：编排者就是用户在 CLI 里自己选模型起的那个会话。
  - 表的家是 dispatch 技能目录 `mmw-v2/skills/dispatch/models.md`，跟着 `install.sh` 的软链走；`dispatch.sh` 用 `realpath` 找到自己旁边的它。
  - 配一份 `references/editing-models.md`：改一行的全过程，四节——确认模型名与强度写法（去问 harness 自己，不凭记忆）、确认宿主（`host` 必须是 `herdr agent` 打印的 kind，参数按新 harness 的 `--help` 整行重写）、让改动生效、去哪核对。`SKILL.md` 必须点名这份 reference，加载技能不会自动读它。
  - `assemble.py` 只管格式：知道五个宿主各自的配置文件格式，模型与思考强度按 `(agent 名, 宿主)` 从 `models.md` 的 subagent 行读；`agent.json` 里不留 `model`/`effort`，表里缺行就停下并点名，不回落——留第二处再加一条优先级规则，正是要消灭的那种漂移。
  - **改完生效的路径两半不同**：启动参数非空的三行由 `dispatch.sh` 派发时现读，改完即生效；`—` 的二十行要在宿主软链所指的那个 checkout 里跑一次 `assemble.py`，跑完即生效，不用 `install.sh`（宿主里是软链，指着固定的成品文件名）。`install.sh` 只在加一个全新 agent 时才要跑。
- 落点：`mmw-v2/skills/dispatch/models.md`、`references/editing-models.md`、`mmw-v2/agents/assemble.py` 与四个 `agent.json`（都在 #67）；#66 缩成只做根 `CONTEXT.md`；#60 第 4 节。

## 块 F · 落地

### F1 验证方式与节奏

- 我提「每步做完就用那张真实的票跑到对应的步」。用户：「这个做法是错误的，应该虚构一张结构完整的票快速测试」「并且不能够一次性改动，很容易失控，所以我才让你仔细登记的」。
- 结论：虚构一张结构完整的票（含 Owns、AC 四行、MANUAL、UI 验收标准、Blocked by），放在一个测试用的小仓库里，每改一处就用它快速测那一处；一次只改一处，测过再改下一处。真实的票留到全部改完后跑一遍（`10` §5 第 1 条：跑通才合 main）。

### F2 改动顺序（用户要求一次性规划完整）

- 用户：「你要一次性规划出完整的改动顺序，如何一点点落地，你检查完我检查，再修改，再下一步」。
- 落点：落地 spec，本仓 issue #60（Implementation Decisions 十一节 = 改动顺序，每节带「我检查 / 你检查」）；经 claim-checker 核查 55 条陈述、修 13 条后发布。

## 块 G · 按机制用途复查（2026-08-29）

### G0 原则：每种机制只为一个目的而用

- 用户原话：「你要从 agent 原理上去思考，之所以用技能是因为里面的内容需要被多个 agent 使用或者主 agent 需要完成多项任务，之所以用 agent 配置文档是因为可以自定义模型思考并且在调用 subagent 时自动加载固定的上下文，之所以用 herdr 派发外部 agent 是因为要使用搭载多种模型的 agent，之所以使用 hooks 是因为要强制执行并进行判断，之所以要用脚本是因为固定的操作可以脚本化避免出错跳步同时减少 agent 不必要的思考和 token 消耗，之所以通过文档传递上下文是为了避免漏传、错传，标定事实，同时一份文档可以服务多个流程多个 agent，同时已经记录在文档里的内容绝对不需要再次抄写进提示词里，只需要用路径或者章节指针」；「我从来没有说过不许用 hooks」。
- 结论：设计每一步先按这张表核对用的是不是对的机制。此前各文档写「无 hook」的两条理由（`10` §3.a.1 注入送错会话、§3.a.3 镜像文件）只针对注入型 hook 与本地账本，对不注入、不建文件的 gate 不适用；`10` §6 表「hook 层 … 不做」一行由本块覆盖。
- 落点：记忆「工作流机制选择原则」；`13-scriptable-steps.md`。

### G1 `verify-ticket` 是一个脚本，技能正文只剩调用形

- 现状：#60 第 2 节把三种用法写成「取票 → 临时账本 → gate-check → 算 Outside Owns → 贴评论」的散文步骤，由模型逐步照做。
- 结论：`scripts/verify-ticket.py <n> [--reverify|--lint|--preflight|--closeout]` 一个脚本；`--lint` 加同 spec 票图的环与悬空核对（grok `validate_dag` 复用）；`--preflight` 做开工守卫后认领；`--closeout` 核收尾评论首行、`ABANDON` kind、`Counts:`、`VERDICT` commit == HEAD、工作区与分支，全过才由脚本关票或换标签。不持有状态文件。verifier `body.md` 只补 `VERDICT <完整 commit> <level> …` 一行，level 是它唯一要判的事。
- 用户裁决：「看起来没问题」（对 `13-scriptable-steps.md` 的提议）。
- 落点：#60 第 2、3、5、7、9 节；Testing Decisions 加自写脚本的 `tests/`。

### G2 两个 hook gate：worker 半途不许停、不经校验不许关票

- 事实（2026-08-29 核实，`13-scriptable-steps.md`「五个宿主的 hook 能力」）：Claude Code / Grok Build / Codex 有 `Stop` 硬 gate 与 `PreToolUse` deny；Cursor 的 `stop` 只能 `followup_message` 软顶回（`loop_limit` 5），`beforeShellExecution` 可 deny；pi 用扩展 `tool_call` block、`agent_end` 续一轮。本机 `~/.grok/config.toml` 关了 `[compat.claude]`/`[compat.cursor]` 的 `hooks`，Grok 要单独写 `~/.grok/hooks/`。Herdr 已在五宿主各装一个 `SessionStart` hook，安装方式照抄。
- 结论：`scripts/hook.py <stop|pretool> <host>`，只在 `HERDR_ENV=1` 且分支名匹配 `issue-<n>` 时动作（自定位，主 agent 与 reviewer 会话不命中），读 `gh` 不读文件，`gh` 失败放行。`stop`：票没关也没 `HANDOFF REQUIRED` 就 block；`pretool`：`gh issue close` / 换标签前跑 `--closeout --check-only`，非零 deny。`install.sh` 多装这一层（四份 JSON 合并 + pi 一个 `.ts`），`--check` 核对。
- 落点：#60 第 2 节（hook.py、install.sh 段）、第 9 节第 6 步、Out of Scope「票不动而 agent 已 idle」一句。

### G3 派发是固定操作：`dispatch.sh`（**落点被 G9 取代**）

- 现状：主 agent 每票重复「读 `models.md` 抄行 → `herdr pane split` → `agent start` → 等 idle → `agent prompt`」；worker 起 reviewer 会话是同一串；等评论出现靠模型自己轮询。
- 结论：`scripts/dispatch.sh <n> <role>` 从 `models.md` 三列表按角色读第三列；`dispatch.sh wait <n> <首行前缀> [秒]` 轮询票评论。`models.md` 定为「角色 | 宿主 | 完整启动命令」三列，用户照旧只改表。
- 落点：#60 第 2 节、第 4 节、第 9 节第 3 步。**「放进 `verify-ticket` 技能」这一条被 G9 取代**：`dispatch.sh` 与 `models.md` 独立成 dispatch 技能；本条其余部分（派发是固定操作、`wait` 的调用形、用户只改表）沿用。

### G4 不采的

merge-note 与正文一致性 canary（「关键句」无法机械定义）；二次调用审计（0.3）；对照实验 harness（C1）；跨票记忆（消费端是提示词）。

### G5 vendor 的批准机制去掉

- 现状：`gate-check.mjs` 跑任何一条 `CHECK:` 之前要求这条命令先被批准过一次，批准记录是一堆文件，目录必须属主私有且在仓库外（`verify-ticket.py` 放在 `~/.mmw/verify-ticket-approvals`）。
- 上游为什么有这套：`unlazy/SECURITY.md:3` 写明它的安全边界是「explicit review and approval, not command sandboxing」——那里的账本随着**别人写的仓库**一起到你机器上（`:11` 的 inherited ledger），人读一遍每条 `CHECK:`、`EXPECT:`、`CWD:` 再 `--approve`，记录替他记住这个「是」；记录放在仓库外，仓库才伪造不了自己的批准。
- 我们这里那个「是」没有人给：`--approve` 每次都带。记录也一次都没被复用——批准以账本的绝对路径为键（`gate-check.mjs:367`），而账本每次写进一个新的临时目录，于是 `~/.mmw/verify-ticket-approvals` 攒了 261 个死文件。真正读这些命令的地方在出票那一步：主 agent 写 `CHECK:`、`--lint` 审写法、票给用户看。
- 用户裁决：「我们的 check 跑的不是 issue 里的命令吗，issue 不是 agent 自己写的吗，check 的绝大多数都是测试啊，我没看出有任何必要需要人去审一遍」「你应该精简上游的设计，拿掉整套审核命令的东西，只保留他对我们来说最有参考价值的代码」。
- 结论：`gate-check.mjs` 894 行减到 701 行——`--approve`、`~/.unlazy/approved` 及其属主与 no-follow 校验、逐条记录与它们的锁、`APPROVAL REQUIRED` / `NOT RUN` 那条路全部去掉。判定本身一个字没动：三态、exit 0 ∧ EXPECT 双条件、超时、输出上限、正则 worker、进程树清理、STALE 签名核对。
- 连带：Codex 的沙箱不必为一个仓库外的目录放宽（G7）。
- 落点：`mmw-v2/skills/verify-ticket/scripts/gate-check/gate-check.mjs` 与它的 `UPSTREAM.md`；`verify-ticket.py` 的 `run_checks`；`05-runnable-acceptance-gates.md` §2.6 与 §10；#60 第 2 节。

### G6 一条 `CHECK:` 可以写好几行（**已被 G8 取代**）

- 触发：#69 第一次自跑，9 条标准里 8 条 unmet，报的全是 `/bin/sh: -c: line 0: unexpected EOF while looking for matching `"'`。
- 原因：账本一行一条属性（`gate-check/lib/gates.mjs:46` 的 `ATTR_RE`），上游对 `CHECK:` 底下那些行什么也不做，于是只有第一行进 shell，剩下的一声不响地消失，命令成了一个没闭合的引号。全批 35 条 `CHECK:` 是这么写的，分布在 #62、#64、#66、#68、#70、#71、#72、#73、#74。
- 我先做成解析时报错。用户裁决：「不应该报错而是应该解析识别，如果做不到就改技能，报错算什么东西啊」。
- 结论：**一条 `CHECK:` 底下、到下一条属性或下一条标准之间的行，都是这条命令的一部分。** `CHECK:` 是一条 shell 命令，shell 命令本来就可以是好几行。每条标准另记 `attrEnd`（最后一行属性的下一行），补 `EVIDENCE:` 时插在那里，不插进命令中间。`verify-ticket.py` 的 `criteria_lines` 把续行拼回 CHECK，`count_gates` 找 `EVIDENCE:` 时按下一条标准断句而不是按缩进（续行是顶格的）。
- 那 35 条一条都不用改；不写成出票规则，也不进 `--lint`。
- 落点：`gate-check/lib/gates.mjs`、`gate-check.mjs` 的 `insertOrUpdateEvidence`、`verify-ticket.py` 的 `criteria_lines`、`count_gates` 与 `parse_criteria`；`gate-check/UPSTREAM.md`。
- **这条读法后来被 G8 取代，起因就记在这里。** `parse_criteria` 是 #63 为 `--closeout` 后来新写的，不在上面那张落点清单上，于是仍按缩进读——带多行 `CHECK:` 的标准一律显示为「打了勾但 EVIDENCE 还是 pending」，这样的票关不掉，而且改草稿没用，因为要改的不是草稿。2026-08-30 关 #64 时撞出来（它的 AC6 是一段 heredoc），先用一行止血（`019632c8`）。**第五个读者漏实现了这条看不见的规则，正是 G8 把它换成显式定界符的理由**；落点清单本身不再有效，以 G8 为准。

### G8 多行 `CHECK:` 写成代码块围栏，隐式续行退场（取代 G6）

- 现状：G6 定的读法是「一条 `CHECK:` 底下、到下一条属性或下一条标准之间的非空行都属于它」。这条断句规则是隐式的，**每一个逐条读标准的读者都要各自复刻一遍**，而它无法表述成可查的规则——G6 自己就写了「不写成出票规则，也不进 `--lint`」。
- 代价已经付了两次：G6 那次一次性改了四处；`parse_criteria`（#63 为 `--closeout` 后来新写的）漏了，带多行 `CHECK:` 的标准一律显示「打了勾但 EVIDENCE 还是 pending」，票永远关不掉、改草稿没用、不报错。
- 而且隐式续行**当时就在静默丢数据**：`gates.mjs` 的续行条件要求该行非空，所以多行命令里一个空行就丢掉后面全部；续行里出现 ` ``` ` 会被 `FENCE_OPEN_RE` 当围栏开口吞掉后文；出现 `- [ ] AC1:` 会被 `GATE_RE` 当成新标准。而这个工具的 `CHECK:` 恰恰经常要生成含这两样的 markdown。
- 曾考虑「一行写不下就放进仓库当脚本，`CHECK:` 调它」。不采：`gate-check.mjs` 的 `signature` 只 hash `gate.check` 的文本，`CHECK: bash scripts/x.sh` 之后脚本内容改了签名不变，STALE 核对失效；而且命令搬出票面之后，「出票那一步人读命令」这条依据没了——那正是 G5 砍掉整套批准机制的全部理由。
- 用户裁决：「解析器解析不了就改他妈的解析器呀」——vendor 的 `gate-check` 是我们的，改它不算代价；判据是「以后每一张票、每一个读票的东西长期要付的成本」。咨询过 advisor（读了 `gates.mjs`、`gate-check.mjs`、`verify-ticket.py` 后作答），判围栏最优，并要求配套把无围栏续行改成解析错误，否则隐式规则还在。
- 结论：**一条 `CHECK:` 的命令，一行写得下就照旧写在冒号后面；写不下就紧跟一个代码块围栏，围栏内是命令正文，按围栏自身的缩进剥掉。** 围栏内不扫标准行、属性行、`ABANDON:`——正是原来「代码块一律不当真」守的那件事，一寸未失；只在「围栏紧跟一条活标准的 `CHECK:`」时被当作命令。没有围栏的顶格续行改为解析错误，错误话里指明用围栏。同一条 `CHECK:` 既有值又跟围栏也报错。
- 连带：`verify-ticket.py` 原本三个各自读标准的函数（`criteria_lines`、`count_gates`、`parse_criteria`）合成**一个** `parse_criteria`，另两个成为它的薄封装——三个读者各自判断边界，正是这条规则出事的形状。
- 落点：`gate-check/lib/gates.mjs`、`gate-check/UPSTREAM.md`、`verify-ticket.py`、`verify-ticket/SKILL.md`、`tests/test_fenced_check.py`；#68 的出票规则；存量 30 条多行 `CHECK:`（#68、#70–#74）已包进围栏。#90。

### G7 落地 verifier 时三处宿主细节

- **`agent.json` 顶层键 `sandbox`。** `assemble.py` 把 Cursor 的 `readonly`、Codex 的 `sandbox_mode`、Grok 的 `default_capability_mode` 三处写死成只读，而 verifier 要跑 `CHECK:`。加一个可选键 `sandbox`（`read-only` / `workspace-write`，缺省 `read-only`），verifier 写 `workspace-write`；Claude 与 pi 不看这个键，它们靠各自 `hosts` 里的 `tools` 列表放行。键名与上一次落地的 `94fc6d01` 相同。
- **Grok Build 给子进程带 `CLICOLOR_FORCE=1`**，`gh` 在这个变量下连 `--json` 都输出带 ANSI 转义的 JSON，`json.loads` 读不动。`verify-ticket.py` 九处 `gh` 调用统一走一个去掉这个变量的 `env`。复现不需要 grok：`CLICOLOR_FORCE=1 gh issue view 77 --json comments`。
- **`06-independent-verifier.md` §9 的两条待核事实有答案了**：真派之后读会话记录，Codex 的子代理确实跑 `agent.json` 写的 `gpt-5.6-terra`，Grok Build 的确实跑 `grok-4.5`——两家都按定义文件切模型。另记一条：Codex 的父会话自己是 `workspace-write` 时连子代理都起不来（`failed to initialize in-process app-server client`），要 `danger-full-access`；真实流程里 worker 本来就是权限全放行起的（E1），对得上。
- 落点：`mmw-v2/agents/assemble.py`、`mmw-v2/agents/verifier/agent.json`、`verify-ticket.py` 的 `GH_ENV`；`06-independent-verifier.md` §8.3、§9；#69 的 AC9。

### G9 dispatch 独立成技能（取代 G3 的落点）

- 现状：G3 把 `dispatch.sh` 的落点写成 #60 第 2 节，也就是塞进新技能 `verify-ticket`。当时的理由只是 `verify-ticket` 是唯一带自有脚本的技能，有现成的安装位置——是图省事，不是分工。这与 G0「每种机制只为一个目的而用」冲突：`verify-ticket` 是跑一张票的验收标准并把结果贴回票，dispatch 是派 agent。
- 用户原话：「`dispatch.sh` 为什么要放在 `verify-ticket` 技能里」「这个新技能应该通过被其他技能在合适的步骤里引用去触发，新技能里只需要写清楚如何派发指定的 agent 就可以了」「subagent 调用不需要这个技能教，直接在其他技能相应地方写调用某个 subagent 以及要给 subagent 什么东西就可以了」。
- 结论：新技能 `mmw-v2/skills/dispatch/`（`SKILL.md`、`models.md`、`references/editing-models.md`、`scripts/dispatch.sh`、`tests/test_dispatch.sh`），`skills.txt` 加 `self/dispatch`。它服务的是「一个 agent 起另一个 agent」这一步，由引用方在自己的步骤里触发（主 agent 派 worker；`implement` 收尾第 3 步派 reviewer）。
  - `SKILL.md` 只教两条调用形的参数怎么填：`dispatch.sh <票号> <角色> [起点 commit]` 与 `dispatch.sh wait <票号> "<评论首行正则>" [秒]`，加三档退出码的含义，加一句指向 `references/editing-models.md`。
  - Herdr 那一串固定操作（查票、`tab create`、`pane split`、`agent start`、等 idle、`agent prompt`、`pane rename`、写 `model` token、`agent wait` + 一次 `gh` 确认）全部包在 `dispatch.sh` 里，一条命令走完，调用方只给角色名与票号。编排规则（worker 开 tab / reviewer 同 tab 分屏、Herdr 名、pane 标签、派发词、120 秒 idle 上限）写死在脚本里，不进表——它们由流水线形状决定（H1），不是用户要调的东西。
  - **subagent 的调用不归这个技能教**：由引用方在自己的正文里写「派哪个子代理、给它什么」（`implement` 收尾第 2 步写「派 verifier 子代理，提示词只有 `verify #<n>`」）。dispatch 技能只在 `models.md` 里持有它们的配置。
  - 不采：`caffeinate -dims` 前缀防睡机（#67 Read first 里 swarm-forge `swarmforge.bb` L565-576 的「可顺带加」）；`agent start` 被挡时补一条 `agent rename`（`14` §3）——两条都由用户裁定不加。
- 落点：#67 整张改写；#60 第 2 节删 `dispatch.sh` 段、新增一节写 dispatch 技能、第 9 节第 2–3 步措辞；#73 收尾第 2–3 步。

## 块 H · Herdr 与自动化（2026-08-29 下午）

调查文件：`14-herdr-utilization.md`（Herdr 能力盘点与编排）、`15-monitor-tab-and-wakeup-loop.md`（信息交换、监控 tab、唤醒闭环）、`16-stall-and-loop-risks.md`（会让 agent 停下或转圈的设定）。

### H0 两条新原则（用户裁定，覆盖多处）

- **可见性的读者不在 Herdr 的侧栏。** 用户原话：「其实我通常会去 GitHub 上面查看 issue，更加直观全面，几乎不会使用 gh 命令更不会在 herdr 里查看」「我看你的潜在用法全部是修改 herdr 侧边栏，但是现在侧边栏已经足够拥挤复杂了，我想知道是否开一个 tab 利用终端去监控和汇总工作流信息呢……这个 tab 终端里的内容既可以被 agent 看懂并利用，也可以被人类看懂而不是全是满满的命令和代码」。落点：`14` §2.4、§4.2、§5.1、§5.3、§5.4 全部改为不做（读者只有侧栏）；`15` §4 的监控 tab。
- **约束工作方法以提高质量，而不是轻易判失败或让人接管；同时不许无限循环，收不了的问题要完整及时地记录下来供以后修。** 用户原话：「关键就在于不要过度干预 agent 工作、约束 agent 的工作方法论以提高结果质量而不是轻易判定失败或人类接管。但是又要警惕不能够陷入 agent 之间的无限循环（我明令禁止的反复 review 就是例子），此时应该完整并及时地记录问题供后续修复优化」。落点：`16` 全文；H4。

### H1 Herdr 的编排、命名与状态互知

九项实测见 `14` §1。定下五条，其余提议按 H0 第一条丢弃（`14` §6 表末段列了丢掉的五项）：

1. **一张票一个 tab**。`dispatch.sh <n> worker` 的第一步是 `herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd <仓库根> --label "#<n> <标题前 20 字>" --env MMW_TICKET=<n> --no-focus`，用返回的 `.result.root_pane.pane_id` 直接 `agent start`；worker 在根 pane，收尾时的 reviewer 会话在同一个 tab 分屏，方向按 `herdr pane layout` 的 `area.width` 判（≥160 向右，否则向下）。不为夜里的票另开 workspace。（`14` §2.2–§2.5）
2. **四个命名位各管一件事**：`agent name` = `issue-<n>` / `issue-<n>-review`（CLI 定位句柄，可预测，唤醒方不必查表）；`pane label` = `#<n> worker`（人眼）；`tab label` = 票号加标题（人眼）；token = 机读台账。`herdr agent rename` 让命名不必发生在 `agent start` 那一刻。（`14` §3）
3. **phase token 由 `verify-ticket.py` 写**，取值 `implement|selfcheck|verify|closed|handoff|closeout-rejected`（P6：`stalled` 随 Stop gate 拿掉），连同 `ticket`/`role`/`ac`/`model` 一起，`--ttl-ms 86400000`；`HERDR_ENV` 不为 1 或 `HERDR_PANE_ID` 为空时整段跳过，socket 失败不影响退出码。它让「`agent_status` 是 idle 但 phase 不是 `closed`/`handoff`」= 半路停了，可机器判定。技能正文不改，worker 无感。（`14` §4.1–§4.2）
4. **`dispatch.sh wait` 内部用 `herdr agent wait` 加一次 `gh` 确认**，不再每 30 秒轮询；调用形不变。（`14` §4.3）
5. **`hook.py` 的票号优先取 `$MMW_TICKET`**（由 `tab create --env` 注入，已实测能到达 pane 里的 agent 进程），取不到再按分支名 `issue-<n>` 匹配。（`14` §6）

- 咨询过 advisor（读了 `14`、`09`、`12`、#60 后作答），它判 1、3、4、5 成立，第 2 条砍掉 `--state-label`，专用 workspace 丢弃；用户裁决「advisor 的判定没问题」。

### H2 账本与通知分开；监控开在一个 tab 里

- **账本是票，通知是 Herdr。** 票（GitHub Issue）承接结论：EVIDENCE、VERDICT、收尾评论、sub-issue，永久、跨机器、用户在网页上看。Herdr 的 pane token 与事件推送承接心跳：谁 idle 了、phase 变了，会话内有效。唤醒信号不写进票——它是用户唯一常看的界面，写进去会淹掉真正要读的评论，而且读回来还得轮询。（`15` §1）
- **监控 tab 是一个程序三种形态**：`board.py --once` 打印一屏表格给 agent 读；无参常驻、事件到来时**追加一行**（不重绘、不进终端备用屏，所以 `herdr pane read` 也读得到）给人看；`--watch` 按查表动手。数据源只有 `herdr api snapshot` 的 token 与 `gh issue list`，不持有状态文件。输出里的词全部沿用已有词汇（phase 取值、Herdr 状态词、`ALL MET`/`HANDOFF REQUIRED`、`VERDICT` 五级）。（`15` §4）
- **不能只做全屏 TUI**：备用屏滚出的行不进 Herdr 滚动缓冲（`09` §1.5、§7 实测），agent 读不到。
- **重新 prompt 别人之前的七条前提**见 `15` §3，前五条抄自 `andybarilla/herdr-scuttlebutt` 与 `rcosteira79/herdr-autocontinue` 在真实使用中付出的代价，后两条是 Herdr 自身的拒绝行为（`agent_blocked`、`agent_prompt_stalled`）。
- **本轮不做**：把 board 包成 Herdr 插件（`[[panes]] placement = "tab"`，scuttlebutt 的 manifest 是模板）；夜间编排主循环本身仍在 #60 的 Out of Scope 里。#62、#63、#64、#67 不为迁就某一种唤醒方的形态而改形状，它们只需产出 `phase` token 这一个输入。

### H3 `ABANDON: decision` 之后不停整张票

- 现状：`08-failure-vocabulary.md` §5.3 与 B6 定的是——只要有一条 `ABANDON`（四个 kind 之一），整张票就是 `HANDOFF REQUIRED`，不关票、不关 PR、`ready-for-agent` 换 `ready-for-human`。
- 用户原则（H0 第二条）：任何需要人决策的地方都应该小到可以先记录在 issue 里、等人重新决策后再精确修改。
- 选项：甲——`decision` 改为「在 spec 下开 sub-issue（`--parent <spec> --label needs-triage`）+ 继续做完其余标准」，只在其余标准也没过时才整票 HANDOFF；乙——维持现状。
- **用户裁决：甲。**
- 结论：`ABANDON: AC<n> decision <理由>` 触发开 sub-issue 并继续；`failed` / `blocked` / `impossible` 维持整票 HANDOFF。`decision` 走的通道与 0.1「写码中发现契约装不下 → 继续做，开 sub-issue」是同一条，只是此前没有接上。连带：`failed` 在自动化下先走 H4 的三轮自跑上限，到上限才写 `ABANDON: failed`。
- 落点：`08-failure-vocabulary.md` §5.3 的 kind 表、#60 第 9 节第 5 步与第 6 步、#73；`--closeout` 对「有 ABANDON 就不得 `ALL MET`」的校验要放行 `decision` 这一支。

### H4 会让 agent 停下或转圈的设定

逐条检查见 `16-stall-and-loop-risks.md`，编号 S1–S11。已定的九条：

- **S1**：`--closeout` 的「最后一条 `VERDICT` 的 commit == HEAD」与 B2 结论末句「`VERDICT` 行照实绑 verifier 验过的那个 commit」直接矛盾，且会让任何一张 code-review 提出票内发现的票**永远关不掉**。改为 `git merge-base --is-ancestor <VERDICT commit> HEAD`，收尾评论加 `Post-verdict:` 行列出 VERDICT 之后的 commit 与来源。
- **S4**：verifier 前后两次 `git status --porcelain`（B4）与 `--closeout` 的同一项，改成只查已跟踪文件（`--untracked-files=no`）——否则 `visual-parity.py --out` 的截图目录、`.pytest_cache` 会让它必然报「动了东西」。
- **S5**：`--closeout` 的「diff 非空」改为警告，容纳「不需要改代码」的票。
- **S6**：`--preflight` 的 assignee 条件改成「为空**或就是我**」，让重派同一张票是幂等的。
- **S7**：`--preflight` 失败时由脚本自己在票上评论 `NOT_READY: <原因>` 再让 worker 停——否则票上没有任何痕迹，早上看不出派过。
- **S8**：`blockedBy` 全 CLOSED 由 `dispatch.sh` 在**派发前**查，不满足就不派。
- **S9**：`dispatch.sh wait` 超时后在票上评论说明 code-review 没能完成，跳过这一轮继续收尾——一个挂掉的 reviewer 不该让整张票交给人。
- **S10**：`visual-parity.py` 负控制失败时退出码与 CHECK 失败一致，首行说明是负控制失败（要修的是工具或环境，不是实现）。
- **S11**：#60 第 9 节第 1 步「没过的修，再跑，直到全过或确认修不了」是整条流水线上**唯一没有上限**的循环。定为同一条 AC 连续三轮仍未过就停手，写 `ABANDON: AC<n> failed <三次各做了什么>`，继续处理其余标准。

不动的防转圈设定（`16` §5）：code-review 一轮不复审、verifier 一次、`verifier-failed`/`verifier-blocked` 不触发 HANDOFF、两个 hook gate、gate-check 的双条件。

### H5 verifier 仍然只派一次（S2 不采）

- 我提的选项：允许 verifier 在 code-review 引出代码修改时再派一次（上限二次），好处是 `VERDICT` 绑在最终 commit 上。
- 用户反问：「S2 为啥非要再派一次 verifier，派他去干什么」。
- 回答与结论：说不出它第二次要做的事。verifier 的工作是在最终 commit 上重跑每条 `CHECK:` 并判一个 `level`（B4）；code-review 之后 worker 改完，#60 第 9 节第 3 步已定「修完再 `verify-ticket.py <n>`」——同一套 CHECK、同一个 `gate-check.mjs`、同一个双条件判定，EVIDENCE 由脚本写，worker 伪造不了。第二次的命令、环境（同一个 worktree）都一样，`level` 大概率不变，增量只剩「换一个没有写码记忆的上下文」，而它防的「自评自勾」风险已被脚本挡住。这正是 `06-independent-verifier.md` §5.2 引 pstack 的「重跑一条命令的 verifier 是仪式」；B3 否掉的是给票分类，不是这个判断。
- **结论：不采。verifier 仍然只派一次。** 剩余风险（code-review 之后的改动没有独立确认）由 S1 的两样东西承接：`--closeout` 核 `VERDICT` 的 commit 是 HEAD 的祖先，收尾评论的 `Post-verdict:` 行列出之后的每个 commit 与来源，早上一眼看得到「验的是 A，之后因 code-review 改了 B」。
- 落点：`16-stall-and-loop-risks.md` §1.1 与 S2；B2、B5 不变。

### H6（S3）带 `MANUAL:` 的票按 decision 同样处理（**被 I2 取代**）

- 现状：manual gate 算 met 的条件是「勾了且 `EVIDENCE:` 非 `pending`」（`08-failure-vocabulary.md` §2.1 标准层三态表，第 19 行），而 `05-runnable-acceptance-gates.md` §8.2 第 4 条定「worker 不代填、不代勾」，verifier 对 MANUAL 条目「标 manual, not run」（#60 第 5 节）。于是任何带一条 `MANUAL:` 的票夜里必然有一条 unmet、必然 `HANDOFF REQUIRED`，首行同时表示「出事了」和「一切正常只等你看一眼」。
- 选项：甲——每条 MANUAL 项开成 spec 下的 sub-issue，其余标准全过就 `ALL MET` 关票；乙——维持整票 HANDOFF，首行计数把人工项单列；丙——出票禁止 MANUAL（与 #60 US3 冲突）。
- **用户裁决：甲。**
- 结论：worker 收尾时把每条未填 EVIDENCE 的 `MANUAL:` 标准开成 sub-issue（`--parent <spec> --label ready-for-human`，正文抄 `MANUAL:` 行原文与相关材料），列进收尾评论的 `Sub-issues opened:`；这些标准不计入 unmet，其余标准全过即 `ALL MET` 关票。`Counts:` 增加一个 `manual` 数，形如 `Counts: 5 met, 0 unmet, 0 abandoned, 1 manual of 6`。与 H3 是同一条逻辑：需要人的那一点小到能单独记成一张 issue，票本身不停。
- 落点：`08-failure-vocabulary.md` §5.3 的计数格式、#60 第 9 节第 5–6 步、#63 的 `--closeout` 校验、#68（`to-tickets` 出票时 MANUAL 行的写法不变）、#73。

### H7 `Owns` 的粒度：同一目录内多票分工时写到文件级

- 触发：把块 H 与 S1–S11 同步进 #61–#75 之后，用 `Blocked by` 边算传递闭包、再两两比 `Owns`，发现四对「同一 frontier 上 Owns 重叠却没有阻塞边」——#63、#64、#65、#67 四张票都在新建的 `mmw-v2/skills/verify-ticket/` 里做不同文件（`verify-ticket.py` 的子命令、`hook.py`、`visual-parity.py`、`dispatch.sh`），按「目录级 glob」写就是四份 `mmw-v2/skills/verify-ticket/**`，两两重叠；`tests/**` 同理；`mmw-v2/skills.txt` 被 #62 与 #74 同时声明，`mmw-v2/install.sh` 被 #64 与 #69 同时声明。
- A2 与 #60 第 3 节定的是「仓库相对的**目录** glob」，`04-owns-write-boundary.md` §7.1 的原意是「逼出票人想清楚动哪些目录」。在一张 spec 把一个新目录拆给四张票做的场合，目录级粒度不够：要么给本来能并行的票加上假的阻塞边，要么放任重叠。
- 结论：**`Owns` 的粒度跟着实际分工走**——多张票分工同一个目录时写到文件级（`scripts/hook.py`、`tests/test_hook.py`），一张票独占一个目录时仍写目录 glob（`mmw-v2/agents/verifier/**`、`mmw-v2/upstream/skills/engineering/implement/**`）。判据不是「目录还是文件」，而是「同一 frontier 上两票的 `Owns` 不得相交」——这条是 A2 与 #60 第 3 节本来就有的，粒度只是满足它的手段。共用的单个文件（`skills.txt`、`install.sh`）无法再切，只能加阻塞边。
- 已按此改：#63、#64 从整目录收窄到具体文件；#65、#67 的 `tests/**` 收窄到各自的测试文件；#65 加 `Blocked by #63`、#67 加 `#65`、#64 加 `#69`、#74 加 `#62`、#75 补 `#68`。改完重算票图：同 frontier 且 Owns 重叠的票对 0 个、无环、无悬空引用、启动层级六层。
- 落点：#68（`to-tickets` 的 `## Owns` 规则加这一句）、#60 第 3 节同一处；`--lint` 的票图核对（#63）已经会查环与悬空，重叠仍靠出票时人眼比对（A2 原样）。

### H8 「你检查」的制品必须在 GitHub 网页上读得到

- 触发：用户看到蓝图页步 13 还挂着五条 `gh issue list` 命令，问「我几乎不会去用，那它们还有用吗」。按 H0 第一条盘点，发现只做了减法（删掉以 herdr 侧栏为读者的五处提议），没做加法——面向用户的入口仍然假设他会敲命令、会翻 Herdr pane 与会话记录。
- 逐条查出来的：#60 的 User Story 15 主语写的就是「用户」而手段是五条命令；蓝图页步 13 与目录卡片；十五张票里九处 `MANUAL: 用户 …`（看五个宿主的会话记录、看三次启动的终端输出、看 Herdr 的 pane 与 `herdr agent list`、跑五条查询、看会话记录）。
- 结论：**凡是「你检查」或 `MANUAL: 用户 …`，制品都必须是 GitHub 网页上打得开的东西**——票正文、票评论、spec issue 的 sub-issue 面板、票页面上的 Blocked by 区块。跑命令、开 Herdr、翻会话记录是我（主 agent）的事，做完把结果抄成一条票评论；用户读那条评论。
- 早上的入口因此改成：**打开 spec issue 那一页**（原生 sub-issue 面板给出每张票的开关状态与完成度；worker 夜里用 `--parent <spec>` 开的 sub-issue 也在同一面板里；票页面的原生 Blocked by 给出还卡在谁身上）加**两个书签链接**（`issues?q=is:issue+state:open+label:ready-for-human` 要人处理的、加 `assignee:@me` 的 `ready-for-agent` 是认领了却没收尾的）。2026-08-29 实测：#60 的 `sub_issues_summary` 为 15 张、完成 0；#63 的 `issue_dependencies_summary` 为 blocked_by 1、blocking 3，`parent` 指向 #60——三样都是 GitHub 原生字段，页面直接显示。
- 那五条 `gh issue list` 查询不作废，**读者从人换成程序**：写进 `15-monitor-tab-and-wakeup-loop.md` §4.2 的数据源一节，`board.py` 与将来的唤醒闭环跑它们。这是 G0 的应用：同一批查询，读者是人就该是链接，读者是程序就该在脚本里。
- 落点：#60 的 US15 与第 9 节「我检查」；蓝图页步 13 与目录卡片、落地顺序表第 9 节；`15` §4.2；#64、#66、#67、#71、#72、#73、#75 共九处 `MANUAL: 用户 …`；#75 的 AC6 标准正文与它的 `MANUAL:` 行同写网页入口（spec 页的 sub-issue 面板加两个书签链接）。

## 块 I · 标签工作流与失败词汇收敛（2026-08-30）

起因：用户翻十七张票，发现 121 条 `CHECK:` 之外还有 33 条 `MANUAL:`，占两成，其中 15 条点名「主 agent」——而主 agent 是 agent。追下去发现根子不在这 33 条：**落地计划这套词汇从来没有和现役 mmw-v2 已有的能力接过轨**。triage 技能的五个状态服务的是从外面来的东西，落地流水线自己造了 `MANUAL:` 和 `ready-for-human` 两条通往人的路，中间没人对齐过。

调查取证 2026-08-30：仓库全文检索每个标签的写入者与读取者，加 `gh issue list` 计数。查出七处断裂，逐条见 https://claude.ai/code/artifact/e83b2342-8de8-40ad-b128-6da798b2328a 。

### I1 标签只表达「在哪个队列」，不新增、删两个

- 现状：20 个标签。`ready-for-agent` 52 张里只有 12 张还开着（关票不摘）；spec 和 ticket 共用它，于是 agent 队列里躺着一张 spec（#60），而 `--preflight` 的四项检查 spec 全都满足、拦不住；`worker:junior` / `worker:senior` 没有任何技能读写，而 0.4 明写「不打定级标签」，仍有两张票挂着。
- 用户原话（P4，本轮复用）：「尽可能不要再增加标签了……甚至需要再清理一次留下真正合法的标签」。
- 结论：一个新标签都不加，删掉 `worker:junior` / `worker:senior`（#56、#57 上的挂载一并摘）。每个标签只表达一件事：`ready-for-agent` = 在 agent 队列里（等派或正在做，由 assignee 区分），两条出口都摘掉它；`ready-for-human` = 在你的队列里，且票上写明为什么不能委派；`needs-triage` = 还没有人判过；`needs-info` 与 `wontfix` 只服务外来件。**spec 不打状态标签**——它是容器不是待办。category（`bug` / `enhancement`）只属于外来件，本仓规划出来的票不带。
- 落点：`verify-ticket.py` 的 `close_ticket()`；`to-spec`（merge-note）；`docs/agents/triage-labels.md`；仓库标签设置；#60 的 US16。

### I2 `MANUAL:` 退场，按「这条标准的读者是谁」分三条出路（取代 H6）

- 现状：`MANUAL:` 是我们在 vendor 来的 `gate-check` 上自造的第五个属性（上游 `gates.mjs:46` 只认 `CHECK|EXPECT|EVIDENCE|CWD`），上游不认识它，于是它静默地不被计数——一条没人跑的标准。A5 已经把判据定对了（问读者是谁），但写法留了 `MANUAL: 主 agent …` 这条口子，于是 15 条本该由 agent 自己判的标准挂在了「等人」的形态上；H6 又让它们各开一张 `ready-for-human` 的 sub-issue，每晚往用户早上的清单里塞纸。
- 结论：拿掉 `MANUAL:` 这个属性。写标准时按 A5 的判据分三条出路——读者是 agent 且写得出命令 → `CHECK:`/`EXPECT:`；读者是 agent 但写不出命令 → 仍是这张票的一条标准，不写 `CHECK:`，由做票的 agent 自己判、自己勾、`EVIDENCE:` 写读了什么与结论（`--lint` 报一条 warn 提醒再想一次）；**读者确实是人 → 不留在这张票上，出票时单开一张 `ready-for-human` 的票**，用阻塞边挂在产出被判之物的那张票后面，正文写明为什么不能委派（判断、只有人有的访问权、设计决定、手工测试——沿用 triage 技能对 `ready-for-human` 的定义）。判断从收尾挪到出票，`--lint` 看得见。
- 连带：`Counts:` 去掉 `manual` 一格，回到 `<k> met, <m> unmet, <n> abandoned of <total>`；`--closeout` 不再数 sub-issue；verifier 的「manual, not run」分支去掉。
- 落点：`verify-ticket.py` 六处、`agents/verifier/body.md`、`to-tickets`（merge-note）、#60 第 3 与第 9 节、#68、#73；现存 33 条按此重新分类（13 条留在票上由 agent 自判，6 条开成 #78、#91–#95，其余在已关的票上不追改）。

### I3 `HANDOFF REQUIRED` 交回 `needs-triage`（覆盖 B6 的落点）

- 现状：B6 定的是 `ready-for-human`。但 `ready-for-human` 有三个写入者、**零个自动读取者**——triage 技能只往里放，从不取出；它唯一的读者是用户打开书签的那一刻。而 triage 对 `ready-for-human` 的定义是「需要人来**实现**」，那是判完之后的结论，不该由一个卡住的 worker 直接下。
- 用户原话：「所有 agent 经过工作流处理不了的事情，都应该直接打上 needs-triage 事后再去判断」。
- 结论：`--closeout` 的 HANDOFF 分支改成 `--remove-label ready-for-agent --add-label needs-triage`。语义更准（worker 卡住的那一刻还没有人判定过它要人做、要补信息还是换个 agent），而且这是**唯一一道有技能主动去取的队列**——triage 整台机器就是为它写的：读全票、复现、给建议、落到四个出口之一。早上两条查询因此变成 `is:open label:needs-triage`（夜里倒下的，可以先让 agent 跑一遍 `/triage`）与 `is:open label:ready-for-human`（确实只有你做得了的）。
- 计划自己此前不一致：H3 让 `decision` 的 sub-issue 落 `needs-triage`，H6 让 `MANUAL` 的 sub-issue 落 `ready-for-human`——同一件事两个落点。本条统一。
- 落点：`verify-ticket.py` 的 `hand_back_for_triage()`、`hook.py` 认的命令、#60 第 2 与第 9 节、蓝图页图 3b 与图 4 与第 5 节。

### I4 `ABANDON` 的 kind 四种收成三种

- 现状：四个 kind 里机器只分得出 `decision`（不挡关票），`failed` / `blocked` / `impossible` 一视同仁。一个词要留下，得有人据它做不同的事。
- 结论：三个——`decision`（要人拍一句话，开 sub-issue 后继续，不挡 `ALL MET`）、`failed`（跑了没过，`--closeout` 要求票上数得出三条该标准未过的 `self-run` 评论）、`stuck`（跑不起来或任务内做不到，不看轮次——它第一轮就该允许放弃，理由须含试过的路）。`blocked` 与 `impossible` 并成 `stuck`：三轮上限只对「跑了没过」有意义，逼另外两种凑三轮是浪费。
- 落点：`verify-ticket.py` 的 `ABANDON_KINDS` / `HANDOFF_KINDS`、`08-failure-vocabulary.md` §5.3 的 kind 表、#60 第 2 与第 9 节、#73、蓝图页图 4 与词表。

### I5 自跑三轮上限的实现：轮次由票自己数

- 现状：S11（H4）定了「同一条 AC 连续三轮自跑仍未过就写 `ABANDON`」，但没写这个数从哪来；而 G1 定了 `verify-ticket.py` 不持有状态文件。
- 结论：数票上的评论。每次自跑都留一条首行 `self-run` 的评论，里面是那一轮的账本，所以「AC3 连续几轮没过」就是数前面有几条这样的评论——脚本本来就把全部评论取下来了。第三轮那条标准的行改成 `ROUND LIMIT`，点名该写 `ABANDON: AC<n> failed`；真正的门在 `--closeout`：`failed` 只有数得出三条才被接受。**上限不是「不许再跑」**——第四轮照跑，修好了照样判过；它管的是什么时候允许放弃、什么时候必须放弃。
- 落点：`verify-ticket.py` 的自跑与 `--closeout`、#60 第 9 节、#73、蓝图页 S8。

### I6 「不过半」取消（取消 A1 的第三条）

- 触发：落地 #68 时发现它的 AC3 还要求技能正文里写出「不过半」，而 #68 的 What to build、#60 第 3 节、蓝图页 §2 三处都已不提它——一条只活在验收标准里、正文没有对应物的规则。
- 现状：「不过半」的对象是 `MANUAL:` 标准（A1 第三条、`05-runnable-acceptance-gates.md` §3.1 的 manual 比例行、§8.2 的 Read back 自检行）。I2 把 `MANUAL:` 整个属性拿掉之后，票上不再有「人工项」这一类：读者是人的标准已经在出票时搬到另一张 `ready-for-human` 的票上，留在票上的都是 agent 判得了的。
- 选项：① 取消；② 保留，把对象换成「不带 `CHECK:` 的标准」，写成一条比例规则进技能正文。
- 用户裁决：「删掉，改 AC3」。
- 结论：取消。技能正文不出现任何比例规则。这类标准的把关改由 `--lint` 的 `manual-gate` 逐条 WARN 承担（A4 定的 ERROR 清零、WARN 逐条看过），一条一条问「能不能写成命令」，比一个总数上限更贴近它要防的事。
- 落点：#68 的 AC3（已改：断言三条出路都在，不再断言比例）；本条。`05-runnable-acceptance-gates.md` §3.1 与 §8.2 是调查记录，原文保留。
