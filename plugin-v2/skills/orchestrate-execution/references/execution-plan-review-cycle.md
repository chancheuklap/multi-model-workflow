# Plan 执行 + Review 循环

> **流程位置**：`orchestrate-execution` Steps 4-9 · per-plan 循环 · 通过 → Step 13；needs repair → Step 10

## FOR EACH Plan（按 Blocked by 排序）

### Steps 4-7c：Pack 执行循环（per pack within current Plan）

#### Step 4：选择 Worker 类型

| Risk flags | Agent | 模型 | TDD |
| --- | --- | --- | --- |
| `trivial`（配置常量 / 文档更新 / 样式调整） | `pack-executor` | Sonnet | 宽松（验证通过即可，不强制红-绿循环） |
| `normal` | `pack-executor` | Sonnet | 严格 |
| `high-risk` / `production-risk` / `billing` / `permission` / `migration` / `runtime` / `HITL` | `complex-pack-executor` | Opus 4.7 | 严格 |

#### Step 5：构造 Pack Brief

##### Step 5a：Pre-dispatch Context Transfer（强制）

构造 Pack Brief 之前，Coordinator 必须确认以下内容在上下文中：

1. **Read** 当前 pack 对应的 plan 文件（`docs/orchestrate/plans/<slug>/00N-*.md`）—— 如果上下文中没有该 plan 内容（首个 pack 或经过 compact），必须重新 Read
2. 从该 plan 中**定位当前 pack** 的完整章节，提取所有字段：Goal behavior、Implementation tasks（全文）、Owned files、Read first、Acceptance criteria、Verification commands、Risk flags、Contract anchors、Mockup anchors、Dependencies、Out of scope
3. 读取 `execution-worker-dispatch.md` 获取 Pack Brief 模板

##### Step 5b：填充 Pack Brief

**将 Step 5a 提取的内容逐字段填入模板**。关键规则：

- `Implementation tasks` 字段：**完整粘贴** plan 中该 pack 的所有 task 原文（包括 step 编号、文件路径、命令、expected result），不得摘要、不得省略、不得写"见 plan"
- `Goal behavior` 字段：从 plan 中该 pack 的 Goal behavior 完整复制
- `Acceptance criteria` 字段：从 plan 中该 pack 的 Acceptance criteria 完整复制
- `Verification commands` 字段：从 plan 中该 pack 的 Verification commands 完整复制
- `Context hint` 字段：填入当前 Plan 中所有 Pack 编号（"Your code will be reviewed alongside packs N.1..N.M within Plan N"）
- 条件字段（Contract anchors / Mockup anchors / Dependencies 等）：plan 中有则复制，无则不写

Dispatch prompt 必须自足——worker 不读 SKILL.md、不读 references、不读 plan 文件。**验证：prompt 中不得出现未替换的 `<>` 占位符、"见 plan"、"参考上文" 等间接引用。**

#### Step 6：派发 Worker

```
Agent({
  subagent_type: "<pack-executor | complex-pack-executor>",
  description: "Execute Task Pack N.M: <title>",
  prompt: "<Pack Brief>",
  isolation: "worktree"  // 仅并行 pack 使用
})
```

`validate-pack-dispatch.sh` hook 自动拦截缺少 `start_commit` 或 Pack 状态非 `pending` 的 dispatch。

**记录返回的 agentId**——后续复杂修复需要用 SendMessage 继续该 worker。并行 pack 在同一消息中发送多个 Agent tool call。

Coordinator 写入 execution state：`packs[N.M].status = dispatched`。

#### Step 7：接收 Worker 返回

`agent-return-handler.sh`（PostToolUse Agent hook）自动从 Worker 的 dispatch prompt 提取 Pack ID，读取 `pack-returns/<run_id>/<pack-id>.json`（或从 `tool_response` 解析 verdict 作为 fallback），更新 execution state（`status = returned`、`worker_verdict`），并通过 `additionalContext` 输出 `NEXT` 指令告知 Coordinator 下一步。非 execution 路线（无 execution-state 文件）静默放行。

