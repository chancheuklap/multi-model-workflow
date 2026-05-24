# Codex 跨 PR 集成审查

> **流程位置**：`orchestrate-multi-pr-merge` Steps 16-18 · 所有冲突解决后（或 explorer 未发现冲突）进入 · 通过后 → Steps 19-22（`merge-completion.md`）

这不是 Plan Implementation Review（审查单个 Plan 的全部 pack），不是 Final Review（审查 design intent coverage）——这是**跨 PR 集成审查**，验证多个 PR 合在一起后系统是否正确。

## Step 16：构造 Codex Dispatch

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

Review prompt 写入 `.codex/multi-model-workflow/review-prompts/multi-pr-integration-review.md`：

```markdown
## Scope
跨 PR 集成审查。多个并行 PR 来自同一大设计，各自已通过 Final Review。
本次审查验证它们合在一起后是否正确。

## 大设计文档
<path>

## PRs included
| PR | Branch | 核心行为 | Final Review verdict |
<paste>

## 冲突解决记录
<paste resolved conflicts + how they were fixed>
<if no conflicts: 'Explorer 确认无 PR 间冲突'>

## Combined diff
<combined diff of all PRs against base>

## 合同地图
<all cross-PR contract surfaces>

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

- 简单修复（≤ 2 文件、不碰合同）→ Coordinator 直接修
- 复杂修复 → 派 worker

修复后做 **Targeted Re-Review**：
1. 写 prompt → `.codex/multi-model-workflow/review-prompts/<gate>.md`
2. 读取 baseline reviewer `agent_id`：`.codex/multi-model-workflow/review-agents/multi-pr-integration-review.agent-id`
3. `send_input({ target: "<baseline reviewer agent_id>", message: "<full contents of review-prompts/<gate>.md>" })`
4. `wait_agent({ targets: ["<baseline reviewer agent_id>"], timeout_ms: 600000 })`
5. 将 reviewer 最终消息存到 `.codex/multi-model-workflow/review-results/<gate>.md`

Compaction 恢复：有 `.agent-id` 无对应 `review-results/` → wait 该 reviewer agent；targeted re-review 缺少 baseline `.agent-id` 时 BLOCKED，不新建 reviewer。

gate 名使用 `multi-pr-repair-<round>`（`<round>` = 当前修复轮次 1/2），不覆盖 baseline 结果。

Review prompt 写入 `.codex/multi-model-workflow/review-prompts/multi-pr-repair-<round>.md`：

```markdown
## Scope
Targeted re-review for Multi-PR integration repair.
Only review the changes made to address the listed findings.

## Original findings
<paste accepted findings>

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

---
> **下一步**：通过 → Steps 19-22（`merge-completion.md`）。BLOCKED → 返回 verdict。
