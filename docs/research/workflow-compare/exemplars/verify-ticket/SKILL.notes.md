# 能力技能范本注解：`exemplars/verify-ticket/SKILL.md`

这份范本是 `verify-ticket` 按 R18 §4.1 剥离流程之后的 `SKILL.md`，按 R20 5.5 模板写成。名字按 R19 §4.1 保留 `verify-ticket`（现役 717 处，还写在给消费仓库的 downstream-note 里）；它的 reference `sub-issues.md` 按 R19 §4.5 改名 `child-issues.md`。没有用户定的名字。

剥离后它只剩三件能力（R18 §4.1 verify-ticket 行）：跑一张票的判据并打印结果、lint 票面与批次的阻塞图、发布 spec 与票；另有 `issue_tree.py`。写票状态的命令、事件词表 `events.py`、`own_session()`、「谁在何时用我」的句子全部离开（去处见 R18 §4.1 同一行）。

缩写：`verify-ticket/SKILL.md` = 现行 `mmw-v2/skills/verify-ticket/SKILL.md`（25 行）；`verify-ticket.py` = `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`；`issue_tree.py` = 同目录。

## 主形态

R20 S-C2 的「分支型」加三个做法节：`## Pick a branch` 表把两个有独立材料的分支（子票 kind、lint）交给 reference；跑判据、读树、发布三件事各写一节，因为它们都是一条命令加「每种结果之后做什么」（X12），没有先后，不是步骤型。结尾是 `## Output` 与 `## Composing this skill`，没有下一步（S-C3、X13）。

退出码之后做什么，写在这个命令的做法节里（`## Run a ticket's criteria`、`## Read the tree under an issue`、`## Publish a spec or a batch`）。`--lint` 没有做法节：它的材料在 `references/linting.md`，由 `## Pick a branch` 交出，所以它的退出码与之后做什么写在 `## Output` 的 `--lint` 项里（理由见逐段来源 `## Output` 的 `--lint` 退出码一行）。别的能力技能照这条分：有做法节的命令，退出码写在做法节；做法在 reference 里的命令，退出码写在 `## Output`。

## 逐段来源

