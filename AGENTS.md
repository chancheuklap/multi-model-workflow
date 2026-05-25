# AGENTS.md

## 作用域

本文件是 Codex 在本仓库工作的规则入口，只记录稳定的仓库事实、所有权边界、运行时合同和验收门槛。详细架构写在 `codex-orchestrate/architecture-draft.md`；面向使用者的快速入口写在 `README.md`。

## 当前真相

- 本仓库保存同一套编排思想的两个宿主实现。
- `plugin/` 是 Claude Code plugin 源码和行为蓝本。Codex 可以只读它来做 parity 对照，但不能修改、格式化、构建、安装或暂存 `plugin/` 下的文件。
- `codex-orchestrate/` 是 Codex 原生源码权威。skills、TOML agents、hooks、scripts、state schema、build templates、manifest 和运行时合同都应落在这里。
- `.agents/plugins/marketplace.json` 负责把 Codex plugin 暴露给 repo-local marketplace；除非源码根目录正式迁移，否则 source path 必须继续指向 `./codex-orchestrate`。
- `codex-orchestrate/.codex-plugin/plugin.json` 是 Codex plugin manifest；版本号以该文件为准，并且必须声明 `skills: "./skills/"` 与 `hooks: "./hooks.json"`。
- Source 改动不等于 runtime 已生效。发布或安装类任务必须在受影响时核对 plugin cache、custom agent runtime、hook wiring 和 SessionStart 输出。

## 目录合同

| 路径 | 责任 | 规则 |
| --- | --- | --- |
| `codex-orchestrate/architecture-draft.md` | Codex 架构权威 | 必须贴合 live source 合同；不要为了让文档好看而改运行时行为。 |
| `codex-orchestrate/skills/` | Codex skill 入口 | 保留 route graph 和 phase contract；phase reference 必须能从所属 skill 找到。 |
| `codex-orchestrate/agents/*.toml` | Codex custom agents | agent 指令必须自足；subagent 不会自动继承父 skill 的 references。 |
| `codex-orchestrate/hooks.json` | Codex hook manifest | hook 注册在这里；`hooks/` 只放可执行 handler。不要迁回 `hooks/hooks.json`。 |
| `codex-orchestrate/hooks/` | Hook handlers | 使用 Codex payload 和 plugin-root 路径，不使用旧宿主 payload 名称或依赖 cwd 的路径。 |
| `codex-orchestrate/scripts/` | 状态、派发、验证、summary 工具 | 状态路径属于 `.codex/multi-model-workflow/`；不要给旧 runtime 加 fallback。 |
| `codex-orchestrate/state-schema/` | workflow / execution state 合同 | schema、`state.sh`、validators 和生成文本必须一致。 |
| `codex-orchestrate/build/` | template / resolver 系统 | 改 template 要 build apply/check；生成片段必须和 resolver 输出一致。 |
| `docs/orchestrate/` | 设计与审查证据 | workflow 行为、成熟度标准、route 语义或验收门槛变化时同步更新。 |

## Workflow 合同

- `orchestrate-workflow` 是 coordinator 入口。Formal work 依次走 discovery、plan writing、execution、final review 和 closing。
- Route 2 处理未知根因 bug；Route 3 处理 multi-PR merge；Routes 4-7 分别覆盖 hotfix、quick fix、spike、maintenance。不要把这些路线压成一个泛执行流程。
- Codex App 启动的 workflow 常位于 `.codex/worktrees/...` detached HEAD。进入正式执行前必须先在当前 worktree 创建命名分支；如果当前目录是主仓库，则只允许先创建独立 worktree，不得在主仓库直接切任务分支。
- 派发必须是 Codex-native：使用 `spawn_agent`、`resume_agent`、`send_input`、`wait_agent`、`close_agent`，并调用已注册的 `pack_executor`、`complex_pack_executor`、`plan_writer`、`codex_reviewer`、`root_cause_analyst` 和 explorer agents。
- 派发后必须尊重 sub-agent ownership：Coordinator 不重复执行已派发的同一任务，不用短间隔轮询催促，不在未完成时要求中间结论，不中断或关闭仍在运行的 agent。等待期间只能做不重叠的协调工作；需要结果才能继续时就等待 `wait_agent` 返回。
- sub-agent 生命周期必须闭合：`wait_agent` 返回 final status 且结果已保存/写入 state 后，立即 `close_agent` 释放容量；后续需要同一 owner 续修或 targeted re-review 时，先 `resume_agent` 再 `send_input`，再次等待、保存结果并关闭。不得让 completed agents 长期挂起占用并发上限。
- Pack / review prompt 必须自带 scope、anchors、return contract 和 routing vocabulary。不要假设 worker 或 reviewer 能从父 skill 隐式推断上下文。
- 高风险合同栈是 `workflow-state` / `execution-state`、`DISPATCH_ENVELOPE`、dispatch validators、hook registration、template-generated text、review budget 和 verify harness。成熟度或 runtime 变更必须逐层核。
- Hook 的价值在于从 Codex plugin manifest 自动触发。能手动运行的 helper script 不等于 hook wiring 已生效。
- `plugin/` 可以提供行为意图，但 Codex 落地必须使用 Codex-native 路径、payload、subagent 字段、state file 和安装合同。

