# MMW 产出和使用的产物完整清单

范围快照：commit `b3d924ce9db88a7380dbcc13ad615aaa014454f9`，2026-08-11。

以下每条都由主 agent 打开引用位置核对过。行号指该 commit 下的实际行。

## 1. 产物清单

「Git」列写「是」表示该产物提交进仓库并长期保留；写「任务期间是」表示提交进仓库，但收尾时被删除。

| 产物 | 生产者 | 读取者 | 路径形状 | 名字来源 | Git |
| --- | --- | --- | --- | --- | --- |
| 领域文档、Context Map、leaf | `mmw-domain-modeling/SKILL.md:34-39,68-74` | 各技能按 `AGENTS.md` 领域规则读取，例如 `mmw-to-spec/SKILL.md:10,44`、`mmw-planner/SKILL.md:24` | `CONTEXT.md`、`CONTEXT-MAP.md`、`docs/context/` | 固定名；leaf 名由 bounded context 决定 | 是 |
| ADR | `mmw-domain-modeling/SKILL.md:96,110` | 同上 | `docs/adr/0001-<slug>.md`；Wayfinder 先写 `draft-<ticket 编号>-<短名>.md` 再转正式编号（`mmw-wayfinder/walking.md:59,100`） | 四位序号由 `mmw domain adr-next` 给出 | 是 |
| prototype 资产与索引 | `mmw-prototype/SKILL.md:36-39,51-68`、`capture.md:3,24-40` | `mmw-to-spec/SKILL.md:20`、`mmw-to-tickets/SKILL.md:20-24`、`mmw-to-plan/SKILL.md:28-31`、`mmw-planner/SKILL.md:22`、`mmw-implement/SKILL.md:56-57`、`mmw-review/SKILL.md:45-67` | `docs/prototypes/<产物目录>/`，Wayfinder 加 `issue-<编号>/`；内含 `README.md`、`logic/`、`mockup/current/`、`mockup/variants/<问题 slug>/` | 产物目录 | 是 |
| research 索引、报告、配套文件 | `mmw-research/MAIN.md:82-108` | `mmw-grilling/SKILL.md:46-48`、`mmw-to-spec/SKILL.md:59,71`、`mmw-to-tickets/SKILL.md:21-24`、`mmw-to-plan/SKILL.md:30-31`、`mmw-planner/SKILL.md:23`、`mmw-implement/SKILL.md:57`、`mmw-review/SKILL.md:47-67` | 普通任务 `docs/research/<产物目录>/<主题>/`；Wayfinder `docs/research/<产物目录>/issue-<编号>/<主题>/` | 产物目录 + 主题 | 是 |
| 外部实测计划与 raw evidence | `mmw-research/EVIDENCE.md:20,70-88` | 同 research | research 目录内的 `test-plan.md`、`report.md`、`raw/` | 同 research | 是 |
| spec | `mmw-to-spec/SKILL.md:40,55` | `mmw-to-tickets/SKILL.md:20`、`mmw-to-plan/SKILL.md:19,28`、`mmw-planner/SKILL.md:19`、`mmw-implement/SKILL.md:16,26`、`mmw-review/SKILL.md:58-67`、`mmw-closing/SKILL.md:45` | `docs/specs/<任务 slug>/<任务 slug>.md` | 任务 slug | 任务期间是；`mmw-closing/SKILL.md:88` 删除 |
| plan | `mmw-planner/SKILL.md:38`，由 `mmw-to-plan/SKILL.md:68-82` 派发 | `mmw-implement/SKILL.md:29,54`、`mmw-review/SKILL.md:32,50-52`、`mmw-closing/SKILL.md:46` | `docs/plans/<任务 slug>/<NN>-<ticket-slug>.md`；`NN` 是 ticket 两位编号，`ticket-slug` 由标题压缩（`mmw-to-tickets/SKILL.md:105-115`） | 任务 slug | 任务期间是；`mmw-closing/SKILL.md:88` 删除 |
| 界面验收 evidence | `mmw-implement/SKILL.md:99`、`mmw-review/SKILL.md:73` | 只加进「对照终审」的读栏（`mmw-review/SKILL.md:73`） | 临时 `.scratch/<任务 slug>/evidence/`；用户要留则挪进 `docs/evidence/<任务 slug>/` | 任务 slug | 临时否；保留后是 |
| 共同理解记录 | `mmw-grilling/SKILL.md:62-74` | `mmw-review/SKILL.md:30,47`、`mmw-reviewer/references/understanding.md:5-31` | `.scratch/<产物目录>/understanding.md` | 产物目录 | 否 |
| 审查记录与审查 task | `mmw-review/SKILL.md:77-99`；集成记录 `mmw-integrate/SKILL.md:79` | `mmw-release/SKILL.md:16-17`、`mmw-closing/SKILL.md:21,104-106`、`mmw-start/resuming.md:28-31` | `.reviews/<任务 slug>-<understanding\|spec\|plan\|final>.md`、`.reviews/<任务 slug>-<哪一道>-<任务名>.prompt.md`、`.reviews/<任务 slug>-integration-<YYYY-MM-DD>.md` | 任务 slug | 否 |
| 派发四栏 task 与角色报告 | 报告由 adapter 写：`mmw/cli/adapters/claude-code.sh:85-97` | `mmw-closing/SKILL.md:104-106` 只按归属清理 | `.dispatch/<角色>-<task 文件基名>.md` | 角色名 + task 文件基名 | 否 |
| 派发进度日志 | `mmw/cli/adapters/claude-code.sh:90-97,143-159` | 失败时输出路径给主 agent | `<paths.scratch>/dispatch/<角色>-<task 基名>.log`；成功后删除 | 同上 | 否 |
| Wayfinder map | `mmw-wayfinder/charting.md:27-33` | `mmw-wayfinder/walking.md:5-20`、`closing.md:5-17`、`mmw-to-spec/SKILL.md:22`、`mmw-release` 读 `分支` 一节 | GitHub issue，带 `wayfinder:map`；正文固定七节 | issue 编号 | issue 不进仓库 |
| decision ticket 与结论评论 | 正文 `mmw-wayfinder/charting.md:35-42`；评论 `charting.md:60-67`、`walking.md:65-69` | `mmw-wayfinder/walking.md:34-50`、`mmw-to-spec/SKILL.md:22` | GitHub issue，带 `wayfinder:<类型>`；正文只有 `## Question` | issue 编号 | issue 不进仓库 |
| spec issue | `mmw-to-spec/SKILL.md:79-89` | `mmw-to-tickets/SKILL.md:24`、`mmw-to-plan/SKILL.md:19-45`、`mmw-closing/SKILL.md:96` | GitHub issue，带 `ready-for-agent` | issue 编号 | issue 不进仓库 |
| tracer bullet ticket | `mmw-to-tickets/SKILL.md:80-115` | `mmw-to-plan/SKILL.md:43`、`mmw-implement/SKILL.md:29`、`mmw-review` plan 审与终审 | GitHub issue，spec issue 的子 issue；正文七节：`Parent`、`What to build`、`Plan`、`Acceptance criteria`、`prototype 资产`、`research`、`Blocked by` | issue 编号 | issue 不进仓库 |
| agent brief | `mmw-triage/SKILL.md:103-110`、`AGENT-BRIEF.md:3` | `mmw-to-spec/SKILL.md:21`、`mmw-implement/SKILL.md:17` | GitHub issue 评论，固定从 `## Agent Brief` 开始 | 所在 issue 编号 | issue 不进仓库 |
| `.out-of-scope/` 记录 | `mmw-triage/SKILL.md:107-110`、`mmw-wayfinder/walking.md:61` | `mmw-triage/SKILL.md:87-95`、`OUT-OF-SCOPE.md:70-82` | `.out-of-scope/<概念>.md`，概念名 kebab-case | 概念名 | 是 |
| Wiki spec 页与导航 | `mmw-closing/SKILL.md:35-74` | `mmw wiki nav` 扫描重建导航；`mmw wiki verify` 校验；`mmw-start/resuming.md:29` | Wiki 根 `Spec-<任务 slug>.md`、`Home.md`、`_Sidebar.md`；首行 `<!-- mmw:spec ... -->` | 任务 slug | 属 Wiki 仓库 |
| 出包状态与阶段产物 | `mmw/release/release-flow.sh:592-628,943-1016` | `mmw release where`、`receipt`、`dispatch` | `<paths.release>/release-state.json`、`<paths.release>/release-artifacts/a<序号>-<stage>/` | attempt 序号 + stage 名 | 否 |
| 交付记录 | `mmw/release/release-flow.sh:1262-1285`、`mmw-release/driving.md:52-57` | `mmw-release/SKILL.md:58-67` 核对 `source_commit` | 主仓库根 `<paths.release>/delivered/<product>.json` | 产品名 | 否 |
| 结构图谱 | `mmw/mcp/graphify_ensure.py:19-25,158-166,398-462` | Graphify MCP 查询前确保新鲜；`mmw graph verify`（`mmw/cli/lib/graph.sh:23-48`） | 仓库根 `graphify-out/graph.json`、`.mmw-freshness.json`、`.mmw-ensure.lock`、两个 `.mmw-backup.*` | 固定名 | 否 |
| 任务 worktree | `mmw/cli/lib/task.sh:130-132,174-202` | `mmw task state`、`result verify`、`result integrate`、`task cleanup` | `<paths.worktrees>/<任务 slug>`；Wiki clone 为 `<paths.worktrees>/.wiki` | 任务 slug | 否 |
| questionnaire | `to-questionnaire/SKILL.md:24-35` | 用户或知识持有者填写，调用方吸收答案（`to-questionnaire/SKILL.md:69-73`） | `.scratch/<产物目录>/<子目录>/to-questionnaire-<主题 slug>.md` | 产物目录 + 主题 slug | 否 |
| wizard 脚本 | `wizard/SKILL.md:46-74` | 用户执行 | `.scratch/<产物目录>/<子目录>/wizard-<流程 slug>.sh` | 产物目录 + 流程 slug | 否 |
| bug 诊断过程材料 | `mmw-diagnosing-bugs/SKILL.md:21-32` | 诊断阶段自身 | `.scratch/<产物目录>/<子目录>/` | 产物目录 | 否 |
| handoff、架构候选报告、解释 HTML | `handoff/SKILL.md:8-16`、`mmw-improve-codebase-architecture/SKILL.md:63-67`、`wait-what/VISUAL.md:13-19` | 新会话或用户 | 操作系统临时目录；`architecture-review-<时间戳>.html` | 时间戳 | 否 |

