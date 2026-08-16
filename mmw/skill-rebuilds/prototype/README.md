# Prototype 重建区

这个目录用于从 Matt Pocock Skills 1.2.2 重新建立 MMW Prototype。当前发布技能仍位于 `mmw/skills-src/mmw-prototype/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文逆向（2026-08-16）

底稿是上游英文原文（`SKILL.md` + `LOGIC.md` + `UI.md`）。候选是 **3 个文件**：[`candidate/SKILL.md`](candidate/SKILL.md)、[`candidate/LOGIC.md`](candidate/LOGIC.md)、[`candidate/UI.md`](candidate/UI.md)，按将来位于 `mmw/skills-src/mmw-prototype/` 书写。无 `capture.md`。现役四文件技能源未改。

上游骨架留下：问题决定形态、两条主分支、六条共同规则、Logic 的 shareable demo、UI 的 radically different variants 与 floating switcher。throwaway 只约束写法。

已叠进候选的接线：

- 文件留在仓库，走 `mmw artifact path prototype`。`README.md` 是索引，不是可运行的 prototype。下游点名 README，再读它列出的文件。
- 一轮一个问题；后续轮次改同一份资产。
- 本轮只走一条分支。第三条「看一次输出就够」留在 `SKILL.md`，不另开文件。
- 走查：用户操作。各开一页。不替用户点、选、宣布完成。
- 外部系统既有表现交给 `/mmw-research`。问题还走查不了交给 `/mmw-grilling`。
- 首次写入前 `[[mmw-require-task-branch]]`。调用方传了 `--name` / `--issue` 就加上。
- Logic 的纯 `module` 单独成文件；HTML 外壳不列为可复用、不挂产品路由。
- UI 变体留在这份 prototype 里。选中的写成 current UI。本技能不折进正式代码。
- 多个结构方向并行时，派一组宿主自带的可写 subagent，`current` worktree。不派 `prototype-worker`，不派 `worker`。
- 提交本轮文件。UI 轮提交后跑 `/mmw-ui-qa`，不替代走查。

未叠：

- throwaway 分支、不进 main、本技能负责折进正式代码。
- `capture.md`、目录树、浏览器步骤表、变体 `preview/` 目录、撞名 `-02`、四栏 task 开篇。
- 把 Logic HTML 再绕去 `/mmw-wait-what`。

同轮改了 wayfinder 候选 `## Answer` 一句：prototype ticket 读 README 和它列出的文件。

leaf 草稿见 [`candidate/leaf-terms.md`](candidate/leaf-terms.md)。

本轮不派冷读 subagent。

## 先前阶段（中文重建）

第一阶段已经完成上游 `SKILL.md`、`LOGIC.md`、`UI.md` 和 `agents/openai.yaml` 的逐行中文翻译。翻译保留 logic 与 UI 两条分支、共同规则、可移植 logic module、引导式走查、UI 子形态、variant switcher、用户反馈迭代和一手来源留存，不加入 MMW prototype 资产接线。

第二阶段已经形成单文件精简稿。它只应用已经确认的调整：把 prototype 改为持续迭代的仓库资产；允许后端脚本、Logic HTML 和 UI/UX 在同一份 prototype 中连续演进；按是否需要用按钮驱动状态模型选择最小后端脚本或 Logic HTML；只在 UI 结构方向未定时生成多个变体；允许达到项目质量要求的可移植内容被直接复用；把外部系统取证分支移出本技能、删除固定三状态字面量和单独的人工审批关卡。

第三阶段已经在 `../candidate/skills/mmw-prototype/` 形成四文件候选。那份中文候选不是本轮英文底稿。

| 文件 | 作用 |
| --- | --- |
| [upstream-1.2.2.zh-CN.md](upstream-1.2.2.zh-CN.md) | 上游 1.2.2 的逐行中文翻译基线 |
| [translation-audit.md](translation-audit.md) | 术语选择、逐行完整性与无新增语义检查 |
| [simplified.zh-CN.md](simplified.zh-CN.md) | 以精确翻译为基线形成的单文件精简稿 |
| `../candidate/skills/mmw-prototype/` | 中文四文件候选。不是本轮英文底稿。 |

## 2026-08 复审改动（中文候选）

复审确认中文候选把 prototype 从上游「一次性反应物」改为「持久资产」后，丢掉了上游的第二道防线（`UI.md`「Promoting the prototype directly to production… Rewrite it properly when you fold it in」、`LOGIC.md`「Don't ship the HTML shell into production」）。已补回中文候选。英文候选用上游反模式段承担同一道防线。
