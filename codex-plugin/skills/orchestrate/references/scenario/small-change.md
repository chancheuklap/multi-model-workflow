# Small-change · 需独立任务边界的小改

> orchestrate 路由到这:**范围明确,但仍需独立任务边界与验收;根因清楚、不需要设计**。这条路从头到尾就读这一份,不用回 SKILL。
> **预设 `small-change`**,阶段序列:落地(含 ④终审闸)→ 收尾(build→closing)。无 investigate / design / plan,但**落地产物过后照样进 ④终审闸**(引擎强制,跟 develop 一致)。
> **动手前轻确认(唯一一次)**:写第一行代码前,把「打算怎么改 + 影响面」一句话给用户,**等他回一句再动**(值守档 afk 也要这一停——这是本路仅有的人闸)。
> **落地 = 主线程就地 TDD**(不派 pack-executor):build 阶段按 `mmw where` 报的 `scenario=small-change` 就地 TDD,build 自按 scenario 选落地模式。
> 改动小但仍走 ④终审闸,不跳质量门;落地撞出超范围问题 → `mmw spinoff` 登记,别就地扩。

<!-- BEGIN: worktree-setup -->
## 采用 Codex App 当前 worktree

1. 从对话主题起一个切题的 slug，格式 `YYYY-MM-DD-<theme>`。任务 branch 固定为
   `codex/<slug>`，让 Codex App 的 sidebar、terminal、diff 和 branch 始终指向同一份
   checkout。

2. 在当前 checkout 运行：

   ```bash
   mmw task new --scenario small-change --slug <slug> --title "<人类可读标题>" --request "<用户原始需求与验收条件>"
   ```

   仅 develop：用户已经给出明确方向时加 `--direction-given`；整件事仍在雾里时加
   `--with-wayfind`。

3. 按回执继续：

   - `NEEDS_APP_WORKTREE`：当前是 local checkout。请用户在 Codex App 为这个仓库创建
     Worktree task，然后在那个 task 重跑同一条命令。plugin 不在后台创建另一个
     outer worktree。
   - `NEEDS_APP_BRANCH`：当前 App task 还是 detached 或 branch 名不对。请用户在
     App 当前 task 选择 **Create branch here**，创建回执给出的
     `codex/<slug>`，然后重跑同一条命令。
   - `PREPARED`：当前 App worktree/branch 已原地采用。保持当前 task 和 cwd，运行
     `mmw where` 进入第一阶段。

CLI 或 IDE 入口也只接受已经进入的 linked worktree 和 `codex/<slug>` branch；
plugin 不替宿主创建 outer。任务文档提交进当前 App branch；过程审查产物由
`docs/.gitignore` 忽略；临时状态固定落 `.codex/multi-model-workflow/`。
<!-- END: worktree-setup -->

<!-- BEGIN: phase-contract -->
## 阶段运行契约(进 worktree 后的主循环)

进 worktree 后,每个阶段都是同样 4 个动作;阶段之间唯一变的是「干」用哪套方法论。**这是个循环**:交完拿到回执 → 按回执跳到目标阶段 → 回 ① 进 → …… 直到回执说收尾。

| 动作 | 做什么 | 命令 / 机制 |
|---|---|---|
| **① 进** | `mmw where` 报:在哪阶段、在不在审闸、上阶段钉了什么(`prev_outputs` 照单读,不自己找)、`load`(读哪份)/ `do`(干什么)/ `then`(交什么)。照 `load` 加载 | `mmw where` |
| **② 干** | 按 `where` 的 `do` 跑该阶段方法论,读 `prev_outputs` 当输入 | `load` 指向的 reference |
| **③ 钉** | 把本阶段承重产出钉进接力单,下阶段照单读 | handoff 的 `--produced`(漏钉/产物后到 → `mmw pin` 补) |
| **④ 交** | 给一个结论词,引擎算下一步、写进度、回执;照「回执 → 怎么跳」表行动 | `mmw handoff` |

**③ 钉 + ④ 交 —— 一条 handoff:**

```bash
mmw handoff --conclusion <结论词> [--produced <本阶段产出路径>]...
```

