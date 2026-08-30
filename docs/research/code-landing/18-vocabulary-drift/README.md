# mmw-v2 用词漂移审计

审的是 `mmw-v2/` 全部活内容（技能正文、脚本、agents、install.sh、merge-notes）加 `CONTEXT.md`、`AGENTS.md`、`docs/agents/`、`docs/adr/`。九个子代理各审一簇，报告在本目录 `01-`～`09-`，共 173 条原始发现，每条带 `路径:行号` 与逐字原文。定位写法 `簇-发现`，如 `5-7` = `05-code-review.md` 发现 7。

第一节是主结果：**同一个概念在 mmw 里有几个名字、几份定义，以及这种漂移让同一个操作在不同文件里变成了不同的步骤**。附一～附四是按修法归类的清单，末列「状态」标注每条的处置：绝大多数已按「英文为准、以脚本与现役用法为准」直接改掉，六条原「待拍板」项已按用户裁决落地，状态列写明各自选了哪条。

## 一、概念漂移总表

### 角色

| 概念 | 出现的叫法 | 漂移造成的后果 | 出处 |
| --- | --- | --- | --- |
| main agent | `main agent` / `orchestrator`（`models.md:4`）/ `coordinator`（`15-monitor-tab-and-wakeup-loop.md:120,133`）/ `mmw-main`（Herdr 名）/ `you`（`dispatch/SKILL.md:71`） | 读 `models.md` 的人以为表里少了一行 | 4-5, 5-17, 7-20 |
| worker | `worker` / `you`（`implement/SKILL.md` 全篇）/ `junior-worker` `senior-worker`（只在 `models.md`、`dispatch/SKILL.md:32`）/ `worker`（`exe-release/scripts/fix_dispatch.py` 里指已删的插件子进程） | grep 一个词捞到两样东西 | 7-A 表, 7-24 |
| verifier | `verifier` / `verifier 子代理`（`merge-notes/implement.md:15`）/ 「read-only subagent」（`CONTEXT.md:28`）但三宿主配置都是 `workspace-write` / `self-reported`（派不出时的降级，只在 `CONTEXT.md:269`） | 派不出 verifier 时两条路：词表说自己写 `by self-reported` 关票，`verify-ticket/SKILL.md:70-72` 说走 `HANDOFF REQUIRED` | 3-6, 3-8, 7-21, 9-9 |
| reviewer | `reviewer` = 会话（`CONTEXT.md:32`、`models.md:26`）/ `reviewer` = 三个子代理之一（`merge-notes/code-review.md:5,43`、`references/*-reviewer.md` 文件名）/ `reviewer 会话`（`merge-notes/implement.md:15`）/ `issue-<n>-review` 被写成分支名（`CONTEXT.md:396`），实际是 Herdr 名，reviewer 不建分支 | 「一个 reviewer 一份 reference」按会话理解是一份、按轴是三份；找不存在的分支 | 2-4, 5-8, 5-9, 7-11 |
| dispatcher（派发者） | `CONTEXT.md:36` = code review 内起子代理的角色；`board.py:241`、`hook.py:20`、`verify-ticket.py:753,781` = `dispatch.sh`/`board.py` | worker 读 `NOT_READY: … the dispatcher starts this ticket again` 按词表找错人 | 5-7, 7-9, 9-15 |
| user | `user` / `maintainer`（`triage/SKILL.md:48`）/ `reporter`（`triage/SKILL.md:73`、`triage-labels.md:8`）/ `human` / `driving dev`（`issue-tracker.md:41`）/ `you`（三个技能里分别指人、worker、main agent） | `needs-info` 等 reporter，本仓没有 reporter | 7-17 |
| host | `host`（`models.md:22` 表头、`agent.json`）/ `harness`（`models.md:9,16`、`references/editing-models.md` 全篇）/ `宿主`（`AGENTS.md:19`、`assemble.py:41`）/ `agent kind`（`editing-models.md:26`）/ Herdr 字段 `agent`（`board.py:271`） | 改一行 `models.md` 要认四个词；`CONTEXT.md` 无条目 | 4-16, 7-18, 8-10 |
| role | CLI 参数（`junior-worker`…，`dispatch/SKILL.md:32`）/ pane token（`worker`/`reviewer`，`dispatch.sh:236-244`）/ `models.md:22` 表头 `agent` / triage role（标签，`triage/SKILL.md:25-30`） | 两种取值集合同名 | 7-8 |

### 派发与夜间循环

| 概念 | 叫法/定义 | 后果 | 出处 |
| --- | --- | --- | --- |
| frontier | `CONTEXT.md:98`「Owns 不相交」/ `to-tickets/SKILL.md:118`「blocker 全关」/ `wayfinder/SKILL.md:68` / `grilling/SKILL.md:8`（决策集合）/ `board.py:375-380`（open + 标签 + 无 blocker + 无 assignee + 无活会话） | `board.py` 派发根本不读 `## Owns`；`17-night-loop.md:51` 说「按启动层级」派，脚本按票号 | 1-8, 4-2, 7-6, 9-2 |
| base-commit（起点 commit） | `implement/SKILL.md:34` → 去看 dispatch SKILL；`dispatch/SKILL.md:33` → 「review 的起点」；`CONTEXT.md:526` → 「diff 起点」 | 三处互指，无一处给算法；`verify-ticket.py:244` 已用 `merge-base main HEAD` 但没接过来 | 2-3, 4-18, 5-1, 9-8 |
| `mmw board: … — run board.py --once` | `CONTEXT.md:448`、`dispatch/SKILL.md:100` 都说照敲 | 无路径、无 spec；交回的票 pane 已关（`board.py:771-776`），`--once` 表里没有 | 4-1 |
| board.py 唤醒 case | `dispatch/SKILL.md:105-106` 列三个字面值 | 脚本第四个 `night over`（`board.py:823`）没登记 | 4-15, 9-18 |
| `board` | `CONTEXT.md:433` `_Avoid_: board` | `dispatch/SKILL.md:73,81,98` 通篇 the board，日志第一列 `board`（`board.py:541`） | 4-17 |
| `models.md` 第五列 | `launch command`（`CONTEXT.md:392`）/ `launch arguments`（`models.md:22`）/ `12-decisions.md:342`「不写程序名」 | 按词表填整条命令会把程序名传给 harness | 4-10 |
| `TIME LIMIT: … since dispatch` | `board.py:509` 文案 | 计时从 board 第一眼看见算（`board.py:642`），崩溃重起归零 | 4-9 |
| `WAKEUP LIMIT:` | `board.py:507` 对 idle 与对表单上限（`board.py:668-670`）同一句「went idle again」 | 早上分不清哪种 | 4-14 |
| `HOOKS-INSTALLED` | `CONTEXT.md:370`、`11-target-pipeline.html:1105` 说安装器打印 | `install.sh` 全文没有；`test_closeout.py:258` 自己 print 造标记 | 4-7, 8-13 |
| `MMW_TICKET` | `CONTEXT.md:400`「hook 找它的第一处」 | `hook.py:19-22` 唯一处；无变量无 gate；reviewer 没有它（`dispatch.sh:195-206`） | 4-12, 9-13 |
| 早上五条查询 | `CONTEXT.md:614` 五条 / `12-decisions.md:553` 裁成两条 / `17-night-loop.md:70` 数据源两个 / `board.py` 一条不跑 | 追到哪一层都落空；五条里没有一条查夜里交回的 `needs-triage` | 4-8, 9-17 |
| `dispatch.sh` 退出码 | `dispatch/SKILL.md:38-39`：1 一因、2 三因 | 脚本：1 两因（`dispatch.sh:225-229`）、2 十余因 | 4-13, 9-12 |

