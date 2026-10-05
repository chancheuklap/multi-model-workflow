---
date: 2026-10-06
amends: [0022]
---

# 机器的产品槽位全被占时，worker 的这次运行什么都不跑、退 2，票按 `ui-acceptance` 的第 4 条报受阻；不排队，也没有人为槽位叫醒它

`verify-ticket.py` 跑一张票的判据，凡是要起产品的，先向 `lease.py` 要这个工作树的槽位（`try_claim`）。工作树已经占着槽位就直接用；没有又一个都不剩，这次运行一条判据也不跑、什么都不写，退 2，stderr 说本机 N 个槽位都被占着。worker 读到的是 `Work a ticket` 第 3 步：照 `ui-acceptance` 技能 **Five rules while the product is running** 的第 4 条，开一个 `fault` 子票报受阻，停下。槽位仍然一直占到票落地或被交还（`land`、`retract`、`suspend` 交还它）。

## 要修的是什么

- 0022 给等槽位的 worker 配了一整条路：`worker.queued` 事件、中继按交还槽位的事件排叫醒、status 里「等槽位」一行、retro 把它算成停顿。2026-09-11 到 2026-10-02 中继排过 715 次叫醒，其中为槽位的 0 次；两个接入仓库都没声明产品上限，这条路在真实运行里走不到。
- 这条路大约 215 行代码、29 个测试，每改一次事件词表或中继都要跟着维护。

## Considered Options

- **保留排队，只删掉没用的部分。** 否决。排队的每一环（事件、叫醒、显示、复盘）彼此依赖，留任何一环都要留住整条链。
- **满了就在命令里等，等到有槽位为止。** 否决。这是 0010 禁的轮询，而且占着一个模型回合。
- **满了就把票交还给 triage。** 否决。机器满不是票的问题；交还会让一张没毛病的票离开这一夜，等人来处理。

## Consequences

- 0022 里「等槽位的 worker 也由中继叫醒」「`SLOT_ENDS` 排队叫醒」那部分不再成立；一个仓库一个中继、一夜一个 watch、每个 watch 叫醒开它的主 agent，这些照旧。
- 事件词表里没有 `worker.queued`；中继、watchdog、status、retro 都不再认它。
- 真的满了，worker 开 `fault` 子票，orchestrator 在 `Run a night` 第 5 步被叫醒，按 `fault` 那一行处理：是本仓库环境的事它修，是流水线的事它告诉用户。
- 任务看板（`mmw-v3/board/`）和 `docs/specs/task-board/screen-contract.yaml` 里还有「等槽位」的显示。它属于看板的屏幕契约和设计包，要改由用户定；在那之前它永远不会出现，因为没有事件再让票进入那个状态。
