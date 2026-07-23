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
- **design 阶段不走 handoff pass 离开**:设计定稿 + 预审结果给用户后,由用户敲 `$multi-model-workflow:approve-design` 过门(唯一人闸;引擎盖承重指纹、切 afk、推进)。
- 中途挖到 bug / 旁路优化 → `mmw spinoff --tag <bug|optimize|out-of-scope|needs-evaluation> --finding "<一句话>"`,登记成关联子任务,主流程不动。
- 阶段性进展/待拍板变化随手 `mmw note set --text "<一句话>"`——下次开场的三源回报靠它 + 提交流水 + 设计文档 Open Decisions,不靠会话记忆。

**断点续传**:任何时候 `mmw where` + 接力单 + 开场三源回报就够你接着跑——进度、产出、现场全在盘上。跨天、compaction 或新 Codex task 仍从同一份磁盘状态续跑。
