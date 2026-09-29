# mode 范本注解：`exemplars/mmw/SKILL.md`

这份范本是 R18 第 2 节在 B2 批次结束时的 mode，已按 R18 第 17 节 D1–D7 调整，名字按 R19。它给写 B1、B2 mode 票的会话当基准：每一段标出是搬运还是新写，搬运的给源文件与行号，新写的给出处；结构依据写 R20 的规则号与它背后的 pstack 出处，写法依据写 R20 的规则号与它背后的 mattpocock 出处。脚本的写法按 `README.md` `## 范本共用的约定` 第 1 条。

缩写同 R20 第 1 节：`PS mode` = `docs/research/code-landing-refs/pstack/skills/poteto-mode/SKILL.md`；`SSR` = `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md`（现行版）；`implement` = `mmw-v2/upstream/skills/engineering/implement/SKILL.md`（现行版，含 MMW 改动）；`dispatch/SKILL.md` = `mmw-v2/skills/dispatch/SKILL.md`；`verify-ticket/SKILL.md` = `mmw-v2/skills/verify-ticket/SKILL.md`（现行版）。

## 名字

- **技能名 `mmw`**：R18 第 17 节 D10 定（由 Claude 代定，待用户复核），R19 `## 用户过目` 与 §4.1 第 1 行「保留 `mmw`」照写。frontmatter `name`、description 与 `## Subagents` 简报首句都逐字取 R18 §2.1、§2.2 的原句，不带改名。落地文件是 `mmw-v2/skills/mmw/SKILL.md`（R19 第 7 节），目录名与 `name` 相等（R20 K9）；指针前缀是 `mmw <slug>#<Step title>`（R20 N5）。

## 逐段来源

