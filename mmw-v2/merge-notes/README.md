# merge-notes

两个上游 subtree 里被我们改过的技能，每个一份说明：改了哪几段、为什么改、上游再动这几段时怎么取舍。
给的是**意图**，不是 diff——diff 用 `git diff <上一个 Squashed 提交>:skills/<类别>/<技能> HEAD:mmw-v2/upstream/skills/<类别>/<技能>` 看（squash 提交的树根是上游仓库根，没有 `mmw-v2/upstream/` 前缀；上一个 Squashed 提交用 `git log --oneline --grep "Squashed 'mmw-v2/upstream/'"` 找）。

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

## 目前有说明的技能

- [ask-matt](ask-matt.md) — `engineering/ask-matt`
- [code-review](code-review.md) — `engineering/code-review`
- [domain-modeling](domain-modeling.md) — `engineering/domain-modeling`
- [grill-with-docs](grill-with-docs.md) — `engineering/grill-with-docs`
- [implement](implement.md) — `engineering/implement`
- [improve-codebase-architecture](improve-codebase-architecture.md) — `engineering/improve-codebase-architecture`
- [prototype](prototype.md) — `engineering/prototype`
- [to-spec](to-spec.md) — `engineering/to-spec`
- [to-tickets](to-tickets.md) — `engineering/to-tickets`
- [setup-matt-pocock-skills](setup-matt-pocock-skills.md) — `engineering/setup-matt-pocock-skills`
- [triage](triage.md) — `engineering/triage`
- [wayfinder](wayfinder.md) — `engineering/wayfinder`
- [teach](teach.md) — `productivity/teach`
- [to-questionnaire](to-questionnaire.md) — `productivity/to-questionnaire`
- [wait-what](wait-what.md) — `productivity/wait-what`
- [writing-for-agents](writing-for-agents.md) — `productivity/writing-for-agents`
- [diagram-design](diagram-design.md) — `mmw-v2/upstream-diagram-design/`，另一个上游、另一个 subtree
