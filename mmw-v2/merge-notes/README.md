# merge-notes

两个上游 subtree 里被我们改过的技能，每个一份说明：改了哪几段、为什么改、上游再动这几段时怎么取舍。
给的是**意图**，不是 diff——diff 用 `git diff <上一个 Squashed 提交>:skills/<类别>/<技能> HEAD:mmw-v2/upstream/skills/<类别>/<技能>` 看（squash 提交的树根是上游仓库根，没有 `mmw-v2/upstream/` 前缀；上一个 Squashed 提交用 `git log --oneline --grep "Squashed 'mmw-v2/upstream/'"` 找）。
反方向——本仓库改了、consuming repository 里哪些产物作废——是 downstream-note，见 [`../downstream-notes/README.md`](../downstream-notes/README.md)。

## 上游更新时怎么用

1. 拉对应的 subtree。mattpocock 的：
   `git subtree pull --prefix mmw-v2/upstream https://github.com/mattpocock/skills main --squash`
   `diagram-design` 自己一个，命令写在它的说明里。
2. 每个冲突文件，打开它所属技能的说明，对着冲突段落找到对应条目，按条目里的取舍规则决定留谁。
   说明里没覆盖的段落：我们没改过，取上游。
3. 解完：通读该技能的 `SKILL.md` 及其 reference 一遍，确认没有互相矛盾的句子；跑 `bash mmw-v2/install.sh --check`。
4. 上游把我们引用的文件改名、合并或拆分时，更新说明里的段落定位。

## `disable-model-invocation`

`SKILL.md` frontmatter 的 `disable-model-invocation: true`（Claude Code 读）与 `agents/openai.yaml` 的 `policy.allow_implicit_invocation: false`（Codex 读）说的是同一件事：这个 skill 只有 user 点名才触发。两处同增同删——只动一处，同一个 skill 在一半 host 上是 user 触发、在另一半是模型可触发。

两个 subtree 装进来的 skill 默认让模型可触发：user 漏说技能名时，agent 自己认得出该用它。本仓自研的技能不归这里管，取舍登记在根 `CONTEXT.md` 的 `SKILL.md` 条目。两行都留着的只有 `setup-matt-pocock-skills`、`grill-me`、`handoff`、`wait-what`。上游改这两行 → 本仓的取舍不变，两处一起跟。

下面每份说明只写它那个 skill 站在哪一边，不复述这条规则。

## host 中立

十二份装了的上游技能，正文原来按一家 host 说话：`the Skill tool` 这个工具名，和 `/名字` 这种斜杠调用。根 `AGENTS.md` 的第一条约定与根 `CONTEXT.md` 的 `host neutrality` 条目要求同一件事——一份 `SKILL.md` 对所有 host 是同一份，不把任何 host 当默认或首选，不按 host 名分支，能力差异用按能力判断的自然语言写。没有那两样东西的 host 上，读到 `call the Skill tool with "codebase-design"` 的 agent 只能猜：跳过这一句，或者去找一个不存在的工具；读到 `` tell the user to run `/setup-matt-pocock-skills` `` 的 agent 会把这一串原样打给用户，而用户敲它什么也不会发生。

三种替换写法，按那一句自己想要什么分，不按它提到了谁：

- **要词汇、要就地照办**：写成 `` read the `<X>` skill's `SKILL.md` `` 加一句读它干什么。判据在 `tdd/SKILL.md` 自己的话里：`it is a reference to consult, not a session to run`。
- **要另一个上下文**：写成 `` ask for your host's own general-purpose subagent and have it use the `<X>` skill ``。措辞取自根 `CONTEXT.md` 的 `subagent` 条目：`a skill that needs one asks for the host's own general-purpose subagent`。不写工具名——「use the Task tool」和 `the Skill tool` 是同一个毛病换件衣服。
- **会话管理命令**（只有 `/clear` 与 `/compact` 两个，它们不是技能）：写成那个动作本身，并在那份文件里只写一次这句能力说明：`Emptying a session's context and compressing it into a summary both exist on every host, under a different name on each; use the one your host gives you.`

技能名的散文写法由根 `CONTEXT.md` 的 `skill` 条目定死：`` A skill is named by its directory name; `the X skill` in prose, never `/X`. ``

**上游把某一段改回工具名或斜杠命令 → 收上游对那一段其余部分的措辞，按能力说话这一层不收回去。** 下面每份说明只写它那个技能改了哪几段，不复述这三条。

一处已知偏差，记录，不修，不加守卫：`mmw-v2/upstream/CONTEXT.md` 举的 label 例子是 `ready-for-afk`，而本仓库的 label 是 `ready-for-agent`。约定明写 `mmw-v2/upstream/` 自己的 `AGENTS.md`、`CLAUDE.md`、`CONTEXT.md` 原样不动，所以这处偏差留着。不加守卫的理由是三样现有的东西已经拦住一个 agent 真去打这个 label：根 `CONTEXT.md` 的 `label` 条目写 `No new label is added`；`docs/agents/triage-labels.md` 是 `triage` 与 `to-tickets` 唯一的 label 来源；`verify-ticket.py --closeout` 是流水线里唯一改 label 的一步，而 `hook.py pretool` 拦下把票挪出 agent 队列的那两条命令。一个打错的 label 不会让票进队列，也不会让它关掉，靠的是它不等于 `ready-for-agent`。这一条写在这里，是为了让下一次拉 upstream 的人不要把它当成本仓库的疏漏去「修」。

## 目前有说明的技能

- [ask-matt](ask-matt.md) — `engineering/ask-matt`
- [code-review](code-review.md) — `engineering/code-review`
- [codebase-design](codebase-design.md) — `engineering/codebase-design`
- [domain-modeling](domain-modeling.md) — `engineering/domain-modeling`
- [grill-with-docs](grill-with-docs.md) — `engineering/grill-with-docs`
- [implement](implement.md) — `engineering/implement`
- [improve-codebase-architecture](improve-codebase-architecture.md) — `engineering/improve-codebase-architecture`
- [prototype](prototype.md) — `engineering/prototype`
- [resolving-merge-conflicts](resolving-merge-conflicts.md) — `engineering/resolving-merge-conflicts`
- [to-spec](to-spec.md) — `engineering/to-spec`
- [to-tickets](to-tickets.md) — `engineering/to-tickets`
- [setup-matt-pocock-skills](setup-matt-pocock-skills.md) — `engineering/setup-matt-pocock-skills`
- [tdd](tdd.md) — `engineering/tdd`
- [triage](triage.md) — `engineering/triage`
- [wayfinder](wayfinder.md) — `engineering/wayfinder`
- [wizard](wizard.md) — `engineering/wizard`
- [grill-me](grill-me.md) — `productivity/grill-me`
- [handoff](handoff.md) — `productivity/handoff`
- [teach](teach.md) — `productivity/teach`
- [to-questionnaire](to-questionnaire.md) — `productivity/to-questionnaire`
- [wait-what](wait-what.md) — `productivity/wait-what`
- [writing-for-agents](writing-for-agents.md) — `productivity/writing-for-agents`
- [diagram-design](diagram-design.md) — `mmw-v2/upstream-diagram-design/`，另一个上游、另一个 subtree