| 段 | 来源 | 结构依据（pstack） | 写法依据（mattpocock） |
|---|---|---|---|
| frontmatter `description` | 搬运：R18 §2.1 的英文原句，逐字。句中的「`mmw <playbook>#<step>`」是 R18 §2.1 的写法；指针的实际形状按 R20 N5 是 `mmw <slug>#<Step title>`，两者指同一个东西，description 不为统一改写 | S-G6、S-M1（R18 §2.1：只有 `name`、`description`，不带开关） | SSR L67：「是什么」加三个触发分支（X7） |
| `# MMW mode` | 新写：R20 5.1 骨架 `# <Name> mode`；显示名取品牌 MMW | S-G1（PS mode L11 `# Poteto mode`） | 无 |
| `## Non-negotiables` 首段第 1、2 句 | 搬运：PS mode L15 第 2、3 句，「leaf SKILL.md」改为「file」（R18 §2.2 标注的改动） | S-M1（PS mode L13–15） | 无 |
| 首段第 3 句「An unattended session writes them into its deliverable …」 | 新写：R18 §2.2「无人会话把这一句写进交付物（第 6 节）」、R18 §6 表 | 同上 | W-G9（无人时的出路） |
| 触发行 1（L12，关票、改 label、写事件） | 新写，英译 R18 §2.2 表第 1 行；B2 版关票写 `ticket_state.py`（R18 §2.4 B2 行，R19 §4.6 `ticket.py` → `ticket_state.py`）。这是 mode 里第一次点名两个脚本，按约定写出解释器与路径。第 2 句理由「a ticket closed around them carries no event the pipeline can read」是新写，出处 `mmw-v2/skills/verify-ticket/scripts/events.py` L30–32「Every event is written by a script … and never typed by a model」（推断：绕开脚本关票就没有事件） | S-M3（PS mode L19–35 的 `条件 → 去处`） | W-G2（理由写在规则旁）；X3（禁令配理由） |
| 触发行 2（L13，被拒绝） | 新写，英译 R18 §2.2 表第 2 行 | S-M3；N2 | W-G12（点名不复述） |
| 触发行 3（L14，产品、进程、端口） | 第 1 句新写，条件取 `verify-ticket/SKILL.md` L25「you are about to touch a process or a port」与 `dispatch.sh` L109 `PRODUCT_RULES`「Before you start, reach or stop the product」；第 2 句搬运 `PRODUCT_RULES` 第 1 句「Several tickets run on this machine at once.」。源里这一句只有一处，全套也只在这里搬运一次：`work-a-ticket` 的 `#### While the product runs` 不再带它，改为指向本行（见该注解逐段来源） | S-M3；N1 | W-G2：这一句是理由 |
| 触发行 4（L15，oracle 输出行与 `.mmw/target.json`） | 新写。条件逐字取 `verify-ticket/SKILL.md` L25 的第 2、3 个分句「you are reading a `DIFF`, `MISS`, `JOURNEY` or `HARNESS` line; the repository has no `.mmw/target.json`」，改成触发行的主语形式；去处按 R18 §4.1 verify-ticket 行「`## Reached from here` → mode 触发行」；与 `ui-acceptance` description「reading a DIFF, MISS, JOURNEY or HARNESS line」「filling `.mmw/target.json`」一致 | S-M3；N1 | R20b M7（用原 description 的话） |
| 触发行 5（L16，screen contract 覆盖的代码） | 新写，英译 R18 §2.2 表第 4 行；文件名按 R19 §4.5 `writing-interface-code.md` → `writing-ui-code.md` | S-M3；N8 | R20b M7：条件写成可观察的情况 |
| 触发行 6（L17，advisor） | 新写。三个条件逐字取 `mmw-v2/skills/advisor/SKILL.md` L3 description 的前三支「before an architecture choice, a data migration, a big refactor or an API shape is committed; when one problem has resisted two attempts; before a disputed reading of the task is treated as settled」，第三支改成「is about to be treated as settled」与前两支同一句式；命令取 R18 §4.1 advisor 行「mode 触发行写 `dispatch.sh advise`」；门槛指针取 R18 §2.2 表第 5 行 | S-M3；N7、N8、N9 | R20b M7 |
| 触发行 7、8（L18、L19） | 新写，逐行英译 R18 §2.2 表第 7、8 行（合并、人工步骤）。第 7 行条件取 `resolving-merge-conflicts` description「an in-progress merge or rebase has conflicts, or when a clean merge makes the repository checks fail」。R18 表第 6、9 行（前提、阶段边界）不进 mode，见删去的句子 | S-M3；N1、N2 | R20b M7 |
| 触发行 9（L20，自建 worktree） | 新写；末半句「those names belong to the pipeline」搬运根 `AGENTS.md` `## Key Conventions` 第 2 条的半句；加 `research-<n>` 出处 R18 §16 脚本行 | S-M3 | W-G2 |
| 触发行 10（L21，凭据） | 新写，英译 R18 §5.2 该原则的规则列；原则名按 R19 §4.3 | S-M3；N2 | 无 |
| 触发行 11（L22，槽位与 pstack 名字） | 新写，英译 R18 §2.2 表第 16 行；文件名按 R19 §4.5 `slots.md` → `pstack-names.md`；原文里的「Cursor」按 D3 与 S-G8 改写成「a tool, setting or skill that only an imported pstack file uses」 | S-M3；S-G8 | 无 |
| 触发行 12（L23，流水线故障） | 新写，英译 R18 §2.2 表第 17 行；「not yours to route around」搬运 `mmw-v2/skills/ui-acceptance/SKILL.md` L36 规则 5 的短语；原则名按 R19 §4.3 | S-M3；N2 | W-G9（在场与无人两种出路）；X3 |
| 触发行 13（L24，rebase 读作 integrate） | 新写；「never a rebase」取 `implement` L78「Never rebase, abort or push from this integration command.」 | S-M3 | W-G6（一词一义） |
| `## Principles` 首段第 1、2 句 | 搬运：PS mode L39，「leaf skill」改为「principle file」（R18 §2.2 标注的改动） | S-M1（PS mode L37–39） | 无 |
| 首段第 3 句（解析规则） | 新写，英译 R18 §2.2 `## Principles` 第 2 条 | 同上 | W-G6 |
| 分组与 pstack 14 条索引行 | 搬运：显示名逐字取各原则文件 H1（X14），「何时适用」逐字取各原则 `description` 的第一句（R18 §2.2 第 3 条；`docs/research/code-landing-refs/pstack/skills/principle-*/SKILL.md` 第 3、7 行）。只列 R18 D6 下 B1 导入的 14 条（R18 §5.3 B1 行「MMW 调用方」一列非空者） | S-M3 索引行格式（PS mode L41–77） | 无 |
| `**Pipeline**` 组 12 行 | 新写：显示名是 MMW 原则的 H1（sentence case，X14），slug 按 R19 §4.3；「何时适用」是各原则 description 第一句的草稿，出处 R18 §5.2 表的规则列与「被谁点名」列。第 1 行与本轮原则范本的 description 第一句逐字相同 | 同上 | X7 |
| `**User rules.**`（L74）第 1 句 | 新写：给 `shared.md` 下一次定义，因为读 mode 的 agent 看不到叫这个名字的文件（S-G8、W-G6）。出处：根 `AGENTS.md` `## Commands` 的 install 行（`~/.claude/CLAUDE.md` → `mmw-v2/prompt/shared.md`；Codex、Pi、Grok 的 AGENTS.md 由 `render.py` 生成）、`mmw-v2/prompt/README.md` 的表；编号 1–15 与三个节名本轮在 `mmw-v2/prompt/shared.md` 核对过（文件开头另有 1–5 的前言编号，不是规则，所以句中写明节名） | S-G4（粗体段首标签） | W-G6（一个名字只指一样东西） |
| `**User rules.**` 其余句 | 新写，英译 R18 §2.2 `## Principles` 第 4 条（规则号 1、6、10、11、13、14、15）；每条的时机取 `shared.md` 对应编号的规则 | S-G4 | W-M1（只点名规则号，不复述） |
| `## Autonomy` `**Precedence.**` | 新写，英译 R18 §2.2 `## Autonomy` 优先级条；出处 L7 C.2 与 ADR 0032（R18 已注明是新写的工程决定）。末句的例子没有照 R18 写「`to-spec` 的产品闸门变成 `decision` 子票」：`to-spec` 只在人在场时跑（**Write a spec and tickets** 的 `**Entry.**` **Unattended.** 一行），无人会话里碰到产品闸门的是 worker，它的出路是 `decision` 子票（`implement` L23 第 3 句）。见「偏离」 | S-G4（PS mode L79–87 的粗体段首标签） | W-M2（只写对所有 playbook 成立的立场） |
| `**With the user present.**` | 新写，英译 R18 §2.2 人在场条；「which remains the user's release decision」取 `mmw-v2/skills/dispatch/references/night.md` L200「that remains the user's release decision」；`route` 按 R19 §4.7 写 `resolve-child` | S-G4 | W-G9 |
| `**Unattended.**` 第 1 句 | 新写：无人会话的判定，出处 R18 §2.2「启动提示词带 `Unattended`，或 `tool-guard.py` 拦下了一次提问」。写「marks the session unattended」而不引一个字面标记：R18 §2.3 的 worker 提示词写小写的「unattended: mmw work-a-ticket#Claim」，advisor 提示词写「Unattended per the mmw skill's ## Autonomy」，§16 researcher 写「unattended: …」，三种写法不一致，引任何一个都会让拿到另一种的 agent 认不出自己无人看守（见「没有核对的」） | S-G4 | W-G9 |
| `**Unattended.**` 第 2 句 | 搬运：`dispatch.sh` L108 `AUTONOMOUS` 常量第 2 句（R18 §2.2 最后一条：常量删掉，规则进本节） | 同上 | W-G2：这一句是理由 |
| `**Unattended.**` 第 3、4 句 | 搬运：`implement` L23 第 1、2 句，「under **Decisions I made on my own**」改为「where your role records a decision」（见改写清单第 2 条）。这是全套里唯一写「屏幕上不放问题、取最可能的选项、写一行、继续」的地方；各角色 playbook 的 `#### Unattended outlets` 只写本角色写到哪里（见 `README.md` `## 范本共用的约定` 第 3 条） | 同上 | W-G9 |
| `**Where each role records a decision.**` Worker 行（L86） | 新写：第 1 分句「Under `Decisions I made on my own` in the closing comment」英译 R18 §2.2 `## Autonomy` worker 那一条的前半「写进 closeout 的 `Decisions I made on my own`」；后半是指向 `#### Unattended outlets` in **Work a ticket** 的指针（N4）。`implement` L23 第 3 句（「… gets … `decision` … instead」）不进 mode，只在 work-a-ticket `#### Unattended outlets` 出现一次，意思保持原文的「instead」 | 规则项用粗体标签（S-P3 子项写法） | W-G9；W-G12 |
| Reviewer 行（L87） | 新写：位置「On the finding's line in the `REVIEW` report」取 R18 §7.6 `tool-guard.py` `NO_QUESTION` 行给 reviewer 的句子「at the end of that finding's line in your report」与 `mmw-v2/upstream/skills/engineering/code-review/references/session.md` L82 的 finding 行格式（一条 finding 一行，行末是 `source:`）；后半是指向 **Review a ticket** 的 `#### Unattended outlets` 的指针（R18 §3.3 P16 规则簇「拿不准时在该条末尾写 `unverified: …`」）。`session.md` L89 第 2 句搬进那份 playbook，改写见改写清单第 3 条 | 同上 | W-G9 |
| Advisor 行（L88） | 新写：位置「In your answer, beside the recommendation and the deciding risk」取 `mmw-v2/skills/advisor/references/advising.md` L19「The recommendation, the deciding risk, and what is missing」；后半按名点名 `advising.md` L18 的粗体条目（N8），不复述它 | 同上 | W-G9；W-G12 |
| Orchestrator 行（L89） | 新写：去处「In a comment on the spec」英译 R18 §6 无人表 orchestrator 行「spec 上的一条评论」（出处 `mmw-v2/skills/dispatch/references/night.md` L5「leaves its reason where that reader will look」）；后半指向 **Run a night** 的 `#### Unattended outlets`，R18 §3.3 P12 规则簇列有这一簇（`night.md` L100：没开始的票移到 `needs-triage`，在子票上评论，留给用户）。单票的 orchestrator（**Land one ticket**）没有写进这一行：R18 §3.3 P14 没有给它无人出路，也没有 spec 可以评论（见「偏离与待定」） | 同上 | W-G9 |
| Researcher 行（L90） | 新写。去处由两处来源合出，不是哪一处原文直说：R18 第 6 节采用的决定「无人：`skip:` 行与点名原则写进本 playbook 的交付物」，加上 R18 §16 P8 的第 4 步 **Answer on the ticket**（resolution comment 给出分支上的报告链接与三句结论，然后关票）与它的交付物「推送的报告、resolution comment、关闭的票」；issue #591 C 节「调研会话自己发 resolution comment（带报告路径）并关票」、D 节第 2 条（下一个推进地图的会话读关闭的调研票）说明读这条评论的是推进地图的会话与用户。选评论而不选报告文件：评论是关票时唯一必定被读到的地方，报告在 `research/<n>` 分支上，要等合并才进基线（#591 D 节第 1 条）。后半指向 **Research a question** 的 `#### Unattended outlets`：`researcher` 是脚本起的角色，那份 playbook 按 R20 5.3 写，这一簇要由写它的票补上（`README.md` `## 已知的必须改写处` 第 3 组） | 同上 | W-G9 || `**Redo or report.**` | 新写，英译 R18 §2.2 规则 11 划界条；「not yours to route around」搬运 `ui-acceptance` L36 的短语 | S-G4 | W-G3（诱惑：自己绕过去；替代动作：开 `fault` 子票） |
| `**Imported principles.**` | 新写，英译 R18 §2.2 导入原则冲突条 | S-G4 | W-M2 |
| `## Re-entry` 引导句 | 新写：R18 §2.2 节名后的括注「被唤醒、被压缩、被 `resume` 时」 | S-M1 | 无 |
| 第 1 步正文 | 搬运：`dispatch/SKILL.md` L25，逐字，句末插原则点名（T2 附加项）；第 3 句「The pipeline's commands are written to be run again.」新写，英译 R18 §2.2 `## Re-entry` 第 1 步冒号后的本地限定 | S-P3、X17 | W-P2（原则旁写本地后果） |
| 第 2 步正文 | 搬运：`dispatch/SKILL.md` L26，逐字 | 同上 | 无 |
| 第 3 步正文 | 搬运：`dispatch/SKILL.md` L27，逐字；`bash scripts/dispatch.sh` 的相对路径在 B2 后解析到 `mmw/scripts/dispatch.sh`（整目录平移，R18 §1.1），T2 第 4 种 | 同上 | W-G2（L27 第 2 句就是理由） |
| 第 4 步正文 | 新写，英译 R18 §2.2 `## Re-entry` 第 4 步；取代 `dispatch/SKILL.md` L28「Act on it, as your moment's file says.」（moment 表随 `dispatch` 解散） | 同上 | 无 |
| 四个步骤标题 | 新写：源里没有标题（R20 5.2 表「源里没有标题的才新写」）；sentence case 祈使短语（S-P3） | X17 | 无 |
| 四行 `Done when` | 新写：第 3 行取 `dispatch.sh ack` 的退出码语义；第 4 行取 R18 §7.7 `where` 的四种输出形式 | X10 | W-G7、W-O1（写脚本可观察的结果） |
| 末段（L109）第 1 句 | 新写，英译 R18 §2.2 `## Re-entry` 末段 | 无 | 无 |
| 末段第 2 句 | 搬运：`dispatch/SKILL.md` L8 第 3 句，逐字。`dispatch` 解散后，持有 `scripts/dispatch.sh` 的是 mode，这句操作规则（带理由「so no path is ever passed to it」）的去处就在这里 | 无 | W-G2 |
| 末段第 3、4 句 | 新写，英译 R18 §2.2 `## Re-entry` 末段；「that copy is the product being changed」取根 `AGENTS.md` `## Self-hosting boundary` 第 1 条「is the product being changed」。第 4 句留在 mode，与删去的两行自托管触发行（见删去的句子）情况不同：`bash scripts/dispatch.sh` 是相对路径，照 shell 的工作目录解析，任何仓库的工作树里都可能有一个 `scripts/dispatch.sh`；而任何仓库的工作树都是正在被改的产品，所以这一句在每个消费仓库都成立（推断：没有观察到误跑的运行），不是只在 MMW 仓库成立的规则 | 无 | W-G2 |
| `## Subagents` 第 1 段 | 新写，英译 R18 §2.2 `## Subagents` 第 1 条；简报首句搬运 R18 给出的英文原句，逐字 | S-B1 前置（R20 5.7 形式一） | X16 |
| 第 2 段 | 新写，英译 R18 §2.2 第 2 条；出处 `session.md` L23、L33，`to-tickets` L113、L119 | 无 | W-B3 |
| 第 3 段 | 新写，英译 R18 §2.2 第 3 条；引号内一句搬运 R18 给出的英文原句 | 无 | X16 |
| 第 4 段 | 新写，英译 R18 §2.2 第 4 条；按 D7 删去「面板角色经 `dispatch.sh panel` 另起会话」 | 无 | X16 |
| 第 5 段（L121） | 搬运：PS mode L95 第 1、2 句，第 2 句「Review the diff」改为「Read its output」（见改写清单第 8 条）；第 4、5 句不搬（见删去的句子） | 无 | W-B4 |
| `## Writing the reply` 第 1 句 | 新写，英译 R18 §2.2 第 1 条 | 无 | W-M1 |
| 第 2 句 | 搬运：PS mode L109 第 1 句，删去「, PR link as `https://github.com/<owner>/<repo>/pull/<number>`」（R18 §2.2 标注的删改；D2 删掉 PR 交付） | 无 | 无 |
| 第 3 句 | 改写：PS mode L109 第 2 句，见改写清单第 5 条 | 无 | W-G6 |
| 第 4 句 | 新写，英译 R18 §2.2 第 3 条 | 无 | W-G9 |
| `## Playbooks` 第 1 段第 1–3 句 | 搬运：PS mode L117，逐字 | S-M1（PS mode L115–117） | 无 |
| 第 1 段第 4、5 句 | 新写，英译 R18 §6「只有编号步骤（长 playbook 是 `#### Steps` 下的）进待办」与「宿主没有待办工具时，在回复开头列出步骤标题与 skip 行」 | S-O2 | 无 |
| 第 2 段第 1 句「When no playbook below fits」 | 改写：R18 §2.2 `## Playbooks` 第 3 条给出的 B1、B2 版英文原句，箭头改成条件从句（见改写清单第 9 条） | S-G5（正文段落不用箭头） | W-G9 |
| 第 2 段第 2 句「The deliverable before any code is the workflow itself.」 | 新写：逐字取 `docs/research/code-landing-refs/pstack/skills/figure-it-out/SKILL.md` L9 第 2 句的前半（冒号前）；R18 §2.2 第 3 条把这一行列为上一句的来源。`figure-it-out` 在 D7 下不导入，所以这里不是搬运，而是一行带整句的 `new`。它是上一句「before any work」的理由：先交出的是流程本身 | 无 | W-G2 |
| 第 3 段（别名） | 新写，合并 R18 §2.2 `## Playbooks` 第 2 条的五个别名为两句；「**poteto-mode** or `/poteto-mode` means this skill」逐字取 R18 | 无 | W-G6 |
| 16 行路由 | 新写，英译 R18 §3.1 表的「任务类型与用户原话」「Distinct from」两列；名字按 R19 §4.2（Define a change → Write a spec and tickets；Design an interface → Design a UI；Direct change → Make a small change；Run one ticket → Land one ticket）。用户原话由中文译成英文（SSR L78「Skill text is English」） | S-M3 路由行格式（PS mode L121–143） | R20b M7；S-G3（Distinct from 句） |
| **Onboard a repository.** 的 Distinct from | 新写：R18 §3.1 这一列是「—」。与 `setup-mmw` 区分，因为两者都是「接入、设置」类请求（推断：没有观察到混淆的运行）；`setup-mmw` 的能力取 `dispatch/SKILL.md` L3 description | S-G3 | 无 |
| **Deliver a change.** 的调用方与 Distinct from | 新写：调用方逐一点名 R18 §3.3 P5 第 4 步、P6 第 5 步、P11 第 7 步三份以 **Deliver** 收尾的 playbook（本仓库私有的 **Pull an upstream**、**Import a component** 也以它收尾，私有 playbook 不进 mode）；Distinct from 取本表 `exe-release` 行已有的 `finish` 说法与 R18 D2 的现行交付链 | S-M4（只写能核对的调用关系） | 无 |
| **Authoring or modifying a skill.** 的 Distinct from | 新写：R18 §3.1 这一列只有「B3 起 Eval」，D6 下 Eval 不在核心批次。与 **Make a small change** 区分：两者都可能是一次小改动，区别在改的是产品代码还是 agent 读的文字（推断） | S-G3 | 无 |
| 直接能力行 15 行 | 新写，英译 R18 §3.1「直接指向能力技能的行」，一个技能一行，每行用 N1 写法。`handoff`、`domain-modeling`/`codebase-design`、`wait-what` 三行从 R18 §2.2 触发表移来（见「偏离」第 1 条）；`wait-what` 一行合并了触发表「刚说的话没被理解」与 §3.1「把刚说的讲简单」两个条件 | S-M3 | S-G3 |
| 末段（私有 playbook） | 新写，英译 R18 §2.2 `## Playbooks` 第 5 条 | 无 | 无 |