- **结论词**五选一(`pass` / `needs-repair` / `needs-redirection` / `needs-context` / `blocked`),选哪个是你的判断——引擎照单执行,不否决;`where` 的 `then` 已给好带承重产出的命令模板。`needs-context` 必须另带 `--waiting-for '<必须由用户补充的具体问题>'`(落盘进任务档案,下次会话冷启动靠它接上;用户答完 `mmw task resume` 续跑)。
- 回执里的 `WARN=` 行是引擎摆到明面的缺口(没钉产出/路径不存在/返工轮多了),读了要处理:补钉用 `mmw pin --produced <路径> [--phase <阶段>]`,不要无视。
- **讨论态(investigate/propose/design)来回是常态**:掉头不计成本、不留案底,想回哪就 `needs-redirection`(默认回上一阶段,`--to-phase` 指定更远上游)。**流水线态(to-issue 之后)** 回上游同样走得通,但从第 2 次起先向用户讲清楚为什么又回头。
- **design 阶段不走 handoff pass 离开**:设计定稿 + 预审结果给用户后,由用户敲 `/approve-design` 过门(唯一人闸;引擎盖承重指纹、切 afk、推进)。
- 中途挖到 bug / 旁路优化 → `mmw spinoff --tag <bug|optimize|out-of-scope|needs-evaluation> --finding "<一句话>"`,登记成关联子任务,主流程不动。
- 阶段性进展/待拍板变化随手 `mmw note set --text "<一句话>"`——下次开场的三源回报靠它 + 提交流水 + 设计文档 Open Decisions,不靠会话记忆。

**断点续传**:任何时候 `mmw where` + 接力单 + 开场三源回报就够你接着跑——进度、产出、现场全在盘上。跨天、compaction 或新 Codex task 仍从同一份磁盘状态续跑。
<!-- END: phase-contract -->

<!-- BEGIN: receipt-jump -->
## 回执 → 怎么跳(阶段间流转的全部规则)

`mmw handoff` 回执三行 `NEXT_ACTION` / `NEXT_PHASE` / `STATUS`(可能带 `WARN=` 缺口行),照这张表行动:

| `NEXT_ACTION` | `STATUS` | 你下一步 |
|---|---|---|
| `advance` | active | 往下跳:回 ① 进,对 `NEXT_PHASE` 跑 `mmw where`。**正常前进就是这条。** |
| `review` | active | 别 advance(phase 没动)。进审闸:`where` 的 `load` 自动切到 `review/review.md`,照 `review_start` 起审;审完再 `handoff` 一次 verdict——`pass` 才真 advance(引擎核审查留痕落盘含 verdict,没有留痕不放行),`needs-repair` 回本阶段返工。 |
| `repair` | active | 留在本阶段返工:回 ② 干按缺陷改,改完再 `handoff`。第 3 轮起回执会提醒:每轮向用户汇报卡点再继续。审闸返工:指纹重合(同缺陷反复)或 repair_count 超 max_repair_rounds(默认 3)→ 打转守卫 GUARD(afk/attended 交人,unattended 硬停);非审闸只 WARN 不硬顶。 |
| `turn-around` | active | 掉头回上游:对 `NEXT_PHASE` 回 ① 进重跑(默认回上一阶段;下游已过期的接力单产出引擎已剪,盘上文件还在)。第 2 次起先向用户讲清楚为什么又回头。 |
| `ask-user` | waiting-user | 停。用 `request_user_input` 把缺的输入问用户;补齐后 `mmw task resume` 续本阶段。 |
| `report-user` | blocked | 停。带完整经过上报用户,等指示——别自己硬闯。 |
| `done` | ready-to-close | 末阶段过 → 走本文「收尾」。 |

**`report-user`(blocked)上报用两层**(别只甩一句"卡住了"):**业务影响层**(给用户,非技术:这事卡住对用户能力 / 数据 / 交付意味着什么)+ **技术详情层**(在哪个 phase、什么 verdict、根因、已试过什么),让用户能拍下一步。
<!-- END: receipt-jump -->

<!-- BEGIN: closing-cleanup -->
## 收尾：合并 App branch，保留 App worktree

回执 `done`（`STATUS=ready-to-close`）后，先找到 `target_branch` 已有的 clean checkout。
它不存在、dirty 或正在 merge/rebase 时停止并说明缺口，不再创建 closing worktree。

在 target checkout 本地执行：

```bash
git merge --no-ff <codex/任务-branch>
```

禁止 `--squash`。本地 merge 完成并通过最终验证后，在 target checkout 运行：

```bash
mmw task cleanup --slug <slug>
```

cleanup 只删除任务 App worktree 内的 `.codex/multi-model-workflow/` 状态。App
worktree 和 App branch 都保留，由用户继续在 Codex App 中查看、handoff、archive
或管理 branch。`git push`、远端 PR merge 和部署仍须用户批准。
<!-- END: closing-cleanup -->
