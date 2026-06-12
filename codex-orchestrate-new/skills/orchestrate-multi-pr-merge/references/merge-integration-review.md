# Codex 跨 PR 集成审查

> **流程位置**：`orchestrate-multi-pr-merge` Steps 16-18 · 所有冲突解决后（或 explorer 未发现冲突）进入 · 通过后 → Steps 19-22（`merge-completion.md`）

这不是 Plan Implementation Review（审查单个 Plan 的全部 pack），不是 Final Review（审查 design intent coverage）——这是**跨 PR 集成审查**，验证多个 PR 合在一起后系统是否正确。

## Step 16：构造 Codex Dispatch

**Read** `${MMW_PLUGIN_ROOT}/skills/_shared/review-dispatch.md` 并按其格式派发 Codex review。

Review prompt 写入 `.codex/multi-model-workflow/review-prompts/multi-pr-integration-review.md`：

```markdown
## Scope
跨 PR 集成审查。多个并行 PR 来自同一大设计，各自已通过 Final Review。
本次审查验证它们合在一起后是否正确。

## Merge context
读 `.codex/multi-model-workflow/merge-brief-<run_id>.md` 获取：
- 大设计文档路径（你自读该文档）
- PRs included（PR / Branch / 核心行为 / Final Review verdict）
- 冲突解决记录（resolved conflicts + how they were fixed；或 'Explorer 确认无 PR 间冲突'）
- 合同地图（all cross-PR contract surfaces）

## Combined diff
自行运行 `git diff <base-branch>..HEAD`（或对每个 PR branch 分别 diff 后合并）。

## Review angles

### 1. 组合行为正确性
所有 PR 合在一起是否产出大设计描述的正确行为。
每个 PR 各自正确不代表组合正确——关注交互、顺序、依赖。

### 2. 合同一致性
跨 PR 的 Pydantic model / API / DB schema / JSON payload / registry 是否一致。
一个 PR 提供的合同是否被另一个 PR 正确消费。

### 3. 迁移完整性
多个 PR 的 migration 合并后：
- 顺序是否正确
- 是否有遗漏的 migration（PR A 改了 model，PR B 没有对应 migration）
- 回滚是否安全

### 4. 状态一致性
跨 PR 的 shared state 假设是否一致。
并发访问 shared state 是否安全。

### 5. Import / 依赖
合并后是否有循环 import。
依赖版本是否一致。

### 6. 回归
合并所有 PR 后，既有功能是否完好。
跑完整测试套件并报告结果。

### 7. 冲突修复质量（如有）
之前解决的冲突的修复是否正确、完整。
修复是否引入了新问题。

## Calibration
**不要信任各 PR 的 Final Review 结论——独立验证组合行为。** 每个 PR 各自正确不代表组合正确。你的审查必须基于合并后的代码事实，不是各 PR 独立 review 的结论。

只标记会导致实际问题的 issue。每个 finding 必须有 evidence。
单个 PR 内部的代码质量——已在各自 Final Review 中覆盖，不再重复。
措辞、命名、风格——不是 finding。

## Return Contract
### Verdict
pass / blocked / needs repair / needs context
### Evidence
### Result
组合行为:
合同一致性:
迁移完整性:
状态一致性:
Import / 依赖:
回归:
冲突修复质量:
Critical:
Important:
Disposition required:
### Verification
### Open Items
```

## Step 17：接收 + Disposition

**整体 Verdict 前置检查**：reviewer 返回整体 `needs context` 时，Coordinator 补充上下文后重新 dispatch，不进入 per-finding disposition。

**Read** `${MMW_PLUGIN_ROOT}/skills/_shared/disposition-table.md` 并按其 disposition 选项处理 findings。

Multi-PR 增加验证维度：对照大设计文档确认 spec 判断 + 对照冲突解决记录确认修复判断。

`needs evidence` 补证的 explorer 选型 + prompt + 返回契约见上述 disposition-table.md。

**Review 通过** → Step 19（`merge-completion.md`）。

**有 accepted findings** → Step 18。

## Step 18：集成审查修复

修复路由同冲突解决阶段：

**Read** `${MMW_PLUGIN_ROOT}/skills/_shared/repair-routing.md` 并按其流程处理 review findings。

- 简单修复（≤ 2 文件、不碰合同）→ Coordinator 直接修
- 复杂修复 → 派 worker

- 简单修复（≤ 2 文件、不碰合同）→ Coordinator 直接修
- 复杂修复 → 派 worker

修复后由 Coordinator 自验：对照 merge-brief §3（合同地图）/§7（集成审查 7 角度）+ 跑 validation commands；自验通过即闭合，自验失败 → BLOCKED 报告用户。

1 轮修复 + Coordinator 自验 → 失败 BLOCKED（不再派 targeted re-review；不消耗 review budget）。

**Phase 内部 review dispatch 软上限**：1（1 integration review + 0 targeted re-review）。

---
> **下一步**：通过 → Steps 19-22（`merge-completion.md`）。BLOCKED → 返回 verdict。
