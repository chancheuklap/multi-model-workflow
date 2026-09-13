---
date: 2026-09-14
amends: [0018, 0019, 0020, 0021, 0022, 0023, 0024]
---

# 取消 verifier 会话；worker 在 review 后对最终 commit 运行全部 acceptance criteria，并由 closeout 直接核验这次运行

一张 ticket 只派发 worker 和 reviewer。Review 结束并处理 finding 后，worker 用 `--reverify --actor worker` 对最终 `HEAD` 完整运行 acceptance criteria；closeout 只接受最新的这次 `ticket.checked`，并核对 actor、commit、result 与当前 criterion shape。Main agent 在落地后的回归检查仍使用 `--reverify --actor main`。旧的 verifier events 不再属于事件词表，也不参与 fold。

## 要解决的问题

独立 verifier 会话重复运行 worker 已能完成的机械 criteria，却新增一份模型配置、一次 session 启动、四种 events、relay wake、watchdog hold 与失败恢复路径。它并不提供 code review 的独立判断；reviewer 已承担 Standards、Spec、Tests 三个判断轴。保留这个角色使 closing proof 分散在 `ticket.checked` 和 verifier result 两套记录里。

迁移脚本 `mmw-v2/migrations/remove-verifier.py` 在升级前检查没有 active watch，也没有 open ticket 留着未完成的 `verifier.started`，随后删除历史 retired events 尾部的 machine block，并在锁内原子删除 `models.json` 的旧 role row。评论给人看的正文保留。

## Considered Options

- **保留独立会话，只把结果并入 `ticket.checked`。** 否决：session、model row、relay 与 liveness 分支仍全部存在，没有消除重复流程。
- **由 reviewer 完成 final run。** 否决：reviewer 的职责是判断 diff，且它的 report 在 worker 修复之前；让它同时证明最终 commit 会要求第二轮 review 或混合两种职责。
- **closeout 自己运行全部 criteria。** 否决：closeout 还要执行 repository checks；把两次运行合在 gate 内会让失败记录、重试位置与 product lease 边界不清楚。

## Consequences

- 每张 ticket 少一个模型会话、一行 machine configuration、四种 events 及其 wake 与 liveness 分支。
- Final proof 只有一份：actor 为 `worker`、commit 等于 `HEAD`、result 为 `met`、criterion shape 与 ticket 当前正文一致的最新 `reverify` event。
- `--reverify` 必须显式给 `--actor worker|main`，遗漏 actor 会直接拒绝，避免两种阶段写出无法判断来源的记录。
- 旧历史不能靠 compatibility 分支继续解释；迁移必须在升级代码前运行，且 active work 存在时拒绝修改。

