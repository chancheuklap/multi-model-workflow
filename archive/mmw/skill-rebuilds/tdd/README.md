# TDD 重建区

这个目录用于从 Matt Pocock Skills 重新建立 MMW TDD。当前发布技能仍位于 `mmw/skills-src/mmw-tdd/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文逆向（2026-08-16）

底稿是上游英文原文（vendor `1.2.3`：`SKILL.md`、`tests.md`、`mocking.md`），只叠必要接线。候选按将来位于 `mmw/skills-src/mmw-tdd/` 书写。现役技能源未改。`planner` / `worker` / 审查者仍加载本技能。

已叠进候选的接线：

- `CONTEXT.md` 换成 `mmw domain path`；ADR 用 `mmw artifact index adr`。
- 开工前读目标仓库 `TESTING.md`。没有就从 `AGENTS.md` / `CLAUDE.md` 找。找不到就按本技能做，并在报告里说。冲突就列出，不自行覆盖。
- spec 已点名 seam 时从 spec 读，不再问一遍。需要 spec 没写的 seam 就停。`worker` 同样停。
- `/codebase-design` → `/mmw-codebase-design`；审查写成 `/mmw-review`。
- `mocking.md`：系统边界最终以 `TESTING.md` 为准。
- description 补上 `planner`、`worker`、审查者会加载本技能。

未叠：

- 「全部 seam 走完后回到调用方」的收口教程。
- `agents/openai.yaml`。

本轮不派冷读 subagent。不改 leaf。`correct seam` 已在现役用语里。

## 先前阶段（中文重建）

第一阶段已经完成上游 `SKILL.md`、`mocking.md`、`tests.md` 和 `agents/openai.yaml` 的逐行中文翻译。

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐行中文翻译基线 |
| `translation-audit.md` | 术语选择、逐行完整性与无新增语义检查 |
| [candidate/](candidate/) | 本轮英文接线候选 |
