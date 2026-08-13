---
slug: grok-host
summary: 把 Grok Build 做成完整 MMW 宿主，切断 Claude 兼容加载，接上全部技能、角色、工作树和外部工具。
date: 2026-08-13
branch: grok-host
spec_issue: 0
artifact_refs: []
---

# Grok Build 完整宿主 spec

> 来源：用户在 Grok Build 会话中确认「方案看起来可以了」，并要求写成 spec，再核对每一个 MMW 细节，特别是外部工具。输入是该会话中已经确认的决定，以及对照 Cursor 宿主计划与当前源码核对过的事实。没有单独保存的 research 目录。

## Problem Statement

用户在 Grok Build 里使用 MMW。MMW 现在不认这个宿主。本机会话加载的是 Claude Code 展开的技能，启动句是 `mmw dispatch`。工人没有单独的结果树合同。检索服务器、走查浏览器、并行 ticket 用的 Herdr、编辑后诊断，都没有 Grok 自己的安排。用户无法在 Grok 上完整走完 MMW。

## Solution

把 Grok Build 做成与 Pi、Claude Code、Codex 同级的 MMW 宿主。宿主名是 `grok`。

这是 Grok Build 的适配。共享资源的行为对 Pi、Claude Code、Codex 必须保持原样。只给 Grok 增加自己的面。

技能源仍是一份。物化时整块替换启动块和进树块。Grok 展开只出现 Grok 自己的动作。现有宿主的展开函数与展开正文不得改语义。

建树由 Grok 做。MMW 只绑定。改正式代码的工人由 Grok 另开一棵结果树。查、审、写 plan 不另开结果树。prototype 变体工人继续走技能源里现有的 `worktree` 合同，不在本 spec 改成四宿主同树。

外部工具有各自的安装面和 doctor 检查：三台检索服务器、GitHub CLI、语言检查器、Playwright、Herdr、`mmw` 命令本身。不改这些工具的共享声明和共用规则表。

## Current State

`mmw_host` 只认 Claude Code、Pi、Codex。本机会话里 `mmw task state` 失败。

技能物化只支持 `pi`、`claude-code`、`codex`。非 Pi 一律走 Claude 的 `mmw dispatch`。

角色物化只有 Pi 和 Cursor 的 profile。没有 Grok 的角色文件。

`install.sh` 没有 Grok 分支。`install-mcp.sh` 只写 Pi 和 Cursor 的用户级 MCP。

`task bind` 在 detached worktree 上只许 Codex。可写目录不认 `~/.grok/worktrees/`。

本机 `grok inspect` 把 Claude Code 的 MMW 插件当成 `plugin: mmw [claude]` 加载。29 个技能、hooks、三台检索服务器都来自这份 Claude 插件。`grok plugin list` 显示没有安装任何 Grok 插件。`[compat.claude]` 默认开。`[compat.cursor]` 本机已关。

本机 `grok models` 只有 `grok-4.6` 和 `grok-4.5`。PATH 上的 `agent` 是 Cursor CLI，不是 Grok。`herdr agent` 的 kind 列表含 `grok`。本会话在 Herdr 里，`HERDR_ENV=1`。

Grok 没有内置浏览器。Grok 的 `PostToolUse` hook 忽略 stdout。能把正文交回模型的是 `Stop` 与 `SubagentStop`。

技能源里 `prototype-worker` 仍是 `:worktree`。没有 `[[mmw-enter-worktree]]` 占位。本 spec 不把前者改成四宿主同树。

## User Stories

1. 作为在 Grok Build 里工作的用户，我希望 `mmw` 认出当前宿主是 `grok`，以便任务、派发和 doctor 能跑。

2. 作为主 agent，我希望显式指定 `MMW_HOST=grok` 时也能认出宿主，以便在探测失败时仍能工作。

3. 作为主 agent，我希望打开技能后看到的是 Grok 的启动句，以便去调 `spawn_subagent`，而不是 `mmw dispatch`。

4. 作为用户，我希望用 `/mmw-start`、`/wait-what`、`/handoff` 这三个 slash 启动对应技能，以便只有我能发起这三件入口工作。

5. 作为主 agent，我希望模型不会自动调用上述三个入口技能，以便它们保持用户发起。

6. 作为主 agent，我希望派 `investigator` 时只开一个只读的原生 subagent，以便查事实时不建结果树。

