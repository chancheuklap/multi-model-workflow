---
date: 2026-10-06
amends: [0003]
---

# MMW v3 按 pstack 的形状重建：一份 mode 按任务选 playbook，规则写成原则技能，上游拷进 `skills/` 由 `imports.tsv` 逐行记账

`mmw-v3/` 取代 `mmw-v2/`。每个会话先读 `mmw-v3/skills/mmw-mode/SKILL.md`：七节与 pstack 的 `poteto-mode` 同名同序（`## Non-negotiables`、`## Principles`、`## Autonomy`、`## Subagents`、`## Writing the reply`、`## Comments`、`## Playbooks`），其中 `## Playbooks` 是全套唯一的路由，每行指向 `mmw-mode/playbooks/` 下的一份 playbook（今天 25 份）。v2 写在提示词和各技能里的工作规则，改写成 15 个 `principle-*` 技能，`## Principles` 一行一条索引。人启动的会话由 `mode-hook.py` 在 Claude Code 与 Codex 的 SessionStart 上读 mode，`dispatch.sh` 开的会话由起始提示词的第一句读 mode。上游技能不再软链进子树：用到的文件拷进 `mmw-v3/skills/`，`mmw-v3/imports.tsv` 每个文件一行，记上游、源路径与提交号，每一处改动一条 J 记录，`mmw-v3/check_imports.py` 核对没有记录的改动。

## 要修的是什么

- v2 的规则分在提示词、35 个技能和 merge-notes 里，同一条规则有几种说法，一个会话要读哪些全靠技能自己的 description 触发；前两次迁移都卡在不知道每样东西何时被读。
- merge-notes 按段落记改动，没有机器核对：上游一拉，哪段对不上要人逐段看。
- `skills.txt` 是第二处登记：加了技能目录、忘了加这一行，就装不上，而且没有检查抓。

## Considered Options

- **在 v2 上逐个技能改。** 否决。规则分散在三层，逐个改只是把同一个问题挪个地方；两次迁移都这样失败过。
- **整套照搬 pstack，连它的脚本和 PR 流程。** 否决。pstack 的内容是它作者的工作方式；MMW 不开 PR，夜里的机器（`dispatch.sh`、事件、relay、watchdog）已经在真实运行里跑熟。拿它的组织方式，留 MMW 的内容和机器。
- **上游继续以子树加软链的方式进来。** 否决。软链让上游文件和本仓库的改动混在一个路径里，改了什么只能靠 merge-notes 的文字；拷进来逐文件记账，`check_imports.py` 能算出每一处差异有没有记录。
- **保留 `skills.txt`。** 否决。pstack 装整个目录；`mmw-v3/skills/` 下每个带 `SKILL.md` 的目录就是安装清单。

## Consequences

- 0003 的「五个宿主」变成四个：Claude Code、Codex、Grok、Cursor。v3 不装 Pi；`install.sh` 摘掉 v2 给 Pi 写的扩展文件和生成的 `AGENTS.md`，`--check` 把它们报成残留。
- 加一份 playbook、一条原则或一个技能，登记处各只有一个：mode 的一行、原则索引的一行、或技能目录本身。`mmw-v3/tests/lib/check_wiring.py` 在每套测试开头核对路由行对 playbook 文件、索引行对原则目录、步骤点名的技能、文件、脚本和 `dispatch.sh` 命令都存在。
- 上游以只读快照留在 `mmw-v3/upstream-mattpocock/`、`mmw-v3/upstream-pstack/`、`mmw-v3/upstream-diagram-design/`，是 `imports.tsv` 读源文件的地方。拉新版的命令写在 `mmw-mode` 的 `references/skill-set-rules.md`。unlazy 不再跟上游：gate-check 是本仓库自己的代码（见 `imports.tsv` 中 gate-check 那几行的 J 记录）。
- merge-notes 与 downstream-notes 两个目录不再有：前者由 `imports.tsv` 的 J 记录承接；后者在 v3 里没有承接对象，v2 时期留下的票不做兼容，改票。
- v2 留在 `mmw-v2/`，直到本机装着的 checkout 换成 v3；之后它和 `archive/` 一样只供查历史。
