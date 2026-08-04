# AGENTS.md

## 仓库范围

`mmw/` 是仓库唯一活跃的多模型工作流（Multi-Model Workflow，MMW）插件。它共享一套产品语义；Claude Code 与 Pi 有正式发布入口，Cursor 通过 `mmw agents materialize` 安装原生 subagent。

| 宿主 | 发布入口 | 角色执行后端 |
| --- | --- | --- |
| Claude Code | `mmw/.claude-plugin/plugin.json`、根 `.claude-plugin/marketplace.json` | GPT 走后台 Codex CLI；Claude 走后台 Agent 工具 |
| Pi | `mmw/package.json` | 原生 `subagent` 直调；型号/思考档/async/context/skill 在 `agents-pi` frontmatter；不经 `mmw dispatch` |
| Cursor（安装面） | `mmw agents materialize --host cursor` → `~/.cursor/agents/` | 原生 subagent；frontmatter 由同一套 `agent-src/` 按 profile 生成 |

原生多模型宿主的 agent 文件不要手改 model 行。改 `.mmw.json` 或 `mmw/cli/mmw.default.json` 后执行：

```bash
mmw agents materialize --host pi      # 更新包内 agents-pi/
mmw agents materialize --host cursor  # 安装到 ~/.cursor/agents/
```

`archive/` 是冻结归档。归档内容不参与行为判断、构建、测试或发布；没有明确指令时不修改。旧 Claude Code、Factory Droid、Pi 和 Cursor 插件统一归档在 `archive/legacy-host-plugins/`。

`vendor/mattpocock-skills/` 是上游 `mattpocock/skills` 的完整副本，通过 Git subtree squash 更新。不要手改；更新时运行：

```bash
git subtree pull --prefix vendor/mattpocock-skills https://github.com/mattpocock/skills main --squash
```

根文档保留 `AGENTS.md`、`CLAUDE.md`、`TESTING.md`。根 `mmw-skill-map.html` 是当前 MMW 架构的可视化产物，必须保留并随架构变化更新。不要新增其他 README、架构、设计、调查、计划或审查类根文档。长期规则写本文件；运行行为写 `mmw/skills/`、`mmw/cli/` 与测试。

## 唯一事实来源

同一项行为按以下顺序核对：

1. Claude Code manifest、根 marketplace 或 Pi package。
2. `mmw/cli/` 的机械动作、宿主 adapter 和 `.mmw.json` 配置合同。
3. `mmw/skills/` 的流程判据与方法论。
4. `mmw/cli/tests/`、`mmw/release/tests/`、`mmw/mcp/` 和 `mmw/graph/tests/`。

`.mmw.json` 保存目标仓库的模型档、标签、路径和领域文档形态。技能不硬编码这些值；通过 `mmw` 对应子命令读取。

`.mcp.json` 是检索服务器声明的唯一事实来源。占位符只由 `mmw/mcp/resolve.py` 展开。图谱只由 `mmw graph build` 更新；Graphify 和 Serena 的结果都是候选，关键结论必须回当前源码验证。

## 宿主边界

共享角色、技能和流程语义。宿主差异留在原生 agent frontmatter、`mmw/cli/adapters/`、manifest 与 `.mmw.json` 的 hosts 覆盖：

- Claude Code 的 GPT 角色通过后台 Bash 执行 Codex CLI；Claude 角色通过后台 Agent 工具执行。这个宿主只接 claude 与 gpt 两个模型族。派发走 `mmw dispatch`，由 adapter 写出工具参数。
- Pi / Cursor 的全部角色走宿主原生 subagent。型号、思考档、`async`、`context`、`skill` 物化在 agent frontmatter（`mmw agents materialize`）。**运行时主 agent 直调原生工具**，只传 agent 名、task（指令与路径，不粘文件正文）、可写时的 cwd；不经 `mmw dispatch` 转发。可写前确认 worktree 干净（`git status`）。
- 模型分配默认各宿主相同。某个宿主接不了基线模型时，在 `.mmw.json` 该角色底下写 `hosts.<宿主>` 覆盖，按字段生效。
- 流程技能写「打开并执行 `/mmw-dispatching-agents` 的「启动」四节」，并写明角色与 cwd；不写型号、不写宿主工具参数细节。**派发技能正文按发布面写死**：Pi 包与 Cursor 安装面用 `mmw/skills/mmw-dispatching-agents`（原生 agent 直调）；Claude Code 用 `mmw/skills-claude-code/mmw-dispatching-agents`（只 `mmw dispatch`）。同一技能名，两套正文，安装哪面就只看见哪套，禁止在一份正文里让 agent 按宿主二选一。
- 运行时不得探测、调用或回退到归档插件。

