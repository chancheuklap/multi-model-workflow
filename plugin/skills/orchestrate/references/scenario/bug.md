# Bug · 根因不明的修复

> orchestrate 路由到这:**bug / 报错 / regression,根因不明**。这条路从头到尾就读这一份,不用回 SKILL。
> **预设 `bug`**,阶段序列:查清(查根因)→ 落地(修)→ 验收 → 收尾(investigate→build→verify→closing)。无 design / plan、无审闸——bug 是定点修,不走设计/计划的重流程。
>
> **三个 bug 专属点**(方法论在各阶段 reference,这里点明这条路怎么用它们):
> - **查清 = 跑 `diagnosing-bugs` 查根因**:investigate 阶段用 `diagnosing-bugs` skill 复现 → 隔离 → 定位根因(`investigate-internal` workflow 的 angle 选 `diagnosing-bugs`),产出带 `file:line` 的根因报告,不泛泛查现状。够窄(单函数/已知文件)就主线程直接 `diagnosing-bugs` + `rg`/`Read` 查完,别起 workflow。
> - **落地 = 主线程就地 TDD 定点修**(不派 Codex):build 阶段按 `mmw where` 报的 `scenario=bug` 就地 TDD 定点修(build 自按 scenario 选落地模式)——先按根因写一条**复现失败测试**,再最小修、转绿、提交。改动跨多文件 → 先写一份**单计划**(主线程自己写,不派 plan-writer、不进计划审)理清 Task Pack 再逐个 TDD;简单定点修直接修。
> - **根因是系统性设计问题 → 原地升级 develop**:investigate 发现根因不是局部 bug 而是设计级缺陷(要重做设计 / 拆计划)→ `mmw task escalate --to develop` 把剩余流水线换成 develop 完整设计路(investigate→propose→design→to-issue→plan→build→verify→closing),**worktree 不重开、已查的根因投查成果全留**,游标回 investigate 带设计意图重查。升级前先一句话告诉用户"这不是局部 bug,是设计级问题,升级到设计路",别闷头升。

<!-- BEGIN: worktree-setup -->
## 建 worktree(进去之后才开干)

1. **起名**:从对话主题提一个人类可读、切题的 slug,格式 `YYYY-MM-DD-<theme>`(kebab,如 `2026-06-28-phone-login`)。这个名贯穿 worktree / 分支 / docs 目录,你要在 VSCode 里认得出。**向用户确认一次**(可同时让他改名)。

2. **一条命令建好**(从本地最新 HEAD 分叉,scaffold docs,写 manifest):
   ```bash
   mmw task new --scenario <你这条路径:small-change|develop|bug> --slug <slug> --title "<人类可读标题>"
   ```
   回执给出 `worktree_path`;prepare 把本路径的阶段序列固化进 manifest 的 `phases`。

3. **进 worktree**(只有这步能切会话 cwd,脚本切不了):
   ```
   EnterWorktree({ path: "<回执里的 worktree_path>" })
   ```

文档产出提交进分支(查清 `docs/investigating/`、设计 `docs/design/`、issue `docs/issues/`、计划 `docs/plans/`、领域 `docs/context/`);临时状态落 `.claude/multi-model-workflow/`(随 worktree 删)。
<!-- END: worktree-setup -->

<!-- BEGIN: phase-contract -->
## 阶段运行契约(进 worktree 后的主循环)

进 worktree 后,你对每个阶段都做同样 4 个动作。阶段之间唯一变的是「干」用哪套方法论;进 / 钉 / 交完全一样。**这是个循环**:④ 交完拿到回执 → 按回执跳到目标阶段 → 回 ① 进 → …… 直到回执说收尾。你不预判、不跳号,只认回执。

| 动作 | 做什么 | 命令 / 机制 |
|---|---|---|
| **① 进** | `mmw where` 直接报:在哪阶段、在不在审闸、上阶段钉了什么(`prev_outputs` 照单读,不自己找)、`load`(读哪份)/ `do`(干什么)/ `then`(交什么)。照 `load` 加载 | `mmw where` |
| **② 干** | 按 `where` 的 `do` 跑该阶段方法论(唯一因阶段而异),读 `prev_outputs` 当输入 | `load` 指向的 reference(阶段方法论都在 `references/` 下,含 design/、plan/) |
| **③ 钉** | 把本阶段承重产出钉进接力单,下阶段照单读 | handoff 的 `--produced` |
| **④ 交** | 给一个结论词,引擎算下一步、写进度、回执;照本文「回执 → 怎么跳」表行动 | `mmw handoff` |

**③ 钉 + ④ 交 —— 一条 handoff:**

```bash
mmw handoff --conclusion <结论词> [--produced <本阶段产出路径>]...
```

- **结论词**五选一(`pass` / `needs-repair` / `needs-redirection` / `needs-context` / `blocked`),选哪个是你的判断;`where` 的 `then` 已给好带承重产出的命令模板。缺结论或词非法当场拦(fail-closed)。
- **`--produced` 必带本阶段承重产出**——它钉进接力单,下阶段靠它接,不靠"自己找"。
- 中途挖到 bug / 旁路优化 → `mmw spinoff --tag <bug|optimize|out-of-scope|needs-evaluation> --finding "<一句话>"`,登记成关联子任务,主流程不动。

**断点续传**:任何时候 `mmw where` + 接力单就够你接着跑——进度、游标、各阶段产出全在 manifest,不靠会话记忆。
<!-- END: phase-contract -->

<!-- BEGIN: receipt-jump -->
## 回执 → 怎么跳(阶段间流转的全部规则)

`mmw handoff` 回执三行 `NEXT_ACTION` / `NEXT_PHASE` / `STATUS`,照这张表行动:

| `NEXT_ACTION` | `STATUS` | 你下一步 |
|---|---|---|
| `advance` | active | 往下跳:回 ① 进,对 `NEXT_PHASE` 跑 `mmw where`。**正常前进就是这条。** |
| `review` | active | 别 advance(phase 没动)。进审闸:`where` 的 `load` 自动切到 `review/review.md`,跑 `REVIEW_STAGE` 的审 loop;审完再 `handoff` 一次 verdict —— `pass` 才真 advance,`needs-repair` 回本阶段返工。 |
| `repair` | active | 留在本阶段返工:回 ② 干按缺陷改,改完再 `handoff`。 |
| `turn-around` | active | 掉头回上游:对 `NEXT_PHASE` 回 ① 进重跑。 |
| `ask-user` | waiting-user | 停。把缺的输入问用户(在场 `AskUserQuestion`);补齐后 `mmw task resume` 续本阶段。 |
| `report-user` | blocked | 停。带完整经过上报用户,等指示——别自己硬闯。 |
| `done` | ready-to-close | 末阶段过 → 走本文「收尾」。 |

`repair` / `turn-around` 有上限(引擎命令计数强制),到顶自动转 `report-user`(STATUS=blocked),绝不无限往返。
<!-- END: receipt-jump -->

<!-- BEGIN: closing-cleanup -->
## 收尾 · 合并后删干净

回执 `done`(STATUS=ready-to-close)= 末阶段过。合并是红线:用户确认后 `mmw release-approve` → `git merge --no-ff <branch>`(禁 `--squash`)。任务分支 merge 进主线后,worktree 连同里面的临时状态一起删:

```bash
mmw task cleanup --slug <slug>   # 回主仓库执行
```

worktree 在**使用期**持久(可跨天,别中途删);**合并后**才 cleanup,worktree + 分支 + `.claude/` 临时状态一并清除。
<!-- END: closing-cleanup -->
