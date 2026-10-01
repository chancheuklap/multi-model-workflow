# wayfinder

源目录：`mmw-v2/upstream/skills/engineering/wayfinder/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| `## Ticket Types` 的 **Research** 一条，与 `### Chart the map` 第 5 步 **Hand off the research tickets.**（标题与正文） | host 中立：两处正文都换成同一句「Hand each research ticket to a separate session that can commit files and close the ticket; a subagent that must return findings as text cannot.」，不点名 `dispatch`，不点名宿主；第 5 步的标题从上游的「Fire the research subagents.」换成「Hand off the research tickets.」，因为原标题仍叫 agent 去派子代理。这是对上游 #763（由画 map 的会话派子代理调研，结果留在 `research/<name>` 分支上）的有意偏离，理由两条：子代理不能在项目里新建报告文件（#591 现场：agentflow map #1000 上 4 个调研子代理都在写报告一步被 Claude Code 拒绝，报错原文 `Subagents should return findings as text, not write report files.`）；调研要按角色选宿主（`models.json` 的 `researcher` 行），宿主自带的子代理做不到。怎样起这个会话、派完不等回报、推进地图时跳过已有 `research/<n>` 分支的调研票、把报告的指针补进 map，写在 `mmw` 技能的 playbook **Map a large effort**（`mmw-v2/skills/mmw/playbooks/map-a-large-effort.md`），不写进本技能。上游再改这两处 → 收上游对其余部分的措辞，这一句与第 5 步的标题保留；上游改成由一个能写文件、能关票的会话做调研 → 取上游，删掉这一行 |
| `## Ticket Types` 的 Prototype、Grilling 两条，`### Chart the map` 第 1 步 **Name the destination.**，`### Work through the map` 第 3 步 | host 中立：上游这几处写「call the Skill tool」，这个工具名只在一家 host 上存在；改成读那份技能的 `SKILL.md`（Prototype 与 Grilling 两类票用户在场，开子会话会把用户挡在外面），第 1 步与第 3 步同样读那份技能的 `SKILL.md`。共同理由见 [README.md](README.md#host-中立)，写法见 `mmw` 技能的 `references/skill-set-rules.md` `### Paths and host neutrality` 与 `### Hand-offs` |
| `### The map body` 模板 `## Notes` 那一行末尾的「the effort's directory name under `prototypes/` and `docs/specs/`」 | 能力改动：map 在 Notes 里写下这次工作的目录名（小写 ASCII 单词用 `-` 连），`prototype` 的叶目录 `prototypes/<effort>/`、`design-pages` 的 pull 写的 design package `prototypes/<effort>/claude-design/` 与 screen contract 所在的 `docs/specs/<effort>/` 都用它。理由：map 标题常是中文、带空格和冒号，按标题起目录名每个 session 各起各的（任务板试点 #541）。上游改这行模板 → 收上游措辞，把这一项接回去 |
