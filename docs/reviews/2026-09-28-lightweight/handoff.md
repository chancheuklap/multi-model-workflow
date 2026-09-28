# handoff

## 定稿（主 agent 复核）

**判断**：本仓只改了一个词组，与上游逐字相同，不改。可选的补句（交接文档优先写只存在于对话里的东西）不加：唯一一份真实的交接文档在没有这句的情况下也写对了。

另外记一件与文本无关的事：本机的 `orca-cli` 技能会抢走"handoff"这个口语说法。想写交接文档时，要点名 `handoff` 技能。

## 结论
`mmw-v2/upstream/skills/productivity/handoff/SKILL.md` 共 135 词（含 frontmatter），另有 `agents/openai.yaml` 13 词，没有脚本、没有 reference。本仓对上游只改了一处：`Include a "suggested skills" section …` 句尾的 `call the Skill tool for` 换成 `reach for`（host 中立，见 `mmw-v2/merge-notes/handoff.md`）。对照上一个上游 squash 提交 `5b1a4c51`，以及 2026-09-28 取到的 mattpocock/skills `main` 上的当前原文，除这一处外两者逐字相同。技能正文里没有可删的内容：五句话都是目标或防误用，没有流程、没有复述脚本。“灵魂”基本完整。只有一个可选补充：告诉 agent，文档应该优先写只存在于对话里的东西。按用户“上游原文尽量不改”的裁定，这一条建议先不加。

## A. 删除或改成脚本
无。五句正文逐句核对：
- 每句都在规定产出物是什么、给谁看、放在哪里、不写什么；
- 没有复述脚本，也没有写历史；
- `Redact any sensitive information …` 看似 agent 默认就会做，但这份文档本来就是要带去别的 host 或交给别人的，这一句是 `SKILL-SET-REVIEW.md` `### Redundancy and bloat` 说的“a sentence that prevents a known misuse”，留着。

## B. 灵魂
### 保留，勿删
- `SKILL.md` 第一句 `… so a fresh agent can continue the work.`：规定了读者是谁（一个什么都不知道的新 agent），也规定了完成标准（它能接着干下去）。其余每句都从这里推出来。
- `SKILL.md` `Do not duplicate content already captured in other artifacts (specs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.`：这是整个技能里唯一讲“取舍”的一句。文档只装对话里独有的东西，其余指向真正的来源；来源以后会变，抄一份进来的会过期。
- `SKILL.md` `Save to the temporary directory of the user's OS - not the current workspace.`：防止交接文档作为一个多出来的文件落进仓库或 ticket worktree。
- `SKILL.md` `Include a "suggested skills" section …`：在 MMW 里，下一个 agent 冷启动，面对 `mmw-v2/skills.txt` 里三十多个技能。点名该用哪几个技能，就是在给它指路。唯一一份真实交接文档 `docs/research/mmw-structure/2026-09-06-handoff.md`（提交 `9f4efc97`）的 `## 六、建议下一个 agent 调用的技能` 还写了“不要调用 `dispatch` 或 `verify-ticket`”。可见这一节在实际使用中也用来写“哪些技能不该用”。
- frontmatter `argument-hint` 与末句 `If the user passed arguments …`：让用户用一句话决定文档往哪个方向裁剪。

### 缺口与补充草稿
- `SKILL.md` 第一句之后，属于可选补充，优先级低。`summarising the current conversation` 可能让 agent 写成按时间顺序的经过回顾。对新 agent 最值钱的其实是四样东西：已经做出的决定和理由、已被否掉的路线和否掉它的证据、用户立下的判据、还没决定的问题。
  - 证据：`docs/research/mmw-structure/2026-09-06-handoff.md` 自己就是按这几样组织的，有 `## 二、已经被否掉的方案，以及否掉它们的证据`、`## 四、还没裁的一个矛盾`、`## 五、用户在这场讨论里立下的判据`、`## 七、动手前必须知道的一个约束`。也就是说，写它的 agent 没有这句提示也做对了。
  - 所以这个缺口还没有造成过失败。建议等真的出现一份写得很浅的交接文档，再加这一句，并在 `mmw-v2/merge-notes/handoff.md` 记一行。它和“上游原文尽量不改”的裁定有冲突，以裁定为准。
  > The next agent can read every artifact; it cannot read this conversation. Spend the document on what only the conversation holds: what was decided and why, what was tried or ruled out and the evidence against it, the criteria the user set, and what is still open. A recap of events that leaves these out sends the next agent down paths already closed.

## C. 死板的流程
无。技能里没有编号步骤、没有模板、没有固定结构。文档写成什么形状完全交给 agent。

## 脚本
无。

## 与其他技能的重复或交接问题
- 什么时候该用 `handoff`，写在 `mmw-v2/upstream/skills/engineering/ask-matt/SKILL.md` `## The main flow: idea → ship` 第 2 步和 `## Phase boundaries` 的 `**Handoff**` 一条，以及 `ask-matt/PHASE-BOUNDARIES.md` 的 `**3. Do you need to hand off?**`（new host、new directory、colleague、mid-phase fork）。`handoff` 的 description 曾写过同样的触发条件，在 `c9f4e5c7` 里改回了上游原文。`handoff` 是用户点名才触发的技能，“何时用”本来就该由路由技能 `ask-matt` 来讲，两边现在没有重复，保持现状。
- `mmw-v2/merge-notes/handoff.md` 第一行（`disable-model-invocation`）把另外六个同类技能重新列了一遍。同样的名单还出现在 `mmw-v2/merge-notes/README.md` `## disable-model-invocation`，以及 `grill-me.md`、`grill-with-docs.md`、`teach.md`、`improve-codebase-architecture.md`，一共六处。README 同一节自己写着“下面每份说明只写它那个 skill 站在哪一边，不复述这条规则”。这属于维护文档里的冗余（第 6 类），不影响任何 agent 的行为。建议只在 README 保留这份名单，五份说明里删掉“另六个是 …”的括号。剩余风险：没有；将来新增第八个这样的技能时，只需改 README 一处。
- 本机另装了一个非 MMW 技能 `orca-cli`（`~/.claude/skills/orca-cli`），它的 description 会在用户说出 “handoff” / “handover” 时触发。`handoff` 对模型不可见，所以用户用自然语言说“做个 handoff”而不点技能名时，会被路由到 `orca-cli`，也就是把工作交给另一个 worktree 的终端，和写交接文档是两回事。这里只做记录，不是 MMW 能改的东西。用户想要交接文档时，点 `handoff` 技能名即可。

## 没查到的
- `docs/research/mmw-structure/2026-09-06-handoff.md` 是否真由 `handoff` 技能写成：从它有“建议下一个 agent 调用的技能”一节推断是，但没有找到会话记录来证实。这份文档被存进仓库并提交了，没放在临时目录。这是用户的选择，不算技能的缺陷。
- 没有查各 host 的会话日志，所以不知道这个技能被调用过多少次。
- `agents/openai.yaml` 在 Codex 上的实际表现没有实测。
