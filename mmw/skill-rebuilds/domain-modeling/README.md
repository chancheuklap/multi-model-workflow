# Domain Modeling 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW Domain Modeling。当前发布技能仍位于 `mmw/skills-src/mmw-domain-modeling/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文逆向（2026-08-16）

底稿是上游英文原文（`SKILL.md` 75 行、`CONTEXT-FORMAT.md`、`ADR-FORMAT.md`），只叠必要接线。候选是 **3 个文件**，按将来位于 `mmw/skills-src/mmw-domain-modeling/` 书写：

- [`candidate/SKILL.md`](candidate/SKILL.md)
- [`candidate/CONTEXT-FORMAT.md`](candidate/CONTEXT-FORMAT.md)
- [`candidate/ADR-FORMAT.md`](candidate/ADR-FORMAT.md)

现役技能源未改。上游本来就是三份：格式是按需打开的 reference，不并进 `SKILL.md`。

已叠进候选的接线：

- 入口三行：整件计划交给 `/mmw-grilling`（它会在同一场对话里调用本技能）；术语 / bounded context / ADR 留下；被调用则做完交回。
- 形态用 `mmw domain path`，落点用 `mmw domain dirs`。不把 `AGENTS.md` 的消费表再抄一遍。
- 多 bounded context 的 leaf 在 context 目录，不在 `src/<name>/CONTEXT.md`。这是 `mmw domain check` 的合同。
- 没有领域文档时不报缺失。第一个必须长期留下的术语谈清了再创建。
- 多个 bounded context 时 `mmw domain map-init`，然后登记首个 leaf。数量不清就问。
- 改 Context Map 或 leaf 之后 `mmw domain check` 退出 0 才算写完。
- 共享术语一份定义，其他 leaf 用 authoritative reference。
- 首次写入前 `[[mmw-require-task-branch]]`。不写 `git symbolic-ref` 讲义。
- ADR：`date` / `amends` 元数据块（`mmw artifact index adr` 要这两个字段）；编号用 `mmw domain adr-next`；wayfinder decision ticket 上写成 `draft-<ticket-number>-<slug>.md`。

未叠（现役有、上游没有、本轮当手续丢掉）：

- 「别的技能说按本节读领域文档」和与 `AGENTS.md` 种子重复的那张消费表。消费面仍由 `mmw domain sync` 写进 `AGENTS.md`。
- Context Map 合同逐条复述 CLI 已能拒绝的每一项。留下表头规则、例子、`mmw domain check`。
- Relationships「至少一项」——`map-init` 骨架是空列表，CLI 也不查这一项。
- 权威引用例子里的 `../ordering.md`。leaf 都在同一 context 目录里，正确相对路径是 `./ordering.md`。现役例子会让 `mmw domain check` 失败。
- 结果分支合回后改正式编号的步骤。英文 wayfinder 候选已经不写 integrate；CLI `mmw domain adr-next` 的帮助文本仍说合回后再取号。本技能只负责写出 draft。改号留给 integrate / wayfinder 以后那一轮。
- 冷读式路由教程。

同轮不改 wayfinder / grilling 候选。grilling 已经在同一场对话调用 `/mmw-domain-modeling`；wayfinder 已经要求 ADR 用 `draft-<ticket-number>-<slug>.md`。

### 发布时的 leaf 与级联（未改现役）

- `docs/context/project-context.md`：`领域模型` → `domain model`；`权威引用` → `authoritative reference`；`canonical 术语` → `canonical term`。草稿见 [`candidate/leaf-terms.md`](candidate/leaf-terms.md)。
- `CONTEXT-MAP.md` 的 Owns 列跟着改这三个名字。
- `mmw/cli/seeds/AGENTS-domain-context.md` 仍是中文「领域文档 / leaf」。发布本技能会短暂中英混用。种子英文化是 CLI 那一轮。
- `mmw/cli/seeds/CONTEXT-MAP-rules.md` 仍是中文提示。同上。
- 现役 `/mmw-wayfinder/walking.md` 仍写合回后改 ADR 正式编号。英文 wayfinder 候选删了那一步；发布两轮技能之前，改号这件事没有技能接。CLI 帮助还在。

本轮不派冷读 subagent。grilling 那一轮把方法正文和已有标签报成缺口，并因此加了不该加的教程。

## 先前阶段（中文重建）

第一阶段：上游 `SKILL.md`、`ADR-FORMAT.md`、`CONTEXT-FORMAT.md` 和 `agents/openai.yaml` 的逐行中文翻译。第二阶段精简稿与翻译基线逐字一致。第三阶段在 `../candidate/skills/mmw-domain-modeling/` 加入中文接线。那些候选不是本轮英文底稿。

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐行中文翻译基线 |
| `translation-audit.md` | 术语选择、逐行完整性与无新增语义检查 |
| `simplified.zh-CN.md` | 与翻译基线逐字一致的精简层 |
