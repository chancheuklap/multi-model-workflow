# Dispatch Contract

本文件在三种时候读取：即将派发 custom agent、接收 worker / reviewer 返回、或经过多轮 repair / compaction 后需要恢复方向。

## Reader Boundary

| 文件 | 读者 | 责任 |
| --- | --- | --- |
| `SKILL.md` | parent coordinator | Phase 路由、escalation gates、reference selection |
| `references/*.md` | parent coordinator | phase-specific checks、pack rules、prompt payloads、finding classification |
| `codex/agents/*.toml` | custom sub-agent | 自足角色纪律、local skill routing、project overlay、return discipline |

Sub-agent 不会自动读取 `SKILL.md` 或 references。References 是 parent 用来抽取 prompt payload 的合同，不是转发给 sub-agent 的说明书。Parent dispatch prompt 必须自足，包含 phase、source docs、anchors、pack / review payload、verification、risk flags、return contract 和 routing vocabulary；不要只写"按 Orchestrate reference 做"。

## Dispatch 步骤

1. 写 Scope Contract。
2. 判断本次属于 baseline review / targeted re-review / release gate / worker implementation / repair / explorer / docs worker / upstream route。
3. 读当前 phase reference，抽取本次 prompt payload。
4. 触碰合同边界时读 `contract-boundary.md`，写 Contract anchors。
5. 派 worker 前确认 Git Checkpoint；worker / reviewer 不 commit。
6. 要求标准 Return Contract。
7. 收到结果后执行 Reception Gate；没有 disposition 的 finding 不能进入 repair。

## Scope Contract

每次 dispatch 前，parent 必须写清：

```text
Scope:
Source artifacts:
Editable artifacts:
Read-only context:
Out of scope:
Issue recording target:
```

规则：

- `Source artifacts` 只包含用户明确提供的文档 / tracker refs / diff，以及当前 phase 已确认的直接输入。
- `Editable artifacts` 只能是 source artifacts 或当前 phase 明确要求产出的 design / plan / pack / report。
- `Read-only context` 可以包含相关 issue、ADR、代码或 runbook，但 sub-agent 只能用来判断当前 source artifacts，不得把它们变成交付范围。
- `Out of scope` 必须明确列出容易被误纳入的相关 issue、ADR、未来能力、其它文档或环境。
- `Issue recording target` 说明 small issue hierarchy 写回哪里。AgentFlow 使用 GitHub Issues 时，先写入 parent large issue 文档；未获明确授权不得新建 standalone issue 文档。

收到 sub-agent 结果后，parent 必须过滤越界建议：out-of-scope 文件不能因为 reviewer 提到就被修改、纳入 plan source 或作为 Task Pack 来源。

## Pack Brief

派 worker 时 prompt 至少包含：

```text
Pack / Issue / Scope / Goal behavior / Implementation tasks /
Owned files / Read first / Contract anchors / Mockup anchors /
Acceptance criteria / Verification commands / Risk flags /
发布风险 / Commit boundary / AFK-HITL / Dependencies /
Parallel safety / Out of scope / Return contract
```

Formal Orchestrate 的 Pack Brief 必须来自已通过 Phase 0b 的 plan。无效 pack 先修回 plan，不在 dispatch prompt 里临场重切。

Direct Repair Brief 用同一字段：

- `Pack` 写 `Targeted repair`。
- `Issue` 写 accepted reviewer finding、failing test、批准 design / plan / mockup / acceptance 的 locator，或用户明确 repair brief。
- `Implementation tasks` 只写修复 accepted finding 或 failing behavior 所需步骤；不临场扩展 issue hierarchy。
- 缺目标行为、合同边界、UI target 或验收口径时，返回 Discovery / user decision，不让 worker 自行决定。

### Direct Repair Review 分级

Worker 返回后，按改动风险决定 review 方式：

