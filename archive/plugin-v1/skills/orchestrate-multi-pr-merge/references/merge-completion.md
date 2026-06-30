# Multi-PR Merge 完成：顺序合并 + 清扫 + 返回

> **流程位置**：`orchestrate-multi-pr-merge` Steps 19-22 · 含 verdict 判定 · 完成后回到 SKILL.md 返回区

Codex 跨 PR 集成审查通过后，进入顺序合并。

---

## Step 19：确定合并顺序

按依赖顺序合并 PR。

合并顺序基于 Step 2 确定的依赖关系：
1. 被依赖的 PR 先合（foundation / infra / contract provider）
2. 依赖方后合（consumer / feature / UI）
3. 无依赖关系的按计划文档中的顺序

## Step 20：逐个执行合并

**串行合并**——不并行，避免 merge conflict 级联。

对每个 PR 按顺序执行：

```bash
git fetch origin <pr-branch>
git merge origin/<pr-branch> --no-ff -m "Merge PR #<number>: <title>"
```

**冲突处理**：
- 代码冲突（预期内，冲突解决阶段已处理的区域）→ 按已确定的解决方案应用
- 意外冲突（冲突解决阶段没发现的新冲突）→ 暂停合并，回到 Step 7 分类并处理

**每次 merge 后**：
1. 跑完整测试套件
2. 测试失败 → 暂停，调查原因（可能是合并引入的回归）
3. 测试通过 → 继续下一个 PR

## Step 21：全量集成验证

所有 PR merge 完成后：
1. 跑完整测试套件
2. 跑大设计文档中所有 validation commands
3. 确认合并后的行为与"合并后正确状态"模型一致

---

## 清扫纪律

清扫纪律同 Final Review Step 13（详见 `final-review-completion.md`）。Multi-PR 独有清扫来源：
- 所有冲突解决记录中标记为 "out of scope" 的项 → 确认已开 GitHub issue
- 合并过程中 worker Open Items → 逐项处置（修复 / 开 issue / 确认不是问题）
- `git diff <base>..HEAD` 范围内新增的 TODO/FIXME → 处置

---

## Step 22：确定 Verdict

| 条件 | Verdict |
| --- | --- |
| 所有 PR 合并成功 + 集成审查通过 + 全量测试通过 | `MERGE_COMPLETE` |
| analyst 发现设计/意图冲突，需要重新对齐设计 | `NEEDS_DISCOVERY` |
| 冲突解决需要用户决策 | `NEEDS_USER_DECISION` |
| 无法自主解决 | `BLOCKED` |

---
> **下一步**：verdict 确定后回到 SKILL.md 返回区。MERGE_COMPLETE → orchestrate-workflow Closing。
