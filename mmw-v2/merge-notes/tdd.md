# tdd

源目录：`mmw-v2/upstream/skills/engineering/tdd/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| `## Seams: where tests go` 的 `**Test only at pre-agreed seams.**` 一段 | 改掉「什么算 pre-agreed」：约定的载体是写下来的东西，不是一次对话——手上有票就是票的 `## Seam` 一节；没有票（用户手动跑这份技能）才回到「跟用户写下来」这一支。票缺 `## Seam` 时的退路不写：`to-tickets` 的模板每张 agent 票都带这一节，两个 tracker 的 154 张 agent 票没有一张缺它。`No test is written at an unconfirmed seam` 这条判断没删。理由：本仓库的 worker 夜里没有用户，照原句做只能停下等一个不会来的回答，或者自己伪造一次确认。上游改这一段 → 收上游对「为什么只在约定好的 seam 上测」的说法，「约定的载体是写下来的东西、不是一次对话」这一层必须留着 |
| `## Seams: where tests go` 末句 `When the shape of that interface is itself in question …` | host 中立：改成读 `codebase-design` 技能的 `SKILL.md` 取词汇。判据是这一句自己给的——`it is a reference to consult, not a session to run`。共同理由见 [README.md](README.md#host-中立)，写法见 `mmw` 技能的 `references/skill-set-rules.md` `### Paths and host neutrality` 与 `### Hand-offs` |
| `## Rules of the loop` 的 `**Refactoring is not part of the loop.**` 一条 | 现在这一条说的是：green 表示这一刀完成，重新整理结构是完成之后单独的一轮，用不带上一刀红绿压力的眼光去看，而不是在下一次红之前被顺手跳过；带票时那一轮就是它审完之后的修复轮，不带票时是每刀都绿了之后专门抽一轮做；本次改动本身该保持正确（改过的东西的调用方、改动让它变死的分支）算在这一刀里，不算重构。理由：原来只说重构归哪里，不带票单独用时那个"审完的修复轮"根本不存在，重构永远没有着落；带票时又可能被当成 `implement` 写码规则要求的"新写的东西取代了已有分支就同一个 commit 删掉它"，从而被推迟。这一条不点 `the review stage` 这种在本仓库是死词的 stage 名，也不说拿着 `code-review` 的那个会话会修东西。上游改这一条 → 不收，除非它自己也不再把 refactoring 交给一个不修东西的 review 阶段，并且给不带票的单独使用留了去处 |

### tests.md 与 mocking.md

| 段落 | 我们的意图 |
| --- | --- |
| 两份全文 | 上游原文，不改。`code-review` 技能的 Tests axis 按技能名读这两份（`references/tests-reviewer.md` 第 3 节，见 [code-review.md](code-review.md)），引用的是 `tests.md` 的 **Tautological tests**、**Implementation-detail tests** 两个小节与 red flag `Verifying through external means instead of interface`、`Test name describes HOW not WHAT`，和 `mocking.md` 的 `Don't mock` 清单。上游改这些小节名或措辞 → 收上游，同时改 `references/tests-reviewer.md` 第 3 节的指向 |
