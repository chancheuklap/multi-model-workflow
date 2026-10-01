# merge-notes

四个上游 subtree 里被我们改过的技能和脚本，每个一份说明：改了哪几段、为什么改、上游再动这几段时怎么取舍。
给的是**意图**，不是 diff——diff 用 `git diff <上一个 Squashed 提交>:skills/<类别>/<技能> HEAD:mmw-v2/upstream/skills/<类别>/<技能>` 看（squash 提交的树根是上游仓库根，没有 `mmw-v2/upstream/` 前缀；上一个 Squashed 提交用 `git log --oneline --grep "Squashed 'mmw-v2/upstream/'"` 找）。
反方向——本仓库改了、consuming repository 里哪些产物作废——是 downstream-note，见 [`../downstream-notes/README.md`](../downstream-notes/README.md)。

## 上游更新时怎么用

1. 拉对应的 subtree。mattpocock 的：
   `git subtree pull --prefix mmw-v2/upstream https://github.com/mattpocock/skills main --squash`
   `diagram-design`、`unlazy` 和 `pstack` 各自一个，命令写在各自的说明里。
2. 每个冲突文件，打开它所属技能的说明，对着冲突段落找到对应条目，按条目里的取舍规则决定留谁。
   说明里没覆盖的段落：我们没改过，取上游。
3. 解完：通读该技能的 `SKILL.md` 及其 reference 一遍，确认没有互相矛盾的句子；跑 `bash mmw-v2/install.sh --check`。
   `unlazy` 不是技能，换成：读上游对说明里每个段落的 diff，没冲突的也读——一条自动合进来的上游条件就能悄悄撤掉我们的改动；再跑 `bash mmw-v2/tests/verify-ticket/run.sh`。
4. 上游把我们引用的文件改名、合并或拆分时，更新说明里的段落定位。

## 上游目录只允许两类改动

`mmw-v2/upstream/`、`mmw-v2/upstream-diagram-design/`、`mmw-v2/upstream-unlazy/` 里的技能和脚本只允许两类改动：

1. **host 中立**：把只在一家 host 上存在的工具名与会话命令改成每家 host 都读得懂的写法，见下面的 `## host 中立`。
2. **能力改动**：改变这项能力本身怎么做，在这里写一份说明，记改了哪段、为什么、上游再动这段时怎么取舍。

流程句（这一步之后做什么、交给哪个技能）、原则句和本仓库的配置字面（例如 label 名）不写进上游目录：流程在 `mmw` 技能的 playbook 里，原则在它的 `principles/` 里，label 名在 `docs/agents/` 下由技能读取的文件里。调用开关也不在子树里改，见 `## disable-model-invocation`。`mmw-v2/upstream-pstack/` 里的文字一律不改。

`code-review`、`implement`、`tdd`、`resolving-merge-conflicts` 里还有这两类以外的本仓文字（流水线的步骤与票的说法）；`wizard` 生成的脚本头注释把上游的 `/wizard` 写成了散文（见 [wizard](wizard.md)）。拉 upstream 时照各自的说明处理。`to-spec`、`to-tickets` 的本仓文字不在上游目录里：它们分叉成本仓自有的技能 `mmw-v2/skills/to-spec/`、`mmw-v2/skills/to-tickets/`，上游目录里的同名技能是原文、不安装，两份说明记本仓的文字现在在哪里。

## `disable-model-invocation`

`SKILL.md` frontmatter 的 `disable-model-invocation: true`（Claude Code 读）与 `agents/openai.yaml` 的 `policy.allow_implicit_invocation: false`（Codex 读）说的是同一件事：这个 skill 只有 user 点名才触发。两处同增同删——只动一处，同一个 skill 在一半 host 上是 user 触发、在另一半是模型可触发。

被 mode 或 playbook 点名、要模型调用的上游技能不改子树，只在 `skills.txt` 那一行加 `+model-invoked`，由 `install.sh` 在安装副本里去掉这两处。

本仓自研的技能不归这里管：它们的 frontmatter 只有 `name` 和 `description` 两个键（`mmw` 技能的 `references/skill-set-rules.md` `### Descriptions`）。`skills.txt` 装的上游技能里，两行都留着的十个是 `setup-matt-pocock-skills`、`grill-me`、`grill-with-docs`、`handoff`、`teach`、`improve-codebase-architecture`、`wait-what`、`triage`、`wayfinder`、`to-questionnaire`。其中 `setup-matt-pocock-skills`、`grill-me`、`handoff`、`teach`、`wait-what`、`triage`、`wayfinder`、`to-questionnaire` 在 `skills.txt` 带 `+model-invoked`；`grill-with-docs`、`improve-codebase-architecture` 不带标记，只由用户点名。不装的 `ask-matt` 与上游目录里的 `to-spec`、`to-tickets` 是原文，也留着两行。上游改这两行 → 子树里两处一起跟；带标记的，由安装副本去掉。

