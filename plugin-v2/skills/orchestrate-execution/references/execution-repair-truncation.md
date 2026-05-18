# 修复分流 + Targeted Re-Review + 截断

## Step 10：修复路由（三条路径）

所有 repair prompt 只携带 accepted findings，不夹带 rejected / out-of-scope / low-confidence observations。

### 路径 A：Coordinator 直接修复

**条件**：≤ 2 文件、不触碰合同边界、不需新增测试、意图明确。

1. Coordinator 读 diff、理解 finding
2. 直接修改代码
3. 跑 verification commands 确认修复
4. 进入 Step 11（Targeted Re-Review）

### 路径 B：SendMessage 给原 Worker

**条件**：多文件、需要代码上下文、需要新增/修改测试、但根因已知。

1. 检查 SendMessage 是否可用（`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`）
2. 可用 → SendMessage 给 saved agentId，附 accepted findings
3. 不可用 → 新建同类 agent，prompt 含 accepted findings + pack brief subset + git diff scope
4. Worker 修复后返回 → 进入 Step 11

### 路径 C：Complex-Code-Explorer 调查

**条件**：根因不明——reviewer 指出症状但无法确定原因。

1. 新建 `complex-code-explorer`，prompt 含症状描述 + 相关文件 + 调查方向
2. Explorer 返回只读调查结果（不修代码）
3. 根据调查结果选择路径 A 或 B 继续修复

### 修复归属快速判定

| 信号 | 路径 |
| --- | --- |
| "这行该返回 X 而不是 Y" + ≤ 2 文件 | A（Coordinator 直接修） |
| "缺 migration / 缺 consumer 同步 / 测试不覆盖" | B（Worker 修） |
| "行为异常但不清楚为什么" | C（Explorer 查） |
| accepted finding 涉及 migration / billing / permission / runtime / shared contract | B（用 complex-pack-executor） |

## Step 11：Targeted Re-Review

修复完成后，只重审 accepted findings 涉及的变更部分。不做 full review rerun。

派发方式同 Step 8（读取 `execution-dispatch-templates.md`），但 scope 缩小到：
- changed files（修复涉及的文件）
- accepted findings（原 finding 是否解决）
- 受影响 angle（spec / quality / contract / risk 中与修复相关的）

## Step 12：修复预算 + 截断

每个 pack 最多 **2 Worker repair round + 1 root-cause-analyst round = 3 repair round**。全局 review budget 优先。

| Round | 动作 |
| --- | --- |
| Round 1 | 路径 A/B/C 修复 → Targeted Re-Review |
| Round 2 | 仍 needs repair → 路径 A/B/C 修复 → Targeted Re-Review |
| Round 3（截断） | 仍 needs repair → 新建 `root-cause-analyst`（读取 `execution-dispatch-templates.md` RCA 模板） |

**Analyst Resolution 路由**：`fixed` → Targeted Re-Review（Round 3） / `root cause found, not fixed` → 重新 dispatch worker（Round 3） / `root cause in design/plan` → 写回 → orchestrate-discovery 或 orchestrate-plan-writing / `unable to reproduce` → 报告用户 / `unable to determine` → BLOCKED。

Round 3 Targeted Re-Review 仍 needs repair → BLOCKED，报告用户。