### 验收标准与收尾

| 概念 | 叫法/定义 | 后果 | 出处 |
| --- | --- | --- | --- |
| `ALL MET` / `HANDOFF REQUIRED:` | 收尾评论首行（`CONTEXT.md:284,288`）vs gate-check 汇总行（`gate-check.mjs:685,689`：`ALL MET (n met)` / `HANDOFF REQUIRED: n abandoned (met: …)`），后者被 `verify-ticket.py:35,713` 抄进 self-run 评论 | 照抄进草稿 `--closeout` 必拒（`HANDOFF_RE`）；`board.py:199` 只认 `UNMET:`，全过时 `ac` 列显示 `-` | 1-12, 2-8, 3-3, 3-4 |
| `UNMET: <n> (met: <m>)` | `CONTEXT.md:228`「self-run 第二行」 | 全过时第二行是 `ALL MET (…)` | 3-4 |
| `--preflight` 核几项 | 4（`implement/SKILL.md:8`、`merge-notes/implement.md:11`）/ 5（`CONTEXT.md:326`）/ 6（`verify-ticket.py:761-788`，含 `ready-for-agent` 标签、assignee） | `NOT_READY: … no ready-for-agent label` 在文档里查不到 | 1-6, 2-2, 3-2, 9-6 |
| `--closeout` 核几项 | 10（`CONTEXT.md:330`）/ 7（`verify-ticket/SKILL.md:66-70`）/ ~17（`draft_problems` + `git_problems` + `run_closeout`） | 自查数不齐 | 1-19, 2-7, 9-7 |
| `hook.py pretool` | `CONTEXT.md:378`「跑 dry run 按退出码放行」；`verify-ticket.py:820`、`test_closeout.py:402` 注释「hook 只转述 stderr 首行」 | `hook.py:14-17` 一律拒绝、不跑任何命令；两处注释的理由建在不存在的调用链上 | 2-1, 3-1 |
| `--closeout --check-only` | `verify-ticket/SKILL.md:39` | 缺 `<draft>`，照敲报用法错误 | 3-10 |
| linter 标签 | `CONTEXT.md:357` 五个（`cycle`/`dangling` 不是标签） | 实际 11 个；`unexplained-edge`（`verify-ticket.py:985`）没登记；票图错误无 ERROR 前缀 | 1-7, 2-11, 3-9, 9-22 |
| `PASS AC:` | `CONTEXT.md:232`「re-run 后打印」 | 每次都打印；同族 RUN/FAIL/STALE/UNMET 未登记 | 2-13, 3-13 |
| `STALE` / `CWD:` | `CONTEXT.md:212` 只提 `CHECK:` 签名 | 实际 CHECK/EXPECT/CWD/shell（`gate-check.mjs:605`）；`CWD:` 属性无条目 | 3-12 |
| VERDICT commit | 40 位（`CONTEXT.md:242`、`verifier/body.md:21`） | `VERDICT_RE` 收 7 位，`test_closeout.py:247` 用 15 位 | 3-7 |
| VERDICT level | `CONTEXT.md:246`「verifier 唯一要判的」五值；`:258` `type-check-only` 不许过 | 流水线无一处读 level | 3-5 |
| `Branch:/Commit:/PR:` | 三行（`CONTEXT.md:292`）/ 一行（`implement/SKILL.md:38`、`test_closeout.py:40`） | 两种形状 | 2-6 |
| `Sub-issues opened:` | 只收 `ABANDON: decision`（`CONTEXT.md:308`）/ both kinds（`implement/SKILL.md:43`）/ 实际四个来源 | 列多列少都不算错 | 7-16 |
| `Outside Owns:` | `verify-ticket/SKILL.md:75`「评论以它结尾」写在 closeout 段 | 只对 self-run 成立，草稿另有四段在后 | 2-9 |
| 写码纪律 | `ponytail 五句`（`CONTEXT.md:651`，`ponytail` 全仓一处）/ `七条`（`merge-notes/implement.md:14`）/ 七个 bullet（`implement/SKILL.md:18-24`） | 数不清哪两条不算 | 2-5 |
| `先验（probe first）` | 只在 `CONTEXT.md:671` | 无步骤承载 | 2-10 |
| 撤销 | `CONTEXT.md:194` 行内写 `撤销`；`to-tickets/SKILL.md:58` 删条不重用编号 | 脚本无 `撤销`，会被数成 unmet | 1-5 |
| `gate` | 引擎每条评论都用（`gate-check.mjs:654`） | `CONTEXT.md` 只有 criterion | 1-17 |

### 票与 spec

