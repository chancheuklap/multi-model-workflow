# AGENTS.md

## 仓库范围

`mmw/` 是仓库唯一活跃的多模型工作流（Multi-Model Workflow，MMW）。它共享一套产品语义；Codex App、Claude Code 与 Pi 有正式发布入口，Cursor 通过 `mmw agents materialize` 安装原生 subagent。

| 宿主 | 发布入口 | 角色执行后端 |
| --- | --- | --- |
| Codex App | 根 `.agents/plugins/marketplace.json`、`mmw/.codex-plugin/plugin.json`、`mmw/codex/runtime.py` | `worker`、`worker-high-risk`、`prototype-worker` 走 App 后台 Worktree 任务；`planner`、`designer`、`investigator`、`reviewer-gpt` 走原生 subagent；全部使用 Codex 内置 GPT 模型 |
| Claude Code | `mmw/.claude-plugin/plugin.json`、根 `.claude-plugin/marketplace.json` | GPT 走后台 Codex CLI；Claude 走后台 Agent 工具 |
| Pi | `mmw/package.json` | 原生 `subagent` 直调；型号/思考档/async/context/skill 在 `agents-pi` frontmatter；不经 `mmw dispatch` |
| Cursor（安装面） | `mmw agents materialize --host cursor` → `~/.cursor/agents/` | 原生 subagent；frontmatter 由同一套 `agent-src/` 按 profile 生成 |

原生多模型宿主的 agent 文件不要手改 model 行。改 `.mmw.json` 或 `mmw/cli/mmw.default.json` 后执行：

```bash
mmw agents materialize --host pi      # 更新包内 agents-pi/
mmw agents materialize --host cursor  # 安装到 ~/.cursor/agents/
python3 mmw/codex/runtime.py materialize  # 更新 Codex plugin 与四个原生 subagent
```

`archive/` 是冻结归档。归档内容不参与行为判断、构建、测试或发布；没有明确指令时不修改。旧 Claude Code、Factory Droid、Pi 和 Cursor 插件统一归档在 `archive/legacy-host-plugins/`。

`.agents/skills/` 只保存供 Codex 维护本仓库的方法。它不属于 MMW Plugin 发布根，不进入 manifest、README 技能清单、`mmw-skill-map.html` 或宿主物化产物。

`vendor/mattpocock-skills/` 是上游 `mattpocock/skills` 的完整副本，通过 Git subtree squash 更新。不要手改；更新时运行：

```bash
git subtree pull --prefix vendor/mattpocock-skills https://github.com/mattpocock/skills main --squash
```

根文档保留 `README.md`、`AGENTS.md`、`CLAUDE.md`、`TESTING.md`。根 `mmw-skill-map.html` 是当前 MMW 架构的可视化产物，必须保留并随架构变化更新。不要新增其他架构、设计、research、计划或审查类根文档。长期规则写本文件；运行行为写 `mmw/skills/`（源）、物化产物 `mmw/skills-pi/`、`mmw/skills-claude-code/` 与 `mmw/skills-codex/`、`mmw/cli/`。

## 唯一事实来源

同一项行为按以下顺序核对：

1. 对应宿主的 manifest、根 marketplace 或 Pi package；Codex 角色结构只认 `mmw/codex/profiles.json`，模型只认 `mmw/cli/mmw.default.json` 的 `hosts.codex` 覆盖。
2. `mmw/cli/` 的机械动作、宿主 adapter 和 `.mmw.json` 配置合同。
3. `mmw/skills/` 技能源（含 `[[mmw-launch:…]]` 与 `[[mmw-host-action:…]]`）与 `mmw skills materialize` 产物；流程判据以源为准，宿主动作以对应产物为准。

`.mmw.json` 保存目标仓库的模型档、标签、路径和领域文档形态。技能不硬编码这些值；通过 `mmw` 对应子命令读取。

