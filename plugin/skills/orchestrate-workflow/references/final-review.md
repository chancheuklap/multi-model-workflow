# Final Review (Phase B + Phase C)

验证所有 pack 合并后是否满足 design intent，确认无 release blocker。

## 输入

- Scope + design doc + plan + pack completion summary + starting commit + diff + changed files + mockup + validation commands + 发布风险和人工门禁 + project docs + Contract baseline。

## Pass 条件

两个 baseline review 通过 + release-risk gate 通过（或不触发）。每个 gap 最多 2 个 repair rounds。Phase B dispatch 总量上限 15。

## 与 Pack Review 的分工

每个 pack 已经独立通过了 spec compliance + code quality review。Final Review **不重复审单个 pack 已验证的内容**（行为正确性、合同闭合、测试质量、helper placement）。

Final Review 只审 Pack Review 看不到的东西：

1. **跨 pack 交互**：pack A 和 pack B 合在一起是否产生新问题（合同冲突、状态竞争、import 循环、migration 顺序）。
2. **Design intent 缝隙**：是否有 design intent 落在 pack 之间的缝隙里，没有任何 pack 覆盖。
3. **合并回归**：所有 pack 合并后，既有功能是否被破坏。

如果所有 pack review 都已通过且 pack 之间没有共享 contract / migration / state surface，Final Review 可以只做 design intent 覆盖核查 + 回归检查，不需要重新读每个 pack 的 diff。

## Dispatch：2 个 baseline `codex-reviewer`（可并行，不合并）

两个 angle 均通过 `codex:codex-rescue --model gpt-5.4` 派发。每次 review 是全新 Codex task。

### Baseline 1: Intent Coverage And Cross-Pack Review

审所有 pack 合并后是否满足 design intent，检查跨 pack 交互和合并回归。

Prompt 包含：Read first / Project baseline / Contract baseline / Mockup baseline / design doc / plan / starting commit / diff / pack completion summary（含每个 pack 的 review verdict 和已验证行为）/ 发布风险 / validation commands。

Prompt 必须明确告诉 reviewer：每个 pack 已独立通过 Pack Review，本次只审跨 pack 交互、intent 覆盖缝隙和合并回归。

步骤：

1. 从 design doc 和 mockup 提取每条可验证 intent。
2. 对照 pack completion summary，标出哪些 intent 已被 Pack Review 验证、哪些可能落在缝隙里。
3. 只对缝隙 intent 和跨 pack 交互写验证方法并运行；已被 Pack Review 验证的 intent 标为 `covered by pack review`，不重复验证。
4. 每条 intent 判定：pass / covered by pack review / implementation gap / design gap / context gap / unverifiable。
5. 跑 changed-files 回归检查。
6. 跨 pack 代码交叉审查：shared contract surface、migration 顺序、import 关系、状态竞争。
7. UI 任务：只检查跨 pack 的页面集成效果；单 pack 内的 UI 状态已在 Pack Review 验证。

### Baseline 2: Independent Code-Level Audit

独立第二视角对最终实现做正确性、回归和集成审查。

Prompt 包含：starting commit / diff scope / design doc / plan / pack completion summary。

步骤：

1. Correctness：逻辑错误、off-by-one、null/undefined 处理、类型不匹配。
2. Regression：变更是否破坏既有功能；跑测试套件并报告结果。
3. Security：injection、auth bypass、敏感数据泄漏、insecure defaults。
4. Integration：跨文件变更是否协调一致；模块间是否有不一致。
5. Design alignment：实现是否匹配 design doc 的 stated intents。
6. 二阶故障：如果 A 失败，B 是否优雅处理。
7. Edge cases：空状态、错误路径、retry/rollback、竞态、测试未覆盖的边缘。

### Gap 分类

- **Implementation Gap**: 设计合理，代码没做到 → worker。
- **Design Gap**: 设计承诺不可实现或遗漏约束 → user decision / 文档修正。
- **Context Gap**: 需要术语 / owner / UI target 确认 → orchestrate-discovery。
- **Unverifiable**: 环境 / 账号 / 生产 gate 缺失 → 写清已验证证据和 manual gate owner。

## Result Payload

不要用 worker self-report 作为通过证据；Final Review 必须以 source design、plan、diff、changed files、verification evidence、mockup / contract anchors 和可运行检查为准。

`### Result` 下使用：

```text
Final Intent Review:
通过: X / Y
Implementation Gaps:
Design Gaps:
Context Gaps:
Unverifiable:

Regression / Cross-Pack Review:
Critical:
Important:

Code-Level Audit:
Critical:
Important:

Release Risk:
Blockers:
Manual verification:
Rollback concerns:

Phase Summary:
可以完成 / 阻塞
Disposition required:
```

每条 finding 必须使用统一 Finding Shape。Final review result 必须能被主线程执行 Reception Gate。

## Release Gate

两个 baseline review 通过后，最终 diff 触碰以下任一时派 `codex-release-reviewer`（via `codex:codex-rescue --model gpt-5.5`）：migration / billing / permission / runtime / cross-service / deploy order / rollback / manual gate / API compatibility。

Release blocker：数据丢失或无法回滚 / 权限绕过 / 账务不一致 / 合同未同步 / registry-migration-catalog 未闭合 / deploy order 导致 401/500 / release gate 无验证证据。

## Reception

- accepted implementation gap → Phase A targeted repair。
- accepted design / context gap → orchestrate-discovery → 必要 Phase 0a / plan。
- accepted plan gap → orchestrate-plan-writing / Phase 0b repair。
- accepted release blocker → complex-pack-executor / user decision → targeted release re-review。

## Phase C Finishing

Phase B 通过后：汇报能力、验证证据和残余风险。未通过时只汇报当前状态和 blocker，不声称完成。只有用户明确要求才 merge / PR / push / cleanup。收尾工作（branch 整理、PR 创建、最终 push）直接在 Phase C 内完成，不交给外部流程。
