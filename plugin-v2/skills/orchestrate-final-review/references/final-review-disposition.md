# Final Review 接收 + Disposition

## Step 6：接收 Review Findings

**Coordinator 不是传话筒**——必须主动验证每条 finding：

1. **读代码**：检查 reviewer 说的是否与代码事实一致
2. **跑测试**：reviewer 说测试不覆盖 → 跑一下确认
3. **对照 source artifacts**：reviewer 说 spec 不符 → 对照 design document 和 plan 确认
4. **对照 pack completion summary**：确认 finding 不是 Pack Review 已验证且 regression sweep 确认 intact 的行为重复
5. **用自己的判断力质疑和确认**：不因为 reviewer 说了就当真，也不因为 worker 说通过就放行

## Step 7：逐条 Disposition

| Disposition | Coordinator 动作 |
| --- | --- |
| `accepted` | 转成 repair payload；写明 affected artifacts、repair scope、targeted re-review scope |
| `rejected` | 记录反证；不 repair，不让同一 finding 反复进入 review |
| `needs evidence` | 派 `code-explorer` / `complex-code-explorer` 补证据；补证前不 repair |
| `duplicate / already covered` | 链到已有 finding / pack / commit / test；不新增路线 |
| `out of scope` | 从当前 scope 移出；只有用户授权或项目规则要求时才写 durable issue |
| `user decision` | 停止执行，一次只问一个会改变设计/计划/发布策略的问题 |

冲突按 evidence quality 判断，不按 reviewer 数量投票。

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
