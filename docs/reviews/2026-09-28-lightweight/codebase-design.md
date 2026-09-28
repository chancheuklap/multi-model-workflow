# codebase-design

## 定稿（主 agent 复核）

**判断**：本仓只改了一句（`## Glossary` 首段的范围限定），保留。上游的灵魂完整。补一句"这是参考，不是流程"：它在上游只写在不装进宿主的文档页里。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `SKILL.md` 开头段之后（本仓加，merge-note 记一条） | This skill is a reference, not a process: it has no steps and no end of its own, so the task that brought you here decides what you do next. When nothing else is driving, answer the design question you were asked in these terms and stop. | 上游 issue #449（仍开着）：agent 把它当流程执行，跑去并行派 subagent。本仓的 ticket 会话里还没发生过。 |

### 连带改动

- `writing-for-agents` 的 `SKILL-SET-REVIEW.md` Sediment 表会把 `(Michael Feathers)`、`(Ousterhout)` 这类出处当成该删的"出处行"。已在 `writing-for-agents` 定稿里处理：这类名字能让模型调出整套理论，保留。

## 结论

`codebase-design` 是上游 mattpocock/skills 的纯参考型技能，没有脚本：`SKILL.md` 883 词（含 frontmatter），`DEEPENING.md` 385 词，`DESIGN-IT-TWICE.md` 393 词，合计约 1,660 词。本仓对它只有一处改动，即 `SKILL.md` `## Glossary` 首段加的一句范围限定（`The rule governs prose, not names that already exist: …`，约 35 词）；与最新 squash 提交 `5b1a4c51` 以及 GitHub 上 mattpocock/skills 当前 main 比对，其余三份文件逐字一致。本仓改动经四问评估后建议保留，所以 A 类没有应删条目，可删词数为 0。上游原文里有若干冗余（例如 `## Principles` 与 `DEEPENING.md` `## Seam discipline` 重复两条），按任务书不为减字数报上游。"灵魂"基本完整，只缺一样：技能没有告诉直接加载它的 agent "这是参考，不是流程"。上游自己的文档页把这一点列为使用前最该知道的事，上游 issue #449 记录了缺它时的真实失败，至今未关闭。

## A. 删除或改成脚本

无应删条目。

评估过、建议保留的本仓改动：

| # | 位置 | 类别 | 四问证据 | 结论 |
| --- | --- | --- | --- | --- |
| 1 | `SKILL.md` `## Glossary` 首段第三句 `The rule governs prose, not names that already exist: a command name, an acceptance-criterion category, or a literal a program prints keeps the name it has.` | 候选 5（过度防御） | 触发过吗：没找到。它由提交 `793d4703`（2026-09-10）加入，提交信息写的是推理（"照做的 agent 会去改 `scripts/boundary-check.py`…"），没有引用任何事故；`nmem` 与 `~/.claude/projects`、`~/.codex/sessions` 里都没有 agent 因这条禁令改名的记录。正常输入能走到吗：能。本仓库确有以禁用词命名的真东西，我逐一核对过仍存在：`mmw-v2/skills/ui-acceptance/scripts/boundary-check.py`、它第 138 行打印的 `BOUNDARY OK {n}/{n}`、`docs/specs/task-board/screen-contract.yaml` 的 `component:` 列。一张重构 `ui-acceptance` 脚本的票可能同时加载本技能（经 `tdd` 的 `## Seams: where tests go` 末句）并碰到这些名字（推断，未见实例）。 | 第二问答"能"，不满足过度防御的判定条件，保留。另一个理由：`mmw-v2/merge-notes/improve-codebase-architecture.md` 第 14 行明确依赖这一句（那边的同一条禁令不加限定，就是因为 agent 会读到这里的限定），删它就要同时改那边。 |

## B. 灵魂

### 保留，勿删