| 段 | 来源 | 结构依据（pstack） | 写法依据（mattpocock） |
|---|---|---|---|
| frontmatter `description` | 改写：现行 description「Run one ticket's acceptance criteria, and close the ticket when they pass. Use when something has to be cut out of a ticket, and when a batch is about to be published.」。「is」部分重写成剥离后的三件能力加 `issue_tree.py`（关票离开，R18 §4.1；R18 §4.1 verify-ticket 行把 `issue_tree.py`「读 spec → 票 → 子票的树」列为本技能的能力，写进 description 是为了让需要读树的 agent 找得到它）；触发分支保留原有两支（「when something has to be cut out of a ticket」「when a batch is about to be published」逐字），加一支「when a ticket's criteria have to be run」 | S-C1、S-G6 | SSR L67（只写是什么与触发分支） |
| `# Verify ticket` | 搬运：`verify-ticket/SKILL.md` L6，逐字 | R20a C2 第 1 项 | 无 |
| 目标段第 1 句 | 搬运：`verify-ticket/SKILL.md` L8 第 1 句，逐字 | R20a C2 第 2 项（`PS:skills/how/SKILL.md` L9） | W-C1 |
| 目标段第 2 句 | 改写：`verify-ticket/SKILL.md` L8 第 2 句「This skill runs them and posts the outcome on the ticket as an event.」→「This skill runs them and prints the outcome.」（R18 §4.1：跑判据只打印结果，不写事件） | 同上 | W-C1 |
| 目标段第 3 句 | 搬运：`implement` L78「A criterion passes only when its `CHECK` exits 0 and its output matches `EXPECT`.」，逐字。它定义「通过」，属于这项能力本身（S-P5）；`work-a-ticket` 范本对应处写了 `drop` | 同上 | W-G6（通过的定义只有一个家） |
| 目标段第 4 句「Your reading of the output never stands in for either.」（立场） | 新写。出处：`mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md` L84「`ok`, `passed` or `done` on their own also appear in failing output」、ADR 0008 第 3 条（推断：agent 会想自己读输出判定通过）。「its `EXPECT` match」沿用本段第 1 句对 `EXPECT:` 的叫法，不另起「the marker」这个同义词（W-G6；`to-tickets` L84 把它叫 success-only marker，那是写判据一侧的词）。它紧跟第 3 句的定义，只说立场，不再定义一次「通过」：「either」指第 3 句的两个条件 | 同上 | W-G3（诱惑与替代动作）；R20b M3 |
| 目标段第 5 句（谁用、代价） | 新写。出处：`implement` L22「The checks exist so the user can trust a closed ticket without reading its code.」；为避免与 `work-a-ticket` `#### While writing code` 里保留的原句重复（K37），换了说法。代价写成具体后果「ships that behaviour unseen」：用户不读代码，没人再看这一处行为 | 同上 | W-G1（谁用产出、做浅了的代价） |
| 目标段第 6 句（lint 与发布为了什么） | 新写。出处：`mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md` L10「Each ticket is read by agents who were not in this conversation and cannot ask it anything」；`mmw-v2/skills/verify-ticket/references/linting.md` L11「The graph it checks is the tracker's blocking edges, the same ones `--preflight` refuses on and `advance` dispatches from」。读树没有另写一句：`## Read the tree under an issue` 末句已写出读短了的代价 | 同上 | W-C1（每一项能力都说出为了什么） |
| 第 2 段第 1 句 | 搬运：`verify-ticket/SKILL.md` L10 第 1 句，逐字，句末插原则点名（T2 附加项；R18 §4.1「第 10 行理由 → 点名 **principle-the-tracker-is-the-state**」，R19 §4.3 改名） | 同上 | N2 |
| 第 2 段第 2 句 | 改写：L10 第 2 句删去「writes its events,」并去掉随之多余的逗号（见改写清单第 2 条） | 同上 | 无 |
| 第 3 段 | 搬运：`verify-ticket/SKILL.md` L12，逐字 | 同上 | W-G2（分号后是理由） |
| `## Pick a branch` 表 | 改写：`verify-ticket/SKILL.md` L18–21 的表；列名「You are here」→「When」（R20 5.5 骨架）；两行条件去掉时机（「opening a night on a spec」离开，R18 §4.1「`linting.md` 第 3 行「何时 lint」→ P1、P12」）；第 1 行文件名按 R19 §4.5；第 1 行后半「and you have to say which kind of child it becomes」是新写，出处 R18 §4.1 verify-ticket 行「子票五种 kind 及判别问题」：剥离后这份 reference 只剩 kind 的判别表，条件要说出读它是为了定 kind | S-C2 分支型（`UP:engineering/prototype/SKILL.md` L10–17） | SSR L31（多选一写成表） |
| `## Run a ticket's criteria` 第 1 句 | 新写：命令形式取 `verify-ticket.py` L4120–4122 的位置参数；`--reverify` 的说明搬运 argparse help L4124「re-run every criterion, including the ones already ticked」改成陈述句 | N9 | X12（写命令，不叙述内部） |
| 第 2 句「It posts nothing on the ticket.」 | 新写：R18 §4.1「跑判据只打印结果，不写事件」 | 同上 | W-G6（与 `ticket_state.py` 的记录运行区分，R19 §4.8 区分句） |
| 第 3 句（产品规则） | 改写：`verify-ticket/SKILL.md` L25 的条件「A criterion has to launch, reach or observe the running product」与结论「Its five rules while the product is running bind every run of this skill」合成一句（见改写清单）。它不是「下一步」，而是约束本技能运行的规则，所以留在能力技能里 | S-C5 | W-G12 |
| 四个退出码 | 改写：`verify-ticket.py` L4074–4079 的退出码说明，逐项改成「结果 → 做什么」（X12）。删去码 4（「the ticket.checked recording them could not be written」），因为剥离后这次运行不写事件（推断，见「没有核对的」） | N9 | X12、W-O1 |
| Exit 1 的后半「a `FAIL` line above the summary shows what each failing criterion printed, and the line under the summary names the criteria it counts」 | 新写。本轮对照 `mmw-v2/skills/verify-ticket/scripts/gate-check/gate-check.mjs` 核实：每条跑到的判据先打一行 `RUN`（L587），跑完打 `PASS` 或 `FAIL` 加一行 `exit=…; EXPECT=…; output=…`（L599–605，通过时 output 只是指纹）；`UNMET:`、`HANDOFF REQUIRED:` 行下面一行列出计入的判据编号（L758–767）。`verify-ticket.py` L1876–1878 把 gate-check 的输出原样写到 stdout。`ticket_state.py` 拆出后若改了输出，这一句要跟着改 | 同上 | X12（写出下一步要看哪一行） |
| Exit 3 的第 2 句「Nothing signals when a slot frees, so do not retry in a loop: carry on with other work and run the same command again when you next need its result.」 | 新写。直接跑本技能的命令时，没有唤醒告诉你槽位空了：`worker.queued` 的唤醒属于 `ticket_state.py` 的记录运行（R18 §4.1），不属于这里。`EXIT_CODES`（`verify-ticket.py` L4076 至 L4078）写明一次普通运行拿不到槽位就立刻退出 3，`--reverify` 在脚本里先等 `MMW_SLOT_WAIT_S` 秒；所以脚本已经替调用方等过，调用方不必再轮询（**principle-agents-are-woken-not-polled** 的精神；「下次需要结果时再跑」是推断，没有观察到的运行） | 同上 | W-G9（每种结果都有出路）；K30 |
| Exit 3 的末句「A run that waits for a slot is not a run that failed.」 | 新写的理由。它针对的情况：agent 把退出 3 当成判据没通过，去改代码或写 `ABANDON`（推断，没有观察到的运行）。依据 `EXIT_CODES` L4076–4077「no product slot was free, nothing run」 | 同上 | W-G2；W-G3 |
| `Done when` | 新写：R20 5.5 做法节（步骤型、阶段型才强制；这里加一行，因为 agent 会把退出 2、3 当成结果） | X10 | W-G7（能失败） |
| `## Read the tree under an issue` 第 1 句 | 新写：何时用这项能力（X12、K25）。出处 R18 §4.1 verify-ticket 行「`issue_tree.py`（读 spec → 票 → 子票的树）」；它的第一个调用方是 `work-a-ticket` 第 2 步读本票开着的子票（该范本改写清单第 18 条） | N9 | X12 |
| 第 2–4 句 | 改写：`issue_tree.py` L1–11 docstring 的用法行与 L37–39 的退出码。R18 §4.1 把 `issue_tree.py` 留在本技能；本轮之前没有任何技能文本点名它（`grep`），现在 `work-a-ticket` 第 2 步点名它 | N9 | W-G7 |
| 末句前半「Exit 2 means the tree was not read, not that it is small」 | 新写。它针对的情况：agent 把退出 2 读成「这一层没有子票」（推断）。依据 `issue_tree.py` L9–11「refuses to answer when any list came back shorter than the count the tracker gives for it」 | N9 | W-G3 |
| 末句后半「a page left unread reads exactly like an issue with fewer children」 | 改写：取 `issue_tree.py` L8–9「a page left unread raises no error: it reads exactly like an issue with fewer children」，删去「raises no error:」（见改写清单第 6 条） | N9 | W-G2（这半句是理由）；与 **principle-silence-is-never-a-pass** 同一个意思 |
| `## Publish a spec or a batch` | 改写：`verify-ticket.py` L4099–4106 的 `--publish` 退出码，与 argparse help L4127–4142；草稿格式不复述，指向 `--help`（N9「完整开关表留在脚本的 `--help`」）。「Neither writes an event.」取 R18 §4.1「`--publish`，本轮核实它不写事件」。两处退出 2 都加「fix what stderr names」，与 `## Run a ticket's criteria` 的写法一致 | N9 | X12 |
| `--drafts` 退出 2 之后的出路（从「Every draft printed as」到段末） | 新写。本轮读 `run_publish_drafts`（`verify-ticket.py` L3992–4069）与 `_draft_dependencies`（L3975–3989）核实：草稿按层级顺序逐份创建，每建一份打印 `<draft> -> #<n>`（L4055），失败时 stderr 末尾列出 `already published: …`（L4027–4029、L4044–4053）；重跑不会跳过已发布的草稿，所以同一目录重跑会在 tracker 上再建一遍，重复的 issue 对外可见；阻塞边在全部草稿创建之后才连（L4057–4066），中途停下时一条边也没有记；`BLOCKED BY:` 接受 `#<n>`（L3981–3983）；全部打印之后的退出 2 只能来自最后的 `lint_spec`（L4068，例如 oracle 够不到）。出路本身（移走、改写 `BLOCKED BY:`、补边）没有实跑过，是推断；拆分票若给脚本加「跳过已发布」的能力，这一段改成点名那个开关 | N9 | X12（每种结果之后做什么）；W-G3（诱惑：原样重跑） |
| `## Output` | 新写，四项的格式分别取：判据运行取 `mmw-v2/skills/verify-ticket/scripts/gate-check/gate-check.mjs` L587、L599–605、L754–767 与 `verify-ticket.py` L50 `SUMMARY_RE`（本轮核实，原来写的「One line per criterion」不准）；`--lint` 取 L3682–3694 `lint_criteria` 的 `say` 与 `verdict`；`--publish` 取 `--spec-body` 的退出码说明与 L4055 的打印；`issue_tree.py` 取 L30–33 | R20 P12（写产物结构）；R20a F5 | 即使细节在 reference 里也列出节名（R20 5.5 表） |
| `## Output` 的 `--lint` 退出码 | 改写：`EXIT_CODES` L4083–4087，逐项改成「结果 → 做什么」（X12）。放在这里而不是 `references/linting.md`：`write-a-spec-and-tickets` 第 8 步的 `Done when` 按「`--lint` exits 0」判断完成，而现行 `linting.md` L1–11 没有退出码；`SKILL.md` 每次都读，写 `linting.md` 范本时不再复述这三个码 | X12 | W-G9（每种结果都有出路） |
| `## Composing this skill` | 新写，照 `PS:skills/show-me-your-work/SKILL.md` L79–81 的写法（「Reference it by name and let it own the format. Don't restate the columns.」）。它回答剥离后最容易出错的地方：mode 的 `ticket_state.py <n> --run-and-record-criteria` 跑的是同一批判据（R19 §4.8），那一侧不该复述 `CHECK:`、`EXPECT:` 的读法。按 S-C3 不点名调用方 | R20 5.5 `## Composing this skill`（R20a C2 第 8 项） | W-G12 |

