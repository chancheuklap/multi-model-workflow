# implement

源目录：`mmw-v2/upstream/skills/engineering/implement/`

`SKILL.md` 回到 `5b1a4c51` 的上游原文：15 行，`disable-model-invocation` 与 `agents/openai.yaml` 的 `policy` 两处开关都在。`skills.txt` 的 `engineering/implement` 暂带 `+model-invoked`，安装副本里去掉这两处；`s6-mode-b2` 删掉那一行后不再安装。没有保留任何改动。拉 upstream 时 `SKILL.md`、`agents/openai.yaml` 取上游。

## 逐段意图

### SKILL.md

原来的内容去了哪里（spec #597）：

- 认领、读入、写码、收尾各步 → `mmw-v2/skills/mmw/playbooks/work-a-ticket.md`（第 6 节）
- 两条写码规则 → `mmw-v2/skills/mmw/references/code-writing-rules.md`（第 6 节）
- `## Shared experience while implementing` 的做法 → `mmw-v2/skills/memory-records/SKILL.md`（第 9 节）；何时用 → `mmw-v2/skills/mmw/playbooks/work-a-ticket.md` `#### Memory while working`（第 6 节）
- `references/saving-memory.md` → `mmw-v2/skills/memory-records/references/saving-memory.md`（第 9 节）
- `references/writing-interface-code.md` → `mmw-v2/skills/ui-acceptance/references/writing-ui-code.md`（第 6 节）

文档页 `mmw-v2/upstream/docs/engineering/implement.md` 回到上游原文。

旧的逐段意图见 `git show 3155bf4f:mmw-v2/merge-notes/implement.md`。
