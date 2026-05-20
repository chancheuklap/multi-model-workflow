# Dispatch Primitives

Coordinator 首次派发 sub-agent 时加载。适用所有 phase 和 route。

## Dispatch Checklist

1. 写 Scope Contract（SKILL.md Step 3）。
2. 判断本次属于 baseline review / targeted re-review / release gate / worker / repair / explorer / docs worker / upstream route。
3. spawn reviewer 前检查 `review-budget.md` 全局预算和 per-phase 规则。
4. 读当前 phase reference，抽取 prompt payload。
5. 触碰合同边界时读 `contract-boundary.md`，写 Contract anchors。
6. worker / reviewer 不 commit；Git Checkpoint 由主线程管理。
7. prompt 必须自足——包含 phase、source docs、anchors、payload、verification、risk flags 和 Return Contract；不要只写"按 reference 做"。
8. 收到结果后按当前 phase reference 的 Reception 做 disposition；没有 disposition 的 finding 不能进入 repair。

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
```

Phase reference 和 agent definitions 可以在 `### Result` 内定义 role-specific payload headings，但不得替换标准顶层 headings。

## Finding Shape

```text
- severity:
  confidence:
  locator:
  evidence:
  impact:
  remediation:
```

## Reception Rules

收到 finding 后，parent 不是传话筒——必须主动验证正确性（读代码、跑测试、对照 source artifacts），然后逐条给 disposition。没有 disposition 的 finding 不能进入 repair。收到 sub-agent 结果后过滤越界建议：out-of-scope 文件不能因为 reviewer 提到就被修改。

### Disposition 定义

| disposition | parent 动作 |
| --- | --- |
| `accepted` | 转成 repair / doc / issue / upstream payload；写明 route、owner、affected artifacts 和 targeted re-review scope |
| `rejected` | 记录反证；不派 repair，不让同一 finding 反复进入 review |
| `needs evidence` | 派 explorer 或让 reviewer 补证据；补证前不 repair |
| `duplicate / already covered` | 链到已有 finding、pack、commit、test 或文档；不新增路线 |
| `out of scope` | 从当前 scope 移出；只有用户授权或项目规则要求时才写 durable issue |
| `user decision` | 停止执行，一次只问一个会改变设计、计划或发布策略的问题 |

冲突按 evidence quality 判断，不按 reviewer 数量投票。

### 修复归属

Disposition 为 `accepted` 后：

- **Phase 0（Design / Plan）**：parent 直接修。Design 和 Plan 是 coordinator 写的，coordinator 拥有完整用户上下文。
- **Phase A/B — 简单修复**（≤ 2 文件、不触碰合同边界、不需新增测试、意图明确）：parent 直接修复，跑验证后调度 targeted re-review。
- **Phase A/B — 复杂修复**：SendMessage 原 worker（异步，等通知）；未启用 Agent Teams 时新建同类 targeted-repair agent，prompt 含 accepted findings + pack brief subset + git diff scope。
- **Phase A/B — 根因不明**：新建 `root-cause-analyst`（始终新建，需要全新视角）。

### SendMessage vs 新建 agent

| 维度 | SendMessage | 新建 agent |
| --- | --- | --- |
| 上下文 | 保留 | 仅 prompt |
| 时序 | 异步（等通知） | 同步（阻塞） |
| 前提 | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` | 无 |
| 适用 | 同 pack review → 修复 | 未启用 / 跨 pack / 新问题 |

派修复前：检查 SendMessage 在工具列表中 → 有则 SendMessage（agentId）→ 无则新建同类 agent。

### Repair 术语

- `repair round`：一轮 = disposition → repair → targeted re-review。
- `targeted re-review`：只重审 accepted findings、repair diff、受影响 source artifacts、contract surface、mockup anchors 和 verification。
- `full phase review rerun`：重新派发该 phase 的 baseline review angles；只有 source design / issue / plan、scope、Task Pack inventory、shared contract、migration、permission、billing、runtime 或 mockup baseline 改变时才允许。

各 phase 写的"最多 N 轮修复"只限制 `repair round`。没有 accepted finding 就不进入 repair，也不触发 targeted re-review。

Repair prompt 只携带 accepted findings，不夹带 rejected、out-of-scope 或 low-confidence observations。Repair 返回后默认只做 targeted re-review。只有 source baseline 改变或 targeted review 发现新 blocker 时，才 full phase review rerun。
