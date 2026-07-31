---
name: mmw-next
description: 往下一个阶段走，或跳到指定阶段。
argument-hint: "[阶段]"
---

## 怎么做

1. 读 `.mmw/task.json`。
2. **唯一拒绝点**：当前是 `design` 且 `design_approved` 是 null，停下，让用户敲 `/mmw-approve-design`。
3. 定目标阶段：给了参数就是那个阶段（中文名与英文键都认）；没给就取下一个阶段。
4. 写回 `phase`，同时把这个阶段为什么停下、下一步等什么写进 `note`。下次新开会话 `/mmw` 要原样念它。
5. 报给用户到了哪个阶段，接着读那个阶段的技能（`mmw-<阶段键>`，只有收尾读 `mmw-done`）开始干。产物落在哪由它自己说，不在这里找。

无人值守时自己敲 `/mmw-next` 即为代敲，`note` 里写明这是代敲和依据。

阶段顺序：`wayfind` → `investigate` → `propose` → `design` → `to-issue` → `plan` → `build` → `package` → `closing`。

---

## 线下 · 不是技能内容

### 施工单

- **来源**：`plugin/scripts/flow.sh` 的 handoff 与阶段推进
- **保留**：改 phase、算约定路径、指向目标格的技能
- **删除**：推进引擎、阶段序列与游标、五个结论词、审闸强制、打转守卫、掉头台账——它们的接收方都是那台引擎

<!-- 方法论正文待填。填之前先读「来源」里的旧文件全文，按保留与删除两列取舍。 -->
