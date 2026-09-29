# 范本（exemplars）

这个目录放五份写好的技能文本范本，每份旁边一份 `.notes.md` 注解。它们是 MMW 架构升级（`../reports/R18-mmw-architecture-v2.md`，第 17 节 D9）里「搬文字的票」的基准：票上的搬运清单照注解写，worker 照范本写。写法规则本身在 `../reports/R20-writing-style-guide.md`，名字在 `../reports/R19-naming-table.md`；范本是这两份规则落到真实文本上的样子。范本不安装，目录位置也不是落地后的安装位置（落地位置见各注解开头）。

## 五份范本是什么

| 范本 | 组件类型 | 对应 R18 | 套的 R20 模板 | 主要示范什么 |
|---|---|---|---|---|
| `mmw/SKILL.md` | mode（技能名 `mmw`，R18 第 17 节 D10） | §2 | 5.1 | 触发行、原则索引、`## Autonomy` 各角色的去处、`## Re-entry` 的编号步骤、路由表与直接能力行 |
| `mmw/playbooks/write-a-spec-and-tickets.md` | 白天 playbook，长形态 | §3.3 P1 | 5.2 长形态（另带事实表式 `**Where you are.**`） | 转交步骤、`(judgement)` 步骤、跨会话的事实表、从能力技能 reference 整份搬来的规则簇 |
| `mmw/playbooks/work-a-ticket.md` | 角色 playbook（worker） | §3.3 P15 | 5.3 | 步骤只留动作、闸门与 `Done when`，成段规则进规则簇；`#### Unattended outlets`；唤醒与重入 |
| `mmw/principles/principle-silence-is-never-a-pass.md` | MMW 自有原则 | §5.2 第 1 行 | 5.4 | 固定标签、每句跨任务成立、中文 ADR 只能翻译时怎样登记 |
| `verify-ticket/SKILL.md` | 能力技能（剥离流程之后） | §4.1 verify-ticket 行 | 5.5 分支型 | 目标段、`## Pick a branch`、「结果 → 做什么」的退出码写法、`## Output`、`## Composing this skill` |

## 怎样作为票的基准使用

1. **注解就是搬运清单的草稿。** 注解的四张表对应票上 `## Moves`（R21 §3.2）的几种行：
   - `## 逐段来源` 里标「搬运」的 → `move` 或 `copy` 行（源文件与行号已写出；「copy」的写明原处保留）。
   - 标「新写」的 → `new <目标> "<整句>"` 行。整句就是范本里那一句，逐字抄；出处列就是票上要写的出处（R20 T5）。
   - `## 必须改写、做不到逐字搬运的地方` → `replace` 行，原句与新句都已写出（R20 T3）。
   - `## 删去的句子` → `drop` 行，已写出它原本指导的情况与删后由什么指导（R20 T9）。源范围里的标题也是单元（R21 §3.3 只拿标题与标题比），删掉的标题同样逐个写 `drop`，改名的标题写 `replace`。
   - `## 全文通用的机械改名`（只有 `work-a-ticket` 有）→ 票上的 `rename` 行，取自 R19 第 7 节；表里标明「整句 `replace`」的（脚本拆分）不走 `rename`，逐句列在改写清单里。
   - 「来源」列写「翻译」或「改写」的行：翻译的句子是带整句的 `new` 行；改写的句子是 `replace` 行，原句与新句在改写清单里。
   - 注解说「copy」的，原处保留；没说的都是 `move`。同一个源句只搬运一次：两处都要用时，一处 `move`，另一处写成指针或带整句的 `new`。
