# Dispatch Contract

本文件只在即将派发 custom agent、接收 reviewer / worker 结果、或跨上下文恢复方向时读取。

## 文档层级

| 层级 | 读者 | 责任 |
| --- | --- | --- |
| `SKILL.md` | parent coordinator | Phase 路由、escalation gates、reference selection。 |
| `references/*.md` | parent coordinator | phase-specific checks、pack rules、prompt payloads、finding classification。 |
| `codex/agents/*.toml` | custom sub-agent | 自足角色纪律、local skill routing、project overlay、return discipline。 |

References 告诉 parent dispatch prompt 应该包含什么；sub-agents 不会自动读取 references。Parent 必须把 phase、source docs、anchors、pack / review payload、verification、risk flags 和 return contract 写进 dispatch prompt。

## Pack Brief

派 worker 时不要只发 pack 标题。Prompt 至少包含：

```text
Pack:
Issue:
Goal behavior:
Implementation tasks:
Owned files / responsibilities:
Read first:
Contract anchors:
Mockup anchors:
Acceptance criteria:
Verification commands:
Risk flags:
AFK / HITL:
Dependencies:
Parallel safety:
Out of scope:
Return contract:
```

Pack Brief 必须来自已通过 Phase 0b 的 plan。无效 pack 先修回 plan，不在 dispatch prompt 里临场重切。

## 标准 Return Contract

每个 worker / explorer / reviewer / docs dispatch 都必须包含这些顶层 heading：

```text
### Verdict
pass / blocked / needs repair / needs context

### Evidence
- 实际检查过的 files / docs / tests / commands / screenshots
- 关键事实；需要时给 locator

### Result
- 本次 changed、found、reviewed 或 confirmed 的内容

### Verification
- 已运行的 commands 或 checks，以及结果
- 未运行的 checks，以及原因

### Open Items
- parent 必须处理的问题、风险、缺口或决策

### Routing
- Suggested next owner: parent / original worker / coding_worker / complex_coding_worker / complex_code_explorer / code_reviewer / release_reviewer / upstream grill-with-docs / upstream diagnose / upstream prototype / upstream improve-codebase-architecture / upstream triage-to-issues / user decision
```

References 和 agent TOMLs 可以在 `### Result` 内定义 role-specific payload headings，但不得替换标准顶层 headings。

## Finding Shape

Review findings 使用：

```text
- severity:
  confidence:
  locator:
  evidence:
  impact:
  remediation:
  routing:
```

## Review 接收门禁

收到 reviewer finding 后，parent 必须用 docs、code、tests、diff、logs、screenshots、command output 验证证据，并分类：

- `valid`；
- `invalid`；
- `needs clarification`；
- `user decision`。

冲突按 evidence quality 判断，不按 reviewer 数量投票。

路由：

- valid implementation finding -> original worker；
- unknown root cause -> `complex_code_explorer`；
- high-risk repair -> `complex_coding_worker`；
- production risk -> `release_reviewer`；
- domain / UX / terminology / ownership ambiguity -> `grill-with-docs`；
- bad seam -> `improve-codebase-architecture`；
- UI / state / interface direction -> `prototype`；
- low-confidence / wrong-context -> 用证据退回。

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

写行为合同，不写“去某文件第 N 行改 X”。UI / UX durable brief 必须保留 mockup path、目标 viewport、关键 states 和允许偏差。如果 durable brief 来自 grill / prototype / architecture review，写明 resolved context、prototype verdict 或 architecture finding。

## 方向检查

经过多个 packs、review rounds、repair loops 或 context compaction 后，先重述：

- 当前 phase / pack；
- 剩余 packs / phases；
- source design intent；
- 累计 findings 和 disposition；
- plan checkbox progress。

然后从下一个未阻塞 phase 继续。