| 概念 | 叫法/定义 | 后果 | 出处 |
| --- | --- | --- | --- |
| `ready-for-agent` 票体 | `to-tickets` 七节 + 四行 AC / `triage/AGENT-BRIEF.md` 的 agent brief（粗体行、无 CHECK） | 同一队列两种票，worker 与 lint 读不了后一种 | 1-1 |
| `ready-for-human` 票体 | `to-tickets/SKILL.md:81-87`：`reaction`/`reach` + 五样 / `triage/SKILL.md:79`：四理由（`merge-notes/to-tickets.md:21` 已判作废）/ `triage-labels.md:20`「一行理由」/ 回读只核三样（`to-tickets/SKILL.md:138-139`）/ merge-note 说四样 | 同队列两种票，早上处理方式不同 | 1-2, 1-13, 7-1, 7-2, 7-19 |
| `## Implementation Decisions` | `CONTEXT.md:112`：落地顺序 + 我检查/你检查 / `to-spec/SKILL.md:50-60`：编号小节 + 出处 | 两种 spec 形状；`我检查/你检查` 只在词表 | 1-4 |
| `## Sources` / `## Testing Decisions` | `CONTEXT.md:124` 四类 / `to-spec/SKILL.md:80-90` 九类 + none；`to-spec/SKILL.md:68` seam 首句词表没有 | | 1-14 |
| precedent / 先例 | `to-spec/SKILL.md:71` `prior art` | 同物两名，`merge-notes/to-tickets.md:23` 只改了一侧 | 1-11 |
| `## Seam` | 票节（层/目录/先例，`CONTEXT.md:58`）vs `codebase-design/SKILL.md:22` 的 seam | Standards 轴若接 codebase-design 会读错 | 5-5, 5-13 |
| `## Blocked by` | lint 读正文（`verify-ticket.py:189`）；preflight/board 读原生边（`verify-ticket.py:777`、`board.py:162`） | 无核对 | 1-9 |
| 票模板 | issue 版 `## ` 小节 / local-files 版粗体行 + Status（`to-tickets/SKILL.md:149-159`） | lint 只吃前者 | 1-10 |
| `[fixture]` 票、`落地 <n>/15` | `CONTEXT.md:89-95` 登记为标题前缀 | 无人产生、无人读 | 1-18 |

### code review

| 概念 | 叫法/定义 | 后果 | 出处 |
| --- | --- | --- | --- |
| 轴数 | 两（`CONTEXT.md:36`、`ask-matt/SKILL.md:25`、`engineering/README.md:30`）/ 三（`code-review/SKILL.md:6`、`CONTEXT.md:497-507`） | 同一份 `CONTEXT.md` 自相矛盾 | 2-14, 5-2, 7-10, 8-3, 9-14 |
| 时机 | before committing（`ask-matt/SKILL.md:25`、`engineering/README.md:16`）/ 提交后第 3 步（`implement/SKILL.md:30`） | 提交前 review diff 为空 | 5-3 |
| `Tests` 轴范围 | 只读 CHECK 点名的（`CONTEXT.md:506`）/ diff 里其余测试仍报归票外（`tests-reviewer.md:23`） | 票外栏永远 None | 5-6 |
| `REVIEW <base-commit>..` | `CONTEXT.md:521` / `<base commit>`（`code-review/SKILL.md:60`） | | 5-18 |
| 空 diff | `code-review/SKILL.md:18`「说明并停」 | 不写票，worker 空等 1800 s | 5-11 |
| test smell baseline | 与 `tdd/tests.md`、`tdd/mocking.md` 同一批判据两份副本（`merge-notes/code-review.md:29`） | 靠人手工对齐 | 5-15 |

### 原型与 UI 验收

| 概念 | 叫法/定义 | 后果 | 出处 |
| --- | --- | --- | --- |
| 交接包 | `handoff package` / `基线目录`（`merge-notes/to-tickets.md:19`、`merge-notes/code-review.md:18`）/ `baseline directory`（`spec-reviewer.md:46`）/ `--baseline`（参数）/ `baseline` 又指 smell baseline（`standards-reviewer.md:25`）和 `## Read first` 里的契约（`CONTEXT.md:632`） | Spec reviewer 按词表会把所有基线当「不许读」 | 5-12, 6-7 |
| 「the design skill」 | `CONTEXT.md:536` | 宿主另有 `design` 技能；实指 `claude-design-blocks` | 6-8 |
| 叶子目录 | `CONTEXT.md:532` 只 UI 一支 / `prototype/SKILL.md:22` 三支 | | 6-5 |
| 场景清单 | `claude-design-blocks/SKILL.md:57`「一行一组件」/ `visual-parity.py:428-455` 要 `scenes.json`（name/page/props） | 工具报「无 scenes.json」 | 6-2 |
| 交接包内容 | 下载 README + `.dc.html`（`claude-design-blocks/SKILL.md:57`）/ `visual-parity.py:7-9` 要五件 | 基线页 404 | 6-1 |
| `?variant=<winner>` | 登记在 UI acceptance（`CONTEXT.md:556`） | 实现页收的是 `props`（`visual-parity.py:375-381`）；`prototype/UI.md:102-109` 拆脚手架在前、`claude-design-blocks/SKILL.md:46` 还要用它 | 6-4, 6-15 |
| `#dc-root` / 归一化第三条 / 负控制「first」/ `DIFF` 行 | `CONTEXT.md:552,564,568,576` | 代码不同（`visual-parity.py:128,257,352,501,512`） | 6-9, 6-10, 6-14, 6-16 |
| 基线 | `CONTEXT.md:632` 五类 / `to-tickets/SKILL.md:184` 四类 / `implement/SKILL.md:12` 三类（漏交接包） | worker 不把交接包当契约 | 6-6 |
| ui-qa | `docs/adr/0002`、`0004` 整篇规定它 | 已退役，`docs/adr/README.md` 无退役标记 | 6-11 |

### 仓库与元技能