2. **写票的人照抄，不重写。** 首段、立场句、`**Why:**`、`Done when`、`**Reply:**`、连接句这些承载理解的位置，范本已经写成整句；票上用带整句的 `new` 行，worker 不自行起草（R20 T5「谁起草」）。只有范本没有覆盖的文件，才用不带整句的 `new <目标>`，并在票上点名范本里对应的段落，让 worker 照那段的写法写。
3. **结构不交给 worker。** 节的顺序、步骤怎样切、哪些句子进规则簇，范本已经定了（例：`mmw/playbooks/work-a-ticket.notes.md` `## 结构决定：步骤只留动作、闸门与 \`Done when\``）。worker 改结构，就是票上没有的改动。
4. **范本之外的同类文件照同一种写法。** 例如 `review-a-ticket`、`run-a-night`、`land-one-ticket`、`research-a-question`（`researcher` 是脚本起的角色，R20 5.3）照 `work-a-ticket`；其余白天 playbook 照 `write-a-spec-and-tickets`；其余 11 条 MMW 原则照 `principle-silence-is-never-a-pass`；其余剥离后的能力技能照 `verify-ticket`。
5. **注解里的「推断」与「没有核对的」是未满足的验收项。** 写票时，这些条目要么在切票会话里核实掉，要么在票上写成一条验收项，不能当成已知事实往下传（`shared.md` rule 4）。

## 注解怎么读

每份注解都有下面这些节，顺序相同；标「可选」的只在有内容时出现：

- 开头：这份范本对应 R18 的哪一节、名字按 R19 的哪一条，以及缩写表。mode 的注解另有 `## 名字` 一节（技能名的决定出处）。
- 可选的结构节：`work-a-ticket` 的 `## 结构决定：步骤只留动作、闸门与 \`Done when\``、`write-a-spec-and-tickets` 的 `## 用的是哪种骨架`、`verify-ticket` 的 `## 主形态`，写范本为什么是这个骨架。
- 可选的 `## 全文通用的机械改名`：对应 `rename` 行（见上一节第 1 条）。
- `## 逐段来源`：一行一段（或一句）。「来源」列写搬运还是新写、源文件与行号、做了什么改写；「结构依据（pstack）」列写 R20 的结构规则号（S-、X-）与它背后的 pstack 文件；「写法依据（mattpocock）」列写 R20 的写法规则号（W-）与它背后的 mattpocock 原文。行号都是相对仓库根目录的路径加行号；报告内的规则号（T、S、W、N、K、X）指 R20 的对应条目。
- `## 必须改写、做不到逐字搬运的地方`：每条写原句、新句和理由。
- `## 删去的句子`：每条写被删的句子、它原本指导的情况、删后由什么指导。
- `## 与 R18 的偏离`（mode 与 `verify-ticket` 的注解写作 `## 与 R18 的偏离与待定`，多列几条等别的票定的事）：范本没有照 R18 写的地方和理由。写票的人以范本为准，除非用户另有决定（R18 第 17 节 D9 定范本是票的基准）。
- 可选的长度节（`## 长度`、`## 长度与审查提示`）：行数或词数与 R20 S-G9 的参照。
- `## 没有核对的`：本轮没有读到或没有实跑的部分。

「推断」表示这一句的依据是推理，不是读到的原文或观察到的运行。

## 范本共用的约定

这几条是五份范本一致执行的做法，现在都写进了 R20，规则本身以 R20 为准；这里只列对应的规则号，并说明范本里的实例在哪。

1. **脚本的写法**：R20 N9。实例：`work-a-ticket` 的「Commands of … are named bare below.」一句，`write-a-spec-and-tickets` 第 8 步的「the `verify-ticket` skill's `python3 scripts/verify-ticket.py <spec> --lint`」。
2. **`(judgement)` 的位置**：R20 S-P7。标记写在粗体标题之后，按 R21 §3.3 的切分属于标题之后的第一句，所以那一句不再是逐字搬来的句子：注解的改写清单把标记写进 `replace` 的新句（`write-a-spec-and-tickets` 第 2 条、`work-a-ticket` 第 6 条）。
3. **无人出路的分工**：R20 W-O3（W-G9 指向它）。实例：mode `**Where each role records a decision.**` 与 `work-a-ticket` 的 `#### Unattended outlets`。
4. **子票叫 child**：R20 N11。
5. **`shared.md` 的叫法**：R20 N12。实例：mode `**User rules.**`。
6. **白天长 playbook 的事实表式 `**Where you are.**`**：R20 S-P6。实例：`write-a-spec-and-tickets`。
7. **`**Entry.**` 每个入口一行、粗体标签的列表**：R20 S-P8。实例：两份 playbook 范本。
8. **规则簇的顺序**：R20 S-O3。先是步骤点名的簇，按第一次点名的顺序（`#### Unattended outlets` 也在其中）；然后是 `roles.json` 登记的唤醒处理簇。实例：`work-a-ticket`。

