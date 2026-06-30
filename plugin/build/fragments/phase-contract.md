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