## 修改规则

- 改技能前读完整 `SKILL.md` 及其链接的 reference。测前读根 `TESTING.md`。
- 只实现请求范围内行为；不用归档残留、兼容目录或静默默认值掩盖错误。
- 脚本异常必须非零退出或留下结构化告警。
- Claude Code 版本同步修改 `mmw/.claude-plugin/plugin.json`、根 marketplace 的插件版本和 marketplace 顶层版本。Pi 同步修改 `mmw/package.json`。
- `mmw/skills/mmw-setup/` 只保存旧背景材料，不是技能。扫描技能正文时必须排除它。
- 每份流程技能以 `## 下一步` 收尾。表格固定为“情况、下一步”两列，动作只用“自己继续”“移交”“停”。只有 agent 无法开启新会话或需要用户决定时才停。
- 审查方法论只在 `/mmw-reviewer`；`/mmw-review` 只管编排。审查者通过安装的技能读取方法论，不把整份方法论粘进提示词。
- 技能引用另一个技能时写 `` `/技能名` ``。同名分支、标签值和文件路径不加斜杠。
- 领域文档位置必须通过 `mmw domain path` 与 `mmw domain dirs` 获取，不写死根 `CONTEXT.md`。
- 派发角色名使用 CLI / `roles.json` 字面串并加反引号（如 `worker`、`planner`），不另起中文名。Claude Code 路径里的 `mmw dispatch` 角色参数同此。
- CLI 不带参数只列命令名；每条命令的参数进入自己的 `usage_*`。认不出参数时只输出该命令的用法。
- Shell 变量后紧跟非 ASCII 字母、数字或下划线时使用 `${var}`，避免非 UTF-8 locale 误解析。
- 技能正文不得使用“同上”“见上”“前面那条”等位置指代。每次写清文件路径、技能名、节名或完整清单。

## 术语

| 概念 | 使用 | 不使用 |
| --- | --- | --- |
| 发起并协调其他 agent | 主 agent | 主线程 |
| 被派出的执行者 | subagent | 子代理、sub-agent |
| 写代码角色 | `worker` | 工人、写码工人 |
| 写计划角色 | `planner` | 计划工人 |
| 审查角色 | 审查者；具体写 `reviewer-gpt`、`reviewer-claude` | 审者 |
| 非交互式 Codex | headless | 无头 |
| 派发任务说明 | task / brief | 简报 |
| subagent 交回内容 | 报告 | 回执、笔记 |
| 主 agent 检查事实 | 验证 | 复核、核验、亲验 |
| 可点击的位置 | 出处 | 锚 |
| 唯一权威内容 | 唯一事实来源 | 真相源、事实源 |
| 必须用户确认的关卡 | 人工审批关卡 | 人闸 |
| 建隔离目录 | 建 worktree | 建树、进树 |
| 发送到外部系统 | 对外发布 | 出站动作 |
| sandbox 与工具白名单 | 护栏（guardrails） | 围栏 |

有行业标准中文译名时使用标准中文；没有时使用英文原词。不要自造术语、缩写或比喻性动词。

## Git 与安全

- 正式改动在独立 worktree；合回主分支使用 `git merge --no-ff`，禁止 squash。
- 本地提交和合并可自主执行。`git push`、远端合并、部署和正式发布必须得到用户明确授权。
- subagent 报告不是唯一事实来源。关键定位、测试结果和发布结论由主 agent 用当前源码或运行结果验证。
- 删除、覆盖、归档或移动现有发布入口前确认用户授权。
- 禁止使用 `--no-verify`。

## 构建与测试

完整门控以根 `TESTING.md` 为准。最低提交门槛：

```bash
for test_file in mmw/cli/tests/test_*.sh; do bash "$test_file" || exit 1; done
for test_file in mmw/release/tests/test_*.sh; do bash "$test_file" || exit 1; done
(cd mmw/mcp && uv run --quiet --with pytest pytest test_graphify_ensure.py -q) || exit 1
(cd mmw/graph && uv run --quiet --with pytest pytest tests/test_graph.py -q) || exit 1
(cd mmw/release/tests && uv run --quiet --with pytest --with pydantic pytest \
  test_release_contracts.py test_release_script_assembler.py -q) || exit 1
```

提交前运行 `git diff --check`。本次改动的 JSON 使用 `python3 -m json.tool` 校验；本次改动的 Shell 使用 ShellCheck 校验。