## 已知的必须改写处

### 第 1 组：范本之外、要改别的文件的地方

R20 要补的已补（上一节各条的规则号；R20 `## 审查记录` 第 18 条）。下面是本轮没有改、要由别的票或下一次改报告时改的：

1. **R19 与词表的 `several-specs.md`**：范本照 R18，这份文件整份并入 **Write a spec and tickets** 的 `#### Several specs from one reference`（`mmw/playbooks/write-a-spec-and-tickets.notes.md` 开头）。R19 §4.5 第 189 行的改名行、§7 第 375、383 行的 `path` 与 `token` 行要删去，改记为「并入 playbook 规则簇」；`docs/contexts/tickets/CONTEXT.md` L73 **spec division** 的 `_Home_` 改为 `to-spec` 分叉的 `## Process` 加那个规则簇。
2. **R21 的 mode 目录名**：R21 L29、L107、L294 仍写「`mmw` 还是 `mmw-mode` 等用户拍板」，`MODE_DIR` 要定为 `mmw`（R18 D10）。
3. **R21 §4.2 `step-names-component`**：要认 R20 S-P7 的位置（粗体标题之后的 `(judgement)`），不要求它是正文第一个词之前的独立单元。
4. **R21 §4.2 `numbered-cross-reference`**：现在的模式（`step \d+`、`## \d+`、`closing step \d`、`Phase [A-Z]`）认不出「rules 3 and 4 of the `ui-acceptance` skill's …」这种跨文件按编号引用规则的写法。范本已改成按内容与簇名引用；模式是否加 `rules? \d`，由写这道检查的 B0 票定。
5. **无人会话的标记**：R18 §2.3 的 worker 行写「unattended: …」，advisor 行写「Unattended per …」，§16 researcher 写「unattended: …」。R18 与 `dispatch.sh` 的提示词模板要统一成一种；mode 现在写「marks the session unattended」，统一后可以逐字引用（`mmw/SKILL.notes.md` `## 没有核对的`）。
6. **词表里的 child**：R20 N11 定了「child」的用法；`docs/contexts/tickets/CONTEXT.md` 的 **sub-issue** 条与 ticket-run 的 child kind 条要写明两者的分工，由改词表的票做。

### 第 2 组：各范本的「必须改写」条目（逐条原句与新句在各注解里）

| 注解 | 条数 | 主要种类 |
|---|---|---|
| `mmw/SKILL.notes.md` | 10 | pstack 原句里只对 pstack 成立的词（leaf skill、PR 链接、`below`、`Review the diff`）；`implement` 句子搬到对所有角色成立的位置；`session.md` 的「the same line」搬走后没有所指；正文段落的箭头改成条件从句；`## On waking` 改名 `## Re-entry` |
| `mmw/playbooks/work-a-ticket.notes.md` | 23 | 脚本拆分后的整句 `replace`（`verify-ticket.py` → `ticket_state.py`，逐句列出）；按编号引用改为按标题或簇名引用；搬走后失去所指的「Then」「as above」「these readers」；「sub-issue」改「child」；`gh api` 查询换成 `issue_tree.py`；Memory 索引改在 `Data:` 文件里；带 `(judgement)` 的新句；`## After the closeout` 改名为簇名 |
| `mmw/playbooks/write-a-spec-and-tickets.notes.md` | 11 | 问句改成带 `(judgement)` 的祈使句；去掉「Branch:」标签后「the branch」改「the answer」；「this skill」改为点名 playbook；`triage` L82 两条路都保留；「the one judgement」改「a judgement」；`### Context hygiene` 改名 `#### Session boundaries` |
| `mmw/principles/principle-silence-is-never-a-pass.notes.md` | 4（另 5 句只能翻译） | 中文 ADR 0008 的五句只能译成英文；界面与票的专有词换成通用词，原句留在 `ui-acceptance` 作本地后果 |
| `verify-ticket/SKILL.notes.md` | 6 | 剥离后不再写事件、不再关票；分支表逐格改写；脚本 docstring 与退出码说明改成「结果 → 做什么」，逐句列出（票上是带整句的 `new` 行） |

