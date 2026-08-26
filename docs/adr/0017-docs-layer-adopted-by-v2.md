---
date: 2026-08-25
amends: []
---

# docs 文档层过继到 v2：tracker 配置落地，索引与编号脱离冻结 CLI

docs 层的约定与工具一直接在上一代：ADR 编号与 README 索引由冻结区 `mmw/cli/` 的生成器产出——而根 AGENTS.md 对冻结区的约定是「不改、不加、不当事实」，局部约定却要求调用它，两份约定互相矛盾。同时 v2 时代的 tracker 配置（`docs/agents/issue-tracker.md` 等）从未落过，engineering 技能的前置检查一直踩空。

因此过继：①补齐 `docs/agents/` 三件配置（照 setup 技能的 GitHub 种子、默认标签、单 context）并在根 AGENTS.md 落 `## Agent skills` 块；②ADR 编号改为「现有最大号 + 1」，README 索引改为手工维护、新增条目顺手追加一行；③docs 层不再调用冻结区任何命令。

## Considered Options

- **续用冻结区那个生成器。** 否决。依赖它与根约定矛盾，而且它维护的索引本身已经烂掉——生成物没有跟随此前三个月新增的条目。
- **把生成器搬进 `mmw-v2/` 再续用。** 否决。索引是一张十几行的表，手工追加一行的成本低于维护一个生成器；「机械校验只判机器能直接判定的事实」这条仓库边界也不鼓励为可派生副本养工具。将来条目多到手工失控时再议。

## Consequences

- 冻结区 `mmw/cli/` 自此对活层零调用；它自身照旧冻结，不删不改。
- engineering 技能（to-spec、to-tickets、triage、code-review）的 tracker 前置检查自此在本仓成立。
- `docs/adr/README.md` 重建为手工维护的完整索引。

来源：2026-08-25 与用户的对话（用户质疑仓库未做 v2 配置，查证属实）；setup 技能种子 `mmw-v2/upstream/skills/engineering/setup-matt-pocock-skills/`。