| 条件 | review 方式 |
| --- | --- |
| 不触碰合同边界、不改 shared contract / migration / permission / billing / runtime、不改 public API、变更 ≤ 3 个文件且全部是 UI / copy / config / style / test fix | coordinator 自检：读 diff、跑 verification、确认 acceptance → 不派 reviewer |
| 上述条件任一不满足 | targeted Pack Review（派 `code_reviewer`） |
| 触碰 migration / billing / permission / runtime / release boundary | targeted Pack Review + 检查是否触发 early release gate |

Coordinator 自检必须实际读 diff 和跑验证命令，不能只看 worker self-report。自检不通过时仍派 reviewer。

## Return Contract

所有 sub-agent 使用这些顶层 heading：

```text
### Verdict
pass / blocked / needs repair / needs context

### Evidence
- 实际检查过的 files / docs / tests / commands / screenshots

### Result
- 本次 changed / found / reviewed 的内容

### Verification
- 已运行的 commands 和结果
- 未运行的 checks 和原因

### Open Items
- parent 必须处理的问题

### Routing
- Suggested next owner
```

References 和 agent TOMLs 可以在 `### Result` 内定义 role-specific payload headings，但不得替换标准顶层 headings。

## Routing Vocabulary

所有 sub-agent 只使用这组 owner 名称：

| owner | 使用条件 |
| --- | --- |
| `parent` | coordinator 归并证据、更新进度、继续下一 phase |
| `original worker` | accepted implementation finding 明确属于刚返回的 worker scope |
| `coding_worker` | 普通 repair / implementation，改动范围清楚 |
| `complex_coding_worker` | migration、billing、auth、permission、runtime、shared contract、release boundary 或高风险 repair |
| `code_explorer` | 窄范围文件、符号、调用链、测试入口问题 |
| `complex_code_explorer` | unknown root cause、多模块调查、历史行为或迁移链路 |
| `code_reviewer` | baseline design / plan / pack / final review，或 targeted re-review |
| `release_reviewer` | early / final release-risk gate；不能替代 baseline review |
| `docs_worker` | parent 明确授权的低风险文档整理或 issue 文案草稿 |
| `orchestrate-discovery` | design / domain / UX / terminology / ownership / target-state ambiguity |
| `orchestrate-plan-writing` | reviewed design 和 confirmed issue hierarchy 已存在，但 plan 自身需要生成或修复 |
| `upstream diagnose` | 缺 feedback loop、复现、hypothesis 或 regression target |
| `upstream zoom-out` | 需要 module map、call chain、boundary context 或 test / config entrypoint |
| `upstream prototype` | 状态行为、interface shape 或 UI direction 需要 throwaway proof |
| `upstream improve-codebase-architecture` | bad seam、single-adapter interface、repeated repair、weak test surface |
| `upstream triage` | issue ready state、AFK / HITL、blocked-by 或 label/status 不清 |
| `upstream to-issues` | large / small issue hierarchy 缺失或 small issue 不能独立验证 |
| `user decision` | 产品、业务、账务、权限、UX 或发布决策无法从 source artifacts 判定 |

不要返回自由 owner 名称。需要组合路线时写主要 owner，并在 `### Open Items` 说明 parent 应携带的 payload。

## Finding Shape

```text
- severity:
  confidence:
  locator:
  evidence:
  impact:
  remediation:
  routing:
```

## Reception Gate

收到 reviewer finding 后，parent 必须用 docs、code、tests、diff、logs、screenshots、command output 验证证据，并逐条给 disposition。没有 disposition 的 finding 不能进入 repair。

先统一三个词：

- `repair round`：只针对 accepted findings 的闭环，一轮 = disposition → repair → targeted re-review。
- `targeted re-review`：只重审 accepted findings、repair diff、受影响 source artifacts、contract surface、mockup anchors 和 verification。
- `full phase review rerun`：重新派发该 phase 的 baseline review angles；只有 source design / issue / plan、scope、Task Pack inventory、shared contract、migration、permission、billing、runtime 或 mockup baseline 改变时才允许。

