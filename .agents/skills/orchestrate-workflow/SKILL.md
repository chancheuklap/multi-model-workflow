---
name: orchestrate-workflow
description: "正式开发流程主编排。用户给出新功能、系统性改造、系统性 bug、wrong state、performance regression、design / SPEC / ADR、PRD / issue、backlog、implementation plan、Task Pack、bug brief、测试失败、UI / UX 反馈、截图反馈、已实现 diff，或要求根据设计 / issue / plan 开始实现、继续执行、修复、review、验收、收尾、业务汇报时主动使用。缺少可 review 设计文档的输入先交给 orchestrate-discovery；已有设计、计划、实现 diff 则进入对应 Phase。负责 workflow 节点选择、Phase 0 / Phase A / Phase B / Phase C、upstream skill 联动、custom agent 派发和 review 接收；不要等用户点名。"
---

# Orchestrate Workflow

主线程 coordinator。职责：判断 workflow 节点 → 读节点 reference → 构建自足 dispatch prompt → 派 custom agent → 根据返回推进、修复、回流或停止。

## 执行顺序

每次触发：

1. **Entry Gate** → 判断走哪条路线。
2. **Resume Gate** → 已有 gate 通过且 source 未变时，从最近通过 gate 后继续。
3. **Scope** → 写清 Source artifacts / Editable artifacts / Read-only context / Out of scope / Issue recording target。
4. **Git Checkpoint** → 会改文件时处理分支和 dirty files。
5. **Node Reference** → 进入节点前先打开 Reference Map 指定的 reference。
6. **Dispatch** → prompt 必须自足，sub-agent 看不到本 SKILL.md 和 references。
7. **Reception** → 按 `references/dispatch-contract.md` 做 finding disposition 和路由。Coordinator 不是传话筒——必须主动验证 reviewer finding 的正确性（读代码、跑测试、对照 source），然后判断修复归属（见下方修复分流规则）。

## 修复分流规则

Reviewer finding 经 coordinator 验证和 disposition 后，按以下规则决定**谁来修**：

| Phase | 修复归属 | 理由 |
| --- | --- | --- |
| Phase 0a（Design） | **coordinator 直接修** | Design 是 coordinator 写的，coordinator 拥有完整的用户上下文和设计意图 |
| Phase 0b（Plan） | **coordinator 直接修** | Plan 是 coordinator 写的，coordinator 拥有 design 完整上下文 |
| Phase A（Pack Review）— 简单修复 | **coordinator 直接修** | 变更 ≤ 2 个文件、改动意图明确（typo / import / 命名 / 格式 / 缺失 return / 简单逻辑修正）、不需要理解 worker 的实现上下文 |
| Phase A（Pack Review）— 复杂修复 | **继续原 worker** | 涉及多文件联动、需要理解实现上下文、需要新增测试、涉及架构决策 |
| Phase A（Pack Review）— 根因不明 | **新建 `complex_code_explorer`** | 无法确定修复方向，需要独立调查 |
| Phase B（Final Review） | 同 Phase A 分流规则 | Implementation gap 按复杂度分流 |

**Coordinator 直接修的条件**（全部满足才自修，否则派 worker）：
1. 改动范围 ≤ 2 个文件
2. 不触碰合同边界（Pydantic / migration / registry / shared contract）
3. 不需要新增或修改测试
4. 修复意图从 finding 描述即可确定，不需要回读 worker 的实现上下文

## Entry Gate

| 路线 | 条件 | 下一步 |
| --- | --- | --- |
| Answer-only | 只问概念/状态/解释 | 回答后停止 |
| One-shot Review | 只要 review，不要修复 | 写 scope，按对应 review reference 审查 |
| Direct Repair | 已有批准 design/plan/mockup/acceptance/failing test，目标行为清楚 | 按 `dispatch-contract.md` 派 worker，完成后按风险分级决定 review 方式 |
| Formal Orchestrate | 新功能、系统性改造、含混 bug/feedback、缺 design/issue/plan | 进入 Formal Workflow |
| User Decision | 产品/业务/权限/账务/发布策略无法判定 | 一次只问一个问题 |

## Formal Workflow

