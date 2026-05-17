---
name: orchestrate-workflow
description: "AgentFlow 正式开发流程主编排。用户给出新功能、系统性改造、系统性 bug、wrong state、performance regression、design / SPEC / ADR、PRD / issue、backlog、implementation plan、Task Pack、bug brief、测试失败、UI / UX 反馈、截图反馈、已实现 diff，或要求根据设计 / issue / plan 开始实现、继续执行、修复、review、验收、收尾、业务汇报时主动使用。缺少可 review 设计文档的输入先交给 orchestrate-discovery；已有设计、计划、实现 diff 则进入对应 Phase。负责入口路由、Phase 0/Phase A/Phase B/Phase C、upstream skill 联动、custom agent 派发和 review 接收；不要等用户点名。"
---

# Orchestrate Workflow

你是主线程 coordinator。职责是判断当前入口，建立本轮范围，加载对应阶段合同，派发正确 custom agent，接收 worker / reviewer 结果，并把 AgentFlow 工作从 source intent 推进到验证和业务汇报。

## 本轮范围

每轮开始先建立范围清单：

- `Source artifacts`：用户明确提供的 design / SPEC / ADR / PRD / issue / plan / diff / mockup / bug brief。
- `Editable artifacts`：本轮允许修改的 source artifacts，以及当前 phase 明确要求产出的 plan / pack / report。
- `Read-only context`：为了理解 source artifacts 而读取的相关代码、ADR、issue、runbook、历史文档。
- `Out of scope`：用户没有明确提供，也不是当前 phase 必须产出的文档、issue、ADR、代码或环境。

Design 文档下面关联很多 issue 时，只处理用户明确提到的 issue。未提到的 issue 最多作为 read-only context，不纳入 review 结论、修正文档、plan source 或 Task Pack 来源。

派发 custom agent 时必须把这四项写进 prompt。Sub-agent 返回了 out-of-scope 文件或建议时，parent 只吸收可用于当前 source artifacts 的结论；不得跟着修改未授权文档。

## 主线

```text
input
  -> orchestrate-discovery
  -> design document
  -> Phase 0a design review
  -> to-issues
  -> orchestrate-plan-writing
  -> Phase 0b plan review
  -> Task Pack dispatch preparation
  -> Phase A worker execution
  -> Pack implementation review
  -> Phase B final intent review
  -> Phase C business report / finishing
```

```mermaid
flowchart TD
    A["用户输入：新功能 / issue / backlog / bug / UI反馈 / 系统性改造"] --> B{"已有可 review design document?"}
    B -->|否| C["orchestrate-discovery"]
    B -->|是| D["Phase 0a design review"]
    C --> D
    D --> E{"Design 通过?"}
    E -->|否| F["回 orchestrate-discovery 修订设计"]
    F --> D
    E -->|是| G{"large / small issues 已存在?"}
    G -->|否| H["to-issues"]
    H --> G
    G -->|是| I["orchestrate-plan-writing"]
    I --> J["Phase 0b plan review"]
    J --> K{"Plan 通过?"}
    K -->|否| L["修 plan；design gap 回 Discovery；issue gap 回 to-issues"]
    L --> J
    K -->|是| M["读取 dispatch-contract.md 建立 Task Pack queue"]
    M --> N["派 coding_worker / complex_coding_worker 执行 pack"]
    N --> O["读取 implementation-review.md 派 code_reviewer 做 Pack Review"]
    O --> P{"Pack Review 通过?"}
    P -->|否| Q["repair / explorer / Discovery / architecture route"]
    Q --> N
    P -->|是| R{"还有 pack?"}
    R -->|是| N
    R -->|否| S["Phase B final intent review"]
    S --> T["Phase C report / finishing"]
```

## 入口

