# tdd

源目录：`mmw-v2/upstream/skills/engineering/tdd/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| `## Seams: where tests go` 的 `**Test only at pre-agreed seams.**` 一段 | 第 22 行的「Working from a ticket, the seams under test are the ones its `## Seam` section names.」→ `mmw-v2/skills/mmw/playbooks/work-a-ticket.md` 第 3 步 **Write the code**（spec #597 第 6 节）；第 38 行带票的那半句 → 同一份 playbook 的 `#### The review round`（spec #597 第 6 节）；其余加句随回原文撤回（R18 §4.2 `tdd` 行）。 |
| `## Seams: where tests go` 末句 `When the shape of that interface is itself in question …` | host 中立：改成读 `codebase-design` 技能的 `SKILL.md` 取词汇。判据是这一句自己给的——`it is a reference to consult, not a session to run`。共同理由见 [README.md](README.md#host-中立)，写法见 `mmw` 技能的 `references/skill-set-rules.md` `### Paths and host neutrality` 与 `### Hand-offs` |

### tests.md 与 mocking.md

| 段落 | 我们的意图 |
| --- | --- |
| 两份全文 | 上游原文，不改。`mmw` 技能的 `references/tests-reviewer.md` 按技能名读这两份（`s6-review-a-ticket` 把它搬到那里），引用的是 `tests.md` 的 **Tautological tests**、**Implementation-detail tests** 两个小节与 red flag `Verifying through external means instead of interface`、`Test name describes HOW not WHAT`，和 `mocking.md` 的 `Don't mock` 清单。上游改这些小节名或措辞 → 收上游，同时改 `mmw` 技能的 `references/tests-reviewer.md` 第 3 节的指向 |
