# code-review

源目录：`mmw-v2/upstream/skills/engineering/code-review/`

`SKILL.md` 回到上游 87 行的两轴评审，继续安装。上游没有调用开关。`agents/openai.yaml` 与文档页 `mmw-v2/upstream/docs/engineering/code-review.md` 回到上游原文。没有保留任何改动。拉 upstream 时 `SKILL.md`、`agents/openai.yaml` 与文档页取上游。

## 逐段意图

### SKILL.md

原来的内容去了哪里（spec #597 第 8 节）：

- 第 8 行 → `mmw-v2/skills/mmw/playbooks/review-a-ticket.md` 首段与 **principle-a-second-reader-judges**
- `## Find your moment` 与 `references/session.md` → `mmw-v2/skills/mmw/playbooks/review-a-ticket.md`；其中子代理的共同规则 → mode `## Subagents`
- 四份评审简报 → `mmw-v2/skills/mmw/references/standards-reviewer.md`、`mmw-v2/skills/mmw/references/spec-reviewer.md`、`mmw-v2/skills/mmw/references/tests-reviewer.md`、`mmw-v2/skills/mmw/references/ui-reviewer.md`

旧的逐段意图见 `git show 3155bf4f:mmw-v2/merge-notes/code-review.md`。
