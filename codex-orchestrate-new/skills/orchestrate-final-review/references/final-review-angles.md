# Final Review 增强型审查

> **流程位置**：`orchestrate-final-review` Steps 4-5 · 派发后 → Steps 6-8（`final-review-disposition.md`）

## 与 Plan Implementation Review 的分工

每个 Plan 已经独立通过了 spec compliance + code quality + cross-pack coherence review。Final Review 增加三层 Plan Implementation Review 结构性看不到的覆盖：

1. **Regression sweep**（全新层）：读完整 diff（starting commit → HEAD），跑完整测试套件。检查任何 pack 的改动是否破坏另一 pack 的行为或既有功能。这是"全新眼光看全局"的层。
2. **Design intent coverage**（增强层）：逐条走 design doc 和 mockup 中每个可验证 intent。已被 Plan Implementation Review 验证的 intent 只做 1 行确认（merge 后证据仍有效）；落在 Plan 之间缝隙的 gap intent 做完整验证。
3. **Cross-Plan Integration**（改名+降级）：只检查**跨 Plan** 的集成——Plan 内跨 Pack 已由 Plan Implementation Review 的 Cross-Pack Coherence 覆盖。如果所有 Plan 之间没有共享 contract / migration / state surface，Cross-Plan Integration 降级为确认独立性的 1 行声明。Regression sweep 和 Design intent coverage 仍必须执行。

**Final Review 不重复的事**：
- 不重新审查 Plan Implementation Review 已验证且 regression sweep 确认 intact 的行为
- 不重新检查 Plan 内跨 Pack 的 coherence（已由 Plan Implementation Review 覆盖）
- 不重新检查 helper placement、命名或单 pack owned files 内的代码质量

---

## Step 4：派发 2 个 Baseline Codex Reviewer

两个 baseline 分别提交 Codex review 任务，可并行提交，结果独立返回。

**Read** `${MMW_PLUGIN_ROOT}/skills/_shared/review-dispatch.md` 并按其格式派发 Codex review。

### Baseline 1：Regression Sweep + Intent Coverage + Cross-Plan Integration

Review prompt 写入 `.codex/multi-model-workflow/review-prompts/final-review-baseline-1.md`：

```markdown
## Scope
Final Review for a completed implementation. All Plans have individually
passed Plan Implementation Review. Your job is to verify the COMBINED result.

## Read first
自读：`<project_root>/AGENTS.md`、`<project_root>/CONTEXT.md` 或 `<project_root>/CONTEXT-MAP.md` + map 索引的子 context 文件（若存在）、相关 ADR。

## Feature slug（从 Scope Contract 读取）
<YYYY-MM-DD-feature>

## Source design
docs/orchestrate/design/<slug>.md（已通过 Design Review）

## Plans（已通过 Plan Review）
docs/orchestrate/plans/<slug>/（目录，逐个列出所有 plan 文件路径）

## Cross-plan contract anchors（已通过 Plan Review）
docs/orchestrate/design/<slug>.md#cross-plan-contract-anchors

## Issue hierarchy
docs/orchestrate/issues/<slug>/

## Starting commit
从 `.codex/multi-model-workflow/execution-state-<run_id>.json` 读取各 completed Plan 的 `start_commit` / `end_commit`。需要全局 diff 时，使用最早的 non-null `start_commit` 作为 `<implementation_base_commit>`。

## Full diff
自行运行：`git diff <implementation_base_commit>..HEAD`，并按 execution-state 中每个 Plan 的 `start_commit..end_commit` 复核分 Plan 变更。

## Changed files
自读 `.codex/multi-model-workflow/pack-returns/<run_id>/` 目录下各 pack JSON 的 `changed_files` 字段，合并去重（带 pack ownership 标注）。

## Plan completion summary
| Plan | Plan Impl Review verdict | Repair rounds | Packs | Release gate |
自读 `.codex/multi-model-workflow/review-registry/` 目录下各 plan-impl-review JSON 获取 verdict 和 repair rounds。

## Pack completion summary
| Pack | Plan | Worker verdict | Verified behaviors | Open Items |
自读 `.codex/multi-model-workflow/pack-returns/<run_id>/` 目录下各 pack JSON 获取。

## Contract baseline
自读 `docs/orchestrate/plans/<slug>/` 目录下各 plan 文件的 `## Contract anchors` 节（若有合同边界则列出所有 boundary types）。

