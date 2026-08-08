# Multi-Model Workflow

多模型工作流（Multi-Model Workflow，MMW）是一套面向软件开发 agent 团队的交付工作流。它把需求讨论、research、设计、计划、实现、审查、集成和发布连接起来，让一项工作可以跨 agent、跨会话、跨 worktree 持续推进。

MMW 的用户界面是技能。日常工作的统一入口是 `$mmw:mmw-start`。用户把目标、issue、PR、map 或当前任务交给它，它负责判断路线、建立或绑定任务 worktree，再移交给对应技能。

`mmw` 命令行界面（Command-Line Interface，CLI）是技能使用的机械层。它负责 Git、worktree、issue tracker、领域文档、Wiki 和 release 等确定性动作。用户不需要手动运行这些命令。

| 项目 | 数量 | 结论 |
| --- | --- | --- |
| 当前版本 | 0.11.0 | 对齐 Matt Pocock Skills 1.2.3，并发布重建后的技能、安装和仓库初始化合同 |
| 日常工作流入口 | 1 个 | `$mmw:mmw-start` |
| `mmw-start` 调用方式 | 1 种 | 只允许用户显式调用 |
| `mmw-start` 识别的输入 | 路由表加兜底 | 恢复当前任务、直接查询，或者移交下游技能 |
| MMW 工作流技能 | 23 个 | 21 个可触发技能，2 个角色方法论技能 |
| 辅助技能 | 5 个 | 支持交接、agent 文档、人工向导、问卷和用户说明 |

## MMW 怎样管理上下文

上下文（context）指 agent 当前能看到并据此判断的信息。MMW 不依赖一段不断增长的聊天记录。它把项目事实留在可重新读取的位置，再为每个 agent 选择完成当前任务所需的材料。

| 材料 | 保存什么 | 谁使用 |
| --- | --- | --- |
| 领域文档 | 项目特有的术语、需要避开的说法、职责归属和跨 bounded context 关系 | 主 agent 与本次任务涉及的 subagent |
| issue、spec、plan、ADR、GitHub Wiki | 用户目标、已经确认的决定、ticket、实施步骤和已经交付的设计 | 当前阶段的技能和角色 |
| task（四栏表） | 本次派发的目标、必须读取的位置、行为约束和验收标准 | 一个指定的 subagent |
| 报告与验证证据 | 源码出处、命令输出、测试结果、结果分支、HEAD 和基点 | 主 agent |

### 领域上下文

小型仓库可以使用一份 `CONTEXT.md`。包含多个 bounded context 的仓库使用 `CONTEXT-MAP.md` 作为索引，再为每个 bounded context 建立一份 leaf。这里的 bounded context 指一套业务术语和职责保持一致的范围。Map 记录每个范围拥有的概念、职责和相互关系。

MMW 会在每个 agent 开工前选择本次涉及的领域文档。任务进入另一个 bounded context 时，agent 会重新选择相应 leaf。长期形成的新术语和关系由 `mmw-domain-modeling` 写回拥有它们的 leaf。难以回退的决定进入 ADR。

用户需要把当前会话交给另一个 agent 时，可以显式调用 `handoff`。普通技能按照自己的下一步直接移交，不经过额外的阶段边界层。

### task（四栏表）

主 agent 派发 subagent 时，会写一份四栏 task。task 是一次派发的完整合同。

| 栏 | 内容 |
| --- | --- |
| 目标 | 这一次只需要回答或完成什么 |
| 读 | 必须打开的源码、领域文档、issue、spec、plan 或方法论路径 |
| 约束 | 只读还是可写，可以改哪些文件，哪些决定已经确认 |
| 验收 | 必须交回什么，以及完成需要哪些证据 |

task 的“读”栏保存路径和 issue 编号。唯一事实来源留在原处，subagent 每次读取当前版本。返工使用新的 subagent，不继承上一轮上下文。审查只运行一轮；采信项由主 agent 验证修复，不再派审查者。材料不足时，subagent 必须报告 `needs-context`，不能自行猜测。

### 报告、验证与独立上下文

subagent 交回的是报告。报告中的断言只有经过主 agent 验证才能进入项目结论。

`investigator` 只回答一个可验证的 research 问题。`worker` 只实现一张 ticket。审查者只检查一个视角。审查者使用独立上下文，产物作者不审查自己的结果。