### 第 3 组：仍待写 spec 的人决定，或要在票上写成验收项的事

1. **`review-a-ticket`、`run-a-night`、`research-a-question` 的 `#### Unattended outlets` 还没有范本。** mode 的 Reviewer、Orchestrator、Researcher 三行已经指向它们。Reviewer 那一簇的句子（`session.md` L89 第 2 句的 `replace`）写在 `mmw/SKILL.notes.md` 改写清单第 3 条；Orchestrator 那一簇的内容 R18 §3.3 P12 已列（`night.md` L100）；Researcher 那一簇 R18 §16 P8 没有列，写 **Research a question** 票的人要按 R20 5.3 补上，内容是「写进 resolution comment」（去处的来源见 `mmw/SKILL.notes.md` 逐段来源 Researcher 行：R18 第 6 节加 §16 P8 第 4 步与交付物、issue #591 C 节）。
2. **单票 orchestrator（**Land one ticket**）的无人出路没有定。** R18 §3.3 P14 没有规则簇，第 6 节 orchestrator 行说的是 spec 上的评论，而单票没有这次运行的 spec。写 B2 **Land one ticket** 票的人定去处，定下后补进 mode 的 Orchestrator 行；在那之前，它是 B1 mode 票上一条未满足的验收项。
3. **自己拿起的票的 Memory 索引从哪来**，是 B2 的工程决定，不等用户：`work-a-ticket` 的 `#### Memory while working` 说 Memory 索引在启动提示词的 `Data:` 文件里，而 R18 §2.3 只为 `start` 定义了数据文件，`adopt` 会话没有启动提示词。建议的做法是 `adopt` 也写一份 `prompts/<n>-adopting-worker.md` 并把路径打印给会话；写 B2 `adopt` 票的人把它写成一条验收项。
4. **「a UI difference never goes here: it is a `contract` child」的去处是推断，来源不能定。** issue #73 正文（`gh issue view 73`）只写「UI 差异不走这里」，没有去处；首次写进这半句的提交 `d541e10e` 与 `mmw-v2/merge-notes/implement.md` 都没有写理由。唯一的依据是 `implement` L22（**Read first** 下的 baseline 不成立 → `contract` 子票）。写 spec 的人把它列为一条开着的验收项，请用户确认；不确认就改成只登记删除这半句的 `drop`（`work-a-ticket.notes.md` 改写清单第 21 条）。
5. **`issue_tree.py` 会列出所有子票**，`work-a-ticket` 第 2 步要的是开着的。是否加只列开着的开关，由拆分 `verify-ticket.py` 的票决定。
6. **`verify-ticket` 的 `--drafts` 部分发布后的出路**（移走已发布的草稿、改 `BLOCKED BY:`、手动补边）是读代码得出的，没有实跑过。拆分票若给脚本加「跳过已发布」的能力，这一段改成点名那个开关。
7. **`ticket_state.py`、`dispatch.sh where` 还不存在**；两份夜间范本里它们的开关与退出码沿用今天 `verify-ticket.py` 的行为，是推断。`--closeout` 按步骤标题核对 `skip:` 行也还没有实现，但它已由 R18 第 6 节定下（B2 只报告，B3 起拒绝），不是待决定的事：`work-a-ticket` `#### Unattended outlets` 第 2 段在 B2、B3 都成立，写 B2 `ticket_state.py` 票时把这项核对列为它的依赖。
8. **五份范本都没有实测**对 agent 行为的作用（R20 第 8 节）。按 `SKILL-SET-RULES.md` 的 `## Verifying`，应当让一个只拿到触发与真实任务的新 agent 各跑一次。