| 概念 | 叫法/定义 | 后果 | 出处 |
| --- | --- | --- | --- |
| upstream | 两个 subtree（`AGENTS.md:22`）/ unlazy vendored 脚本（`gate-check/UPSTREAM.md:1-4`）；`CONTEXT.md:204,208` 说 gate-check「from upstream」 | 去 `mmw-v2/upstream/` 找不到 | 8-11 |
| merge-note / `UPSTREAM.md` | 两套 provenance 记录（`CONTEXT.md:236,668`） | | 8-11 |
| `CONTEXT.md` | 根词表用 `ticket`；`mmw-v2/upstream/CONTEXT.md:11-13` 把 `ticket` 列进 `_Avoid_`、`:19` 含 `ready-for-afk`；`AGENTS.md:22` 豁免名单没有它 | 两份互斥词表 | 1-15, 7-12, 7-13 |
| `CONTEXT.md` 定位 | `domain-modeling/SKILL.md:64`：纯词表一两句 / 实际 699 行含签名、常量、格式 | 改它的人两条指令相反 | 8-7 |
| `install.sh` 做几件事 | `install.sh:2`「就这两件事」/ `:15-16` 实装四样；`AGENTS.md:13` 也写两样 | | 8-12 |
| `skills.txt` 来源 | `skills.txt:4`「两种」/ `:5-7` 列三种 | | 8-15 |
| 测试层 | `CONTEXT.md:679-698` 五层 / `AGENTS.md:11-15` 无测试命令 / 「unittest」但三个是 bash / `tests/run.sh` 只两个技能有 | | 8-9 |
| 结构核对 | `CONTEXT.md:682` 两条命令 | `install.sh:210-211` `--check` 已含 `assemble.py --check` | 8-17 |
| 脚本路径 | `~/.agents/skills/…` 写死（`implement/SKILL.md:8,32`）/ 「next to this file 现算」（`verify-ticket/SKILL.md:19`、`exe-release/SKILL.md:14`）/ `$(dirname …)`（`manage-agents-md/verify.md:10`） | | 8-18 |
| 写 AGENTS.md 的规则 | `manage-agents-md/prune.md:41-48`、`write.md:151-153` 与 `writing-for-agents/SKILL.md:16-18,74-81` 逐字重复互不引用；`setup-matt-pocock-skills/SKILL.md:76` 与 `manage-agents-md/write.md:13` 对 `CLAUDE.md` 指令相反 | | 8-1, 8-6 |
| `disable-model-invocation` | 九份 merge-note「全部删」/ 四个已装技能仍在 / 两份上游 README 的 User-invoked 清单全错 | | 8-4 |
| ask-matt | `ask-matt/SKILL.md:3`「本仓技能 router」 | 七个自研技能一个不提 | 8-5 |
| reference | `CONTEXT.md:632`（非契约材料）/ `references/` 目录 / `## External References` 表 / `writing-for-agents/SKILL.md:31` 内容类型 | | 8-21 |
| 五标签 | `CONTEXT.md:585-610`、`triage-labels.md`、`AGENTS.md:32` 各定义一遍；`/triage`「四个 outcome」无处列、`triage/SKILL.md:77-85` 五条 | | 7-3, 8-16 |
| ADR 改写关系 | `Status: superseded by`（`ADR-FORMAT.md:21`）/ `amends:` / 索引两列 / `ADR-0007`（`domain.md:51`） | | 8-8 |

### 幽灵词（`_Avoid_` 里的词仍在活文件）

`orchestrator`（`models.md:4`）、`coordinator`、`verifier 子代理`、`reviewer 会话`、`基线目录`、`顶格续行`（`merge-notes/to-tickets.md:15`）、「没到终点就停了 / 半路停了 / 半途停下」（`15-monitor…:92,126`、`14-herdr…:106`、`11-target-pipeline.html:1301`）、`ready-for-afk`、`AFK-ready`；反向：`gate-check.mjs` / `gate-lint.mjs` 被 `_Avoid_` 但它们是文件名。出处 G1–G11。

## 附一、断点清单（改文件即可）

| # | 一句话 | 以谁为准 | 出处  状态 |
| --- | --- | --- | --- | --- |
| B1 | 票从未被挂成 spec 的原生 sub-issue；`verify-ticket.py --lint` 与 `board.py --watch` 只认 sub-issue，白天 lint 静默 return 0，夜里一张票不派 | 两个脚本；`to-tickets` 第 7 步加 `--parent`，第 8 步加核对 | 1-3, 9-1 | 已改 |
| B2 | 收尾第 3 步的 `<base-commit>` 三处互指、无人给算法 | `git merge-base main HEAD`（`verify-ticket.py:244` 已用） | 2-3, 4-18, 5-1, 9-8 | 已改 |
| B3 | `hook.py pretool`：词表与两处注释说「跑 dry run 按退出码放行」，脚本一律拒绝、不跑任何命令 | `hook.py:14-17` | 2-1, 3-1 | 已改 |
| B4 | `mmw board: … — run board.py --once` 这句主 agent 照敲跑不出结果：无路径、无 spec，交回的票 pane 已关不在表里 | 改 `MAIN_LINE` 带路径与 spec | 4-1 | 已改 |
| B5 | 夜里交回的票全落 `needs-triage`，但 `/triage` 全篇按外来 issue + reporter 写，没有承接支路；「早上五条查询」也没有一条以它为目标 | 按 `12-decisions.md:553` 改成两条查询；`triage` 加支路 | 4-8, 7-4, 9-17 | 已改 |
| B6 | 交回 `needs-triage` 时不摘 assignee；`board.py` frontier 要求无 assignee，这票再也派不出去 | 两处 `hand_back` 加 `--remove-assignee` | 7-22 | 已改 |
| B7 | `self-reported` 只在词表存在；`verify-ticket/SKILL.md:70-72` 说派不出 verifier 唯一出路是 `HANDOFF REQUIRED` | 删词条 | 3-6, 9-9 | 已改 |
| B8 | `--closeout --check-only` 按 SKILL.md 写法直接报用法错误（缺 `<draft>`） | 脚本 | 3-10 | 已改 |
| B9 | `to-tickets:134` 的 `verify-ticket.py <n> --lint` 无路径，本地文件形态跑不起来 | 写成 `implement:8` 的全路径形式 | 1-10, 9-3 | 已改 |
| B10 | `to-tickets` 结束后无人把主 agent 交到 `dispatch.sh run` | `to-tickets` 末尾加一句 | 9-4 | 已改 |
| B11 | `visual-parity.py --baseline` 要五件东西（`.dc.html`/`styles/`/`data/`/`support.js`/`scenes.json`），`claude-design-blocks` 第 7 步只下载 README + `.dc.html`，场景清单写成文本行而非 `scenes.json` | 脚本 | 6-1, 6-2 | 已改 |
| B12 | `prototype/UI.md` 让赢家选出后拆 `?variant=`，`claude-design-blocks` 之后还要靠它开页取 CSS | `CONTEXT.md:632` 的先后：先移植再拆 | 6-4 | 已改 |
| B13 | reviewer diff 为空/base 解析失败时不写票，worker 空等 1800 s | 失败也评论 `REVIEW …` 首行 | 5-11 | 已改 |
| B14 | `triage` 要求每条评论首行是 AI 免责声明，而整条流水线以评论首行为协议位 | 声明移到末行 | 9-21 | 已改 |
| B15 | `exe-release:95` 失败交给 `/implement`，而 `implement` 第一步要票号 | 先开 `needs-triage` 票再 `implement #<n>` | 8-19 | 已改 |
| B16 | `code-review` 要三个子代理的绝对路径，表里只有相对链接 | 写 `~/.agents/skills/code-review/references/…` | 9-16 | 已改 |
| B17 | `--lint` 的「no sub-issues」return 0 静默放行 | 改 ERROR | 9-1 | 已改 |