可写任务使用独立结果分支。主 agent 验证结果分支、HEAD 和基点，并在结果 worktree 验收实际差异。验收通过后才能集成到当前任务分支。

## 技能系统

当前 MMW 有 23 个 `mmw-*` 工作流技能。`mmw-start` 是统一入口。`mmw-planner` 和 `mmw-reviewer` 只供对应角色读取。其余 20 个技能可以由 `mmw-start` 移交，也可以在用户明确知道所需阶段时直接触发。

| 分组 | 技能 | 职责 |
| --- | --- | --- |
| 入口与分诊 | `mmw-start`、`mmw-triage`、`mmw-wayfinder` | 路由新工作；分诊 issue 和 PR；规划超过一个 agent 会话且路线尚不清楚的 effort |
| research 与收敛 | `mmw-grilling`、`mmw-prototype`、`mmw-research`、`mmw-retrieval`、`mmw-diagnosing-bugs`、`mmw-improve-codebase-architecture` | 谈清需求；用 prototype 回答设计问题；执行重型多角度 research；恢复检索能力；诊断 bug；寻找架构改进候选 |
| 领域与设计 | `mmw-domain-modeling`、`mmw-codebase-design` | 维护领域语言和 ADR；定义 module、interface、seam、adapter 与 depth |
| 交付 | `mmw-to-spec`、`mmw-to-tickets`、`mmw-to-plan`、`mmw-implement`、`mmw-tdd` | 发布 spec；拆 tracer bullet ticket；写 plan；派 `worker` 实现；执行 red 到 green 的测试循环 |
| 验证与交付完成 | `mmw-verifying-agent-output`、`mmw-review`、`mmw-integrate`、`mmw-release`、`mmw-closing` | 验证报告；编排审查；集成分支；出正式安装包；归档 spec 和 plan |
| 角色方法论 | `mmw-planner`、`mmw-reviewer` | 分别供 `planner` 和审查者读取；主 agent 与用户不直接使用 |

直接触发专业技能时使用 `$mmw:<技能名>`。例如，审查一条已有分支可以显式调用 `$mmw:mmw-review`。日常使用仍以 `$mmw:mmw-start` 为主。

MMW 插件（plugin）还包含五个辅助技能。它们不属于上述 23 个 MMW 工作流技能，也不参与 `mmw-start` 的日常路线。

| 辅助技能 | 用途 |
| --- | --- |
| `handoff` | 把当前会话压缩成可由另一个 agent 继续的交接文档 |
| `writing-for-agents` | 约束技能、agent 指令和其他供 agent 读取的文本 |
| `wizard` | 为复杂的人工操作生成可审查、可逐步执行的向导脚本 |
| `to-questionnaire` | 把缺失信息整理成可转交给另一位知识持有者的问题清单 |
| `wait-what` | 重新说明上一条消息，或者生成普通 HTML 可视化解释；需要按钮驱动状态模型时移交 `mmw-prototype` |

## MMW 与 Matt Pocock Skills 的关系

MMW 基于 Matt Pocock Skills 的工程方法构建。对于有上游对应项的技能，Matt Pocock Skills 提供方法、步骤、解释和完成判据。MMW 提供 worktree、tracker、报告验证、领域文档、人工审批关卡和多宿主物化等正式工作流承载。

两套合同必须同时成立。MMW 不会因为上游更新而删除自己的工作流，也不会用工作流适配改写上游方法的执行效果。

| 出现差异时 | 处理方式 |
| --- | --- |
| MMW 的差异有当前工作流合同支持，而且不改变方法效果 | 保留差异，并验证上下游接缝 |
| MMW 的差异缺少仓库证据，而且删改了方法步骤、解释或完成判据 | 恢复上游合同，再接回 MMW 工作流 |
| 当前证据无法判断，而且选择会改变方法效果或用户流程 | 收敛成一个必要决定，再请用户确认 |

prototype 同时体现这两层合同。后端脚本、Logic HTML 和 UI/UX 是同一份 prototype 的不同工作面。它们在原位置持续迭代，由用户逐轮走查。Wayfinder map 在正文固定一个 `产物目录`。Wayfinder decision ticket 使用 `docs/prototypes/<产物目录>/issue-<编号>/`，普通任务使用 `docs/prototypes/<任务 slug>/`。prototype 索引向下游传递用户走查结论、选中产物、否定约束和可复用的想法。过程截图、DOM、console、录屏和生成中间物进入 Git 忽略的 scratch。prototype 外壳不直接进入正式产品。

