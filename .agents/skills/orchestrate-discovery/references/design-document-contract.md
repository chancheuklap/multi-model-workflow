# Design Document Contract

写 design document 时加载。本文件定义 Orchestrate Discovery 输出的设计文档结构。

## 模板

```markdown
# <功能 / 问题> 设计文档

## 背景和问题

从用户视角描述当前问题、触发场景和为什么需要解决。

## 目标结果

描述完成后用户或系统能稳定做到什么。

## 用户场景 / User Stories

用 actor、action、benefit 描述主要场景。复杂功能要覆盖 happy path、失败、空状态、权限不足、重复提交、并发或回滚。

## 业务对象、角色和状态

列出本设计涉及的对象、owner、writer、reader、verifier、状态、生命周期和关键关系。

## 方案设计

描述产品行为、系统行为、数据流、UI 状态、接口形状、错误处理和 rollout 边界。

## 关键实现决定

记录模块、接口、schema、API、Pydantic、DB、JSON、sync、billing、permission、runtime、helper placement、migration 或架构决定。

## 合同边界

涉及 API / Pydantic / DB / JSON / sync / task payload / UI action / helper 时，写清 owner、provider、consumer、model、schema_version、registry / migration / catalog、repository / read model、verification。

## UI / UX 状态

涉及 UI 时写清 mockup / screenshot / prototype path、页面、viewport、states、copy、interaction、视觉允许偏差和验证方式。

## 失败场景和异常处理

写清错误、权限不足、空状态、重复提交、并发、重试、回滚、兼容或降级。

## 测试和验收决定

写清外部行为测试、相关模块、既有测试先例、manual gate、visual verification 或 regression check。

## 不在本次范围

只写会影响执行边界的排除项，不写大段消极列表。

## Open Decisions

列出无法从代码、文档或当前用户决策中确认，但会影响后续 plan / implementation 的问题。
```

## 要求

- 使用项目正式术语。
- 不写当前聊天才能理解的句子。
- 不使用 TODO / TBD / later / follow-up 掩盖缺口。
- 不写具体 file path 作为长期实现指令，除非它是 mockup、source artifact、existing module anchor 或已确认 contract anchor。
- prototype 代码片段只有在精确表达 state machine、schema、type shape 或 reducer decision 时才可摘录，且必须标注为 decision artifact，不作为生产实现代码。
- 文档是 Phase 0a 输入，不是 implementation plan，不写 Task Pack，不写 worker 指令。
