---
name: mmw-next
description: 往下一个阶段走。点名一个阶段就跳到那个，不点就走下一个。
argument-hint: "[探路|查清现状|给方案|做设计|切片|写计划|落地|出包|收尾]"
---

1. 读 `.mmw/task.json`。**当前是 `mmw-design` 而 `design_approved` 是 null 就停在这里**，请用户先敲 `/mmw-approve-design`。
2. 把 `phase` 改成目标阶段的技能名。用户点了阶段就去那个，没点就按下面的顺序取下一个。
3. 把这次为什么停、下一步等什么写进 `note`。新开会话时 `/mmw` 只念得出这一句。
4. 读 `phase` 里那份技能，接着干。

`mmw-wayfind` → `mmw-investigate` → `mmw-propose` → `mmw-design` → `mmw-to-issue` → `mmw-plan` → `mmw-build` → `mmw-package` → `mmw-done`

用户不在场、你自己走了这一份，`note` 里写明这一步是你替他推的以及凭什么推。

---

## 线下 · 不是技能内容

**中文阶段名怎么对应到技能，正文一个字都不写**：主线程装着那九份技能，`description` 头一个词就是阶段名，它看到「落地」自然去 `mmw-build`。曾经写过一句「认出它是哪份技能——每份 description 的头一个词就是那个中文名」，那是拿话教一个模型做它默认就会做的事，删了。

**主干顺序为什么在这份和 `mmw-back` 里各写一行**：读的人眼前只有当前这一份，写「顺序见另一份」他就得跨文件找。九个箭头一行的重复，比一次跳转便宜。

### 施工单

- **来源**：`plugin/scripts/flow.sh` 的 handoff 与阶段推进
- **保留**：改 phase、算约定路径、指向目标阶段的技能
- **删除**：推进引擎、阶段序列与游标、五个结论词、审闸强制、打转守卫、掉头台账——它们的接收方都是那台引擎