`mmw/.mcp.json` 是检索服务器声明的唯一事实来源。Claude Code、Pi 与 Cursor 的占位符由 `mmw/mcp/resolve.py` 展开。Codex 的直接 server map `mmw/.mcp-codex.json` 由 `mmw/codex/runtime.py materialize` 生成，三台服务器都通过 `mmw mcp serve` 回到同一份定义；该入口保留任务目录，并读取同一份密钥文件。图谱只由 `mmw graph build` 更新；Graphify 和 Serena 的结果都是候选，关键结论必须回当前源码验证。

## 宿主边界

共享角色、技能和流程语义。宿主差异留在 Codex profile、原生 agent frontmatter、`mmw/cli/adapters/`、manifest 与 `.mmw.json` 的 hosts 覆盖：

- Codex App 是 MMW 的主 agent 运行时，不调用外部模型 CLI 或 harness。`worker`、`worker-high-risk` 与 `prototype-worker` 使用独立后台 Worktree 任务。`planner` 在当前任务 worktree 写指定 plan；`designer`、`investigator` 与 `reviewer-gpt` 只交报告。四个原生 subagent 的结构由 `mmw/codex/profiles.json` 物化，模型从 `mmw/cli/mmw.default.json` 解析。
- Codex 主任务的 worktree 由用户创建。App 设置里的 Worktree root 是所有项目共用的 managed worktree 物理存放目录，不是 MMW 源码路径，也不受目标项目 `.mmw.json` 的 `paths.worktrees` 控制。确认任务和父分支后，运行 `mmw task bind codex/<slug> "<用户原话>" --from <父分支或基点 SHA>`。后台结果先用 `mmw result verify` 验证分支、HEAD SHA 与基点，并在命令返回的 worktree 路径验收；验收通过后再用 `mmw result integrate` 合入当前任务分支。
- Codex plugin 以 `mmw/` 为发布根，直接复用 Graph、MCP 与配置源码，并生成 `skills-codex/` 和 `.mcp-codex.json`。`mmw/codex/runtime.py install` 安装四个原生 subagent 和指向已安装 plugin cache 的 `mmw` 命令，并删除旧 Claude Code bridge 在 `~/.codex/skills/` 下的三个 MMW 链接；运行时不得回退 MMW 源码 checkout 或目标项目里的同名目录。安装器不改 `~/.codex/config.toml`，也不直接写 App plugin cache。
- Claude Code 的 GPT 角色通过后台 Bash 执行 Codex CLI；Claude 角色通过后台 Agent 工具执行。这个宿主只接 claude 与 gpt 两个模型族。技能产物在 `mmw/skills-claude-code/`：启动句已物化为 `mmw dispatch`。
- Pi 的全部角色走宿主原生 `subagent`。技能产物在 `mmw/skills-pi/`：启动句已物化为 `subagent({ agent, task, cwd })`。型号等在 agent frontmatter（`mmw agents materialize`）。可写前确认 worktree 干净。
- 模型分配默认各宿主相同。某个宿主接不了基线模型时，在 `.mmw.json` 该角色底下写 `hosts.<宿主>` 覆盖，按字段生效。
- **禁止**在技能源或产物正文里让 agent 按宿主二选一。共享技能用完整自然语言规定流程；宿主差异只写成完整的 `[[mmw-launch:…]]`、`[[mmw-launch-group:…]]` 或 `[[mmw-host-action:…]]` 动作块，再由 `mmw skills materialize` 整块替换。物化器不得按自然语言句子做局部替换；**没有** `mmw-dispatching-agents` 中转技能。
- 运行时不得探测、调用或回退到归档插件。

## 修改规则

