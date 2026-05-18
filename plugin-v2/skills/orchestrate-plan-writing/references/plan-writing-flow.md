# Plan 写作流程

plan-writer agent 被派发后按此流程执行。

## 步骤

1. **读取 source design**——提取 goal、architecture、tech stack、行为清单、合同边界、失败场景。
2. **读取 issue hierarchy**——确认 large issues 和 small issues 完整，每个 small issue 可独立验证。映射不成立时返回 needs context（见下方路由表）。
3. **探索代码库**——用 `rg` / `find` / `improve-codebase-architecture` 验证 source design 涉及的路径、模块、合同面、已有模式。
4. **读取 `references/plan-contract.md`**——确认 issue→pack 映射成立，按模板写 Plan Header、Scope Check、Source Coverage Map、File/Responsibility Map、发布风险表、每个 Task Pack。
5. **读取 `references/plan-checklist.md`**——做过度设计 / 设计不足 / coverage 自审，修正。
6. **保存**——写入 dispatch prompt 指定的路径。

## 映射不成立时

| 状况 | 返回 |
| --- | --- |
| 缺 large / small issue | needs context："缺 issue hierarchy，需要 to-issues" |
| small issue 不可独立验证 | needs context："issue 粒度不足，建议用 to-issues 继续拆" |
| 术语 / 验收不清 | needs context："业务意图不清，需要 discovery" |
| scope 应拆多个 plan | needs context："scope 过大，应拆分 plan" |
| 架构假设与代码现实不符 | needs context：具体说明哪个假设不成立 |

不自创 issue 或把建议拆分当正式 Task Pack。

## 修订流程（Mode 2）

收到 Phase 0b plan review findings 后：

1. 读完所有 findings。
2. 按优先级修订：结构性问题 → 内容缺失 → 精度问题。
3. 重跑 `references/plan-checklist.md` 自审。
4. 保存修订后的 plan。
5. 返回修订摘要。

如果 finding 不正确，说明技术原因推回。
