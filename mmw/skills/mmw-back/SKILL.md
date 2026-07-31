---
name: mmw-back
description: 退回一个阶段。点名一个阶段就退到那个，不点就退上一个。落地完回设计改东西走这条。
argument-hint: "[探路|查清现状|给方案|做设计|切片|写计划|落地|出包|收尾]"
---

1. 读 `.mmw/task.json`。
2. 把 `phase` 改成目标阶段的技能名。用户点了阶段就去那个，没点就按下面的顺序取上一个。
3. **目标是 `mmw-design` 就把 `design_approved` 改回 null**，并告诉用户设计改完要重新敲 `/mmw-approve-design`。退回别的阶段不动这个字段。
4. 把这次为什么退回、回去要改什么写进 `note`。
5. 读 `phase` 里那份技能，接着干。

`mmw-wayfind` → `mmw-investigate` → `mmw-propose` → `mmw-design` → `mmw-to-issue` → `mmw-plan` → `mmw-build` → `mmw-package` → `mmw-done`

---

## 线下 · 不是技能内容

**为什么只有退回设计才清过门标记**：过门锁的是那份设计文档当时的内容。回到设计就是要动它，动完再往下走必须重新确认。退回查清现状、退回给方案不碰设计文档，标记照旧。这样判不必让用户交代意图，也不必给文档算哈希——目标阶段自己就是意图。

**为什么不写「照 `mmw-next` 那几步做，方向相反」**：读这份的人眼前只有这一份，`mmw-next` 的第几步他数不到。五步全写出来，两份各自读得完。

### 施工单

- **来源**：`plugin/scripts/flow.sh` 的 needs-redirection
- **保留**：改 phase 并说清退回了哪个阶段
- **删除**：掉头计数与方向横跳判据；讨论态与流水线态的区分；回上一个阶段要向用户汇报的强制模板