7. 作为主 agent，我希望派 `designer` 时只开一个只读的原生 subagent，以便出 interface 主意时不建结果树。

8. 作为主 agent，我希望派审查时仍是两个审查角色，以便 ⓪①②⑤ 的双角色合同不变。

9. 作为主 agent，我希望两个审查角色用两个不同的 Grok 模型，以便换模型而不是只换上下文。

10. 作为主 agent，我希望派 `planner` 时工人留在当前任务 worktree，以便 plan 写在任务分支上。

11. 作为主 agent，我希望派 prototype 变体工人时仍走技能源里现有的 `worktree` 合同，以便不改其他宿主的 prototype 行为。

12. 作为主 agent，我希望派 `worker` 或 `worker-high-risk` 时 Grok 给工人单独一棵结果树，以便实现提交不进任务分支。

13. 作为工人，我希望进结果树后先 `mmw task bind`，以便结果分支、工作名和基点 SHA 绑在一起。

14. 作为主 agent，我希望工人交回结果分支名、HEAD SHA 和基点 SHA，以便跑 `mmw result verify`。

15. 作为主 agent，我希望用 `mmw result integrate` 合并结果，以便不走 Grok 自带的 apply worktree。

16. 作为主 agent，我希望续跑工人或 planner 时用 Grok 的续跑通道，以便带着原上下文修，而不是假装没有续跑。

17. 作为主 agent，我希望句柄取不到时按现有材料清单重派，以便不静默当成新派发。

18. 作为主 agent，我希望在 Herdr 里给每张并行 wayfinder ticket 开一个顶层 Grok 窗口，以便绕过「subagent 不能再派 subagent」。

19. 作为主 agent，我希望每张 decision ticket 有自己的任务 worktree，以便并行票互不覆盖。

20. 作为主 agent，我希望 Grok 建树后只跑 `mmw task bind`，以便不调用已被拒绝的 `mmw task new`。

21. 作为主 agent，我希望 `mmw task cleanup` 在 Grok 上被拒绝，以便回收由 Grok 做。

22. 作为主 agent，我希望任务树和结果树都落在 `~/.grok/worktrees/`，以便不写进仓库内 `paths.worktrees`。

23. 作为主 agent，我希望结果分支名就是 slug 本身，以便不发明 `grok/` 前缀。

24. 作为主 agent，我希望在任务 worktree 里查符号、查结构、查库文档时三台检索服务器可用，以便检索合同与其他宿主相同。

25. 作为主 agent，我希望这三台服务器的路径指向已安装 runtime，以便不回源码 checkout。

26. 作为主 agent，我希望 Serena 按启动时的当前目录认项目，以便 Herdr 在任务树里启动的会话查的是这棵树。

27. 作为主 agent，我希望走查 prototype 时用 Playwright，以便 Grok 没有内置浏览器时用户仍能操作页面。

28. 作为主 agent，我希望 Playwright 和内置浏览器都没有时停下，以便不把只给 URL 当成走查完成。

29. 作为主 agent，我希望改完文件后诊断能回到对话里，以便先看检查器结果再继续。

30. 作为主 agent，我希望诊断走 `Stop` hook，以便不使用忽略 stdout 的 `PostToolUse`。

31. 作为用户，我希望 doctor 在 Grok 会话里检查安装面和外部工具，以便坏了能当场看见。

32. 作为用户，我希望安装时不整文件覆盖 hooks 和 MCP 配置，以便本机已有的 Herdr hook 还在。

33. 作为用户，我希望 Grok 工人看见的是 Grok 展开的 MMW 技能，以便不再同时吃到 Claude 的 `mmw dispatch` 正文。

34. 作为用户，我希望不删除 `~/.claude` 也能做到上一件，以便 Claude Code 继续可用。

35. 作为用户，我希望 PATH 上继续用 `grok`，以便不会误调名为 `agent` 的 Cursor CLI。

36. 作为用户，我希望 `mmw init` 仍只配仓库，以便换仓库不必重做 Grok 安装面。

37. 作为用户，我希望 tracker、artifact、graph、release、closing 的 CLI 行为不变，以便这些命令不按宿主分岔。

38. 作为维护者，我希望 `bash mmw/test.sh` 锁住 Grok 的物化和生命周期合同，以便漏写 `expand_grok` 会当场失败。

