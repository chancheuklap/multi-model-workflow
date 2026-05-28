# Design Review Angles + Dispatch Details

> **流程位置**：`orchestrate-discovery` Steps 10-11 · Design Review 派发 + 修复 · 通过后回到 SKILL.md Step 12

## Self-Read Protocol

你是 codex-reviewer（执行 Design Review）。启动时按以下顺序执行：

1. 读 dispatch prompt 头部的 `DISPATCH_ENVELOPE`，提取 `run_id`、`gate`、feature slug。
2. 读 `<project_root>/CLAUDE.md` 和 `<project_root>/CONTEXT.md`（若存在）获取项目基线、不变量、contract wall。
3. 读 `docs/orchestrate/design/<slug>.md` 获取设计文档全文。
4. 读本文件（你正在读的这份手册），理解 Review Angles 与 Return Contract 格式。
5. 按两个 Baseline Review angle 独立验证，遵守 Pre-emit Verification Gate，输出 findings。

## Codex Dispatch 公共部分

两个 review angle 分别提交 Codex review 任务，可并行提交，结果独立返回。

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
3. Validate envelope and dispatch:
   - **Baseline review** (envelope `review_intent: "baseline"`):
     Run `bash "${CLAUDE_PLUGIN_ROOT}/scripts/dispatch-review.sh" validate --prompt-file ".claude/multi-model-workflow/review-prompts/<gate>.md" --gate "<gate>"`.
     `node "$CODEX_SCRIPT" task --background --prompt-file <path> <model flags>`
     -> record JOB_ID into `review-prompts/<gate>.job-id`
     Then write the registry entry: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/dispatch-review.sh" record --prompt-file ".claude/multi-model-workflow/review-prompts/<gate>.md" --gate "<gate>" --agent-id "<JOB_ID>"`.
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
<!-- END: review-dispatch -->

**整体 Verdict 前置检查**：如果 reviewer 返回整体 `needs context`（不是某条 finding 的 `needs evidence`），说明 reviewer 无法完成审查。Coordinator 补充 reviewer 所需的上下文后重新 dispatch，不进入 per-finding disposition。

每条 finding 使用 Finding Shape：`severity / confidence / locator / evidence / impact / remediation`。

## Baseline 1: Design Content Review

Review prompt 写入 `.claude/multi-model-workflow/review-prompts/design-content-review.md`：

```markdown
## Scope
Design Content Review — 审设计自身是否完整、可测试、可执行。

## Read first
自读：`<project_root>/CLAUDE.md`、`<project_root>/CONTEXT.md`（若存在）、相关 ADR 文件。

## Source design
docs/orchestrate/design/<slug>.md

## Project baseline
自读 `docs/orchestrate/design/<slug>.md` 中 `## Cross-Plan Contract Anchors` 节（若设计触碰合同边界）。

## Review angles

### 业务术语一致性
设计文档中的术语是否与 CONTEXT.md / ADR 一致。

### 用户旅程覆盖
每条用户可感知的行为是否有对应的目标描述。

### 可测试性
每条目标行为是否可通过命令、断言或截图验证。不可测的 intent 是 finding。

### UI mockup 转化（与设计文档同等重要）
Mockup 是可视化设计文档，地位与文字设计文档平等。如有 mockup（docs/orchestrate/mockups/<slug>/），检查：
- 每个 mockup 页面 × viewport × states 是否已在 `## UI / UX 状态` 中拆解为具体视觉规格（布局/颜色/字体/间距/组件结构）
- 拆解出的视觉规格是否可直接转为 issue 和 plan 的 acceptance criteria（不是"见 mockup"指针）
- 交互行为（点击/hover/输入/动画）是否逐项描述
- 状态变体（空/加载/错误/成功/权限不足）是否在 mockup 中体现并描述

### Contract anchors
跨边界数据是否有 Contract anchors（boundary type / owner / provider / consumer / verifier）。缺 anchors 是 finding。

### 失败场景
错误路径、边界条件、回退策略是否覆盖。

### Scope 纪律
是否混入了未来需求或超出 scope 的能力。

