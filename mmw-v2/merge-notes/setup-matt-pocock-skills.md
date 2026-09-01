# setup-matt-pocock-skills

源目录：`mmw-v2/upstream/skills/engineering/setup-matt-pocock-skills/`

这个技能只跑一次，写出三份配置文件。它在本仓的落地件是 `docs/agents/` 下与三份种子同名的文件：

| 种子 | 本仓的落地件 |
| --- | --- |
| `issue-tracker-github.md` | `docs/agents/issue-tracker.md` |
| `domain.md` | `docs/agents/domain.md` |
| `triage-labels.md` | `docs/agents/triage-labels.md` |

**重跑这个技能之前先备份 `docs/agents/triage-labels.md`。** 它的 `## What carries a label here` 一节是本仓自己加的（哪个 label 代表哪个 queue、spec 不带 label、本仓自建 ticket 不带 category），种子里没有这一节，重跑会把它盖掉。另外两份落地件与种子几乎逐字相同，只差几处标点。

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 保留。这是四个例外之一（另三个是 `grill-me`、`handoff`、`wait-what`）：它一个仓库只跑一次、会覆盖 `docs/agents/` 下三份文件，不该由模型自己认出来触发。上游改这一行 → 收上游，跟 `agents/openai.yaml` 的 `policy` 块一起处理 |
| 第 3 步 Confirm and edit 的第一条草稿项 | 从「whichever of `CLAUDE.md` / `AGENTS.md` is being edited」改成固定的 `AGENTS.md`，跟第 4 步同步 |
| 第 4 步 Pick the file to edit（`CLAUDE.md` 在就改它、两个都没有就问用户、绝不在另一个已存在时新建） | 改成：`## Agent skills` 块永远写进 `AGENTS.md`，没有就建；`CLAUDE.md` 只放 `@AGENTS.md` 一行加它原有的其他 `@` 行，别的内容搬进 `AGENTS.md`。理由是本仓另一个技能 `manage-agents-md` 就是这个形态（`mmw-v2/skills/manage-agents-md/write.md:13`「the line `@AGENTS.md` … Nothing else.」），它的 `scripts/check.sh` 会把 `CLAUDE.md` 里每一行非 `@import` 判成错——照上游的规则跑完 setup，再跑 `manage-agents-md` 就是两个技能互相拆台。本仓已经按这个形态落地（`docs/adr/0005-docs-layer-adopted-by-v2.md`：`## Agent skills` 块在根 `AGENTS.md`）。上游改这一步 → 不收，除非它自己也变成只写 `AGENTS.md` |

### triage-labels.md（种子）

| 段落 | 我们的意图 |
| --- | --- |
| 表格下面那句举例「apply the AFK-ready triage label」 | 例子换成 `ready-for-agent`。这句教读者「技能提到 triage role → 来这张表取本仓真实的 label」，而 `AFK-ready` 在表里没有对应行，全仓也没有一个技能这么写——`triage/SKILL.md` 从头到尾直接写 `ready-for-agent`。上游改这句 → 收上游措辞，例子必须用表里真有的 label |
