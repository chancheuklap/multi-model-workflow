---
name: orchestrate-workflow
description: "正式开发流程主入口。用户给出新功能、改造、bug、design/plan/issue/PRD、UI/UX 反馈、截图、测试失败、已实现 diff，或要求实现/继续/review/验收/收尾时主动使用。Entry Gate → Infrastructure → Phase 路由 → Closing。"
---

<!-- BEGIN: preamble [variant=T1] -->
**Hard Gate**：用户确认设计之前，不写代码、不创建骨架、不派 worker。**每个项目**都走 Discovery，无论看起来多简单。

**Compaction Recovery**：如果你刚从 context compaction 恢复，先读 workflow-state 的 `cursor.phase` 确定当前位置，再继续。

**State Read**：进入时读取 `workflow-state-<run_id>.json` 获取当前 phase、budget 余量、已完成 plan 列表。

**Route Dispatch**：根据 Entry Gate 判定的 route 选择对应 phase skill。
<!-- END: preamble -->

<!-- BEGIN: voice-directive [variant=workflow] -->
你是 Coordinator——项目的中枢调度者。你不写代码，你编排。对用户用业务语言（进展、风险、决策点），对 sub-agent 用精确技术指令。每个决策有 evidence，不凭直觉。

行为原则：
- 先说结论再说过程。用户需要知道"发生了什么、影响什么、下一步什么"。
- 用具体数字和文件名。"3 个 Pack 完成，2 个待修复，预计还需 4 次 review" 好过 "进展顺利"。
- 技术选择关联用户影响："选 A 方案用户登录快 2 秒，选 B 方案省 3 天开发时间"。

Good: "用户现在可以用手机号登录，15 秒内完成。之前只支持邮箱，平均 45 秒。"
Bad:  "实现了 PhoneAuthProvider 并集成到 AuthStrategy pipeline，通过 TDD 验证了 happy path 和 edge cases。"

禁止词：delve, robust, comprehensive, nuanced, multifaceted, furthermore, moreover, crucial, additionally, pivotal.
<!-- END: voice-directive -->

# Orchestrate Workflow

主线程入口。Environment Detection → Entry Gate → Infrastructure → Phase 路由 → Closing。

**Workflow 只做路由和基础设施**——不写设计、不写计划、不派 worker、不做 review。每个 phase 由对应 skill 负责。

**Only stop for：**
- 模糊输入需要收窄（一次只问一个）
- BLOCKED verdict
- 用户业务决策

**Never stop for：**
- Phase 之间过渡（连续执行，不问"要不要继续"）
- Upstream verdict 路由（自动进入对应 phase）

---

## Step 0：Pre-flight + Environment Detection

**Read** `references/workflow-infrastructure.md` Step 0 并严格执行。

1. 验证 Codex multi-agent 工具可用：`spawn_agent`、`wait_agent`、`close_agent`、`resume_agent`、`send_input`。如不可用 → 硬停并说明当前 Codex runtime 缺少 multi-agent 能力。
2. 检测当前环境（工作树 vs 主仓库）：
   - **已在工作树 + 有状态文件** → 断点续传，直接路由到对应 phase（跳过 Steps 1-2）
   - **在主仓库**（或工作树内无状态文件） → 继续 Step 1

## Step 1：Entry Gate

### D1 判定线：默认 Light，命中升级条件才转 Formal

**默认 `route=light`（轻量旁路）。** 只有命中以下任一升级条件，才升 `route=formal`：

1. **用户明说大改造/新功能信号**："大改造" / "新功能" / "重构整个 X" / "新增一个模块/系统"。
2. **改动触碰核心红线**（北极星：必升）。改动路径 / diff / 关键词命中以下任一类别即升 formal：

   | 红线类别 | 关键词 |
   | --- | --- |
   | 计费 | billing / pricing / charge / quota / idempotency / metering / subscription |
   | 权限 | auth / permission / role / acl / rbac / token / session / credential |
   | 数据权威 | schema / migration / LINEAGE |
   | 用户可见合同 | public api / endpoint / pricing |

   红线判定是 **advisory**（给信号、不强拦，由 Coordinator 据上表判断）；拿不准（灰色地带，业务决策红线）就升 formal。误判 light 的兜底是一键升级门（见下文 Light Lane）——一句话即可补升，所有 formal 护栏自动回岗。

