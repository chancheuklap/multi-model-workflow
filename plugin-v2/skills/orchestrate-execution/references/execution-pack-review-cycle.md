# Pack 执行 + Review 循环

> **流程位置**：`orchestrate-execution` Steps 4-9 · per-pack 循环 · 通过 → Step 13；needs repair → Step 10

## Step 4：选择 Worker 类型

| Risk flags | Agent | 模型 |
| --- | --- | --- |
| `normal` | `pack-executor` | Sonnet |
| `high-risk` / `production-risk` / `billing` / `permission` / `migration` / `runtime` / `HITL` | `complex-pack-executor` | Opus 4.7 |

## Step 5：构造 Pack Brief

读取 `execution-worker-dispatch.md`。Dispatch prompt 必须自足——worker 不读 SKILL.md、不读 references、不读 plan 文件。Coordinator 从 plan 中提取并在 prompt 中写全所有字段。

## Step 6：派发 Worker

```
Agent({
  subagent_type: "<pack-executor | complex-pack-executor>",
  description: "Execute Task Pack N.M: <title>",
  prompt: "<Pack Brief>",
  isolation: "worktree"  // 仅并行 pack 使用
})
```

**记录返回的 agentId**——后续复杂修复需要用 SendMessage 继续该 worker。并行 pack 在同一消息中发送多个 Agent tool call。

## Step 7：接收 Worker 返回

| Worker Verdict | 含义 | Coordinator 动作 |
| --- | --- | --- |
| `pass`（DONE） | 实现完成，全部测试通过 | 进入 Step 8（Pack Review） |
| `needs repair`（DONE_WITH_CONCERNS） | 实现完成但有疑虑 | 读 concerns。正确性/scope concerns → 按 Step 10 修复分流 → 修完进 Pack Review。观察性意见 → 记录，进 Pack Review |
| `needs context` | 缺信息 | SendMessage 补充上下文给原 worker；补充后继续 |
| `blocked` | 无法完成 | 技术阻塞：拆 pack / 更多上下文 / 换模型。业务阻塞：询问用户 |

**Worker scope drift 检测**：检查 Changed files 是否超出 Owned files。属于当前 scope 其它 pack → 记录不 revert；不属于当前 scope → revert。

## Step 8：派发 Codex Reviewer

读取 `execution-review-dispatch.md`。通过 `codex:codex-rescue --model gpt-5.4` 派发 1 个 baseline reviewer。

**Budget check**：`budget_used + 1 ≤ budget_total`。80% 触发 Direction Check。超预算停止报告用户。

## Step 9：接收 Review Findings + Disposition

**Coordinator 不是传话筒**——亲验每条 finding（读代码、跑测试、对照 source artifacts）。

| Disposition | 动作 |
| --- | --- |
| `accepted` | 转成 repair payload；写明 affected artifacts、repair scope、targeted re-review scope |
| `rejected` | 记录反证；不 repair |
| `needs evidence` | 派 `code-explorer` / `complex-code-explorer` 补证据；补证前不 repair |
| `duplicate / already covered` | 链到已有 finding / pack / commit / test |
| `out of scope` | 从当前 scope 移出；只有用户授权时才写 durable issue |
| `user decision` | 停止执行，一次只问一个问题 |

冲突按 evidence quality 判断，不按 reviewer 数量投票。

**通过** → Step 13（Release Gate）。**Needs repair** → Step 10（读取 `execution-repair-truncation.md`）。
