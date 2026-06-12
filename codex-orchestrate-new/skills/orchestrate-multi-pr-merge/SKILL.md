---
name: orchestrate-multi-pr-merge
description: "多个并行 PR 需合并审查时使用（Route 3）。冲突发现 → 分类修复 → Codex 集成审查 → 依赖顺序合并。产出：所有 PR 合并 + 集成审查通过。"
---

<!-- BEGIN: signpost -->
**Phase 过渡标记**：

完成当前 phase 时，更新 workflow-state 的 cursor 和 status 锚：

```bash
bash "${MMW_PLUGIN_ROOT}/scripts/state.sh" transition \
  --run-id "<run_id>" --actor Coordinator \
  --from "<current_phase>" --to "<next_phase>"
```

`--to` 由本 phase skill 流程指定，合法跳转以 `routes-v1.json[route].phase_transitions` 为准并机器校验（非法即 `exit 2`）——phase 序列不在散文写死。Compaction 恢复读 `cursor.phase`。

Phase complete. 返回 orchestrate-workflow 主循环。
<!-- END: signpost -->

<!-- BEGIN: preamble [variant=T2] -->
**Hard Gate**：用户确认设计之前，不写代码、不创建骨架、不派 worker。**每个项目**都走 Discovery，无论看起来多简单。

**Compaction Recovery**：如果你刚从 context compaction 恢复，先读 workflow-state 的 `cursor.phase` 确定当前位置，再继续。

**State Read**：进入时读取 `workflow-state-<run_id>.json` 获取当前 phase、budget 余量、已完成 plan 列表。

**Only stop for：**
- 需要用户确认设计方向
- 需要用户确认设计文档
- BLOCKED

**Never stop for：**
- 讨论中间环节（一问一答持续迭代）
- Design Review findings（Coordinator 直接修复，不问用户）

**State Write**：每个 phase 完成时通过 `state.sh transition` 写入下一个 phase。

**Honesty Rule**：不要仅因为相关代码已提交就标记完成。处理某个交付物的代码不等于交付物本身。不确定时优先返回 needs context 而非 pass——多问一句好过静默遗漏。

**用户决策**：BLOCKED / Direction Check / user decision 时 **Read** `${MMW_PLUGIN_ROOT}/skills/_shared/decision-brief.md` 并按其格式输出。是/否 简单确认不需要完整 brief，直接问即可。
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

**Multi-PR route 不创建 plan-count budget**——workflow-state 使用 `budget_status = "unlimited"` 支撑 review validation、idempotency 和 resume；Codex 审查 dispatch 控制在合理范围内（通常 2-4 次 baseline review）。

**Only stop for：**
- 冲突解决需要用户决策（NEEDS_USER_DECISION）
- BLOCKED

**Never stop for：**
- 简单冲突（Coordinator 直接修）
- 复杂冲突（派 Worker 修复）
- 系统性冲突（Analyst 调查 → Worker 修复）

---

## merge-brief 写作流程

**Merge Brief 是本 phase 的唯一合成模型源。所有 dispatch 必须引用其路径而非粘贴内容。**

merge-brief 文件路径：`.codex/multi-model-workflow/merge-brief-<run_id>.md`

### 创建（Step 2，强制）

```bash
bash "${MMW_PLUGIN_ROOT}/scripts/state.sh" merge-brief init \
  --run-id "<run_id>" --slug "<feature-slug>"
```

创建后：Coordinator 读各 PR 文档 → 按 `references/merge-brief-template.md` 直接 Edit 填写 §2 PR 表 + §3 正确状态模型 → 写入 `workflow-state.cursor.reference`：

```bash
bash "${MMW_PLUGIN_ROOT}/scripts/state.sh" update \
  --run-id "<run_id>" \
  --field ".cursor.reference" \
  --value '"'.codex/multi-model-workflow/merge-brief-<run_id>.md"'"
```

### 阶段推进（按流程推进）

```bash
bash "${MMW_PLUGIN_ROOT}/scripts/state.sh" merge-brief stage \
  --run-id "<run_id>" --stage "conflict_discovery"
# 可用 stage: init | conflict_discovery | rca | repair | integration_review | merging | complete
```

### dispatch 使用规范

- Explorer dispatch：prompt 只携带 merge-brief 路径 + Explorer handbook 路径，不粘贴 PR 内容
- Worker dispatch：prompt 只携带 merge-brief 路径 + conflict_id + Worker handbook 路径
- Codex review dispatch：prompt 只携带 merge-brief 路径（reviewer 自读 §3/§6/§7 + 自跑 git diff）
- 内容追加：Coordinator 从 agent return 中提炼后直接 Edit merge-brief 对应段落

### 验证（提交前）

```bash
bash "${MMW_PLUGIN_ROOT}/scripts/state.sh" merge-brief verify --run-id "<run_id>"
# 检查：META 完整 + 9 段存在 + §4 status 与 §5/§6 自洽
```

---

## Coordinator dispatch 通用步骤

Multi-PR Merge 阶段 4 类 dispatch（explorer / analyst / worker / reviewer）均遵循以下通用模板：

1. 写 `merge-brief-<run_id>.md`（若已写则复用），确保包含 PR 列表、设计文档路径、合同地图、冲突解决记录、各阶段当前 stage
2. 写 `DISPATCH_ENVELOPE`：填入 `run_id`、`gate`（对应阶段名）、`review_intent: "baseline"`（reviewer 类）或 agent_role（其他类）
3. 写 dispatch prompt 文件 / 派发：reviewer 类走 review-prompts + validate/record；其他类直接 spawn_agent 调用
4. 等待返回 → 跑 result/complete 脚本 → Coordinator 校验返回事实 → 写入 merge-brief 对应段

各阶段 reference（merge-preparation / merge-conflict-discovery / merge-rca-investigation / merge-conflict-repair / merge-integration-review）只描述该阶段特有的 prompt 模板与返回处置，**不再重复 Coordinator dispatch 通用步骤**。

**4 类 dispatch 返回事实校验**：Coordinator 收到 explorer / analyst / worker / reviewer 返回的 PR 列表、冲突点、文件路径、行号、grep 结果等事实，必须抽验（至少 1 个事实 grep / Read / gh pr view）后再写入 merge-brief 对应段。事实失实 -> 重派或 Coordinator 亲查。

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
