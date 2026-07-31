---
name: mmw-approve-design
description: 设计过门。唯一硬人闸。
disable-model-invocation: true
---

只记两件事：已过门这个事实，以及当时认可的文档清单。

## 怎么做

1. 读 `.mmw/task.json`。
2. 列出这次认可的设计文档：主文档 `docs/design/<任务名>/<任务名>.md`，加上它当前引用的原型证据。
3. 写 `design_approved`：

```json
{ "at": "<ISO 8601 时间>", "docs": ["docs/design/<任务名>/<任务名>.md", "..."] }
```

4. 告诉用户过门了，接着可以往下走。

---

## 线下 · 不是技能内容

**为什么不算哈希**：过门记的是「用户在这个时间点认可了这几份」这个事实，不是文档内容的快照。

### 施工单

- **来源**：`plugin/commands/approve-design.md`、`plugin/scripts/steer.sh` 的 approve
- **保留**：过门是用户显式动作，口头同意不算
- **删除**：承重文档指纹与哈希比对；过门即自动切值守档；过门顺带推进阶段与放权

<!-- 方法论正文待填。填之前先读「来源」里的旧文件全文，按保留与删除两列取舍。 -->
