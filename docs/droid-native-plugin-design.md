# Droid 原生多模型工作流插件迁移设计

日期：2026-07-13

## 目标

新建独立的 `droid-plugin/`，完整保留现有多模型工作流的业务能力，同时只面向 Factory Droid。原 `plugin/` 保持不变，两个插件不共享运行时代码，也不通过宿主判断维持兼容。

迁移完成后，Droid 专属版本必须继续提供：

- 四类入口：明确小改、新功能或改造、根因未知的 bug、多个 worktree 合并。
- 完整主流程：调查、方向提案、设计、设计审、issue 切片、计划、计划审、落地、合同门、最终审、打包、收尾。
- HITL 集中在方向与设计，计划阶段起支持无人值守。
- task、phase、step、loop、review、package、release 的磁盘账本与断点恢复。
- 并行调查、并行写计划、每个计划独立 worktree 落地、跨模型审查。
- 进度板、值守切换、计划外发现、重新评估、跳步、改范围、重排余下计划、强制验证等控制面。
- hooks 分诊、相位锚、红线拦截、提交记账。
- Worker 禁改 `docs/`、计划工人只准改 `docs/plans/` 与 `docs/issues/`、审查结论亲验、push/远端合并/部署需人工批准等安全门。
- Windows 打包与 release-flow 全部能力。

## Droid 原生边界

| 领域 | 目标状态 |
| --- | --- |
| 插件格式 | 只保留 `.factory-plugin/plugin.json`、`skills/`、`commands/`、`droids/`、`hooks/` 等 Droid 原生目录 |
| 状态平面 | 固定为 `.factory/multi-model-workflow/` |
| worktree 根 | 固定为 `.factory/worktrees/`，分支固定使用 `worker/` 前缀 |
| 插件定位 | 只扫描 `~/.factory/plugins` 与 Factory marketplace 记录，只读取 `.factory-plugin/plugin.json` |
| 工具语言 | 只使用 `Execute`、`Create`、`Edit`、`ApplyPatch`、`AskUser`、`Task`、`Read`、`Grep`、`Glob`、`LS`、`WebSearch`、`FetchUrl` |
| 并行执行 | 统一通过 `Task` 派 Custom Droid；独立工作优先后台运行，后续通过 task ID 获取结果或恢复 |
| 调查 | 使用 `investigate-topic`，内部与外部 topic 均可并行，不保留 Workflow 脚本 |
| 写计划 | 使用 `plan-writer`，主线程只编排、亲验和回填跨计划合同 |
| 写代码 | 使用 `pack-executor`，一个 plan 对应一个子 worktree |
| 审查 | 使用阶段专属 reviewer droids，写者与审者分离，最终审保持跨模型 |
| hooks | 只匹配 Droid 事件与 `Execute`，只引用 `${DROID_PLUGIN_ROOT}` |
| 状态恢复 | 只恢复 Droid 状态，不扫描、迁移或清理其他宿主目录 |

## 截至迁移日采用的 Droid 能力

迁移以 2026-07-13 Factory 官方文档为准：

- 插件原生支持 skills、commands、droids、hooks 与 MCP。
- Custom Droids 支持独立上下文、模型、reasoning effort、工具白名单和 autonomy。
- `Task` 支持前台流式进度、后台执行、task ID 查询、停止和恢复；子代理不能再派子代理，也不能调用 `AskUser`。
- skills 同时支持模型自动调用与 slash 调用；现有 commands 继续作为稳定控制面保留。
- hooks 使用 `SessionStart`、`UserPromptSubmit`、`PreToolUse`、`PostToolUse`、`Stop`、`SubagentStop` 等事件，插件路径使用 `${DROID_PLUGIN_ROOT}`。
- Droid CLI 原生支持 worktree、Spec Mode、分级 autonomy、`droid exec`、模型与 reasoning effort 选择。

## 角色与模型

模型 ID 以 Factory 当日模型目录为准。所有 droid 都使用有效的 reasoning effort 枚举。

| 角色 | 模型 | 责任 |
| --- | --- | --- |
| `investigate-topic` | `minimax-m3` | 单 topic 证据收集 |
| `code-explorer` | `kimi-k2.7-code` | 代码边界与数据流探索 |
| `decision-advisor` | `gemini-3.1-pro-preview` | 方向、设计或无人值守拍板时提供稀疏第二意见 |
| `plan-writer` | `gpt-5.6-terra` | 写单份可执行计划 |
| `pack-executor` | `glm-5.2` | 按计划 TDD 落地 |
| 设计与计划审查 | `claude-opus-4-8` | 两轴独立审查 |
| 最终审 A | `gpt-5.6-terra` | 回归、意图、跨计划合同 |
| 最终审 B | `claude-opus-4-8` | 独立代码审计 |

`decision-advisor` 替代不可用的旧顾问模型，保持顾问职责但不进入审闸。

## 实现结构

```text
droid-plugin/
├── .factory-plugin/plugin.json
├── commands/
├── droids/
├── hooks/
├── scripts/
│   ├── lib/runtime.sh
│   └── tests/
├── skills/
├── state-schema/
└── build/
```

`runtime.sh` 只提供固定 Droid 路径、插件根、状态定位、worktree 定位、工具名与忽略规则。它不接受宿主覆盖，不包含对端状态，不提供兼容分支。

## 派发与恢复合同

1. `mmw worker dispatch` 或 `plan-dispatch` 创建 worktree、边界基线和 prompt 包。
2. 主线程按回执调用 `Task`，使用指定 Custom Droid。互不依赖的任务并行并优先后台运行。
3. 主线程把返回的 task ID 写回对应 dispatch 账本。
4. 恢复时优先使用同一 task ID 的 `resume`，保留子代理上下文；不存在 task ID 才生成新的修复 prompt 并重新派发。
5. Task 完成后，主线程先执行机器边界检查，再亲验文件、diff、提交和测试，最后才推进 loop。

## 审查合同

- 设计审与计划审各派两路独立 reviewer。
- 小改和 bug 的最终审派一路 reviewer 覆盖两条基线。
- 普通 develop 最终审按风险和 diff 大小选择两路或四路。
- 高风险计划、数据缺失或 diff 过大时 fail-closed 使用四路。
- findings 原样落盘，主线程逐条亲验并写 verdict；审查 droid 的陈述不能直接作为事实。

## 兼容性与清理

Droid 专属插件不读取旧 `.claude/` 状态，也不提供 `MMW_HOST`、`CLAUDE_PLUGIN_ROOT`、`Bash` matcher、`AskUserQuestion`、Agent/Workflow、Codex CLI 或 Claude 插件 manifest。模型名称中的 `claude-*` 是 Factory 模型 ID，不代表 Claude Code 宿主兼容。

## 验收

1. Droid 专属插件独立通过所有脚本、构建、JSON 和 shell 语法检查。
2. 静态扫描除 Factory 模型 ID 外，不出现 Claude Code、Codex CLI、`.claude/`、`CLAUDE_PLUGIN_ROOT`、`MMW_HOST`、`Bash` matcher、`AskUserQuestion` 或 Workflow 调用。
3. 原插件的 route、phase、loop、command、hook、worker、review、package、release 能力在新插件中均有对应实现和测试。
4. 本地 marketplace 能同时识别原插件与 Droid 专属插件，名称和 source 不冲突。
5. 从零上下文安装后，第二个 Droid 能仅依赖插件自身完成新任务、断点恢复和收尾。