## 必须改写、做不到逐字搬运的地方

1. PS mode L15、L39：「leaf SKILL.md」「leaf skill」改为「file」「principle file」。R18 §2.2 已标注，原因是 MMW 的原则是文件，不是技能。
2. `implement` L23 第 1、2 句进 `**Unattended.**`：「under **Decisions I made on my own**」改为「where your role records a decision」。原句只对 worker 成立，mode 这一段对所有无人角色成立（R18 §2.2「写一行进本角色的决定记录」）。
3. `session.md` L89 第 2 句不进 mode，进 **Review a ticket** 的 `#### Unattended outlets`。原句「When you could not tell, append `unverified: <what would settle it>` at the end of the same line.」里的「the same line」在原处指前一句所说的 finding 出处所在的行，搬走后没有所指，要写成 `replace`：新句「When you could not tell, append `unverified: <what would settle it>` at the end of that finding's line in the `REVIEW` report.」（措辞取 R18 §7.6 `NO_QUESTION` 的 reviewer 句）。写 review-a-ticket 票的人照抄这一句。
4. PS mode L109 第 1 句删去 PR 链接半句（R18 §2.2 已标注）。
5. PS mode L109 第 2 句「The per-playbook lines below name only the content unique to that playbook.」→「Each playbook's `**Reply:**` line names only the content unique to that playbook.」：在 pstack mode 里「below」指路由表下面各份的 Reply 行；MMW 的回复行在各 playbook 自己的 `**Reply:**` 里，mode 下面只有路由表，「below」没有所指。写成 `replace`。
6. `dispatch/SKILL.md` L28「Act on it, as your moment's file says.」整句替换为第 4 步新句：moment 表随 `dispatch` 解散不复存在。
7. R18 §2.2 各条都是中文，除 R18 本身给出的英文原句外，mode 里对应的句子只能英译，按新写处理。
8. PS mode L95 第 2 句「Review the diff and write your own summary, don't pass through what it said.」→「Read its output and write your own summary, don't pass through what it said.」：只读的子代理交回的是报告，不是 diff（本节第 3 段）。写成 `replace`。
9. R18 §2.2 `## Playbooks` 第 3 条的英文原句「No playbook below fits → say so, then open a todolist of the steps you will take, each naming the component it uses, before any work; the same `skip:` rule applies.」→「When no playbook below fits, say so, then open a todolist of the steps you will take, each naming the component it uses, before any work; the same `skip:` rule applies.」：箭头只用在触发行与索引行（R20 S-G5），这一段是正文段落。写成 `replace`。
10. `dispatch/SKILL.md` L23 标题 `## On waking` → `## Re-entry`：R18 §2.2 的节名，节名固定（R20 S-M1）。标题只与标题比（R21 §3.3），写成 `replace`。