## 改动纪律

- 改动前先读 `README.md`、本文件、相关 `codex-orchestrate/**/agents.overrides.md` 和实际要动的源码。
- 改 `codex-orchestrate/` 子目录时，同步检查本层或上层 `agents.overrides.md` 是否需要更新。
- 文档、计划、skill、reference、agent 指令、template 和面向用户 / agent 的源码文字默认使用中文。英文只用于必要的命令、路径、协议字段、工具名、代码标识符、API 名称和不可翻译的宿主术语。
- 如果当前目录是 Codex App detached worktree，先在原地创建命名分支再改文件；已有任务名时用 `codex/<task-slug>`，尚未确定任务名时用 repo/date/worktree id 组成临时分支名。如果当前目录是主仓库主分支，先创建 Codex 约定路径下的 worktree，再进入 worktree 工作。不要在主仓库直接新建或切换任务分支。
- 除非用户明确要求 Claude Code plugin 工作，否则不要修改 `plugin/`。
- 不要重建 `.agents/skills/orchestrate-*` 或旧 `codex/` 源码树作为当前权威。
- Source 改动完成后不要自动同步到 runtime。常规修复以 source diff、验证结果和 commit 为交付边界；只有用户明确要求安装、发布、同步 runtime，或在汇报 source 验证结果和 runtime dry-run 差异后获得明确确认，才允许写入 `~/.codex/plugins/cache/`、`~/.codex/agents/` 或 `~/.codex/config.toml`。
- commit 要原子且及时。一个有意义的 repo rule、runtime contract、hook、build 或 doc-sync 改动应单独提交；不要把多个 phase、多个 pack 或多轮修复堆到最后一次性提交。
- 纯文档、规则、计划或提示词改动不新增无意义测试。验证应证明真实合同：`git diff --check`、build check、生成器 check、路径 / 链接校验、manifest / schema 校验或人工可审查 diff。不要为了断言某句文字存在而新建 grep 测试，除非那句话是生成产物或 runtime contract 的正式锚点。

## 验证门槛

按改动面选择能证明合同的最小验证。涉及 Codex Orchestrate 行为时优先使用：

```bash
bash codex-orchestrate/build/build.sh --check --plugin-dir codex-orchestrate
bash codex-orchestrate/scripts/run-all-tests.sh
bash codex-orchestrate/scripts/verify-maturity.sh
bash codex-orchestrate/scripts/validate-plugin-contract.sh codex-orchestrate
```

当前系统级 `validate_plugin.py` 如果拒绝 `.codex-plugin/plugin.json` 的 `hooks` 字段，不代表本仓库 manifest 错误。Codex Orchestrate 必须保留 `"hooks": "./hooks.json"`；此时以 `build.sh --check`、`run-all-tests.sh`、`verify-maturity.sh` 和 manifest/hook source 审查作为权威验证，不为了通过旧 validator 删除 hooks。

发布或安装类任务还要验证 source/runtime parity，不要只相信安装输出。按 manifest 版本核对 `~/.codex/plugins/cache/multi-model-workflow/multi-model-workflow/<version>/` 下的 plugin cache、`~/.codex/agents/` 下的 agent TOML，以及本次改动涉及的 hook / SessionStart 行为。