## Implementation Decisions

### 共享资源不得改行为

本 spec 只适配 Grok。下面这些共享资源，对 Pi、Claude Code、Codex 的外部行为必须与改前相同。

| 共享资源 | 本 spec 允许 | 本 spec 禁止 |
| --- | --- | --- |
| 技能源里的流程正文、launch 占位、角色 cwd_mode | 只为进树增加一个物化块，见下 | 改 launch 的角色或 cwd_mode；按宿主名写分支；改「按能力」的走查、检索、`gh` 句子 |
| `expand_pi` / `expand_claude` / `expand_codex` 与审查组在这三家上的展开 | 不改 | 改函数语义，或让现有三家产物换启动句 |
| 八角角色的共享 body、`roles.json` 的 skill 与 description | 不改 | 改「在独立 worktree」等会进所有宿主角色文件的句子 |
| Codex 后台 Worktree 任务名单与原生 subagent 名单 | 不改 | 从名单里拿掉 `prototype-worker` |
| `mmw/.mcp.json`、规则表、工具链模板、`artifacts.json` | 不改声明与规则 | 为 Grok 另写一套服务器清单或检查器 |
| MCP 展开器已有格式 | 可新增 Grok 输出格式 | 改 Pi、Cursor、Codex 格式的字段或路径规则 |
| `mmw init`、toolchain detect/apply/install/check、tracker、issue、artifact、graph、release、result | 不改命令语义 | 让这些命令按宿主分岔 |
| Pi / Claude Code 的可写目录规则 | 不改 | 把 Grok 的 `~/.grok/worktrees/` 例外开给这两家 |
| 现有三家的安装步骤与诊断通道 | 只追加 Grok 行 | 重写 Claude LSP、Codex hook、Pi 扩展的既有步骤 |
| 领域文档与 `AGENTS.md` | 宿主表追加 Grok；`host-runtime` 补 Grok 安装面 | 改其他宿主已有定义的含义 |

唯一允许改技能源的共享编辑：把「`mmw task new` 之后切换到返回路径」这类进树句换成 `[[mmw-enter-worktree]]`。原因：这些句子在 Grok 上会去调已被拒绝的 `task new`。Pi、Claude Code、Codex 对这个块的展开必须等于今天的正文。物化测试必须锁住这三家进树句不漂。除此之外不改技能源。

### 宿主身份

宿主字面值是 `grok`。

探测顺序保持现有顺序，并在 Codex 探测之前增加 Grok：当前进程存在 `GROK_AGENT`，且没有 `CLAUDECODE`、`PI_CODING_AGENT`、`CODEX_THREAD_ID` 时，宿主是 `grok`。`MMW_HOST=grok` 始终覆盖。

`GROK_AGENT` 在 Grok 文档里表示自定义 agent 名。本机普通会话把它设成 `1`。探测只看变量在不在，不看取值是不是路径。实现前必须在普通 TUI、`grok -p`、Herdr 窗格各证实一次。证实失败则只保留显式 `MMW_HOST=grok`，并让 doctor 报「没有稳定探测标识」。

认不出时的错误文案加上 Grok。

### 安装面

不注册 Grok marketplace plugin。不把 `mmw/` 源码仓库当成 Grok plugin 根。Grok 没有第六处产品版本号。

安装打散到用户目录：

- 技能产物 `skills-grok/` 同步到 `~/.grok/skills/`，只同步受管的 `mmw-*`、`wizard`、`handoff`、`wait-what`、`to-questionnaire`、`writing-for-agents`
- 角色同步到 `~/.grok/agents/mmw-*.md`
- 诊断 hook 拷到 `~/.grok/hooks/`
- 三台检索服务器合并进 `~/.grok/config.toml` 的 `[mcp_servers]`

用户自有技能、自有 agent、自有 MCP、自有 hook 不动。合并去重，禁止整文件替换。本机已有 Herdr 的 `SessionStart` hook，必须保留。

`~/.grok/skills/` 的同名技能优先于 Claude 插件技能。这样 Grok 展开的 `mmw-*` 会盖住 Claude 展开的同名技能。doctor 仍必须检查 Claude 兼容是否还在喂 MMW 的 hook 或另一套 MCP。若 Claude 的 MMW hook 仍在加载，doctor 报出来，并写明把 `[compat.claude] hooks` 设为 `false`。安装脚本不自动改用户的全部 Claude 兼容开关。

