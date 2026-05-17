# Plan Review (Phase 0b)

审 issue-backed plan，确认完整承接 source design 和 source issues，Task Pack inventory 可进入 Phase A。

## 输入

- Scope + source design + source issues + plan + 相关 mockup + project docs + Contract anchors。
- 没有 source design 或 source issues → `needs context`，route discovery 或 to-issues。

## Pass 条件

三个 baseline review 通过 + 无 invalid pack / source mismatch / 虚构路径。最多 2 个 repair rounds。

## Plan Entry Gate（主线程在派 review 前检查）

Plan 必须包含：Source design / Source issues / Execution owner: Orchestrate Workflow / Plan unit / Completion gate / 发布风险和人工门禁 / large→small→pack mapping。

缺 Execution owner 或有额外 handoff → `needs repair`。声称 issue-backed 但缺 issues → `needs context` → to-issues。

## Task Pack Inventory Gate

每个 pack 必须：对应 confirmed small issue / vertical slice 可独立验证 / 有 owned files / 有 verification / 有 Contract anchors（触碰合同时）/ 有 Mockup anchors（UI 时）/ 有 Commit boundary。

不进入 Phase A 的 pack：横切 pack / 前后端分层不能单独验证 / UI 只写"实现 mockup"无状态 / 缺目标行为需 worker 猜 / 多 worker 写同一文件 / 只写 helper 无 public behavior。

## Dispatch：3 个 baseline `codex-reviewer`（可并行，不合并）

三个 angle 均通过 `codex:codex-rescue --model gpt-5.4` 派发。Codex review 无 SendMessage；每次 re-review 是全新 task。

### Baseline 1: Coverage And Task Quality

审 plan 是否覆盖 source design/issues，Task Pack 是否可执行。

检查：intent 覆盖 / issue acceptance 进入 pack / large→small→pack 映射 / read-only context 未误纳入 / mockup 转化 / 含混行为 / scope creep / 过度设计 / 设计不足 / 细 task 短反馈循环 / 依赖真实性 / 分组合理 / 高风险有验证。

Critical：intent 无覆盖 / source intent 不清却直接实现 / pack 不可执行 / 依赖错误 / 缺 Task Pack inventory / mockup 未转化 / 合同缺 anchors。

### Baseline 2: Compliance And Verification

审路径、命令、合同、项目规则是否真实。

逐条验真：文件路径 / mockup / fixtures / 命令存在 / 新文件标 Create / agents.overrides.md 同步 / migration tree / 注册位置 / Pydantic contract / JSON registry / DB 闭合 / helper placement。

Critical：引用不存在的路径 / 违反项目规则 / 允许 bare dict 进入实现 / 高风险缺迁移回滚。

### Baseline 3: Cross-Verification

独立第三视角验证 plan 的正确性和可执行性。用 grep/find 逐条验真 plan 中引用的路径、函数名、类名。

检查：file paths / function names / class names 实际存在 / task descriptions 足够清晰可执行 / tasks 之间无逻辑矛盾 / 无遗漏 task（如改模块未更新测试）/ 无风险假设（假设不存在的 API 或特定 data shape）/ tasks 之间无循环依赖 / 修改同一文件的 tasks 分布在不同 section（merge conflict 风险）/ 隐式顺序依赖未在 plan 标注 / 项目工程规则违反。

Critical：引用不存在的路径或符号 / task 间逻辑矛盾 / 循环依赖 / 关键遗漏 task。

## Result Payload

`### Result` 下使用：

```text
Review: 计划文档审查 - <Coverage And Task Quality / Compliance And Verification / Cross-Verification>
Phase summary: 可执行 / 需修正
设计与 issue 覆盖:
Grep / rg 验真:
Task Pack inventory:
Critical:
Important:
低置信度观察:
Disposition required:
```

Plan finding 必须说明是 plan 自身问题、design-plan mismatch、source design gap、issue-plan mismatch、context ambiguity，还是 architecture friction；source design gap 和 context ambiguity route 给 `orchestrate-discovery`，architecture friction route 给 `improve-codebase-architecture`。Phase 0 plan findings 返回 coordinator；不派 worker 写代码。

## Release Gate

只在 release order / rollback / manual gate 必须提前判定时追加 `codex-release-reviewer`（via `codex:codex-rescue --model gpt-5.5`）。

## Reception

- accepted plan repair → orchestrate-plan-writing 或 coordinator 修。
- accepted design gap → orchestrate-discovery → Phase 0a → plan。
- accepted issue-plan mismatch → to-issues → plan-writing。
- accepted architecture friction → improve-codebase-architecture → 回写后 re-review。

修复后 targeted re-review changed sections + affected packs + 受影响 angle。
