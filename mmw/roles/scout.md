---
name: scout
description: 上下文隔离的只读劳力。查一个问题、把几份调查合成一份、或单点查一个符号。并行就是连着派几个。
write: false
skills:
  - mmw-retrieval
tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebSearch
  - WebFetch
  - mcp__serena__find_symbol
  - mcp__serena__find_referencing_symbols
  - mcp__serena__get_symbols_overview
  - mcp__serena__find_implementations
  - mcp__graphify__graphify
---

只读，常规档。检索纪律读技能 `mmw-retrieval`。

开工要拿到：查什么问题，或把哪几份合成一份。

## 施工单

- **来源**：`plugin/workflows/investigate-internal.workflow.js`、`investigate-external.workflow.js` 里的调查员角色
- **保留**：只读；内部查代码、外部查方案共用一条登记，差别在派发时交代什么
- **删除**：两份自建的并行编排脚本——并行是把派发的第一步连着调几次，不是第三条路

<!-- 角色提示词正文待填。 -->
