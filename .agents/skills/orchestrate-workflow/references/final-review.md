# Final Review (Phase B + Phase C)

验证所有 pack 合并后是否满足 design intent，确认无 release blocker。

## 输入

- Scope + design doc + plan + pack completion summary + starting commit + diff + changed files + mockup + validation commands + 发布风险和人工门禁 + project docs + Contract baseline。

## Pass 条件

Final Intent Review 通过 + release-risk gate 通过（或不触发）。每个 gap 最多 2 个 repair rounds。Phase B dispatch 总量上限 15。

## Dispatch：1 次 baseline `code_reviewer` 做 Final Intent Review

Prompt 包含：Read first / Project baseline / Contract baseline / Mockup baseline / design doc / plan / starting commit / diff / pack completion / 发布风险 / validation commands。

### Final Intent Review 步骤

1. 从 design doc 和 mockup 提取每条可验证 intent。
2. 为每条写验证方法（pytest / curl / CLI / UI / screenshot / DOM / manual）。
3. 运行能运行的验证；不能运行时说明环境缺口。
4. 每条 intent 判定：pass / implementation gap / design gap / context gap / unverifiable。
5. 跑 changed-files 回归检查。
6. 涉及合同边界时逐项确认 Pydantic / registry / migration / repository / catalog / producer-consumer。
7. 跨 pack 代码交叉审查。
8. UI 任务对照 mockup 检查最终页面。

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

Final Intent Review 通过后，最终 diff 触碰以下任一时派 `release_reviewer`：migration / billing / permission / runtime / cross-service / deploy order / rollback / manual gate / API compatibility。

Release blocker：数据丢失或无法回滚 / 权限绕过 / 账务不一致 / 合同未同步 / registry-migration-catalog 未闭合 / deploy order 导致 401/500 / release gate 无验证证据。

## Reception

- accepted implementation gap → Phase A targeted repair。
- accepted design / context gap → orchestrate-discovery → 必要 Phase 0a / plan。
- accepted plan gap → orchestrate-plan-writing / Phase 0b repair。
- accepted release blocker → complex_coding_worker / user decision → targeted release re-review。

## Phase C Finishing

Phase B 通过后：汇报能力、验证证据和残余风险。未通过时只汇报当前状态和 blocker，不声称完成。只有用户明确要求才 merge / PR / push / cleanup。
