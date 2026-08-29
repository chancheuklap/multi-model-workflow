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
| `CHECK:`/`EXPECT:`/`EVIDENCE:` | 加；写不出命令的标 `MANUAL:`，不过半 | 沿用；A1 定编号与写法；B8 定用 gate-check 跑 |
| verifier 次数 | 只审一次。worker 自跑 → verifier 一次 → 没过的 worker 修并自跑填证据 → 关票；不复审 | 沿用；B2 定它在 code-review 之前 |
| ponytail | 收：grep 每个调用方修共用处；写 helper 前先在仓库与 Read first 的 prototype 找现成；加文件/依赖/配置前说出已有的为何不够；安全与「票里明确要求的东西」不许简化；收尾 `skipped: [X], add when [Y]`。不收：原生控件替代自绘、先交懒版本再问、`demo()` 自检、`ponytail:` 注释、交互模式段。措辞写成动作 + 票字段；「逐字复制」改为保留骨架只换对象；用第一张真实的票跑一遍验证 | 沿用；C1 定不做对照实验 |
| UI 验收 | 两档自动判定：ARIA 树（去 Claude Design 运行时包裹）diff 必须为零；同场景同窗口截图差异像素 ≤ 3%（默认，Testing Decisions 可改）。没过即 `failed`，worker 修；不产生 `decision`；三张图贴票供人参考。不用 `accepted-diffs.json` | 沿用；阈值**被 0.3 改为 1%** |
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

## 块 A · 票的形态

### A1 验收标准的编号与人工项的写法

- 现状：`to-tickets/SKILL.md` `<issue-template>` 的验收标准是 `- [ ] Criterion 1` 两行打勾清单，无编号；worker 做完自由文本写证据、自己打勾。
- 已定（昨晚）：每条标准出票时带 `CHECK:`（能跑的命令）、`EXPECT:`（只在成功时打印的那句）、`EVIDENCE:`（做完填）；写不出命令的标人工；人工项不过半。
- 待定细节与选项：① 编号——unlazy 要求显式 id（行号不稳定），`05` §8.1 用 `AC<n>`；② 人工项——unlazy 是「CHECK/EXPECT 都不写」靠脚本识别，我们无脚本，`05` §8.1 自造 `MANUAL: <谁> <看哪个制品>` 一行；③「不过半」是硬规则还是提醒。
- 建议：`AC<n>` 出票时编、不重排；明写 `MANUAL:` 行；过半为出票硬规则，回 `/to-spec` 补测试层（夜里跑的票人工项 agent 跑不了，过半的票出了也白出）。
- 用户裁决：「都可以」。
- 结论：三条全采。
- 落点：`to-tickets` 模板与 Read back。

### A2 `Outside Owns:` 的 diff 起点；Owns 的两档规则

- 现状：昨晚定票加 `## Owns`（允许改的目录 glob）；收尾跑 `git diff --name-only <起点>..HEAD -- . ':(glob,exclude)<每条 glob>'` 列出范围外改动，非空则收尾评论逐条说明（`04` §3、§7.4）。
- 待定：起点取 A `git merge-base main HEAD` 自动算，还是 B 开工时记进票。
- 用户先质疑范围本身：「为什么要限定票允许改的范围，不会导致中途额外发现的问题的堆积和代码质量的下降吗？既然参考了 unlazy 的做法，为什么不思考是否使用它的脚本呢？」
- 回答要点：范围不是「一律不许碰」，是两档——为过本票 AC 不得不改的范围外文件照改并在收尾评论 `Outside Owns:` 说明；与 AC 无关的顺手改动不改、开 sub-issue。判据：不改它本票哪条 AC 过不了。目的是让票外改动可见（上次尸检里工人「自己拿了六个主意」用户看不懂）。堆积会堆在 sub-issue 里早上分诊；质量由 tdd、code-review、verifier 管，范围不拦第一档。unlazy 的 `OWNS` 脚本只做并发加锁、从不检查实际改了哪里（`04` §2.4），用不上；它的 `gate-check.mjs` 跑验收标准值得考虑——留到 B8 讨论。
- 用户裁决：「A」。
- 结论：起点 `git merge-base main HEAD`，不记进票（每票一个 worktree、按阻塞关系串行开工，分支都从 main 开）；两档规则确认。
- 落点：`implement` 收尾段。

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

