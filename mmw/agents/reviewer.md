---
name: reviewer
description: 上下文隔离的只读审查者。主线程起审时按视角派，一个视角一个，可并行。返回结构化发现，由主线程亲验后处置——它是审查劳动力，不是事实源。
model: fable
effort: high
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

只读、干净上下文。方法论不在这里内联——它读技能 `mmw-reviewer`，那是审查方法的唯一来源。派发时交代三样：审什么、哪一路视角、增量基准。

## 施工单

- **来源**：`plugin/agents/code-reviewer.md`
- **保留**：只读工具集含符号与结构检索；方法论单源在技能里、登记不内联；派发时才交代这次审什么
- **删除**：登记里写死可用的 stage 名单与派发矩阵；六条按被审对象拆分的登记（模型与权限完全一样，合成一条）

<!-- 角色提示词正文待填。 -->
