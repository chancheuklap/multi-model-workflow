# Codex 跨 PR 集成审查

> **流程位置**：`orchestrate-multi-pr-merge` Steps 16-18 · 所有冲突解决后（或 explorer 未发现冲突）进入 · 通过后 → Steps 19-22（`merge-completion.md`）

## Self-Read Protocol

你是 codex-reviewer（执行 Multi-PR 集成审查）。启动时按以下顺序执行：

1. 读 dispatch prompt 头部的 `DISPATCH_ENVELOPE`，提取 `run_id`、`gate`、`phase: "multi-pr-merge"`。
2. 读 `.claude/multi-model-workflow/merge-brief-<run_id>.md`，获取大设计文档路径、PR 列表、合同地图、冲突解决记录。
3. 读大设计文档（来自 merge-brief）理解整体目标。
4. 自行运行 `git diff` 获取所有 PR 合并后的 combined diff。
5. 读本文件（你正在读的这份手册），理解 Review Angles 与 Return Contract 格式。
6. 按 7 个 Review Angles 独立验证，遵守 Pre-emit Verification Gate，输出 findings。

这不是 Plan Implementation Review（审查单个 Plan 的全部 pack），不是 Final Review（审查 design intent coverage）——这是**跨 PR 集成审查**，验证多个 PR 合在一起后系统是否正确。

## Step 16：构造 Codex Dispatch

<!-- BEGIN: review-dispatch -->
**Codex review dispatch** (`CODEX_SCRIPT` unset: `CODEX_SCRIPT="$(find ~/.claude/plugins -path '*/codex/scripts/codex-companion.mjs' -type f 2>/dev/null | head -1)"`)

