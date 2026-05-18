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

## Upstream Skill 调用协议

路由到 upstream skill 时，parent 使用 `Skill({ skill: "<name>" })` 调用。Skill 内容注入主线程上下文，由 coordinator 直接执行。调用前必须给出 Scope、source artifacts、允许输出和写回目标。

每个 phase skill 的 SKILL.md 直接列出该阶段相关的 upstream skill、触发条件和写回目标。本节只定义通用协议：

- 只消费下游会读取的结果。
- upstream skill 的原始流程还包含发布 issue、改代码、创建长期文档、prototype 文件或 tracker 状态变更时，parent 只在当前 Scope / Issue recording target / editable artifacts 授权范围内执行。
- 完成后必须把 verdict 写回 phase skill 指定的写回目标，再回到当前 Orchestrate 节点。

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

