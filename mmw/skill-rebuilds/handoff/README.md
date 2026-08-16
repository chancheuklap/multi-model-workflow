# Handoff 重建区

这个目录用于从 Matt Pocock Skills 重新建立 MMW Handoff。当前发布技能位于 `mmw/skills-src/mmw-handoff/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文逆向（2026-08-16）

底稿是上游英文原文（vendor `1.2.3`：一份 7 行 `SKILL.md`），只叠必要接线。候选按将来位于 `mmw/skills-src/mmw-handoff/SKILL.md` 书写。现役技能源目录已改为 `mmw-handoff`。技能名是 `mmw-handoff`。保持 user-invoked。

上游正文几乎原样留下：写到操作系统临时目录，不写进当前工作区；suggested skills；不重复已有产物；脱敏；用户参数当作下一场焦点。

已叠进候选的接线：

- suggested skills 用 MMW 技能名（`/mmw-grilling`、`/mmw-to-spec` 这类）。

未叠：

- 改成 `mmw artifact path`。上游明确写操作系统临时目录。
- `agents/openai.yaml`。`SKILL.md` 已有 `disable-model-invocation: true`。现役仍有这份 Codex 包装；发布时不要再拷进去。

本轮不派冷读 subagent。不改 leaf。
