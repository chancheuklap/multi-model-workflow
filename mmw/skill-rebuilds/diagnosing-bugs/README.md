# Diagnosing Bugs 重建区

这个目录用于从 Matt Pocock Skills 重新建立 MMW Diagnosing Bugs。当前发布技能仍位于 `mmw/skills-src/mmw-diagnosing-bugs/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文逆向（2026-08-16）

底稿是上游英文原文（vendor `1.2.3`：一份六 Phase `SKILL.md` + `scripts/hitl-loop.template.sh`），只叠必要接线。候选按将来位于 `mmw/skills-src/mmw-diagnosing-bugs/` 书写。现役技能源未改。

上游六个 Phase 留在同一份 `SKILL.md`。HITL 模板原样留下。

已叠进候选的接线：

- `CONTEXT.md` 换成 `mmw domain path`；ADR 用 `mmw artifact index adr`。
- 首次写入前 `[[mmw-require-task-branch]]`。
- 过程材料落 `mmw artifact path scratch --sub diagnosis/<short-name>`。正确 seam 上的回归测试是源码，按 Phase 5 写。
- Phase 6 交给 `/mmw-improve-codebase-architecture`。

未叠：

- `narrowing.md` / `fixing.md` 拆文件。
- Phase 5 派 `worker`、四栏表、`mmw result integrate`。
- 宿主浏览器分支、Serena / Graphify 教程。
- `agents/openai.yaml`。

本轮不派冷读 subagent。不改 leaf。

## 先前阶段（中文重建）

第一阶段已经完成上游 `SKILL.md`、`scripts/hitl-loop.template.sh` 和 `agents/openai.yaml` 的逐行中文翻译。vendor 1.2.3 的 Redact 修补已进现役中文稿；本轮英文底稿直接用 vendor 1.2.3。

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐行中文翻译基线 |
| `translation-audit.md` | 术语选择、逐行完整性与无新增语义检查 |
| [candidate/](candidate/) | 本轮英文接线候选 |