## 附二、分岔清单（已选定以谁为准）

| # | 一句话 | 以谁为准 | 出处  状态 |
| --- | --- | --- | --- | --- |
| F1 | `--preflight` 核几项：4 / 4 / 5 / 脚本 6（含 `ready-for-agent` 标签、assignee） | `verify-ticket.py:761-788` 六项 | 1-6, 2-2, 3-2, 9-6 | 已改 |
| F2 | `--closeout` 核几项：10 / 7 / 脚本约 17 | 去掉数字，清单只留 `verify-ticket/SKILL.md` | 1-19, 2-7, 9-7 | 已改 |
| F3 | code review 两轴还是三轴（`CONTEXT.md:36`、`ask-matt:25`、`engineering/README.md:30` 说两） | 三轴 | 2-14, 5-2, 7-10, 8-3, 9-14 | 已改 |
| F4 | review 在提交前还是提交后（`ask-matt`/README 说 before committing） | `implement:30` 提交后 | 5-3 | 已改 |
| F5 | `ALL MET` / `HANDOFF REQUIRED:` 各有两种格式：gate-check 汇总行 vs 收尾评论首行，同前缀不兼容；`UNMET:` 不是全过时的第二行，`board.py` 的 `ac` 列因此显示 `-` | 词表另立「gate-check 汇总行」；`board.py:199` 正则补 `ALL MET (n met)` | 1-12, 2-8, 3-3, 3-4 | 已改 |
| F6 | linter 标签：词表 5 个（2 个不是标签），实际 11 个 | 按 `gate-lint.mjs` + `verify-ticket.py` 补全；cycle/dangling 打印加 ERROR 前缀 | 1-7, 2-11, 3-9, 9-22 | 已改 |
| F7 | `## Implementation Decisions`：词表「落地顺序 + 我检查/你检查」vs `to-spec` 模板「编号小节 + 出处」 | `to-spec` 模板 | 1-4 | 已改 |
| F8 | `## Sources` 四类 vs 九类 + none；`## Testing Decisions` 丢 seam 首句 | `to-spec` 模板 | 1-14 | 已改 |
| F9 | `prior art`（to-spec）vs `precedent`/先例（to-tickets、词表） | `precedent` | 1-11 | 已改 |
| F10 | `ready-for-human` 核 4 样 / 5 样 / 回读只核 3 样 | 5 样 | 1-13, 7-2 | 已改 |
| F11 | `Tests` 轴范围：词表「只读 CHECK 点名的」vs reference「diff 里其余测试仍报、归票外」 | `tests-reviewer.md:23` | 5-6 | 已改 |
| F12 | `REVIEW <base-commit>..` vs `<base commit>` | `SKILL.md:60` | 5-18 | 已改 |
| F13 | `Sub-issues opened:` 收 1 类 / 2 类 / 实际 4 类来源 | 四类 | 7-16 | 已改 |
| F14 | `implement:12` 基线三类漏交接包；词表五类 | 五类 | 6-6 | 已改 |
| F15 | `dispatch.sh` 退出 1 有两因、退出 2 有十余因，SKILL.md 各写一/三条 | 「原因在 stderr，逐字读」 | 4-13, 9-12 | 已改 |
| F16 | `run --role` 校验松：subagent 行能过开跑校验，夜里每轮 exit 2 空转 | 加「启动参数不能是 `—`」 | 4-13 | 已改 |
| F17 | `dispatch/SKILL.md` 唤醒表漏第四个 case `night over` | 补 | 4-15, 9-18 | 已改 |
| F18 | `WAKEUP LIMIT:` 对表单上限也说「went idle again」 | 表单用自己的句子 | 4-14 | 已改 |
| F19 | `MMW_TICKET`「hook 找它的第一处」；实际唯一处，无变量无 gate；且 reviewer 没有它 | `hook.py:19-22` | 4-12, 9-13 | 已改 |
| F20 | `issue-<n>-review` 被写成分支名；reviewer 不建分支，在 worker worktree 里跑 | 改「Herdr 名」 | 2-4, 4-12, 5-9 | 已改 |
| F21 | `models.md` 第五列：词表叫 launch command，表头 launch arguments，裁决不许写程序名 | launch arguments | 4-10 | 已改 |
| F22 | `junior-worker` 行 effort 列是死数据（启动参数无 `{effort}`） | 写 `—` | 4-11 | 已改 |
| F23 | `VERDICT` commit 要 40 位，正则收 7 位，测试用 15 位 | 40 位 | 3-7 | 已改 |
| F24 | verifier 被称 read-only subagent，三宿主配置都是 workspace-write | 用 `body.md:35` 措辞 | 3-8 | 已改 |
| F25 | `STALE` 只提 `CHECK:`，实际 CHECK/EXPECT/CWD/shell 四者；`CWD:` 属性未登记 | 补 | 3-12 | 已改 |
| F26 | `PASS AC:` 说 re-run 后打印，实际每次；同族 RUN/FAIL/STALE/UNMET 未登记 | 补 | 2-13, 3-13 | 已改 |
| F27 | 归一化第三条：文档「lift nested main」，代码丢内层 main 上提子节点 | 代码 | 6-9 | 已改 |
| F28 | `#dc-root` 只是基线侧锚点，实现侧截视口读 body | 代码 | 6-10 | 已改 |
| F29 | 负控制「first」：实际第一视口跑完全部场景后造一次 | 代码 | 6-14 | 已改 |
| F30 | `DIFF` 行多一截 `— <reasons>`，非 aria 失败下面无 ARIA 行 | 代码 | 6-16 | 已改 |
| F31 | `?variant=<winner>` 登记在 UI acceptance，实际实现页收的是 `scenes.json` 的 `props` | 挪回原型段 | 6-15 | 已改 |
| F32 | `mkallharness.py` 要不要传参，同一 SKILL.md 前后相反 | 不传 | 6-13 | 已改 |
| F33 | `Outside Owns:`「评论以它结尾」写在 closeout 段，只对 self-run 成立 | 改主语 | 2-9 | 已改 |
| F34 | `test_closeout.py:21,26` 的 EVIDENCE 样本不是引擎产出的形状 | 换成 `:262` 形状 | 2-12 | 已改 |
| F35 | `test_board.py:67-69` 的 `UNMET: 0 (met: 5)` 是 gate-check 不会打印的假评论 | 换真输出 | 3-4 | 已改 |
| F36 | 拒绝理由「stderr 一行」，实际 1 + N 行 `also:` | 改 | 3-11 | 已改 |
| F37 | `UPSTREAM.md` 说 701 行，实际 700 | 改 | 3-16 | 已改 |
| F38 | `The environment is yours; the repository is not.` 源文件无句号、是标题 | 改 | 3-15 | 已改 |
| F39 | `merge-notes/code-review.md:37` 说上游只一个文件，八行后又列 `agents/openai.yaml` | 改两个文件 | 5-14 | 已改 |
| F40 | `merge-notes/to-spec.md:12` 不打标签的理由已不成立（守卫第四项就查标签） | 重写理由 | 2-2, 9-5 | 已改 |
| F41 | `install.sh:2` 自称两件事实装四样；`AGENTS.md:13` 也只写两样 | 四件 | 8-12 | 已改 |
| F42 | 安装器「五个宿主」「齐了 N 处」两计数写死/只数技能 | 改 | 8-14 | 已改 |
| F43 | `skills.txt:4`「两种来源」实列三种 | 三种 | 8-15 | 已改 |
| F44 | `结构核对` 两条命令，`install.sh --check` 已内含 `assemble.py --check` | 注明 | 8-17 | 已改 |
| F45 | 技能脚本路径两种写法：`~/.agents/skills/…` 写死 vs 「next to this file 现算」 | next to this file | 8-18 | 无需改：跨技能引用用 `~/.agents/skills/…`、本技能内用 next to this file，现状即约定 |
| F46 | ADR 0006 两条 Consequences 数字过期（30 条→32；两处分支→另有两组表） | 顶部加引言 | 8-20 | 已改 |
| F47 | `docs/adr/README.md:3` 写死「ADR 0005」，已到 0006 | 删括号 | 8-8 | 已改 |
| F48 | `17-night-loop.md` §11 说步 3 待返工、4/5 未做；全已落地 | 删状态列 | 4-3, 9-19 | 已改 |
| F49 | `17-night-loop.md:17` reviewer 行漏 `<base-commit>`；等待正则 `^REVIEW` / `^REVIEW ` 两种 | 补；统一 | 4-18, 9-10 | 已改 |
| F50 | `12-decisions.md:636` J11 自相矛盾 | 改括号 | 4-19 | 已改 |
| F51 | `08-failure-vocabulary.md` §7.1 收尾格式与 `implement:36-45` + 正则不兼容 | 标明已被取代 | 9-11 | 已改 |
| F52 | sub_issues 端点三种占位符写法 | `{owner}/{repo}` | 9-23 | 已改 |
| F53 | `merge-notes/README.md:3` 范围首句与清单不符 | 改 | 8-23 | 已改 |
| F54 | `setup-matt-pocock-skills` 与 `manage-agents-md` 对根 `CLAUDE.md` 能否写 `@import` 以外内容指令相反；本仓已选一边无 merge-note | `manage-agents-md` | 8-1 | 已改 |
| F55 | 九份 merge-note 说「全部技能模型可触发」，四个已装技能仍 `disable-model-invocation: true`，两份上游 README 的 User-invoked 清单全错 | 收窄措辞或补 merge-note | 8-4 | 已改 |

