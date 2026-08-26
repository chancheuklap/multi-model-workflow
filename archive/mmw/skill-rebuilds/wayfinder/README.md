# Wayfinder 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW Wayfinder。当前发布技能仍位于 `mmw/skills-src/mmw-wayfinder/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文逆向（2026-08-15）

底稿是上游英文原文，只叠用户已勾的 MMW 差异。候选是 **1 个文件**：[`candidate/SKILL.md`](candidate/SKILL.md)，按将来位于 `mmw/skills-src/mmw-wayfinder/SKILL.md` 书写。发布时一并替换的 leaf 草稿：[`candidate/wayfinding.md`](candidate/wayfinding.md) → `docs/context/wayfinding.md`。现役四文件技能源未改。

已勾、写进候选的：

- 一份文件，Chart 与 Walk 仍是同一文件里的两个入口。无 `charting.md` / `walking.md` / `closing.md`。
- map 正文 `## Branch`（现役 `## 分支`）。
- ticket 正文 `## Required materials`（现役 `## 必读材料声明`）。解析收成模板下两句：`mmw artifact path`，以及读 `<!-- mmw:conclusion -->`。
- 步骤里的 `mmw issue create / link / claim / frontier / append`。无独立 tracker 文档。
- research 走 `mmw artifact path` + resolution comment，直接保存。无 throwaway `research/<name>` 分支。`/mmw-research` 交回 README 路径；写 `## Answer` 前读索引和它列出的 findings 文件。prototype ticket 同样：读 `/mmw-prototype` 交回的 README 和它列出的文件。
- ADR 文件名 `draft-<ticket-number>-<slug>.md`。
- 已确认精简：一次 session 替代 100K；research 含仓库源码；无 `/setup-matt-pocock-skills`；grilling 只调 `/mmw-grilling`；无 `disable-model-invocation`。

已勾、未写进候选的：

- 并发 worktree 专节；禁止占用 map 树；四类 ticket 五项交接表；`/mmw-wizard`；三个 SHA；`mmw result integrate`；`closing.md`。开树和合回由用户另开会话做。

### 发布时的 leaf 与级联（未改现役）

- `docs/context/wayfinding.md` 换成 `candidate/wayfinding.md`。`decision ticket` 不再要求自己的任务分支。删 `交回评论`（本技能不再写 `<!-- mmw:handback -->`）。`CONTEXT-MAP.md` 的 Owns 列跟着改。
- `delivery-workflow.md` 的 `共同理解` 在发布本技能时改成 `shared understanding`（本技能第一次用这个英文名）。现役 `/mmw-grilling` 仍写 `## 共同理解`，发布前是混用窗口。
- 现役 `/mmw-grilling` 仍写「按 `/mmw-wayfinder` 的解析必读材料声明读取」。发布后那一节不在了；grilling 那一轮改成读 Required materials 那两句。
- 已有 map 的 `## 分支` / `## 必读材料声明` / `## 答案` 不会自动改名。新 map 用英文标题。
- `mmw artifact list` 已删除。现役 wayfinder 由 agent 自己写 Required materials 行，再用 `artifact path` 解析。
- `handback-comment` 仍在 CLI 产物类型里。本技能不再生产它；删不删留给 CLI 自己那一轮。

## 先前阶段（中文重建，已过时）


第一阶段已经完成上游原文的逐段中文翻译。翻译保持上游章节顺序、方法、步骤、完成判据、例子和解释性文字，不加入 MMW 的 tracker、worktree、领域文档、报告验证、资产或人工审批关卡。

第二阶段已经形成单文件精简稿。它只应用已经确认的四项调整：删除 100K token 数字、收窄并补全 Prototype 合同、删除上游 tracker 通用安装与 fallback、把 Grilling 双重调用收敛到 `/mmw-grilling`。

第三阶段已经在 `../candidate/skills/mmw-wayfinder/` 形成四文件候选。共享方法保留在 `../candidate/skills/mmw-wayfinder/SKILL.md`；Chart the map、沿 map 推进和 MMW 收尾分别按调用分支放在 `../candidate/skills/mmw-wayfinder/charting.md`、`../candidate/skills/mmw-wayfinder/walking.md` 和 `../candidate/skills/mmw-wayfinder/closing.md`。候选增加 tracker 命令、research 验证与保存、产物目录、持久资产和下游技能接线。

ticket 正文只写 `Question`：`产物目录` 从 map 正文读，`issue-<编号>` 子目录由 ticket 自己的编号得到，因此建 ticket 不再需要 `gh issue edit` 回填。

会话隔离按 map 分支加任务分支处理：map 任务拥有 map 分支，每张 decision ticket 使用一条从 map 分支派生的任务分支，解决期间写下的领域 leaf、ADR 和资产提交在这条任务分支上，再交回 map 任务验证并集成。两个会话并发解 ticket 时，分开的 worktree 让冲突在合并时暴露；共用工作目录会直接互相覆盖。ADR 在任务分支上先用 `draft-<ticket 编号>-<slug>.md`，集成后由 map 任务分配正式编号。

`wayfinder:research` ticket 是 AFK：ticket 本身就是用户对这次调查的批准，所以这条路径上的 research 直接保存，不再逐张停下来询问。