- `SKILL.md` 开头段 `Design **deep modules**: … The aim is leverage for callers, locality for maintainers, and testability for everyone.`：一句话给出整套词汇为谁服务、换来什么，后面每条原则都是在兑现这三个目标。
- `SKILL.md` `## Glossary` 的 `Consistent language is the whole point.`：告诉 agent 用词纪律不是风格偏好，而是这个技能存在的理由；没有它，禁用词清单读起来就是一条可以随手放宽的规矩。
- `SKILL.md` `**Interface**` 词条（`everything a caller must know … invariants, ordering constraints, error modes, required configuration, and performance characteristics`）：这是整份技能里最能改变 agent 做法的一条定义，它让 agent 在设计接口时写出不变量和错误模式，而不是只写类型签名。
- `SKILL.md` `**Depth**` 词条与 `## Rejected framings` 第一条（`Depth as ratio of implementation-lines to interface-lines (Ousterhout): rewards padding the implementation.`）：说明为什么不用一个可计量的指标，防止 agent 用堆实现代码来"加深"模块。
- `SKILL.md` `## Principles` 四条（`Depth is a property of the interface`、`The deletion test`、`The interface is the test surface`、`One adapter means a hypothetical seam. Two adapters means a real one.`）：都是判断工具而不是步骤，agent 遇到清单外的设计问题时靠的就是这几条。
- `SKILL.md` `**Seam**` 词条的 `_(Michael Feathers)_` 与 `## Rejected framings`、`DESIGN-IT-TWICE.md` 首段里的 `(Ousterhout)`：出处本身就是内容，它让模型调出自己已有的整套知识（Feathers 的 *Working Effectively with Legacy Code*、Ousterhout 的 *A Philosophy of Software Design*）。这与 `SKILL-SET-REVIEW.md` `### Redundancy and bloat` 的 Sediment 表冲突，见下文"与写作标准的冲突"。
- `DEEPENING.md` `## Dependency categories` 首段 `The category determines how the deepened module is tested across its seam.`：说明分类的用途，四个类别因此是判断依据，而不是需要背下来的分类表。
- `DEEPENING.md` `## Testing strategy: replace, don't layer`，尤其是 `If a test has to change when the implementation changes, it's testing past the interface.`：给了一个 agent 自己就能用的检验标准。
- `DESIGN-IT-TWICE.md` 首段 `your first idea is unlikely to be the best`、第 1 步的 `The user reads and thinks while the sub-agents work in parallel`、第 3 步的 `Be opinionated: the user wants a strong read, not a menu.`：分别说明为什么要设计多个方案、为什么先给用户看问题再并行、最后该交出什么。

### 缺口与补充草稿

- `SKILL.md`，开头段（第 8 行）之后、`## Glossary` 之前。缺的是：这是一份参考，没有自己的流程和终点。一个 agent 因为 description 命中（`Use when the user wants to design or improve a module's interface, find deepening opportunities, …`）直接加载本技能时，读不到这一点。从 `tdd` 进来的 agent 读得到，因为 `tdd/SKILL.md` `## Seams: where tests go` 末句写了 `it is a reference to consult, not a session to run`；但直接加载的 agent 读不到。证据：上游文档页 `mmw-v2/upstream/docs/engineering/codebase-design.md` 第 5 行说 `It is a reference, not a process. … That is the thing to know before you invoke it`，第 56 行记录了 issue #449（agent 把本技能当成要执行的流程，抓住 `DESIGN-IT-TWICE.md` 里最像行动的部分，重新探索已经摸清的代码，跑了很久才问第一个问题）；我用 `gh issue view 449 -R mattpocock/skills` 确认它仍是 OPEN。但这份文档页不在技能目录里，不会装进任何宿主，agent 看不到。在 MMW 里的影响：交互会话中会白白消耗大量 token 和时间；夜里没人回答，而 `DESIGN-IT-TWICE.md` 的第 1、3 步都是写给在场用户的。我查了 `~/.claude/projects` 和 `~/.codex/sessions` 的会话记录，没有找到本仓库里任何一次读取 `DESIGN-IT-TWICE.md` 的 ticket 会话，所以这是上游已证实、本仓尚未发生的风险。优先级：低到中。它会改动上游文件，落地时要在 `mmw-v2/merge-notes/codebase-design.md` 加一行（上游若自己修了 #449 → 收上游）。
  > This skill is a reference, not a process: it has no steps, no checkpoint and no end of its own, so it never decides what you do next. The task that brought you here does, whether that is a spec, a ticket, a review or a question from the user. Speak these terms and apply these principles inside that task. When nothing else is driving, answer the design question you were asked in these terms and stop; exploring the codebase, redesigning modules or spawning sub-agents is work the user starts, not work this skill starts.

- 考虑过、不建议补的一条：description 提到 `make code more testable or AI-navigable`，但正文从没解释 "AI-navigable" 与模块深度的关系（每个夜里的 worker 都从空上下文开始，深模块让它只读接口就能正确使用）。这段话对 MMW 有意义，但我找不到 agent 因为缺它而做错的证据，而且补它要改上游正文，不满足"上游原文只在真会让 agent 做错时才动"的门槛。记下来供参考，不列为建议。

## C. 死板的流程

