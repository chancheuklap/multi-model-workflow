# Codex Orchestrate Architecture

本文是 `codex-orchestrate-new/` 的架构权威。该目录是一次干净迁移：以 `plugin/` 的工作流能力为行为蓝本，但所有运行时合同、agent、hook、state、manifest、dispatch 和文档入口都改成 Codex-native 形态。

## 目标

- 保留多模型编排的核心业务价值：路线判断、设计确认、计划写作、Plan 级执行、独立审查、修复分流、终审和关闭。
- 使用 Codex custom agents 与 Codex multi-agent 工具作为唯一执行和审查载体。
- 所有可执行源、生成模板、state schema、测试和安装入口都落在 `codex-orchestrate-new/`。
- 不依赖旧宿主的 payload、环境变量、命令、agent 文件格式或运行时路径。

## 源码边界

| 路径 | 职责 |
| --- | --- |
| `.codex-plugin/plugin.json` | Codex plugin manifest，声明 skills 与 root `hooks.json`。 |
| `hooks.json` | Codex hook manifest，指向 `hooks/*.sh` handler。 |
| `skills/` | 用户入口和 phase skill。面向 agent 的说明必须能从 skill 自己定位到 reference。 |
| `agents/*.toml` | Codex custom agent 配置。所有 agent 指令自足，不依赖父 skill 隐式上下文。 |
| `scripts/` | state、dispatch、review、验证、runtime parity 和 agent sync 工具。 |
| `state-schema/` | workflow state、execution state、dispatch envelope、route graph 和 return artifact schema。 |
| `build/` | 模板解析和生成系统，负责把共享片段注入 skills / agents。 |

`plugin/` 只作为只读行为蓝本，不是运行时 source of truth。

## 运行时入口

`orchestrate-workflow` 是唯一 coordinator 入口。它做四件事：

1. 读取项目规则、当前 git/worktree 状态和用户目标。
2. 根据 route graph 初始化 `workflow-state-<run_id>.json`。
3. 进入对应 phase skill，派发 Codex custom agents 或 Codex reviewer。
4. 在每个 phase 结束时用 `state.sh transition` 写 cursor，直到 Closing。

Codex App 工作树经常处于 detached HEAD。进入正式执行前，Coordinator 必须在当前 worktree 创建命名分支；如果当前目录是主仓库，只能先创建独立 worktree。

## Route Graph

`state-schema/routes-v1.json` 是路线和 phase 转移的机器权威。

| Route | 用途 | 主要 phase |
| --- | --- | --- |
| `formal` | 大改造、新功能、核心红线、需要设计确认的工作 | discovery → plan-writing → execution → final-review → closed |
| `light` | 日常小改、维护、quick fix、hotfix 子模式 | workflow → execution → final-review → closed |
| `direct-repair` | 已知问题的直接修复 | direct-repair → closed |
| `bug-investigation` | 未知根因 bug | bug-investigation → closed |
| `multi-pr-merge` | 多 PR 合并与语义冲突处理 | multi-pr-merge → closed |

Light Lane 是路线名，表示跳过完整 discovery / plan review 的轻量流程。它不代表执行载体选择。

## Codex Agents

所有 agent 都是 TOML 配置，安装到 Codex custom agent runtime 后通过 `spawn_agent(agent_type="...")` 使用。

| Agent | 模型 | 权限 | 用途 |
| --- | --- | --- | --- |
| `plan_writer` | `gpt-5.5` | read-only | 把 reviewed design 和 issue hierarchy 写成可执行 Plan。 |
| `pack_executor` | `gpt-5.4` | workspace-write | 普通风险 Plan 的代码执行和 finding 修复。 |
| `complex_pack_executor` | `gpt-5.5` | workspace-write | 高风险 Plan、跨模块、迁移、计费、权限、runtime 和共享合同修复。 |
| `codex_reviewer` | `gpt-5.4` | read-only | 设计、计划、执行、终审、发布和 ad-hoc review。 |
| `root_cause_analyst` | `gpt-5.5` | workspace-write | 未知根因调查和修复，或 repair 循环截断后的根因定位。 |
| `code_explorer` | `gpt-5.4-mini` | read-only | 窄范围代码事实调查。 |
| `complex_code_explorer` | `gpt-5.5` | read-only | 多模块、架构、历史行为和只读根因调查。 |

