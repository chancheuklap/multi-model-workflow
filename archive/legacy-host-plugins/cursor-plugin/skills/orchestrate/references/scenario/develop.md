# Develop · 需设计审批或协调交付的完整主干

> orchestrate 已按治理能力路由到这：只读定向确认目标或架构方向需要用户设计审批，或多个独立交付切片需要协调。新功能、系统改造或优化这些名称本身不触发 MMW。
> **预设 `develop`**,两态一门:**讨论态**(investigate→propose→design,自由往返、值守 attended、和用户想清楚)→ **唯一人闸**(用户 `/approve-design` 确认设计,引擎盖指纹、切 afk)→ **流水线态**(to-issue→plan→build→package→closing,自主跑)。plan / build 产物过后各被引擎强制审一道闸(②计划审 / ④终审,`mmw where` 的 `review_start` 报);design 的审是过门前的**预审服务**(agent 自起,结果给用户参考),不是闸。
> HITL 集中在 propose(选方向)/ design(讨论 + 过门);**过门起放权自主跑**,只有缺输入 / 方向疑 / 出站红线才停。
> **propose 给方案 + 用户拍(选一个进 design,或全否回上游),不在 investigate 也不在 design 里。**

<!-- BEGIN: worktree-setup -->
## 建 worktree(进去之后才开干)

1. **起名**:从对话主题提一个人类可读、切题的 slug,格式 `YYYY-MM-DD-<theme>`(kebab,如 `2026-06-28-phone-login`)。这个名贯穿 worktree / 分支 / docs 目录,你要在 Cursor 里认得出。**把名字亮给用户但不阻塞**:`attended`(develop 讨论态)顺口让他改名;`afk` 路(bug / small-change)直接建,回执里带上名字,他不满意说一声再改(没动代码前重建零成本)。

2. **一条命令建好**(从本地最新 HEAD 分叉,scaffold docs,写 manifest):
   ```bash
   mmw task new --scenario develop --slug <slug> --title "<人类可读标题>" --request "<用户原始需求与验收条件>" \
     --entry-capability <治理能力> --entry-evidence "<触发该能力的用户原话或只读定向证据>"
   ```
   `--entry-capability` 可重复，取值为 `explicit-request`、`durable-state`、`design-approval`、`coordinated-delivery`、`gated-assurance`、`multi-result-integration`；至少传一个。不要把“新功能 / 根因不明 / 多文件”当证据。回执给出 `worktree_path`;prepare 把入口依据和阶段序列固化进 manifest。
   仅 develop:用户开口已带明确方向(不用再摆备选)→ 加 `--direction-given`,propose 阶段引擎自动降级(`where` 的 `do` 会照 manifest 报降级指令:只落方向文档+一个最强对照,不重摆 2-3 方案)。
   大任务拆并行子任务:允许在任务 worktree 内直接跑 `task new`。新 worktree 一律挂到主仓库 `.cursor/worktrees/` 下(扁平,不做目录嵌套),但分支从**当前 worktree 的 HEAD** 分叉,子任务因此继承父任务已完成的进度;父子关系写进两边 manifest 的 `parent` 与 `child_tasks`,供 `team` 视图和合并顺序溯源。清理仍需回主仓库(`cleanup` 不能删自己脚下的目录)。
   仅 develop:终点明确但整件事还在雾里(连要决定什么都还没理清、单会话装不下)→ 加 `--with-wayfind`:phases 前加 wayfind 探路阶段,先与用户逐个拍清决策再进 investigate(`where` 会把 `load` 指到 `references/wayfind.md`)。

3. **进 worktree**(Cursor 无 pi 的 `enter_worktree`;会话 cwd 靠打开该文件夹):
   - 用 Cursor **File → Open Folder**（或 Agents Window 选该 folder）打开回执里的 `worktree_path`
   - 在该窗口继续跑 `mmw where`，之后所有读写都落在该 checkout
   - **禁止**调用不存在的 `enter_worktree(...)`；不要依赖 `move_agent_to_root` 替代 Open Folder

提交进分支的文档:设计文件夹 `docs/design/<slug>/` 全部成员(主文档 `<slug>.md` 与文件夹同名 + direction/investigating/prototype/mockup/evidence 类型细分)、issue `docs/issues/`、计划 `docs/plans/`、领域 `docs/context/`(项目级资产)。**过程产物不永久存档**(`docs/.gitignore` 已忽略,随 worktree 删):审查留痕 `docs/reviews/`、终审报告。临时状态固定落 `.cursor/multi-model-workflow/`。
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

**Advisor 纪律(MMW 内覆盖全局 rule)**：Cursor 无原生 advisor，用 Task(subagent_type="advisor") + handoff pack（goal / evidence / tentative_decision / open_questions / constraints；父会话不自动转发，pack 就是它看得到的全部上下文）。**在 MMW 编排内按触发条件咨询,不按节拍咨询**——承重架构 / 数据权威 / 安全决策需要独立判断、几次具体尝试仍不收敛、或现有证据与先前判断冲突时才调。全局 rule 里「长于几步就定路线前一次、宣布完成前一次」的节拍要求**在 MMW 阶段内不适用**(它没有 MMW 的审闸;MMW 的独立保证来自①~④跨模型审者)。**禁止**:把它当每阶段的例行开场或收尾复查;review 闸内用它替代 `reviewer-*`;用它替代用户 HITL;让它直接写交付物;用它复查自己刚跑测试验证过的产物。与一手实证矛盾时以实证为准。

**断点续传**:任何时候 `mmw where` + 接力单 + 开场三源回报就够你接着跑——进度、产出、现场全在盘上。跨天或换 Cursor 会话时仍从同一份磁盘状态续跑。
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
| `ask-user` | waiting-user | 停。用 `AskQuestion` 问缺的输入（会话未挂载该工具时改聊天正文固定选项；勿用 `cursor_dialog`）；补齐后 `mmw task resume` 续本阶段。 |
| `report-user` | blocked | 停。带完整经过上报用户,等指示——别自己硬闯。 |
| `done` | ready-to-close | 末阶段过 → 走本文「收尾」。 |

**`report-user`(blocked)上报用两层**(别只甩一句"卡住了"):**业务影响层**(给用户,非技术:这事卡住对用户能力 / 数据 / 交付意味着什么)+ **技术详情层**(在哪个 phase、什么 verdict、根因、已试过什么),让用户能拍下一步。
<!-- END: receipt-jump -->

<!-- BEGIN: closing-cleanup -->
## 收尾 · 合并后删干净

回执 `done`(STATUS=ready-to-close)= 末阶段过。合并进主分支是自主收尾动作(本地可逆、不出站,不拦):用 Cursor **File → Open Folder** 打开主仓库(与进 worktree 对称;**没有 `exit_worktree(...)` 这个工具**),在该窗口跑 `git merge --no-ff <branch>`(禁 `--squash`),无人值守也自主推进;要发布到远端再 `git push`——那时 `guard-redline` 经 `beforeShellExecution` hook(failClosed)拦下来让用户亲批。任务分支 merge 进主线后,worktree 连同里面的临时状态一起删:

```bash
mmw task cleanup --slug <slug> # 回主仓库执行
```

worktree 在**使用期**持久(可跨天,别中途删);**合并后**才 cleanup,worktree + 分支 + `.cursor/multi-model-workflow/` 临时状态一并清除。
<!-- END: closing-cleanup -->