## 2. 名字来源只有两个，而且互不统一

`mmw/skills-src/` 下（已排除 `mmw-setup/`）：`<slug>` 出现 43 处，`<任务 slug>` 12 处，`<产物目录>` 分布在 20 个文件里。

| 名字 | 定义位置 | 用它的产物 |
| --- | --- | --- |
| 任务 slug | `docs/context/delivery-workflow.md:60` 规定 spec 落 `docs/specs/<任务 slug>/` | spec、plan、evidence、审查记录、Wiki 页、任务 worktree |
| 产物目录 | `docs/context/wayfinding.md:19-21`：一个 effort 的 prototype、research、evidence 和 scratch 共用的单个安全路径段 | prototype、research、scratch、共同理解记录、questionnaire、wizard、bug 过程材料 |

`mmw-wayfinder/closing.md:41` 把两者作为**两个独立值**分别交给 `/mmw-to-spec`：产物目录取自 map 正文，任务 slug 另取 map 标题的短名。两个值可以不同。

`mmw-to-spec/SKILL.md:26-40` 有一张五行的「确定任务 slug」表，其中一行是「使用这次 prototype 使用的 `产物目录`」。

`docs/context/wayfinding.md:20` 声明「evidence」由产物目录决定，而 `mmw-implement/SKILL.md:99` 与 `mmw-review/SKILL.md:73` 实际写的是 `.scratch/<任务 slug>/evidence/` 和 `docs/evidence/<任务 slug>/`。leaf 与技能源在这一项上不一致。