各 phase 写的"最多 N 轮修复"只限制 `repair round`，不是要求或授权反复重跑完整 review。没有 accepted finding，或 finding 被判为 rejected / out of scope / duplicate，就不进入 repair，也不触发 targeted re-review。

| disposition | parent 动作 |
| --- | --- |
| `accepted` | 转成 repair / doc / issue / upstream payload；写明 route、owner、affected artifacts 和 targeted re-review scope |
| `rejected` | 记录反证；不派 repair，不让同一 finding 反复进入 review |
| `needs evidence` | 派 `code_explorer` / `complex_code_explorer` 或让 reviewer 补证据；补证前不 repair |
| `duplicate / already covered` | 链到已有 finding、pack、commit、test 或文档；不新增路线 |
| `out of scope` | 从当前 scope 移出；只有用户授权或项目规则要求时才写 durable issue |
| `user decision` | 停止执行，一次只问一个会改变设计、计划或发布策略的问题 |

冲突按 evidence quality 判断，不按 reviewer 数量投票。

Accepted finding 路由：

- implementation finding → `original worker`。
- unknown root cause → `complex_code_explorer`。
- module map / call-chain context gap → `code_explorer` / `complex_code_explorer` 或 `upstream zoom-out`。
- high-risk repair → `complex_coding_worker`。
- 满足 early / final release gate → `release_reviewer`。
- accepted release blocker → `complex_coding_worker` 或 `user decision`；修复后只做 targeted release re-review。
- domain / UX / terminology / ownership ambiguity → `orchestrate-discovery`。
- bad seam → `upstream improve-codebase-architecture`。
- UI / state / interface direction → `upstream prototype`。
- low-confidence / wrong-context → 用证据退回。

Repair prompt 只携带 accepted findings，不夹带 rejected、out-of-scope 或 low-confidence observations。Repair 返回后默认只做 targeted re-review。只有 source design / issue / plan 被修改、scope 扩大、shared contract / migration / permission / billing / runtime surface 改变，或 targeted review 发现新 blocker 时，才 full phase review rerun。

## Review Budget

### 全局预算

一个 Formal Orchestrate 的 review dispatch 总数有预算。超出预算时强制 Direction Check，由 coordinator 判断是继续、简化还是停止。

| 组成部分 | 预算 |
| --- | --- |
| Phase 0a baseline | 2 |
| Phase 0b baseline | 2 |
| Phase A Pack Review | 每个 pack 1 |
| Phase B Final Review | 1 |
| Release gate | 最多 2（early + final 合并同发布风险面） |
| Repair headroom | baseline 总数 × 1.0 |

**公式**：预算 = 2 + 2 + N + 1 + 2 + (5 + N) = 2N + 12

示例：4 个 pack → 预算 = 11 + 9 = 20。实际 happy path 用 11，留 9 给 repair。

**刹车机制**：累计 review dispatch 达到预算的 80% 时，coordinator 必须做 Direction Check，重述当前 phase / 剩余工作 / 累计 findings / 是否继续。超过预算时停止并报告用户。

### Per-phase 规则

- `code_reviewer` 是 baseline reviewer；每个 phase 指定的 baseline angles 可并行不可合并。
- `release_reviewer` 只审 release-risk，不审普通代码质量、设计完整性或 plan coverage。
- `production-risk` risk flag 先进入 plan 的"发布风险和人工门禁"；真正 dispatch trigger 是 early release gate 或 final release gate。
- Repair 后默认 targeted re-review；只有 source design / plan / scope / shared contract / migration / permission / billing / runtime baseline 改变时才 full phase review rerun。
- 追加 reviewer 只允许：evidence conflict / 连续 repair 后同类风险仍复现 / release gate / 用户要求。
- 多个相邻 high-risk packs 属于同一发布风险面时合并一次 release-risk review。
- release blocker 修复后只做 targeted release re-review；不重跑 baseline review，除非修复改变 source design / plan / shared contract / migration / permission / billing / runtime baseline。
- 每次 spawn reviewer 前先数清本 phase 已经派过的 baseline reviews、targeted re-reviews 和 release gates；如果下一次 spawn 不属于这三类，先做方向检查，不用 review 填补不确定感。