## 删去的句子（写成票上 `drop` 行时用）

- PS mode L15 第 1 句「The Principles section below grounds every trigger.」：它指导「按原则找触发」这种读法；MMW 的触发行取自技能 description，不从原则推出，理由见 R18 §2.2 表的「来源」列。删后由触发行自己的条件指导。
- PS mode L17「Remaining triggers:」：依附上一句，同删。
- PS mode L95 第 3 句「Interrupt-chained resumes silently drop directives …」：它指导「续跑一个被打断的子代理」的情形。MMW 会话内的子代理是一次性的（ADR 0015），另起会话的角色被 `resume` 时由 orchestrator 重发指令（`night.md` L104）。删后由 `work-a-ticket` 的 `#### When the orchestrator resumes you` 指导。
- PS mode L95 第 4、5 句「A second opinion is the same prompt against a different model. Agreement is high-signal.」：它们指导「用另一个模型跑同一提示来取第二意见」。MMW 会话内的子代理不指定模型（本节第 4 段），这条路不存在，照做只会用同一模型跑两次还当成第二意见；「Agreement is high-signal」离开前一句没有可执行的内容。删后由 `## Non-negotiables` 的 advisor 触发行指导：一个决定的第二意见是另起会话的 `advisor`。这是对 R18 §2.2 `## Subagents` 第 5 条的偏离（R18 列出要搬这两句）。
- `AUTONOMOUS` 常量第 1 句「You are operating autonomously.」：由 `**Unattended.**` 第 1 句的判定条件代替。
- `dispatch/SKILL.md` L8 第 1 句「Choose the moment that matches your role.」：它指导按 moment 表找自己的文件；moment 表随 `dispatch` 解散。删后由 `## Playbooks` 路由与启动提示词的指针指导。
- `dispatch/SKILL.md` L8 第 2 句「Where you are is what the ticket's events say, not what this session remembers.」：它指导「从票上的事件而不是会话记忆找位置」。删后由 **principle-resume-from-durable-state** 承接（`## Re-entry` 第 4 步点名它，`where` 从事件算位置）。
- `verify-ticket/SKILL.md` L25 的结论句「Its five rules while the product is running bind every run of this skill.」不进 mode：它约束的是 `verify-ticket` 自己的运行，留在能力技能（见 `exemplars/verify-ticket/SKILL.notes.md` 改写清单第 4 条）。mode 的触发行 3 与能力技能各有一个指向 `## Five rules while the product is running` 的指针，两处都只点名、不复述规则，不算 K37 的重复；能力技能要能脱离 mode 使用（R18 §4.5 末条），所以它自己的指针要留。
- R18 §2.2 触发表最后一行（英文产物 → `unslop`）：D6 下 `unslop` 不在核心批次导入，指向它会让连线检查第 2 类失败；回复部分已在 `## Writing the reply`。英文产物的写作由 **Authoring or modifying a skill** 与 `writing-for-agents` 管。
- R18 §2.2 触发表「在本仓库、有 watch 开着 → 不运行正在被改的 MMW，不移动已安装 checkout」与「改了 `mmw-v2/upstream*/` 的文本 → 写 merge-note；让消费仓库的产物失效 → 写 downstream-note」两行：它们指导在 MMW 仓库自身工作的会话，只在那一个仓库成立，而 mode 在每个消费仓库的每个任务开头都被读（S-M2）。删后由 MMW 仓库根 `AGENTS.md` 的 `## Self-hosting boundary` 与 `## Key Conventions` 指导：在那个仓库工作的 agent 都会加载它。根 `AGENTS.md` L12 的「In particular, do not call a repo-local `dispatch.sh`, …」一句随之留在原处，不搬。
- R18 §3.1 直接能力行「顾问 → `advisor`」：它指导用户点名要第二意见的情形。删后由 `## Non-negotiables` 的 advisor 触发行与 `advisor` 自己的 description（「A second opinion on one decision …」）指导；同一技能不在 mode 里出现两次（SSR L40）。
- R18 §3.1 直接能力行里的「只有人能做的步骤 → `wizard`」：同上，由 `## Non-negotiables` 的人工步骤触发行指导。
- R18 §2.2 触发表「打开任务板、换 host/model/effort/runner → `setup-mmw`」：它是任务类型的路由，不是「不照做就出错」的情况。删后由直接能力行的 `setup-mmw` 一行指导。
- R18 §2.2 `## Autonomy` 的「产品事项清单抄一次」：D3 删去。
- R18 §2.2 `## Autonomy` 的 **principle-experience-first** 产品限定句：D6 下这条原则属 B3 按需导入，B2 不在。
- R18 §2.2 `## Playbooks` 别名「**Writing the reply** … means `shared.md` rules 4–9」：mode 本身有同名节，导入文字点名它时直接落到这一节，别名多余。
- R18 §2.2 `## Subagents` 的面板角色一句：D7。
- 路由表 P17 **Session pickup**、P18 **Pause safely**：D6 推迟到按需导入。
- R18 §2.2 触发表「同一前提下两次修复都失败 → **principle-attack-the-premise**」「一个阶段结束 → **principle-decide-at-phase-boundaries**」两行：它们指导「两次修复都失败」「一个阶段结束」这两个时刻去读对应原则。两行只把 agent 送到原则，没有本地动作或限定，条件又与 `## Principles` 索引行的「何时适用」几乎逐字相同（「Apply when two or more fixes that share one premise have failed the same gate.」「Apply when a phase of the session ends.」），同一个意思在每个任务都读的文件里写了两次（SSR L40；R20 S-M2 按行计成本）。删后由 `## Principles` 的两条索引行指导。留下的只指向原则的触发行（被拒绝、人工步骤、凭据）各带一个本地动作或限定。
- `dispatch/SKILL.md` L23 的节名 `## On waking` 见改写清单第 10 条（改名，不是删除）。

