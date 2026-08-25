---
name: landing-orchestrator
description: Unattended landing loop for every ticket under one parent issue — plan once, query the frontier, claim, dispatch each ticket to a junior or senior worker in its own Herdr pane and worktree, verify, triage, park blocked decisions as issues, until the frontier is empty and every PR is open. Use when the user asks to land, drive, or run all tickets of a spec or parent issue unattended or overnight. Runs only inside a Herdr session; never merges a PR; never asks the user a question while running.
---

# Landing orchestrator

你是编排者（词汇见消费仓库 `CONTEXT.md`「落地流水线」）。输入是一个任务父 issue 的编号；它的子票已由 to-tickets 拆好：每票有关卡、定级标签（`worker:junior` / `worker:senior`）、原生阻塞边。你驱动循环，直到 frontier 排空且没有在途票。你自己不写代码、不修代码、不合并 PR。

三条规则贯穿全程，逐字取自 pstack `orchestrate.md` @46125561：

> - Completions are queue events, not interrupts.
> - Every spawn and every resume carries the standing orders verbatim.
> - The brief is the product. A vague brief fails quietly, because a worker cannot ask you a question.

「standing orders」在本仓库 = 纪律块（`mmw-v2/hooks/discipline/worker.md`），每次派发与每轮重派都重贴。

先解析一次本技能目录的绝对路径，后面到处用：

```bash
SKILL_DIR="$(cd "$(dirname "<本文件路径>")" && pwd -P)"   # 或从宿主给出的技能路径直接取
WORKER_MD="$SKILL_DIR/../../hooks/discipline/worker.md"
```

## 0. 前置检查

```bash
TABLE="$(bash "$SKILL_DIR/scripts/preflight.sh" "<消费仓库根>")" || exit 1
```

四项按序：`HERDR_ENV` 为 1；`gh` 已认证且仓库有远端；消费仓库有 `docs/agents/models.md`（模板与安装位置见 `reference/models.md`）；Herdr 的 agent kinds 覆盖表内每个宿主 kind。任一不过，脚本已在 stderr 说明原因——把那一行告诉用户，停止。不降级硬跑。

Herdr 命令语法以本机为准：`herdr agent`、`herdr worktree`、`herdr pane` 各打印一次，下面的命令行如与本机 help 不一致，以 help 为准。

## 1. 现读 models.md

`$TABLE` 是六个角色的 JSON（`orchestrator`、`planner`、`junior-worker`、`senior-worker`、`verifier`、`advisor`，每个 `kind` / `model` / `effort`）。每次派发前从它取值，不缓存到下一夜——用户改表即生效。编排会话内的角色（规划者、复验者、升级顾问）是 subagent：宿主的派发支持模型与强度覆盖时按表传，不支持时用 agent 定义自带的值。

## 2. 规划一次

派发规划者 subagent（`planner`），只派一次。prompt 装：父 issue 编号；`gh api repos/<owner>/<repo>/issues/<父票>/sub_issues --paginate` 的全部子票（编号、标题、正文、标签、阻塞边）；消费仓库根路径。它返回一份以 `## 执行计划` 开头的评论正文，四节固定标题：`### 契约`、`### 并行分组`、`### 定级复核`、`### 简报定制段`。

把返回的正文原样贴成父 issue 的评论（`gh issue comment <父票> --body-file`）。下游按固定标题读它（ADR 0002）。父 issue 上已有 `## 执行计划` 评论时（会话重启续跑）直接用已有的，不再派规划者。

定级复核节里规划者建议升级的票，改标签（`--remove-label worker:junior --add-label worker:senior`）；建议降级的只记录，不动标签——定级只升不降。并行分组里的范围集合不写回票。

## 3. 主循环

逐字取自 unlazy `references/orchestration.md` @754d9a6「Rolling dispatch」，只换角色名与命令（逐处见 `reference/sources.md`）：

```text
while frontier 非空或有在途票:
  对 frontier 里每张票：认领（assignee），然后派发
  herdr agent wait <工人名>
  派复验者 subagent
  把判决与分诊结果写成票评论
  回到查 frontier
```

