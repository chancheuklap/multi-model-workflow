# AGENTS.md

这个仓库是用户的一整套工作流集合工具箱。它不是一个简单的技能仓库。任何有可能在不同的 agent harness、不同的仓库、不同的电脑上面使用的通用工作流工具，都应该由这个仓库管理，而不是写到某一个项目仓库里面。

这个仓库是里面的技能和工具，不是你的工作指南。永远站在要使用它们的全新 agent 的角度去思考问题和撰写文档。

## 仓库范围

`mmw/` 是仓库唯一活跃的多模型工作流（Multi-Model Workflow，MMW）。

MMW 不打包成任何宿主的插件。`mmw/install.sh` 是唯一安装入口：它从源码仓库构建稳定
runtime，再把五个组件装进每个宿主自己的用户级目录。

| 组件 | Claude Code | Codex App | Pi | Cursor | Grok Build |
| --- | --- | --- | --- | --- | --- |
| 技能 | `~/.claude/skills` | `~/.codex/skills` | `~/.pi/agent/skills` | `~/.cursor/skills` | `~/.grok/skills` |
| 原生 subagent | `~/.claude/agents` | `~/.codex/agents` | `~/.pi/agent/agents` | `~/.cursor/agents` | `~/.grok/agents` 与 `~/.grok/roles` |
| hooks | `~/.claude/settings.json` | `~/.codex/hooks.json` | 扩展目录 | `~/.cursor/hooks.json` | `~/.grok/hooks` |
| MCP | `~/.claude.json` | `~/.codex/config.toml` | `~/.pi/agent/mcp.json` | `~/.cursor/mcp.json` | `~/.grok/config.toml` |
| 权限 | `~/.claude/settings.json` | — | — | `~/.cursor/permissions.json` | — |

`mmw` CLI 与 `mmw-cursor-agent`、`mmw-ui-qa` 三个转发器装进 `$BIN_DIR`，五个宿主共用。

技能是软链，不是拷贝：升级 runtime 之后技能跟着变，不用重装。每个目标目录留一份
`.mmw-skills` 或 `.mmw-agents` 清单，装之前按它清理上一次装了、这次没有的那些。目录
里同名的东西不是 MMW 装的就一律不动，报冲突并非零退出。

产品没有插件版本号，也没有版本号闸门。以前那道闸门防的是插件缓存不刷新，没有插件
就没有缓存：改完跑一次 `mmw/install.sh`，宿主读到的就是新内容。

原生多模型宿主的 agent 文件不要手改 model 行。模型档只保存在 `mmw/cli/mmw.default.json`。角色产物不入库。五个宿主的 agent 文件都在 `mmw/install.sh` 里从源码渲染进各自的目标目录：Pi 落在已安装 runtime 的包目录（它的包合同要求 agent 文件在包内），另外四家落在宿主自己的用户目录。改完模型档或角色真源，跑一次 `mmw/install.sh` 即可；只想单独更新某一家时：

```bash
mmw agents materialize --host <pi|cursor|grok|claude-code|all>
python3 mmw/codex/runtime.py materialize      # Codex，写进 ~/.codex/agents/
```

目标仓库初始化只执行 `mmw init`；验收本机运行时时另行执行只读的 `mmw doctor`。

`archive/` 是冻结归档。

`mmw/skill-rebuilds/` 保存上游翻译与技能重建的候选材料。

`vendor/mattpocock-skills/` 是上游 `mattpocock/skills` 的完整副本，通过 Git subtree squash 更新。不要手改；更新时运行：

```bash
git subtree pull --prefix vendor/mattpocock-skills https://github.com/mattpocock/skills main --squash
```

根 `mmw-skill-map.html` 是当前 MMW 架构的可视化产物，必须保留并随架构变化更新。

## 唯一事实来源

同一项行为按以下顺序核对：

