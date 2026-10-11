---
date: 2026-10-09
amends: [0026]
---

# 关票的最终证明是 `HEAD` 上最新的一次 worker 运行：关票接受的和关票评论引用的是同一次；第一次运行之后没有新提交时，就是第一次运行

ADR 0026 定 final proof 只有一份：最新的 worker `reverify`。可 Work a ticket 第 3 步已经在同一个提交上跑过全部标准，审查没有发现、之后也没有新提交时，第 8 步再跑一遍是同一个结论验第二次；而关票评论的证据取自第 3 步那次，关票认的却是第 8 步那次，主人读到的不是关票依据的那次。这份决定改写 0026 的那一条：`--closeout` 接受、`--draft` 引用的，都是 actor 为 `worker` 的最新一次运行，不论是第 3 步的那次还是 `--reverify --actor worker`；它必须在 `HEAD` 上、result 为 `met`、criterion shape 与票的当前正文一致。

## 要修的是什么

审查 `docs/reviews/2026-10-09-verification/README.md` 问题 3。修法同时改了 `work-a-ticket.md`：审查修复之后只跑 `dispatch.sh integrate`，不再跑全部标准，第 8 步是修复后唯一的一次；第 3 步之后没有提交时第 8 步跳过。

## Considered Options

- **仍只认 `reverify`，让 `--draft` 也改读它。** 否决。两处一致了，可没有新提交时仍要在同一个提交上把全部标准再跑一遍，最贵的驱动产品的标准也在内。
- **只认第 3 步那次。** 否决。审查修复和 Audit 之后的提交必须有一次运行在其上。

## Consequences

- worker 的每次运行都记 `outside_owns`：任何一次都可能是关票引用的那次，关票评论的 `Outside Owns:` 一行取自它。main agent 在合并分支上的 `reverify` 仍不记。
- 0026 的其余部分不变：没有 verifier 会话；`--reverify` 必须给 `--actor`；main agent 落地后的回归检查仍是 `--reverify --actor main`。
- 续跑点按新顺序算：审查之后没有自己的运行时回到 Read the review，运行之后又有提交时到 Audit，`HEAD` 上已有运行时到 Run every criterion one final time（它的完成判据此时已满足）。
