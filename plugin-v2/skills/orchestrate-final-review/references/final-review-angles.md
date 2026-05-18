# Final Review Angles (Augmented — F4)

## 与 Pack Review 的分工

每个 pack 已经独立通过了 spec compliance + code quality review。Final Review 增加三层 Pack Review 结构性看不到的覆盖：

1. **Regression sweep**（NEW）：读 FULL diff（从 starting commit 到 HEAD）。跑完整测试套件。检查任何 pack 的改动是否破坏另一 pack 的行为或既有功能。这是"全新眼光看全局"的层。
2. **Design intent coverage**（AUGMENTED）：逐条走 design doc 中每个可验证 intent。已被 Pack Review 验证的 intent，确认验证证据在 merge 后仍有效（1 行确认，不做 re-audit）。落在 pack 之间缝隙的 gap intent，做完整验证。
3. **Cross-pack audit**（KEPT）：shared contract surface、migration 顺序、import 循环、状态竞争——不变。

**Final Review 不做的事**：
- 不重新审查单个 pack 内 Pack Review 已验证且 regression sweep 确认 intact 的行为
- 不重新检查 helper placement、命名或单 pack owned files 内的代码质量

## 输入

- Scope + design doc + plan + pack completion summary + starting commit + diff + changed files + mockup + validation commands + 发布风险和人工门禁 + project docs + Contract baseline。

## Dispatch：2 个 baseline `codex-reviewer`（可并行，不合并）

两个 angle 均通过 `codex:codex-rescue --model gpt-5.4` 派发。每次 review 是全新 Codex task。Return Contract 和 Finding Shape 格式见 `dispatch-primitives.md`。

### Baseline 1: Regression Sweep + Intent Coverage + Cross-Pack Audit

Prompt 包含：Read first / Project baseline / Contract baseline / Mockup baseline / design doc / plan / starting commit / diff / pack completion summary（含每个 pack 的 review verdict 和已验证行为）/ 发布风险 / validation commands。

Prompt 必须明确告诉 reviewer：每个 pack 已独立通过 Pack Review。本次重点：

1. **Regression sweep**: 从 starting commit 读完整 diff。跑完整测试。识别跨 pack 回归。
2. **Intent coverage**: 从 design doc 和 mockup 提取每条可验证 intent。对照 pack completion summary 标出：
   - `covered by pack review` — 已被 Pack Review 验证，确认 merge 后证据仍有效。
   - `gap intent` — 落在 pack 之间，做完整验证。
   - `implementation gap` / `design gap` / `context gap` / `unverifiable`。
3. **Cross-pack audit**: shared contract surface、migration 顺序、import 关系、状态竞争。
4. UI 任务：只检查跨 pack 的页面集成效果；单 pack 内的 UI 状态已在 Pack Review 验证。

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

## Gap 分类

- **Implementation Gap**: 设计合理，代码没做到 → worker。
- **Design Gap**: 设计承诺不可实现或遗漏约束 → user decision / 文档修正。
- **Context Gap**: 需要术语 / owner / UI target 确认 → orchestrate-discovery。
- **Unverifiable**: 环境 / 账号 / 生产 gate 缺失 → 写清已验证证据和 manual gate owner。

## Result Payload

不要用 worker self-report 作为通过证据；Final Review 必须以 source design、plan、diff、changed files、verification evidence、mockup / contract anchors 和可运行检查为准。

`### Result` 下使用：

```text
Regression Sweep:
Critical:
Important:

Intent Coverage:
通过: X / Y
Gap intents verified:
Covered by pack review (confirmed intact):
Implementation Gaps:
Design Gaps:
Context Gaps:
Unverifiable:

Cross-Pack Audit:
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

两个 baseline review 通过后，最终 diff 触碰以下任一时派 `codex:codex-rescue --model gpt-5.5`：migration / billing / permission / runtime / cross-service / deploy order / rollback / manual gate / API compatibility。

Release blocker：数据丢失或无法回滚 / 权限绕过 / 账务不一致 / 合同未同步 / registry-migration-catalog 未闭合 / deploy order 导致 401/500 / release gate 无验证证据。