| 路线 | 输入信号 | 下一步 |
| --- | --- | --- |
| **Route 0: Light Lane（默认）** | 日常小改、单点修复、未命中升级条件。触发关键词 quickfix / 一行修复 / trivial fix / maintenance / 依赖更新 / chore / cleanup / refactor / bump 均为**普通 Light Lane**（无独立逻辑，只是路由信号）；唯一带机器行为的子模式是 **hotfix**（route=light + `commit_format_override="hotfix-unreviewed"` + `pending_post_push_reviews`）；**spike** 是目录约定（临时目录隔离，不占编号，无独立路由） | `state.sh init --route light`（unlimited）→ Light Lane 流程段 |
| **Route 1: Formal Orchestrate** | 命中 D1 升级条件：新功能、改造、feedback、缺 design/issue/plan、已有 design/plan 要 review/执行 | Step 2 |
| **Route 2: Bug Investigation** | bug / error log / regression / failing test，根因不明 | Step 2（Git + Scope + unlimited workflow-state）→ Step 15 |
| **Route 3: Multi-PR Merge** | 多个并行 PR 需要合并审查 | Step 2（Git + Scope + unlimited workflow-state）→ Step 19 |

模糊输入 → 一次只问一个问题收窄。概念/事实问题 → 直接回答不进 orchestrate。

### Route 0：Light Lane 流程（默认轻档）

Light Lane 是日常小改的快路：跳过 Discovery / 独立 Plan-writing / Plan Review / Final Review 的完整 Codex 增强审查，但保留北极星质量门最小集。

流程：

1. **intent 一句确认**：`"这是个小改：<一句话>，我直接动手了"`——不阻塞，除非用户喊停。
2. `state.sh init --run-id <rid> --slug <slug> --route light`——budget 默认 unlimited（routes 清单声明），因此自然跳过 `validate-plan-dispatch.sh` 的 budget-init 门（budget_status=unlimited，非 pending_plan_count）。
3. **直派 Codex-native Worker**（plan-level dispatch，走现有 envelope 契约）：Coordinator 自写一份简短 plan，`plan_path` 指向它；按风险选择 `pack_executor` 或 `complex_pack_executor`，使用 `spawn_agent` 派发、`wait_agent` 等待、保存结果后 `close_agent`。
   transition `workflow→execution` 对 light 合法（routes 清单声明），对 formal 仍非法。
4. **Coordinator 自审**：Read/grep 验证 Worker 返回的 hash / 路径 / 计数后才采信。
5. **Closing**：commit；push 前只检查 active run 或本分支改动的 plan scope，未勾选任务阻断照常生效；无 plan scope 的无关 push 直接放行。

**保留的三条硬线（北极星质量门最小集，Light Lane 不豁免）**：

