# State Schema

JSON Schema 定义目录，用于验证 multi-model-workflow 运行时状态文档。

## 文件索引

| 文件 | 描述 |
| --- | --- |
| `workflow-state-v1.json` | 主工作流状态（cursor / budget / dispositions / plans） |
| `dispatch-envelope-v1.json` | Agent dispatch envelope（protocol_version / run_id / phase / plan_id / pack_id） |
| `execution-state-v1.json` | Pack 级执行状态（per-pack status / agent_id / commit_sha） |
| `pack-returns-v1.json` | Pack worker 返回结构 |
| `plan-return-v1.json` | Plan worker 返回结构 |
| `open-items-v1.json` | Open items 追加格式 |
| `merge-brief-v1.json` | Multi-PR merge 合成模型中介文档（9 段 schema） |
| `state-transition-matrix.md` | 合法状态转换矩阵文档 |

## merge-brief-v1.json 说明

merge-brief 是 multi-pr-merge route 的**合成模型载体**，文件格式为 Markdown（带 META HTML 注释）：

- 路径：`.claude/multi-model-workflow/merge-brief-<run_id>.md`
- 9 段固定结构：Meta / 参与PR / 正确状态模型 / Conflict Findings / RCA / Resolution Log / Integration Review Pointers / Open Items / Verdict
- 由 `state.sh merge-brief init/stage/verify` 管理 META 结构化字段
- 内容段由 Coordinator 直接 Edit 维护

### Decision 8（写入 schema 注释）

- `conflict_id` per-run（C-001 起编，跨 run 不重用）
- 追加 PR 视为新 run，不在同 brief 增量
- 默认不归档到 `docs/orchestrate/merge-briefs/`，随 worktree 清理一起删