### 技能物化

`--host` 增加 `grok`。`all` 变成 `pi, claude-code, codex, grok`。默认产物目录增加 `skills-grok`。

必须有独立的 `expand_grok`。禁止「不是 Pi 就走 Claude」。漏写则物化测试失败。`expand_pi`、`expand_claude`、`expand_codex` 的返回值不得改。

审查组在 Grok 上走双角色。不要改 Codex 现有的单模型降级。

`[[mmw-resume]]` 只改 Grok 产物：原生 subagent 用 `resume_from`；若该实例是顶层 `grok` 会话，用 `grok --resume <sessionId>`。句柄取不到时退回现有材料清单。Pi 与 Codex 继续用现有退路。Claude Code 继续用现有 `mmw dispatch --resume`。

新增 `[[mmw-enter-worktree]]`，只替换进树那一类句子。Pi、Claude Code、Codex 展开必须等于今天的正文：

- Pi：现有 `mmw task new`，再用返回路径作 cwd
- Claude Code：现有 `mmw task new`，再 `EnterWorktree`
- Codex：禁止 `task new`；已在树上则 `bind`
- Grok：禁止 `task new`。Herdr 里用 `herdr worktree create --path ~/.grok/worktrees/<repo>/<slug>`，在该路径启动 `grok`，再 `bind`。已有树则新窗格的 cwd 指到该路径再启动，再 `bind`。不在 Herdr 且还没有树时，请用户用 `grok --worktree=<slug>` 开新会话，再 `bind`。不要 `git worktree add`。不要用终端 `cd` 代替把会话放进树。

Grok 会话必须在任务 worktree 里启动。不要先在主检出启动再改目录。Serena 按启动时的当前目录认项目。不改 Serena 的共享配置。

### 派发展开

`none`：调用原生 subagent。agent 设为角色对应的 `mmw-*`。只读角色加只读能力。task 传四栏表全文。互不依赖的实例在同一条消息里并行启动。

`current`：先确认 `mmw task state` 以 `bound` 开头。调用原生 subagent。该 subagent 使用当前任务 worktree。不创建结果 worktree。用 `cwd` 指向当前任务 worktree。不要打开 worktree 隔离。

`worktree`：用于技能源里现有的 `worker`、`worker-high-risk` 和 `prototype-worker`。先确认当前任务 worktree 为 `bound`，再取工作名。调用原生 subagent，打开 Grok 的 worktree 隔离。工人进 Grok 新建的那棵树后，先 `mmw task bind <结果分支 slug> "<目标栏原文>" --name <工作名> --from <基点 SHA>`，再工作并提交。交回结果分支名、HEAD SHA、基点 SHA。不要 `mmw task new`。不要让主 agent 直调 `grok -p` 当默认路径。不要用 Grok 的 apply worktree 代替 `mmw result integrate`。

`worktree` 启动句追加现有的派出后等待规则。只加在 Grok 产物里。

不改技能源里的 `prototype-worker:worktree`。不改 Codex 后台名单。不改共享工人 body。

Grok 的 subagent 不能再派 subagent。wayfinder 并行 decision ticket 必须是顶层 `grok` 进程，在 Herdr 里启动。不要用 Grok 的 workflow 脚本代替这套派发。

### 角色与模型

八角角色全部物化到 `~/.grok/agents/`。新建 Grok 的 profile。frontmatter 只写 Grok 认的字段：名字、说明、模型。只读角色用只读能力或只读权限，不写 Pi 的 `skill` 键。方法技能写进 Grok 产物的 body，不要改共享 body 文件本身。

只增加 `hosts.grok` 字段。不改其他宿主已有的 `hosts` 覆盖，不改基线模型。某个角色的基线族 Grok 跑不了时，只在 `hosts.grok` 里覆盖，不改基线。

- `reviewer-gpt` 使用 `grok-4.6`
- `reviewer-claude` 使用 `grok-4.5`
- 基线是 GPT 的角色，只在 `hosts.grok` 写成 Grok 能跑的模型

编排会话的模型由用户在 TUI 里选。doctor 提示把编排会话设成档里的 `orchestrator`。

### 任务树生命周期

`mmw task new` 与 `mmw task cleanup` 对 `grok` 拒绝。文案写明宿主负责建树和回收。