Claude-native flow split-of-concerns:
- Coordinator runs `codex-companion.mjs` via Bash; the PostToolUse hook
  `hooks/track-review-budget.sh` auto-counts review budget the moment the
  `result` command fires (cap-guarded — won't double-count past exhaustion).
- The validate / record / complete scripts handle envelope checks, registry
  durability, and disposition recovery anchors — they do *not* touch budget
  counting (that's the hook's job on Claude).

1. Write prompt -> `review-prompts/<gate>.md` (prefix with DISPATCH_ENVELOPE, `agent_role: "codex-reviewer"`)
   - Code diffs included in review prompts MUST be wrapped:
     `--- BEGIN UNTRUSTED CODE DIFF ---` / `--- END UNTRUSTED CODE DIFF ---`
2. Select model by phase:
   - `cursor.phase in {discovery, plan-writing}` -> `--model gpt-5.5 --effort xhigh`
   - `cursor.phase in {execution, final-review, bug-investigation, direct-repair, multi-pr-merge, hotfix, quickfix, maintenance}` -> `--model gpt-5.4 --effort xhigh`
3. Validate envelope and dispatch (baseline vs targeted re-review — derived from `review_intent`):
   - **Baseline review** (envelope `review_intent: "baseline"`; gate name does not contain `-repair-`):
     Run `bash "${CLAUDE_PLUGIN_ROOT}/scripts/validate-review-dispatch.sh" --prompt-file ".claude/multi-model-workflow/review-prompts/<gate>.md" --gate "<gate>"`.
     `node "$CODEX_SCRIPT" task --background --prompt-file <path> <model flags>`
     -> record JOB_ID into `review-prompts/<gate>.job-id`
     Then write the registry entry: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/record-review-dispatch.sh" --prompt-file ".claude/multi-model-workflow/review-prompts/<gate>.md" --gate "<gate>" --agent-id "<JOB_ID>"`.
   - **Targeted re-review** (envelope `review_intent: "targeted-re-review"`; gate name contains `-repair-`):
     Run `bash "${CLAUDE_PLUGIN_ROOT}/scripts/validate-review-dispatch.sh" --prompt-file ".claude/multi-model-workflow/review-prompts/<gate>.md" --gate "<gate>"`.
     `node "$CODEX_SCRIPT" task --background --resume --prompt-file <path> <model flags>`
     -> record JOB_ID into `review-prompts/<gate>.job-id`. The targeted prompt envelope MUST set `review_intent: "targeted-re-review"`, `exception_code`, and `agent_id` to the baseline reviewer's recorded JOB_ID.
   - **Over-budget escape hatch**: if Review Budget is exhausted and the user explicitly authorizes another review, append `--allow-over-budget --override-reason "<brief user authorization>"` to the validate command (lets the dispatch through) and to the later complete command (records the override in the registry). Do not use this flag for convenience or for Effort Budget.
4. Wait: `node "$CODEX_SCRIPT" status "$(cat .claude/multi-model-workflow/review-prompts/<gate>.job-id)" --wait --timeout-ms 600000` (run_in_background: true)
5. Result: `node "$CODEX_SCRIPT" result "$(cat .claude/multi-model-workflow/review-prompts/<gate>.job-id)"` -> `review-results/<gate>.md`
   - The `track-review-budget` hook auto-increments review_used here (cap-guarded).
6. Mark durable: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/complete-review-dispatch.sh" --run-id "<run_id>" --gate "<gate>" --agent-id "<JOB_ID>" --result-file ".claude/multi-model-workflow/review-results/<gate>.md"`. If Step 3 used the over-budget escape hatch, pass the same `--allow-over-budget --override-reason "<brief user authorization>"` here to record the override in the registry.
6b. Disposition recovery anchor: before reading findings for disposition, run `bash "${CLAUDE_PLUGIN_ROOT}/scripts/record-review-disposition.sh" --run-id "<run_id>" --gate "<gate>" --status started`; after all findings have disposition records, run the same command with `--status completed`.

**Confidence rubric (REQUIRED in every review prompt)**:
- 1-3: low confidence. Coordinator may suppress without deep investigation.
- 4-6: medium. Coordinator must gather additional evidence before disposition.
- 7-10: high. Coordinator should default to accept unless contradicted by evidence.

**Pre-emit Verification Gate**：

每个 finding 必须满足以下条件才能进入报告：

1. **引用触发 finding 的具体代码行**——file:line + 该行的原始文本。
   - "field X doesn't exist on model Y" → 引用 class Y 的定义体，证明字段缺失
   - "dict.get() might return None" → 引用 dict 的初始化代码
   - "race condition between A and B" → 引用 A 和 B 两处代码

2. **无法引用 = finding 未验证**。将 confidence 强制设为 4-5（从主报告中抑制，移入附录）。
   不要通过虚构 confidence 7+ 来绕过此门槛。

3. **框架元编程特例**：当符号来自 ORM 元类、装饰器、代码生成器时，引用生成该符号的元构造，而非期望在类体中 grep 到字面名称。

**Rationalization Prevention**：
- "This looks fine" 不是 finding。要么引用证据证明确实没问题，要么标记为未验证。
- "likely handled elsewhere" → 读并引用处理代码，或标记 unknown。
- "probably tested" → 给出测试文件和方法名，或标记 unknown。

**证据表 (REQUIRED)**：
Reviewer 必须在 `### Evidence` 下填写半结构化证据表。证据表证明 reviewer 实际检查过什么；它不是设计意图摘要，也不能替代阅读 source artifacts。

| 字段 | 必填内容 |
| --- | --- |
| 已读设计 / mockup / plan 来源 | 实际读过的 design、mockup、plan、issue、Scope Contract 或 review baseline 路径。没有对应来源时写 `不适用`，不能留空。 |
| 已检查代码或产物路径 | 实际检查的源码、生成产物、state schema、hooks、templates、文档或 runtime contract 路径。 |
| 已运行命令或验证 | 实际执行的命令、测试、build check、schema check、browser smoke 或 manual gate；未运行时写明原因。 |
| Finding 证据 | 每个 finding 的路径、行号、diff、命令输出或可观察行为；无证据的 finding 必须移入低置信度观察。 |
| 假设 | 影响 verdict 的前提，例如环境、账号、fixture、平台或 reviewer 未能直接验证的 upstream 状态。 |
| 未验证项 | 相关但未验证的内容和原因；没有未验证项时写 `无`。 |

**Bias indicators (REQUIRED at end of review output)**:
Reviewer must declare which modules/stacks they lack experience with and which findings may be affected.

Compaction recovery:
- `.job-id` present but no `review-results/<gate>.md` -> resume from Step 4 (status + result) using that JOB_ID; once the result is saved and bookkeeping is complete, proceed to Step 6.
- `review-registry/<gate>.json` status is `completed` or `disposition_started`, and `review-results/<gate>.md` exists -> Read that exact result file and continue Coordinator disposition. Do not re-dispatch review and do not proceed to repair until `record-review-disposition.sh --status completed` has been recorded.
- If the `.job-id` is missing for a targeted re-review, mark BLOCKED; do not create a new reviewer for the same baseline.
<!-- END: review-dispatch -->

Review prompt 写入 `.claude/multi-model-workflow/review-prompts/multi-pr-integration-review.md`：

```markdown
## Scope
跨 PR 集成审查。多个并行 PR 来自同一大设计，各自已通过 Final Review。
本次审查验证它们合在一起后是否正确。

## Merge context
读 `.claude/multi-model-workflow/merge-brief-<run_id>.md` 获取：
- 大设计文档路径（你自读该文档）
- PRs included（PR / Branch / 核心行为 / Final Review verdict）
- 冲突解决记录（resolved conflicts + how they were fixed；或 'Explorer 确认无 PR 间冲突'）
- 合同地图（all cross-PR contract surfaces）

## Combined diff
自行运行 `git diff <base-branch>..HEAD`（或对每个 PR branch 分别 diff 后合并）。

## Review angles

### 1. 组合行为正确性
所有 PR 合在一起是否产出大设计描述的正确行为。
每个 PR 各自正确不代表组合正确——关注交互、顺序、依赖。

### 2. 合同一致性
跨 PR 的 Pydantic model / API / DB schema / JSON payload / registry 是否一致。
一个 PR 提供的合同是否被另一个 PR 正确消费。

### 3. 迁移完整性
多个 PR 的 migration 合并后：
- 顺序是否正确
- 是否有遗漏的 migration（PR A 改了 model，PR B 没有对应 migration）
- 回滚是否安全

### 4. 状态一致性
跨 PR 的 shared state 假设是否一致。
并发访问 shared state 是否安全。

### 5. Import / 依赖
合并后是否有循环 import。
依赖版本是否一致。

### 6. 回归
合并所有 PR 后，既有功能是否完好。
跑完整测试套件并报告结果。

### 7. 冲突修复质量（如有）
之前解决的冲突的修复是否正确、完整。
修复是否引入了新问题。

## Calibration
**不要信任各 PR 的 Final Review 结论——独立验证组合行为。** 每个 PR 各自正确不代表组合正确。你的审查必须基于合并后的代码事实，不是各 PR 独立 review 的结论。

只标记会导致实际问题的 issue。每个 finding 必须有 evidence。
单个 PR 内部的代码质量——已在各自 Final Review 中覆盖，不再重复。
措辞、命名、风格——不是 finding。

## Return Contract
### Verdict
pass / blocked / needs repair / needs context
### Evidence
### Result
组合行为:
合同一致性:
迁移完整性:
状态一致性:
Import / 依赖:
回归:
冲突修复质量:
Critical:
Important:
Disposition required:
### Verification
### Open Items
```

## Step 17：接收 + Disposition

**整体 Verdict 前置检查**：reviewer 返回整体 `needs context` 时，Coordinator 补充上下文后重新 dispatch，不进入 per-finding disposition。

<!-- BEGIN: disposition-table -->
**Coordinator 亲验纪律** (disposition 之前的必经步骤):

收到 reviewer findings 后**禁止直接转发给 worker**。逐条执行：
1. 亲验：用 Read / grep / 对照设计文档验证 finding 的事实主张
2. Disposition：accepted / rejected / needs evidence / out of scope（调用 state.sh disposition append）
3. 修复指令：只把 accepted findings 翻译为具体修复指令传给 worker。Reviewer 原始输出不传

没有 disposition 的 finding 不能进入 repair。过滤越界建议：out-of-scope 文件不能因为 reviewer 提到就被修改。

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
| `rejected` | 记录反证；不派 repair，不让同一 finding 反复进入 review |
| `needs evidence` | 派 explorer 补证据（窄范围用 `code-explorer`，多模块用 `complex-code-explorer`）；补证前不 repair |
| `duplicate / already covered` | 链到已有 finding、pack、commit、test 或文档；不新增路线 |
| `out of scope` | 从当前 scope 移出；**立即**开 GitHub issue（Durable Handoff Brief 格式，先查重） |
| `needs evaluation` | 不在当前 pack 可修范围但需独立评估；**立即**开 GitHub issue，标明评估要点 |
| `user decision` | 停止执行，一次只问一个会改变设计、计划或发布策略的问题 |

冲突按 evidence quality 判断，不按 reviewer 数量投票。

**Path A re-review 规则** (仅 confidence >= 7 的 accepted findings):
- Coordinator Path A 直接修复 -> 强制 targeted Codex re-review
- Codex 返回 `needs_repair` -> 必须升级 Path B 派 worker
- 用 `state.sh path-a-escalation start/update/clear` 追踪
<!-- END: disposition-table -->

Multi-PR 增加验证维度：对照大设计文档确认 spec 判断 + 对照冲突解决记录确认修复判断。

**`needs evidence` 补证**：派 `code-explorer`（窄范围单文件/单调用链）或 `complex-code-explorer`（多模块/跨边界）做只读调查。Prompt 包含：finding 待验证、reviewer 主张、Coordinator 存疑点、相关文件。Explorer 返回 confirmed / refuted / partially confirmed 后再给最终 disposition。

**Review 通过** → Step 19（`merge-completion.md`）。

**有 accepted findings** → Step 18。

## Step 18：集成审查修复

修复路由同冲突解决阶段：

<!-- BEGIN: repair-routing -->
**Finding-to-owner 修复分流 (REQUIRED)**：

这套规则在 reviewer 已经产出 finding、Coordinator 完成 disposition 之后使用。它不对 review 内容预先分风险等级，只根据 finding 的风险面、根因清晰度和修复形态选择 owner。

| Finding / 修复形态 | 修复 owner |
| --- | --- |
| 范围小、本地化、意图清楚、不碰合同边界 | Coordinator Path A 可自修；修完必须验证，Path A targeted re-review 失败时升级 Path B。 |
| 同一个 pack 内的普通修复，原 worker 能胜任 | 使用 `SendMessage({ to: "<agent_id>", ... })` 续修原 `pack-executor`；已有 agent_id 时不得新建同类 worker。 |
| 高风险或跨边界修复：跨模块、migration、billing、permission、runtime、共享合同、state machine、生成模板 | 如果原 worker 是 `complex-pack-executor` 且仍适合承接，使用 `SendMessage` 续修原 agent；如果原 worker 是 `pack-executor`，或 finding 证明原 owner 不具备高风险合同能力，必须升级 owner。Formal Execution 中先形成新的 repair Pack / 回到 Execution 边界，再按新的 pending pack 派发 `complex-pack-executor`；non-execution route 中使用新的 route-worker escalation dispatch。两种情况都必须记录 `original_agent_id`、`context_ref`、`disposition_ref` 和 accepted finding refs。 |
| 根因不清，只知道症状 | 先派 `code-explorer` 或 `complex-code-explorer` 做只读补证；确认根因前不 patch。 |
| 系统性 bug、重复修复失败、未知 regression | 派 `root-cause-analyst`，要求列可证伪假设、排除证据和回归验证。 |
| Final Review 发现跨 plan 合同问题 | 返回一次 `NEEDS_EXECUTION`，附 affected plans / packs / 连接面 / producer-consumer 断点，通过 execution repair 处理。 |
| 设计、mockup 或 plan 不足以判断正确性 | 回流 Discovery 或 Plan Writing；不得用代码 patch 代替 source artifact 修复。 |
| Release blocker | 简单且不碰合同边界可 Path A；涉及 migration / deploy order / rollback / permission / billing / runtime 时派 `complex-pack-executor`。 |
| Multi-PR 合并冲突 | 简单冲突可 Coordinator 修；跨 PR 合同、迁移、状态或依赖冲突派 `complex-pack-executor`；系统性冲突派 `root-cause-analyst`。 |

调度纪律：
- Targeted repair 默认优先 `SendMessage` 续修原 agent；但高风险 finding 不能被原普通 worker 绑定。如果原 worker 是 `pack-executor`，Coordinator 必须写明 `escalation_reason`，并按当前 route 的状态模型升级 owner。
- Formal Execution 的升级不能对同一个 `pack_id` 再次 `Agent({...})`：`validate-pack-dispatch.sh` 只允许 pending pack 首次派发，已有 `agent_id` 的同一 pack 普通修复只能 `SendMessage` 原 agent。若 accepted finding 证明必须换成 `complex-pack-executor`，Coordinator 必须回到 Execution/Plan 边界，把修复表达成新的 repair Pack 或 plan revision，使其拥有新的 `pack_id`、pending status、完整 Pack Brief 和独立 dispatch；不能用第二个 agent 冒充同一 Pack 的续修。
- Non-execution route 的升级派发不是原 worker 的续修：使用 `validate-route-worker-dispatch.sh --transport Agent`，envelope 里 `agent_id: null`、`pack_id: null`、`repair_round` 保留当前轮次、`idempotency_key` 使用新的 escalation key，并用 `record-route-worker-dispatch.sh` 写入独立 `.agent-id` 文件。只有同一 owner 的普通 follow-up 才使用 `SendMessage` 续修原 agent；缺失原 `agent_id` 仍然 BLOCKED，不能用新 worker 冒充续修。
- 升级派发 prompt 必须带上 `original_agent_id`、`context_ref`、`disposition_ref`、accepted findings、已确认风险面和回归证据要求，保证新 `complex-pack-executor` 能追溯原 context。
- `Path A` 只适用于真正小范围修复；失败或 targeted re-review 返回 `needs repair` 时必须升级，不重复同一修法。
- `needs evidence` finding 先补证再决定 owner。
- 所有 repair prompt 只携带 accepted findings 和 Coordinator 亲验后的修复指令，不转发 reviewer 原始输出。

**回归证据要求 (REQUIRED in repair return)**：

Repair agent 或 Coordinator Path A 返回时必须提供回归证据；不要求每个 finding 都新增一个测试。优先选择能证明用户可见行为、合同或发布风险已修好的证据，不新增低价值实现细节测试。

| Finding 类型 | 优先证据 |
| --- | --- |
| Public behavior bug | 现有或新增 behavior / integration test。 |
| 合同、schema、migration、生成产物 bug | 合同检查、schema validation、migration check 或 build check。 |
| UI 行为 bug | Browser smoke、screenshot、DOM state validation 或现有 UI test。 |
| permission、billing、runtime、state machine、hook 问题 | integration check、state transition check、hook test，或带 owner 和步骤的 manual validation gate。 |
| 文档或 plan mismatch | 文档一致性证据和修正后的 source 链接。 |
| 只能环境验证的问题 | 明确 owner、命令、预期结果和阻塞条件的 manual validation gate。 |

Repair Return Contract 必须补充：
- `Regression evidence`: 命令、测试、build/schema/migration/hook check、browser evidence，或 manual validation gate。
- `Test choice`: 说明为何使用现有测试、新增高层测试、合同检查或 manual gate；不得为纯实现细节新增脆弱测试。
- `Unverified`: 仍未验证的边界和原因；没有则写 `无`。
<!-- END: repair-routing -->

- 简单修复（≤ 2 文件、不碰合同）→ Coordinator 直接修
- 复杂修复 → 派 worker

修复后做 **Targeted Re-Review**。按以下步骤派发 Codex review（复用已有 `CODEX_SCRIPT`）：
1. 写 prompt → `review-prompts/<gate>.md`，并以前缀 `DISPATCH_ENVELOPE` 声明 `agent_role: "codex-reviewer"`、`review_intent: "targeted-re-review"`、`exception_code: "user_requested"` 和非空 `disposition_refs`。
2. 按 Step 16 的共享 `review-dispatch` 执行；gate 名包含 `-repair-`，因此 dispatch 命令必须使用 `--resume` 继续 baseline reviewer session。
3. 等待和读取结果也按 Step 16 的共享 `review-dispatch` 执行，结果写入 `review-results/<gate>.md`。

Compaction 恢复：有 `.job-id` 无对应 `review-results/` → 从 Step 3 继续。

gate 名使用 `multi-pr-repair-<round>`（`<round>` = 当前修复轮次 1/2），不覆盖 baseline 结果。

Review prompt 写入 `.claude/multi-model-workflow/review-prompts/multi-pr-repair-<round>.md`。下例以第 1 轮为例；第 2 轮时同步替换 `repair_round` 和 `idempotency_key`：

```markdown
<!-- DISPATCH_ENVELOPE
{
  "protocol_version": "1",
  "run_id": "<run_id>",
  "phase": "multi-pr-merge",
  "agent_role": "codex-reviewer",
  "agent_id": null,
  "pack_id": null,
  "repair_round": 1,
  "idempotency_key": "<run_id>/multi-pr-repair-1",
  "disposition_refs": ["<accepted finding ids>"],
  "review_intent": "targeted-re-review",
  "exception_code": "user_requested"
}
-->

## Scope
Targeted re-review for Multi-PR integration repair.
Only review the changes made to address the listed findings.

## Original findings
读 `DISPATCH_ENVELOPE.disposition_refs` 对应的 accepted findings（由 Coordinator 在 repair dispatch 时填入）。

## Repair diff
<git diff of repair changes>

## Review focus
- Each accepted finding has been addressed
- Repair does not introduce new issues

## Calibration
只验证修复是否解决了原始 finding。不做全面重审。

## Return Contract
### Verdict
pass / needs repair / blocked
### Evidence
### Result
Per-finding status:
### Verification
### Open Items
```

最多 2 轮修复。超过 → BLOCKED。

## Coordinator 端最小职责

Coordinator 在派发时只需完成以下动作，其余由 Reviewer 自读：

1. 写 `merge-brief-<run_id>.md`（若已写则复用），确保包含 PR 列表、设计文档路径、合同地图、冲突解决记录。
2. 写 `DISPATCH_ENVELOPE`，填入 `run_id`、`gate`（`multi-pr-integration-review`）、`review_intent: "baseline"`。
3. 写 review-prompts 文件，运行 validate/record 脚本，触发 Codex job。
4. 等待 job 完成后运行 result/complete 脚本，进入 Steps 17-18 disposition 流程。

---
> **下一步**：通过 → Steps 19-22（`merge-completion.md`）。BLOCKED → 返回 verdict。
