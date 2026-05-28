# Multi-PR Conflict Worker Handbook

> **角色**：pack-executor 或 complex-pack-executor，负责 Multi-PR 冲突修复。
> **流程位置**：orchestrate-multi-pr-merge Steps 12-15，修复单个或一组冲突。

## Self-Read Protocol

启动时按以下顺序执行，缺少任何步骤 → BLOCKED，不猜测：

1. 读 dispatch prompt 头部的 `DISPATCH_ENVELOPE`，提取 `run_id`、`conflict_id`、`phase: "multi-pr-merge"`。
2. 读 `.claude/multi-model-workflow/merge-brief-<run_id>.md`：
   - §2 PR 表：获取大设计文档路径、PR branch、核心行为。
   - §4 Conflict C-`<conflict_id>` 段：获取冲突详情、classification、route。
   - §5 RCA（若 route=analyst-then-worker）：获取根因分析和修复方向。
3. 读大设计文档（来自 merge-brief §2 的 `big_design_path`），理解大设计目标和正确状态。
4. 读本文件（你正在读的这份 handbook），理解 Scope/Acceptance 和 Return Contract 格式。
5. 执行冲突修复，运行回归测试，输出修复摘要。

---

## Scope 约束

**允许修改**：
- 冲突涉及的 PR 分支中的源码文件（merge-brief §4 conflict 的 `files` 字段列出的文件，及直接依赖）
- 现有测试用例（仅修复因冲突导致的测试失败，不增删测试套件）
- 配置文件（仅当冲突涉及 config 不一致时）

**禁止修改**：
- 各 PR 已通过 Final Review 的核心行为（不能以"修复冲突"为由删功能）
- `docs/` 目录（worker 不能改 docs/）
- 与本次冲突无关的文件（scope drift = BLOCKED，Coordinator 处理）
- 大设计文档、大计划文档（不在 worker 权限范围）

**scope drift 处理**：发现修复需要改动 scope 外的文件 → 立即返回 BLOCKED + 说明原因，不擅自扩大范围。

---

## Acceptance Criteria（通用）

每次 conflict 修复完成后，必须满足以下条件：

1. **冲突已解决**：§4 中描述的冲突症状不再复现（运行测试验证）
2. **修复方向一致**：修复与 §5 RCA `fix_direction`（或 Coordinator 的 dispatch 指示）一致；如采用不同方案，在 Return 中说明理由
3. **不破坏已有行为**：所有参与 PR 的核心行为（merge-brief §2 `core_behavior` 字段）仍然成立
4. **回归测试通过**：运行受影响的测试套件，全部 pass
5. **不引入新功能**：大设计未要求的功能一律不写

---

## Commit 规范

每个逻辑变更独立 commit，commit message 格式：

```
fix(multi-pr-<conflict_id>): <一行修复摘要>

Resolves conflict <conflict_id> between PR #NNN and PR #MMM.
Root cause: <根因一句话>
Fix: <修复方式一句话>

merge-brief: .claude/multi-model-workflow/merge-brief-<run_id>.md
```

---

## Verification 规范

修复后必须运行：

```bash
# 1. 受影响的单元/集成测试
<project-specific test command for affected modules>

# 2. 回归：确认各 PR 的核心行为仍然成立
<specific behavior verification commands>

# 3. 如修复涉及 migration order / schema change
python3 -m py_compile <modified_files>  # 或等效语法检查
```

所有命令的输出 **必须** 包含在 Return Contract 的 Verification 段中。

---

## Return Contract

```markdown
### Verdict
pass / blocked / needs repair / needs context

### Evidence
（简要描述做了什么验证，有哪些关键证据）

### Result
- Changed files: [file:line 列表]
- Per-conflict resolution:
  - C-NNN: <修复摘要，1-2 句>
    - status_after: resolved | escalated-to-systemic | new-conflict-spawned
    - new_conflict_id: C-NNN（仅 new-conflict-spawned 时填）
- Open Items: （scope 外的发现，不是 finding，供 Coordinator 决策）

### Verification
（完整命令 + 输出摘要）
- `<command>` → <pass/fail + 关键输出>

### Known gaps
（未验证的内容和原因）
```

---

## 常见错误模式

**不要做的事**：
- 复制 PR 代码来"绕开"冲突（应该是修复根因，不是规避）
- 为了通过测试而 skip/mock 测试（这是掩盖冲突，不是解决冲突）
- 修改范围扩展到 5 个以上文件（可能是 systemic conflict，应 BLOCKED 让 Coordinator 决策）
- 在没有理解 §5 RCA 根因的情况下直接改代码
