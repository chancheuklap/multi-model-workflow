# Improve Codebase Architecture 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW Improve Codebase Architecture。当前发布技能仍位于 `mmw/skills-src/mmw-improve-codebase-architecture/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文逆向（2026-08-16）

底稿是上游英文原文（`SKILL.md` 72 行 + `HTML-REPORT.md`）。候选是 **2 个文件**：[`candidate/SKILL.md`](candidate/SKILL.md)、[`candidate/HTML-REPORT.md`](candidate/HTML-REPORT.md)，按将来位于 `mmw/skills-src/mmw-improve-codebase-architecture/` 书写。现役技能源已改成点名 Explore，不再派 `investigator`。

上游方法留下。探索改成一组 **Explore**，各走各的路；五问仍是心理线索，不分配、不切范围。同一处摩擦只写一张卡片。

已叠进候选的最小接线：

- 技能名 `/mmw-codebase-design`、`/mmw-grilling`、`/mmw-domain-modeling`。
- 领域文档走 `mmw domain path`，不写死只读根上的 `CONTEXT.md`。
- 保持 model-invoked（无 `disable-model-invocation`），好让 `/mmw-diagnosing-bugs` 能移交进来。description 带上这条触发。
- 点名 Explore，不用 `investigator`，不用 `[[mmw-launch:…]]`。

未叠：

- 3–4 个 `investigator`、四栏 task、独立去重节。
- 「本技能不改代码」、选中后 `[[mmw-require-task-branch]]`、类型 `refactor`、谈完问要不要写 spec。任务分支由 `/mmw-domain-modeling` 在落笔前处理；grilling 被别的技能调用时交回路径。

`HTML-REPORT.md` 是上游原文，只把 `/codebase-design` 改成 `/mmw-codebase-design`。

本轮不派冷读 subagent。

## 先前阶段（中文重建）

第一阶段已经完成上游 `SKILL.md`、`HTML-REPORT.md` 和 `agents/openai.yaml` 的逐行中文翻译。

第三阶段的接线候选已经建立在 `../candidate/skills/mmw-improve-codebase-architecture/`。那一轮**没有新增精简**——上游内容全部保留，所以不产生 `simplified.zh-CN.md`。候选的基线不是翻译稿，而是当时的现役技能：那一轮要修的是现役与上游之间的**编排偏离**，不是从零重写。那份中文候选不是本轮英文底稿。

## 先前阶段：中文重建为什么开

复核发现现役第 2 步把上游的探索方法整个换掉了，而且换的方向正是上游那一节明确禁止的。

上游 `SKILL.md:18-35` 派**一个** agent（`subagent_type=Explore`）自然探索，并明写「不要遵循僵化的启发法；自然探索，并记录你遇到摩擦的位置」。那五个问题是给这一个 agent 的**心理线索**。

现役把五问拆成五个视角、一个视角一个 `investigator`，每个视角写死进 task 的「目标」栏——这恰恰是把启发法固化成了分工表。现役自己还留着「不要给它僵硬的打分表」这句，跟它上面那张视角分工表互相打架。后果是每个 `investigator` 只对自己那一条负责，落在五问之外的摩擦没有人报，而"哪里摩擦大"本来就不该由派工的人预先决定。

## 先前阶段：中文候选改了什么

| 位置 | 改动 | 依据 |
| --- | --- | --- |
| 第 2 步 | 五视角分工 → 派 3–4 个 `investigator`，**每份 task 完全一样**，都探整片区域；五问降级为写进 task 的「起手入口」，并原样附上「这五问是入口，不是清单，撞见之外的照样报」 | 恢复上游「自然探索、不用僵硬启发法」的方法效果；多样性改由各自独立的上下文提供，而不是由分配提供 |
| 第 3 步 | 改成「先去重，再逐条验证」，并写明重叠是预期之内的，几个人独立撞见同一处摩擦本身就是证据 | 同质并行的必然结果，原来的单视角结构不产生重叠，所以现役没有这一步 |
| 第 1 步 | 补回 YAGNI 和那句因果：做深的回报是让**将来**改它变容易，所以最近改动多的地方权重高；并补上「有实打实迹象说马上要大改的，即使 `git log` 安静也算热点」 | 上游 `SKILL.md:18` 原文有这层因果，现役只留了结论「最近一直在改的地方权重最高」，遇到「很久没改但即将大改」推不出该不该扫 |
| 第 4 步 | 补一句「这份报告以图为主，不是以文字为主」，卡片字段的「图」改成「before/after 图 — 整张卡片的重心，两列并排」 | 上游 `SKILL.md:37-60` 明写「报告必须以视觉内容为主」，现役只在 `HTML-REPORT.md` 里有，`SKILL.md` 这一层丢了 |
| 全文 | 「假 seam」→「一个 adapter 只是假设有这条 seam，两个 adapter 才证明它真的存在」 | 上游是 hypothetical（尚未证实），不是 fake（虚假）。这一处已经同步修进现役，候选跟着带 |

`../candidate/skills/mmw-improve-codebase-architecture/` 是那一轮的中文候选，不是本轮英文底稿。

那一轮未决 finding：`[[mmw-launch-group:…]]` 当时只认 `reviewers`。英文候选点名 Explore，不走占位块。

| 文件 | 作用 |
| --- | --- |
| `upstream-1.2.2.zh-CN.md` | 上游 1.2.2 的逐行中文翻译基线 |
| `translation-audit.md` | 术语选择、逐行完整性与无新增语义检查 |
| `../candidate/skills/mmw-improve-codebase-architecture/` | 中文接线候选。不是本轮英文底稿。 |
