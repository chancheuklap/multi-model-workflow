# Worktree Merge Protocol (F2)

并行 pack 使用 `isolation: "worktree"` 执行。本文档定义合并协议。

## 核心规则

1. **Worker 不 commit。** `pack-executor` 和 `complex-pack-executor` 有明确规则：不运行 git commit / merge / push。所有改动保持 unstaged。

2. **Coordinator 在 pack review 通过后 commit。** Coordinator 进入 worktree 目录，stage 相关文件，用 pack-scoped message commit。

3. **Coordinator 按顺序 merge。** `git merge --no-ff <worktree-branch>`。不并行 merge。

4. **冲突由 Coordinator 解决。** Coordinator 有全部 pack 的上下文。决不让 worker 解决跨 pack 冲突。冲突复杂时新建 targeted-repair agent。

5. **Merge 后跑完整测试。** 每次 merge 后验证整体通过。失败则定位是哪个 pack 的问题。

6. **Coordinator 清理 worktree。** `git worktree remove <path>`。成功 merge、失败、abandon 都由 coordinator 清理。

## 流程

```
对每个已通过 pack review 的 worktree branch:
  1. git merge --no-ff <worktree-branch>
  2. 有冲突 → 读 diff → 解决 → stage → commit
  3. 跑完整测试
  4. 失败 → 定位问题 pack → 新建 targeted-repair agent → repair → re-test
  5. 通过 → git worktree remove <path>
```

## Test Failure → 回到原 Worker

merge 后测试失败且问题属于单个 pack：

- SendMessage 原 worker（仍在 worktree 中）带上失败详情。
- Worker 在 worktree 内修复并重跑测试。
- SendMessage 不可用时新建同类 agent。

跨 pack 冲突导致的测试失败：coordinator 直接修或新建 targeted-repair agent。
