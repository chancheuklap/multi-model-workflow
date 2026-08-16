# Codebase Design 重建区

这个目录用于从 Matt Pocock Skills 重新建立 MMW Codebase Design。当前发布技能仍位于 `mmw/skills-src/mmw-codebase-design/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文逆向（2026-08-16）

底稿是上游英文原文（vendor `1.2.3`：`SKILL.md`、`DEEPENING.md`、`DESIGN-IT-TWICE.md`），只叠必要接线。候选按将来位于 `mmw/skills-src/mmw-codebase-design/` 书写。现役技能源未改。

已叠进候选的接线：

- 技能名 `mmw-codebase-design`。Going deeper 里的并行设计写成 `designer`。
- `DESIGN-IT-TWICE.md`：`[[mmw-launch:designer:none]]`。`CONTEXT.md` 换成 `mmw domain path`。
- `DEEPENING.md` 末尾一句：挪 seam 写进 spec，跟用户谈定后再 `/mmw-implement`。`worker` 落地时不发明 seam。
- 英文 [`candidate/mmw-designer.md`](candidate/mmw-designer.md) 角色正文，发布进 `mmw/agent-src/bodies/mmw-designer.md`。

未叠：

- 四栏 task 表。
- 「两份设计同形状就重派」——上游已要求 radically different。
- `agents/openai.yaml`。

本轮不派冷读 subagent。不改 leaf。词汇已在 `docs/context/` 的 architecture 相关 leaf。

## 先前阶段（中文重建）

第一阶段已经完成上游 `SKILL.md`、`DEEPENING.md`、`DESIGN-IT-TWICE.md` 和 `agents/openai.yaml` 的逐行中文翻译。翻译保留 deep module 词汇、依赖分类、seam 纪律、测试策略和并行设计方法，不加入 MMW 角色或流程接线。

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐行中文翻译基线 |
| `translation-audit.md` | 术语选择、逐行完整性与无新增语义检查 |
| [candidate/](candidate/) | 本轮英文接线候选 |