Coordinator 不采信 subagent 未验证事实。任何路径、计数、commit、测试输出或文件存在性，在写入正式交付前都要由 Coordinator 亲自核验。

## Execution

Execution 是 Plan 级自治执行：

1. Coordinator 读取 reviewed Plan inventory，创建或恢复 `execution-state-<run_id>.json`。
2. `state.sh dep-batches` 按 Plan 依赖计算批次。
3. 每个 Plan 派一个 worker：
   - 普通风险用 `pack_executor`。
   - 高风险用 `complex_pack_executor`。
4. Worker 读取完整 Plan、source issue、execution-state、项目规则和 worker reference。
5. Worker 按 Pack dependencies 顺序执行 TDD、verification、commit，并写：
   - `pack-returns/<run_id>/<pack_id>.json`
   - `plan-returns/<run_id>/<plan_id>/plan-return.json`
   - `plan-returns/<run_id>/<plan_id>/open-items.json`
6. Coordinator 用 `wait_agent` 等待，保存 final message，亲验事实，然后调用 `agent-return-handler.sh` 或对应 state 命令收口。

Worker 的合法 verdict：

| Verdict | 含义 |
| --- | --- |
| `pass` | 全部 Pack 完成且验证通过。 |
| `partial-pass` | 部分 Pack 完成，部分 blocked。 |
| `blocked` | Plan 无法继续，需用户或 Coordinator 决策。 |
| `need-fresh-worker` | 当前 worker 上下文过长，剩余 Pack 交给新 worker。 |
| `needs-context` | 缺关键合同、mockup、验证或业务上下文。 |
| `needs-plan-revision` | Plan 必备字段缺失、依赖不可解析或和 source issue 冲突。 |

## Review Dispatch

所有 review 走 `_shared/review-dispatch.md`：

1. Coordinator 写 review prompt 到 `.codex/multi-model-workflow/review-prompts/<gate>.md`。
2. prompt 首段必须是 `DISPATCH_ENVELOPE`，`agent_role` 必须是 `codex_reviewer`，`review_intent` 必须是 `baseline`。
3. `dispatch-review.sh validate` 校验 envelope、gate、budget、repair round 和 execution 前置条件。
4. Coordinator 调用 `spawn_agent(agent_type="codex_reviewer")`。
5. `dispatch-review.sh record` 写 review registry 和 agent id。
6. `wait_agent` 返回后，Coordinator 保存 result，立即 `close_agent`。
7. `complete-review-dispatch.sh` durable 标记结果，并 exactly-once 递增 review budget。
8. disposition 开始和完成分别由 `record-review-disposition.sh` 标记。

Codex hook 不从 Bash 命令文本猜测 native subagent prompt。真实 review gate 在显式 validate 脚本里。

## Repair Routing

`skills/_shared/repair-routing.md` 是 accepted finding 的分流权威。

| Finding 类型 | Owner |
| --- | --- |
| 小范围、本地化、意图清楚 | Coordinator Path A 可自修。 |
| 同 Plan 普通修复 | `resume_agent` 后 `send_input` 原 `pack_executor`。 |
| 高风险或跨边界修复 | 升级到 `complex_pack_executor`，或把修复表达成新的 repair Pack。 |
| 根因不明 | `code_explorer` / `complex_code_explorer` 补证，或 `root_cause_analyst` 调查。 |
| Final Review 跨 Plan 合同问题 | 返回 `NEEDS_EXECUTION`，通过 execution repair 处理。 |
| 设计或计划不足 | 回流 Discovery 或 Plan Writing。 |