## 3. 已确认的落点冲突

### 3.1 共同理解记录在 Wayfinder 下丢掉上层目录

`mmw-grilling/SKILL.md:62` 原文：

> 第一件：把这次访谈写成一份**共同理解记录**，`.scratch/<产物目录>/understanding.md`。`<产物目录>` 用这次讨论主题的短横线名字，进入 `/mmw-to-spec` 时沿用同一个；解决 Wayfinder 的 decision ticket 时用 `issue-<编号>`。

它把 `<产物目录>` **整段替换**成 `issue-<编号>`，结果是 `.scratch/issue-<编号>/understanding.md`。而 `mmw-wayfinder/charting.md:54` 与 `walking.md:36-50` 传给下游的 scratch 路径是 `.scratch/<产物目录>/issue-<编号>`。两者指向不同目录。

### 3.2 界面 evidence 落在产物目录之外

`mmw-closing/SKILL.md:98-102` 自己写出了这个后果：

> 当前任务的 scratch 目录是：Wayfinder 派生的 spec 用 `.scratch/<产物目录>/task-<任务 slug>`，普通 spec 用 `.scratch/<产物目录>`。只删除这一个目录。
>
> 界面证据另有一个落点 `.scratch/<任务 slug>/evidence/`（`/mmw-implement` 的界面验收和 `/mmw-review` 的终审取证都写这儿）。普通 spec 的产物目录就是任务 slug，它正好在上面那个目录里，一起删掉；**Wayfinder 派生的 spec 两个 slug 不同，它落在外面**，那时另外删这一个目录。