## 附三、需要拍板的分岔

| # | 问题 | 选项 | 出处  状态 |
| --- | --- | --- | --- | --- |
| D1 | `dispatcher（派发者）`：词表划给 code review 内角色，三份脚本注释用它指 `dispatch.sh`/`board.py` | (a) 脚本改 `dispatch.sh`；(b) code review 角色改名 `review dispatcher` | 5-7, 7-9, 9-15 | 已改 |
| D2 | `reviewer`：会话 vs 三个子代理；三个子代理叫什么、进不进 `models.md` | 子代理叫 `Standards`/`Spec`/`Tests` sub-agent；进表或在 `models.md:3` 写例外 | 5-8, 5-10, 7-11 | 已改 |
| D3 | `frontier` 五份定义（词表 Owns 不相交、to-tickets、wayfinder、grilling、`board.py` 五条件） | 以 `board.py:375-380` 为定义，Owns 不相交另立为出票判据 | 1-8, 4-2, 7-6, 9-2 | 已改 |
| D4 | `/triage` 出的 `ready-for-agent` 票是 agent brief，不是七节票；进队列后 worker 读不到 Read first/Seam/Owns，lint 出空账本 | (a) triage 出口改走 to-tickets；(b) AGENT-BRIEF 模板改七节 | 1-1 | 已改（选 a）：`/triage` 的 `ready-for-agent` 出口改走 `/to-spec`→`/to-tickets`，agent brief 降为调查记录 |
| D5 | `ready-for-human` 内容：to-tickets 的 `reaction`/`reach` 五样 vs triage 的四理由（merge-note 已判四理由作废） | 五样 | 1-2, 7-1, 7-19 | 已改 |
| D6 | `## Blocked by` 正文与 GitHub 原生边无核对：lint 读正文，preflight/board 读原生 | (a) lint 加集合比对；(b) 票图改读原生 | 1-9 | 已改（选 b）：票图读 tracker 原生阻塞边，`## Blocked by` 为人读副本，不一致报 `[blocked-by-mismatch]` WARN |
| D7 | `to-tickets` 两份票模板（issue 七节 vs local-files 粗体行），lint 只吃前者 | (a) 统一 `## ` 小节；(b) local 分支明写不跑 lint | 1-10 | 已改：`/to-tickets` 删掉 local-files 发布形态与 `<local-ticket-template>`，只发真 tracker |
| D8 | `CONTEXT.md` 定位：`domain-modeling` 说纯词表一两句，本文件 699 行含命令签名、常量表、输出格式 | (a) merge-note 声明两用；(b) 把契约挪到脚本旁 | 8-7 | 已改 |
| D9 | `mmw-v2/upstream/CONTEXT.md` 把 `ticket` 列进 `_Avoid_`、含 `ready-for-afk`；`AGENTS.md:22` 豁免名单没有它 | 加进豁免名单 | 1-15, 7-12, 7-13 | 已改 |
| D10 | ADR 0002/0004 整篇规定已退役的 ui-qa；`docs/adr/README.md` 无退役标记 | (a) 写取代 ADR；(b) 删 | 6-11 | 已改 |
| D11 | `verify-ticket/SKILL.md` 对同目录 `visual-parity.py` 一字不提 | (a) 加 UI 验收段；(b) 明说只由 to-tickets 写进 CHECK | 6-3 | 已改 |
| D12 | `HOOKS-INSTALLED` 谁也不打印；测试自己 `print` 造假标记 | (a) `install.sh --check` 真打印；(b) 删词条 | 4-7, 8-13 | 已改 |
| D13 | VERDICT `level` 五值无人读；`type-check-only` 那句禁令无门执行；`implement:33` 禁二派 verifier | (a) level 只给人读；(b) closeout 读 level + 安排重跑 | 3-5 | 已改：`VERDICT` 行删 level（`VERDICT <commit> by <model> — <one line>`）；`--closeout` 在 `ALL MET` 时核最新 run 评论的汇总行 |
| D14 | `board.py` 输出：英文列头/动作词 vs `17-night-loop.md` 中文样例 | 二选一 | 4-4, 9-20 | 已改 |
| D15 | `board` 在 `_Avoid_`，`SKILL.md` 通篇 the board，日志第一列 `board` | (a) 删 `_Avoid_`；(b) 全改 `board.py` | 4-17 | 已改 |
| D16 | `TIME LIMIT: … since dispatch`，实际从 board 第一眼算、崩溃重起归零 | (a) 改措辞；(b) 从票上读认领时间 | 4-9 | 已改 |
| D17 | `Branch:/Commit:/PR:` 一行还是三行；「无 PR 写理由」只在词表 | 二选一 | 2-6 | 已改 |
| D18 | 「ponytail 五句」vs 「写码纪律七条」vs 正文七 bullet；`ponytail` 全仓一处 | (a) 改名七条；(b) 五句 + 两条单立 | 2-5 | 已改 |
| D19 | `先验（probe first）` 只在词表，无任何步骤承载 | 写进 implement 或删 | 2-10 | 已改 |
| D20 | `[fixture]` 票、`落地 <n>/15` 前缀：登记了，无人产生或读取 | 写进 to-tickets 或删 | 1-18 | 已改：`[fixture]` 与 `落地 <n>/15` 两词条删除，技能行为层措辞脱钩 |
| D21 | 前提消失的 AC：词表「行内写 `撤销`」vs to-tickets「删条不重用编号」；脚本无 `撤销` | 删条 | 1-5 | 已改 |
| D22 | `code-review` description 招揽无票用法，正文必须要票号 | (a) 收窄 description；(b) 加无票落点 | 5-4 | 已改 |
| D23 | `## Seam`（票节：层/目录/先例）与 codebase-design 的 seam（Feathers）双定义；Standards 轴未接 codebase-design | 词表接起两义；Standards 来源加 codebase-design | 5-5, 5-13 | 已改 |
| D24 | test smell baseline 与 `tdd/tests.md`/`mocking.md` 是同一批判据的副本，靠人手工对齐 | (a) 接受副本、两文件互指；(b) tdd 指向 reference | 5-15 | 已改 |
| D25 | 本仓 `AGENTS.md` 过不了 `manage-agents-md/scripts/check.sh`（缺 subdirectory 句） | (a) 补句；(b) 声明不受管辖 | 8-2 | 已改 |
| D26 | `manage-agents-md` 的 `prune.md`/`write.md` 与 `writing-for-agents` 三段逐字重复、互不引用 | 删重复改 pointer | 8-6 | 已改 |
| D27 | `ask-matt` 自称本仓技能 router，七个自研技能一个不提 | 补进或改 description | 8-5 | 已改 |
| D28 | `docs/agents/` 三份与 setup 种子近逐字重复，本仓加的 `## What carries a label here` 重跑 setup 即丢；无 merge-note | 写 merge-note | 7-15 | 已改 |
| D29 | `bug`/`enhancement` category role 映射表无行；`triage:40` 要求每票带一个 | 以 `triage-labels.md:24` 例外为准写回 | 7-5 | 已改 |
| D30 | `role` 四义：CLI 参数（junior-worker…）、pane token（worker/reviewer）、models.md 表头 `agent`、triage role | pane token 改 `kind`；表头与参数二选一 | 7-8 | 已改：pane token 改名 `kind`（`dispatch.sh`、`board.py`、`verify-ticket.py` 与测试、文档同步） |
| D31 | `reference` 四义（非契约材料 / references/ 目录 / External References 表 / 内容类型） | `CONTEXT.md:631` 换词 | 8-21 | 已改 |
| D32 | ADR 0001「原 issue 关闭挂到 spec 下」无技能执行 | 写进 to-spec 或注明手工 | 7-23 | 已改 |
| D33 | `create-design-md` 被 `claude-design-blocks` 要求，`install.sh` 不装 | 写全来源或收进 skills.txt | 6-12 | 已改 |
| D34 | `reviewer 会话` 在 `_Avoid_`，但词表定义本身就是「the session」 | 删 `_Avoid_` 或改两处 | 5-16 | 已改 |
| D35 | `gate-check.mjs`/`gate-lint.mjs` 被 `_Avoid_`，可它们是文件名 | 改 `_Avoid_` 措辞 | 1-20 | 已改 |