`mmw-research` 由主 agent 和 `investigator` 共用入口。主 agent 只读取编排流程；`investigator` 根据 task 读取内部或外部取证方法。普通 research 完成验证与综合后，MMW 展示结论摘要、拟保存文件和完整路径，并询问用户是否保存。Wayfinder research ticket 和外部系统实测直接保存。普通任务使用 `docs/research/<产物目录>/<research 主题>/`；Wayfinder decision ticket 使用 `docs/research/<产物目录>/issue-<编号>/<research 主题>/`。下游只读取当前工作点名的 `README.md` 和精确文件。

0.10.0 还恢复了一次会话只解决一张 Wayfinder decision ticket、ticket 发布前人工审批关卡、阶段边界决策树、实现阶段测试频率和出包后重新终审等合同。它新增 `writing-for-agents`、`wizard`、`to-questionnaire` 和 `wait-what`，但没有把这些辅助技能加入日常主路由。

0.10.1 补齐了 prototype 资产在 `planner` 与 `reviewer-gpt` 中的读取接缝。当前合同进一步把读取范围收紧到 prototype 资产索引、用户选中的产物和明确相关的走查证据，避免把无关过程材料传给下游。

0.10.2 扩展 `wait-what`：默认生成与要解释的内容放在一起的完整 HTML，并由 Codex Sites 保存版本。

0.10.3 统一 active skill 的触发描述和文档结构，明确 prototype、research、evidence、scratch 与 review 的资产合同，并校正 Research、plan、审查和 tracer bullet ticket 的职责边界。⑤ final 终审与 ⑥ 合并集成审是互斥终审；多分支集成通过 ⑥ 后不再发起 ⑤。

0.11.0 发布技能 rebuild。`mmw-start` 改为用户专用入口；下游缺少任务上下文时停止并说明，不再回跳。Prototype 改为持续迭代的持久资产。Research 按主 agent 与 `investigator` 身份渐进加载。审查收敛为五道，多分支集成结果进入同一道 ⑤ final 终审。模型档归已安装 runtime；`mmw/install.sh` 负责本机安装，`mmw init` 只配置目标仓库。

## 用户使用的三个阶段

用户会接触安装、仓库初始化和日常工作三个阶段。安装和初始化是准备工作。MMW 日常工作流只有一个入口。

| 使用时机 | 用户做什么 | Codex 做什么 |
| --- | --- | --- |
| 首次安装 | 授权 Codex 安装 MMW | 安装 plugin、原生 subagent、`mmw` 命令和检索依赖 |
| 每个仓库首次接入 | 要求 Codex 初始化当前仓库 | 运行 `mmw init` 配置仓库，再运行 `mmw doctor` 只读检查本机运行时 |
| 开始或继续工作 | 显式调用 `$mmw:mmw-start` | 判断路线、处理任务 worktree，并移交对应技能 |

日常开发只有一个统一入口：`$mmw:mmw-start`。用户不需要自己选择 `mmw-grilling`、`mmw-to-spec`、`mmw-implement` 或 `mmw-review`。

## Codex 中怎样调用入口

