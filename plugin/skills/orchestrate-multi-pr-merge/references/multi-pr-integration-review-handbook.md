# Multi-PR Integration Review Handbook

> **角色**：codex-reviewer，负责 Multi-PR 跨 PR 集成审查。
> **流程位置**：orchestrate-multi-pr-merge Steps 16-18。
> **目标**：验证多个 PR 合在一起后，系统整体是否正确——不是审查单个 PR，而是审查组合行为。

## Self-Read Protocol

启动时按以下顺序执行，缺少任何步骤 → BLOCKED：

1. 读 dispatch prompt 头部的 `DISPATCH_ENVELOPE`，提取 `run_id`、`gate`、`phase: "multi-pr-merge"`。
2. 读 `.claude/multi-model-workflow/merge-brief-<run_id>.md`：
   - §2 PR 表：PR 列表、branch、Final Review verdict、核心行为
   - §3 合同地图、文件交叉矩阵、风险热点（理解高风险区域）
   - §4 Conflict Findings：发现的冲突（用于判断修复覆盖是否完整）
   - §6 Resolution Log：冲突修复记录（审查修复质量）
   - §7 Integration Review Pointers：base_diff_range、contract_surfaces_to_audit、regression_focus_files
3. 读大设计文档（来自 merge-brief §2 `big_design_path`），理解大设计目标和预期的合并后状态。
4. 自行运行 `git diff`，获取合并后的 combined diff：
   ```bash
   git diff $(git merge-base <main-branch> HEAD)..HEAD
   # 或对每个 PR branch 分别 diff
   git diff main...<branch_A>
   git diff main...<branch_B>
   ```
5. 读本文件（你正在读的这份 handbook），理解 7 个 Review Angles 和 Return Contract 格式。
6. 按 7 个 Review Angles 独立验证，遵守 Pre-emit Verification Gate，输出 findings。

---

## Calibration

**核心原则**：
- **不信任各 PR 的 Final Review 结论**——独立验证组合行为。每个 PR 各自正确不代表组合正确。
- **只标记会导致实际问题的 issue**。每个 finding 必须有 evidence（file:line + 代码引用）。
- **单个 PR 内部代码质量**——已在各自 Final Review 覆盖，不再重复。
- **措辞、命名、风格**——不是 finding。
- **已在各 PR 的 open items 中记录的问题**——列入 "Out of scope observations"，不作为 finding。

**Targeted re-review 时**（envelope `review_intent=targeted-re-review`）：
只重审 `disposition_refs` 中 finding 关联的修复文件；不重审全部 diff。新发现的问题超出 disposition scope 的，列入 "Out of scope observations"。

---

## 7 Review Angles

### Angle 1：组合行为正确性

**检查**：所有 PR 合在一起是否产出大设计描述的正确行为？

方法：
- 对照大设计文档的 Goal Behavior 逐条验证
- 检查 merge-brief §3.1 行为清单是否全部成立
- 关注跨 PR 的行为交互（PR A 的输出是 PR B 的输入时，接口是否对齐）

**典型 finding**：PR A 实现了 Feature X，PR B 假设 Feature X 的某个特定行为但实现不符。

### Angle 2：合同一致性

**检查**：跨 PR 的 contract surface 是否一致？

来源：merge-brief §3.2 合同地图 + §7 `contract_surfaces_to_audit`。

检查点：
- Pydantic model 的 field 列表、类型、validator 是否跨 PR 一致
- API 端点的 request/response schema 是否跨 PR 一致
- DB schema 的 column 类型、nullable、index 是否跨 PR 一致
- Registry / config 的 key 格式是否跨 PR 一致

**典型 finding**：PR A 定义 `user.phone: Optional[str]`，PR B 的 API 把 phone 当 required 字段使用。

### Angle 3：迁移完整性

**检查**：多个 PR 的 migration 合并后顺序、完整性、安全性？

步骤：
```bash
# 查看所有新 migration 文件
git diff --name-only <base>..HEAD | grep migrations
# 检查 migration 顺序（alembic / Django）
python3 -m alembic history  # 或等效命令
```

检查点：
- migration 顺序是否正确（依赖关系驱动）
- 是否有遗漏的 migration（PR 改了 model 但没有对应 migration）
- 回滚是否安全（`down()` 是否完整）
- 是否有 data migration 风险（在生产数据上操作的 migration）

### Angle 4：状态一致性

**检查**：跨 PR 的 shared state 假设是否一致？并发安全？

检查点：
- 全局变量、class variable、module-level state 是否被多个 PR 以不兼容方式修改
- Cache key / TTL 假设是否一致
- 并发写入 shared state 是否有 race condition 风险

### Angle 5：Import / 依赖

**检查**：合并后是否有 import 问题？

```bash
# 检查循环 import（Python）
python3 -c "import <affected_module>" 2>&1
# 检查依赖版本冲突
cat requirements.txt | sort | uniq -d
```

检查点：
- 循环 import（PR A import PR B，PR B import PR A）
- 依赖版本冲突（PR A 要求 lib>=1.5，PR B 要求 lib<1.5）
- 新增的外部依赖是否已加入 requirements/package.json

### Angle 6：回归

**检查**：合并所有 PR 后，既有功能是否完好？

```bash
# 运行完整测试套件
<project-test-command>
# 运行回归重点文件（来自 merge-brief §7 regression_focus_files）
<targeted-test-command for regression_focus_files>
```

必须提供测试结果的实际输出（pass count / fail count / 具体失败测试）。

### Angle 7：冲突修复质量（仅当 §4 中有 resolved conflicts 时）

**检查**：之前解决的冲突的修复是否正确、完整？是否引入新问题？

来源：merge-brief §6 Resolution Log。对每个 `status_after=resolved` 的冲突：
- 复现冲突的原始场景，验证不再出现
- 检查修复代码是否改变了合同（有时 fix 是改了接口而非适配接口）
- 检查修复是否有 regression

---

## Return Contract

```markdown
### Verdict
pass / blocked / needs repair / needs context

### Evidence
| 字段 | 内容 |
| --- | --- |
| 已读设计 / plan 来源 | <merge-brief 路径 + 大设计文档路径> |
| 已检查代码路径 | <实际检查的文件列表> |
| 已运行命令 | <test commands + outputs> |
| Finding 证据 | <per-finding：file:line + 代码引用> |
| 假设 | <影响 verdict 的前提> |
| 未验证项 | <未验证原因> |

### Result

**组合行为正确性**: <pass / issue: …>
**合同一致性**: <pass / issue: …>
**迁移完整性**: <pass / issue: …>
**状态一致性**: <pass / issue: …>
**Import / 依赖**: <pass / issue: …>
**回归**: <pass N/N tests / fail M: …>
**冲突修复质量**: <pass / issue: … / not applicable>

Critical:
- [C1] <finding with file:line>
  Confidence: N

Important:
- [I1] <finding with file:line>
  Confidence: N

Low confidence observations (confidence ≤4):
- [L1] <observation>

Out of scope observations:
- [O1] <observation (not a finding)>

Disposition required: [C1], [I1]

### Verification
（测试命令 + 完整输出摘要）

### Open Items
（无法在当前 review 中完整验证的项，附理由）

### Bias indicators
（声明对哪些模块/技术栈经验不足，以及哪些 finding 可能受此影响）
```