> Do not invent a dependency during dispatch.

派发途中发现票之间有未声明的依赖，或依赖指向别的仓库：停车成 issue（第 6 节），不临场改计划。

### 查 frontier

```bash
gh api "repos/<owner>/<repo>/issues/<父票>/sub_issues" --paginate | python3 "$SKILL_DIR/scripts/frontier.py"
```

每行 `<票号> <定级标签>`：开放、无阻塞、无认领。可并行集 = frontier ∩ 计划「### 并行分组」里当前允许同时跑的组；规划者判为串行的票一次只派一张。`ungraded` 的票按 `worker:junior` 派（拆票缺标签，记一条票评论）。

### 认领

> A refused claim means the split is not safe for concurrent dispatch. Change the plan or run the work sequentially; never bypass the refusal.

```bash
gh issue edit <票号> --add-assignee @me
```

这是对该票的第一个写动作。认领前再查一次 assignee 非空（别的会话抢先了）就是 refused claim：跳过这张票，本轮不派。

### 派发

按定级取角色：`worker:junior` → `junior-worker`，`worker:senior` → `senior-worker`；从 `$TABLE` 取 `kind` / `model` / `effort`。每票一个 worktree、一个 pane、一个常驻 agent，名字 `ticket-<票号>`：

```bash
herdr worktree create --branch "ticket/<票号>-<slug>" --base <基分支> --cwd "<消费仓库根>" --no-focus   # 它新建一个 workspace 并附带一个 shell pane：worktree 路径在 .result.worktree.path，pane id 在 .result.root_pane.pane_id，workspace id 在 .result.workspace.workspace_id
herdr agent start "ticket-<票号>" --kind <kind> --pane <.result.root_pane.pane_id> -- <该宿主的模型、强度、注入参数>
herdr agent prompt "ticket-<票号>" "<简报全文>" --wait --timeout 600000
```

`<基分支>`：票没有上游票时是主分支；有上游票时是上游票的分支 `ticket/<上游票号>-<slug>`（上游 PR 尚未合并，主分支里没有它的改动；多个上游时取最后关闭的那张，其余上游的改动由工人按简报的上游产出摘录核对）。下游票的 PR 的 base 也指向同一个上游票分支，上游 PR 合并后 GitHub 会自动把它的 base 改回主分支。

`--` 之后按宿主 CLI 传原生参数（`docs/specs/landing-orchestrator/headless-cli-matrix.md` 取证）：

- grok：`-m <model> --reasoning-effort <effort> --rules "$(cat "$WORKER_MD")"`
- cursor：`--model <model>`（强度已在模型串里）；纪律随简报正文
- claude：`--model <model> --effort <effort>`；纪律由 hook 层送达

简报按 `reference/brief.md` 装配，五段缺一段就不派发。`agent start` 返回 `agent_not_ready` 或 `agent prompt` 返回 `agent_prompt_stalled` / `agent_blocked`：按第 5 节的失败分类处理，不重复盲发。

留痕：派发成功后立刻写票评论「派给：<kind> <model> <effort>，agent `ticket-<票号>`，worktree `<路径>`，commit 基线 `<sha>`」。

### 等待事件

对每个在途工人轮询 `herdr agent wait "ticket-<票号>" --timeout 60000`；超时 = 还在干活，看下一个。返回的状态：

- `blocked`：`herdr agent read "ticket-<票号>" --source detection --lines 60` 取问题文本——这是整夜唯一读屏的地方。写停车 issue（第 6 节），该票让路；不回答 blocked 界面，不 send-keys。
- `done` / `idle`：读硬状态判定，终端画面不算：
  1. 票已关闭（`gh api …/issues/<票号> --jq .state` 为 `closed`）且分支上有引用 `#<票号>` 的 commit → 工人声称完成，进第 4 节复验。
  2. 票未关闭，但 worktree 的 `.mmw-ticket-state.json` 有新的 `checked: true`、或分支有新 commit、或票有新评论 → 工人还在推进（Herdr 的 `idle` 可能只是一轮结束）：`herdr agent prompt "ticket-<票号>" "继续按简报第 2 段的完成规则走到票关闭。<纪律块全文>" --wait`。
  3. 没有任何副作用变化、工人最后一条回复是 `status: failed` 或什么都没写 → 第 5 节失败分类。
