## 回执 → 怎么跳(阶段间流转的全部规则)

`mmw handoff` 回执三行 `NEXT_ACTION` / `NEXT_PHASE` / `STATUS`,照这张表行动:

| `NEXT_ACTION` | `STATUS` | 你下一步 |
|---|---|---|
| `advance` | active | 往下跳:回 ① 进,对 `NEXT_PHASE` 跑 `mmw where`。**正常前进就是这条。** |
| `review` | active | 别 advance(phase 没动)。进审闸:`where` 的 `load` 自动切到 `review.md`,跑 `REVIEW_STAGE` 的审 loop;审完再 `handoff` 一次 verdict —— `pass` 才真 advance,`needs-repair` 回本阶段返工。 |
| `repair` | active | 留在本阶段返工:回 ② 干按缺陷改,改完再 `handoff`。 |
| `turn-around` | active | 掉头回上游:对 `NEXT_PHASE` 回 ① 进重跑。 |
| `ask-user` | waiting-user | 停。把缺的输入问用户(在场 `AskUserQuestion`);补齐后 `mmw task resume` 续本阶段。 |
| `report-user` | blocked | 停。带完整经过上报用户,等指示——别自己硬闯。 |
| `done` | ready-to-close | 末阶段过 → 收尾(见下)。 |

`repair` / `turn-around` 有上限(引擎命令计数强制),到顶自动转 `report-user`(STATUS=blocked),绝不无限往返。