```mermaid
flowchart TD
    A["输入"] --> B["Entry + Resume Gate"]
    B -->|缺 design| C["orchestrate-discovery"]
    B -->|有 design| D["Phase 0a Design Review"]
    C -->|DISCOVERY_READY / NOT_NEEDED| D
    D -->|"design finding → coordinator 自修"| D
    D -->|design / domain / UX gap| C
    D -->|pass, 缺 issues| E["to-issues"]
    D -->|pass, issues ready| F["orchestrate-plan-writing"]
    E --> F
    F -->|PLAN_CREATED| G["Phase 0b Plan Review"]
    G -->|"plan finding → coordinator 自修"| G
    G -->|design gap| C
    G -->|issue gap| E
    G -->|pass| H["Phase A Execution"]
    H -->|"简单 finding → coordinator 自修"| H
    H -->|"复杂 finding → 继续原 worker"| H
    H -->|needs evidence / unknown root cause| P["code_explorer / complex_code_explorer"]
    P --> H
    H -->|domain / UX ambiguity| C
    H -->|architecture friction| Q["improve-codebase-architecture"]
    Q -->|只影响当前 pack| H
    Q -->|改变 plan anchors| G
    H -->|all packs pass| I["Phase B Final Review"]
    I -->|"简单 gap → coordinator 自修"| H
    I -->|"复杂 gap → 继续原 worker"| H
    I -->|design / context gap| C
    I -->|plan gap| F
    I -->|pass, no release-risk| K["Phase C Finishing"]
    I -->|pass, release-risk| J["release_reviewer"]
    J -->|release blocker| N["complex_coding_worker / User Decision"]
    N -->|resolved| J
    J -->|release gate pass| K
```

## Reference Map

| 节点 | 到达条件 | 必读 | 主线程动作 | 下一跳 |
| --- | --- | --- | --- | --- |
| `orchestrate-discovery` | 缺可 review design document，或 review 暴露 design / domain / UX / context gap | `orchestrate-discovery/SKILL.md` | 生成或修订 design document；必要时联动 `diagnose` / `prototype` / `improve-codebase-architecture` / `zoom-out` / `triage` | Phase 0a |
| Phase 0a | 已有 / 刚生成 design document | `references/design-review.md` | 派 2 baseline `code_reviewer` angles；只在设计期必须判定 release strategy 时追加 `release_reviewer` | design gap → Discovery；pass → 检查 issue hierarchy |
| `to-issues` | Phase 0a 通过，但缺 large / small issue hierarchy | `dispatch-contract.md` Upstream Route | 生成 vertical large issues 和 small issues；写回 Issue recording target | `orchestrate-plan-writing` |
| `orchestrate-plan-writing` | design 通过且 issue hierarchy 已确认，或 Phase 0b 暴露 plan gap | `orchestrate-plan-writing/SKILL.md` | 生成 / 修复 issue-backed plan | Phase 0b |
| Phase 0b | 已有 / 刚生成 plan | `references/plan-review.md` | 派 2 baseline `code_reviewer` angles；审 source design + issues + plan + Task Pack inventory | design gap → Discovery；issue gap → `to-issues`；plan gap → plan-writing；pass → Phase A |
| Phase A | Phase 0b 通过，或 Direct Repair / accepted implementation gap | `references/dispatch-contract.md` + `references/implementation-review.md` | 逐 pack 派 worker → Pack Review；必要时 early release gate | 全部 pack pass → Phase B |
| Phase B | 所有 pack review 通过 | `references/final-review.md` | Final Intent Review + release gate | implementation gap → Phase A；design/context gap → Discovery；plan gap → plan-writing；pass → Phase C |
| Phase C | Phase B 通过且 release gate 不触发或已通过 | `references/final-review.md` | 汇报能力、验证证据和残余风险；只有用户明确要求才 merge / PR / push | 完成或暂停 |
| 合同边界 | 任意节点触碰 API / Pydantic / DB / JSON / sync / billing / permission / runtime | `references/contract-boundary.md` | 确认 owner / producer / consumer / schema / migration / verification；anchors 写入 dispatch prompt | 回到当前节点 |

## Handoff Status

| 来源 | Verdict | 下一步 |
| --- | --- | --- |
| discovery | `DISCOVERY_READY` / `DISCOVERY_NOT_NEEDED` | Phase 0a |
| discovery | `READY_FOR_REPAIR` | Direct Repair |
| discovery | `NEEDS_USER_DECISION` | User Decision |
| discovery | `BLOCKED` | 停止 |
| plan-writing | `PLAN_CREATED` | Phase 0b |
| plan-writing | `NEEDS_DISCOVERY` | discovery |
| plan-writing | `NEEDS_DESIGN_REVIEW` | Phase 0a |
| plan-writing | `NEEDS_ISSUES` | to-issues |
| plan-writing | `NEEDS_TRIAGE` | triage |
| plan-writing | `NEEDS_DIAGNOSIS` | diagnose / discovery |
| plan-writing | `NEEDS_DECISION` | user / prototype |
| plan-writing | `NEEDS_ARCHITECTURE` | improve-codebase-architecture |
| plan-writing | `NEEDS_CONTEXT` | code_explorer / zoom-out |
| review | `pass` | 下一 phase |
| review | `needs repair` | 修复后 targeted re-review |
| review | `needs context` | explorer / discovery |
| review | `blocked` | 停止 |

## Custom Agents

