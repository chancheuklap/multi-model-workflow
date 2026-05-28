# Plan Implementation Review Codex Dispatch Template

> **流程位置**：`orchestrate-execution` Step 8 · 同一 Plan 内所有 Pack 完成后派发

同一 Plan 内所有 Pack 完成 Open Items 处置 + Git Checkpoint 后，派发 **1 个** baseline Codex reviewer 覆盖该 Plan 全部代码变更。

**Read** `plugin/skills/_shared/review-dispatch.md` 并按其格式派发 Codex review。

以下是 review prompt 内容（写入 `.claude/multi-model-workflow/review-prompts/plan-impl-review-N.md`）：

```markdown
## Scope
Review the implementation of Plan N: <plan title>
This plan implements Issue N: <issue title> (a vertical slice of <feature>).
All Task Packs within this plan have been executed and committed.

## Source artifacts
- Plan: docs/orchestrate/plans/<slug>/00N-*.md
- Source design: docs/orchestrate/design/<slug>.md
- Source issue: docs/orchestrate/issues/<slug>/00N-*.md
- Scope Contract: .claude/multi-model-workflow/scope-<run_id>.md

## Pack summary
| Pack | Worker verdict | Repair rounds | Changed files |
自读 `.claude/multi-model-workflow/pack-returns/<run_id>/` 目录下各 pack JSON，汇总此表。

## Aggregate diff
自行运行：`git diff <plan-start-commit>..<plan-end-commit>`（commit hash 从 Scope Contract 的 `plan_start_commit` 字段读取）

## Changed files (all packs combined)
自读 pack-returns JSON 中各 `changed_files` 字段，合并去重。

## Contract anchors
自读 `docs/orchestrate/plans/<slug>/00N-*.md` 中各 pack 的 Contract anchors 段。

## Mockup anchors
自读 plan 文件中各 pack 的 Mockup specs 段（若无 UI work 则跳过此节）。

## Review angles (single integrated review)

### Spec Compliance
验 plan 中所有 pack 的实现是否满足要求：
- 每个 pack 的 acceptance criteria 是否满足
- 每个 pack 的 goal behavior 是否可从代码确认
- pack 之间是否有遗漏的交互行为
- 是否有 missing requirements（设计中有但代码没做到的）
- 是否有 extra/unneeded work（YAGNI）

### Code Quality
验实现是否正确、可维护：
- TDD 纪律：测试测的是 public behavior 而非 mock behavior
- Mock 纪律：mock 只用在外部边界
- 合同纪律：跨边界数据用正式 Pydantic contract
- Pack 间接口一致性：Pack A 暴露的接口是否与 Pack B 消费的一致
- Forbidden shortcuts（同现有列表）：
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

### Cross-Pack Coherence（原 Final Review 的 Cross-Pack Audit 下沉到这里）
验同 Plan 内多个 Pack 合在一起是否协调：
- Shared contract surface：跨 pack 的 Pydantic model / schema_version / API 一致
- Migration 顺序：多个 migration 的执行顺序正确
- Import 关系：跨 pack 的 import 无循环
- 状态竞争：并发访问共享 state 安全
- UI 集成（如有）：跨 pack 的页面集成效果

如果 Plan 中所有 Pack 之间没有共享 contract / migration / state surface，
Cross-Pack Coherence 降级为确认独立性的 1 行声明。

### Contract & Risk
验高风险面是否正确处理：
- Contract anchors 闭合（owner / provider / consumer / verification）
- Migration / registry / catalog 完整
- 发布风险标注准确
- rollback / compatibility 考虑

## Calibration
**不要信任 worker 的报告——独立验证一切。**
只标记会导致实际问题的 issue。
措辞、风格偏好、nice-to-have 建议——不是。
除非有严重缺口，否则 approve。

## Return Contract
### Verdict
pass / blocked / needs repair / needs context
### Evidence
### Result
Plan Implementation Review 结果：
Spec compliance:
Code quality:
Cross-pack coherence:
Contract & risk:
Critical:
  - [Pack N.M] <finding>
Important:
  - [Pack N.M] <finding>
Affected packs:
低置信度观察:
Disposition required:
### Verification
### Open Items
```

Plan Implementation Review finding 必须标注 `[Pack N.M]` 归属。`Affected packs` 字段列出所有涉及 finding 的 Pack 编号，Coordinator 据此路由 repair。

## Coordinator 端最小职责

Coordinator 在派发时只需完成以下动作，其余由 Reviewer 自读：

1. 写 `DISPATCH_ENVELOPE`，填入 `run_id`、`plan_id`、`gate`（`plan-impl-review-N`）、`review_intent: "baseline"`。
2. 在 `Source artifacts:` 中列出 plan 文件路径（reviewer 自读内容）。
3. 写 `review-prompts/<gate>.md`，运行 validate/record 脚本，触发 Codex job。
4. 等待 job 完成后运行 result/complete 脚本，触发 `track-review-budget` hook。
5. 读取 review-results 文件，进入 disposition 流程。

---
> **回到**：SKILL.md Step 9（接收 Review Findings + Disposition）。