## 必须改写、做不到逐字搬运的地方

1. `verify-ticket/SKILL.md` L8 第 2 句：「posts the outcome on the ticket as an event」→「prints the outcome」。行为变了：写事件的部分搬去 `ticket_state.py`（R18 §4.1）。
2. `verify-ticket/SKILL.md` L10 第 2 句：「Every run reads it fresh, writes its events, and carries nothing to the next run.」→「Every run reads it fresh and carries nothing to the next run.」写成 `replace`：删去「writes its events,」（同上），并去掉「fresh」后的逗号，因为只剩两个并列谓语（T3：改标点也不是机械改写）。
3. `verify-ticket/SKILL.md` L18 至 L21 的表，逐格写成 `replace`（表格行按单元格切句，R21 §3.3）：
   - 列名「You are here」→「When」（R20 5.5 骨架）；「Read」不变。
   - 第 1 行条件「Cutting something out of the ticket」→「Something has to leave a ticket, and you have to say which kind of child it becomes」：剥离后这份 reference 只剩 kind 的判别表（R18 §4.1），条件要说出读它是为了定 kind。
   - 第 1 行文件「[references/sub-issues.md](references/sub-issues.md)」→「`references/child-issues.md`」（R19 §4.5 改名；链接写法改成 N7 的行内路径）。
   - 第 2 行条件「About to publish a batch (its drafts), having published one, or opening a night on a spec」→「A batch has to be linted: its drafts before any is published, one ticket and the graph it sits in, or every ticket under a published spec」：何时 lint 离开本技能（R18 §4.1「`linting.md` 第 3 行「何时 lint」→ P1、P12」），条件改成 lint 的三种对象，逐项对应 `linting.md` L6 至 L8 的三条命令。
   - 第 2 行文件「[references/linting.md](references/linting.md)」→「`references/linting.md`」（同一个文件，T2 第 4 种，不单列）。
