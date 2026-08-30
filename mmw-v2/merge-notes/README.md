# merge-notes

`mmw-v2/upstream/` 里被我们改过的技能，每个一份说明：改了哪几段、为什么改、上游再动这几段时怎么取舍。
给的是**意图**，不是 diff——diff 用 `git diff <上一个 Squashed 提交> -- <技能目录>` 看。

## 上游更新时怎么用

1. 拉对应的 subtree。mattpocock 的：
   `git subtree pull --prefix mmw-v2/upstream https://github.com/mattpocock/skills main --squash`
   `diagram-design` 自己一个，命令写在它的说明里。
2. 每个冲突文件，打开它所属技能的说明，对着冲突段落找到对应条目，按条目里的取舍规则决定留谁。
   说明里没覆盖的段落：我们没改过，取上游。
3. 解完：通读该技能的 `SKILL.md` 及其 reference 一遍，确认没有互相矛盾的句子；跑 `bash mmw-v2/install.sh --check`。
4. 上游把我们引用的文件改名、合并或拆分时，更新说明里的段落定位。

## 目前有说明的技能

- [ask-matt](ask-matt.md) — `engineering/ask-matt`
- [code-review](code-review.md) — `engineering/code-review`
- [domain-modeling](domain-modeling.md) — `engineering/domain-modeling`
- [grill-with-docs](grill-with-docs.md) — `engineering/grill-with-docs`
- [implement](implement.md) — `engineering/implement`
- [improve-codebase-architecture](improve-codebase-architecture.md) — `engineering/improve-codebase-architecture`
- [prototype](prototype.md) — `engineering/prototype`
- [research](research.md) — `engineering/research`
- [to-spec](to-spec.md) — `engineering/to-spec`
- [to-tickets](to-tickets.md) — `engineering/to-tickets`
- [triage](triage.md) — `engineering/triage`
- [wayfinder](wayfinder.md) — `engineering/wayfinder`
- [teach](teach.md) — `productivity/teach`
- [to-questionnaire](to-questionnaire.md) — `productivity/to-questionnaire`
- [wait-what](wait-what.md) — `productivity/wait-what`
- [diagram-design](diagram-design.md) — `mmw-v2/upstream-diagram-design/`，另一个上游、另一个 subtree