## Critical 定义
以下为 Critical（必须修复才能进入 plan）：
- 核心意图不可测
- 目标行为含混导致 plan 必须猜
- UI 有 mockup 但没拆解为具体视觉规格表（只写了目录路径不算转化）
- 合同缺 anchors
- 文档内部矛盾
- 关键场景缺失
- 新对象缺 owner

## Calibration
只标记会导致实际问题的 issue。措辞改进、风格偏好、"某些 section 不够详细"——不是 finding。除非有严重缺口会导致有缺陷的 plan，否则 approve。

## Return Contract
### Verdict
pass / blocked / needs repair / needs context
### Evidence
- 实际检查过的 files / docs / tests / commands / screenshots
### Result
Review: 设计文档 - Design Content Review
Phase summary: 通过 / 阻塞
Critical:
Important:
低置信度观察:
Disposition required:
### Verification
- 已运行的 commands 和结果
### Open Items
- parent 必须处理的问题
```

## Baseline 2: Project Alignment Review

Review prompt 写入 `.claude/multi-model-workflow/review-prompts/design-alignment-review.md`：

```markdown
## Scope
Project Alignment Review — 审设计是否符合项目事实和约束。

## Read first
自读：`<project_root>/CLAUDE.md`、`<project_root>/CONTEXT.md`（若存在）、相关 ADR 文件。

## Source design
docs/orchestrate/design/<slug>.md

## Project baseline
- 北极星 / 不变量 / 数据权威 / contract wall
自读 `<project_root>/CONTEXT.md` 和相关 ADR 获取不变量定义。

## Contract anchors
自读 `docs/orchestrate/design/<slug>.md` 中 `## Cross-Plan Contract Anchors` 节（若设计触碰合同边界）。

## Review angles

### 项目术语
设计文档中的术语是否与项目既有定义一致。

### 数据权威和模块边界
新增数据的权威来源是否明确，是否跨越了既有模块边界。

### 不变量
设计是否违反项目声明的不变量。

### 新端口注册
新增的 port / command / chargeable action / capability 是否进入 registry / catalog。

### Migration tree
新增 DB 字段 / schema 变更是否有对应 migration。

### Helper placement
新增 helper 是否放在正确的模块边界内（不为绕过边界而存在）。

### 基础设施依赖
设计依赖的基础设施（队列、缓存、外部服务）是否已存在或有创建计划。

### ADR 条件
是否触发了需要新 ADR 的架构决策。

## Critical 定义
以下为 Critical（必须修复才能进入 plan）：
- 违反北极星或不变量
- 依赖不存在的基础设施
- 跨服务合同缺 producer-consumer
- 绕过 Pydantic / registry / migration
- 未设计生产风险

## Calibration
只标记会导致实际问题的 issue。措辞改进、风格偏好——不是 finding。除非有严重缺口会导致有缺陷的 plan，否则 approve。

## Return Contract
### Verdict
pass / blocked / needs repair / needs context
### Evidence
- 实际检查过的 files / docs / tests / commands / screenshots
### Result
Review: 设计文档 - Project Alignment Review
Phase summary: 通过 / 阻塞
Critical:
Important:
低置信度观察:
Disposition required:
### Verification
- 已运行的 commands 和结果
### Open Items
- parent 必须处理的问题
```

---
## Disposition 流程

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

## Coordinator 端最小职责

Coordinator 在派发时只需完成以下动作，其余由 Reviewer 自读：

1. 写 `DISPATCH_ENVELOPE`，填入 `run_id`、`gate`（`design-content-review` / `design-alignment-review`）、`review_intent: "baseline"`。
2. 在 `Source design:` 中列出 design 文件路径（reviewer 自读全文）。
3. 写 review-prompts 文件，运行 validate/record 脚本，触发 Codex job。
4. 等待 job 完成后运行 result/complete 脚本，进入 Disposition 流程。

> **下一步**：Design Review 通过 → 回到 SKILL.md Step 12（大 issue 拆分）。needs repair → Coordinator 直接修设计文档 → targeted re-review。
