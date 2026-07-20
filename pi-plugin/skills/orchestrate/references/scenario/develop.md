# Develop · 新功能 / 优化改造完整主干

> orchestrate 路由到这:**新想法 / 功能,或旧系统优化改造**(要设计)。这条路从头到尾就读这一份,不用回 SKILL。
> **预设 `develop`**,两态一门:**讨论态**(investigate→propose→design,自由往返、值守 attended、和用户想清楚)→ **唯一人闸**(用户 `/approve-design` 确认设计,引擎盖指纹、切 afk)→ **流水线态**(to-issue→plan→build→package→closing,自主跑)。plan / build 产物过后各被引擎强制审一道闸(②计划审 / ④终审,`mmw where` 的 `review_start` 报);design 的审是过门前的**预审服务**(agent 自起,结果给用户参考),不是闸。
> HITL 集中在 propose(选方向)/ design(讨论 + 过门);**过门起放权自主跑**,只有缺输入 / 方向疑 / 出站红线才停。
> **propose 给方案 + 用户拍(选一个进 design,或全否回上游),不在 investigate 也不在 design 里。**

<!-- BEGIN: worktree-setup -->
## 建 worktree(进去之后才开干)

1. **起名**:从对话主题提一个人类可读、切题的 slug,格式 `YYYY-MM-DD-<theme>`(kebab,如 `2026-06-28-phone-login`)。这个名贯穿 worktree / 分支 / docs 目录,你要在 VSCode 里认得出。**把名字亮给用户但不阻塞**:`attended`(develop 讨论态)顺口让他改名;`afk` 路(bug / small-change)直接建,回执里带上名字,他不满意说一声再改(没动代码前重建零成本)。

2. **一条命令建好**(从本地最新 HEAD 分叉,scaffold docs,写 manifest):
   ```bash
   mmw task new --scenario develop --slug <slug> --title "<人类可读标题>" --request "<用户原始需求与验收条件>"
   ```
   回执给出 `worktree_path`;prepare 把本路径的阶段序列固化进 manifest 的 `phases`。
   仅 develop:用户开口已带明确方向(不用再摆备选)→ 加 `--direction-given`,propose 阶段引擎自动降级(`where` 的 `do` 会照 manifest 报降级指令:只落方向文档+一个最强对照,不重摆 2-3 方案)。

3. **进 worktree**(只有这步能切会话 cwd,脚本切不了):
   ```
   `enter_worktree({ path: "<回执里的 worktree_path>" })`
   ```

提交进分支的文档:设计文件夹 `docs/design/<slug>/` 全部成员(主文档 `<slug>.md` 与文件夹同名 + direction/investigating/prototype/mockup/evidence 类型细分)、issue `docs/issues/`、计划 `docs/plans/`、领域 `docs/context/`(项目级资产)。**过程产物不永久存档**(`docs/.gitignore` 已忽略,随 worktree 删):审查留痕 `docs/reviews/`、终审报告。临时状态固定落 `.pi/multi-model-workflow/`。
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

**Advisor 纪律**:advisor 工具是执行者的强判断顾问(零参数,自动转发全对话),非审闸、不替用户拍板、不写产物。需要先定位文件/读源时先做 orientation,随后在实质写作、解释或路线固化前咨询;长于几步的任务至少在定路线前一次、承重产物已落盘并验证后再一次。短任务若下一步已被刚读到的工具结果唯一决定,不重复咨询。卡住、结果与预期不符或准备换路时也咨询。**禁止**:review 闸内用它替代 `reviewer-*`;用它替代用户 HITL;让它直接写交付物。咨询前把证据和当前决策在对话里摆清楚,它才看得到。与一手实证矛盾时以实证为准。

**断点续传**:任何时候 `mmw where` + 接力单 + 开场三源回报就够你接着跑——进度、产出、现场全在盘上。跨天或换 pi 会话时仍从同一份磁盘状态续跑。
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
| `ask-user` | waiting-user | 停。用 `ask_user` 把缺的输入问用户;补齐后 `mmw task resume` 续本阶段。 |
| `report-user` | blocked | 停。带完整经过上报用户,等指示——别自己硬闯。 |
| `done` | ready-to-close | 末阶段过 → 走本文「收尾」。 |

**`report-user`(blocked)上报用两层**(别只甩一句"卡住了"):**业务影响层**(给用户,非技术:这事卡住对用户能力 / 数据 / 交付意味着什么)+ **技术详情层**(在哪个 phase、什么 verdict、根因、已试过什么),让用户能拍下一步。
<!-- END: receipt-jump -->

<!-- BEGIN: closing-cleanup -->
## 收尾 · 合并后删干净

回执 `done`(STATUS=ready-to-close)= 末阶段过。合并进主分支是自主收尾动作(本地可逆、不出站,不拦):`exit_worktree({ action: "keep" })` 回主仓库,再跑 `git merge --no-ff <branch>`(禁 `--squash`),无人值守也自主推进;要发布到远端再 `git push`——那时 `guard-redline` 经 pi 扩展弹确认框由用户亲批(无令牌可代批)。任务分支 merge 进主线后,worktree 连同里面的临时状态一起删:

```bash
mmw task cleanup --slug <slug> # 回主仓库执行
```

worktree 在**使用期**持久(可跨天,别中途删);**合并后**才 cleanup,worktree + 分支 + `.pi/multi-model-workflow/` 临时状态一并清除。
<!-- END: closing-cleanup -->
