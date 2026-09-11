---
date: 2026-09-11
amends: [0012]
---

# base branch 以 GitHub 上那份为准：本机与云端走同一条合并路径，先合、再查、再 fast-forward 推送，合不进去交给 triage

票开始、落地与重新验收都以 `origin/<base branch>` 为权威。`advance`、`land` 与 `reverify` 在每条 base branch 的常驻 detached worktree 里取回并重置；落地合并 `ticket.passed.commit`，在合并结果上跑 repository checks，最后 fast-forward 推送。冲突或检查失败不改变 base branch，改成 `ticket.bounced` 交给早上的 triage。

## 要修的是什么

- 本机 base branch 作为合并目标时，本机 agent 与云端 agent 看见的集成状态不同；另一个 checkout 还会被合并过程移动或留下冲突。
- 票关闭以后，ticket branch 可能继续前进；落地必须合并已经验收的 commit，而不是分支当前末端。
- 合得干净不等于组合后仍正确；repository checks 必须看合并结果，并以 `MMW_BASE_REF=origin/<base branch>` 比较同一份基线。
- fast-forward push 被拒说明 origin 已前进，旧合并结果不再是要发布的结果；必须取回、重合、重查。

## Considered Options

- **继续在 main agent 的 checkout 合并。** 否决。它把本机分支状态变成隐含权威，也会让冲突污染主会话正在使用的目录。
- **直接推 ticket branch 或当前 tip。** 否决。它可能发布 `ticket.passed` 之后、未被 verifier 覆盖的提交，也没有验证与最新 base branch 组合后的结果。
- **冲突或检查失败时让 `advance` 停住，等 main agent 当晚修。** 否决。后面的独立票会一起停住，而且失败票会绕过正常的 review 与 verification。`ticket.bounced` 保留工作区与证据，交给 triage 决定下一次工作。
- **推送被拒后强推。** 否决。它会删除别人刚落到 base branch 的工作；重新取回与重跑检查才保留双方结果。

## Consequences

- 本机与云端 worker 从同一个 origin 基线开始，base branch 的集成结果也只在 origin 上成立；本机同名分支只是缓存。
- 每条 base branch 多一个常驻 detached worktree 和一把锁，换来 ignored dependencies 可复用、caller checkout 不动、同机合并串行。
- `ticket.landed` 只在 push 成功后写，并同时记录 passed commit、base branch 与 merge commit；已经在 origin 里的 passed commit 不再生成新 merge。
- `ticket.bounced` 重开票、移入 `needs-triage`、释放认领与 slot，但保留 ticket worktree；同一夜不再试这张票，也不唤醒 worker。
- consuming repository 的 checks 与 `CHECK:` 不应写死本机 branch 名，统一从 `MMW_BASE_REF` 读取比较基线。
