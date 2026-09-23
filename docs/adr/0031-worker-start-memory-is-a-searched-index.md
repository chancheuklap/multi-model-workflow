---
date: 2026-09-18
amends: []
---

# worker 开工时拿到的是两份有上限的 Memory 索引：相关经验用本票 `## Owns` 路径和各级标题的短查询搜出，不用 spec 或 map 正文

`dispatch.sh start <n> worker` 把 Memory 放进 worker 首次 prompt 的方式：当前 task 的记录按 task scope label 列出最新 30 条；相关经验对本票 `## Owns` 下每条路径（最多 8 条）和 ticket、spec、map 标题各做一次 `memories search --label mmw-experience --limit 10`，合并后最多 15 条，正文写到本票某条路径的记录排前，其次按命中次数，最后按单次 score。两份都只放索引行（id、title、正文首行、Space），worker 自己判断打开哪几条。

## 要修的是什么

最初的设计让 worker start 以 map 的 `Destination`、`Notes`、`Decisions so far` 或 standalone spec 的四个已定章节做一次 semantic search，并把命中记录的完整正文放进 prompt。实测这条路径取不回任何东西：Nowledge Mem 的 `memories search` 在查询词含有任何记录都没有的具体标识时整批不返回（`--explain` 报 `unsupported_specific_anchor`），而 spec 与 map 正文必然含有这类标识。score 也只在同一次 search 内可比，一张无关仓库的 ticket 同样得到 0.78，所以不能用阈值过滤。

路径和标题是短查询：路径正是 worker 写 Memory 时在“证据”里写出的具体标识，标题只含任务名词。放完整正文会让 prompt 随 Memory 总量增长；索引行有固定上限，完整内容由 worker 用 `memories show` 按需打开。

## Considered Options

- 用 spec / map 正文做一次长查询：否决。上述 anchor 行为使它在真实 Memory 上返回 0 条。
- 列出 repository 与 `mmw-toolbox` 的全部 `mmw-experience` 记录：否决。prompt 随记录数线性增长，且大部分与本票无关。
- 设 score 阈值过滤：否决。score 跨 search 不可比，无关 ticket 也能拿到高分。
- 把命中记录的完整正文放进 prompt：否决。15 条完整正文会占掉 worker 的上下文，而 worker 通常只需要其中几条。

## Consequences

- worker 写 Memory 时必须在“证据”里写出涉及的仓库路径，否则后来的 worker 按路径搜不到它；`implement` 的 `## Shared experience while implementing` 写明了这一点。
- worker 运行中的 search 也只用报错、命令与组件做查询词，并放在 `--` 之后，理由相同。
- 没有 `## Owns` 的旧 ticket 只剩三个标题做查询词，相关经验明显变少。
- 当前 task 超过 30 条时，索引首行写 `truncated:`，其余记录要靠 task-scope search 取得。
