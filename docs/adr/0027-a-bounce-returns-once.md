---
date: 2026-09-14
amends: [0023]
---

# 同一夜第一次 landing conflict 把 ticket 交回原 worker，第二次才交 triage

`dispatch.sh advance <spec>` 与 `dispatch.sh land <n>` 以最新 `spec.opened` 为夜的边界：第一次 `ticket.bounced` 把 ticket 放回 `ready-for-agent`，保留 standing workspace，让下一次 `advance` 启动原 worker；第二次才放进 `needs-triage`。第一次 bounce 的 worker 从 preflight 开始，先把最新 `origin/<base branch>` 合进 ticket branch，再运行全部 acceptance criteria 和 closeout；不再启动 reviewer，因为 reviewer 已经审过 ticket 自己的改动。

## 为什么只交回一次

landing conflict 是 ticket 改动与同夜较早 landing 的改动在 base branch 上相遇。原 worker 已经掌握 ticket 的范围、验收条件和 reviewer 结论，也拥有保留下来的 workspace，因此它是完成这次 integration 的最小责任边界。

同一个 ticket 第二次仍然不能 landing，说明问题不是一次新的 base branch integration 足以解决。继续自动重试会令一张票在没有新判断的情况下重复占用夜间执行容量，因此第二次交给 triage。

记录 bounce 的那次 `advance` 不得在同一次 frontier 计算中立刻重启 ticket。它先停止旧 session、释放 product slot 并写完事件；下一次 `advance` 才从 standing workspace 启动原 worker，使事件状态、队列状态和实际 session 一致。

## Considered Options

- 第一次冲突立即交给 triage：否决。它把通常只需要一次 base branch integration 的工作留到早间人工处理，也丢掉原 worker 已有的上下文。
- 由 main agent 在 merge worktree 里解决冲突：否决。main agent 没有运行 ticket 全部 acceptance criteria 与 closeout 的责任边界，会把实现责任分到两个 session。
- 一直交回 worker：否决。重复冲突没有终止条件，会让同一张票在一夜内无限重试。
- 第一次 bounce 后在同一次 `advance` 立即重启：否决。旧 session 的停止、slot 释放和新 session 的开始会挤进一次状态转换，难以从事件折叠判断实际在跑的是谁。

## Consequences

- `ticket.bounced` 不再等同于 triage；是否进入 triage 取决于它是不是最新 `spec.opened` 之后的第二次 bounce。
- `NIGHT SUMMARY` 的 `Bounced:` 只列仍带 `needs-triage` 的 bounced ticket；已被 worker 修复并关票的第一次 bounce 不列入。
- standing workspace 与原 ticket branch 跨第一次 bounce 保留，原 worker 可在新 base 上完成 integration，而不重复 reviewer 阶段。
- 一夜最多为同一张票自动承担一次 landing integration；第二次失败明确留给早间 triage。
