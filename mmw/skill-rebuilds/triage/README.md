# Triage 重建区

这个目录用于从 Matt Pocock Skills 重新建立 MMW Triage。当前发布技能仍位于 `mmw/skills-src/mmw-triage/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文逆向（2026-08-16）

底稿是上游英文原文（vendor `1.2.3`：`SKILL.md`、`AGENT-BRIEF.md`、`OUT-OF-SCOPE.md`），只叠必要接线。候选按将来位于 `mmw/skills-src/mmw-triage/` 书写。现役技能源未改。技能保持 user-invoked。

needs-info 模板留在 `SKILL.md`，跟上游一样。例子留在 `AGENT-BRIEF.md`，跟上游一样。

已叠进候选的接线：

- `/setup-matt-pocock-skills` 换成仓库根 `.mmw.json` 的 `tracker.labels`。
- 裸 `#42`：先 `gh issue view`，不是 issue 再 `gh pr view`。
- `/grilling` → `/mmw-grilling`；`/domain-modeling` → `/mmw-domain-modeling`。领域文档用 `mmw domain path`。
- 调用写成 `/mmw-triage`。
- `ready-for-agent` 贴完 brief 后问：开始实现、写 spec、还是到这里停。
- `AGENT-BRIEF.md` 增加 **Test seam**。点不出 correct seam 就改判 `ready-for-human`。

未叠：

- `NEEDS-INFO.md`、`examples.md` 拆文件。
- 四栏上下文表、角色存在理由、半路开新 issue。
- `/mmw-implement` 替维护者把关的长说明。
- `agents/openai.yaml`。

本轮不派冷读 subagent。不改 leaf。`agent brief` / `ready-for-agent` 已在现役用语里。

## 先前阶段（中文重建）

第一阶段已经完成上游 `SKILL.md`、`AGENT-BRIEF.md`、`OUT-OF-SCOPE.md` 和 `agents/openai.yaml` 的逐行翻译。旧中文接线候选在 `../candidate/skills/mmw-triage/`，不是本轮英文底稿。

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐行中文翻译基线 |
| `translation-audit.md` | 术语选择、逐行完整性与无新增语义检查 |
| [candidate/](candidate/) | 本轮英文接线候选 |