无。本仓没有给这个技能加任何流程。上游唯一的编号流程是 `DESIGN-IT-TWICE.md` `## Process`：先向用户框定问题，再并行派子 agent，最后比较并给出推荐。这个顺序有真实依赖（子 agent 的简报要用第 1 步整理出的约束，比较要等所有设计交回），而且每一步都附了理由，不算死板。`SKILL.md` `## Designing for testability` 的 1–3 是三条原则，不是要按顺序执行的步骤。

## 脚本

无。技能目录只有三份 Markdown 和 `agents/openai.yaml`（9 词，只有 `display_name` 与 `short_description`，没有 `policy` 键，与 `SKILL.md` frontmatter 没有 `disable-model-invocation` 的状态一致，符合 `mmw-v2/merge-notes/README.md` `## disable-model-invocation` 的配对规则）。

## 与其他技能的重复或交接问题

- deletion test 有两份：`SKILL.md` `## Principles` 一份，`mmw-v2/upstream/skills/engineering/code-review/references/standards-reviewer.md` 第 3 节末尾一份，措辞相同，后者多了报法（`name the module and the callers …`）。两份都该留：审查者在行动时加载的是后者，而且 `mmw-v2/merge-notes/code-review.md` 第 35 行已经说明，这是 Standards axis 从本技能用到的唯一一条，所以全文写在审查者那边，不让审查者去读整份本技能。
- `seam` 有两个定义：本技能 `**Seam**` 词条用 Feathers 的定义（`a place where you can alter behaviour without editing in that place; the location at which a module's interface lives`）；`tdd/SKILL.md` `## Seams: where tests go` 写的是 `the public boundary you test at`；仓库术语表 `docs/contexts/tickets/CONTEXT.md` 的 **seam** 条目把出处归到 `tdd`。这是已经定下的事：提交 `0b00edcb` 曾把本技能的定义改成 `tdd` 的意思，同一天的提交 `70c9a93f` 又恢复为上游原文，理由是两个定义指的是同一个位置。本轮不重开。附带一处小的措辞不一致，只记录：`tdd` 的定义句里用了 "boundary"，这个词本技能禁用，`docs/contexts/ui-acceptance/CONTEXT.md` 的 **boundary** 条目也说它 `is not a word for a seam`；这是上游 `tdd` 原文（`5b1a4c51` 中即如此）。
- `SKILL.md` `## Glossary` 的范围限定句与 `mmw-v2/merge-notes/improve-codebase-architecture.md` 第 14 行互相依赖：改其中一处，另一处要跟着改（A 表第 1 行已说明）。

## 与写作标准的冲突

`mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-REVIEW.md` `### Redundancy and bloat` 的 Sediment 表把 `a source line ("from chapter 3 of …")` 归为 "nowhere"（应删）。照这一条修剪，会删掉 `SKILL.md` 的 `_(Michael Feathers)_`、`## Rejected framings` 的 `(Ousterhout)` 和 `DESIGN-IT-TWICE.md` 首段的 `Based on "Design It Twice" (Ousterhout)`。按任务书，这几处是灵魂，应当保留：一个作者名能让模型调出它已有的整套理论，而 `## Rejected framings` 那条如果不说明被否决的是谁的定义，就讲不通。该标准同一节的 "These stay" 段没有覆盖"用来调出已有知识的出处"这种情况，下一轮修剪者照表执行就会误删。建议在 "These stay" 段补一类：引用它是为了让模型调出一套已知理论的出处。

## 没查到的

- 没有跑任何测试，也没有加载本技能做实际设计来观察行为；B 节对 agent 行为的判断来自上游文档页记录的 issue #449 和会话记录检索，本仓库内没有复现。
- 会话记录只查了本机的 `~/.claude/projects` 与 `~/.codex/sessions`，没有查 Grok、Cursor、Pi 的会话。检索方法是按文件名和工具调用参数匹配 `DESIGN-IT-TWICE`、`codebase-design/SKILL.md`，没有逐会话阅读。结果：ticket 会话读 `codebase-design/SKILL.md` 集中在 2026-09-06 至 09-22，多数出自当时 `code-review` 指向本技能的旧审查指令（提交 `698659e4` 的 diff 删掉了 `code-review` 里的 `Read the codebase-design skill's SKILL.md as well …` 一行，已核实）；没有 ticket 会话读过 `DESIGN-IT-TWICE.md`。
- 没有读 `to-spec`、`to-tickets` 全文，只确认了它们都不点名本技能（全库 grep）。
