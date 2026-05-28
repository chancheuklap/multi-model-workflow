# Plan-level Worker 自治 + Document-as-Context 实施计划

**Design source**: `docs/orchestrate/design/2026-05-28-plan-level-worker-autonomy.md`（commit d7f9b96 + 第三轮调研追加章节）

## Phase 顺序约束（严格串行）

```
Phase 0 (清理) → Phase 1 (schema 字段) → Phase 2 (SKILL 瘦身) → Phase 3 (dispatch 反转) → Phase 4 (Worker Loop) → Phase 5 (merge-brief) → Phase 6 (测试 + maturity)
```

**关键依赖**：
- Phase 2/3 删除前，Phase 1 必须完成（否则 sub-agent 自读时拿不到信息）
- Phase 4 Worker Loop 上线前，Phase 1 的 Pack Execution Manifest 字段必须就绪
- Phase 5 与 Phase 2/3 的 multi-pr-merge skill 改造可并行
- Phase 6 测试依赖 Phase 0-5 全部完成

## 计划文档清单

| Plan | Phase | 标题 | 风险 | Blocked by |
| --- | --- | --- | --- | --- |
| 001 | 0 | 清理 + dispatch prompt 简化 | trivial | — |
| 002 | 1 | 文档 schema 字段补全 + Enforcement 机制 | high | 001 |
| 003 | 2 | SKILL.md 瘦身（~850 行删除）| normal | 002 |
| 004 | 3 | Dispatch reference 反转（让 sub-agent 自读）| normal | 003 |
| 005 | 4 | Worker Loop 自治 + agent-return-handler 重写 | high | 002, 004 |
| 006 | 5+6 | merge-brief 中介文档 + 测试/maturity 同步 | normal | 005 |

## 跨 Plan 合同边界

详见 `cross-plan-contract-map.md`。

## 不走正规 workflow

按用户指令：不走 orchestrate-workflow 正规流程，但保留计划文档的结构性约束（每 Plan 含 Task Pack + Worker 自足字段）。

## Budget

- Plan 总数：6
- Pack 总数：~38（见各 Plan 文档统计）
- 该工作本身是 plugin 自我改造，不走 review budget（用户 ad-hoc 决策）
