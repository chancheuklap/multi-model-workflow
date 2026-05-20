# Pack 执行 + Review 循环

> **流程位置**：`orchestrate-execution` Steps 4-9 · per-pack 循环 · 通过 → Step 13；needs repair → Step 10

## Step 4：选择 Worker 类型

| Risk flags | Agent | 模型 | TDD |
| --- | --- | --- | --- |
| `trivial`（配置常量 / 文档更新 / 样式调整） | `pack-executor` | Sonnet | 宽松（验证通过即可，不强制红-绿循环） |
| `normal` | `pack-executor` | Sonnet | 严格 |
| `high-risk` / `production-risk` / `billing` / `permission` / `migration` / `runtime` / `HITL` | `complex-pack-executor` | Opus 4.7 | 严格 |

## Step 5：构造 Pack Brief

### Step 5a：Pre-dispatch Context Transfer（强制）

构造 Pack Brief 之前，Coordinator 必须确认以下内容在上下文中：

1. **Read** 当前 pack 对应的 plan 文件（`docs/orchestrate/plans/<slug>/00N-*.md`）—— 如果上下文中没有该 plan 内容（首个 pack 或经过 compact），必须重新 Read
2. 从该 plan 中**定位当前 pack** 的完整章节，提取所有字段：Goal behavior、Implementation tasks（全文）、Owned files、Read first、Acceptance criteria、Verification commands、Risk flags、Contract anchors、Mockup anchors、Dependencies、Out of scope
3. 读取 `execution-worker-dispatch.md` 获取 Pack Brief 模板

### Step 5b：填充 Pack Brief

**将 Step 5a 提取的内容逐字段填入模板**。关键规则：

- `Implementation tasks` 字段：**完整粘贴** plan 中该 pack 的所有 task 原文（包括 step 编号、文件路径、命令、expected result），不得摘要、不得省略、不得写"见 plan"
- `Goal behavior` 字段：从 plan 中该 pack 的 Goal behavior 完整复制
- `Acceptance criteria` 字段：从 plan 中该 pack 的 Acceptance criteria 完整复制
- `Verification commands` 字段：从 plan 中该 pack 的 Verification commands 完整复制
- 条件字段（Contract anchors / Mockup anchors / Dependencies 等）：plan 中有则复制，无则不写

Dispatch prompt 必须自足——worker 不读 SKILL.md、不读 references、不读 plan 文件。**验证：prompt 中不得出现未替换的 `<>` 占位符、"见 plan"、"参考上文" 等间接引用。**

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
| `pass`（DONE） | 实现完成，全部测试通过 | 进入 Step 7a（Open Items 即时处置）→ Step 8（Pack Review） |
| `needs repair`（DONE_WITH_CONCERNS） | 实现完成但有疑虑 | 读 concerns。正确性/scope concerns → 按 Step 10 修复分流 → 修完进 Step 7a → Pack Review。观察性意见 → 记录，进 Step 7a → Pack Review |
| `needs context` | 缺信息 | SendMessage 补充上下文给原 worker；补充后继续 |
| `blocked` | 无法完成 | 技术阻塞：拆 pack / 更多上下文 / 换模型。业务阻塞：询问用户 |

**Worker scope drift 检测**：检查 Changed files 是否超出 Owned files。属于当前 scope 其它 pack → 记录不 revert；不属于当前 scope → revert。

### Step 7a：Open Items 即时处置

Worker 返回的 `### Open Items` 中包含结构化标记的发现。**Coordinator 必须在进入 Pack Review 之前逐项处置**——不堆积到 Final Review。

对每个标记了 `[out-of-scope]` 或 `[needs-evaluation]` 的条目：

| 标记 | Coordinator 动作 |
| --- | --- |
| `[out-of-scope]` | **立即**开 GitHub issue（Durable Handoff Brief 格式）。先 `gh issue list --search "<关键词>"` 查重 |
| `[needs-evaluation]` | Coordinator 评估：属于当前 scope → 记录到当前或后续 pack 的 repair payload；不属于 → 立即开 GitHub issue |
| `[bug]` | Coordinator 判断严重性：影响当前功能 → 加入当前 pack repair；不影响当前功能 → 立即开 GitHub issue 标记为 bug |
| 无标记的观察性意见 | 记录，不开 issue |

**GitHub Issue 内容格式**（Durable Handoff Brief）：

```
Current behavior:
Desired behavior:
Key interfaces:
Acceptance criteria:
Out of scope:
Risk flags:
Source: Pack <N.M> worker discovery
```

## Step 8：派发 Codex Reviewer

**Read** `execution-review-dispatch.md`，按 `external-review-lanes.md` 定义的方式提交 Codex review 任务。

**Budget check**：`budget_used + 1 ≤ budget_total`。超预算停止报告用户。

**Direction Check**：达到预算 80% 时触发。重述当前 phase / 剩余 packs / 累计 findings / 是否继续。只决定下一步 owner 和 scope，不写成新审查。

## Step 9：接收 Review Findings + Disposition

**整体 Verdict 前置检查**：如果 reviewer 返回整体 `needs context`（不是某条 finding 的 `needs evidence`），说明 reviewer 无法完成审查。Coordinator 补充 reviewer 所需的上下文后重新 dispatch（budget 消耗 +1），不进入 per-finding disposition。

收到 finding 后，Coordinator 不是传话筒——必须亲验每条 finding 的正确性（读代码、跑测试、对照 source artifacts），然后逐条给 disposition。没有 disposition 的 finding 不能进入 repair。过滤越界建议：out-of-scope 文件不能因为 reviewer 提到就被修改。

| disposition | parent 动作 |
| --- | --- |
| `accepted` | 转成 repair payload；写明 affected artifacts、repair scope、targeted re-review scope |
| `rejected` | 记录反证；不派 repair，不让同一 finding 反复进入 review |
| `needs evidence` | 派 explorer 补证据（窄范围用 `code-explorer`，多模块用 `complex-code-explorer`）；补证前不 repair |
| `duplicate / already covered` | 链到已有 finding、pack、commit、test 或文档；不新增路线 |
| `out of scope` | 从当前 scope 移出；**立即**开 GitHub issue（Durable Handoff Brief 格式，先查重） |
| `needs evaluation` | 不在当前 pack 可修范围但需独立评估；**立即**开 GitHub issue，标明评估要点 |
| `user decision` | 停止执行，一次只问一个会改变设计、计划或发布策略的问题 |

冲突按 evidence quality 判断，不按 reviewer 数量投票。

**`needs evidence` 补证**：派 `code-explorer`（窄范围单文件/单调用链）或 `complex-code-explorer`（多模块/跨边界）做只读调查。Prompt 包含：finding 待验证、reviewer 主张、Coordinator 存疑点、相关文件。Explorer 返回 confirmed / refuted / partially confirmed 后再给最终 disposition。

**通过** → Step 13（Release Gate）。**Needs repair** → Step 10（读取 `execution-repair-truncation.md`）。
