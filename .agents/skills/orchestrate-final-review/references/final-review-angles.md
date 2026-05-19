# Final Review 增强型审查

> **流程位置**：`orchestrate-final-review` Steps 4-5 · 派发后 → Steps 6-8（`final-review-disposition.md`）

Review lane：派发前先读 `orchestrate-workflow/references/external-review-lanes.md`。默认先用 external Claude subscription runner；失败时回落到 `code_reviewer`。不得调用 `claude -p`，除非用户明确授权 Agent SDK credits / Extra Usage。

## 与 Pack Review 的分工

每个 pack 已经独立通过了 spec compliance + code quality review。Final Review 增加三层 Pack Review 结构性看不到的覆盖：

1. **Regression sweep**（全新层）：读完整 diff（starting commit → HEAD），跑完整测试套件。检查任何 pack 的改动是否破坏另一 pack 的行为或既有功能。这是"全新眼光看全局"的层。
2. **Design intent coverage**（增强层）：逐条走 design doc 和 mockup 中每个可验证 intent。已被 Pack Review 验证的 intent 只做 1 行确认（merge 后证据仍有效）；落在 pack 之间缝隙的 gap intent 做完整验证。
3. **Cross-pack audit**（保留层）：shared contract surface、migration 顺序、import 循环、状态竞争。独立 pack 优化：如果所有 pack 之间没有共享 contract / migration / state surface，Cross-pack audit 降级为确认独立性的 1 行声明。Regression sweep 和 Design intent coverage 仍必须执行。

**Final Review 不重复的事**：
- 不重新审查单个 pack 内 Pack Review 已验证且 regression sweep 确认 intact 的行为
- 不重新检查 helper placement、命名或单 pack owned files 内的代码质量

---

## Step 4：派发 2 个 Baseline Codex Reviewer

两个 baseline 通过 `code_reviewer` 派发。可并行派发，结果不合并——各自独立返回。

### Baseline 1：Regression Sweep + Intent Coverage + Cross-Pack Audit

```
spawn_agent({
  agent_type: "code_reviewer",
  description: "Final Review Baseline 1: Regression + Intent + Cross-Pack",
  prompt: "
    ## Scope
    Final Review for a completed implementation. All Task Packs have individually
    passed Pack Review. Your job is to verify the COMBINED result.

    ## Read first
    <project docs: AGENTS.md / CLAUDE.md, CONTEXT.md, ADRs, relevant SPEC>

    ## Feature slug（从 Scope Contract 读取）
    <YYYY-MM-DD-feature>

    ## Source design
    docs/orchestrate/design/<slug>.md（已通过 Design Review）

    ## Plan
    docs/orchestrate/plans/<slug>.md（已通过 Plan Review）

    ## Issue hierarchy
    docs/orchestrate/issues/<slug>.md

    ## Starting commit
    <commit hash>

    ## Full diff
    git diff <starting_commit>..HEAD

    ## Changed files
    <file list with pack ownership>

    ## Pack completion summary
    | Pack | Worker verdict | Pack Review verdict | Verified behaviors | Repair rounds | Open Items |
    <paste per-pack summary>

    ## Contract baseline
    <contract anchors from plan — all boundary types touched>

    ## Mockup baseline
    docs/orchestrate/mockups/<slug>/（如有 UI 工作）

    ## 发布风险和人工门禁
    <paste from plan>

    ## Validation commands
    <paste from plan — all verification commands>

    ## Review angles

    重要：每个 pack 已独立通过 spec compliance + code quality Pack Review。
    不要重新审查单个 pack 内部已验证的行为。聚焦以下三个层面：

    ### 1. Regression Sweep
    从 starting commit 读完整 diff。跑完整测试套件。识别：
    - 跨 pack 回归：pack A 的改动是否破坏 pack B 的行为或既有功能
    - 既有功能回归：diff 是否破坏了 starting commit 时已有的功能
    - 测试套件回归：全部测试是否通过

    ### 2. Intent Coverage
    从 source design 和 mockup 提取每条可验证 intent。对照 pack completion summary 标出：
    - covered by pack review — 已被 Pack Review 验证，确认 merge 后证据仍有效（1 行确认）
    - gap intent — 落在 pack 之间缝隙，做完整验证
    - implementation gap — 设计合理，代码没做到
    - design gap — 设计承诺不可实现或遗漏约束
    - context gap — 需要术语 / owner / UI target 确认
    - unverifiable — 环境 / 账号 / 生产 gate 缺失

    ### 3. Cross-Pack Audit
    - Shared contract surface：跨 pack 的 Pydantic model / schema_version / API 是否一致
    - Migration 顺序：多个 migration 的执行顺序是否正确
    - Import 关系：跨 pack 的 import 是否循环
    - 状态竞争：并发访问共享 state 是否安全
    - UI 集成（如有）：只检查跨 pack 的页面集成效果

    如果所有 pack 之间没有共享 contract / migration / state surface，
    Cross-pack audit 降级为确认独立性的 1 行声明。

    ## Calibration
    **不要信任 pack completion summary——独立验证。** Worker 和 Pack Review 可能遗漏了跨 pack 交互问题、遗漏了 gap intent、或对已验证行为的判断在 merge 后不再成立。你的 review 必须基于代码和测试事实。

    只标记会导致实际问题的 issue。每个 finding 必须有 evidence。
    Pack Review 已验证且 regression sweep 确认 intact 的行为——不是 finding。
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
    Covered by pack review (confirmed intact):
    Implementation Gaps:
    Design Gaps:
    Context Gaps:
    Unverifiable:

    Cross-Pack Audit:
    Critical:
    Important:

    Release Risk:
    Blockers:
    Manual verification:
    Rollback concerns:

    Phase Summary:
    可以完成 / 阻塞
    Disposition required:
    ### Verification
    ### Open Items
  "
})
```

### Baseline 2：Independent Code-Level Audit

独立第二视角对最终实现做正确性、回归和集成审查。两个 baseline 角度互不重叠——Baseline 1 聚焦 design intent 和跨 pack 完整性，Baseline 2 聚焦代码级正确性和安全性。

```
spawn_agent({
  agent_type: "code_reviewer",
  description: "Final Review Baseline 2: Independent Code-Level Audit",
  prompt: "
    ## Scope
    Independent code-level audit for a completed implementation.
    All Task Packs have individually passed Pack Review.
    You are the second reviewer — your perspective is independent of Baseline 1.

    ## Starting commit
    <commit hash>

    ## Full diff
    git diff <starting_commit>..HEAD

    ## Source design
    docs/orchestrate/design/<slug>.md（已通过 Design Review）

    ## Plan
    docs/orchestrate/plans/<slug>.md（已通过 Plan Review）

    ## Pack completion summary
    | Pack | Worker verdict | Pack Review verdict | Verified behaviors | Repair rounds |
    <paste per-pack summary>

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
    **不要信任 worker 的报告和 Pack Review 结论——独立验证。** 代码可能在 merge 后产生新问题，测试可能不覆盖你正在审查的边界情况。你的审计必须基于代码事实。

    只标记会导致实际问题的 issue。每个 finding 必须有 evidence。
    Pack Review 已验证的代码质量问题——不再重复。
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
  "
})
```

## Step 5：并行派发

两个 baseline 可在同一消息中并行派发（两个 spawn_agent call）。Budget 消耗 2。
