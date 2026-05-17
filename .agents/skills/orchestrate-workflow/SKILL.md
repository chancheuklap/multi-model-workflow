---
name: orchestrate-workflow
description: "AgentFlow 正式开发流程主编排。用户给出新功能、系统性改造、系统性 bug、wrong state、performance regression、design / SPEC / ADR、PRD / issue、backlog、implementation plan、Task Pack、bug brief、测试失败、UI / UX 反馈、截图反馈、已实现 diff，或要求根据设计 / issue / plan 开始实现、继续执行、修复、review、验收、收尾、业务汇报时主动使用。缺少可 review 设计文档的输入先交给 orchestrate-discovery；已有设计、计划、实现 diff 则进入对应 Phase。负责 workflow 节点选择、Phase 0/Phase A/Phase B/Phase C、upstream skill 联动、custom agent 派发和 review 接收；不要等用户点名。"
---

# Orchestrate Workflow

你是主线程 coordinator。这个 skill 只做一件事：把当前工作放到正确 workflow 节点，加载该节点对应 reference，派发正确 custom agent，并根据 review / worker 结果推进、回退或阻塞。

## 范围

每轮开始先写清本轮 scope；所有 subagent prompt 都必须携带同一组 scope。

```text
Source artifacts:
Editable artifacts:
Read-only context:
Out of scope:
Issue recording target:
```

- `Source artifacts` 只包含用户明确提供的 design / SPEC / ADR / PRD / issue / plan / diff / mockup / bug brief，以及当前节点已确认的直接输入。
- `Editable artifacts` 只能是 source artifacts，或当前 workflow 节点明确要求产出的 design / plan / pack / report。
- `Read-only context` 只用于理解当前 source artifacts；不能被自动变成 review 结论、plan source 或 Task Pack 来源。
- `Out of scope` 写清容易被误纳入的相关 issue、ADR、未来能力、其它文档或环境。
- AgentFlow 使用 GitHub Issues 时，small issue hierarchy 先写回 parent large issue 文档；未获明确授权不得新建 standalone issue 文档。

## Workflow

```mermaid
flowchart TD
    A["输入：想法 / issue / bug / feedback / design / plan / diff"] --> B{"有可 review design document?"}
    B -->|否| C["orchestrate-discovery"]
    C --> D["Phase 0a Design Review"]
    B -->|是| D
    D --> E{"Design 通过?"}
    E -->|否| C
    E -->|是| F{"large / small issue hierarchy 已确认?"}
    F -->|否| G["to-issues"]
    G --> F
    F -->|是| H["orchestrate-plan-writing"]
    H --> I["Phase 0b Plan Review"]
    I --> J{"Plan 和 Task Pack inventory 通过?"}
    J -->|否| K{"缺口类型"}
    K -->|design gap| C
    K -->|issue gap| G
    K -->|plan gap| H
    J -->|是| L["Phase A Task Pack Execution"]
    L --> M{"所有 pack review 通过?"}
    M -->|否| N{"finding route"}
    N -->|implementation gap| L
    N -->|unknown root cause| O["complex_code_explorer"]
    N -->|domain / UX ambiguity| C
    N -->|architecture friction| P["improve-codebase-architecture"]
    O --> L
    P --> L
    M -->|是| Q["Phase B Final Review"]
    Q --> R{"Final Review 通过?"}
    R -->|否| S{"gap type"}
    S -->|implementation gap| L
    S -->|design / context gap| C
    S -->|user decision| T["User decision"]
    R -->|是| U["Phase C Report / Finishing"]
```

## Workflow 节点