| Worker Verdict | 含义 | Coordinator 动作 |
| --- | --- | --- |
| `pass`（DONE） | 实现完成，全部测试通过 | 进入 Step 7a（Open Items 即时处置）→ Step 7b（Git Checkpoint）→ 下一个 Pack |
| `needs repair`（DONE_WITH_CONCERNS） | 实现完成但有疑虑 | 读 concerns。正确性/scope concerns → 按 Step 10 修复分流 → 修完进 Step 7a → Git Checkpoint。观察性意见 → 记录，进 Step 7a → Git Checkpoint |
| `needs context` | 缺信息 | SendMessage 补充上下文给原 worker；补充后继续 |
| `blocked` | 无法完成 | **Intra-Plan Blocker**：写入 `packs[N.M].status = blocked` + `plans[N].status = blocked` → 整个 Plan 停止，不继续后续 Pack → 返回 `BLOCKED` |

**Worker scope drift 检测**：检查 Changed files 是否超出 Owned files。属于当前 scope 其它 pack → 记录不 revert；不属于当前 scope → revert。

##### Step 7a：Open Items 即时处置

Worker 返回的 `### Open Items` 中包含结构化标记的发现。**Coordinator 必须在 Git Checkpoint 之前逐项处置**——不堆积到 Final Review。

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

##### Step 7b：Git Checkpoint（per-pack）

1. `git add <owned files + test files + plan doc>`
2. `git commit -m "Pack N.M: <title> — <summary of behavior>"`（`enforce-pack-commit.sh` hook 自动校验格式）
3. `track-execution-state.sh` hook 自动更新 `packs[N.M].status = committed` + `commit_sha` + `plans[N].end_commit`

**规则**：Worker 不 commit；Coordinator 统一提交。不 stage 非当前 scope 文件。

##### Step 7c：合并并行 Pack 的 Worktree

并行 pack 各自完成 Open Items + Git Checkpoint 后，按依赖顺序逐个合并：

1. 确定合并顺序（按 plan 中的 dependencies）
2. `git merge <worktree-branch> --no-ff`
3. 冲突处理：简单 → Coordinator 直接解决；复杂 → 新建 targeted-repair agent
4. 每次 merge 后跑完整测试
5. 全部 merge 完后再跑一次确认集成正确

**合并策略铁律**：只用 `git merge --no-ff`，**绝对禁止 squash merge（`--squash`）和 rebase（`--rebase`）**。

**不并行合并**——串行避免 merge conflict 级联。

---

### Step 8：Plan Implementation Review（所有 Pack 完成后）

当 `track-execution-state.sh` 输出 `NEXT: All N packs in Plan XXX committed` 时（PostToolUse Bash hook，在最后一个 Pack commit 后触发），所有 Pack 已完成。

**Read** `execution-review-dispatch.md`，按其中的 Codex review 派发步骤提交 Plan Implementation Review。

Coordinator 写入 execution state：`plans[N].status = review_pending`。

### Step 9：接收 Review Findings + Disposition

**整体 Verdict 前置检查**：如果 reviewer 返回整体 `needs context`（不是某条 finding 的 `needs evidence`），说明 reviewer 无法完成审查。Coordinator 补充 reviewer 所需的上下文后重新 dispatch，不进入 per-finding disposition。

收到 finding 后，Coordinator 不是传话筒——必须亲验每条 finding 的正确性（读代码、跑测试、对照 source artifacts），然后逐条给 disposition。没有 disposition 的 finding 不能进入 repair。过滤越界建议：out-of-scope 文件不能因为 reviewer 提到就被修改。

| disposition | Coordinator 动作 |
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

Coordinator 写入 execution state：`plans[N].review_verdict = pass/needs repair`、`plans[N].status` 更新。

**通过** → Step 13（Release Gate）。**Needs repair** → Step 10（读取 `execution-repair-truncation.md`）。
