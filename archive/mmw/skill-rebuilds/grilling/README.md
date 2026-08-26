# Grilling 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW Grilling。当前发布技能仍位于 `mmw/skills-src/mmw-grilling/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文逆向（2026-08-16）

底稿是上游英文原文（22 行），只叠必要接线。候选是 **1 个文件**：[`candidate/SKILL.md`](candidate/SKILL.md)，按将来位于 `mmw/skills-src/mmw-grilling/SKILL.md` 书写。现役技能源未改。

`grill-me` 与 `grill-with-docs` 是上游 7 行包装。方法并进本技能：`grill-with-docs` 的 `/domain-modeling` 写成同一场对话里调用 `/mmw-domain-modeling`。

已叠进候选的接线：

- `/mmw-domain-modeling` 在谈清的那一刻调用，不攒到最后。
- 事实：自己查 / `/mmw-research` / `/mmw-prototype` / `/mmw-to-questionnaire` / 各开一页。不教这些技能怎么做。
- 调用方给了 Required materials 时，按 `/mmw-wayfinder` 解析。不把解析步骤抄进来。
- 共同理解记录落 `understanding.md`（HITL 关卡）。三段英文标题：`Round Q&A`、`Shared understanding`、`Supporting materials`。
- 这次点头不能顶替 spec 定稿。
- 可选 ⓪：问一句，等回答，再交 `/mmw-review`。
- 调用方交回路径；用户直接调用则问 spec / prototype / 停。

未叠（现役有、上游没有、本轮当手续丢掉）：

- 浏览器截图、viewport、正式原型目录的长手续。留一句：每个页面各自打开。
- 「解析必读材料声明」这个节名。wayfinder 候选里那一节已经不在。
- 五项交接表。
- 冷读式路由教程。

同轮改了 wayfinder 候选一处：resolution comment 转录 `## Shared understanding`，不再写 `## 共同理解`。

2026-08-16：`/mmw-research` 交回 README 路径。本候选改为读索引和它列出的文件，再把事实放回设计树。Supporting materials 不再写 synthesised facts。

### 发布时的 leaf 与级联（未改现役）

- `docs/context/delivery-workflow.md`：`共同理解` → `shared understanding`；`共同理解记录` → `shared-understanding record`。定义草稿见 [`candidate/leaf-terms.md`](candidate/leaf-terms.md)。
- 现役 `/mmw-to-spec`、`/mmw-reviewer` 的 `understanding.md` 仍读 `## 共同理解` / `## 逐轮问答`。它们还没英文化时，发布本技能会短暂对不上标题。to-spec 与 reviewer 各自那一轮改。
- 人工审批关卡那一条仍写「确认共同理解」。发布 leaf 时改成 shared understanding。

本轮不派冷读 subagent。上一轮把方法正文和已有标签报成缺口，并因此加了不该加的教程。

## 先前阶段（中文重建）

第一阶段：上游逐段中文翻译。第二阶段精简稿与翻译基线逐字一致。第三阶段在 `../candidate/skills/mmw-grilling/` 加入中文接线。那些候选不是本轮英文底稿。

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐段中文翻译基线 |
| `translation-audit.md` | 术语选择、逐段完整性与无新增语义检查 |
| `simplified.zh-CN.md` | 与翻译基线逐字一致的精简层 |