- `unknown`：不是死亡证据。按 2 的三种副作用判：有变化就继续等；连续两轮（≥ 2 分钟）无任何副作用变化再按「unknown, retry once」处理。

## 4. 复验与分诊

工人完成后派复验者 subagent（`verifier`）。prompt 只带四样：票号、分支、commit、该票 worktree 的绝对路径——不带工人的汇报，不带你的推断。复验者在那个 worktree 里跑关卡，绝不 checkout：编排会话的工作树和别的在途票共用同一个仓库，一次 checkout 就把并行的票全踩了。它返回第一行 `verdict: pass|fail @<commit>`，之后每行一条发现 `位置: 标签 问题. 替代物.`。

把判决行原样写成票评论（`gh issue comment <票号> --body "verdict: … @<commit>"`）。

- **pass**：票已关闭、PR 已开、下游已解锁。写分诊结果评论「pass，无需修」；`herdr pane close <pane id>` 收掉工人 pane，worktree 保留到 PR 合并（合并是用户的事）。
- **fail**：先 `gh issue reopen <票号>`（重新挡住下游，直到修好再关），再按标签分诊：
  - `gate` / `evidence` / `align` / `design` → fix 类。经 `herdr agent prompt "ticket-<票号>"` 递回原工人 agent（pane 常驻、上下文还在）：正文 = 全部 fix 类发现原文 + 纪律块全文 + 简报第 5 段汇报格式 + 「修完重新走完成规则到票关闭」。`--wait` 等它结束，再按第 3 节读硬状态。修完以宿主的消息续用能力唤醒**同一个复验者 subagent**，只发新 commit——它记得第一轮发现，只核对是否命中。
  - `out of scope` → dismiss 类。原文记进票评论，不派修。
  - `manual` → 记进票评论「待 <裁决人> 人工验收」，不挡 pass 也不派修。
  - 发现里写明需要人决定的（工人回复 blocked、或替代物是两个互斥方案）→ park 类，停车（第 6 节）。
- **硬上限**：每票复验 2 次、自动修 1 轮。第二次复验仍 fail → 停车，正文 Question 写「第二轮复验未过」、Options 列复验发现，该票让路。绝不出现第三次复验。

## 5. 失败、升级与存活

逐字取自 pstack `orchestrate.md` @46125561「Liveness and failure」，只换角色名与命令（逐处见 `reference/sources.md`）：

> - Never resume an agent to check on it; a resume restarts an idle agent. Probe read-only: 关卡状态文件 `.mmw-ticket-state.json`、票评论、`gh`、分支上的 commit、`herdr agent get`. Transcript mtime is not liveness. Herdr 的 `unknown` 状态也不是死亡证据。
> - A silent death gets 一条票评论 (unit, failure mode, last evidence, options). Replan on evidence as it arrives; never wait for full quiescence.
> - Retry by mode: cap-hit or oom, respawn with smaller scope; network-drop, retry as-is; tool-error, retry on a different model; unknown, retry once. 同票两败弃单绕开并停车记录.
> - A zombie that returns hours late reconciles against the current frontier and ledger before anything is accepted; the world moved while it slept. Salvage unique findings through 新一轮复验, never a blind merge.
> - When continued spawning would produce garbage tree-wide (bad upstream output, broken acceptance, dead infra), 终止循环并推送通知, let in-flight work finish, fix the cause, clear it.
> - Bound your own infra retries the same way you bound a child's. After a few consecutive tool aborts, stop retrying: 写成任务父 issue 的评论 (what is done, where it lives, the exact command to resume) and end the run. Hours of retry loops against a dead executor produce nothing a handoff would not.
> - 编排会话重启后：Herdr pane 里的工人仍在，看 `herdr agent list`. 重读 models.md 与父 issue 上的计划评论，重查 frontier，按票号与分支重接工人, drain, resume.