| 场景 | agent |
| --- | --- |
| baseline review (design/plan/pack/final) | `code_reviewer` |
| release-risk gate | `release_reviewer` |
| 普通 Task Pack / 普通 repair | `coding_worker` |
| 高风险 Task Pack / 高风险 repair | `complex_coding_worker` |
| 多模块调查 / unknown root cause | `complex_code_explorer` |
| 窄范围代码问题 | `code_explorer` |
| 低风险文档整理 | `docs_worker` |

## Hard Gates

- 没有验证证据，不得声称完成。
- 没有用户明确指令，不得 merge / push / PR / discard / 写生产环境。
- Formal Orchestrate 没有可 review 的 design document 时先进 Discovery，不跳到 plan / worker。
- Phase 0a / Phase 0b / Phase B 不可跳过（除非 Entry Gate 选择了 Answer-only / One-shot Review / Direct Repair）。
- upstream skill 结论必须写回 design / plan / bug brief，再继续当前节点。

## Phase A 执行循环

```mermaid
flowchart TD
    A["Phase 0b pass"] --> B["读 plan Task Pack inventory"]
    B --> C["派 worker，保存 agent handle"]
    C --> D["worker 返回"]
    D --> E["Pack Review（code_reviewer）"]
    E --> F{"通过?"}
    F -->|needs repair| V["Coordinator 验证 finding"]
    V --> T{"修复分流"}
    T -->|"简单（≤2 文件、意图明确）"| S["Coordinator 直接修复"]
    T -->|"复杂（多文件、需上下文）"| R["继续原 worker（handle）"]
    T -->|"根因不明"| RCA["新建 complex_code_explorer"]
    S --> RE["targeted re-review（code_reviewer）"]
    R --> D2["worker 修复后返回"]
    D2 --> RE
    RCA --> D3["调查结果返回"]
    D3 --> RE
    RE --> F
    F -->|pass + early release gate| G["release_reviewer"]
    G --> H{"release gate pass?"}
    H -->|否| I["release repair / user decision"]
    I --> G
    H -->|是| J["下一 pack 或 Phase B"]
    F -->|pass, no risk| J
```

### 步骤 1：调度 worker

派 `coding_worker`（普通 pack）或 `complex_coding_worker`（高风险 pack）。Prompt 包含 pack 中所有 task 完整文本 + 上下文。**保存 worker 的 agent handle**——后续 repair 需要用它继续同一 agent。

处理状态：
- **pass** → 步骤 2。
- **needs repair** → 正确性问题先处理；观察性意见记下继续。
- **needs context** → 继续原 worker，提供上下文。
- **blocked** → 技术阻塞自主解决（拆 pack / 调度 `complex_code_explorer`）。业务阻塞询问用户。

### 步骤 2：Pack Review

读取 `references/implementation-review.md`，构建 dispatch prompt，派 `code_reviewer`。

处理结果（coordinator 先验证 finding，再按修复分流规则判断）：
- 通过 → pack 完成，下一个 pack。
- accepted finding 且**满足 coordinator 直接修条件**（≤ 2 文件、不触碰合同边界、不需新增测试、意图明确）→ **coordinator 直接修复**，跑验证，修复后派 `code_reviewer` 做 targeted re-review。
- accepted finding 且**不满足直接修条件** → **继续原 worker（用保存的 handle）**，发 findings。worker 保有之前写代码的完整上下文，直接修复。修复后重新派 `code_reviewer` 做 targeted re-review。
- `complex_code_explorer` → 新建调查 agent。修复后重新派 `code_reviewer`。
- `user decision` → 用业务语言询问用户。

**最多 3 轮/pack。** 每轮 = 一次 repair（coordinator 自修或继续原 worker）+ 一次 targeted re-review。

### 并行调度

2+ 独立 pack → 同一消息多个 agent call。全部返回后：
1. 冲突验证：跑完整测试。失败则继续对应 worker 修复。
2. 逐个跑 Pack Review。

### 进度

每 2-3 个 pack 完成后一行 FYI。

## Scope 模板

```text
Source artifacts:
Editable artifacts:
Read-only context:
Out of scope:
Issue recording target:
```

## Git Checkpoint

- 先看 `git status --short --branch`；在 `main` / `master` / release branch 上先创建 `codex/<short-scope>`，除非用户明确要求留在当前分支。
- 区分当前 scope 改动和用户 / 其它线程改动；不要把不属于当前 scope 的 dirty files 一起 stage。
- design / plan repair、通过 Pack Review 的 Task Pack、accepted finding repair、runtime sync 分别提交；按可回退边界划分 commit。
- 子代理默认不 commit；主线程在 review / verification 通过后 stage 相关文件并提交。
- 没有用户明确指令，不 push、merge、开 PR、删分支或丢弃改动。
