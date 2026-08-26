# Install 重建区

MMW 原创技能，没有 Matt 上游。当前发布技能仍位于 `mmw/skills-src/mmw-install/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文接线（2026-08-16）

候选是 **1 个文件**：[`candidate/SKILL.md`](candidate/SKILL.md)，按将来位于 `mmw/skills-src/mmw-install/SKILL.md` 书写。现役技能源未改。

已叠进候选的接线：

- 两件事分开：本机装一次，仓库配一次。
- 步骤仍是 `install.sh` → `mmw init` → `mmw toolchain` → 宿主要用户点头的 hook → 会从别的 agent 用户目录加载技能时的三件人工设置。
- 不复述 `install.sh` 装了哪五个宿主。诊断怎么送到各宿主，指向 `mmw toolchain` 与规则表文件头。
- 按能力写用户步骤，不按宿主名开五路讲义。设置项仍用它们在界面上的名字。

未叠：

- 把 `install.sh` 的步骤抄进技能。
- 把 Cursor 三件设置改成抽象描述、让用户找不到开关。

leaf 草稿见 [`candidate/leaf-terms.md`](candidate/leaf-terms.md)。本轮不派冷读 subagent。