收尾同时检查 open decision ticket 和 Not yet specified；剩余 fog 再次使用广度优先 grilling。路线清楚后，spec destination 把 map 名称、`产物目录` 和任务 slug 交给 `/mmw-to-spec`；非 spec destination 报告结果并结束 Wayfinding。Wayfinder 不预建 spec issue，不拆分 spec，也不建立 To Spec 回退、重开 map 或 rebase 流程。当前发布技能仍不修改。

唯一上游是：

[上游 Wayfinder `SKILL.md`](../../../vendor/mattpocock-skills/skills/engineering/wayfinder/SKILL.md)

当前文件：

- [upstream-1.2.2.zh-CN.md](upstream-1.2.2.zh-CN.md)：上游 `SKILL.md` 的中文翻译。每段用 HTML 注释标出对应的上游行号。
- [translation-audit.md](translation-audit.md)：本轮翻译使用的固定术语表，以及逐段完整性和语义检查结果。
- [simplified.zh-CN.md](simplified.zh-CN.md)：以精确翻译为基线形成的单文件精简稿。它继续保留上游行号注释，不包含 research、Invocation、worktree、资产或收尾接线。
- [candidate/](../candidate/skills/mmw-wayfinder/)：在精简稿外层增加 MMW 接线的四文件候选。这个目录仍不会被 `mmw skills materialize` 物化。

## 2026-08 复审确认

上游「sized to one 100K token agent session」的具体刻度在候选中改为「必须能在一次 agent session 内解决」。用户确认这是 MMW 自己的工作流取舍（各宿主与模型的窗口不同，不锚定具体数字），不是漏译。

## 2026-08 与 research 路由重构同轮的三处改动

1. **Research 类型判据扩张**（有意改写，用户确认）：上游 `SKILL.md:77` 是 "Use when knowledge outside the current working directory is required"；候选改为「读当前仓库的源码，或者文档、第三方 API、正式规范这类外部资源……事实靠取证就能得到、不需要人参与讨论时使用」。理由：`/mmw-research` 的 INTERNAL 方向（research 台账 2026-08 复审第 2 条）已经覆盖仓库内部取证，原判据把纯内部取证挡在 AFK Research 类型之外，只能挂成 HITL grilling ticket。发布时 `docs/context/wayfinding.md` 的 `wayfinder:research` 定义同步更新。
2. **walking.md 第 4 步评论措辞对齐 charting**：原「链接……prototype 或 research」未指明链接对象文件；改为与 charting 第 6 步一致的「prototype 的路径，或 research 的 `README.md` 精确路径」。
3. **charting.md 删除「明确写一句：这次直接保存」段**：该规则收进 `mmw-research/MAIN.md` 第 0 节入口合同表的 ticket 行（ticket 入口一律直接保存），调用方不再需要传旗标。原段的理由（ticket 即批准、并行不能各自停下）也随规则移到那里。charting 保留一句期望说明：ticket 入口不会停下来问用户。

## 2026-08-09 上游保真重扫补记

1. **charting 第 2 步曾丢失第二场 grilling**（漏译，已修）：上游 `SKILL.md:112` 是 "**Grill again**, breadth-first this time"。发布面一度写成「在当前 charting session 中采用**广度优先**方式」，增写了上游没有、含义相反的限定语，把第二场 grilling 降级成主 agent 在当前会话里的自我判断，frontier 因此失去轮次、frontier 计算、事实与决定的分工和终止条件。`upstream-1.2.2.zh-CN.md:136` 与 `simplified.zh-CN.md:131` 都正确，丢失发生在 candidate 阶段。`translation-audit.md` 审 `SKILL.md:112` 那一行时列了四项，唯独漏掉 `Grill again`。已恢复调用，并按上游 `surfacing` 语义写明本场目的与终止条件。
2. **frontmatter 删除 `disable-model-invocation: true`**（有意接线，此前未记）：上游 `SKILL.md:4` 有该字段，`simplified.zh-CN.md:4` 保留。发布面删除它，与上一条在同一阶段发生。删除是必要的：grilling、to-spec 等技能要调得着 wayfinder，而按 `writing-for-agents/SKILL-MECHANICS.md`，标了该字段的技能任何技能都够不到。因此 MMW 的 wayfinder 是 model-invoked，description 按模型可发现的写法带触发分支。行为不改，本条只补台账。

同轮对 `SKILL.md`、`charting.md`、`walking.md` 各跑了一次单文件冷读。修掉的命中：charting 开头与宿主动作块重复的「运行 mmw task state 确认…」一句删除，补任务 slug 取名规则；map 名称与 ticket 名称补「就是 issue 标题」的来源；两处 `answer.md` 补「先写文件再发评论」的产生步骤；walking 第 1 步补记 map 标题，第 3 步补「gh issue view 取 ticket 正文、Question 在正文里」，第 7 步分开「读交回的报告」与「读路径里的 diff」；charting 第 5 步删除本轮新写的「ticket 入口」措辞，改为直述。未修（记为 finding，等用户决定）：宿主动作块内「用户原话」「这个任务的 slug」「从 map 分支派生」等措辞是跨技能共享的同款块，改动会级联到 `mmw-prototype` 与 `mmw-improve-codebase-architecture`；`SKILL.md` 不写 tracker 具体命令是有意分层，命令全部在 charting/walking。
