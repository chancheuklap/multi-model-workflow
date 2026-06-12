# Codex Orchestrate New Blind Spot Audit

## Scope

本次审计补查 `codex-orchestrate-new/` 迁移后前两轮没有逐项落到的合同面：

- workflow 基础设施和 worktree 创建合同。
- workflow closing、push、PR 创建和状态清理时机。
- execution plan 级隔离 worktree、worker-active marker 和回收合同。
- `execution-worker-dispatch.md` 与 custom agent TOML 的引用边界。
- build template 生成文本与 maturity gate 的防回归覆盖。
- 当前入口文档和 repo-local marketplace 的 source path。

`plugin/` 仍只作为上游行为蓝本，本次没有修改。`docs/orchestrate/` 下 2025/2026 早期设计、旧计划和旧审计文档保留为历史证据；当前 source 权威是 `codex-orchestrate-new/`、`README.md`、`AGENTS.md` 和 `.agents/plugins/marketplace.json`。

## Adopted Fixes

1. Workflow worktree 启动改为 Codex-native git 操作：Codex App detached worktree 原地创建命名分支；主仓库入口创建独立 coordinator worktree。
2. Closing cleanup 改为 PR 创建或 PR 更新成功后触发；`git push` 后保留状态，供 PR body 和 hotfix post-push review 读取。
3. Execution dispatch 明确先创建 plan worktree，再登记 `execution-plan start`；`state.sh` 在登记 worktree 时自动写入 `worker-active-<plan_id>` marker，终态清理沿用已有 finish 路径。
4. `execution-worker-dispatch.md` 降级为 Coordinator Step 5 checklist；Worker runtime 合同直接嵌入 `pack_executor` / `complex_pack_executor` TOML 和 dispatch prompt。
5. Control envelope template 加入 `plan_path`，Plan-level dispatch validator 继续把 `plan_path` 作为必填合同。
6. Maturity gate 增加盲区检查：禁止 host worktree pseudo tools、旧 5 步启动文案、legacy `plan-executor` 主路径、错误 cleanup 触发和 agent 相对 reference 依赖。

## Verification

已执行并通过：

```bash
bash codex-orchestrate-new/build/build.sh --check --plugin-dir codex-orchestrate-new
bash codex-orchestrate-new/scripts/verify-maturity.sh codex-orchestrate-new
bash codex-orchestrate-new/scripts/validate-plugin-contract.sh codex-orchestrate-new
bash codex-orchestrate-new/scripts/run-all-tests.sh
git diff --check
```

结果：

- `verify-maturity.sh`：64 passed, 0 failed。
- `run-all-tests.sh`：56 suites, all passed。
- `validate-plugin-contract.sh`：plugin contract validation passed。
- 源码残留扫描排除 tests 和 maturity 自检脚本后，没有命中 host pseudo tools、旧 5 步启动、错误 cleanup 触发、legacy `plan-executor` 主路径或 Claude-only runtime terms。
