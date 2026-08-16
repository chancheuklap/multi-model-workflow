# Wizard 重建区

这个目录用于从 Matt Pocock Skills 重新建立 MMW Wizard。当前发布技能位于 `mmw/skills-src/mmw-wizard/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文逆向（2026-08-16）

底稿是上游英文原文（vendor `1.2.3`：`SKILL.md` + `template.sh`），只叠必要接线。候选按将来位于 `mmw/skills-src/mmw-wizard/` 书写。现役技能源目录已改为 `mmw-wizard`。技能名是 `mmw-wizard`。

`template.sh` 是上游 1.2.3 原文。`STAGES` 标记上方一个字都没改。

已叠进候选的接线：

- 首次写入前 `[[mmw-require-task-branch]]`。
- 一次性 wizard 落 `mmw artifact path scratch --sub wizard/<procedure>.sh`。用户要可重复入口时写到他确认的正式路径，scratch 不留第二份。
- 一次性 wizard 在流程完成或放弃后从 scratch 删掉。

未叠：

- 「只发生一次就不回本」的劝退句。
- 完成表。
- `agents/openai.yaml`。

本轮不派冷读 subagent。不改 leaf。

## 先前阶段（中文重建）

第一阶段已经完成上游 `SKILL.md`、`template.sh` 和 `agents/openai.yaml` 的逐行中文翻译。vendor 1.2.3 去掉了 `TOTAL_MINUTES`；本轮英文底稿直接用 vendor 1.2.3。

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐行中文翻译基线 |
| `translation-audit.md` | 术语选择、逐行完整性与无新增语义检查 |
| [candidate/](candidate/) | 本轮英文接线候选 |