收尾技能为这处不一致写了一段专门的补偿逻辑，并要求删两个目录。

### 3.3 派发四栏 task 的落点没有统一规定

`mmw-closing/SKILL.md:104` 原文：

> `.dispatch/` 是派发产物的落点——走 `mmw dispatch` 派角色时，四栏表和它交回的报告都落在这儿。

`mmw/cli/adapters/claude-code.sh:85-97` 只写**报告**，文件名 `<角色>-<task 文件基名>.md`。四栏 task 由调用技能自己写，而 `mmw-research/MAIN.md:60` 只说「把四栏表写入 task 文件」，不规定路径。

实测：本次 research 派了 5 个 `investigator`，四栏 task 按 `mmw-research` 的写法落在 `.scratch/mmw-artifact-wiring/issue-19/` 和 `issue-20/`，`.dispatch/` 下只有 5 份报告。`/mmw-closing` 按 `mmw-closing/SKILL.md:104` 去 `.dispatch/` 清四栏表，会找不到。

### 3.4 spec 与 plan 不长期留在仓库里

`mmw-closing/SKILL.md:86-90` 原文：

> ## 6. 删本地文档，提交
>
> 「验证」一节那份清单全过之后，在任务分支上删掉 `docs/specs/<slug>/` 与 `docs/plans/<slug>/` 并提交。
>
> **持久 prototype 资产、用户选择保存的 research 与 evidence 不删。**

spec 与 plan 在收尾时从仓库删除，长期副本在 GitHub Wiki 的 `Spec-<任务 slug>.md`。prototype、research、evidence 留在仓库。

### 3.5 `docs/research/...[/issue-<编号>]/` 的可选层不是冲突

`mmw-to-tickets/SKILL.md:24` 写作 `docs/research/<产物目录>[/issue-<编号>]/<主题>/README.md`。这准确描述了两种入口各自的形状：普通任务没有 `issue-<编号>` 这一层，Wayfinder decision ticket 有。`mmw-wayfinder/charting.md:54` 传入上级目录 `docs/research/<产物目录>/issue-<编号>`，`mmw-research/MAIN.md:82-88` 再追加 `<主题>/`。最终形状与读取形状一致。

## 4. `.mmw.json` 的 `paths` 九项

`.mmw.json:111-120` 有九项。`mmw/cli/mmw.default.json:81-85` 只有四项：`scratch`、`reviews`、`release`、`worktrees`。

`mmw/cli/lib/init.sh:58-63` 原文：

```
      .paths.reviews //= $reviews |
      .paths.release //= $release |
      .paths.worktrees //= $worktrees |
      del(.paths.specs, .paths.plans, .paths.prototypes,
          .paths.research, .paths.evidence, .paths.investigations, .models)
```

`mmw init` 主动删除 `specs`、`plans`、`prototypes`、`research`、`evidence`、`investigations` 和 `models`。本仓库根 `.mmw.json` 仍带这五项，说明它没有跑过当前版本的 `mmw init`。

| 项 | 消费方 |
| --- | --- |
| `specs`、`plans`、`prototypes`、`research`、`evidence` | 无。只被 `init.sh:31-33,61-62` 当旧字段检测并删除 |
| `scratch` | `mmw/cli/adapters/claude-code.sh:90-97` 存派发进度日志；`init.sh:182-185` 加进 `.gitignore` |
| `reviews` | 没有 CLI 产物写入。`init.sh:182-185` 只为加进 `.gitignore` 而读它 |
| `release` | `mmw/release/release-flow.sh:29-40,616-627,943-953,1262-1285` |
| `worktrees` | `mmw/cli/lib/task.sh:130-132,174-202,205-243`；`mmw/cli/lib/wiki.sh:26-28` |