`mmw task bind` 在 detached linked worktree 上对 `grok` 放行。允许名单写成 `codex` 或 `grok`。不要收紧 Codex 现有的 bind 合同。

可写目录对 `grok` 的判据：

- 必须是 linked worktree
- 路径在 `$HOME/.grok/worktrees/` 下
- 不要求 `grok/` 前缀
- 不要求落在仓库 `paths.worktrees`

Pi 与 Claude Code 继续要求仓库内 `paths.worktrees/<slug>`。不要把 Grok 例外开回那两家。

回收由 Grok 的 `grok worktree gc` 或用户删除完成。doctor 写明这一点。

### 外部工具

下面每一件都是 MMW 会用到的外部工具。Grok 宿主必须有安装、使用和检查安排。没有单独安排的工具，沿用现有宿主无关合同。

**`mmw` 命令。** 继续由 `install.sh` 装到 `~/.local/bin/mmw`。工人和主 agent 都从 PATH 调用。doctor 检查命令在。

**`git`。** 建树、提交、绑定、集成都用它。Grok 的 worktree 隔离必须允许工人在结果树里提交。实现前实证 `git commit`。失败则这条工人主路径不能交出去。

**`gh`。** tracker、issue、PR、认领、标签、评论都用它。Grok 不另包一层。doctor 检查 `gh` 在 PATH，并检查 GitHub HTTPS 凭据。技能正文保持现有 `gh` 句子。

**`jq`。** CLI 与技能里的 JSON 处理用它。doctor 检查 `jq` 在 PATH。安装前置与现有 `install.sh` 相同：`git`、`python3`、`jq`、`node`。

**`python3`。** CLI、物化、MCP 展开、Graphify 入口用它。安装前置已有。

**`node` 与 `npx`。** Context7 服务器用 `npx` 拉起。安装前置已有。

**Serena。** 查符号定义、直接引用、实现、文件符号概览。服务器声明仍只来自 `mmw/.mcp.json`，本 spec 不改这份声明。Grok 安装把它写进用户 `config.toml` 的 `[mcp_servers.serena]`。命令与参数经展开器的新 Grok 格式翻译，路径指向 runtime，不是源码 checkout。已有 Pi、Cursor、Codex 格式不得改。启动参数保留 `--project-from-cwd`。主 agent 与工人都通过 Grok 的 `search_tool` / `use_tool` 调用，工具名是 `serena__` 前缀加原工具名。不另写 LSP 客户端。不给 Grok 工人套 Codex 那份检索纪律补丁，除非实证证明 Grok 也丢握手说明。

**Graphify。** 查模块关系、依赖路径、影响面、跨语言数据流。同样写入 `[mcp_servers.graphify]`，路径指向 runtime。调用方式与 Serena 相同，前缀是 `graphify__`。图只由 `mmw graph build` 更新。doctor 握手检查工具集。

**Context7。** `/mmw-research` 查库和框架官方文档。写入 `[mcp_servers.context7]`。密钥仍走现有占位符，不写进仓库。调用前缀是 `context7__`。

三台服务器只加不删。用户已有的其他服务器保留。同名的覆盖成 MMW 这一份。doctor 在认出 `grok` 时检查这三台都在、路径指向 runtime、并能握手。不要依赖「doctor 在 Pi 分支里顺便 check」。

**Herdr。** wayfinder 并行 grilling、research、prototype ticket 用它。主 agent 必须在 `HERDR_ENV=1` 的窗格。kind 是 `grok`。建树命令的 `--path` 必须指到 `~/.grok/worktrees/<repo>/<slug>`。不写没装 Herdr 的退路。doctor 在 Grok 会话里若没有 `HERDR_ENV=1`，提示并行 ticket 要在 Herdr 里开。单窗口串行做一张 ticket 仍允许。

**Playwright。** Grok 没有内置浏览器。prototype 走查走技能里已有的能力句：用当前环境的 Playwright；有 `playwright-cli` 时按现有步骤打开全部变体 URL。主 agent 必须亲自看到页面加载。两者都不可用时停下。不给 Grok 另写一套走查步骤。`playwright-cli` 来自跨宿主共用技能根 `~/.agents/skills`。隔离不得挡住这个目录。

