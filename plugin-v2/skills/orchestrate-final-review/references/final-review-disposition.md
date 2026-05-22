# Final Review 接收 + Disposition

> **流程位置**：`orchestrate-final-review` Steps 6-8 · 通过 → Step 13（`final-review-completion.md`）；有 accepted findings → Step 9（`final-review-repair.md`）

## Steps 6-7：接收 + Disposition

**整体 Verdict 前置检查**：如果 reviewer 返回整体 `needs context`（不是某条 finding 的 `needs evidence`），说明 reviewer 无法完成审查。Coordinator 补充 reviewer 所需的上下文后重新 dispatch，不进入 per-finding disposition。

<!-- BEGIN: disposition-table -->
**Coordinator 亲验纪律** (disposition 之前的必经步骤):

收到 reviewer findings 后**禁止直接转发给 worker**。逐条执行：
1. 亲验：用 Read / grep / 对照设计文档验证 finding 的事实主张
2. Disposition：accepted / rejected / needs evidence / out of scope（调用 state.sh disposition append）
3. 修复指令：只把 accepted findings 翻译为具体修复指令传给 worker。Reviewer 原始输出不传

**Confidence 校准** (Codex 返回 confidence 1-10):

| Confidence | Coordinator 默认动作 | 覆写条件 |
| --- | --- | --- |
| 8-10 (high) | 直接亲验，通常 accept 或 reject | Coordinator 找到反向证据 |
| 5-7 (medium) | 亲验 + 派 code-explorer 补证 -> 再定 disposition | -- |
| 1-4 (low) | 默认 suppress -> 记录为 "suppressed: low confidence" | Coordinator 手动升级并附证据 |

**Disposition 审计写入** (每条 finding 决定后立即调用):

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/state.sh" disposition append \
  --run-id "<run_id>" --review-round <r> --finding-id <id> \
  --disposition <accepted|rejected|suppress|path-a|path-b> \
  --confidence <1-10> --severity <H|M|L> \
  --evidence "<一行理由>" --path "<file:line>"
```

`--evidence` 对 `--disposition accepted` 必填且非空。

**Disposition 表**:

| disposition | Coordinator 动作 |
| --- | --- |
| `accepted` | 转成 repair payload；写明 affected artifacts、repair scope、targeted re-review scope |
| `rejected` | 记录反证；不派 repair |
| `needs evidence` | 派 explorer 补证据 |
| `duplicate / already covered` | 链到已有 finding |
| `out of scope` | 开 GitHub issue（Durable Handoff Brief） |
| `needs evaluation` | 开 GitHub issue |
| `user decision` | 停止执行，一次只问一个决策问题 |

冲突按 evidence quality 判断，不按 reviewer 数量投票。

**Path A re-review 规则** (仅 confidence >= 7 的 accepted findings):
- Coordinator Path A 直接修复 -> 强制 targeted Codex re-review
- Codex 返回 `needs_repair` -> 必须升级 Path B 派 worker
- 用 `state.sh path-a-escalation start/update/clear` 追踪
<!-- END: disposition-table -->

Final Review 增加一层验证：**对照 plan/pack completion summary**——确认 finding 不是 Plan Implementation Review 已验证且 regression sweep 确认 intact 的行为重复。

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
| architecture friction | `Skill({ skill: "improve-codebase-architecture" })` | design doc / plan anchors | 判断影响范围后继续或回流 |

## 路由

- **Review 通过**（全部 finding 为 rejected / out of scope / duplicate，或无 finding）→ Step 13（清扫遗留尾巴）
- **有 accepted finding** → Step 9（读取 `references/final-review-repair.md`）

---
> **下一步**：Review 通过 → Step 13（`final-review-completion.md`）。有 accepted finding → Step 9（`final-review-repair.md`）。