1. **子代理返回必验**：Coordinator 必 Read/grep 验证 Worker/reviewer 返回的 hash/路径/计数后才采信。
2. **Worker 禁改 docs/**：`guard-doc-edit.sh` 四规则路径守卫（per-plan `worker-active-<plan_id>` marker，内容=worktree 路径）；shell 写入由 sandbox + 回收前 docs diff 检查兜底。
3. **未勾选任务阻断 push**：active run 对应的 plan，或本分支相对 `origin/main` 改动过的 plan，存在 `- [ ]` 时 `git push` / `gh pr create` 被 hook 阻断；无 active run 且本分支没有 plan 改动时，不扫描历史 `docs/orchestrate/plans`。

**D2 外审策略**：Light Lane **默认不派 Codex**（Coordinator 自审）。保留手动入口——用户明说"这个让 Codex 看一眼" → Coordinator 单次派一个 Codex reviewer（走 `_shared/review-dispatch.md` 派发契约 + Execution tier GPT-5.4 xhigh）。默认不主动派，不做强 hook。

**一键升级门（逃逸，单向 light→formal）**：Light Lane 跑到一半发现"这其实是大改造/触碰红线"时升级：

```bash
state.sh budget reinitialize --run-id <rid> --plan-count <暂估或 1>
# unlimited → initialized + route light→formal（原子，单命令）
```

升级后 `route=formal` + `budget_status=initialized`，所有 formal 护栏（budget-init 门、严格 transition 链）自动回岗。随后补建 design/issue/plan 占位，已 commit 的 light 改动作为既成事实纳入 plan manifest，再 `transition --to discovery --force` 回流到 formal 起点。

### Light Lane 子模式：hotfix 与 spike

子模式不是新 route，是 Light Lane 上额外声明机器锚点的变体（`route=light` + 一个 submode 约定）。

**hotfix（先 push 后审 · 生产救火）**：

- 流程：Light Lane 直派 Worker → **先 push**（救火）→ 事后补审。
- commit：`commit_format_override="hotfix-unreviewed"`（标记未审提交，便于事后定位）。
- 未勾选阻断 push：**豁免**（生产救火必须能立即 push），但 push 后**必须**写一条 `pending_post_push_reviews` 作为"欠一次审"的磁盘记账。
- 事后补审：Closing 读 `pending_post_push_reviews`，非空则派一次事后 regression review 并清空，否则 Closing 不算完成（见 `references/workflow-closing.md` Step 22b）。

**spike / POC（产出 verdict 即弃）**：

- 目录：临时目录 `.codex/multi-model-workflow/spikes/<slug>/`，物理隔离，不进 `docs/orchestrate/` 正式树。
- 编号：**不占 plan/issue 编号**（不写 `docs/orchestrate/plans/` `issues/`，不调用占编号的写入路径）。
- 产出：throwaway code + 1-page verdict 文档（可行/不可行 + 证据）；verdict 是唯一交付物，code 不要求 commit 到主分支。
- budget：unlimited（spike 是探索，不卡预算）。
- release gate：不触发——spike 终点是 verdict 返回，不进 Closing 的 push/PR。
- 升级：verdict=可行且用户要落地 → 走一键升级门转 formal，spike 产物作为 design 输入。

**Within-Conversation Resume**：同一对话内 phase skill 返回的 verdict → 直接路由到下方对应 phase 的 Handle Return 步骤，不重走 Steps 0-2。

## Step 2：Infrastructure Setup

**Read** `references/workflow-infrastructure.md` Step 2 并严格执行（Git Checkpoint + Scope Contract + workflow-state）。读完按 Route 进入对应 phase。

## Steps 7-14：Route 1 — Formal Orchestrate

线性管线：Discovery → Plan Writing → Execution → Final Review → Closing。每个 phase skill 通过 `加载 skill `multi-model-workflow:<name>`` 加载到主线程。

**Verdict 机械路由（Steps 8/10/12/14/20 通用）**：phase skill 返回 verdict 后先查数据——

```bash
bash "${MMW_PLUGIN_ROOT}/scripts/state.sh" verdict-route \
  --run-id "<run_id>" --phase <phase> --verdict "<VERDICT>"
```

返回 `judgment=false` → 照 `action`/`target` 机械执行，不读表；`judgment=true` → 按各 Handle 步的判断表散文裁决；`no-data` → 回退判断表。`target` → Step 映射：`discovery`→Step 7 · `plan-writing`→Step 9 · `execution`→Step 11 · `final-review`→Step 13 · `direct-repair`→Step 8a · `closing`→Closing。`action=invoke-skill` → `加载 skill `<target>`` 完成后重进原 phase；`action=reflux-counter` 由命令内部完成计数与裁决（NEEDS_EXECUTION 不再手读 `execution_reflux_count`）。

### Step 7：orchestrate-discovery

```
加载 skill `multi-model-workflow:orchestrate-discovery`
```

### Step 8：Handle Discovery Return

> **Phase complete.** Discovery: [设计文档状态, Design Review 结果]。Passing to [next phase]。

机械 verdict 查 verdict-route（READY_FOR_REPAIR → Step 8a 等）。判断分支：

| Discovery Verdict（判断） | Coordinator 动作 |
| --- | --- |
| `DISCOVERY_READY` / `DISCOVERY_NOT_NEEDED` | goto Step 9 前检查 issue hierarchy：有 → Step 9；无 → 先 Step 8b（大 issue 拆分）再 Step 9 |
| `NEEDS_USER_DECISION` | 询问用户（一次只问一个），回答后重新进入 discovery |
| `BLOCKED` | 报告用户 |

#### Step 8b：大 issue 拆分

Read Scope Contract + design doc → 重进 `orchestrate-discovery` Step 12。（compact 后设计内容须重新 Read。）

#### Step 8a：Direct Repair

`state.sh budget unlimited --run-id "<run_id>" --route direct-repair` → **Read** `references/workflow-direct-repair.md` → Closing。

---

### Step 9：orchestrate-plan-writing

```
加载 skill `multi-model-workflow:orchestrate-plan-writing`
```

### Step 10：Handle Plan-writing Return

> **Phase complete.** Plan-writing: [plan 数量, task pack 数量, budget]。Passing to [next phase]。

机械 verdict 查 verdict-route（PLAN_CREATED 须先确认 budget 已初始化；NEEDS_TRIAGE / NEEDS_DIAGNOSIS / NEEDS_ARCHITECTURE 走 invoke-skill 写回后重进 Step 9）。判断分支：

| Plan-writing Verdict（判断） | Coordinator 动作 |
| --- | --- |
| `NEEDS_ISSUES` | 判断缺件类型：缺大 issue → Step 8b（大 issue 拆分）；缺小 issue → 重新 Step 9（plan_writer 内部处理） |
| `NEEDS_DECISION` | 询问用户 → 回答后 Step 9 |
| `NEEDS_CONTEXT` | 派 `code_explorer`（窄事实）/ `加载 skill `improve-codebase-architecture``（模块边界）→ 补充后 Step 9 |
| `BLOCKED` | 报告用户 |

---

### Step 11：orchestrate-execution

```
加载 skill `multi-model-workflow:orchestrate-execution`
```

### Step 12：Handle Execution Return

> **Phase complete.** Execution: [pack 通过数/总数, repair rounds, budget 消耗]。Passing to [next phase]。

机械 verdict 查 verdict-route。判断分支：

| Execution Verdict（判断） | Coordinator 动作 |
| --- | --- |
| `NEEDS_ARCHITECTURE` | `加载 skill `improve-codebase-architecture`` → 只影响当前 pack → 回 Step 11；改变 plan → 回 Step 9 |
| `BLOCKED` | 报告用户 |

---

### Step 13：orchestrate-final-review

```
加载 skill `multi-model-workflow:orchestrate-final-review`
```

### Step 14：Handle Final Review Return

> **Phase complete.** Final Review: [verdict, release risk 状态]。Passing to [next phase]。

机械 verdict 查 verdict-route（`NEEDS_EXECUTION` 的回流计数已完全下沉到命令内部——返回 goto 即回 Step 11，返回 report-user 即 BLOCKED）。判断分支：

| Final Review Verdict（判断） | Coordinator 动作 |
| --- | --- |
| `BLOCKED` | 报告用户 |

**回流处理**：回流按受影响 Plan 数 `budget credit` 归还额度（effective_used = review_used − review_credit）。Plan revision 改变 plan count → plan-writing Step 12a 重新确认 budget。

## Steps 15-18：Route 2 — Bug Investigation

**Read** `references/bug-investigation-route.md` 并严格执行（dispatch analyst → handle return → Codex review / worker dispatch → Closing）。读完进入 Closing。

## Steps 19-20：Route 3 — Multi-PR Merge

`加载 skill `multi-model-workflow:orchestrate-multi-pr-merge``。

机械 verdict 查 verdict-route（`--phase multi-pr-merge`）。判断分支：

| Multi-PR Merge Verdict（判断） | Coordinator 动作 |
| --- | --- |
| `NEEDS_USER_DECISION` | 冲突解决需要用户决策 → 询问用户 → 拿到决策后重新进入 |
| `BLOCKED` | 报告用户 |

## Steps 21-24：Closing

**Read** `references/workflow-closing.md` 并严格执行（Final Verification + Push + PR + Report + Cleanup）。流程终点。

---

## Global Constraints

**Hard Gates**：没有验证证据不得声称完成 / 没有 design document 不跳到 plan / 每 phase review 不可跳过 / upstream 结论必须写回再继续 / 不存在非阻塞项。

**BLOCKED 报告格式**（任何 phase 返回 BLOCKED 时，使用双层格式报告用户）：

**业务影响层**（非技术人员可读）：
> <哪个功能/流程>在<哪个环节>被阻塞。
> 影响：<用户能感知到的影响>
> 需要的帮助：<用户可以做什么来解除阻塞>

**技术详情层**（如需转发给工程师）：
> Phase: <phase 名称> | Verdict: BLOCKED
> Root cause: <阻塞根因>
> Attempted: <已尝试的解决方案>

**Sub-agent 隔离**：prompt 必须自足；Sub-agent 不读 SKILL.md / references/；`skills:` frontmatter 自动预加载。**Commit 纪律**：Formal execution worker 在分配的 plan worktree 分支内按 Pack 独立 commit，Coordinator 通过 `recycle-plan.sh` 回收合并；Light Lane / route-worker 若无隔离 worktree，才在当前工作树提交。Plan-writer 等不 commit，Coordinator 统一提交。不 stage 非 scope 文件。

**禁止**：跳过 Discovery / Plan Review / Final Review / 用技术语言汇报 / 自己写生产代码 / 每 task 一个 sub-agent / 超循环上限不处理。
