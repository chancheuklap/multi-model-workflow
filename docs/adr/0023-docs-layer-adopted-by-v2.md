---
date: 2026-08-25
amends: [0003, 0010]
---

# docs 文档层过继到 v2：spec 文件名带名字段，索引与编号脱离冻结 CLI

docs 层（adr、specs、research）的约定与工具一直接在上一代：spec 强制叫 `spec.md`（八份同名文件无法靠文件名搜索与辨认）、ADR 编号与两个 README 索引由冻结区 `mmw/cli/` 的生成器产出——而根 AGENTS.md 对冻结区的约定是「不改、不加、不当事实」，局部约定却要求调用它，两份约定互相矛盾。同时 v2 时代的 tracker 配置（`docs/agents/issue-tracker.md` 等）从未落过，engineering 技能的前置检查一直踩空。specs 索引也已烂掉：五份 spec 只有一份在索引里。

因此过继：①补齐 `docs/agents/` 三件配置（照 setup 技能的 GitHub 种子、默认标签、单 context）并在根 AGENTS.md 落 `## Agent skills` 块；②spec 文件名改为 `docs/specs/<名字段>/<名字段>.md`，既有五份随本次改动一并更名（`git log --follow` 保历史）；③ADR 编号改为「现有最大号 + 1」，两个 README 索引改为手工维护、新增条目顺手追加一行；④docs 层不再调用冻结区任何命令。

## Considered Options

- **维持 `spec.md` 命名与生成器。** 否决。同名文件的搜索成本是真实痛点（用户当场撞上）；生成器在冻结区，依赖它与根约定矛盾，且它维护的索引已经烂了——生成物没有跟随近三个月的五份 spec。
- **把生成器搬进 mmw-v2 再续用。** 否决。索引是两张十几行的表，手工追加一行的成本低于维护一个生成器；「机械校验只判机器能直接判定的事实」的仓库边界也不鼓励为可派生副本养工具。将来条目多到手工失控时再议。
- **spec 平铺为 `docs/specs/<名字段>.md`。** 否决。spec 有附件（landing-closeout 带 1298 行纪律存档），目录是附件的家；保目录、文件名带名字段已同时解决搜索与标签辨认。

## Consequences

- ADR 0003（同一路径形状）与 0010（索引由命令算出）在 docs 层不再成立，两篇顶部已加引用块指向本篇；其余产物（research、prototype 的路径约定）照旧。
- `docs/AGENTS.md`、`docs/specs/AGENTS.md`、`docs/adr/AGENTS.md`、`docs/research/AGENTS.md` 相应改写；两个 README 重建为手工维护的完整索引。
- 冻结区 `mmw/cli/` 自此对活层零调用；它自身照旧冻结，不删不改。
- engineering 技能（to-spec、to-tickets、triage、code-review）的 tracker 前置检查自此在本仓成立。

来源：2026-08-25 与用户的对话（用户指出 spec.md 同名不可搜索并质疑仓库未做 v2 配置，两点均查证属实）；`docs/specs/README.md` 迁移前只含 5 份中 1 份的现状；setup 技能种子 `mmw-v2/upstream/skills/engineering/setup-matt-pocock-skills/`。