1. `mmw/install.sh` 的安装动作；角色真源是 `mmw/agent-src/roles.json`（五个宿主共用），Codex 的 `mmw/codex/profiles.json` 只补它自己的字段（哪些角色走后台 worktree、哪些走原生 subagent、各自的 `sandbox_mode`），模型只认 `mmw/cli/mmw.default.json` 的 `hosts.codex` 覆盖。
2. `mmw/cli/` 的机械动作、宿主 adapter、`.mmw.json` 配置合同和 `mmw/cli/artifacts.json` 的产物落点数据。
3. `mmw/skills-src/` 技能源。五个宿主装的都是它，没有第二份；流程判据以它为准。派发动作不在技能里，宿主差异只认 `mmw/cli/host-actions.json`，由 `mmw launch` 在运行期回答。

`.mmw.json` 保存目标仓库的标签、CLI 路径和领域文档形态。模型档属于已安装 runtime，不进入目标仓库配置。

产物落点由 `mmw artifact path` 回答。技能正文不写路径字面值。`.mmw.json` 的 `paths` 只配置 CLI 自己消费的 `scratch`、`reviews`、`release` 和 `worktrees`。

`mmw/.mcp.json` 是检索服务器声明的唯一事实来源；各宿主的展开产物都通过 `mmw mcp serve` 回到这一份。图谱只由 `mmw graph build` 更新。

## 宿主边界

五个宿主平权。没有主力宿主，也没有参考宿主：描述、默认值和文档示例都不得把某一个宿主当成默认或首选，也不得只给一个宿主写路径。

共享角色、技能和流程语义。宿主差异留在 Codex profile、原生 agent frontmatter、Claude Code 的 dispatch adapter（`mmw/cli/adapters/claude-code.sh`）、manifest 与 runtime 模型档的 hosts 覆盖：

- Codex App 的全部角色走它自己的原生 subagent 与后台 worktree 任务，不调用外部模型 CLI 或 harness。Codex 的技能与原生 subagent 由 `mmw/install.sh` 装进 `~/.codex/`；运行时读已安装 runtime，不回退 MMW 源码 checkout 或目标项目里的同名目录。App 设置里的 Worktree root 是所有项目共用的 managed worktree 物理存放目录，不是 MMW 源码路径，也不受目标项目 `.mmw.json` 的 `paths.worktrees` 控制。
- Claude Code 只接 claude 与 gpt 两个模型族：GPT 角色通过后台 Bash 执行 Codex CLI，Claude 角色通过后台 Agent 工具执行。
- Pi、Cursor 与 Grok 的全部角色走宿主原生 `subagent`。Claude Code 只有 `reviewer-claude` 一个原生 subagent：其余角色在这个宿主上都是 gpt 族，由 adapter 走后台 Codex CLI，不经过 subagent。四家的 frontmatter 都由 `mmw/agent-src/` 按 profile 生成（`mmw agents materialize`），profile 的 `roles` 键决定这个宿主收哪几个角色。
- 模型分配默认各宿主相同。某个宿主接不了基线模型时，在 `mmw/cli/mmw.default.json` 该角色底下写 `hosts.<宿主>` 覆盖，按字段生效。
- **禁止**在技能源或产物正文里按宿主名称分支。派发 subagent 写 `mmw launch <角色> --scope <范围>`、`mmw launch-group reviewers` 或 `mmw resume <角色> --scope <范围>`，正文只说跑哪条命令、照它打印的动作做；五个宿主拿到的是同一句。宿主差异全部收在 `mmw/cli/host-actions.json`，加一个宿主就是给那张表补一个 key，技能源和展开代码都不动；缺 key 时 `mmw launch` 当场失败，不回退到别的宿主的指令。任务树由用户用宿主打开，agent 只在已有的树上创建任务分支——写死 `mmw worktree add` 会让 Cursor、Codex、Grok 拿到错的指令。其他宿主能力使用按能力判断的自然语言，在所有宿主上保留同一份正文。**没有** `mmw-dispatching-agents` 中转技能。

## 修改规则

