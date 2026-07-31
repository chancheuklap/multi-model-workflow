---
name: mmw
description: 报当前任务现状。新会话接续、想知道上次停在哪时用。
---

合读状态文件、阶段产物、提交流水，报一遍现状。

## 怎么做

1. 从当前目录往上找 `.mmw/task.json`。找不到就说不在任务里，提示用 `/mmw-start <需求>` 开一个，到此为止。
2. 读那五个字段。
3. 按产物路径约定看盘：设计文件夹 `docs/design/<任务名>/`，切片 `docs/issues/<任务名>/`，计划 `docs/plans/<任务名>/`，审查留痕 `.mmw/reviews/`。哪些存在、最后改动时间。
4. `git -C <工作树> log --oneline <base>..HEAD` 看这个任务落了什么。
5. 报给用户三样：在哪个阶段、产物说到哪、上次为什么停（`note` 原样念出来）。然后读那个阶段的技能（`mmw-<阶段键>`，收尾读 `mmw-done`）接着干。

凭盘上的东西报，不读会话记忆，盘上没有的不猜。

---

## 线下 · 不是技能内容

### 施工单

- **来源**：`plugin/commands/progress.md`、`plugin/commands/reassess.md`、`plugin/scripts/progress.sh`、`flow.sh` 的 where
- **保留**：读盘不读记忆；报「在哪一格 / 产物说到哪 / 上次为什么停」三样
- **删除**：进度板渲染器与它的投影层；where 的 load/do/then 指令面——不再由引擎指路

<!-- 方法论正文待填。填之前先读「来源」里的旧文件全文，按保留与删除两列取舍。 -->
