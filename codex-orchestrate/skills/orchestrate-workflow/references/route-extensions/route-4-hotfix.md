# Route 4: Hotfix

> **入口**：`orchestrate-workflow` Step 1 Entry Gate 匹配 hotfix / 紧急 / production fire / P0 / 生产事故

紧急修复路径。跳过 Discovery + Plan Writing，push 后事后 review。生产 triage 优先。

**触发关键词**: hotfix, 紧急修复, 生产事故, P0, production outage

**行为差异**（相对 formal route）:

## Phase 跳过

- **跳过 Discovery**：不写设计文档。直接从用户描述 + 重现步骤开始。
- **跳过 Plan Writing + Plan Review**：单 Pack 或 Coordinator 直接执行。不经过 plan_writer。
- `budget_status = "unlimited"`, `review_total = "unlimited"`, `effort_total = "unlimited"`

## Push 后事后 Review

Hotfix 的核心差异：**先 push 再 review**。修复完成 + 基本测试通过后立即 push。

1. Coordinator 修复或派 single pack_executor
2. 跑所有受影响的测试。Critical path 通过即可 push。
3. Commit message 打 `[hotfix-unreviewed]` 标签
4. `git push` — guard-premature-push.sh 对 hotfix route 放行
5. Push 成功后，将 review 任务写入 workflow-state：
   ```bash
   state.sh update --run-id <run_id> --field '.pending_post_push_reviews' \
     --value '[{"type":"post-push-regression","commit":"<sha>","created_at":"<now>"}]'
   ```
6. 事后 Codex review：回到正常 review 流程，dispatch baseline review
7. Review findings 走 disposition 流程。accepted findings 立即修复 + push follow-up commit

## post-push review 要求

事后 review focus：
- Regression：修复是否引入新问题
- Scope：修复是否只改了必要范围
- Test coverage：是否补了缺失的测试
- 不审设计（hotfix 没有 design doc）

## 回到 Normal Flow

- 事后 review 通过 → Closing
- 事后 review 发现问题 → 立即修复 + push + targeted re-review
- 问题严重到需要 revert → BLOCKED，报告用户

## Closing 清理

Hotfix 路线的 `git push` 不触发 state 清理（`cleanup-before-push.sh` 检测到 `route = "hotfix"` 时延迟清理）。事后 review 完成后，Closing 阶段必须手动执行清理：

```bash
bash "${MMW_PLUGIN_ROOT}/scripts/cleanup-before-push.sh" --force
```

---
> **下一步**：事后 review 通过 → orchestrate-workflow Closing（含手动清理）。BLOCKED → 返回 verdict。