**语言检查器。** 规则表、`mmw toolchain detect/apply/install/check`、CI 模板继续共用。不改规则表，不另写 Grok 规则表。不装 Claude Code 的语言服务器插件。编辑器红线用 Grok 已有的能力；agent 侧诊断以 `mmw toolchain check` 为准。

**编辑后诊断 hook。** 新建 Grok 自己的 hook 脚本。不要改、不要复用 Codex 与 Claude Code 那份退出码 2 脚本。Grok 的 `PostToolUse` 忽略 stdout，不能当诊断通道。脚本挂在 `Stop` 与 `SubagentStop`。stdin 是 Grok hook JSON。跑 `mmw toolchain check --changed-only`。有问题则输出 Grok 认的 `additionalContext`，让模型继续这一轮。没问题、`mmw` 不在 PATH、检查器崩了：退出 0，不输出。不改文件，不当格式化工具。matcher 以实证为准。CLI 工人若没有跑 hook，把「提交前自己跑 `mmw toolchain check`」写进 Grok 的 `worktree` 展开句，不改共享技能源，不改共享工人 body。

**`uv`。** 只属于 `mmw/test.sh` 里那几份 PEP 723 测试。Grok 宿主不另装。现有测试入口缺 `uv` 时已经非零退出。

**Grok CLI。** 顶层会话、`--worktree`、`--resume`、`--cwd` 用 `grok`。禁止调用名为 `agent` 的二进制。doctor 检查 `grok` 在 PATH，且 `agent` 即使存在也不当作 Grok。

**本机已有、但不属于 MMW 宿主合同的工具。** 用户技能里的 Feishu、Surge、Herdr 控制技能本身，只在用户点名时用。Grok 的图像工具、web_search、web_fetch 按技能里已有的能力句使用。不把它们写成 Grok 宿主的安装项。

### 领域文档与其余 CLI

`context_docs` 的宿主枚举加上 `grok`。Grok 只检查 `AGENTS.md` 领域块。不要要求 `CLAUDE.md`。不要改 Claude Code 现有的 `CLAUDE.md` 检查。Grok 若存在 `CLAUDE.md` 会读，但 MMW 领域块只写 `AGENTS.md`。

`mmw init` 的其余产物宿主无关：`.mmw.json`、TESTING.md、labels、gitignore、graphifyignore。Grok 不另做，也不改这些产物的现有内容。

tracker、issue、artifact、graph、release、result verify、result integrate 不按宿主分岔。

### 文档

`host-runtime` leaf 只追加 Grok：技能产物名单加上 Grok；说明 Grok 是用户目录安装面。不改 Codex 后台 Worktree 任务的现有拥有名单。

`AGENTS.md` 宿主表只增加 Grok 一行：安装面是 skills、agents、MCP、hooks；无 plugin 版本号。不改表里其他宿主的单元格。

`mmw-install` 只追加 Grok 的安装与诊断通道。不重写 Claude Code、Codex、Pi 现有步骤。

根技能地图只补 Grok 节点，不重排现有结构。

`walking` 的命名空间句不新开 Grok 分支。Grok 与 Pi 一样无前缀。不改这句的现有措辞。

### 测试

机械测试必须覆盖：

- 物化 host `grok`；`none` 与 `current` 无 `mmw task new`；`worktree` 含 worktree 隔离与 `task bind`、不含 `task new`；Grok 审查组双角色；Grok resume 含续跑；`prototype-worker:worktree` 在 Grok 上仍是结果树启动句；`[[mmw-enter-worktree]]` 的 Pi、Claude Code、Codex 展开与改前正文一致
- 现有 `--host pi`、`claude-code`、`codex` 的物化产物除进树占位替换外不得改语义
- `MMW_HOST=grok` 时 `task new` 与 `task cleanup` 拒绝；`task bind` 在 detached linked worktree 成功；可写目录接受 `~/.grok/worktrees/` 下的树，拒绝仓库内 `.worktrees/`
- `mmw_host` 在 `GROK_AGENT` 下认出 `grok`
- 技能路径扫描加上 `skills-grok`
- `context_docs` 宿主枚举含 `grok`
- `verify_source` 与 `--host all` 含 `grok`
- Grok hook 脚本：有诊断时输出含 `additionalContext`；无路径或无问题时退出 0；不得复用 Codex 退出码 2
- 技能展开句不含裸 `grok -p` 作为默认工人启动，也不含名为 `agent` 的二进制

