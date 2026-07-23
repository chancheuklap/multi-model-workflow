# Codex Runtime Contract

## 路径与所有权

| 对象 | 合同 |
| --- | --- |
| plugin root | 从当前已加载 skill 的 source locator 反推，必须指向 Codex 安装 cache |
| 任务状态 | 当前 App worktree 的 `.codex/multi-model-workflow/` |
| outer worktree/branch | Codex App 创建并持有；MMW 只采用当前 linked worktree 和 `codex/<slug>` |
| plan/build inner worktree | `worker.sh` 创建和管理，固定在仓库 `.codex/worktrees/` 下 |
| worker branch | `worker/<worktree-name>` |

主线程始终在 Codex App 当前 task 中运行。它不靠脚本 `chdir` 模拟切换，也不创建
第二个 App 看不见的 outer。closing 后 cleanup 只清任务状态，App worktree/branch
仍归 App。

## Codex 工具

| 语义 | 工具 |
| --- | --- |
| 壳命令 | `exec_command` |
| 修改文件 | `apply_patch` |
| 结构化问用户 | `request_user_input` |
| GPT subagent | `spawn_agent`、`wait_agent`、`followup_task`、`list_agents` |
| 本地检索 | `rg`、`rg --files` 和文件读取工具 |
| 外部资料 | 当前可用的官方文档、web 或已安装外部 skill |

`unattended` 时主线程和全部 subagents 都禁止向用户提问。子代理缺输入时返回 blocker，
由主线程按 attendance 合同处置。

## Native subagents

调查、写计划、develop 写码、修复、release P1 修复和 GPT 审查全部使用 Codex native
subagents。它们使用当前 Codex 的 GPT 模型，不安装 custom agents，不维护 model
roster，也不通过外部 Codex CLI 启动。

`agents-roster/*.md` 只是主线程读取后交给 `spawn_agent` 的 prompt 模板，不含
model/tool frontmatter，不注册到 Codex。

派发合同：

- 独立任务先全部 `spawn_agent(fork_turns="none")`，再 wait，保证并行和干净上下文。
- prompt 必须钉绝对 worktree、唯一写边界、输入产物和 Return Contract。
- 当轮返修优先 `followup_task` 同一 target；target 不可用时只重派失败任务。
- agent target 不写入磁盘。跨会话恢复只信 task/loop/review 状态、Git commits、
  worktree status 和产物，再派一个干净 agent。
- 子代理是劳动力，不是信源；主线程亲验路径、行号、diff、提交和测试。

## Plan 与 Build

`mmw worker plan-dispatch` 和 `mmw worker dispatch` 只准备隔离 worktree、prompt、
start SHA、边界基线和 verify 命令，不启动模型。

- plan writer 只写指定 plan 和对应 issue 的 `Small issues`，不 commit；verify 后才
  原子发布回任务 App worktree。
- build worker 只在自己的 inner worktree 按 Task Pack TDD 并 commit，禁止改
  `docs/`；主线程 verify、亲验并本地 `--no-ff` 合并。
- accepted prototype 的 README 和 selected 由 dispatch 自动加入；未选候选不进入
  worker 上下文。

## Investigate 与 Review

investigate 的每个 topic 和独立 synthesis 都是 native GPT subagent；主线程用
`investigate-contract.sh` 校验、过滤和保留 dropped，再亲验 locator。

review 方法只有 `worktree-review` 一份：

- GPT slot 用 native subagent。
- 第二模型 slot 只通过 `second-review.sh` 调用用户配置的外部无头 CLI。
- 核心不识别 Claude、Gemini 或其他供应商名；第二模型失败时当前 slot fail loud，
  不用 GPT 代替。
- 审者只读；findings 落 review trace 后由主线程逐条亲验并写 verdict。

外部第二模型只用于独立审查，不参与调查、计划、实现或修复。

## Hooks 与人闸

Codex hooks 只接三类已有行为：SessionStart 恢复、出站红线、Pack commit 记账。
本地 merge 不拦；push、远端 PR merge 和部署必须经过用户批准。

`$multi-model-workflow:approve-design` 是唯一设计人闸，必须由 explicit-only wrapper 触发。用户口头同意
不算；承重设计或 accepted prototype 变化后 approval stale，必须重新明确确认。
package 的开发模式测试和安装后测试也只能由用户确认。

## 安全

- Worker 禁改 `docs/`；plan writer 只准改自己的 plan/issue。
- 所有内部调查和审查只读。
- 不静默吞失败；合法降级也必须留下结构化缺口。
- 本地 `git merge --no-ff` 可自主；禁止 `--squash`。
