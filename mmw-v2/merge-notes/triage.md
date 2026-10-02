# triage

源目录：`mmw-v2/upstream/skills/engineering/triage/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| 开头「must **start** with this disclaimer」 | 改成放 issue comment 最后一行。原来的理由是 issue comment 的 first line 曾是 landing pipeline 的 protocol slot；mmw #315 之后程序只读 comment 末尾的 `<!-- mmw {...} -->` 事件块、不读 first line，但 first line 仍是人在票上扫一眼读到的那一行（`status` 的 `note` 列、night summary 都抄它），免责声明占了它，这张票在哪一步就没人看得出来。正文只写「放末行」，不附理由（旧理由里的 `protocol slot` 已过时）。上游改这句 → 收上游的措辞，位置留在末行 |
| `## Reference docs` 里指向 `references/pipeline-issues.md` 的一条，`## Triage a specific issue or PR` 开头指向它的一句，与 `references/pipeline-issues.md` 本身 | 回到上游原文（spec #597 Implementation Decisions 4）。这三处写的是本仓 landing pipeline 怎样处理它自己产出的 issue，不属于上游目录允许的两类改动（[README.md](README.md) `## 上游目录只允许两类改动`）：`references/pipeline-issues.md` 整份搬到 `mmw` 技能的 `references/pipeline-issues.md`，文件名不变；按 label 把流水线产出的 issue 送去读它的那一句，现在在 `mmw` 技能 playbook **Accept the night** 的 **Work the needs-triage queue** 一步里。上游改这两节 → 取上游 |
| 第 4 步 `Grill (if needed)` | host 中立：上游写「call the Skill tool twice」，这个工具名只在一家 host 上存在；改成读 `grilling` 与 `domain-modeling` 两份技能的 `SKILL.md`。共同理由见 [README.md](README.md#host-中立)，写法见 `mmw` 技能的 `references/skill-set-rules.md` `### Paths and host neutrality` 与 `### Hand-offs`。上游改这一步 → 收上游措辞，工具名仍换成读两份 `SKILL.md` |
| 第 5 步 `**Apply the outcome:**` 标题行，与删掉的 `needs-triage: apply the role` 一条 | 注明 the four outcomes 是 `needs-info` / `ready-for-agent` / `ready-for-human` / `wontfix`，留在 `needs-triage` 不算 outcome，上游那条 `needs-triage` 一并删掉。`CONTEXT.md` 与 `docs/agents/triage-labels.md` 都写「one of the four outcomes」，而上游这一节下面列了五条，读者数不出是哪四个。「`needs-info`、`ready-for-human` 和 `wontfix` 不移动 child」这句只对流水线的 child 有意义，挪到 `mmw` 技能 `references/pipeline-issues.md` 的 `## ready-for-agent`，写成只有 `ready-for-agent` 会移动 child；`SKILL.md` 第 5 步不再重复这句。上游改这一节 → 收上游的条目，「四个」这个数与 `needs-triage` 不算出口这句保留 |
| 第 5 步 `Apply the outcome` 末尾 `A child whose default was right …` 一段 | 回到上游原文（spec #597 Implementation Decisions 4）：这一段是流水线给 child 的出口，搬到 **Accept the night** 的 **Work the needs-triage queue**，命令写成 `dispatch.sh resolve-child`。上游改这一步 → 收上游的条目 |