下面每份说明只写它那个 skill 站在哪一边，不复述这条规则。

## host 中立

host 中立的改动只改两样只在某一家 host 上成立的写法：工具名（`the Skill tool`、`the Task tool`，各只在一家 host 上存在，别的 host 的 agent 只能猜），和会话命令（清空或压缩一个会话的上下文，每家 host 叫法不同），改成每家 host 都读得懂的写法。技能名本身（`/X` 或 `the X skill`）在每个 host 上都可用，不在此列：上游写的 `/X` 不改成散文，拉 upstream 时留着上游的 `/X`。写法是技能文本的规则，写在 `mmw` 技能的 `references/skill-set-rules.md` `### Paths and host neutrality`，点名另一个技能做事的写法见同一文件的 `### Hand-offs`。

**上游把某一段改回工具名或会话命令 → 收上游对那一段其余部分的措辞，工具名与会话命令仍写成每家 host 都读得懂的写法。** 下面每份说明只写它那个技能改了哪几段，不复述这些写法。

一处已知偏差，记录，不修，不加守卫：`mmw-v2/upstream/CONTEXT.md` 举的 label 例子是 `ready-for-afk`，而本仓库的 label 是 `ready-for-agent`。约定明写 `mmw-v2/upstream/` 自己的 `AGENTS.md`、`CLAUDE.md`、`CONTEXT.md` 原样不动，所以这处偏差留着。不加守卫的理由是两样现有的东西已经拦住一个 agent 真去打这个 label：`docs/agents/triage-labels.md` 是 `triage` 与 `to-tickets` 唯一的 label 来源，表里没有 `ready-for-afk`；`verify-ticket.py --closeout` 是 worker 改 label 的唯一一步，而 `tool-guard.py pretool` 拦下把票挪出 agent 队列的那两条命令。一个打错的 label 不会让票进队列，也不会让它关掉，靠的是它不等于 `ready-for-agent`。这一条写在这里，是为了让下一次拉 upstream 的人不要把它当成本仓库的疏漏去「修」。

## 本仓自有正文的技能

`code-review`、`implement` 放在 `mmw-v2/upstream/skills/engineering/` 下，正文却几乎全是本仓写的。拉 upstream 时不合并上游对这两个技能的改动：冲突取本仓的，自动合进来的上游段落也改回本仓的。它们的说明记的是本仓各段的意图，不是与上游的差异。

`mmw-v2/skills/retro/` 是本仓自己的技能，不在任何 subtree 里。它 `## Decide` 第 9 步从 pstack 的 synthesizer 抄来的四条分拣规则，说明在 [pstack](pstack.md) 的 `## retro 的四条分拣规则`。上游的 `in-progress/retro` 是另一个技能，不合进来。

## 目前有说明的技能

- [code-review](code-review.md) — `engineering/code-review`
- [codebase-design](codebase-design.md) — `engineering/codebase-design`
- [domain-modeling](domain-modeling.md) — `engineering/domain-modeling`
- [grill-with-docs](grill-with-docs.md) — `engineering/grill-with-docs`
- [implement](implement.md) — `engineering/implement`
- [improve-codebase-architecture](improve-codebase-architecture.md) — `engineering/improve-codebase-architecture`
- [prototype](prototype.md) — `engineering/prototype`
- [research](research.md) — `engineering/research`
- [resolving-merge-conflicts](resolving-merge-conflicts.md) — `engineering/resolving-merge-conflicts`
- [to-spec](to-spec.md) — `engineering/to-spec`，原文、不安装；装的是本仓的分叉 `mmw-v2/skills/to-spec/`
- [to-tickets](to-tickets.md) — `engineering/to-tickets`，原文、不安装；装的是本仓的分叉 `mmw-v2/skills/to-tickets/`
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
- [unlazy](unlazy.md) — `mmw-v2/upstream-unlazy/`，verify-ticket 的判定引擎 gate-check，不是装进 host 的技能
- [pstack](pstack.md) — `mmw-v2/upstream-pstack/`，另一个上游、另一个 subtree；里面的文字不改
