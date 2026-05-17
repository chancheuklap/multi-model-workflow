# Design Document Contract

Discovery 输出的设计文档模板。文档是 Phase 0a 输入，不是 implementation plan。

## 模板

```markdown
# <功能 / 问题> 设计文档

## 背景和问题
从用户视角描述当前问题、触发场景和为什么需要解决。

## 目标结果
完成后用户或系统能稳定做到什么。

## 用户场景
actor / action / benefit。覆盖 happy path、失败、空状态、权限不足、重复提交、并发、回滚。

## 业务对象、角色和状态
涉及的对象、owner、writer、reader、verifier、状态、生命周期和关键关系。

## 方案设计
产品行为、系统行为、数据流、UI 状态、接口形状、错误处理。

## 合同边界
涉及 API / Pydantic / DB / JSON / sync / task payload / UI action / helper / billing / permission / runtime 时填写：

- boundary type:
- owner:
- provider:
- consumer:
- Pydantic model / schema_version:
- registry / migration / catalog:
- repository / read model:
- verification:

## 发布风险和人工门禁
涉及 migration / billing / permission / runtime / cross-service / deploy order / rollback / manual gate 时填写：风险面、风险来源、是否需提前 review、Phase B 证据、manual gate owner。

## UI / UX 状态
mockup path、页面、viewport、states、copy、interaction、视觉允许偏差、验证方式。

## 失败场景和异常处理
错误、权限不足、空状态、重复提交、并发、重试、回滚、兼容、降级。

## 测试和验收
外部行为测试、相关模块、既有测试先例、manual gate、visual verification、regression check。

## 不在本次范围
影响执行边界的排除项。

## Open Decisions
无法当前确认但影响后续 plan / implementation 的问题。
```

## 要求

- 使用项目正式术语。
- 不写当前聊天才能理解的句子。
- 不用 TODO / TBD / later / defer 掩盖缺口。
- 不写具体 file path 作为长期实现指令（mockup path、existing module anchor、confirmed contract anchor 除外）。
- 不写 Task Pack、worker 指令或 implementation plan。