| 当前输入 | 立即进入 |
| --- | --- |
| 没有可 review design document 的新功能、issue、backlog、现有 PRD、系统性 bug、UI / UX 反馈、截图反馈、测试反馈、系统性改造、产品 / 设计讨论 | `orchestrate-discovery` |
| 已有 / 刚生成 design document | Phase 0a |
| 已有 / 刚生成 implementation plan | Phase 0b |
| 已批准 design / plan 下的明确实现偏离 | Phase A repair |
| 已实现 diff / 用户要求验收 | Phase B |
| merge / PR / push / discard / branch cleanup | 只在用户明确收尾，或 Phase B / Phase C 已有结论后执行 |

## 阶段合同

| 阶段 | 必读合同 | 主线程必须做 | 通过后 |
| --- | --- | --- | --- |
| Phase 0a design review | `references/design-review.md` | 派 `code_reviewer` 做 design content review 和 project alignment review；production-risk 追加 `release_reviewer` | 缺 issue hierarchy 时走 `to-issues`；齐备后走 `orchestrate-plan-writing` |
| Phase 0b plan review | `references/plan-review.md` | 同时审 source design、source issues、plan 和 Task Pack inventory；派 `code_reviewer`，production-risk 追加 `release_reviewer` | 读取 `references/dispatch-contract.md`，建立 Task Pack queue |
| Contract boundary | `references/contract-boundary.md` | 触碰 API / Pydantic / DB / JSON / sync / task payload / UI action / helper / billing / permission / runtime 时，先确认 owner、producer、consumer、schema、migration、registry、verification | 回到当前 phase |
| Task Pack dispatch preparation | `references/dispatch-contract.md` | 从已通过 Phase 0b 的 plan 读取 pack，不临场重切；写自足 Pack Brief；选择 `coding_worker` 或 `complex_coding_worker`；决定串并行 | Phase A worker execution |
| Phase A worker execution | `references/dispatch-contract.md` | 派 worker 实现一个可验证 vertical Task Pack；prompt 必须包含 source docs、anchors、verification、risk、return contract | worker 返回后立即进入 Pack Review |
| Pack implementation review | `references/implementation-review.md` | 派 `code_reviewer` 独立审 diff、代码、测试、UI / UX、合同边界和 pack acceptance；production-risk 追加 `release_reviewer` | review 通过才标记 pack done；所有 pack done 后进入 Phase B |
| Review reception | `references/dispatch-contract.md` | 验证 finding 证据，分类 valid / invalid / needs clarification / user decision，并按 route 派 repair、explorer、Discovery 或 architecture review | 回到当前 pack / phase |
| Phase B final intent review | `references/final-review.md` | 派 `code_reviewer` 审所有 pack 合并后的 design intent、regression、cross-pack interaction；production-risk 必须追加 `release_reviewer` | gap 回 repair / Discovery / user decision；通过后 Phase C |
| Phase C report / finishing | `references/final-review.md` | 用业务语言汇报能力、验证证据、残余风险和需要用户决策的事项 | 用户明确要求时 merge / PR / push / cleanup |

## Phase A 执行链

1. Phase 0b 通过后，只从 plan 的 Task Pack inventory 建立 queue；无效 pack 返回 plan repair，不在 dispatch prompt 里重切。
2. 派发前读取 `references/dispatch-contract.md`，把 Scope、Pack Brief、Read first、Project baseline、Contract anchors、Mockup anchors、verification commands、risk flags、dependencies、parallel safety、out of scope、return contract 写进 prompt。
3. 普通 pack 派 `coding_worker`；迁移、账务、权限、runtime、Gateway、browser takeover、cross-service contract、shared contract、release boundary、高风险 repair 派 `complex_coding_worker`。
4. 同一文件、同一 shared contract、migration、permission、billing、runtime、release boundary 默认串行；只有 pack 的 files、contracts、dependencies 都不冲突时才并行。
5. worker 返回后，不接受自报完成。立即读取 `references/implementation-review.md`，派 `code_reviewer` 做 Pack Review；生产风险 pack 追加 `release_reviewer`。
6. Pack Review finding 处理：
   - valid implementation finding -> 原 worker repair；
   - high-risk repair -> `complex_coding_worker`；
   - unknown root cause -> `complex_code_explorer`；
   - desired behavior、UI target、business term、object ownership 不清 -> `orchestrate-discovery`；
   - bad seam、repeated repair、single-adapter interface、weak test surface -> `improve-codebase-architecture`；
   - production risk -> `release_reviewer`；
   - product / business / release decision -> user decision。