实现前先实证再写死主路径。实证失败的那条不进主路径。

## Failure Paths

| 失败情况 | 触发条件 | 负责处理的边界 | 用户观察到的结果 | 系统行为 |
| --- | --- | --- | --- | --- |
| 认不出宿主 | 没有 `GROK_AGENT`，也没有 `MMW_HOST=grok` | `mmw_host` | 命令失败，文案点名 Grok | 不猜测宿主 |
| 误用 `task new` | 在 Grok 会话跑 `mmw task new` | `cmd_task` | 命令失败，说明宿主负责建树 | 不建仓库内树 |
| 误用 `task cleanup` | 在 Grok 会话跑 `mmw task cleanup` | `cmd_task` | 命令失败，说明宿主负责回收 | 不删 Grok 的树 |
| bind 拒绝 | 不在 detached linked worktree，或不在 `~/.grok/worktrees/` | `task bind` 与可写目录检查 | 命令失败，说明要用宿主已建的树 | 不绑定主检出 |
| 工人隔离实证失败 | 默认隔离下无法提交，或树不在约定根下 | 实现门 | 这条工人主路径不交出去 | 不停在半成品 |
| Claude 技能仍盖住 Grok 技能 | 用户目录没有 Grok 展开的同名技能 | doctor | doctor 失败，指出冲突来源 | 不静默双技能并存 |
| 检索服务器起不来 | 配置缺、路径指错、握手失败 | doctor 与 `mmw-retrieval` | doctor 报哪一台、怎么修 | 技能按现有降级：改用文本检索并写明 |
| 没有浏览器 | 没有 Playwright，也没有可操作页面 | prototype 走查 | 主 agent 停下，说明不能走查 | 不把 URL 当成完成 |
| 没有 Herdr | 用户要并行多张 wayfinder ticket，但不在 Herdr | wayfinder 并行入口 | 主 agent 说明必须在 Herdr 里开 | 不发明退路；单票仍可在当前窗口做 |
| 续跑句柄丢失 | 没有 `resume_from` 或 sessionId | resume 展开 | 按材料清单重派新实例 | 不假装上下文还在 |
| 诊断 hook 故障 | 检查器崩了或 `mmw` 不在 PATH | hook 脚本 | 无输出，不挡干活 | 退出 0 |
| 子 agent 再派子 agent | 工人或审查者调用 `spawn_subagent` | Grok 运行时 | 该调用失败 | 技能不要求子 agent 再派 |

## Testing Decisions

好测试只锁机器能判定的事实：展开正文、拒绝码、路径是否被接受、hook 的 stdin/stdout 形状、安装后目录里有没有受管文件。不锁产物质量，不锁「像不像好技能」。

测这些模块：技能物化、角色物化、任务生命周期、可写目录、宿主探测、doctor 在 `grok` 下的检查项、Grok hook 脚本、MCP 写入与 `--check`。

先例：现有物化测试、guardrails、`verify_source`、hook 脚本测试。Grok 按同一风格加宿主，不另开豁免。

| Seam | 验证的外部行为 | 选择这一层的原因 |
| --- | --- | --- |
| 技能物化 | 给定技能源和 `--host grok`，产物里的启动块、进树块、续跑块是 Grok 动作，且不含 `mmw dispatch`、`mmw task new`。给定同一技能源和现有三家 `--host`，进树块以外的展开与改前一致 | 现有物化测试已经锁三宿主展开。这是漏写 expand 会走错路径、也会误伤其他宿主的那一层 |
| 任务生命周期与可写目录 | `MMW_HOST=grok` 时 new/cleanup 拒绝，bind 在约定根下的 detached 树成功，仓库内 `.worktrees/` 被拒 | 现有 guardrails 已经锁 Pi 与 Codex。这是工人能不能开工的那一层 |
| 安装、doctor、MCP、hook | 装完后用户目录有受管技能、角色、三台检索服务器和 Stop hook；doctor 在 `grok` 下核对它们；hook 的输入输出符合 Grok 合同 | 外部工具坏了必须在这一层被看见，不能等到审查中途 |

## Release Risk

用户通过在 MMW 源码仓库重跑 `mmw/install.sh` 取得 Grok 安装面。装完后要开一个新的 Grok 会话，或重启当前会话，新技能和 hook 才加载。

