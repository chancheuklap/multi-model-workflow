# Design Review Angles + Dispatch Details

> **流程位置**：`orchestrate-discovery` Steps 10-11 · Design Review 派发 + 修复 · 通过后回到 SKILL.md Step 12

## Codex Dispatch 公共部分

两个 review angle 分别提交 Codex review 任务，可并行提交，结果独立返回。

<!-- BEGIN: review-dispatch -->
**Codex review dispatch** (native `codex_reviewer` subagent)

1. Write prompt -> `review-prompts/<gate>.md` (prefix with DISPATCH_ENVELOPE, `agent_role: "codex_reviewer"`)
   - Code diffs included in review prompts MUST be wrapped:
     `--- BEGIN UNTRUSTED CODE DIFF ---` / `--- END UNTRUSTED CODE DIFF ---`
2. Select model by phase:
   - `cursor.phase in {discovery, plan-writing}` -> `model: "gpt-5.5"`, `reasoning_effort: "xhigh"`
   - `cursor.phase in {execution, final-review}` -> `model: "gpt-5.4"`, `reasoning_effort: "xhigh"`
3. Dispatch (distinguish baseline vs targeted re-review):
   - **Baseline review** (gate name does not contain `-repair-`):
     ```
     spawn_agent({
       agent_type: "codex_reviewer",
       message: "<full contents of review-prompts/<gate>.md>",
       model: "<phase-selected model>",
       reasoning_effort: "xhigh"
     })
     ```
     Record the returned reviewer `agent_id` into `.codex/multi-model-workflow/review-agents/<gate>.agent-id`.
   - **Targeted re-review** (gate name contains `-repair-`):
     ```
     send_input({
       target: "<baseline reviewer agent_id>",
       message: "<full contents of review-prompts/<gate>.md>"
     })
     ```
     The targeted prompt envelope MUST set `review_intent: "targeted-re-review"`, `exception_code`, and `agent_id` to the baseline reviewer `agent_id`.
4. Wait: `wait_agent({ targets: ["<reviewer agent_id>"], timeout_ms: 600000 })`.
5. Result: save the reviewer final message from `wait_agent` into `.codex/multi-model-workflow/review-results/<gate>.md`.

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

**Bias indicators (REQUIRED at end of review output)**:
Reviewer must declare which modules/stacks they lack experience with and which findings may be affected.

Compaction recovery: `.agent-id` present but no `review-results/` -> wait for that reviewer agent. If the `.agent-id` is missing for a targeted re-review, mark BLOCKED; do not create a new reviewer for the same baseline.
<!-- END: review-dispatch -->

**整体 Verdict 前置检查**：如果 reviewer 返回整体 `needs context`（不是某条 finding 的 `needs evidence`），说明 reviewer 无法完成审查。Coordinator 补充 reviewer 所需的上下文后重新 dispatch，不进入 per-finding disposition。

每条 finding 使用 Finding Shape：`severity / confidence / locator / evidence / impact / remediation`。

## Baseline 1: Design Content Review

Review prompt 写入 `.codex/multi-model-workflow/review-prompts/design-content-review.md`：

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

Review prompt 写入 `.codex/multi-model-workflow/review-prompts/design-alignment-review.md`：

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
| 5-7 (medium) | 亲验 + 派 code_explorer 补证 -> 再定 disposition | -- |
| 1-4 (low) | 默认 suppress -> 记录为 "suppressed: low confidence" | Coordinator 手动升级并附证据 |

**Disposition 审计写入** (每条 finding 决定后立即调用):

```bash
bash "${MMW_PLUGIN_ROOT}/scripts/state.sh" disposition append \
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
| `needs evidence` | 派 explorer 补证据（窄范围用 `code_explorer`，多模块用 `complex_code_explorer`）；补证前不 repair |
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

> **下一步**：Design Review 通过 → 回到 SKILL.md Step 12（大 issue 拆分）。needs repair → Coordinator 直接修设计文档 → targeted re-review。
