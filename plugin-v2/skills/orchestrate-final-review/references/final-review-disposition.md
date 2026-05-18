# Final Review 接收 + Disposition

> **流程位置**：`orchestrate-final-review` Steps 6-8 · 通过 → Step 13（`final-review-completion.md`）；有 accepted findings → Step 9（`final-review-repair.md`）

## Steps 6-7：接收 + Disposition

**整体 Verdict 前置检查**：如果 reviewer 返回整体 `needs context`（不是某条 finding 的 `needs evidence`），说明 reviewer 无法完成审查。Coordinator 补充 reviewer 所需的上下文后重新 dispatch（budget 消耗 +1），不进入 per-finding disposition。

收到 finding 后，Coordinator 不是传话筒——必须亲验每条 finding 的正确性（读代码、跑测试、对照 source artifacts），然后逐条给 disposition。没有 disposition 的 finding 不能进入 repair。过滤越界建议：out-of-scope 文件不能因为 reviewer 提到就被修改。

Final Review 增加一层验证：**对照 pack completion summary**——确认 finding 不是 Pack Review 已验证且 regression sweep 确认 intact 的行为重复。

| disposition | parent 动作 |
| --- | --- |
| `accepted` | 转成 repair / upstream payload；写明 affected artifacts、repair scope、targeted re-review scope |
| `rejected` | 记录反证；不派 repair，不让同一 finding 反复进入 review |
| `needs evidence` | 派 explorer 补证据（窄范围用 `code-explorer`，多模块用 `complex-code-explorer`）；补证前不 repair |
| `duplicate / already covered` | 链到已有 finding、pack、commit、test 或文档；不新增路线 |
| `out of scope` | 从当前 scope 移出；只有用户授权或项目规则要求时才写 durable issue |
| `user decision` | 停止执行，一次只问一个会改变设计、计划或发布策略的问题 |

冲突按 evidence quality 判断，不按 reviewer 数量投票。

**`needs evidence` 补证**：派 `code-explorer`（窄范围单文件/单调用链）或 `complex-code-explorer`（多模块/跨边界）做只读调查。Prompt 包含：finding 待验证、reviewer 主张、Coordinator 存疑点、相关文件。Explorer 返回 confirmed / refuted / partially confirmed 后再给最终 disposition。

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
| architecture friction | `improve-codebase-architecture`（Skill tool） | design doc / plan anchors | 判断影响范围后继续或回流 |

## 路由

- **Review 通过**（全部 finding 为 rejected / out of scope / duplicate，或无 finding）→ Step 13（清扫遗留尾巴）
- **有 accepted finding** → Step 9（读取 `references/final-review-repair.md`）
