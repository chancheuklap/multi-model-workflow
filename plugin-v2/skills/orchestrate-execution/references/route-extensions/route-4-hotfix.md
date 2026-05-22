# Route 4: Hotfix

紧急修复路径。跳过 Plan Review，直接执行。review_total: unlimited。

**触发关键词**: hotfix, 紧急修复, 生产事故, P0

**行为差异**:
- 跳过 plan-writing phase
- review_total = "unlimited"
- 允许 push 后事后 review（pending_post_push_reviews）
- Final Review 简化为 regression check