## Release Gate

**Early release gate**（Phase A 中触发）：

- 迁移 / deploy order / rollback / manual production gate 必须在实现前决定。
- baseline finding 暴露的问题必须先判定 release strategy 才能修。
- 等待 Phase B 才审会造成不可逆数据、权限、账务或 runtime 风险。
- 用户明确要求。

**Final release gate**（Phase B 后触发）：Final Intent Review 没有 implementation / design / context / plan blocker 后，如果最终 diff 触碰 migration、billing、permission、runtime、cross-service contract、deploy order、rollback 或 manual production dependency，才派 `release_reviewer`。

## Upstream Route

路由到 upstream skill 前，parent 必须给出 Scope、source artifacts、允许输出和写回目标。只消费下游会读取的结果：

| route | 允许输出 | 写回目标 |
| --- | --- | --- |
| `grill-with-docs` | clarified context、resolved term、domain decision、ADR / SPEC / GUIDE need | domain docs 和 design document |
| `diagnose` | current / desired behavior、reproduction / symptom、falsifiable hypotheses、key interfaces、regression target | bug brief、design document 或 Direct Repair Brief |
| `zoom-out` | module map、call chain、boundary context、test / config entrypoints | design document、plan anchors、Direct Repair Brief 或 explorer brief |
| `prototype` | prototype question、verdict、decision artifact、validated / rejected option | design document、plan anchors 或 issue brief |
| `improve-codebase-architecture` | architecture finding、affected modules、test seam impact、recommended boundary | design document、plan anchors 或 bounded issue candidate |
| `triage` | issue category、ready state、AFK / HITL、blocked-by、issue brief | source issue 或 Issue recording target |
| `to-issues` | confirmed vertical large issues、confirmed vertical small issues、blocked-by、AFK / HITL | Issue recording target；GitHub 项目先写 parent large issue 文档 |

如果 upstream skill 的原始流程还包含发布 issue、改代码、创建长期文档、prototype 文件或 tracker 状态变更，parent 只在当前 Scope / Issue recording target / editable artifacts 授权范围内执行；完成后必须把 verdict 写回上表目标，再回到当前 Orchestrate 节点。

## Durable Handoff Brief

跨会话交接、导出为 issue、或留给以后 agent 处理时，用 durable brief，不要只保存当前文件行号。

```text
Current behavior:
Desired behavior:
Key interfaces:
Acceptance criteria:
Out of scope:
Risk flags:
AFK / HITL:
```

写行为合同，不写"去某文件第 N 行改 X"。UI / UX durable brief 必须保留 mockup path、目标 viewport、关键 states 和允许偏差。如果 durable brief 来自 Discovery domain alignment、prototype 或 architecture review，写明 resolved context、prototype verdict 或 architecture finding。

## Direction Check

经过多个 packs、review rounds、repair loops 或 context compaction 后，先重述：

- 当前 phase / pack。
- 剩余 packs / phases。
- source design intent。
- 累计 findings 和 disposition。
- plan checkbox progress。

触发条件：

- 同一 finding 已经经历 2 个 repair rounds。
- 同一 phase 需要追加不属于 release gate 的非 baseline reviewer。
- 下一次 reviewer spawn 的目的无法写成 baseline review、targeted re-review 或 release gate。
- reviewer findings 互相冲突，且无法用 evidence quality 直接判定。

方向检查只决定下一步 owner 和 scope；不要把它写成新审查。下一步明确时直接继续，不把显然该执行的 repair / targeted re-review 推回给用户。
