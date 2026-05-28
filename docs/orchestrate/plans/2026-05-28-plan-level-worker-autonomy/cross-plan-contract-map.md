# Cross-Plan Contract Map

跨 Plan 共享的合同边界 / 接口 / 文件所有权。

## Contract Surfaces

### DISPATCH_ENVELOPE 字段扩展

| Surface | 类型 | Provider Plan | Consumer Plan(s) | 关键字段 |
| --- | --- | --- | --- | --- |
| `dispatch-envelope-v1.json` 加 `plan_id` | JSON schema | Plan 005 (Pack 5.13) | Plan 005（validate-pack-dispatch.sh, agent-return-handler.sh），所有 dispatch reference | `plan_id: string\|null` |
| `parse-envelope.sh` 加 plan_id 解析 | shell parser | Plan 005 (Pack 5.13) | Plan 005 所有 hook | `PLAN_ID` 输出字段 |

### State Schema 扩展

| Surface | 类型 | Provider Plan | Consumer Plan(s) |
| --- | --- | --- | --- |
| `workflow-state.review_dispositions[]` +`plan_id` +`coordinator_verified_evidence` | JSON schema | Plan 002 (Pack 2.4) | Plan 002 (state.sh), Plan 005 (validate-pack-dispatch.sh) |
| `execution-state.plans[N]` +`worker_agent_id` +`pack_summary` | JSON schema | Plan 002 (Pack 2.5) | Plan 005 (agent-return-handler.sh, state.sh) |

### 文档 Schema 扩展

| Surface | Provider Plan | Consumer Plan(s) |
| --- | --- | --- |
| design.md +`## Review History` +`## Cross-Plan Contract Anchors` +`## Business Summary Inputs` | Plan 002 (Pack 2.1) | Plan 004 (plan-writer-dispatch / final-review-angles 反转) |
| issue.md +`## Design context refs` | Plan 002 (Pack 2.2) | Plan 004 (plan-writer-dispatch 反转) |
| plan.md +`## Plan Review History` +`## Pack Execution Manifest` | Plan 002 (Pack 2.3) | Plan 005 (Worker Loop 自读 Manifest) |

### Worker 自治契约

| Surface | 类型 | Provider Plan | Consumer Plan(s) |
| --- | --- | --- | --- |
| `pack-executor.md` +Worker Loop 段 | sub-agent system prompt | Plan 005 (Pack 5.1) | Plan 005 (validate-pack-dispatch.sh 校验逻辑配合) |
| `pack-executor.md` +Context 自监控段 | 同上 | Plan 005 (Pack 5.2) | Plan 005 (agent-return-handler.sh 处理 need-fresh-worker verdict) |
| `plan-returns/<run_id>/<plan_id>/{plan-return.json, doc-patch.diff, open-items.json}` | run state artifact | Plan 005 (Worker 写) | Plan 005 (agent-return-handler.sh 读) |

### Cross-Plan Contract Anchors 迁移（R1 高风险原子改造）

| Surface | 旧路径 | 新路径 | 迁移 Plan |
| --- | --- | --- | --- |
| `cross-plan-contract-map.md` 内容 | `docs/orchestrate/plans/<slug>/cross-plan-contract-map.md` | `design.md` 内 `## Cross-Plan Contract Anchors` section | Plan 002 (Pack 2.11) |
| `plan-gates.md:56` 读路径 | 同上 | 同上 | Plan 002 (Pack 2.11) |
| `plan-review-dispatch.md:92,112` 读路径 | 同上 | 同上 | Plan 002 (Pack 2.11) |
| `final-review-angles.md:125,182` 读路径 | 同上 | 同上 | Plan 002 (Pack 2.11) |
| `final-review-preconditions.md:15` 读路径 | 同上 | 同上 | Plan 002 (Pack 2.11) |

### merge-brief 与现有文档边界

| Document | merge-brief 关系 |
| --- | --- |
| `scope-<run_id>.md` | 正交（范围契约 vs 合成模型）|
| 单 PR design / plan | 单 PR 视角 vs 跨 PR 合成视角 |
| `workflow-state.json` | 状态机锚（含 cursor.reference 指向 merge-brief 路径）|
| `review-prompts/<gate>.md` | 引用 merge-brief 路径，不复制内容 |

## 合并顺序

1. Plan 001（无依赖，最先）
2. Plan 002（依赖 001）
3. Plan 003（依赖 002 schema 就绪）
4. Plan 004（依赖 003 SKILL 已 lean）
5. Plan 005（依赖 002 schema + 004 dispatch 反转）
6. Plan 006（依赖 005）

## 风险热点

- Plan 002 Pack 2.11（cross-plan-contract-map 迁移）= R1 阻塞性，必须原子改造
- Plan 005 Pack 5.9（agent-return-handler.sh 重写）= 结构性重写，需独立测试 fixture
- Plan 002 Pack 2.6 + Plan 005 Pack 5.12 = state.sh 多子命令变更，需 lock 一致
