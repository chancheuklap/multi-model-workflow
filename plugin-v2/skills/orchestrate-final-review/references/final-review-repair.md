# Final Review 修复分流 + 截断

> **流程位置**：`orchestrate-final-review` Steps 9-12 · 仅 needs repair 时进入

## Step 9：修复路由

所有 repair prompt 只携带 accepted findings。Repair 返回后默认只做 targeted re-review；只有 source baseline 改变时才 full phase review rerun。

- **路径 A**（≤ 2 文件、不碰合同边界、意图明确）：Coordinator 直接修 → 跑验证 → Step 11
- **路径 B**（多文件、根因已知）：SendMessage 给原 worker 或新建同类 agent：

```
Agent({
  subagent_type: "<pack-executor | complex-pack-executor>",
  description: "Final Review repair: <finding summary>",
  prompt: "
    ## Scope
    修复 Final Review 发现的问题。

    ## Source design
    <path>

    ## Finding(s)
    <paste accepted findings with severity / locator / evidence / impact / remediation>

    ## Affected files
    <list>

    ## Context
    <pack brief subset — goal behavior + contract anchors + verification commands>

    ## Acceptance criteria
    - [ ] 每条 accepted finding 已修复
    - [ ] 回归测试通过
    - [ ] 不引入 design 未要求的新功能

    ## Return contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    ### Result
    - Changed files
    - Fix applied per finding
    ### Verification
    ### Open Items
  "
})
```

4. Worker 修复后返回 → 进入 Step 11

### 路径 C：Complex-Code-Explorer 调查

**条件**：根因不明——reviewer 指出症状但无法确定原因。

```
Agent({
  subagent_type: "complex-code-explorer",
  description: "Investigate unknown root cause: Final Review finding",
  prompt: "
    ## Scope
    只读调查。Final Review 报告了症状但无法确定根因。找到根因，不写代码。

    ## 症状描述
    <paste accepted finding — severity / locator / evidence / impact>

    ## 已知上下文
    - Source design: <path>
    - Plan: <path>
    - Affected packs: <list>
    - 相关文件: <affected files>
    - Git diff scope: git diff <starting_commit>..HEAD

    ## 调查方向
    <Coordinator 初步判断——跨 pack 交互 / 时序 / 隐式依赖 / 合同闭合 / 状态污染等>

    ## Return Contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    - 实际检查过的 files / tests / logs / commands
    ### Result
    - Facts: confirmed facts with locators
    - Root cause assessment: <root cause + evidence, if found>
    - Recommended fix direction: <路径 A（Coordinator 直接修）/ 路径 B（Worker 修）+ 理由>
    - Excluded paths: hypotheses checked and ruled out with evidence
    - Recommended next probe: <if root cause not found>
    ### Verification
    ### Open Items
  "
})
```

Explorer 返回后路由：

| Explorer Result | 动作 |
| --- | --- |
| Root cause found + 推荐路径 A | Coordinator 直接修复 → Step 11 |
| Root cause found + 推荐路径 B | 派 Worker 修复 → Step 11 |
| Root cause not found | 报告用户，附 explorer 已排除路径 |

**快速判定**：≤ 2 文件 + 意图明确 → A；缺 migration / consumer 同步 / 测试 → B；行为异常原因不明 → C；涉及 migration / billing / permission / runtime / shared contract → B（用 complex-pack-executor）；涉及多个 pack 的系统性问题 → `NEEDS_EXECUTION`（读 budget file `execution_reflux_count`：0 → 可回流；≥1 → BLOCKED 报告用户）。

---

## Step 10：Implementation Gap 回 Execution 的判定

如果 accepted findings 涉及多个 pack 的系统性问题（不是单点修复），Coordinator 判断是否应该回到 orchestrate-execution 处理：

**回 Execution 的条件**（任一成立）：
- 涉及 3 个以上 pack 的 owned files
- 需要重新执行某个完整 pack
- plan 的 Source Coverage Map 有未覆盖的 intent 需要新 pack 实现
- 修复影响其它 pack 的 dependencies 或 contract surface

**留在 Final Review 修复的条件**：
- 涉及 1-2 个 pack 的少量文件
- 修复范围明确、不影响其它 pack
- 不需要新 pack

回 Execution → 立即返回 `NEEDS_EXECUTION` verdict，附 accepted findings 和 affected packs。

