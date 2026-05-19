# Pack 执行 + Review 循环

> **流程位置**：`orchestrate-execution` Steps 4-9 · per-pack 循环 · 通过 → Step 13；needs repair → Step 10

## Step 4：选择 Worker 类型

| Risk flags | Agent | 模型 | TDD |
| --- | --- | --- | --- |
| `trivial`（配置常量 / 文档更新 / 样式调整） | `coding_worker` | gpt-5.3-codex | 宽松（验证通过即可，不强制红-绿循环） |
| `normal` | `coding_worker` | gpt-5.3-codex | 严格 |
| `high-risk` / `production-risk` / `billing` / `permission` / `migration` / `runtime` / `HITL` | `complex_coding_worker` | gpt-5.5 | 严格 |

## Step 5：构造 Pack Brief

读取 `execution-worker-dispatch.md`。Dispatch prompt 必须自足——worker 不读 SKILL.md、不读 references、不读 plan 文件。Coordinator 从 plan 中提取并在 prompt 中写全所有字段。

## Step 6：派发 Worker

```
spawn_agent({
  agent_type: "<coding_worker | complex_coding_worker>",
  description: "Execute Task Pack N.M: <title>",
  prompt: "<Pack Brief>",
  fork_context: true  # Codex 子代理需要继承当前上下文时使用
})
```

**记录返回的 agentId**——后续复杂修复需要用 send_input 继续该 worker。并行 pack 在同一消息中发送多个 spawn_agent call。

## Step 7：接收 Worker 返回

| Worker Verdict | 含义 | Coordinator 动作 |
| --- | --- | --- |
| `pass`（DONE） | 实现完成，全部测试通过 | 进入 Step 8（Pack Review） |
| `needs repair`（DONE_WITH_CONCERNS） | 实现完成但有疑虑 | 读 concerns。正确性/scope concerns → 按 Step 10 修复分流 → 修完进 Pack Review。观察性意见 → 记录，进 Pack Review |
| `needs context` | 缺信息 | send_input 补充上下文给原 worker；补充后继续 |
| `blocked` | 无法完成 | 技术阻塞：拆 pack / 更多上下文 / 换模型。业务阻塞：询问用户 |

**Worker scope drift 检测**：检查 Changed files 是否超出 Owned files。属于当前 scope 其它 pack → 记录不 revert；不属于当前 scope → revert。

## Step 8：派发 Codex Reviewer

读取 `execution-review-dispatch.md`。通过 `code_reviewer` 派发 1 个 baseline reviewer。

**Budget check**：`budget_used + 1 ≤ budget_total`。超预算停止报告用户。

**Direction Check**：达到预算 80% 时触发。重述当前 phase / 剩余 packs / 累计 findings / 是否继续。只决定下一步 owner 和 scope，不写成新审查。

## Step 9：接收 Review Findings + Disposition

**整体 Verdict 前置检查**：如果 reviewer 返回整体 `needs context`（不是某条 finding 的 `needs evidence`），说明 reviewer 无法完成审查。Coordinator 补充 reviewer 所需的上下文后重新 dispatch（budget 消耗 +1），不进入 per-finding disposition。

收到 finding 后，Coordinator 不是传话筒——必须亲验每条 finding 的正确性（读代码、跑测试、对照 source artifacts），然后逐条给 disposition。没有 disposition 的 finding 不能进入 repair。过滤越界建议：out-of-scope 文件不能因为 reviewer 提到就被修改。

| disposition | parent 动作 |
| --- | --- |
| `accepted` | 转成 repair payload；写明 affected artifacts、repair scope、targeted re-review scope |
| `rejected` | 记录反证；不派 repair，不让同一 finding 反复进入 review |
| `needs evidence` | 派 explorer 补证据（窄范围用 `code_explorer`，多模块用 `complex_code_explorer`）；补证前不 repair |
| `duplicate / already covered` | 链到已有 finding、pack、commit、test 或文档；不新增路线 |
| `out of scope` | 从当前 scope 移出；只有用户授权或项目规则要求时才写 durable issue |
| `user decision` | 停止执行，一次只问一个会改变设计、计划或发布策略的问题 |

冲突按 evidence quality 判断，不按 reviewer 数量投票。

**`needs evidence` 补证**：派 `code_explorer`（窄范围单文件/单调用链）或 `complex_code_explorer`（多模块/跨边界）做只读调查。Prompt 包含：finding 待验证、reviewer 主张、Coordinator 存疑点、相关文件。Explorer 返回 confirmed / refuted / partially confirmed 后再给最终 disposition。

**通过** → Step 13（Release Gate）。**Needs repair** → Step 10（读取 `execution-repair-truncation.md`）。
