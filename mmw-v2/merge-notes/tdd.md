# tdd

源目录：`mmw-v2/upstream/skills/engineering/tdd/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| `## Seams: where tests go` 的 `**Test only at pre-agreed seams.**` 一段 | 改掉「什么算 pre-agreed」：约定的载体是写下来的东西，不是一次对话——手上有票就是票的 `## Seam` 一节；没有票（用户手动跑这份技能）才回到「跟用户写下来」这一支。票缺 `## Seam` 时的退路不写：`to-tickets` 的模板每张 agent 票都带这一节，两个 tracker 的 154 张 agent 票没有一张缺它。`No test is written at an unconfirmed seam` 这条判断没删。理由：本仓库的 worker 夜里没有用户，照原句做只能停下等一个不会来的回答，或者自己伪造一次确认。上游改这一段 → 收上游对「为什么只在约定好的 seam 上测」的说法，「约定的载体是写下来的东西、不是一次对话」这一层必须留着 |
| `## Seams: where tests go` 末句 `When the shape of that interface is itself in question …` | host 中立：改成读 `codebase-design` 技能的 `SKILL.md` 取词汇。判据是这一句自己给的——`it is a reference to consult, not a session to run`。共同理由见 [README.md](README.md#host-中立)，写法见 `writing-for-agents` 技能的 `SKILL-SET-REVIEW.md` `### Paths, tokens and host neutrality` 与 `### Hand-offs` |
| `## Rules of the loop` 的 `**Refactoring is not part of the loop.**` 一条 | 改成 refactoring 落在 review 之后那一轮票内修复里、与被审的代码受同一套写作规则约束，不点任何 stage 的名。理由：`the review stage` 在本仓库是死词，而拿着 `code-review` 的那个会话本身不修任何东西。上游改这一条 → 不收，除非它自己也不再把 refactoring 交给一个不修东西的 review 阶段 |

### tests.md 与 mocking.md

| 段落 | 我们的意图 |
| --- | --- |
| 两份全文 | 上游原文，不改。`code-review` 技能的 Tests axis 按技能名读这两份（`references/tests-reviewer.md` 第 2 节，见 [code-review.md](code-review.md)），引用的是 `tests.md` 的 **Tautological tests**、**Implementation-detail tests** 两个小节与 red flag `Verifying through external means instead of interface`、`Test name describes HOW not WHAT`，和 `mocking.md` 的 `Don't mock` 清单。上游改这些小节名或措辞 → 收上游，同时改 `references/tests-reviewer.md` 第 2 节的指向 |
