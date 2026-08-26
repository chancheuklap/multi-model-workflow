# Retrieval 重建区

MMW 原创技能，没有 Matt 上游。当前发布技能仍位于 `mmw/skills-src/mmw-retrieval/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文接线（2026-08-16）

候选是 **2 个文件**：[`candidate/SKILL.md`](candidate/SKILL.md)、[`candidate/building.md`](candidate/building.md)，按将来位于 `mmw/skills-src/mmw-retrieval/` 书写。现役技能源未改。

已叠进候选的接线：

- 怎么查询仍由 Serena / Graphify 的服务器说明规定。本技能只管图可用，以及工具连不上时怎么查。
- 三种图状态：缺失、过期、新鲜。只由 `mmw graph build` 更新。
- 工具连不上跑 `mmw doctor`。
- `building.md` 仍是 `.mmw.json` `retrieval.graph` 的环境缓存，本轮按现役翻译，不改成 `--help`。
- 宿主不在握手时附上服务器说明、派发提示词也没有检索纪律时，走第 3 节。不按宿主名开分支。

未叠：

- 把 Serena / Graphify 用法抄进本技能。
- 用提交号判断新鲜度。

leaf 草稿见 [`candidate/leaf-terms.md`](candidate/leaf-terms.md)。本轮不派冷读 subagent。
