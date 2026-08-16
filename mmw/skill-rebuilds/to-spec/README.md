# To Spec 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW To Spec。当前发布技能仍位于 `mmw/skills-src/mmw-to-spec/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文逆向（2026-08-16）

底稿是上游英文原文（一份 `SKILL.md`，模板写在同一个文件里）。候选也是 **1 个文件**：[`candidate/SKILL.md`](candidate/SKILL.md)，按将来位于 `mmw/skills-src/mmw-to-spec/SKILL.md` 书写。现役技能源未改。无 `disable-model-invocation`。

上游第 1、2 步和模板正文（Problem Statement 到 Further Notes，含 prototype 例外）按原文保留。第 3 步在「写」和「发布」之间插入等待，不改这两句本身的措辞。

已叠进候选的接线：

- 决定可能不在当前对话：调用方给了 map、shared-understanding record 路径或 prototype `README.md` 路径就先读。分诊 issue 是输入不是 spec。缺决定就停。
- 写到 `mmw artifact path spec` 打出的路径。首次写入前 `[[mmw-require-task-branch]]`。`mmw artifact check` 非零先修 `artifact_refs`。
- 模板头六个元数据字段。发布前 `spec_issue: 0`，建 issue 后回填。
- Testing Decisions 末尾一张已确认 seam 表。条件式 `## Contract Boundaries`：每个合同要有名字，后面的 plan 引用条目名（2026-08-16 to-plan 同轮加的一句）。
- ① 先问再派，与 grilling 的 ⓪ 相同。
- 用户批准后才提交、才 `mmw issue create --label ready-for-agent`。
- 分诊 issue 的 `set-parent` 只写在发布那一段旁边。
- 做完问：拆 tickets，还是停。

未叠 / 本轮从候选拿掉：

- 五列表入口教程；wayfinder `--name`；SKILL 里第二张 seam 表；五条自检；① 材料清单；`## Input sources`；标签含义讲义；「四件事都成立」。
- Current State、Failure Paths、Visual Contract、Release Risk。这些内容写进 Implementation Decisions 或 Out of Scope。
- 独立 `spec-template.md`。模板回到与上游相同的位置：`SKILL.md` 里的 `<spec-template>`。
- `/setup-matt-pocock-skills`。
- `## Cross-Plan Contract Anchors`。接口形状只在 `## Contract Boundaries`。to-plan 候选不再往 spec 里加这一节。

同轮改了 to-tickets 候选：不再读 `## Input sources`；没有 `ready-for-agent` 时回 `/mmw-to-spec`，不再写「第 6 步」。

现役 `/mmw-to-plan` 仍读 spec issue 的 `## 输入出处`。精简后的 to-spec 不再写这一节。to-plan 候选读 spec 文件与 `mmw issue children`，不再读那一节。

本轮不改 leaf。`走查` 和 `## 输入出处` 都不在这份候选里出现。

本轮不派冷读 subagent。

## 先前阶段（中文重建）

第一阶段：上游逐段中文翻译。第二阶段精简稿曾削弱 user story 完成判据，候选已恢复上游原文。第三阶段在 `../candidate/skills/mmw-to-spec/` 加入中文接线。那些候选不是本轮英文底稿。

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐段中文翻译基线 |
| `translation-audit.md` | 术语选择、逐段完整性与无新增语义检查 |
| `simplified.zh-CN.md` | 只应用用户已经确认的精简 |
