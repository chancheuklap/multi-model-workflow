# Coordinator Tools

## Handoff Status

收到 upstream skill verdict 后查此表决定下一步：

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
| plan-writing | `NEEDS_CONTEXT` | code-explorer / zoom-out |
| review | `pass` | 下一 phase |
| review | `needs repair` | 修复后 targeted re-review |
| review | `needs context` | explorer / discovery |
| review | `blocked` | 停止 |

## Upstream Skill 调用

路由到 upstream skill 时，parent 使用 `Skill({ skill: "<name>" })` 调用。Skill 内容注入主线程上下文，由 coordinator 直接执行。调用前必须给出 Scope、source artifacts、允许输出和写回目标。只消费下游会读取的结果：

| Skill 调用 | 允许输出 | 写回目标 |
| --- | --- | --- |
| `Skill: grill-with-docs` | clarified context、resolved term、domain decision、ADR / SPEC / GUIDE need | domain docs 和 design document |
| `Skill: diagnose` | current / desired behavior、reproduction / symptom、falsifiable hypotheses、key interfaces、regression target | bug brief、design document 或 Direct Repair Brief |
| `Skill: zoom-out` | module map、call chain、boundary context、test / config entrypoints | design document、plan anchors、Direct Repair Brief 或 explorer brief |
| `Skill: prototype` | prototype question、verdict、decision artifact、validated / rejected option | design document、plan anchors 或 issue brief |
| `Skill: improve-codebase-architecture` | architecture finding、affected modules、test seam impact、recommended boundary | design document、plan anchors 或 bounded issue candidate |
| `Skill: triage` | issue category、ready state、AFK / HITL、blocked-by、issue brief | source issue 或 Issue recording target |
| `Skill: to-issues` | confirmed vertical large issues、confirmed vertical small issues、blocked-by、AFK / HITL | Issue recording target；GitHub 项目先写 parent large issue 文档 |

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

## Routing Vocabulary

Coordinator 做路由决策时的完整参考。Sub-agent 不输出 routing——coordinator 根据 Verdict + Finding 自行判断：

| owner | 使用条件 |
| --- | --- |
| `parent` | coordinator 归并证据、更新进度、继续下一 phase |
| `original worker` | accepted implementation finding 明确属于刚返回的 worker scope。优先 SendMessage 继续原 agent（保留上下文）；SendMessage 不可用时新建同类 agent |
| `pack-executor` | 普通 repair / implementation，改动范围清楚 |
| `complex-pack-executor` | migration、billing、auth、permission、runtime、shared contract、release boundary 或高风险 repair |
| `code-explorer` | 窄范围文件、符号、调用链、测试入口问题 |
| `complex-code-explorer` | unknown root cause（只读调查）、多模块调查、历史行为或迁移链路 |
| `root-cause-analyst` | unknown root cause（需要调查 + 修复）、测试通过但功能不工作、改 A 坏 B 因果不明 |
| `codex-reviewer` | baseline design / plan / pack / final review，或 targeted re-review（via `codex:codex-rescue --model gpt-5.4`） |
| `codex-release-reviewer` | early / final release-risk gate；不能替代 baseline review（via `codex:codex-rescue --model gpt-5.5`） |
| `docs-worker` | parent 明确授权的低风险文档整理或 issue 文案草稿 |
| `Skill: orchestrate-discovery` | design / domain / UX / terminology / ownership / target-state ambiguity |
| `Skill: orchestrate-plan-writing` | reviewed design 和 confirmed issue hierarchy 已存在，但 plan 自身需要生成或修复 |
| `Skill: diagnose` | 缺 feedback loop、复现、hypothesis 或 regression target |
| `Skill: zoom-out` | 需要 module map、call chain、boundary context 或 test / config entrypoint |
| `Skill: prototype` | 状态行为、interface shape 或 UI direction 需要 throwaway proof |
| `Skill: improve-codebase-architecture` | bad seam、single-adapter interface、repeated repair、weak test surface |
| `Skill: triage` | issue ready state、AFK / HITL、blocked-by 或 label/status 不清 |
| `Skill: to-issues` | large / small issue hierarchy 缺失或 small issue 不能独立验证 |
| `user decision` | 产品、业务、账务、权限、UX 或发布决策无法从 source artifacts 判定 |

不要返回自由 owner 名称。需要组合路线时写主要 owner，并在 `### Open Items` 说明 parent 应携带的 payload。
