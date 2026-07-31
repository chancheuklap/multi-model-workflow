---
name: mmw-next
description: 往主干下一格走，或跳到用户点名的那一格。
argument-hint: "[探路|查清现状|给方案|做设计|切片|写计划|落地|出包|收尾]，不给就往下一格"
---

## 怎么做

1. 读 `.mmw/task.json`。
2. **唯一拒绝点**：当前是 `mmw-design` 且 `design_approved` 是 null，停下，请用户敲 `/mmw-approve-design`。
3. 定目标那一格：用户给的是中文格名，认出它是哪份技能——九份你都装着，每份 description 的头一个词就是那个中文名。没给参数就取主干上的下一格。
4. 把那份技能的名字写回 `phase`，同时把这一格为什么停下、下一步等什么写进 `note`。下次新开会话 `/mmw` 要原样念它。
5. 告诉用户到了哪一格，用中文格名说，别念技能名。然后读那份技能开始干——`phase` 里存的就是它的名字。产物落在哪由它自己说，不在这里找。

无人值守时自己敲 `/mmw-next` 即为代敲，`note` 里写明这是代敲和依据。

主干顺序：`mmw-wayfind` → `mmw-investigate` → `mmw-propose` → `mmw-design` → `mmw-to-issue` → `mmw-plan` → `mmw-build` → `mmw-package` → `mmw-done`。

---

## 线下 · 不是技能内容

### 施工单

- **来源**：`plugin/scripts/flow.sh` 的 handoff 与阶段推进
- **保留**：改 phase、算约定路径、指向目标格的技能
- **删除**：推进引擎、阶段序列与游标、五个结论词、审闸强制、打转守卫、掉头台账——它们的接收方都是那台引擎

<!-- 方法论正文待填。填之前先读「来源」里的旧文件全文，按保留与删除两列取舍。 -->
