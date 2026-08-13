---
date: 2026-08-13
amends: []
---

# 界面 QA 的运行时依赖装在 runtime 外面，入口是独立命令不是 mmw 子命令

界面 QA 要三个 npm 包（浏览器自动化框架、可访问性规则引擎、设计系统格式校验器）加一份外部技能（设计系统作者）。它们由 `mmw/install.sh` 装进 `$MMW_RUNTIME_HOME/ui-qa`——跟 runtime 平级，不在 runtime 里面。技能通过 `mmw-ui-qa` 这个独立命令定位那三个 npm 包；那份外部技能另外软链进本机各宿主的技能目录，因为它要被宿主当技能识别，不是被命令调用。软链落点包含 `~/.agents/skills`，Grok 从那里读它。

## Considered Options

**装进 runtime 里面**，否决，三条理由：Codex 与 Claude Code 运行的是 `plugins/cache` 里的副本，`node_modules` 跟着复制会把插件撑大几百 MB，而它们并不需要这份副本；`install.sh` 的 `require_version_bump` 逐字 diff runtime 与已装副本，装在里面会因 `node_modules` 的差异误报「内容变了要升版本号」；依赖版本由 `deps.json` 管，跟产品版本号是两件事，不该绑在一起升。

**做成 `mmw` 的子命令**，否决。`mmw/cli/mmw` 开头写着准入判据：一个动作要么是多请求编排、要么是护栏、要么是宿主机械差异的落点、要么是没有 API 的固定套路。转发到几个已装好的 npm 包一条都不占。

**把设计系统作者装成它的 plugin**，否决。那份 plugin 会把它自己的 marketplace、hooks 与四个 subagent 一起带进宿主，而界面 QA 只用到其中一份技能。改为按 tag 从 GitHub 稀疏检出那一个技能目录：整仓 950MB，那一份 3.4MB。

**把那份外部技能的内容装进用户已有的 `~/.agents/skills/`**，否决。那是用户自己的 git 仓库，MMW 每次升依赖版本都会在里面留下未提交改动。改为装进 MMW 自己的目录再软链进各宿主，跟 `install.sh` 装 MMW 自身技能的做法一致；软链目标指向非 MMW 内容时不覆盖，报出来。

**软链落点不含 `~/.agents/skills/`**，否决。Grok 扫每一层的 `.agents/skills`（见它 user-guide 的 Skill Locations 一节），不软链进去，Grok 读到的就是那个目录里原有的那份副本，而 MMW 升依赖版本时只升自己那份——两份会漂，而且漂了没人知道。改为把 `~/.agents/skills` 也列进软链落点，全机器只保留一份内容。落点上已经有一份真目录时，只在它确实是同一个技能（`SKILL.md` 的 `name` 对得上）时接管，接管前整份移进 `$MMW_RUNTIME_HOME/ui-qa/.backups/`；备份不放回宿主的 skills 目录，那里多出一个带 `SKILL.md` 的目录会被宿主当成另一个技能扫进去。代价是用户的 `~/.agents` 仓库里会出现一次改动：原目录被移走、换成一条软链。这次改动只发生一次，由用户自己决定提交还是忽略；上面否决的那一项是每次升版本都改一次。

**`--check` 只看版本**，否决。装的那一份版本对，不代表宿主读的是这一份：落点上放着另一份真目录时，那个宿主读的是它。`--check` 一并核对每个落点是不是指向 MMW 那一份的软链，`mmw doctor` 因此能报出漂移。

**技能正文直接写依赖路径**，否决。`MMW_RUNTIME_HOME` 可配，写死就锁死了一种安装布局。技能正文写命令名、路径由命令当场算，跟技能正文写 `mmw artifact path` 而不写 `docs/specs/…` 是同一种做法。