安装只追加受管文件和三台检索服务器。它不覆盖用户已有的 hooks、MCP、技能。回滚是删掉 `~/.grok/skills/` 与 `~/.grok/agents/` 下受管的 `mmw-*` 文件，以及本次写入的 hook 脚本和三台服务器条目。不改用户其他配置。

未授权不 `git push`，不对外发布。

## Out of Scope

- 不把 MMW 做成 Grok marketplace plugin
- 不复活任何归档的旧 plugin
- 不在技能源里按「Grok」写分支
- 不在 Grok 上使用仓库内 `paths.worktrees`
- 不用 Grok workflow 脚本代替 MMW 派发或 wayfinder
- 不用 Grok 的 apply worktree 代替 `mmw result integrate`
- 不做 Cloud
- 不给 Grok 装 Claude Code 的语言服务器插件
- 不自写 LSP 客户端
- 不另写一份 Grok 语言规则表
- 不用 `PostToolUse` 当诊断通道
- 不调用名为 `agent` 的二进制
- 不靠改 `HOME`、不靠删 `~/.claude` 来避开 Claude 兼容
- 不挡 `~/.agents/skills`，不挡仓库 `AGENTS.md` 与 `CLAUDE.md`
- 不把用户点名才用的个人技能写成 Grok 安装项
- 不改其他宿主共享资源的外部行为，见「共享资源不得改行为」
- 不把 `prototype-worker:worktree` 改成四宿主 `:current`
- 不改 Codex 后台 Worktree 任务名单
- 不改 `mmw/.mcp.json` 与语言规则表

## Further Notes

技能与宿主动作覆盖。每一行都有本 spec 中的安排。

| 技能或动作 | Grok 安排 |
| --- | --- |
| `mmw-start` / `wait-what` / `handoff` | 保留 slash；模型不可自动调用；进树走 `[[mmw-enter-worktree]]` |
| `mmw-wayfinder` 建 map | Herdr 或 `grok --worktree` 建任务树，再 bind |
| `mmw-wayfinder` 并行 ticket | Herdr，`--kind grok`，每票一棵 `~/.grok/worktrees/` 任务树 |
| `mmw-grilling` / `mmw-research` / `mmw-to-spec` / `mmw-prototype` / `mmw-domain-modeling` / `mmw-diagnosing-bugs` / `mmw-improve-codebase-architecture` / `wizard` / `to-questionnaire` | 进树走同一占位；只读或同树工作按下面的 launch |
| `investigator:none` | 原生只读 subagent |
| `designer:none` | 原生只读 subagent |
| `reviewers:none` | 两个审查角色，模型分别是 `grok-4.6` 与 `grok-4.5` |
| `planner:current` | 同树原生 subagent；可续跑 |
| `prototype-worker:worktree` | 与现有宿主相同：结果树；Grok 用隔离 worktree 承接 |
| `worker:worktree` / `worker-high-risk:worktree` | Grok 隔离结果树；bind；verify；integrate |
| `mmw-resume` | `resume_from` 或 `grok --resume` |
| `mmw-implement` 回收结果树 | 宿主建的树由宿主回收，不跑 `task cleanup` |
| `mmw-integrate` | CLI 宿主无关；回收句按树的位置选 |
| `mmw-tdd` / 工人提交前 | 有 hook 用 hook；没有则自己跑 `mmw toolchain check` |
| `mmw-retrieval` | 三台服务器写入 Grok 用户配置；doctor 握手 |
| `mmw-install` | 只追加 Grok 打散安装与 Stop hook；不重写其他宿主步骤 |
| `mmw-release` / `mmw-closing` / `mmw-to-tickets` / `mmw-triage` / `mmw-planner` / `mmw-reviewer` / `writing-for-agents` | 正文按能力写，Grok 不另分岔 |
| Serena / Graphify / Context7 | 见「外部工具」 |
| `gh` / `jq` / `git` / `python3` / `node` | 见「外部工具」 |
| Playwright | 见「外部工具」 |
| Herdr | 见「外部工具」 |
| 语言检查器 | 共用规则表；Grok 走 Stop hook |
| `uv` | 仍只属于测试入口 |

实现顺序：先实证隔离、bind、续跑、hook、Claude 技能覆盖、Serena 在任务树里的项目根。过不了的那条不写进主路径。然后改 CLI，再物化，再安装与 doctor，再测试，再文档。
