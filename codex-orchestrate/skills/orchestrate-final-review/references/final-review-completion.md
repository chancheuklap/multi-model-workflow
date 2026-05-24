# Final Review 完成：清扫 + Release Gate + 业务汇报

> **流程位置**：`orchestrate-final-review` Steps 13-20 · 含 verdict 判定 · 完成后回到 SKILL.md 返回区

两个 baseline review 的 accepted findings 全部修复并通过 Targeted Re-Review 后（或两个 baseline 直接 pass），进入 Coordinator 主导的后续流程。

---

## 第一段：清扫遗留尾巴（Steps 13-15）

**这是 Coordinator 的职责**，不是 reviewer 的角度。Plan Implementation Review 和 Final baseline review 关注的是"做得对不对"；清扫关注的是"有没有漏做"。项目中不存在"非阻塞项"——所有东西要么当场修复，要么立刻开 GitHub issue。

**注意**：Execution 阶段（Step 7a + Step 9）已经对 Worker Open Items 和 out-of-scope findings 做了即时处置并开了 GitHub issue。Final Review 的清扫是**验证 + 补漏**，不是主要开 issue 的环节。

### Step 13：收集 + 验证已处置项

从三个来源收集所有可能的遗留尾巴，**并验证 Execution 阶段的处置是否完整**：

**13a：Worker Open Items — 验证已处置**

读取每个 pack 的 worker 返回的 `### Open Items`。对照 Execution 阶段的处置记录：每个 `[out-of-scope]`、`[needs-evaluation]`、`[bug]` 标记项是否已有对应的 GitHub issue 或修复记录。**补漏**：发现未处置项 → 按 Step 14 处置。

**13b：代码扫描**

在 diff 范围内扫描遗留标记：

```bash
git diff <starting_commit>..HEAD --diff-filter=AM --name-only | xargs grep -n "TODO\|FIXME\|TBD\|XXX\|HACK\|defer\|later\|placeholder\|temporary\|workaround" 2>/dev/null || true
```

过滤掉 starting commit 之前已存在的遗留标记（`git show <starting_commit>:<file>` 对比）。只关注本次实现新增的。

**13c：Plan Implementation Review Disposition 记录 — 验证 issue 已开**

读取 execution 过程中所有 `out of scope` 和 `needs evaluation` disposition。验证每条是否已有对应 GitHub issue（`gh issue list --search` 确认）。**补漏**：发现 execution 阶段遗漏的 → 按 Step 14 处置。

### Step 14：逐项处置（仅 Step 13 中发现的未处置项）

对每个**尚未处置**的遗留项，Coordinator 必须做出明确处置——**不允许"先放着"**：

| 处置 | 条件 | 动作 |
| --- | --- | --- |
| **立即修复** | 在当前 scope 内、修复简单（≤ 2 文件）、不引入新风险 | Coordinator 直接修或派 worker |
| **开 GitHub Issue** | 不在当前 scope 内、或修复复杂需要独立 session | 立即开 issue（Durable Handoff Brief 格式），先查重 |
| **确认不是问题** | 经查实遗留标记是合理的（如 TODO 指向未来 feature，不影响当前功能） | 记录确认理由，不删除标记也不开 issue |

**铁律**：处置完成后，不应存在任何含糊的遗留项。Execution 阶段已处置的有据可查；Final Review 新发现的全部补处置完毕。

### Step 15：清扫修复验证

如果 Step 14 产生了代码修改：
1. 跑完整测试套件确认不回归
2. 跑所有 pack 的 verification commands
3. 简单修复（Coordinator 直接改）→ 不需要额外 review
4. 复杂修复（派了 worker）→ 做 targeted re-review（Budget 消耗 1）

---

## 第二段：Release Gate（Steps 16-18，条件触发）

清扫完成后，检查最终 diff 是否触碰发布风险面（migration / billing / permission / runtime / cross-service contract / deploy order / manual gate / API compatibility）。

- **触发** → 读取 `final-review-release-gate.md` 执行 Release Gate 流程
- **不触发** → Step 19

---

## 第三段：业务汇报（Step 19）

Final Review 的两个 baseline 通过 + 遗留清扫完成 + Release Gate 通过（如有）后，组装业务汇报。

**汇报用业务语言**，不用技术术语。面向项目负责人 / 产品经理。

### 19a：新增能力

用业务语言描述用户或系统现在能做什么——每项能力是一个用户可感知的行为变化。不列函数名、文件路径或技术实现细节。

### 19b：验证证据

每项能力附上：
- 哪些测试验证了这个行为
- 关键验证命令的运行结果
- UI 验证截图（如有 UI 工作）
- Contract 验证证据（如有 contract 变更）

### 19c：残余风险

未解决的 manual gate、已知 edge case、deploy 注意事项。每项说明：
- 风险是什么
- 影响范围
- 缓解措施（如有）

### 19d：发布检查

| 检查项 | 状态 |
| --- | --- |
| Migration | 通过 / 不适用 / 需人工确认 |
| Rollback | 通过 / 不适用 / 需人工确认 |
| Deploy order | 通过 / 不适用 / 需人工确认 |
| Manual production gate | 通过 / 不适用 / 需人工确认 |

### 业务报告写作锚点

Good:
> **新增能力**：用户现在可以用手机号登录，15 秒内完成。之前只支持邮箱，平均 45 秒。
> **验证证据**：注册→登录→访问首页全流程测试通过。
> **残余风险**：海外手机号格式未覆盖，影响 ~5% 用户。已开 issue #42 跟踪。

Bad:
> **新增能力**：实现了 PhoneAuthProvider 并集成到 AuthStrategy pipeline。
> **验证证据**：TDD red-green-refactor 完成，所有 23 个 test case 通过。
> **残余风险**：需要进一步测试边界条件。

**业务汇报包含在 verdict 返回的 `### Business report` 中。orchestrate-workflow Closing 的 Step 23 将其呈现给用户。**

---

## Step 20：确定 Verdict

| 条件 | Verdict |
| --- | --- |
| 两个 baseline 通过 + 遗留清扫完成 + 无 release gate 触发 | `FINAL_REVIEW_PASSED` |
| 两个 baseline 通过 + 遗留清扫完成 + release gate 触发且通过 | `FINAL_REVIEW_PASSED_WITH_RELEASE_RISK` |
| accepted findings 涉及多 pack 系统性问题 | `NEEDS_EXECUTION`（读 workflow-state 的 `execution_reflux_count`：0 → 可回流；≥1 → BLOCKED） |
| design / context gap 需要 discovery 补充 | `NEEDS_DISCOVERY` |
| plan gap 需要修订 | `NEEDS_PLAN_REVISION` |
| 无法自主解决 | `BLOCKED` |

---
> **下一步**：verdict 确定后回到 SKILL.md 返回区组装最终返回值。NEEDS_EXECUTION → orchestrate-execution。BLOCKED → 报告用户。