### B6 `decision` 类 HANDOFF 的标签

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
- 先读原件再实测（P3）。实测（副本放 scratchpad；`05` §10）：① 接受任意路径的账本文件，不要求 `.unlazy/` 或 `GATES.md`——账本可每次从 `gh issue view` 的 AC 段派生到临时文件，跑完贴回票评论，没有第二份要维护的文件（上次「两处漂移」不再存在）；② 我们的票格式原样能解析：`AC1:` 编号、缩进 CHECK/EXPECT/EVIDENCE、`MANUAL:` 行静默当人工项、其他标题忽略，报 `4 gates`；③ 双条件正确：`echo ok; exit 3` 判 FAIL；④ `--reverify` 把已过的也重跑，汇总 `previously met reverified`；⑤ 代价：Node ≥ 16、审批目录须 0700 且在仓库外、临时账本每次都要 `--approve`、6 个文件约 2000 行（MIT）、默认超时 120 秒。
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
- 结论：新自有技能 `mmw-v2/skills/verify-ticket/`：`scripts/gate-check/`（vendor 6 文件）+ `scripts/visual-parity.py`；正文一段「`gh issue view` 取 AC 段 → 临时账本 → `gate-check --approve [--reverify]` → 更新后的账本评论到票」；`implement` 步 8 写 `/verify-ticket #n`，verifier 定义文件写 `/verify-ticket #n --reverify`；UI 验收标准的 CHECK 写 `uv run ~/.agents/skills/verify-ticket/scripts/visual-parity.py …`（gate-check 用 `/bin/sh` 跑，`~` 展开；`install.sh` 已把技能软链到 `~/.agents/skills`）。不放 `implement/scripts/`（上游 subtree 拉更新要解冲突；verifier 也用）。
- 用户裁决：「那就先造一个新技能试试看」。

### D5 Claude Design 的两样产出进流程

- 用户贴了在 Claude Design 里的两段问答：①「开发交接包」= 可下载 zip，README（概述；声明 HTML 是设计参考要在自己技术栈重建；高保真声明；逐屏布局、组件位置尺寸、色值、字体、圆角、阴影、hover/active/focus、逐字文案；交互与行为；状态管理；设计 token；资源清单；文件索引）+ 全部 `.dc.html`；②DESIGN.md = 纯文本设计系统，上传 Claude Design「Create new design system」一次性搭出色板、字体、组件、UI kit，之后每个界面自动守系统；放进仓库让 Claude Code 等宿主当上下文。
- 建议：①随基线下载进叶子目录，票 `Read first` 指向它，`to-tickets` 写 AC 精确值与逐字文案从它抄（规则 2「copied from the chosen prototype artifact」）；②精修前用技能表里已有的 `create-design-md` 从消费仓库生成 DESIGN.md，上传建 design system；同一份放进消费仓库、`AGENTS.md` External References 指一行；每项目一次。
- 用户裁决：「都进」。

## 块 E · 派发

### E1 派发前提

- 我第一版列「三样前提」：worktree 由 `herdr worktree create` 建、`gh` 已登录、权限放开；并跑 `--help` 核出参数：claude `--permission-mode {acceptEdits,auto,bypassPermissions,manual,dontAsk,plan}`、`-n`、`--model`；grok `--permission-mode {default,acceptEdits,auto,dontAsk,bypassPermissions,plan}`、`--always-approve`、`-m`、`--reasoning-effort`、`--worktree=<名>`；cursor-agent `--force`/`--yolo`、`--trust`、`--model 'x[effort=high]'`、`-w <名>`、`--worktree-base`；codex `-a never`、`-s`；pi `--name`、`--session-id`。
- 用户纠正：「你没查清楚，cursor 和 grok 应该都可以从新 worktree 启动。gh 登录与否这个为啥要给，肯定是提前在电脑里登录好的呀」；三条裁决「1. 全部放行 2. 可以 3. 表可以单独放，关键是怎么去读它」；随后「我不会去读 docs/agents/models.md，我只会修改优化它里面的 agent 和模型安排」。
- 结论：worktree 由宿主自己开（`cursor-agent -w issue-<n> --worktree-base main`、`grok --worktree=issue-<n>`），Herdr pane 开在仓库根，不用 `herdr worktree create`；权限全部放行（cursor `--force --trust`；grok/claude `--permission-mode bypassPermissions`）；Herdr 名 `issue-<n>`（正则不许数字开头），claude/pi 同时 `-n`，cursor/grok 只有 Herdr 一侧有名；`gh` 一次性登好不算前提；角色表 `docs/agents/models.md` 每行「角色 → 宿主 → 完整启动命令」，读者是主 agent（起 worker 时抄 worker 行）和 `implement`（起 reviewer 会话时抄 reviewer 行），读法是 `AGENTS.md` `## Agent skills` 段加「### Roles … See docs/agents/models.md」（与 issue-tracker 同机制），用户只改表里的安排、不读它。
- 补充（写落地 spec 时发现）：Herdr 名在活着的 agent 里必须唯一，同一票的 worker 已占 `issue-<n>`，worker 起的 reviewer 会话用 `issue-<n>-review`；cursor 的模型串是 `cursor-grok-4.6-high`（effort 烧在 slug 里，`cursor-agent models` 无裸 `cursor-grok-4.6`）；grok 要加 `--worktree-ref main`（缺省从当前 HEAD 开，A2 的起点算法要求从 main 开）。
- 角色表数值（昨晚定、今天沿用）：初级 worker cursor `cursor-grok-4.6` effort high；高级 worker grok `grok-4.6` xhigh；reviewer 会话 claude opus；verifier 同宿主不同模型写在 `agents/verifier/agent.json`；编排者 claude opus medium（自动化阶段再用）。

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

