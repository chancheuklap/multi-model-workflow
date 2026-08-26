# To Tickets 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW To Tickets。当前发布技能仍位于 `mmw/skills-src/mmw-to-tickets/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文逆向（2026-08-16）

底稿是上游英文原文（一份 `SKILL.md`，105 行）。候选是 **1 个文件**：[`candidate/SKILL.md`](candidate/SKILL.md)，按将来位于 `mmw/skills-src/mmw-to-tickets/SKILL.md` 书写。现役技能源未改。无 `disable-model-invocation`。

已叠进候选的接线：

- 只从已发布 spec 拆。调用方给 spec issue 编号。没有 `ready-for-agent` 就停，回 `/mmw-to-spec`。
- 读 spec 用 `mmw artifact path spec`。读 spec 的 `artifact_refs`。解析方式与 wayfinder 的 Required materials 相同，不把解析步骤抄进来。
- prefactor 需要多角度时调用 `/mmw-research`。它交回 README 路径；读索引和它列出的文件，再把事实写进消费它们的 ticket。
- 首次写入前 `[[mmw-require-task-branch]]`。
- 切片大小写成一个行为、`worker` 能端到端接下来（不写 100K / 一个 context window）。
- 验收四条判据；用户批准清单时必须看见验收标准。这是拆 ticket 自己的那次点头，不能用 grilling 或 spec 的点头顶替。
- 发布走 `mmw issue create --parent --blocked-by`。不打 `ready-for-agent`——那个标签等 plan 审。不关 spec issue。
- 按依赖顺序发，阻塞方先发：`mmw issue frontier` 按编号升序。
- ticket 正文 `## Plan` 写完整的 `mmw artifact path plan --sub <NN>-<ticket-slug>.md`。`## Artifact refs` 传给下游。
- 做完问：写 plan，还是停。

未叠：

- `/setup-matt-pocock-skills` 和本地 `.scratch/<feature-slug>/issues/` 那条 tracker 分支。MMW 只用 `mmw issue`。
- Matt 在本技能里给 ticket 打 `ready-for-agent`。MMW 要等 ② plan 审。
- Matt 的「Work the frontier」。开工是 `/mmw-implement` / `/mmw-to-plan`。
- 上下文五列表、prototype / research 怎么读的专节。ticket 只传 Artifact refs。
- `git symbolic-ref` 讲义、取 kebab 的专节、`/mmw-verifying-agent-output`。
- 文末下一步表。
- 冷读式路由教程。

同轮 to-spec 精简后不再写 `## Input sources`。本技能只读 spec 的 `artifact_refs`。

### 发布时的 leaf 与级联（未改现役）

- 现役 `/mmw-to-plan` 仍读 ticket 的 `## 产物引用`。发布本技能后那一节是 `## Artifact refs`。to-plan 那一轮改。
- 现役 `/mmw-to-plan` 仍读 spec issue 的 `## 输入出处`。精简后的 to-spec 不再写这一节。to-plan 那一轮改为读 spec 的 `artifact_refs`。

本轮不派冷读 subagent。

## 先前阶段（中文重建）

第一阶段：上游逐行中文翻译。接线候选在 `../candidate/skills/mmw-to-tickets/`。那些候选不是本轮英文底稿。

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐行中文翻译基线 |
| `translation-audit.md` | 术语选择、逐行完整性与无新增语义检查 |