## Mockup baseline（与 design doc 同等权威）
docs/orchestrate/mockups/<slug>/（如有 UI 工作）
**Reviewer 必须 Read mockup 目录中的文件**，对照实现代码和设计文档中 `## UI / UX 状态` 的视觉规格表，验证实现与 mockup 的视觉一致性。不能只看文字描述——mockup 文件是视觉约束的权威源头。

## 发布风险和人工门禁
自读 `docs/orchestrate/plans/<slug>/` 目录下各 plan 文件的 `## 发布风险` 和 `AFK / HITL` 节。

## Validation commands
自读 `docs/orchestrate/plans/<slug>/` 目录下各 plan 文件的 `Verification commands` 节，逐条运行。

## Review angles

重要：每个 Plan 已独立通过 Plan Implementation Review（含 spec compliance + code quality + cross-pack coherence）。
不要重新审查 Plan 内部已验证的行为。聚焦以下三个层面：

### 1. Regression Sweep
从 starting commit 读完整 diff。跑完整测试套件。识别：
- 跨 pack 回归：pack A 的改动是否破坏 pack B 的行为或既有功能
- 既有功能回归：diff 是否破坏了 starting commit 时已有的功能
- 测试套件回归：全部测试是否通过

### 2. Intent Coverage
从 source design 和 mockup（Read mockup 文件，不只看文字描述）提取每条可验证 intent。对照 plan/pack completion summary 标出：
- covered by plan impl review — 已被 Plan Implementation Review 验证，确认 merge 后证据仍有效（1 行确认）
- gap intent — 落在 Plan 之间缝隙，做完整验证
- implementation gap — 设计合理，代码没做到
- design gap — 设计承诺不可实现或遗漏约束
- context gap — 需要术语 / owner / UI target 确认
- unverifiable — 环境 / 账号 / 生产 gate 缺失

### 3. Cross-Plan Integration
只检查**跨 Plan** 的集成（Plan 内跨 Pack 已由 Plan Implementation Review 的 Cross-Pack Coherence 覆盖）：
- Cross-plan contract anchors：逐行读取 `docs/orchestrate/design/<slug>.md` 的 `## Cross-Plan Contract Anchors` section，用 `git diff <implementation_base_commit>..HEAD` 验证 producer / consumer / ownership 是否在合并结果中成立
- Shared contract surface：跨 Plan 的 Pydantic model / schema_version / API 是否一致
- Migration 顺序：跨 Plan 的 migration 执行顺序是否正确
- Import 关系：跨 Plan 的 import 是否循环
- 状态竞争：跨 Plan 并发访问共享 state 是否安全
- UI 集成（如有）：跨 Plan 的页面集成效果

如果所有 Plan 之间没有共享 contract / migration / state surface，
Cross-Plan Integration 降级为确认独立性的 1 行声明。

Final Review 发现跨 plan 合同需要实现层修复时，返回 `NEEDS_EXECUTION`，并列出 affected plans、affected packs、连接面、producer / consumer 断点和必须重跑的验证。

## Calibration
**不要信任 plan/pack completion summary——独立验证。** Worker 和 Plan Implementation Review 可能遗漏了跨 Plan 交互问题、遗漏了 gap intent、或对已验证行为的判断在 merge 后不再成立。你的 review 必须基于代码和测试事实。

只标记会导致实际问题的 issue。每个 finding 必须有 evidence。
Plan Implementation Review 已验证且 regression sweep 确认 intact 的行为——不是 finding。
措辞、风格偏好、nice-to-have 建议——不是 finding。

## Return Contract
### Verdict
pass / blocked / needs repair / needs context
### Evidence
- 实际检查过的 files / docs / tests / commands
### Result
Regression Sweep:
Critical:
Important:

Intent Coverage:
通过: X / Y
Gap intents verified:
Covered by plan impl review (confirmed intact):
Implementation Gaps:
Design Gaps:
Context Gaps:
Unverifiable:

Cross-Plan Integration:
Critical:
Important:
NEEDS_EXECUTION:

Release Risk:
Blockers:
Manual verification:
Rollback concerns:

Phase Summary:
可以完成 / 阻塞
Disposition required:
### Verification
### Open Items
```

### Baseline 2：Independent Code-Level Audit

独立第二视角对最终实现做正确性、回归和集成审查。两个 baseline 角度互不重叠——Baseline 1 聚焦 design intent 和跨 pack 完整性，Baseline 2 聚焦代码级正确性和安全性。

Review prompt 写入 `.codex/multi-model-workflow/review-prompts/final-review-baseline-2.md`：

```markdown
## Scope
Independent code-level audit for a completed implementation.
All Plans have individually passed Plan Implementation Review.
You are the second reviewer — your perspective is independent of Baseline 1.

