# Final Review 接收 + Disposition

> **流程位置**：`orchestrate-final-review` Steps 6-8 · 通过 → Step 13（`final-review-completion.md`）；有 accepted findings → Step 9（`final-review-repair.md`）

## Steps 6-7：接收 + Disposition

**整体 Verdict 前置检查**：如果 reviewer 返回整体 `needs context`（不是某条 finding 的 `needs evidence`），说明 reviewer 无法完成审查。Coordinator 补充 reviewer 所需的上下文后重新 dispatch，不进入 per-finding disposition。

**Read** `${MMW_PLUGIN_ROOT}/skills/_shared/disposition-table.md` 并按其 disposition 选项处理 findings。

Final Review 增加一层验证：**对照 plan/pack completion summary**——确认 finding 不是 Plan Implementation Review 已验证且 regression sweep 确认 intact 的行为重复。

`needs evidence` 补证的 explorer 选型 + prompt + 返回契约见上述 disposition-table.md。

## Step 8：Gap 分类

Accepted findings 按影响范围分类，决定修复路由：

| Gap 类型 | 含义 | 路由 |
| --- | --- | --- |
| **Implementation Gap** | 设计合理，代码没做到 | 修复分流（Step 9）或回 orchestrate-execution targeted repair |
| **Design Gap** | 设计承诺不可实现或遗漏约束 | user decision / orchestrate-discovery 写回 design doc |
| **Context Gap** | 需要术语 / owner / UI target 确认 | orchestrate-discovery 补充 → 写回 |
| **Plan Gap** | plan 与实际代码不一致、plan 遗漏 | orchestrate-plan-writing 修订模式 |
| **Unverifiable** | 环境 / 账号 / 生产 gate 缺失 | 写清已验证证据和 manual gate owner，不算 blocker |

## Backflow 路由

把问题推回正确的上游 skill 处理。调用前给出 Scope、source artifacts、允许输出和写回目标。结论必须写回后再继续。

| 问题类型 | Upstream Skill | 写回目标 | 返回 verdict |
| --- | --- | --- | --- |
| implementation gap（小，≤ 2 pack 少量文件） | 当前 skill 内修复 | N/A | 继续 |
| implementation gap（大，涉及多 pack） | orchestrate-execution re-entry | pack commits | `NEEDS_EXECUTION` |
| design / context gap | orchestrate-discovery | design document | `NEEDS_DISCOVERY` |
| plan gap | orchestrate-plan-writing（修订模式） | plan document | `NEEDS_PLAN_REVISION` |
| architecture friction | `加载 skill `improve-codebase-architecture`` | design doc / plan anchors | 判断影响范围后继续或回流 |

## 路由

- **Review 通过**（全部 finding 为 rejected / out of scope / duplicate，或无 finding）→ Step 13（清扫遗留尾巴）
- **有 accepted finding** → Step 9（读取 `references/final-review-repair.md`）

---
> **下一步**：Review 通过 → Step 13（`final-review-completion.md`）。有 accepted finding → Step 9（`final-review-repair.md`）。
