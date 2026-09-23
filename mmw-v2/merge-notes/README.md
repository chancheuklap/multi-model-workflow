# merge-notes

三个上游 subtree 里被我们改过的技能和脚本，每个一份说明：改了哪几段、为什么改、上游再动这几段时怎么取舍。
给的是**意图**，不是 diff——diff 用 `git diff <上一个 Squashed 提交>:skills/<类别>/<技能> HEAD:mmw-v2/upstream/skills/<类别>/<技能>` 看（squash 提交的树根是上游仓库根，没有 `mmw-v2/upstream/` 前缀；上一个 Squashed 提交用 `git log --oneline --grep "Squashed 'mmw-v2/upstream/'"` 找）。
反方向——本仓库改了、consuming repository 里哪些产物作废——是 downstream-note，见 [`../downstream-notes/README.md`](../downstream-notes/README.md)。

## 上游更新时怎么用

1. 拉对应的 subtree。mattpocock 的：
   `git subtree pull --prefix mmw-v2/upstream https://github.com/mattpocock/skills main --squash`
   `diagram-design` 和 `unlazy` 各自一个，命令写在各自的说明里。
2. 每个冲突文件，打开它所属技能的说明，对着冲突段落找到对应条目，按条目里的取舍规则决定留谁。
   说明里没覆盖的段落：我们没改过，取上游。
3. 解完：通读该技能的 `SKILL.md` 及其 reference 一遍，确认没有互相矛盾的句子；跑 `bash mmw-v2/install.sh --check`。
   `unlazy` 不是技能，换成：读上游对说明里每个段落的 diff，没冲突的也读——一条自动合进来的上游条件就能悄悄撤掉我们的改动；再跑 `bash mmw-v2/tests/verify-ticket/run.sh`。
4. 上游把我们引用的文件改名、合并或拆分时，更新说明里的段落定位。

## `disable-model-invocation`

`SKILL.md` frontmatter 的 `disable-model-invocation: true`（Claude Code 读）与 `agents/openai.yaml` 的 `policy.allow_implicit_invocation: false`（Codex 读）说的是同一件事：这个 skill 只有 user 点名才触发。两处同增同删——只动一处，同一个 skill 在一半 host 上是 user 触发、在另一半是模型可触发。

mattpocock 和 diagram-design 两个 subtree 装进来的 skill 默认让模型可触发：user 漏说技能名时，agent 自己认得出该用它。本仓自研的技能不归这里管：它们的 frontmatter 只有 `name` 和 `description` 两个键（`writing-for-agents` 技能的 `SKILL-SET-REVIEW.md` `### Descriptions`）。两行都留着的只有 `setup-matt-pocock-skills`、`grill-me`、`grill-with-docs`、`handoff`、`teach`、`improve-codebase-architecture`、`wait-what`。上游改这两行 → 本仓的取舍不变，两处一起跟。

下面每份说明只写它那个 skill 站在哪一边，不复述这条规则。

## host 中立

上游技能的正文按一家 host 说话：`the Skill tool` 这个工具名，和 `/名字` 这种斜杠调用。一份技能正文对所有 host 是同一份，而工具名与斜杠调用在别的 host 上不存在：agent 只能猜，用户照打也不起作用。本仓的改法（点名另一个技能的两种写法、会话管理命令的写法、技能名的散文写法）是技能文本的规则，写在 `writing-for-agents` 技能的 `SKILL-SET-REVIEW.md` `### Hand-offs` 与 `### Paths, tokens and host neutrality`。

**上游把某一段改回工具名或斜杠命令 → 收上游对那一段其余部分的措辞，按能力说话这一层不收回去。** 下面每份说明只写它那个技能改了哪几段，不复述这些写法。

一处已知偏差，记录，不修，不加守卫：`mmw-v2/upstream/CONTEXT.md` 举的 label 例子是 `ready-for-afk`，而本仓库的 label 是 `ready-for-agent`。约定明写 `mmw-v2/upstream/` 自己的 `AGENTS.md`、`CLAUDE.md`、`CONTEXT.md` 原样不动，所以这处偏差留着。不加守卫的理由是两样现有的东西已经拦住一个 agent 真去打这个 label：`docs/agents/triage-labels.md` 是 `triage` 与 `to-tickets` 唯一的 label 来源，表里没有 `ready-for-afk`；`verify-ticket.py --closeout` 是 worker 改 label 的唯一一步，而 `tool-guard.py pretool` 拦下把票挪出 agent 队列的那两条命令。一个打错的 label 不会让票进队列，也不会让它关掉，靠的是它不等于 `ready-for-agent`。这一条写在这里，是为了让下一次拉 upstream 的人不要把它当成本仓库的疏漏去「修」。

## 本仓自有正文的技能

`code-review`、`implement`、`to-tickets` 放在 `mmw-v2/upstream/skills/engineering/` 下，正文却几乎全是本仓写的。拉 upstream 时不合并上游对这三个技能的改动：冲突取本仓的，自动合进来的上游段落也改回本仓的。它们的说明记的是本仓各段的意图，不是与上游的差异。

`mmw-v2/skills/retro/` 是本仓自己的技能，不在任何 subtree 里，没有说明；上游的 `in-progress/retro` 是另一个技能，不合进来。

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
- [grilling](grilling.md) — `productivity/grilling`
- [handoff](handoff.md) — `productivity/handoff`
- [teach](teach.md) — `productivity/teach`
- [to-questionnaire](to-questionnaire.md) — `productivity/to-questionnaire`
- [wait-what](wait-what.md) — `productivity/wait-what`
- [writing-for-agents](writing-for-agents.md) — `productivity/writing-for-agents`
- [diagram-design](diagram-design.md) — `mmw-v2/upstream-diagram-design/`，另一个上游、另一个 subtree
- [unlazy](unlazy.md) — `mmw-v2/upstream-unlazy/`，verify-ticket 的判定引擎 gate-check，不是装进 host 的技能
