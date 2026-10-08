---
date: 2026-10-08
amends: [0032]
---

# 技能文字的写作规则都在 `writing-for-agents` 技能里；改技能一律从 Authoring or modifying a skill 开始，一个会话做不完的由它交给 Write a spec

写进一套技能的文字，规则在 `writing-for-agents` 这一个技能里，按要写的东西打开其中一份。`SKILL.md` 是任何一份给 agent 读的文字的写法。`SKILL-MECHANICS.md` 管一个技能的 frontmatter。`SKILL-SET-RULES.md` 管会落进 `mmw-v3/skills/` 的文字，拉上游新版的命令在它的 `### Upstream skills`。`SKILL-SET-COMPONENTS.md` 决定一段文字放进哪种组件。`WALKING-A-SKILL-SET.md` 在一项任务上证明一次改动。

改技能从 playbook Authoring or modifying a skill 开始。一个会话做得完的，在这个会话里检查、走查、提交。一个会话做不完的，由 Land it 交给 Write a spec。主人接受这一夜并且 `finish` 跑完之后，回到 Validate it。Deliver 仍停在提交并告诉主人。发布的四步仍写在根目录 `AGENTS.md` 的 `## Gotchas`，只在主人说发布时才跑。

0032 的正文写着，拉新版的命令在 `mmw-mode` 的 `references/skill-set-rules.md`。那份文件现在是 `mmw-v3/skills/writing-for-agents/SKILL-SET-RULES.md`。命令仍在 `### Upstream skills`。

## Considered Options

- **规则留在 `mmw-mode/references/`。** 否决。mode 的 `## Non-negotiables` 把写 spec 的会话送到 `writing-for-agents`，那个会话到不了 `mmw-mode/references/`。spec #935 就是这样写成的。
- **在 Write a spec 里加一步技能文字的检查。** 否决。Write a spec 服务每一个产品仓库。
- **把发布四步放进 Deliver。** 否决。发布是主人的决定。

## Consequences

- 一次技能改动从 Authoring or modifying a skill 进入。Write a spec、Cut tickets、Work a ticket、Review a ticket、Run a night 不改。