## 附四、幽灵词与撞车清单

| # | 词 | 事实 | 出处  状态 |
| --- | --- | --- | --- | --- |
| G1 | `orchestrator`（`models.md:4`）、`coordinator`（`15-monitor…:120,133`） | `_Avoid_`；改 `main agent` | 2-14, 3-14, 4-5, 5-17, 7-20, 8-22 | 已改 |
| G2 | `verifier 子代理`、`reviewer 会话`（`merge-notes/implement.md:15`；`implement:34` reviewer session） | `_Avoid_` | 3-14, 5-16, 7-21 | 已改 |
| G3 | `基线目录` / baseline directory（`merge-notes/to-tickets.md:19`、`code-review.md:18`、`spec-reviewer.md:46`）；`baseline` 在同簇三义 | 改「交接包 / handoff package」 | 5-12, 6-7, 8-22 | 已改 |
| G4 | 「the design skill」（`CONTEXT.md:536`）指 `claude-design-blocks`，宿主另有 `design` 技能 | 改技能名 | 6-8 | 已改 |
| G5 | 叶子目录只写 UI 一支，原型技能三支都是 | `prototypes/<task>/<issue>/<UI\|LOGIC\|EXP>/` | 6-5 | 已改 |
| G6 | `host` / harness / 宿主 / agent kind 四名一物，词表无条目 | 立 `host（宿主）`，`_Avoid_: harness` | 4-16, 7-18, 8-10 | 已改 |
| G7 | `upstream` 既指两个 subtree 又指 unlazy vendored；`CONTEXT.md:204,208` 说 gate-check「from upstream」 | 改「from unlazy」；`AGENTS.md:22` 补一句 | 8-11 | 已改 |
| G8 | `gate` 出现在每条评论里，词表无条目 | 登记为引擎对 criterion 的叫法 | 1-17 | 已改 |
| G9 | `ready-for-afk` / `AFK-ready`（`upstream/CONTEXT.md:19`、`triage-labels.md:13`） | 改 `ready-for-agent` 或删例子 | 1-16, 7-13, 7-14 | 已改 |
| G10 | `顶格续行`（`merge-notes/to-tickets.md:15`） | `_Avoid_` | 1-20 | 已改 |
| G11 | 「没到终点就停了」「半路停了」「半途停下」（`15-monitor…:92,126`、`14-herdr…:106`、`11-target-pipeline.html:1301`） | `_Avoid_`；改判据本身 | 4-6 | 已改 |
| G12 | 同一个人六个名字：user / maintainer / reporter / human / you / driving dev | `docs/agents/*` 统一 `user` | 7-17 | 已改 |
| G13 | HITL/AFK、reaction/reach、四理由：「能不能让 agent 单干」四套词 | reaction/reach 为准，HITL/AFK 限定 decision ticket | 7-19 | 部分改：triage 侧已统一 reaction/reach；wayfinder 的 HITL/AFK 未注（低优先） |
| G14 | `worker` 在 `exe-release/scripts/fix_dispatch.py` 指插件子进程；「驱动 agent」未登记 | 改 `worker.sh` 字面名 | 7-24 | 已改 |
| G15 | 五标签在 `CONTEXT.md`、`triage-labels.md`、`AGENTS.md` 各定义一遍 | `triage-labels.md` 为准，词表改指路 | 8-16 | 已改 |
| G16 | `/triage`「四个 outcome」无处列出，技能正文列五条 | 在 triage 标题下明列四个 | 1-附, 7-3 | 已改 |
| G17 | 宿主名写进词表（`CONTEXT.md:20,24,32` cursor/grok/Claude Code），`AGENTS.md:21` 说只改 `models.md` | 词表删宿主名 | 7-7 | 已改 |
| G18 | ADR 改写关系三种写法（`Status: superseded by` / `amends:` / 索引两列 / `ADR-0007`） | `amends:` + 索引 | 8-8 | 已改 |
| G19 | 五个测试层只在词表，`AGENTS.md` 命令表无测试命令；「自写脚本层 = unittest」与 bash 测试不符；`tests/run.sh` 只两个技能有 | 命令表补入口 | 8-9 | 已改 |
| G20 | `17-night-loop.md:75` 引 wayfinder 的 frontier 当夜间定义；`:51` 说按启动层级派发，`board.py` 按票号 | 改指 `board.py` | 4-2 | 已改 |

## 附五、簇报告

- `01-ticket-ac.md` — 票与 spec 结构、AC 写法与 lint（20 条）
- `02-worker-path.md` — worker 从领票到收尾（14 条）
- `03-verify-verdict.md` — 跑 AC、复验、VERDICT（16 条）
- `04-dispatch-night.md` — 派发、等待、夜间循环、Herdr（19 条）
- `05-code-review.md` — code review（18 条）
- `06-ui-prototype.md` — 原型、UI 交接与验收（16 条）
- `07-roles-labels.md` — 角色名与标签状态机（24 条）
- `08-infra-meta.md` — 工具箱基建与元技能（23 条）
- `09-walkthrough.md` — 四条执行路径逐步走查（23 条）
