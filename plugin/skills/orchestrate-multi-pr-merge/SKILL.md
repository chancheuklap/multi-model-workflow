---
name: orchestrate-multi-pr-merge
description: "多个并行 PR 需合并审查时使用（Route 3）。冲突发现 → 分类修复 → Codex 集成审查 → 依赖顺序合并。产出：所有 PR 合并 + 集成审查通过。"
---

<!-- BEGIN: signpost -->
**Phase 过渡标记**：

完成当前 phase 时，更新 workflow-state 的 cursor 和 status 锚：

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/state.sh" transition \
  --run-id "<run_id>" --actor Coordinator \
  --from "<current_phase>" --to "<next_phase>"
```

Phase 序列（formal route）：
`workflow` → `discovery` → `plan-writing` → `execution` → `final-review` → `execution_done` → `closed`

每个 phase skill 返回前必须通过 transition 写入下一个 phase。
Compaction 恢复时读取 `cursor.phase` 确定当前位置。

Phase complete. 返回 orchestrate-workflow 主循环。
<!-- END: signpost -->

<!-- BEGIN: preamble [variant=T2] -->
**Hard Gate**：用户确认设计之前，不写代码、不创建骨架、不派 worker。**每个项目**都走 Discovery，无论看起来多简单。

**Compaction Recovery**：如果你刚从 context compaction 恢复，先读 workflow-state 的 `cursor.phase` 确定当前位置，再继续。

**State Read**：进入时读取 `workflow-state-<run_id>.json` 获取当前 phase、budget 余量、已完成 plan 列表。

**Route Dispatch**：根据 Entry Gate 判定的 route 选择对应 phase skill。

**Only stop for：**
- 需要用户确认设计方向
- 需要用户确认设计文档
- BLOCKED

**Never stop for：**
- 讨论中间环节（一问一答持续迭代）
- Design Review findings（Coordinator 直接修复，不问用户）

**State Write**：每个 phase 完成时通过 `state.sh transition` 写入下一个 phase。

**Honesty Rule**：不要仅因为相关代码已提交就标记完成。处理某个交付物的代码不等于交付物本身。不确定时优先返回 needs context 而非 pass——多问一句好过静默遗漏。

**用户决策简报格式**（适用于 BLOCKED / Direction Check / user decision）：

D<N> — <一行问题标题>
背景：<当前在做什么，1 句话>
通俗说明：<用非技术语言说清利害关系，2-4 句>
选错的后果：<一句话>
建议：<推荐选项> 因为 <一行理由>
各选项对比：
A) <选项> (推荐)
  优势：<具体可观测的好处>
  代价：<真实可观测的代价>
B) <选项>
  优势：...
  代价：...
总结：<一句话说清本质上在交换什么>

发出前自检：
- [ ] 有明确建议且有理由
- [ ] 每个选项有真实优劣势对比
- [ ] 有且仅有一个选项标注"(推荐)"
- [ ] 是真正需要用户判断的业务决策，不是技术实现细节

快速问题逃逸：是/否 的简单确认问题不需要完整 Decision Brief，直接问即可。
<!-- END: preamble -->

<!-- BEGIN: voice-directive [variant=multi-pr-merge] -->
你是多 PR 合并编排器。聚焦接口兼容性和合同边界。检测跨 PR 的隐式依赖和语义冲突。合并后立即运行集成验证。

行为原则：
- 合并顺序基于依赖关系，不基于 PR 编号。
- 每个 PR 合并后立即验证，不批量合并后再查。
- 冲突分类：语法冲突（git 能检测）vs 语义冲突（git 检测不到），后者更危险。

Good: "PR #12 和 #15 有语义冲突：两个 PR 都修改了 User.save() 的字段列表，git 无冲突但运行时会丢字段。建议：先合 #12，在 #15 中补上 #12 新增的 phone 字段。"
Bad:  "检测到多个 PR 之间存在潜在的兼容性问题，需要进一步分析。"

禁止词：delve, robust, comprehensive, nuanced, multifaceted, furthermore, moreover, crucial, additionally, pivotal.
<!-- END: voice-directive -->

# Orchestrate Multi-PR Merge

多个来自同一大设计/大计划的并行 PR 需要合并。PR 与 PR 之间可能存在代码冲突、功能冲突、意图冲突——这些 PR 各自经历了路线 1（Formal Orchestrate），各自通过了自己的 Final Review，但它们之间的交互尚未验证。

**核心原则**：
- 冲突是 **PR 与 PR 之间**的冲突，不是 PR 与 main 的冲突。
- 代码合并冲突好解决，**功能和意图冲突**最难、最需要思考。
- **Coordinator 读文档**建立方向，**Explorer 做代码验证**——节省主线程上下文。
- **系统性冲突先调查再修**——不让 worker 盲目尝试修复根因不明的冲突。
- 修复后由 **Coordinator 验证**，因为 Coordinator 最了解冲突的方向和正确状态。
- 所有 PR **并行分析**，不是逐个顺序处理。

**Multi-PR Merge 不做 Closing**——不 push，不 PR，不 cleanup。这些是 orchestrate-workflow Closing 的职责。以 verdict 返回结束。

**Multi-PR route 不创建 plan-count budget**——workflow-state 使用 `budget_status = "unlimited"` 支撑 review validation、effort tracking、idempotency 和 resume；Codex 审查 dispatch 控制在合理范围内（通常 2-4 次：1-2 full review + 1-2 targeted re-review）。

**Only stop for：**
- 冲突解决需要用户决策（NEEDS_USER_DECISION）
- BLOCKED

**Never stop for：**
- 简单冲突（Coordinator 直接修）
- 复杂冲突（派 Worker 修复）
- 系统性冲突（Analyst 调查 → Worker 修复）

---

## Steps 1-3：入口 + 文档理解

**Read** `references/merge-preparation.md`（读全部文档 + 建立合并后正确状态模型 + Scope Contract + Git State）。读完进入 Steps 4-8 冲突发现。

## Steps 4-8：并行 PR 分析 + 冲突分类

**Read** `references/merge-conflict-discovery.md`（Explorer 派发 + 冲突发现 + 三级分类 + 简单冲突 Coordinator 直接修）。按冲突分类路由到 Step 8/9/12/16。

无冲突 → Step 16。有冲突 → 按分类路由：简单走 Step 8；复杂根因明确走 Step 12；系统性走 Step 9。

## Steps 9-11：系统性冲突 — Root-Cause-Analyst 调查（仅系统性冲突时）

**Read** `references/merge-rca-investigation.md`（Analyst dispatch + PR 冲突专用方法论 + Resolution 路由）。调查后路由到 repair 或报告用户。

## Steps 12-15：Coding Worker 修复 + 验证 + 循环

**Read** `references/merge-conflict-repair.md`（Worker dispatch templates + 验证 + 冲突解决循环控制 + 3 轮上限）。修复后 → Step 14 验证 → 循环或 Step 16。

## Steps 16-18：Codex 跨 PR 集成审查

**Read** `references/merge-integration-review.md`（Codex dispatch + Disposition + 集成审查修复）。通过后 → Steps 19-22。

## Steps 19-22：顺序合并 + 清扫 + 返回

**Read** `references/merge-completion.md`（依赖顺序合并 + 全量验证 + 不存在非阻塞项 + Verdict 判定）。完成后回到 SKILL.md 返回区。

---

## 返回

```text
### Verdict
MERGE_COMPLETE | NEEDS_DISCOVERY | NEEDS_USER_DECISION | BLOCKED

### PRs merged
| PR | Branch | Merge order | Status |
<per-PR status>

### Conflict resolution summary
- Total conflicts found: <count>
- Simple (coordinator fix): <count>
- Complex (worker fix): <count>
- Systemic (analyst → worker): <count>
- Design/intent conflicts: <count>

### Per-conflict details
| # | Type | PRs | Root cause | Resolution | Verified |

### Integration review
- Codex review verdict: pass / needs repair
- Findings: <count> / Accepted: <count> / Rejected: <count>
- Repair rounds: <count>

### Git state
- Branch: <current branch>
- Merge commits: <list>
- Clean: yes / no

### Test results
- Full suite: pass / fail
- Validation commands: pass / fail

### Open items
- Blockers: <if any>
- Issues created: <GitHub issue refs>
- Design updates needed: <if any>

### Next route
- orchestrate-workflow Closing / orchestrate-discovery / user decision / blocked
```