## Starting commit
从 `.codex/multi-model-workflow/execution-state-<run_id>.json` 读取各 completed Plan 的 `start_commit` / `end_commit`。需要全局 diff 时，使用最早的 non-null `start_commit` 作为 `<implementation_base_commit>`。

## Full diff
自行运行：`git diff <implementation_base_commit>..HEAD`，并按 execution-state 中每个 Plan 的 `start_commit..end_commit` 复核分 Plan 变更。

## Source design
docs/orchestrate/design/<slug>.md（已通过 Design Review）

## Plans（已通过 Plan Review）
自行运行 `ls docs/orchestrate/plans/<slug>/` 获取所有 plan 文件列表，逐个自读。

## Plan completion summary
| Plan | Plan Impl Review verdict | Repair rounds | Packs | Release gate |
自读 `.codex/multi-model-workflow/review-registry/` 目录下各 plan-impl-review JSON 获取。

## Pack completion summary
| Pack | Plan | Worker verdict | Verified behaviors |
自读 `.codex/multi-model-workflow/pack-returns/<run_id>/` 目录下各 pack JSON 获取。

## Review steps

对 starting commit 到 HEAD 的完整 diff 做以下审查：

1. **Correctness**：逻辑错误、off-by-one、null/undefined 处理、类型不匹配、边界条件。
2. **Regression**：变更是否破坏既有功能。跑完整测试套件并报告结果。
3. **Security**：injection、auth bypass、敏感数据泄漏、insecure defaults、OWASP top 10。
4. **Integration**：跨文件变更是否协调一致；模块间接口是否一致。
5. **Design alignment**：实现是否匹配 design doc 的 stated intents。
6. **二阶故障**：如果 A 失败，B 是否优雅处理（error propagation、retry、rollback）。
7. **Edge cases**：空状态、错误路径、retry/rollback、竞态、测试未覆盖的边缘场景。
8. **Forbidden shortcuts**（以下默认是 finding；影响验收/数据/权限/账务/runtime/发布时是 Critical）：
   · bare dict 作跨模块长期合同
   · route/host 内临时拼 nested dict 绕过正式 contract
   · 新增 route-local schema/helper 而不放 domain service/shared contract
   · public API 返回 dict[str, Any]
   · silent unknown-field drop / extra=allow 无版本策略
   · 直接写 JSONB/SQLite JSON 不注册不走 validator
   · 新 DB 字段没有 migration/repository/read model/回归测试
   · 新 port/command/chargeable action/capability 没进 registry/catalog
   · 测试 mock 仓库内部业务模块
   · helper 只为绕过边界而存在

## Calibration
**不要信任 worker 的报告和 Plan Implementation Review 结论——独立验证。** 代码可能在 merge 后产生新问题，测试可能不覆盖你正在审查的边界情况。你的审计必须基于代码事实。

只标记会导致实际问题的 issue。每个 finding 必须有 evidence。
Plan Implementation Review 已验证的代码质量问题——不再重复。
措辞、命名偏好、nice-to-have 建议——不是 finding。

## Return Contract
### Verdict
pass / blocked / needs repair / needs context
### Evidence
- 实际检查过的 files / docs / tests / commands
### Result
Code-Level Audit:
Critical:
Important:
低置信度观察:

Disposition required:
### Verification
### Open Items
```

## Step 5：并行提交

两个 baseline 可同时提交（两个 `codex_reviewer` subagent）。Budget 消耗 2。

## Coordinator 端最小职责

Coordinator 在派发时只需完成以下动作，其余由 Reviewer 自读：

1. 写 `DISPATCH_ENVELOPE`，填入 `run_id`、`gate`（`final-review-baseline-1` / `final-review-baseline-2`）、`review_intent: "baseline"`。
2. 在 `Source design:` 中列出 design 文件路径（reviewer 自读全文和 diff）。
3. 写两个 review-prompts 文件，分别运行 `dispatch-review.sh validate`，并行 `spawn_agent(agent_type="codex_reviewer")`，再用 `dispatch-review.sh record` 保存两个 agent id。
4. 用 `wait_agent` 等待两个 reviewer final message，保存各自 review-results，再分别运行 `complete-review-dispatch.sh`；complete 成功后 `close_agent` 释放容量，进入 Steps 6-8 disposition 流程。

---
> **下一步**：两个 baseline 提交后 → Steps 6-8（final-review-disposition.md）。