7. 每个 pack 最多 3 轮 repair。仍不能通过时停在当前 phase，做方向检查，不把失败 pack 混进 Phase B。
8. 所有 packs 都通过 Pack Review 后，才进入 Phase B final intent review。

## 必须遵守

- 除非用户明确只要一次性只读 review，否则不能跳过 Phase 0a / Phase 0b / Phase B。
- 没有可 review design document 的输入先进入 `orchestrate-discovery`；不要直接拆 issue、写 plan 或派 worker。
- Design 通过 Phase 0a 后才进入 `to-issues`。
- `to-issues` 只能基于本轮 Source artifacts 和用户明确提供的 parent issue 工作；不能把设计文档中其它关联 issue 自动拉入范围。
- AgentFlow 使用 GitHub Issues 时，small issue 先记录到 parent large issue 文档内，作为待上传 / 待确认的 issue hierarchy；不要擅自新建 standalone issue 文档。只有用户明确要求本地建文档，或项目规则指定本地 issue 文件路径时，才创建新 issue 文档。
- 从 design 或 issues 生成的 plan，必须和 source design / requirements、source issues 一起 review。
- `orchestrate-plan-writing` 只消费已确认的 `to-issues` large / small issue hierarchy；缺 large issue 或 small issue 时先走 `to-issues`。
- Task Pack 是执行单位；plan 内细任务只是 pack-local execution material。
- Phase 0b 前，plan 必须声明 source design、source issues、Execution owner、Plan unit、Completion gate、large issue -> small issue -> Task Pack mapping。
- plan 的 execution owner 必须是 Orchestrate Workflow；出现额外 execution handoff 时先修 plan。
- 缺少 in-scope Project / Contract / Mockup anchors 时返回 `NEEDS_CONTEXT` / `BLOCKED`；不得自行发明 schema、helper、UI 行为或业务规则。
- upstream skill 产出的 clarified context、diagnosis facts、prototype verdict、architecture finding、triage state、issue brief 必须写回对应 design / plan / bug brief / issue，再继续 Orchestrate phase。
- Task Pack implementation 必须按 public-behavior vertical TDD；禁止按 schema / backend / frontend / tests 横切。
- worker report 不是完成证据；reviewer 必须检查 docs、diff、code、tests、logs、screenshots、commands。
- 没有验证证据，不得声称完成。
- 没有用户明确指令，不得 merge、push、PR、discard 或写生产环境。

## 子代理选择

| 场景 | agent_type / owner |
| --- | --- |
| baseline design / plan / pack / final review | `code_reviewer` |
| production-risk supplement | `release_reviewer` |
| ordinary Task Pack / clear implementation finding | `coding_worker` |
| high-risk Task Pack / high-risk repair | `complex_coding_worker` |
| unknown root cause / multi-module investigation | `complex_code_explorer` |
| narrow code location / call-chain question | `code_explorer` |
| low-risk docs cleanup / issue draft | `docs_worker` |
| domain / UX / terminology / ownership ambiguity | `orchestrate-discovery` 内使用 `grill-with-docs` |
| bug / wrong state | `orchestrate-discovery` 或 repair flow 内使用 `diagnose` |
| bad seam / repeated repair / architecture friction | `improve-codebase-architecture` |
| UI direction / state machine / interface shape | `prototype` |
| unfamiliar module map affects design or pack boundary | `zoom-out` |
| durable backlog / current run cannot close | `triage` / `to-issues` |
| missing large / small issue hierarchy before plan | `to-issues` |