4. `verify-ticket/SKILL.md` L25（`## Reached from here` 唯一一条）有四个条件和一句结论。四个条件去 mode 触发行（R18 §4.1）：「A criterion has to launch, reach or observe the running product」与「you are about to touch a process or a port」进 mode 触发行 3（产品、进程、端口）；「you are reading a `DIFF`, `MISS`, `JOURNEY` or `HARNESS` line」与「the repository has no `.mmw/target.json`」进 mode 触发行 4。结论句「Its five rules while the product is running bind every run of this skill.」改写后留在本技能 `## Run a ticket's criteria` 第 3 句，因为跑判据时启动产品的正是这项能力，而能力技能要能脱离 mode 使用（R18 §4.5 末条）。mode 触发行 3 也指向同一节 `## Five rules while the product is running`：两处都是指针，都不复述五条规则，不算 K37 的重复。
5. `verify-ticket.py` 的 `EXIT_CODES` 与 `issue_tree.py` 的 docstring 是脚本文本，不是技能文本。搬进技能要改成「结果 → 做什么」的句式（X12），做不到逐字；其中 `EXIT_CODES` L4106 的「gh failed partway」改为「the tracker failed partway」，不在技能文本里点工具名（S-G8 的精神）。脚本文本不是 Markdown 源，逐字搬运检查不从它切单元（R21 §3.3），所以票上这些句子都是带整句的 `new` 行，出处写脚本的行。逐句如下（原文 → 新句）：
   - `EXIT_CODES` L4075「0 every criterion met」→「**Exit 0.** Every criterion met.」
   - L4075「1 something unmet or abandoned」→「**Exit 1.** Something is unmet or abandoned; a `FAIL` line above the summary shows what each failing criterion printed, and the line under the summary names the criteria it counts.」（后半的出处见逐段来源 Exit 1 一行）
   - L4075 至 L4076「2 the ticket could not be read or the run could not start, reason on stderr, nothing posted」→「**Exit 2.** The ticket could not be read or the run could not start, and nothing ran. Fix what stderr names and run it again.」
   - L4076 至 L4078「3 no product slot was free, nothing run (…)」→「**Exit 3.** No product slot was free, and nothing ran.」加逐段来源里 Exit 3 的两句新句。
   - `issue_tree.py` L4「issue_tree.py <issue> [--root map|spec|ticket]」与 L6「a map, its specs, each spec's tickets, each ticket's children」→「`python3 scripts/issue_tree.py <issue> [--root map|spec|ticket]` prints, as JSON, the tree of issues under one issue: a map, its specs, each spec's tickets, each ticket's children.」
   - L11 至 L12「`--root` says which layer `<issue>` is (default `spec`), so the lists below it get their own layer's size.」→「`--root` says which layer `<issue>` is (default `spec`).」
   - L37 至 L39「exit 2, with the reason on stderr, when the tracker could not be asked, answered with an error, has no such issue, or returned a list shorter than its count.」→「It exits 2, with the reason on stderr, when the tracker could not be asked, answered with an error, has no such issue, or returned a list shorter than its count.」
   - `EXIT_CODES` L4100 至 L4102 与 argparse help L4132 至 L4142（`--publish`、`--spec-body`、`--title`、`--map`）→「`python3 scripts/verify-ticket.py --publish --spec-body <file> --title <title> [--map <map>]` publishes a spec, and with `--map` as a native sub-issue of that map. Exit 0: published, printed as the issue number. Exit 1: published, but the native parent could not be confirmed as `--map`; stderr says so. Exit 2: refused, nothing published; fix what stderr names and run it again.」
   - `EXIT_CODES` L4103 至 L4106 与 argparse help L4127 至 L4131（`--drafts`）→「`python3 scripts/verify-ticket.py <spec> --publish --drafts <dir>` publishes a directory of ticket drafts as native sub-issues of the spec, in the draft shape the script's `--help` gives. Exit 0: every draft published, every blocking edge recorded, and `--lint` on the published spec reported no `ERROR`. Exit 1: published with a blocking edge that could not be recorded, or `--lint` on the published spec found one. Exit 2: refused before anything was created, or stopped after publishing some drafts; fix what stderr names.」其后从「Every draft printed as」到段末的五句是新写，出处见逐段来源。
   - `EXIT_CODES` L4084 至 L4087 的 `--lint` 三个码 →「Exit 0: no `ERROR` counts (a closed ticket's `ERROR` is printed and counts for nothing). Exit 1: a ticket or the graph has an `ERROR`; fix it and lint again. Exit 2: a criterion names an oracle this run cannot reach, and nothing was read; do what stderr names and lint again. No exit runs a `CHECK:` or posts a comment.」
6. `issue_tree.py` L8–9「a page left unread raises no error: it reads exactly like an issue with fewer children」→「a page left unread reads exactly like an issue with fewer children」，删去中间的「raises no error:」，接在新写的「Exit 2 means the tree was not read, not that it is small:」之后。

## 删去的句子（写成 `drop` 行时用）

- `verify-ticket/SKILL.md` L3 description 的「and close the ticket when they pass」：关票离开本技能（R18 §4.1，`--closeout` → `ticket_state.py`）。删后由 `work-a-ticket` 的 **Close out** 指导。
- `verify-ticket/SKILL.md` L10 第 3 句「Every comment it posts is an event: a first line for a person and a trailing `<!-- mmw {...} -->` block, which is the only part any program reads.」：它指导怎样读本技能贴的评论。本技能不再贴评论；事件格式的家是 `events.py` 的模块说明（L27–36），随它搬进 mode 的 `scripts/`。
- `verify-ticket/SKILL.md` L14 节名 `## Find your moment` 与 L16「A worker's claim, criteria runs and closeout are steps of the `implement` skill.」：它指导 worker 去哪里找自己的步骤。R18 §4.1 定「删」；删后由 mode 路由表与 `work-a-ticket` 指导。
- `verify-ticket/SKILL.md` L23 节名 `## Reached from here`：S-C3 禁止这个节。
- `verify-ticket.py` 退出码 4：见上。

## 与 R18 的偏离与待定

- **`--reverify` 与 `--actor` 的归属没有定**。今天 `--reverify` 必须带 `--actor worker|main`（`verify-ticket.py` L4162–4164），`--actor` 是写进事件的值。剥离后本技能不写事件，`--actor` 应随记录一起去 `ticket_state.py`；R19 §4.8 把 `--reverify`、`--actor` 都列为「保留」，没说留在哪个脚本。范本只写 `--reverify` 本身的意思，不写 `--actor`；B2 的拆分票要定。
- **退出码 3（没有空的产品槽）是否还在本技能**。R18 §4.1 把「产品槽排队的 `worker.queued`」移到 `ticket_state.py`，但槽位租约本身是 `lease.py`（`ui-acceptance`）的，本技能跑判据时仍可能拿不到槽。范本保留码 3（推断），拆分票要核实。
- **`--lint` 是否读事件**：R18 §4.1 已写明由 B2 票核实，读的话那部分随 `ticket_state.py` 走。范本按「不读」写。

## 长度

52 行，在 pstack 能力技能多数的 35–115 行之内（S-G9）。

## 没有核对的

- `--publish --drafts` 的打印已从 L4055 核实；`--spec-body` 打印的就是 issue 号，取自退出码说明，没有读它的函数。
- `issue_tree.py` 会列出所有子票（开着的、关了的），调用方要按 state 挑开着的；是否加一个只列开着的开关，由拆分票决定。
- `references/child-issues.md` 与 `references/linting.md` 剥离后的正文没有写范本；`child-issues.md` 应只剩 `sub-issues.md` L13–23 的 kind 判别表（R18 §4.1），它第 5 行点名的「the `implement` skill's bullet "For a file outside **Owns**"」在 `implement` 回原文后没有落点，要改成不点名 playbook 的写法（S-C3）。
- 这份技能对 agent 行为的作用没有实测（R20 第 8 节）。