repair return 必须包含回归证据、测试选择和未验证项。不得用低价值实现细节测试凑数。

## Hooks

Codex manifest 自动注册 `hooks.json`。Hook 使用 Codex payload helper，不依赖 cwd 猜路径。

| Hook | 时机 | 职责 |
| --- | --- | --- |
| `session-start.sh` | SessionStart | 输出 plugin root、active run、state recovery 指引。 |
| `guard-premature-push.sh` | PreToolUse Bash | 防止 active run 绑定的 plan 未闭合时提前 push；无 active run 的普通 push / PR 不扫描历史 plans，也不按分支 diff 猜测 plan scope。 |
| `enforce-plan-commit.sh` | PreToolUse Bash | 校验 Pack commit message。 |
| `guard-doc-edit.sh` | PreToolUse Edit/Write/apply_patch | worker in-flight 时保护 docs 与主树。 |
| `track-execution-state.sh` | PostToolUse Bash | git commit 后更新 execution-state。 |
| `agent-return-handler.sh` | SubagentStop | 解析 worker return，写 plan 状态和下一步提示。 |
| `track-review-budget.sh` | PostToolUse Bash | 保留为 no-op。预算计数由 complete-review-dispatch 负责。 |
| `gate-codex-review.sh` | PreToolUse Bash | 保留为安全提示位。真实 gate 由 dispatch-review validate 负责。 |
| `enforce-repair-round-cap.sh` | PreToolUse Bash | 保留为 no-op。repair round cap 由 dispatch-review validate 负责。 |

## State

`.codex/multi-model-workflow/` 是运行时状态根。

| State | 用途 |
| --- | --- |
| `workflow-state-<run_id>.json` | route、cursor、budget、review disposition、active run。 |
| `execution-state-<run_id>.json` | Plan / Pack 执行状态、worker agent id、commit sha、open items。 |
| `review-registry/<gate>.json` | review dispatch、agent id、prompt、result、budget counted 状态。 |
| `review-results/<gate>.md` | reviewer final message 原文。 |
| `plan-returns/<run_id>/<plan_id>/` | worker 的 Plan 级返回 artifact。 |
| `pack-returns/<run_id>/` | worker 的 Pack 级返回 artifact。 |

Schema、`state.sh`、hooks、dispatch validators 和生成文本必须一致。修改其中任一层要跑 build、test、maturity 和 plugin contract 验证。

## Cross-Plan Contract Anchors

Plan Writing 必须在 plan 文档中维护 `Cross-Plan Contract Anchors`。Final Review 用它检查跨 Plan 的 producer / consumer / verifier 是否闭合，防止每个 Plan 单独通过但整体合同断裂。

锚点至少包含：

- owner：谁对合同负责。
- provider：谁生产数据、API、schema、event 或 UI state。
- consumer：谁读取或依赖该合同。
- verifier：用什么测试、schema、migration、manual gate 或 runtime check 证明闭合。

缺 anchor 或 anchor 无 verifier 时，Plan Review 不能 pass。

## Build And Verification

常规源码验证：

```bash
bash codex-orchestrate-new/build/build.sh --check --plugin-dir codex-orchestrate-new
bash codex-orchestrate-new/scripts/run-all-tests.sh
bash codex-orchestrate-new/scripts/verify-maturity.sh codex-orchestrate-new
bash codex-orchestrate-new/scripts/validate-plugin-contract.sh codex-orchestrate-new
```

安装或发布类任务还要验证 runtime parity：

```bash
bash codex-orchestrate-new/scripts/verify-runtime-parity.sh codex-orchestrate-new
```

Source 改动不等于 runtime 已生效。只有用户明确要求安装、发布或同步 runtime 时，才写入 Codex plugin cache、custom agents 或用户级 config。