- 改技能前读完整 `SKILL.md` 及其链接的 reference。运行提交检查前读根 `TESTING.md`。
- 只实现请求范围内行为；不用归档残留、兼容目录或静默默认值掩盖错误。
- 脚本异常必须非零退出或留下结构化告警。
- 机械校验只覆盖机器能直接判定的事实：语法与固定结构可解析、路径与文件安全、配置完整性和生成产物一致性。
- 产物质量、方法选择、语义真实性和完成度由技能与主 agent 判断。不用计数、列表形状、固定阈值或豁免清单伪装成机械校验。
- 已有校验越过这条边界时删除该校验，不增加例外分支。
- 产品版本同步修改 Codex manifest、Claude Code manifest、根 Claude marketplace 的插件版本与顶层版本，以及 Pi package。
- `mmw/skills/mmw-setup/` 只保存旧背景材料，不是技能。扫描技能正文时必须排除它。
- 每份流程技能以 `## 下一步` 收尾。表格固定为“情况、下一步”两列，动作只用“自己继续”“移交”“停”。只有 agent 无法开启新会话或需要用户决定时才停。
- 审查方法论只在 `/mmw-reviewer`；`/mmw-review` 只管编排。审查者通过安装的技能读取方法论，不把整份方法论粘进提示词。
- 技能引用另一个技能时写 `` `/技能名` ``。同名分支、标签值和文件路径不加斜杠。
- 领域文档位置必须通过 `mmw domain path` 与 `mmw domain dirs` 获取，不写死根 `CONTEXT.md`。
- 派发角色名使用 CLI / `roles.json` 字面串并加反引号（如 `worker`、`planner`），不另起中文名。Claude Code 路径里的 `mmw dispatch` 角色参数同此。
- CLI 不带参数只列命令名；每条命令的参数进入自己的 `usage_*`。认不出参数时只输出该命令的用法。
- Shell 变量后紧跟非 ASCII 字母、数字或下划线时使用 `${var}`，避免非 UTF-8 locale 误解析。
- 技能正文不得使用“同上”“见上”“前面那条”等位置指代。每次写清文件路径、技能名、节名或完整清单。

### Matt 上游技能保真

逐句翻译上游、审查语义漂移、应用有意精简、增加 MMW 接线或升级上游版本时，先完整读取 `.agents/skills/upstream-skill-fidelity/SKILL.md`。这是维护 MMW 仓库的方法，不是 MMW Plugin 的运行技能。

有 Matt Pocock 上游对应项的 MMW 技能同时受两份合同约束：

- **上游方法合同**：`vendor/mattpocock-skills/` 中对应技能及其 reference 规定的方法论、步骤、完成判据和承载理解的解释性文字。
- **MMW 工作流合同**：本仓库规定的 worktree、tracker、报告验证、领域文档、人工审批关卡、prototype 资产、审查、出包和宿主物化流程。

两份合同必须同时成立。上游方法合同不自动否定 MMW 工作流，当前 MMW 行为也不自动证明方法保真。主 agent 按以下顺序判断每一项差异：

1. 找出差异影响的上游方法效果、MMW 上下游接缝和用户可见流程。
2. 查找当前技能源、领域文档、CLI 合同、spec 和 ADR 中的 MMW 证据。Git 历史只用于定位理由，关键断言仍由当前合同和源码支持。
3. MMW 证据能够解释差异，而且差异不改变上游方法效果时，保留 MMW 适配并验证接缝。
4. MMW 证据不能解释差异，或者差异删改了上游方法效果时，恢复上游语义，再做维持 MMW 工作流所需的最小适配。
5. 当前证据仍无法判断，而且选择会改变方法效果、用户流程或长期工作流时，收敛成一个最小问题交给用户决定。技术细节、可逆实现和能由当前证据判断的事项由主 agent 负责。

修改一份有上游对应项的共享技能时，完整读取双方的 `SKILL.md` 和全部相关 reference，再比较方法论、步骤、完成判据和解释性文字。机械 diff 只用于定位，不用于判定保真。删改上游合同内容时，提交说明必须写明对应的 MMW 证据；只有长期工作流理由才写进技能或本文件。

上游技能合集升级时，逐项检查全部 active MMW 技能、全部上游正式技能和本次新增技能。结果至少区分：直接保留、按 MMW 工作流适配、吸收新增技能和不吸收。`/mmw-wayfinder` 等大型路由技能，以及 `/writing-for-agents` 等被其他技能依赖的方法论，必须继续检查每个调用方和完成判据，不能只检查改名文件或入口正文。

prototype 遵守上游的探索方法，也遵守 MMW 的资产合同。Wayfinder map 固定一个 `产物目录`；每张 decision ticket 在该目录下使用自己的 `issue-<编号>` 子目录。持久 prototype 资产保留可运行 prototype、完整界面变体、用户走查结论、选中产物和明确引用的必要证据；过程材料进入 Git 忽略的 scratch。下游先读 prototype 资产索引，再读取精确的选中产物和证据路径。正式实现吸收已经验证的决定和可移植逻辑；prototype 外壳与落选变体继续作为 prototype 资产，不进入生产路由。