结论：**技能正文写死 `docs/specs/`、`docs/plans/`、`docs/prototypes/`、`docs/research/`、`docs/evidence/` 这五个路径，配置里的同名项没有任何代码读取，而且 `mmw init` 会把它们删掉。**

## 5. `mmw domain` 已有的落点查询

`mmw/cli/mmw:466-478` 列出子命令。实测输出（本 worktree，2026-08-11）：

```
$ mmw domain path
map	/Users/…/CONTEXT-MAP.md	这是索引：读它，再读取它列出的本次相关全部 leaf

$ mmw domain dirs
single	/Users/…/CONTEXT.md
map	/Users/…/CONTEXT-MAP.md
context	/Users/…/docs/context
adr	/Users/…/docs/adr
```

`domain path` 返回三列：形态、绝对路径、下一步指令。`domain adr-next` 扫描 ADR 目录里的 `NNNN-*.md` 算出下一个四位编号（`mmw/cli/lib/domain.sh:89-116`）。这是 MMW 现有的唯一一处「由命令回答产物落点」的实现，只覆盖领域文档和 ADR。

注意 `domain dirs` 返回的 `adr` 路径 `docs/adr` 在本仓库当前并不存在。命令返回配置值，不校验目录是否存在。

## 6. `mmw init` 不创建任何产物目录

`mmw/cli/lib/init.sh:24-301` 创建或更新：根 `.mmw.json`、根 `TESTING.md`、`AGENTS.md` 的领域上下文受管区块、`CLAUDE.md` 的 `@AGENTS.md` 导入、`.gitignore`、`.graphifyignore`、按语言检测到的工具链配置。

它**不创建** `docs/specs/`、`docs/plans/`、`docs/prototypes/`、`docs/research/`、`docs/evidence/`、`docs/adr/`，也不创建 Context Map（Map 要单独跑 `mmw domain map-init`，`context_docs.py:843-853`）。

`.gitignore` 由 `init.sh:176-202` 写入六项：`<paths.reviews>/`、`<paths.release>/`、`<paths.scratch>/`、`<paths.worktrees>/`、`.dispatch/`、`graphify-out/`。本仓库 `.gitignore` 当前忽略的正是这六项。

## 7. 无消费方的产物

以下产物在技能源正文和 CLI 源码中都找不到读取其内容的位置：

- `docs/evidence/<任务 slug>/`。`mmw-implement/SKILL.md:99` 和 `mmw-review/SKILL.md:73` 只写「用户要留就挪进 `docs/evidence/<任务 slug>/`」，`mmw-closing/SKILL.md:102` 只写它不在清理范围。没有任何技能读取这个路径。唯一提到读取用途的是 `mmw/skills-src/mmw-setup/issue-tracker.md:68,82`，而 `AGENTS.md` 规定 `mmw-setup/` 只是旧背景材料，扫描技能正文时必须排除。
- `.dispatch/` 中的四栏 task 与角色报告。`mmw-closing/SKILL.md:104-106` 只按归属清理，不读内容。
- 操作系统临时目录中的 handoff 与架构候选报告。交给新会话或用户，没有技能读取。

这三项的判定范围是技能源正文加 `mmw/cli/`、`mmw/release/`、`mmw/mcp/`、`mmw/codex/` 源码。Serena 对 `mmw/cli/lib/context_docs.py` 返回「该路径被忽略」，Graphify 查询被宿主取消，因此没有取得结构候选。**这三项标记为「已查范围内无消费方」，不作为全仓库反向引用的完整结论。**

## 8. `5c1d1e73` 暴露的问题

`git show 5c1d1e73` 只改 `mmw/cli/adapters/claude-code.sh`：Codex 的 stderr 进度日志从 `.dispatch/` 改到 `<paths.scratch>/dispatch/<角色>-<task 基名>.log`，成功时删除日志并在目录空时删除 `<scratch>/dispatch/`，失败时保留并输出路径。

它修的是产物归属混淆：四栏 task 与角色报告是派发产物，Codex stderr 进度是临时过程材料。两类原先同在 `.dispatch/`，而 `mmw-closing/SKILL.md:104-106` 要求按归属逐项清理、不得整目录删除，因此无法可靠区分哪些该留。