- 改技能前读完整 `SKILL.md` 及其链接的 reference。技能写作规范以 `writing-for-agents` 及其链接的 `SKILL-MECHANICS.md` 为准。
- 逐句翻译上游、审查语义漂移、应用有意精简、增加 MMW 接线或升级上游版本时，先完整读取 `upstream-skill-fidelity`。上游的方法要求和 MMW 的工作流要求必须同时成立：上游方法不自动否定 MMW 工作流，当前 MMW 行为也不自动证明方法保真。
- 删技能正文或角色 body 里看起来重复的一段之前，先确定它服务哪条执行面。各宿主的主 agent 与 subagent 拿到的东西不同，某处「重复」可能是某条执行面上的唯一来源。执行面地图在 `mmw/mcp/discipline.py` 的模块文档，引用它，不要另抄一份。
- 只实现请求范围内行为；不用归档残留、兼容目录或静默默认值掩盖错误。
- 脚本异常必须非零退出或留下结构化告警。
- 机械校验只覆盖机器能直接判定的事实：语法与固定结构可解析、路径与文件安全、配置完整性和生成产物一致性。
- 产物质量、方法选择、语义真实性和完成度由技能与主 agent 判断。不用计数、列表形状、固定阈值或豁免清单伪装成机械校验。已有校验越过这条边界时删除该校验，不增加例外分支。

## Git 与安全

- 正式改动在独立 worktree；合回主分支使用 `git merge --no-ff`，禁止 squash。
- 本地提交和合并可自主执行。`git push`、远端合并、部署和正式发布必须得到用户明确授权。
- subagent 交回的报告由主 agent 按结局选路并继续流程。独立审查者仍派。不要求主 agent 打开出处或重跑帮手声称跑过的测试。
- 删除、覆盖、归档或移动现有发布入口前确认用户授权。
- 禁止使用 `--no-verify`。

## 提交检查

改动 `mmw/` 下的 CLI、技能源、出包、图谱或检索之后运行：

```bash
bash mmw/test.sh
```

约两分钟。它在一次性仓库上跑真命令：护栏拒绝了什么、拒绝之后破坏有没有发生、
issue 认领的互斥、图谱在什么情况下判定过期与恢复上一份、出包合同与脚本装配给定输入
返回什么，技能与角色物化成各宿主产物时展开了什么、什么必须当场失败，
以及技能之间的四类引用是否都指得到东西。全部通过时退出码为 0。

其中几份要 `uv`：被测的 Python 是 PEP 723 内联脚本，依赖写在文件头部。没装 uv 时
入口会把没跑的那几份列出来并以非零退出，不静默跳过。

这里不写断言总数。各段自己报数，格式不统一（有的报「过 N，失败 M」，有的报
`N passed`），加起来是多少要当场数：

```bash
bash mmw/test.sh 2>&1 | grep -oE "过 [0-9]+，失败|=== [0-9]+ PASS|^[0-9]+ passed|Ran [0-9]+ tests" \
  | grep -oE "[0-9]+" | paste -sd+ - | bc
```

写死一个数字只会过时——它上一次写的是 860，而那时实际早就不是这个数了。

<!-- MMW-DOMAIN-CONTEXT-START -->
## 领域上下文

开始 research、讨论、设计、写文档、写代码或审查前，先读领域文档。看仓库根有什么，形态就定了：

- 根上有 `CONTEXT-MAP.md`：它是索引。先读它，再读它列出的、本次涉及的全部 leaf（leaf 在 `docs/context/` 下）。
- 根上只有 `CONTEXT.md`：直接读它。
- 两个都没有：直接继续，不报告缺失，也不创建领域文档。

先运行 `mmw artifact index adr` 取得 ADR 索引，再读其中与本次范围相关的那几份。

任何面向用户或写入仓库的内容，都使用 leaf 定义的 canonical term。代码标识符和测试名也适用。不得使用 `_Avoid_` 中列出的说法。

用户说法、leaf、ADR 或代码现状互相冲突时，明确列出冲突，不得自行选择一个覆盖其他内容。

形成长期术语、关系或歧义结论时，使用 `/mmw-domain-modeling` 更新拥有该概念的 leaf。其他 leaf 只保留权威路径引用。

同一 agent 在任务范围不变时只需读取一次。任务进入新的 bounded context 后重新选路并读取。
<!-- MMW-DOMAIN-CONTEXT-END -->