每次 `/mmw-research` 完成验证与综合后，先展示结论摘要、拟保存文件和完整路径，再通过人工审批关卡询问用户是否保存。research 路径只通过 `mmw path research` 取得。保存和下游引用独立；下游只读取当前工作点名的 research 索引和精确文件。subagent 原始报告、网页转储、抓取缓存和未采信内容进入 scratch；research 不进入 ADR 目录。

用户已经提供定稿 spec 或 research 报告，并明确要求直接实施时，把任务作为 plugin 维护直接落地。只有仍有一个靠讨论无法决定的设计问题时，才使用 prototype 取得可运行证据。prototype 一旦形成，就按 prototype 资产合同保留，不把它误作待提交的生产实现。

吸收上游新增技能时，先判断它是否服务 MMW 的仓库交付范围。吸收后保留上游 invocation 方式、步骤、完成判据和配套 reference 或模板；只在现有 MMW 路由确实需要它时才接入主流程。辅助技能保持辅助技能身份。

一次上游升级完成时，以下条件必须全部成立：术语与概念统一；上游方法合同没有遗漏；MMW 工作流没有断点；共享技能源已经物化到全部正式宿主；manifest、版本、README 和 `mmw-skill-map.html` 已按实际变化同步；根 `TESTING.md` 规定的检查已经通过。与本次升级无关的历史漂移单独记录，不混入当前改动。

## 术语

| 概念 | 使用 | 不使用 |
| --- | --- | --- |
| 发起并协调其他 agent | 主 agent | 主线程 |
| 被派出的执行者 | subagent | 子代理、sub-agent |
| 写代码角色 | `worker` | 工人、写码工人 |
| 写计划角色 | `planner` | 计划工人 |
| 审查角色 | 审查者；Codex 写 `reviewer-gpt`，Claude Code/Pi 写 `reviewer-gpt`、`reviewer-claude` | 审者 |
| 非交互式 Codex | headless | 无头 |
| 派发任务说明 | task（四栏表） | brief、简报 |
| issue 分诊合同 | agent brief | 不是 host 工具参数；经 task「读」栏引用 |
| subagent 交回内容 | 报告 | 回执、笔记 |
| 主 agent 检查事实 | 验证 | 复核、核验、亲验 |
| 可点击的位置 | 出处 | 锚 |
| 唯一权威内容 | 唯一事实来源 | 真相源、事实源 |
| 必须用户确认的关卡 | 人工审批关卡 | 人闸 |
| 建隔离目录 | 建 worktree | 建树、进树 |
| 发送到外部系统 | 对外发布 | 出站动作 |
| sandbox 与工具白名单 | 护栏（guardrails） | 围栏 |

人工审批关卡始终表示用户必须明确确认，主 agent 才能继续。各技能只规定本关卡要确认的产物或动作，不改变“人工审批关卡”的含义。

有行业标准中文译名时使用标准中文；没有时使用英文原词。不要自造术语、缩写或比喻性动词。

## Git 与安全

- 正式改动在独立 worktree；合回主分支使用 `git merge --no-ff`，禁止 squash。
- 本地提交和合并可自主执行。`git push`、远端合并、部署和正式发布必须得到用户明确授权。
- subagent 报告不是唯一事实来源。关键定位、测试结果和发布结论由主 agent 用当前源码或运行结果验证。
- 删除、覆盖、归档或移动现有发布入口前确认用户授权。
- 禁止使用 `--no-verify`。

## 提交检查

本仓库不保留自动化测试、测试夹具或测试套件。提交前检查以根 `TESTING.md` 为准。

提交前运行 `git diff --check`。本次改动的 JSON 使用 `python3 -m json.tool` 校验；本次改动的 Shell 使用 ShellCheck 校验；改动 Codex 物化输入时运行 `python3 mmw/codex/runtime.py materialize --check`。

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