| 节点 | 何时到达 | 必读 reference / skill | 主线程动作 | 下一跳 |
| --- | --- | --- | --- | --- |
| `orchestrate-discovery` | 输入缺少可 review design document，或 review 暴露 design / domain / UX / context gap | `orchestrate-discovery` | 生成或修订 design document；必要时让 Discovery 内部联动 `grill-with-docs`、`diagnose`、`prototype`、`improve-codebase-architecture`、`zoom-out`、`triage` | Phase 0a |
| Phase 0a Design Review | 已有 / 刚生成 design document | `references/design-review.md` | 派 `code_reviewer` 做 design content review 和 project alignment review；production-risk 追加 `release_reviewer` | design gap 回 Discovery；通过后检查 issue hierarchy |
| `to-issues` | Phase 0a 通过，但缺 large / small issue hierarchy，或 issue hierarchy 不可独立验证 | `mattpocock-skills:to-issues` | 基于本轮 source artifacts 生成 / 修正 vertical large issues 和 small issues | `orchestrate-plan-writing` |
| `orchestrate-plan-writing` | design 通过且 issue hierarchy 已确认，或 Phase 0b 暴露 plan gap | `orchestrate-plan-writing` | 生成 / 修复 issue-backed implementation plan；large issue -> plan section，small issue -> Task Pack | Phase 0b |
| Phase 0b Plan Review | 已有 / 刚生成 implementation plan | `references/plan-review.md` | 同时审 source design、source issues、plan、Task Pack inventory；派 `code_reviewer`，production-risk 追加 `release_reviewer` | design gap 回 Discovery；issue gap 回 `to-issues`；plan gap 回 plan-writing；通过后 Phase A |
| Phase A Task Pack Execution | Phase 0b 通过，或已批准 design / plan 下的 implementation gap | `references/dispatch-contract.md`，worker 返回后 `references/implementation-review.md` | 从 plan 读取 Task Pack queue；按风险派 `coding_worker` / `complex_coding_worker`；worker 返回后派 `code_reviewer` 做 Pack Review，production-risk 追加 `release_reviewer`；按 Review Reception 路由 repair / explorer / Discovery / architecture | 全部 pack review 通过后 Phase B |
| Phase B Final Review | 所有 Task Pack review 通过，或用户要求验收已实现 diff | `references/final-review.md` | 派 `code_reviewer` 审最终 design intent、cross-pack interaction、regression；production-risk 必须追加 `release_reviewer` | implementation gap 回 Phase A；design / context gap 回 Discovery；通过后 Phase C |
| Phase C Report / Finishing | Phase B 通过，或用户明确要求收尾 | `references/final-review.md` | 用业务语言汇报能力、验证证据、残余风险和需要用户决策的事项；只有用户明确要求才 merge / PR / push / cleanup | 完成 |
| Contract Boundary | 任意节点触碰 API / Pydantic / DB / JSON / sync / task payload / UI action / helper / billing / permission / runtime | `references/contract-boundary.md` | 确认 owner、producer、consumer、schema、migration、registry、verification；把 anchors 写入 review / worker prompt | 回到当前节点 |

## Phase A 定义

Phase A 不是单个 worker，也不是泛泛“开始实现”。Phase A 只表示：

```text
Task Pack queue
  -> dispatch one vertical pack
  -> worker implementation
  -> Pack Review
  -> repair / reroute until pack passes
  -> next pack
```

Phase A 的派发、Pack Brief、Return Contract、Review Reception 都由 `references/dispatch-contract.md` 管；Pack Review 的检查项由 `references/implementation-review.md` 管。`SKILL.md` 不在这里重复这些细节。

## 硬门禁

- 除非用户明确只要一次性只读 review，否则不能跳过 Phase 0a / Phase 0b / Phase B。
- 没有可 review design document 的输入先进入 `orchestrate-discovery`；不要直接拆 issue、写 plan 或派 worker。
- Design 通过 Phase 0a 后才进入 `to-issues`。
- `to-issues` 只能基于本轮 Source artifacts 和用户明确提供的 parent issue 工作；不能把 read-only context 自动拉入范围。
- `orchestrate-plan-writing` 只消费已确认的 vertical large / small issue hierarchy；缺 large issue 或 small issue 时先走 `to-issues`。
- Task Pack 是执行单位；plan 内细任务只是 pack-local execution material。
- Phase 0b 前，plan 必须声明 source design、source issues、Execution owner、Plan unit、Completion gate、large issue -> small issue -> Task Pack mapping。
- plan 的 execution owner 必须是 Orchestrate Workflow；出现额外 execution handoff 时先修 plan。
- 缺少 in-scope Project / Contract / Mockup anchors 时返回 `NEEDS_CONTEXT` / `BLOCKED`；不得自行发明 schema、helper、UI 行为或业务规则。
- upstream skill 产出的 clarified context、diagnosis facts、prototype verdict、architecture finding、triage state、issue brief 必须写回对应 design / plan / bug brief / issue，再继续当前节点。
- Task Pack implementation 必须按 public-behavior vertical TDD；禁止按 schema / backend / frontend / tests 横切。
- worker report 不是完成证据；每个 worker / repair worker 返回后必须进入 Pack Review。
- 没有验证证据，不得声称完成。
- 没有用户明确指令，不得 merge、push、PR、discard 或写生产环境。

## Custom Agent

| 场景 | agent_type |
| --- | --- |
| baseline design / plan / pack / final review | `code_reviewer` |
| production-risk supplement | `release_reviewer` |
| ordinary Task Pack / clear implementation finding | `coding_worker` |
| high-risk Task Pack / high-risk repair | `complex_coding_worker` |
| unknown root cause / multi-module investigation | `complex_code_explorer` |
| narrow code location / call-chain question | `code_explorer` |
| low-risk docs cleanup / issue draft | `docs_worker` |
