# Plan 正文怎么写

一张 ticket 对应一份 plan，由一个 `worker` 从头到尾顺序读取整份 plan。

## 模板

```markdown
---
ticket: <tracer bullet ticket 的 GitHub issue 编号>
artifact_refs: []
---

# Plan: <ticket 标题>

**Goal:** <这张 ticket 完成后的可观察结果>
**Source spec:** <spec 路径>
**Source ticket:** <tracker 编号或标识>
**Prototype source:** <有则写资产目录、用户选中版本和逐轮记录；没有则省略>
**Research source:** <有则写 research 索引和当前 ticket 使用的精确文件；没有则省略>

## Constraints

只写会约束本 ticket 实现的项目规则、spec 决定和范围边界。每条附来源。

## Current State

只在修改既有行为时写。列出实施路线依赖的当前行为和 `文件:行号`。

## Change Map

| 路径 | 动作 | 职责 |
| --- | --- | --- |
| `path` | Create / Modify / Test / Docs·登记·迁移 | 这个文件为本 ticket 承担什么 |

## Contracts and Seams

- **Test seam:** <照抄 spec 已确认的 seam，并说明验证什么行为>
- **Consumes / Produces:** <只有跨 plan 接口存在时写归属方、提供方、消费方和已确定的字段或签名>
- **Migration / Registry:** <只有涉及时写>

## Implementation

1. **<可观察检查点>**
   - Change: <改什么行为>
   - Files: <路径和职责>
   - Verify: `<command>` → <预期结果>

## Acceptance

| Ticket 验收 | 证明方式 | 命令或人工结果 |
| --- | --- | --- |
| <原验收项> | <测试、产物或可观察行为> | `<command>` → <预期结果> |

## Browser Acceptance

<只有界面 ticket 才写页面、路径、状态、viewport 和可见结果。>
自动回归和人工浏览器审批分两栏写，不要混。`Verification commands` 只写能重复执行、带预期结果的测试命令；本节只写人工审批——由主 agent 在浏览器里逐项看的页面、黄金路径、本次相关状态、viewport 和每项可见结果。**两边不能互相冒充**：Playwright CLI 跑出来的不算人工走查，人在浏览器里点出来的也不算自动回归。没有界面就写「不适用」。

## Rollback and Gates

<只有涉及数据、基础设施、计费、权限、共享状态或人工审批时才写。>
```

## 写作规则

- 实施步骤按真实依赖排序。一个步骤对应一个可观察检查点，不设固定分钟数和步骤数。
- plan 只固定已经谈定的行为、合同和风险边界。`worker` 可以在这些边界内选择局部实现。
- 默认不写实现代码。只有公开合同、数据形状或关键算法无法用文字准确表达时才写完整代码片段。
- 不重复 spec 全文。`Constraints` 只保留影响本 ticket 的内容，并写明来源。
- 不重复测试方法论。`Acceptance` 只说明每条验收如何证明；测试组织和 red-green 循环由 `$mmw:mmw-tdd` 与目标仓库 `TESTING.md` 决定。
- prototype 存在时，只把用户确认过的决定写入当前路线。保留资产路径和逐轮记录出处。
- research 存在时，只引用当前 ticket 使用的索引和精确文件。保留适用的范围快照与未查清项。
- 没有对应风险的可选小节直接省略，不写成一排「不适用」。
- 发现未决的目标、合同、数据形状、文案、权限或计费决定时交 `needs-context`，不写占位符。
