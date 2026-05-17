# Dispatch Contract

主线程派发 custom agent、接收返回、处理 finding 时读取。

## Dispatch 步骤

1. 写 Scope（见 SKILL.md 模板）。
2. 判断本次属于 baseline review / targeted re-review / release gate / worker / repair / explorer / docs / upstream route。
3. 读当前 phase reference，抽取 prompt payload。
4. 触碰合同边界时读 `contract-boundary.md`，写 Contract anchors。
5. 派 worker 前确认 Git Checkpoint。
6. 包含 Return Contract。
7. 收到结果后执行 Reception Gate。

## Scope 规则

- Source artifacts: 只放用户明确提供或当前 phase 确认的直接输入。
- Editable artifacts: 只放 source artifacts 或当前 phase 要求产出的文档。
- Read-only context: 可参考但不能变成交付范围或 plan source。
- Out of scope: 列出容易误纳入的相关 issue / ADR / 未来能力。
- Issue recording target: small issue 先写回 parent large issue 文档。

## Pack Brief

派 worker 时 prompt 至少包含：

```text
Pack / Issue / Scope / Goal behavior / Implementation tasks /
Owned files / Read first / Contract anchors / Mockup anchors /
Acceptance criteria / Verification commands / Risk flags /
发布风险 / Commit boundary / AFK-HITL / Dependencies /
Parallel safety / Out of scope / Return contract
```

Direct Repair Brief 用同一字段，Pack 写 `Targeted repair`，Issue 写 finding locator 或用户 repair brief。

## Return Contract

所有 sub-agent 使用这些顶层 heading：

```text
### Verdict
pass / blocked / needs repair / needs context

### Evidence
- 实际检查过的 files / docs / tests / commands

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

## Routing Vocabulary

所有 sub-agent 只使用这组 owner 名称：

`parent` / `original worker` / `coding_worker` / `complex_coding_worker` / `code_explorer` / `complex_code_explorer` / `code_reviewer` / `release_reviewer` / `docs_worker` / `orchestrate-discovery` / `orchestrate-plan-writing` / `upstream diagnose` / `upstream zoom-out` / `upstream prototype` / `upstream improve-codebase-architecture` / `upstream triage` / `upstream to-issues` / `user decision`

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

收到 findings 后，主线程用 docs / code / tests / diff / logs 验证证据，逐条给 disposition：

| disposition | 动作 |
| --- | --- |
| accepted | repair / doc / upstream payload → 写明 route 和 targeted re-review scope |
| rejected | 记录反证，不 repair |
| needs evidence | 派 explorer 补证据，补前不 repair |
| duplicate | 链到已有 finding / pack / commit |
| out of scope | 从当前 scope 移出 |
| user decision | 停止，一次只问一个问题 |

冲突按 evidence quality 判断，不按 reviewer 数量投票。

## Review Budget

- `code_reviewer` 是 baseline reviewer；每个 phase 指定的 baseline angles 可并行不可合并。
- `release_reviewer` 只审 release-risk，不替代 baseline review。
- Repair 后默认 targeted re-review；只有 source design / plan / scope / shared contract / migration / permission / billing / runtime baseline 改变时才 full phase review rerun。
- 追加 reviewer 只允许：evidence conflict / 连续 repair 后同类风险仍复现 / release gate / 用户要求。

## Release Gate

**Early release gate**（Phase A 中触发）：migration / deploy order / rollback / manual gate 必须在实现前决定；baseline finding 需先判 release strategy；等 Phase B 会造成不可逆风险。

**Final release gate**（Phase B 后触发）：Final Intent Review 通过后，最终 diff 触碰 migration / billing / permission / runtime / cross-service / deploy order / rollback / manual gate 时派 `release_reviewer`。

多个相邻 high-risk packs 同一发布风险面时合并一次 release-risk review。

## Upstream Route

路由到 upstream skill 前给出 Scope、source artifacts、允许输出和写回目标：

| route | 允许输出 | 写回目标 |
| --- | --- | --- |
| `grill-with-docs` | clarified context / domain decision | domain docs + design document |
| `diagnose` | current/desired behavior / hypotheses / regression target | bug brief / design document |
| `zoom-out` | module map / call chain / boundary context | design / plan anchors |
| `prototype` | prototype verdict / decision artifact | design / plan anchors |
| `improve-codebase-architecture` | architecture finding / affected modules | design / plan anchors |
| `triage` | ready state / AFK-HITL / blocked-by | source issue |
| `to-issues` | confirmed large/small issues | Issue recording target |

## Direction Check

触发条件：同一 finding 经历 2 个 repair rounds / 需追加非 baseline/release 的 reviewer / reviewer findings 互相冲突。方向检查只决定下一步 owner 和 scope，不是新审查。