## 与 R18 的偏离与待定

- **每个技能在 mode 里只出现一处**（R20 S-M2、SSR L40 Duplication）。R18 §2.2 的触发表与 §3.1 的直接能力行把 `setup-mmw`、`advisor`、`wizard`、`handoff`、`wait-what` 各写了两次。范本的分法：`## Non-negotiables` 只留不照做就会出错的时刻（关票、被拒绝、产品与端口、oracle 输出行、screen contract、advisor、合并、人工步骤、自建 worktree、凭据、pstack 名字、流水线故障、rebase）；任务类型的路由（交接、用词、说清楚、换模型、开任务板）归 `## Playbooks` 的直接能力行。原则也只出现一处：只指向原则、不带本地动作的触发行（前提、阶段边界）删去，由 `## Principles` 索引行承担。
- **R18 §2.4 B2 行说触发行「加上三行」（`setup-mmw`、`orchestrator-events.md`、`ticket.py`）**，但 §2.2 表里没有 `orchestrator-events.md` 那一行的原文。范本不写这一行：orchestrator 被唤醒时由唤醒行的指针进入 `run-a-night` 或 `land-one-ticket` 的 **Handle each wake**，那一步点名 `references/orchestrator-wakes.md`（R19 §4.5 改名）。`setup-mmw` 按上一条放在直接能力行。写 B2 票的人需要确认这一处。
- **advisor 的 Distinct from**：R18 写「Distinct from `interrogate`」，`interrogate` 是 pstack 技能，D6 下不导入。advisor 现在只有 `## Non-negotiables` 一行，触发行格式不带 Distinct from（S-M3），不再写。
- **`**Where each role records a decision.**` 比 R18 §2.2 多两行**：R18 §2.2 只列 worker、reviewer、advisor。night orchestrator 的去处 R18 第 6 节已给出（spec 上的一条评论），researcher 的去处由 R18 第 6 节与 §16 P8 合出（逐段来源 Researcher 行）。两行都指向还没有范本的 `#### Unattended outlets`：**Run a night** 的那一簇 R18 §3.3 P12 已列出，**Research a question** 的那一簇要由写它的票补上。
- **单票 orchestrator 的无人出路没有定**：R18 §3.3 P14 **Land one ticket** 没有规则簇，第 6 节 orchestrator 行说的是 spec 上的评论，而单票没有这次运行的 spec。写 B2 **Land one ticket** 票的人要定去处（候选：票上的一条评论），定下后在 mode 的 Orchestrator 行补上。
- **`**Precedence.**` 的例子与 R18 不同**：R18 §2.2 举「`to-spec` 的产品闸门在无人会话里变成 `decision` 子票」。`to-spec` 只在 **Write a spec and tickets** 里跑，那份 playbook 只在人在场时跑；无人会话遇到产品闸门的是 worker，所以例子改成 worker 开 `decision` 子票。
- **Reviewer 行指向的 `#### Unattended outlets` in **Review a ticket** 还没有范本**；那一簇的句子见改写清单第 3 条。
- **长度**：167 行，R18 §2.2 估计 B2 后约 170 行，R20 S-G9 同。直接能力行拆成一技能一行后多了 8 行，删去 MMW 仓库专属的两行与重复的五处后少了 6 行；删去只指向原则的两行触发行、加上 orchestrator 与 researcher 两行去处，行数不变。
- **「Claude Design」**：路由行 **Design a UI** 用了产品名 Claude Design。它不是宿主名，但 SSR L120 的 grep 会命中 `claude`；现行 `design-pages` 已这样写，结构 lint 的 `host-name` 规则要为这个产品名留例外（R20 K10）。
- **直接能力行没有逐行写 Distinct from**。R20 5.1 表要求「每行一句 Distinct from」，R18 §3.1 末行本身也没有写。范本只在有近邻会被混淆的行写（`exe-release`、`design-pages`）；其余 13 行是否要补，由写 B1 mode 票的人决定，补的话出处写各技能 description。

## 没有核对的

- 14 条 pstack 原则的 H1 与 description 已逐条从快照读出；MMW 自有 12 条原则只有 `principle-silence-is-never-a-pass` 写了范本，其余 11 条的显示名与「何时适用」是草稿，写原则票时以原则文件为准，由连线检查第 5 类核对（R20 K11）。
- `teach`、`grill-me`、`wait-what`、`handoff` 今天都在 `mmw-v2/skills.txt`（L28–33，本轮核对）；B1 以后是否仍装，照 R18 §3.1 写，没有另查。
- 这份 mode 对 agent 行为的作用没有实测（R20 第 8 节「未经验证的」）。
- 无人会话的标记在三种启动提示词里写法不一：R18 §2.3 worker 行「unattended: mmw work-a-ticket#Claim」、advisor 行「Unattended per the mmw skill's ## Autonomy」、§16 researcher「unattended: mmw research-a-question#Name the decision」。mode 因此写「marks the session unattended」。R18 §2.3、§16 与 `dispatch.sh` 的提示词模板要统一成一种写法，由写 B2 启动提示词的票定；定下之后 mode 可以逐字引用它。
