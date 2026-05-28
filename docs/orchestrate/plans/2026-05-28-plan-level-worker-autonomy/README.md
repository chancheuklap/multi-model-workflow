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

| Plan | Phase | 标题 | Pack 数 | 风险 | Blocked by |
| --- | --- | --- | --- | --- | --- |
| 001 | 0 | 清理 + dispatch prompt 简化 | 4 | trivial | — |
| 002 | 1 | 文档 schema 字段补全 + Enforcement 机制 | 14 | high | 001 |
| 003 | 2 | SKILL.md 瘦身（~850 行删除）| 5 | normal | 002 |
| 004 | 3 | Dispatch reference 反转（让 sub-agent 自读）| 9 | normal | 003 |
| 005 | 4 | Worker Loop 自治 + agent-return-handler 重写 | 19 | high | 002, 004 |
| 006 | 5+6 | merge-brief 中介文档 + 测试/maturity 同步 | 11 | normal | 005 |

**Total: 62 Pack**（修正后含新增 enforcement / handbook / 兜底 hook / dispatch reference 反转）

## 跨 Plan 合同边界

详见 `cross-plan-contract-map.md`。

## 不走正规 workflow

按用户指令：不走 orchestrate-workflow 正规流程，但保留计划文档的结构性约束（每 Plan 含 Task Pack + Worker 自足字段）。

## Budget

- Plan 总数：6
- Pack 总数：62（见各 Plan 文档统计）
- 该工作本身是 plugin 自我改造，不走 review budget（用户 ad-hoc 决策）

## 设计文档同步状态

本计划集与 design 文档第三轮决策（决策 1-9）+ 9 项 enforcement 机制 + Worker Loop 完整契约对齐。修复版（2026-05-28 第二轮）已落实：
- 决策 2/3/5/6/7 → Plan 005 顶部「决策记录」段 + 各 Pack 实现
- 决策 8 → Plan 006 Pack 6.1 schema 注释
- 决策 9 → 不加 stop-conditions/blocked-report template
- 9 项 enforcement → 全部映射到 Plan 002 / 005 / 006 具体 Pack
- Worker Loop 5 步启动序列 + Repair Mode + Context 自监控 → Plan 005 Pack 5.1 worker-loop.md.tmpl
- 决策 1（取消 prompt 写文件）→ Plan 001 Pack 1.3 + 1.4