`mmw-start` 是用户专用技能。具体语法见 [Codex Skills 文档](https://learn.chatgpt.com/docs/build-skills)。

| 方式 | 写法 | 结果 |
| --- | --- | --- |
| 显式调用 | 在提示词中使用 `$mmw:mmw-start` | 进入 MMW 统一路由 |
| 只描述任务 | 不调用 `mmw-start` | Agent 按普通技能发现机制处理，不会自动进入统一入口 |

开始 MMW 工作时应使用显式调用。不要只写“使用 MMW”。

## 从源码仓库安装到本机宿主

安装只做一次。用户在任意 Codex 本地任务中发送下面的请求，并把 `<本机目录>` 换成希望保存源码的位置。

```text
请把 MMW 安装到这台电脑已有的 agent harness。

源码仓库：https://github.com/chancheuklap/multi-model-workflow.git
源码位置：<本机目录>

请运行源码仓库里的 mmw/install.sh。
让它安装 Codex、Claude Code、Pi、原生 subagent、mmw 命令和 MCP 中当前可用的部分。
安装后按仓库规则完成运行时和依赖检查。
需要我登录 GitHub、确认权限或提供 Context7 密钥时再停下来问我。
最后说明安装了什么、检查是否通过、哪些能力仍不可用。
```

安装会构建本机稳定 runtime，并修改已经安装的宿主配置、原生 subagent、MCP 配置和 `~/.local/bin/`。安装完成后，重启宿主或开始一个新会话。

### 从已有版本升级

升级从 MMW 源码仓库统一运行 `mmw/install.sh`。安装器构建稳定 runtime，再更新本机已有的 Codex、Claude Code、Pi、原生 subagent、`mmw` 命令和 Pi/Cursor MCP。

用户可以在 MMW 源码仓库的 Codex 任务中发送：

```text
请把当前 MMW 升级安装到 Codex。

先确认源码版本和工作区状态，再运行 mmw/install.sh。
随后运行 mmw doctor，按它报告的缺项处理。
最后确认各宿主、稳定 runtime 和源码使用同一版本。
不要推送或正式发布。
```

升级完成需要同时满足以下条件：

1. `codex plugin list` 显示 MMW 已安装、已启用，并使用当前版本。
2. 四个原生 subagent 已更新。
3. `mmw` 命令指向当前版本的稳定 runtime。
4. Codex runtime 检查和物化检查通过。
5. 用户新建 Codex 任务，或者重启 Codex。已经打开的任务不会热加载新技能。

## 初始化目标仓库

在 Codex App 中打开目标仓库，然后发送：

```text
请为当前仓库初始化 MMW。

开始前检查初始化涉及的文件是否有未提交改动。
运行 `mmw init`，完成项目配置、领域上下文读取规则、测试说明骨架和 GitHub 标签初始化。
再运行 `mmw doctor`，只读检查本机运行时，并说明哪些检查没有通过。
这一步不要替项目创建领域模型。
```

Codex 会完成初始化和检查。用户不需要打开终端，也不需要手动执行 MMW 命令。

初始化可能生成或修改以下内容：

| 位置 | 作用 |
| --- | --- |
| `.mmw.json` | 保存 tracker 标签、CLI 路径和领域文档形态；不保存模型档 |
| `AGENTS.md` | 保存“开工前怎样选择领域上下文”的受管规则块 |
| `TESTING.md` | 保存目标仓库自己的测试层次、seam 和运行方法 |
| `.gitignore` | 忽略审查记录、release 过程材料和结构图谱派生物 |
| issue tracker | 创建缺失的工作流标签 |

初始化是幂等操作。初始化器不会覆盖已有的 `.mmw.json` 和 `TESTING.md`。如果本轮修改了仓库配置，它会创建一个 `chore(mmw): 配置多模型工作流` 提交。

需要建立领域文档时，显式调用对应技能：

```text
$mmw:mmw-domain-modeling 为这个仓库建立领域模型。先和我确认 bounded context 的数量和边界。
```

单一 bounded context 默认使用 `CONTEXT.md`。多个 bounded context 默认使用 `CONTEXT-MAP.md` 和 `docs/context/`。ADR 默认放入 `docs/adr/`。

## 使用 `$mmw:mmw-start`

### 新工作

需要创建任务 worktree 的新工作按以下方式开始：

1. 在 Codex App 中打开已经初始化的目标仓库。
2. 从正确的父分支创建 Worktree 任务。
3. 在新任务中显式调用 `$mmw:mmw-start`，并写明目标。

```text
$mmw:mmw-start 为订单导出增加按日期筛选，并补齐测试和文档。
```

Codex App 先提供 detached worktree。`mmw-start` 判断路线和 slug，再把当前 worktree 绑定到 `codex/<slug>` 任务分支。无需任务 worktree 的路线会跳过绑定。

### 继续当前任务

在已经绑定的 Codex 任务中，不带参数调用入口：

```text
$mmw:mmw-start
```

`mmw-start` 会根据 Git、issue tracker、spec、plan、审查记录和 Wiki 判断当前进度，再移交下一步技能。用户不需要保存另一份状态文件。

### 常用输入

```text
$mmw:mmw-start bug 支付成功后订单仍显示待支付。
```

```text
$mmw:mmw-start wayfinder 重新设计整套商家结算系统。
```

```text
$mmw:mmw-start issue #123
```

```text
$mmw:mmw-start <map 编号或链接>
```

`bug` 和 `wayfinder` 是显式路线标签。没有标签时，`mmw-start` 根据用户内容和 issue tracker 状态判断路线。

## `mmw-start` 的完整路由

`mmw-start` 识别 18 种输入情况。这些情况收敛为恢复、直接查询或 11 个下游技能。

| # | 用户输入或 tracker 状态 | 下一步技能 |
| --- | --- | --- |
| 1 | 没有输入，或者当前 checkout 已绑定任务分支 | 检查当前进度，再移交实际下一步技能 |
| 2 | 一张 map 的编号、链接，或者要求继续某张 map | `mmw-wayfinder` |
| 3 | 带 `wayfinder:` 标签的 decision ticket | `mmw-wayfinder` |
| 4 | 挂在 `wayfinder:map` 下、不带 `wayfinder:` 标签的 spec issue | `mmw-to-spec` |
| 5 | spec issue 下的 tracer bullet ticket 已有 plan，并带 `ready-for-agent` | `mmw-implement` |
| 6 | spec issue 下的 tracer bullet ticket 缺少 plan 或 `ready-for-agent` | `mmw-to-plan` |
| 7 | 尚未分诊的 issue 或 PR | `mmw-triage` |
| 8 | 已是 `ready-for-agent`，但 agent brief 不完整 | `mmw-triage` |
| 9 | 已是 `ready-for-agent`，可以作为一张 ticket 独立验收，只有一个 Test seam，没有未决设计取舍 | `mmw-implement` |
| 10 | 已是 `ready-for-agent`，但需要多张 ticket、多个 Test seam 或仍有设计取舍 | `mmw-to-spec` |
| 11 | 有东西坏了、报错、跑不通、变慢，或者显式使用 `bug` | `mmw-diagnosing-bugs` |
| 12 | 一项超过一个 agent 会话且路线尚不清楚的 effort，或者显式使用 `wayfinder` | `mmw-wayfinder` |
| 13 | 想先看界面 prototype，或者要验证一套状态模型 | `mmw-prototype` |
| 14 | 单个文件、符号、事实或一条命令能答完 | 主 agent 直接查询并回答 |
| 15 | 需要多个独立角度或多份一手资料的重型调查 | `mmw-research` |
| 16 | 新需求，或者对已有需求的改进 | `mmw-grilling` |
| 17 | 没有具体需求，只想找代码库的可维护性问题 | `mmw-improve-codebase-architecture` |
| 18 | 集成并行分支、让结果分支跟上目标分支，或者处理冲突 | `mmw-integrate` |

issue 或 PR 的标签和 agent brief 会影响路由。用户只需提供编号或链接，`mmw-start` 负责读取完整内容和状态。

`mmw-prototype` 产生 prototype 资产。逻辑 prototype 使用可直接双击打开的单文件 HTML，并同时提供自由操作和引导式走查。同一 Wayfinder effort 共用 map 的 `产物目录`，每张 decision ticket 使用自己的 `issue-<编号>` 子目录。下游先读该子目录的 `README.md`，再读取用户选中的产物和明确引用的长期证据。临时运行材料进入 Git 忽略的 scratch。

普通 `mmw-research` 完成后询问用户是否保存。Wayfinder research ticket 和外部系统实测直接保存。`README.md` 是 research 索引。下游只读取当前工作点名的 research 索引和精确文件。research 不进入 ADR 目录；只有满足 ADR 判据的决定才进入 ADR。

`mmw-to-tickets` 会先展示 tracer bullet 切分、阻塞关系，以及 prototype 与 research 引用。用户通过 ticket 切分的人工审批关卡后，MMW 才把 ticket 发布到 tracker。

## 用户与主 agent 的责任

用户负责产品方向、真实使用感受、难以回退的架构决定和对外发布。

主 agent 负责读取领域上下文、选择技能、编写 task、派发 subagent、验证报告、验收结果分支并推进工作流。用户不需要手动选择 `worker`、`planner` 或审查者，也不需要运行 `mmw` 命令。

## 查看完整工作流

[`mmw-skill-map.html`](mmw-skill-map.html) 是当前架构的交互式地图。它展示技能、产物、移交关系、人工审批关卡、宿主发布面和 `mmw-wayfinder` 内部流程。
