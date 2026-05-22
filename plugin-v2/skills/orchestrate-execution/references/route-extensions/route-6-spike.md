# Route 6: Spike

探索性研究路径。产出 throwaway code + verdict，不产出生产代码。

**触发关键词**: spike, 调研, 探索, POC, prototype, 可行性验证, feasibility

**行为差异**（相对 formal route）:

## 目的

Spike 是为回答一个具体问题而存在的。Spike 结束时必须有一个明确的 verdict：
- 方案可行 / 不可行 / 需进一步研究
- 性能可接受 / 不可接受
- 技术限制是 / 否存在

## Phase 简化

- **Discovery 简化**：不写完整设计文档。写一个 1-page spike brief：问题、假设、验证方法、成功标准。
- **skip Plan Review**：spike plan 不需要 review。
- **skip Final Review**：没有生产代码，不需要 Final Review。
- **不触发 release gate**：throwaway 代码不进生产。
- `budget_status = "unlimited"`, `review_total = "unlimited"`, `effort_total = "unlimited"`

## 产出要求

Spike 必须产出以下内容之一：

1. **Verdict 文档**（必须）：写入 `docs/orchestrate/design/<slug>-spike-verdict.md`
   - 问题重述
   - 实验方法
   - 观察到的结果（含 evidence：截图/日志/benchmark）
   - Verdict + 理由
   - 下一步建议

2. **Throwaway code**（可选）：在 spike 分支上。不 merge 到 main。
   - 代码质量不要求（无 TDD，无测试，可以有 TODO/hack）
   - 但必须能跑起来验证假设

## 约束

- Spike 分支名：`spike/<feature>-<date>`
- Spike 不 merge 到 main
- Spike 完成后回到 workflow，用 verdict 指导正式 Discovery
