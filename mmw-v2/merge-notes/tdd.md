# tdd

源目录：`mmw-v2/upstream/skills/engineering/tdd/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| `## Seams: where tests go` 的 `**Test only at pre-agreed seams.**` 一段 | 改掉「什么算 pre-agreed」：约定的载体是写下来的东西，不是一次对话——手上有票就是票的 `## Seam` 一节；票没有那一节，就沿它的 `## Parent` 到 spec 的 `## Testing Decisions` 推出 seam，先评论到票上再写码；没有票（用户手动跑这份技能）才回到「跟用户写下来」这一支。`No test is written at an unconfirmed seam` 这条判断没删。理由：本仓库的 worker 夜里没有用户，照原句做只能停下等一个不会来的回答，或者自己伪造一次确认。上游改这一段 → 收上游对「为什么只在约定好的 seam 上测」的说法，「约定的载体是写下来的东西、不是一次对话」这一层必须留着 |
| `## Seams: where tests go` 末句 `When the shape of that interface is itself in question …` | host 中立：改成读 `codebase-design` 技能的 `SKILL.md` 取词汇。判据是这一句自己给的——`it is a reference to consult, not a session to run`。共同理由与三种替换写法见 [README.md](README.md#host-中立) |
| `## Rules of the loop` 的 `**Refactoring is not part of the loop.**` 一条 | 改成 refactoring 落在 review 之后那一轮票内修复里、与被审的代码受同一套写作规则约束，不点任何 stage 的名。理由：`the review stage` 在本仓库是死词，而拿着 `code-review` 的那个会话本身不修任何东西。上游改这一条 → 不收，除非它自己也不再把 refactoring 交给一个不修东西的 review 阶段 |
