# Design Review Angles + Dispatch Details

> **流程位置**：`orchestrate-discovery` Steps 10-11 · Design Review 派发 + 修复 · 通过后回到 SKILL.md Step 12

## Codex Dispatch 公共部分

两个 review angle 分别提交 Codex review 任务，可并行提交，结果独立返回。

<!-- BEGIN: review-dispatch -->
**Codex review 派发步骤**（`CODEX_SCRIPT` 未定义时先执行 `CODEX_SCRIPT="$(find ~/.claude/plugins -path "*/codex/scripts/codex-companion.mjs" -type f 2>/dev/null | head -1)"`）：
1. 写 prompt → `review-prompts/<gate>.md`
2. `node "$CODEX_SCRIPT" task --background --prompt-file .claude/multi-model-workflow/review-prompts/<gate>.md --model gpt-5.4 --effort xhigh` → 记录 JOB_ID，写入 `review-prompts/<gate>.job-id`
3. `node "$CODEX_SCRIPT" status "$(cat .claude/multi-model-workflow/review-prompts/<gate>.job-id)" --wait --timeout-ms 600000`（run_in_background: true）
4. `node "$CODEX_SCRIPT" result "$(cat .claude/multi-model-workflow/review-prompts/<gate>.job-id)"` → 存到 `review-results/<gate>.md`

Compaction 恢复：有 `.job-id` 无对应 `review-results/` → 从 Step 3 继续。
<!-- END: review-dispatch -->

**整体 Verdict 前置检查**：如果 reviewer 返回整体 `needs context`（不是某条 finding 的 `needs evidence`），说明 reviewer 无法完成审查。Coordinator 补充 reviewer 所需的上下文后重新 dispatch，不进入 per-finding disposition。

每条 finding 使用 Finding Shape：`severity / confidence / locator / evidence / impact / remediation`。

## Baseline 1: Design Content Review

Review prompt 写入 `.claude/multi-model-workflow/review-prompts/design-content-review.md`：

```markdown
## Scope
Design Content Review — 审设计自身是否完整、可测试、可执行。

## Read first
<project docs: CLAUDE.md, CONTEXT.md, ADRs, relevant SPEC>

## Source design
docs/orchestrate/design/<slug>.md

## Project baseline
<paste contract anchors if design touches contract boundaries>

## Review angles

### 业务术语一致性
设计文档中的术语是否与 CONTEXT.md / ADR 一致。

### 用户旅程覆盖
每条用户可感知的行为是否有对应的目标描述。

### 可测试性
每条目标行为是否可通过命令、断言或截图验证。不可测的 intent 是 finding。

### UI mockup 转化
如有 mockup（docs/orchestrate/mockups/<slug>/），每个页面 × viewport × states 是否转成了可验收的目标行为描述。

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
- UI 有 mockup 但没转成验收状态
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
<project docs: CLAUDE.md, CONTEXT.md, ADRs, relevant SPEC>

## Source design
docs/orchestrate/design/<slug>.md

## Project baseline
- 北极星 / 不变量 / 数据权威 / contract wall
<paste from CONTEXT.md / ADRs>

## Contract anchors
<paste if design touches contract boundaries>

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
> **下一步**：Design Review 通过 → 回到 SKILL.md Step 12（过渡到 to-issues）。needs repair → Coordinator 直接修设计文档 → targeted re-review。
