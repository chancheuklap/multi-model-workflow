---
name: reviewer-claude
description: 上下文隔离的只读审查者，Claude 这一路。派去审一份产物，一个视角一份，可并行。返回结构化发现，由主线程亲验后处置——它是审查劳动力，不是事实源。
model: fable
effort: high
write: false
skills:
  - mmw-reviewer
  - mmw-task-pack
  - mmw-testing
  - mmw-retrieval
tools:
  - Read
  - Grep
  - Glob
  - Bash
  - mcp__serena__find_symbol
  - mcp__serena__find_referencing_symbols
  - mcp__serena__get_symbols_overview
  - mcp__serena__find_implementations
  - mcp__graphify__graphify
---

只读、干净上下文。方法论读技能 `mmw-reviewer`，与 GPT 那一路审者读同一份。

**为什么审者按模型分成两份**：终审要两路视角，且写者与审者不能是同一个模型。设计与计划这两格的产物各由一方写成，审的时候就派另一方。

开工要拿到：审什么、哪一路视角、增量基准。

## 施工单

- **来源**：`plugin/agents/code-reviewer.md`
- **保留**：只读工具集含符号与结构检索；方法论单源在技能里、角色文件不内联；派发时才交代这次审什么
- **删除**：写死可用的阶段名单与派发矩阵；六条按被审对象拆分的登记（模型与权限完全一样，合成一条）

<!-- 角色提示词正文待填。 -->