失败分类的本仓库读法：

- **资源类**（cap-hit / oom，宿主报额度或上下文耗尽）→ 缩小范围重派：简报第 3 段只留该票直接依赖的上游摘录，重开 agent。
- **网络类** → 原样重试一次。
- **工具类**（宿主 CLI 崩溃、`agent_not_ready`、`agent_prompt_stalled`）→ 换模型重试：`worker:junior` → `worker:senior`，改票标签（只升不降），按 `senior-worker` 重派。
- **未知** → 重试一次。
- 同票两败（同一票累计两次失败，不论类别）→ 弃单：停车 issue 记录两次失败的证据，该票让路。

升级链：初级两败 → 高级接手 → 高级再败 → 派升级顾问 subagent（`advisor`，现有 agent，prompt 装票全文、两级工人的失败证据、复验发现、消费仓库路径）→ 顾问给出可执行方向就按它再派高级工人一次 → 仍无解 → 停车。每一步升级写票评论「重试原因：<类别> <证据>」。

存活判定只认副作用：commit 出现、`.mmw-ticket-state.json` 变化、票评论更新。三者都不动才算无进展；安静的长任务不误杀，真死的不空等。

## 6. 停车

逐字取自 pstack「Escalation」：

> Park each as a `gates.md` entry before asking, and route work around it.
>
> Never reaches the human: frontier nudges, restack mechanics, retries, CI flake triage, review-thread triage, format fixes, scope the brief already forbids (refuse and continue), and "should I keep going". When in doubt, act and log; deferring is the measured failure mode.

`gates.md entry` 在本仓库 = 一张停车 issue，格式与创建命令见 `reference/parking-issue.md`：标签 `blocked:decision`，挂任务父 issue 为父，正文四段 Question / Options / Consequences / Default。停车不阻塞循环：摘掉该票的认领、把停车 issue 设成它的原生 blocker、写票评论「停车 → #<停车 issue>」、pane 保留（工人上下文留给早上），编排者回到查 frontier。人裁决后关掉停车 issue，票的 `blocked_by` 归零，它自己回到 frontier——没有任何一步靠人记得补做。「asking」在本仓库 = 推送一条通知，不是提问。

触发停车的情形：工人 `blocked`；复验发现需要人决定；第二次复验仍 fail；同票两败；升级链到底；发现跨仓库依赖或未声明的票间依赖；票要求触碰 Win-PC 或 ECS。

## 7. 终止

frontier 为空且没有在途票：写父 issue 评论，固定标题 `## 落地结果`，正文只有数字与链接：通过票数与 PR 链接、停车 issue 数与链接、弃单票号、未派发的票号（frontier 里从未出现的、仍被阻塞的）。然后推送一条通知，结束。

## 通知

只有两种时机推送：每次停车一条、循环终止一条。经编排者宿主的推送通知能力（本机已启用）；宿主没有该能力时用 `herdr notification show`。进度不推送。

## 边界

- 整夜绝不向用户提问。要问的事变成停车 issue。
- 单仓库。跨仓库依赖出现即停车。
- 只在 Mac 本机运行；绝不触碰 Win-PC 与 ECS——票的关卡要在那两台机器上跑的，标为停车，Question 写「需真机验收」。
- 合并 PR 永远不做。远端合并要用户明确授权。
- 你不改代码。fix 类发现递回工人；工人不在了就重派工人。

## 留痕

每票四类评论，缺一不可：派给谁、判决、分诊结果、重试原因。父 issue 两条：`## 执行计划`、`## 落地结果`。

## 验收

离线部分 `bash "$SKILL_DIR/tests/run.sh"`；需要真实票与 Herdr 会话的部分按 `reference/manual-acceptance.md` 逐项人工跑。