---

## Step 11：Targeted Re-Review

修复完成后，只重审 accepted findings 涉及的变更部分。不做 full review rerun。

按以下步骤派发 Codex review（`CODEX_SCRIPT` 未定义时先执行 `CODEX_SCRIPT="$(find ~/.claude/plugins -path "*/codex/scripts/codex-companion.mjs" -type f 2>/dev/null | head -1)"`）：
1. 写 prompt → `review-prompts/final-review-re-review.md`（内容见下方模板）
2. `node "$CODEX_SCRIPT" task --background --prompt-file .claude/multi-model-workflow/review-prompts/final-review-re-review.md --model gpt-5.4 --effort xhigh` → 记录 JOB_ID
3. `node "$CODEX_SCRIPT" status <JOB_ID> --wait --timeout-ms 600000`（run_in_background: true）
4. `node "$CODEX_SCRIPT" result <JOB_ID>` → 存到 `review-results/final-review-re-review.md`

Review prompt 写入 `.claude/multi-model-workflow/review-prompts/final-review-re-review.md`：

```markdown
## Scope
Targeted re-review for Final Review repair.
Only review the changes made to address the listed findings.

## Original findings
<paste accepted findings>

## Repair diff
<git diff of repair changes>

## Changed files
<repair-affected files only>

## Contract anchors
<if repair touches contract boundaries>

## Review focus
- Each accepted finding has been addressed
- Repair does not introduce new issues
- Verification commands pass

## Calibration
只验证修复是否解决了原始 finding。不做全面重审。

## Return Contract
### Verdict
pass / needs repair / blocked
### Evidence
### Result
Per-finding status:
- <finding 1>: resolved / still present / new issue
### Verification
### Open Items
```


---

## Step 12：修复截断

每个 gap 最多 3 个 repair round（2 个 Worker/Coordinator round + 1 个 root-cause-analyst round）。

| Round | 动作 |
| --- | --- |
| Round 1 | 路径 A/B/C 修复 → Targeted Re-Review |
| Round 2 | 仍 needs repair → 路径 A/B/C 修复 → Targeted Re-Review |
| Round 3（截断） | 仍 needs repair → **截断 Worker 循环**，新建 `root-cause-analyst` |

**Root-Cause-Analyst 截断调度**：

```
Agent({
  subagent_type: "root-cause-analyst",
  description: "Investigate Final Review repair failure: <finding>",
  prompt: "
    ## 调度场景
    Repair Truncation（Final Review）。Final Review 修了两轮，reviewer 仍报 needs repair。

    ## 前两轮上下文
    - Round 1 accepted findings: <paste>
    - Round 1 修复内容: <paste>
    - Round 2 accepted findings: <paste>
    - Round 2 修复内容: <paste>
    - Git diff scope: <paste>

    ## Source context
    - Source design: <path>
    - Plan: <path>
    - Affected packs: <list>

    ## 你的任务
    不要重复前两轮的修复方法。从不同维度切入——时序、状态污染、隐式依赖、配置漂移、跨 pack 交互。

    ## Return contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    ### Result
    - Resolution: fixed / root cause found, not fixed / root cause in design/plan / unable to reproduce / unable to determine
    - Root cause: <evidence>
    - Fix applied: <if fixed>
    - Excluded hypotheses: <with evidence>
    - Regression risk: <what could break>
    ### Verification
    ### Open Items
  "
})
```

**Analyst Resolution 路由**：

| Resolution | 下一步 |
| --- | --- |
| `fixed` | Targeted Re-Review（消耗 Round 3 的 review budget） |
| `root cause found, not fixed` | 用 analyst findings dispatch worker（消耗 Round 3） |
| `root cause in design/plan` | 写回 design doc / plan → 返回对应 upstream verdict |
| `unable to reproduce` | 报告用户，附 analyst 排除路径，请求更多重现信息 |
| `unable to determine` | BLOCKED，报告用户，附 analyst 排除路径 |

Round 3 的 Targeted Re-Review 仍 needs repair → BLOCKED，报告用户附完整排查记录。

**Phase 内部 review dispatch 软上限**：10（2 baseline + 最多 3 gaps × 2 rounds + analyst round + final re-review）。

---
> **下一步**：修复通过 → Step 13（`final-review-completion.md`）。BLOCKED → 返回 verdict。
