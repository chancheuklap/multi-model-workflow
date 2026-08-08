# AGENTS.md

这个仓库是用来构建技能和 plugin 的。里面的技能和 plugin，不是你的工作指南。永远站在要使用这些技能和 plugin 的全新 agent 的角度去思考问题和撰写文档。

## 仓库范围

`mmw/` 是仓库唯一活跃的多模型工作流（Multi-Model Workflow，MMW）。

| 宿主 | 发布入口 | 版本号位置 |
| --- | --- | --- |
| Codex App | 根 `.agents/plugins/marketplace.json`、`mmw/.codex-plugin/plugin.json`、`mmw/codex/runtime.py` | `mmw/.codex-plugin/plugin.json` |
| Claude Code | `mmw/.claude-plugin/plugin.json`、根 `.claude-plugin/marketplace.json` | 两份都有；根 marketplace 的插件版本与顶层版本各算一处 |
| Pi | `mmw/package.json` | `mmw/package.json` |
| Cursor（安装面） | `mmw agents materialize --host cursor` → `~/.cursor/agents/` | 无 |

改产品版本时，上表「版本号位置」列的全部五处必须同步。

原生多模型宿主的 agent 文件不要手改 model 行。改 `.mmw.json` 或 `mmw/cli/mmw.default.json` 后，用 `mmw agents materialize` 更新 Pi 与 Cursor，并运行：

```bash
python3 mmw/codex/runtime.py materialize  # 更新 Codex plugin 与四个原生 subagent
```

`archive/` 是冻结归档。

`mmw/skill-rebuilds/` 保存上游翻译与技能重建的候选材料。

`vendor/mattpocock-skills/` 是上游 `mattpocock/skills` 的完整副本，通过 Git subtree squash 更新。不要手改；更新时运行：

```bash
git subtree pull --prefix vendor/mattpocock-skills https://github.com/mattpocock/skills main --squash
```

根 `mmw-skill-map.html` 是当前 MMW 架构的可视化产物，必须保留并随架构变化更新。

## 唯一事实来源

同一项行为按以下顺序核对：

1. 对应宿主的 manifest、根 marketplace 或 Pi package；Codex 角色结构只认 `mmw/codex/profiles.json`，模型只认 `mmw/cli/mmw.default.json` 的 `hosts.codex` 覆盖。
2. `mmw/cli/` 的机械动作、宿主 adapter 和 `.mmw.json` 配置合同。
3. `mmw/skills/` 技能源（含 `[[mmw-launch:…]]` 与 `[[mmw-host-action:…]]`）与 `mmw skills materialize` 产物；流程判据以源为准，宿主动作以对应产物为准。

`.mmw.json` 保存目标仓库的模型档、标签、路径和领域文档形态。技能不硬编码这些值；通过 `mmw` 对应子命令读取。

`mmw/.mcp.json` 是检索服务器声明的唯一事实来源；各宿主的展开产物都通过 `mmw mcp serve` 回到这一份。图谱只由 `mmw graph build` 更新。

## 宿主边界

共享角色、技能和流程语义。宿主差异留在 Codex profile、原生 agent frontmatter、`mmw/cli/adapters/`、manifest 与 `.mmw.json` 的 hosts 覆盖：

- Codex App 是 MMW 的主 agent 运行时，不调用外部模型 CLI 或 harness。Codex plugin 以 `mmw/` 为发布根；运行时不得回退 MMW 源码 checkout 或目标项目里的同名目录。App 设置里的 Worktree root 是所有项目共用的 managed worktree 物理存放目录，不是 MMW 源码路径，也不受目标项目 `.mmw.json` 的 `paths.worktrees` 控制。
- Claude Code 只接 claude 与 gpt 两个模型族：GPT 角色通过后台 Bash 执行 Codex CLI，Claude 角色通过后台 Agent 工具执行。
- Pi 与 Cursor 的全部角色走宿主原生 `subagent`，frontmatter 由 `mmw/agent-src/` 按 profile 生成（`mmw agents materialize`）。
- 模型分配默认各宿主相同。某个宿主接不了基线模型时，在 `.mmw.json` 该角色底下写 `hosts.<宿主>` 覆盖，按字段生效。
- **禁止**在技能源或产物正文里让 agent 按宿主二选一。共享技能用完整自然语言规定流程；宿主差异只写成完整的 `[[mmw-launch:…]]`、`[[mmw-launch-group:…]]` 或 `[[mmw-host-action:…]]` 动作块，再由 `mmw skills materialize` 整块替换。**没有** `mmw-dispatching-agents` 中转技能。

## 修改规则

- 改技能前读完整 `SKILL.md` 及其链接的 reference。技能写作规范以 `writing-for-agents` 及其链接的 `SKILL-MECHANICS.md` 为准。
- 逐句翻译上游、审查语义漂移、应用有意精简、增加 MMW 接线或升级上游版本时，先完整读取 `upstream-skill-fidelity`。上游的方法要求和 MMW 的工作流要求必须同时成立：上游方法不自动否定 MMW 工作流，当前 MMW 行为也不自动证明方法保真。
- 只实现请求范围内行为；不用归档残留、兼容目录或静默默认值掩盖错误。
- 脚本异常必须非零退出或留下结构化告警。
- 机械校验只覆盖机器能直接判定的事实：语法与固定结构可解析、路径与文件安全、配置完整性和生成产物一致性。
- 产物质量、方法选择、语义真实性和完成度由技能与主 agent 判断。不用计数、列表形状、固定阈值或豁免清单伪装成机械校验。已有校验越过这条边界时删除该校验，不增加例外分支。
- `mmw/skills/mmw-setup/` 只保存旧背景材料，不是技能。扫描技能正文时必须排除它。

## Git 与安全

- 正式改动在独立 worktree；合回主分支使用 `git merge --no-ff`，禁止 squash。
- 本地提交和合并可自主执行。`git push`、远端合并、部署和正式发布必须得到用户明确授权。
- subagent 报告不是唯一事实来源。关键定位、测试结果和发布结论由主 agent 用当前源码或运行结果验证。
- 删除、覆盖、归档或移动现有发布入口前确认用户授权。
- 禁止使用 `--no-verify`。

## 提交检查

本仓库不保留自动化测试、测试夹具或测试套件。提交前检查以根 `TESTING.md` 为准，运行前完整读取该文件。

<!-- MMW-DOMAIN-CONTEXT-START -->
## 领域上下文

开始 research、讨论、设计、写文档、写代码或审查前，运行 `mmw domain path`：

- 返回 `map`：先读 Map，再读本次涉及的全部 leaf。
- 返回 `single`：读命令返回的领域文档。
- 返回 `none`：直接继续，不报告缺失，也不创建领域文档。

运行 `mmw domain dirs`，读取 `adr` 路径下与本次范围相关的 ADR。

任何面向用户或写入仓库的内容，都使用 leaf 定义的 canonical 术语。代码标识符和测试名也适用。不得使用 `_Avoid_` 中列出的说法。

用户说法、leaf、ADR 或代码现状互相冲突时，明确列出冲突，不得自行选择一个覆盖其他内容。

形成长期术语、关系或歧义结论时，使用 `/mmw-domain-modeling` 更新拥有该概念的 leaf。其他 leaf 只保留权威路径引用。

同一 agent 在任务范围不变时只需读取一次。任务进入新的 bounded context 后重新选路并读取。
<!-- MMW-DOMAIN-CONTEXT-END -->