### G3 派发是固定操作：`dispatch.sh`

- 现状：主 agent 每票重复「读 `models.md` 抄行 → `herdr pane split` → `agent start` → 等 idle → `agent prompt`」；worker 起 reviewer 会话是同一串；等评论出现靠模型自己轮询。
- 结论：`scripts/dispatch.sh <n> <role>` 从 `models.md` 三列表按角色读第三列；`dispatch.sh wait <n> <首行前缀> [秒]` 轮询票评论。`models.md` 定为「角色 | 宿主 | 完整启动命令」三列，用户照旧只改表。
- 落点：#60 第 2 节、第 4 节、第 9 节第 3 步。

### G4 不采的

merge-note 与正文一致性 canary（「关键句」无法机械定义）；二次调用审计（0.3）；对照实验 harness（C1）；跨票记忆（消费端是提示词）。

## 块 H · Herdr 与自动化（2026-08-29 下午）

调查文件：`14-herdr-utilization.md`（Herdr 能力盘点与编排）、`15-monitor-tab-and-wakeup-loop.md`（信息交换、监控 tab、唤醒闭环）、`16-stall-and-loop-risks.md`（会让 agent 停下或转圈的设定）。

### H0 两条新原则（用户裁定，覆盖多处）

- **可见性的读者不在 Herdr 的侧栏。** 用户原话：「其实我通常会去 GitHub 上面查看 issue，更加直观全面，几乎不会使用 gh 命令更不会在 herdr 里查看」「我看你的潜在用法全部是修改 herdr 侧边栏，但是现在侧边栏已经足够拥挤复杂了，我想知道是否开一个 tab 利用终端去监控和汇总工作流信息呢……这个 tab 终端里的内容既可以被 agent 看懂并利用，也可以被人类看懂而不是全是满满的命令和代码」。落点：`14` §2.4、§4.2、§5.1、§5.3、§5.4 全部改为不做（读者只有侧栏）；`15` §4 的监控 tab。
- **约束工作方法以提高质量，而不是轻易判失败或让人接管；同时不许无限循环，收不了的问题要完整及时地记录下来供以后修。** 用户原话：「关键就在于不要过度干预 agent 工作、约束 agent 的工作方法论以提高结果质量而不是轻易判定失败或人类接管。但是又要警惕不能够陷入 agent 之间的无限循环（我明令禁止的反复 review 就是例子），此时应该完整并及时地记录问题供后续修复优化」。落点：`16` 全文；H4。

### H1 Herdr 的编排、命名与状态互知

九项实测见 `14` §1。定下五条，其余提议按 H0 第一条丢弃（`14` §6 表末段列了丢掉的五项）：

1. **一张票一个 tab**。`dispatch.sh <n> worker` 的第一步是 `herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd <仓库根> --label "#<n> <标题前 20 字>" --env MMW_TICKET=<n> --no-focus`，用返回的 `.result.root_pane.pane_id` 直接 `agent start`；worker 在根 pane，收尾时的 reviewer 会话在同一个 tab 分屏，方向按 `herdr pane layout` 的 `area.width` 判（≥160 向右，否则向下）。不为夜里的票另开 workspace。（`14` §2.2–§2.5）
2. **四个命名位各管一件事**：`agent name` = `issue-<n>` / `issue-<n>-review`（CLI 定位句柄，可预测，唤醒方不必查表）；`pane label` = `#<n> worker`（人眼）；`tab label` = 票号加标题（人眼）；token = 机读台账。`herdr agent rename` 让命名不必发生在 `agent start` 那一刻。（`14` §3）
3. **phase token 由 `verify-ticket.py` 写**，取值 `implement|selfcheck|verify|closed|handoff|stalled`，连同 `ticket`/`role`/`ac`/`model` 一起，`--ttl-ms 86400000`；`HERDR_ENV` 不为 1 或 `HERDR_PANE_ID` 为空时整段跳过，socket 失败不影响退出码。它让「`agent_status` 是 idle 但 phase 不是 `closed`/`handoff`」= 半路停了，可机器判定。技能正文不改，worker 无感。（`14` §4.1–§4.2）
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
- **S4**：verifier 前后两次 `git status --porcelain`（B4）与 `--closeout` 的同一项，改成只查已跟踪文件（`--untracked-files=no`）——否则 `visual-parity.py --out` 的证据页、`.pytest_cache` 会让它必然报「动了东西」。
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

### H6（S3）带 `MANUAL:` 的票按 decision 同样处理

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
- 落点：#60 的 US15 与第 9 节「我检查」；蓝图页步 13 与目录卡片、落地顺序表第 9 节；`15` §4.2；#64、#66、#67、#71、#72、#73、#75 共九处 `MANUAL: 用户 …`。
