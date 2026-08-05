# 领域上下文消费合同 spec

> 本 spec 来自用户已批准的领域上下文规则方案。当前仓库运行 `mmw domain path` 返回 `none`，因此本次没有可引用的领域 leaf。

## Problem Statement

MMW 能定位领域文档，却没有把“所有 agent 在沟通和产出前必须读取并使用领域定义”安装成每个目标仓库的稳定规则。已有 Map 也没有统一的消费合同和可检查格式。结果是主 agent 或 subagent 可能跳过 leaf，使用非 canonical 术语，或者静默处理用户说法、leaf、ADR 与代码现状之间的冲突。

AgentFlow 已有 `CONTEXT-MAP.md` 和七份 leaf，但 Map 混有通用规则、项目路由和宿主实现细节。MMW 当前还假定多上下文 leaf 名为 `CONTEXT.md`，不能准确描述 AgentFlow 已在使用的命名文件。

## Solution

`mmw init` 把一段固定、高密度的领域上下文消费规则同步到目标仓库的 `AGENTS.md`。主 agent 与 subagent 读取同一份仓库规则，不额外在派发 task 中注入 leaf 路径。Claude Code 目标仓库同时获得指向 `AGENTS.md` 的根 `CLAUDE.md` 桥接。

多上下文仓库的 `CONTEXT-MAP.md` 包含固定的 `使用规则` 受管区块，以及项目自行维护的 `Contexts` 和 `Relationships`。同步只更新受管区块，不改写上下文清单、关系或 leaf 内容。

MMW 接受 `context` 目录下的命名 Markdown leaf。AgentFlow 保留现有七份 leaf 路径，并把根 Map 重构为标准结构。

## Current State

- `.mmw.json` 已用 `domain.map`、`domain.fallback`、`domain.context_dir` 和 `domain.adr_dir` 保存目标仓库的领域文档形态（`.mmw.json:119`）。
- `mmw domain path` 只区分 `map`、`single`、`none`。`map` 的提示假定每个上下文都使用 `CONTEXT.md`（`mmw/cli/lib/domain.sh:16`）。
- `mmw domain dirs` 已能返回 `context` 与 `adr` 的绝对目录（`mmw/cli/lib/domain.sh:34`）。
- `mmw init` 当前只初始化配置、宿主运行面、测试骨架、标签、忽略项、技能和 MCP，没有同步 `AGENTS.md` 或 `CONTEXT-MAP.md`（`mmw/cli/lib/init.sh:233`）。
- `mmw init` 已有“只提交本轮登记路径”的机制，但它会暂存目标文件的全部变化。领域规则同步必须先确认既有目标文件干净，才能复用该提交机制（`mmw/cli/lib/init.sh:186`）。
- `mmw doctor` 当前不检查领域规则、Map 结构或 leaf 链接（`mmw/cli/mmw:571`）。
- 领域格式只展示 `Contexts`、`Relationships` 和 `.../CONTEXT.md` leaf，没有规定受管规则区块或表格列（`mmw/skills/mmw-domain-modeling/CONTEXT-FORMAT.md:32`）。
- 部分直接产生文档、ticket、plan 或 Wiki 的技能没有显式要求先消费领域文档。目标仓库 `AGENTS.md` 将成为这些路径的共同规则入口（`mmw/skills/mmw-to-tickets/SKILL.md:20`、`mmw/skills/mmw-to-plan/SKILL.md:10`、`mmw/skills/mmw-closing/SKILL.md:12`）。
- 技能源会物化到 Pi、Claude Code 和 Codex 三套发布目录，Codex 运行时检查也消费同一物化结果（`mmw/cli/lib/materialize_skills.py:333`、`mmw/codex/runtime.py:139`）。

复用现有 `.mmw.json` 路径合同、初始化修改登记、技能物化和 Codex 原子写入模式。新增领域规则同步器，因为当前 CLI 没有可复用的 Markdown 受管区块更新实现。

## User Stories

1. 作为使用 MMW 的 agent，我要从仓库 `AGENTS.md` 得知何时读取 Map、leaf 和 ADR，以便在沟通和产出中使用项目定义。
2. 作为使用多上下文仓库的 agent，我要从标准 Map 选择全部相关 leaf，以便跨 bounded context 的任务不会漏读定义。
3. 作为仓库维护者，我要让 `mmw init` 幂等安装和升级通用规则，同时保留项目路由与关系。
4. 作为仓库维护者，我要让 `mmw doctor` 报告缺失、漂移、格式错误和失效链接，以便在 agent 开工前发现合同失效。
5. 作为 AgentFlow 维护者，我要保留现有七份 leaf 路径，只重构根 Map 和仓库规则，以免制造无价值的路径迁移。

## Implementation Decisions

1. `AGENTS.md` 使用 `MMW-DOMAIN-CONTEXT-START` 与 `MMW-DOMAIN-CONTEXT-END` 标记一段 MMW 受管区块。内容只写 agent 要执行的动作、术语约束、冲突处理和更新边界。该规则覆盖主 agent 与 subagent。无需原型，因为这是仓库行为合同，没有可视界面。
2. `CONTEXT-MAP.md` 使用 `MMW-CONTEXT-MAP-RULES-START` 与 `MMW-CONTEXT-MAP-RULES-END` 标记 `使用规则`。MMW 只管理这一区块。`Contexts` 和 `Relationships` 由项目持有。无需原型，因为输出格式已经由用户逐字批准。
3. 同步器以种子文件为唯一事实来源。缺少 `AGENTS.md` 时创建；存在完整标记时替换区块；没有标记时插入区块；标记缺失、重复或次序错误时非零退出且不改原文件。同步器不创建 Map；Map 由领域建模流程按需创建。AGENTS、Map 与 CLAUDE 目标必须是普通文件，不能是符号链接；三个目标解析后不得重合。已有 Map 使用同步后的候选正文完成表格、Relationships、leaf 与 authoritative 检查后才允许整轮写入。
4. 同步器先读取原文件内容，再生成同目录临时文件并原子替换，避免留下半写文件。相同输入不产生文件变化。同步前的 Git 干净检查保护已有用户改动；初始化期间不支持并发编辑同一目标文件，也不承诺合并并发修改。正向替换失败时恢复已替换目标；任一恢复失败都在 `io-error` 中点名未恢复目标，并清理回滚临时文件。
5. `mmw init` 修改既有 `AGENTS.md`、`CLAUDE.md` 或 Map 前，要求该文件已被 Git 跟踪且暂存区和工作区都干净。文件不存在时可以创建。文件未跟踪或已有修改时，初始化报告目标并停止同步，避免把用户改动带入 MMW 配置提交。只有实际变化且满足上述条件的路径进入本轮提交。初始化使用 Bash 数组逐项暂存和提交路径，保留路径中的空格。
6. `none` 和 `single` 只同步 `AGENTS.md`。`map` 同步 `AGENTS.md` 和已经存在的 Map。`none` 不创建领域文档。doctor 在 `none` 只检查 AGENTS 规则；在 `single` 另检查 fallback 是可读的普通 UTF-8 Markdown 文件；在 `map` 才检查 Map 规则、结构和 leaf。fallback 已存在但不合格时必须失败，不得降级为 `none`。三种形态都是合法成功状态。
7. Claude Code 宿主确保根 `CLAUDE.md` 导入 `AGENTS.md`。缺少文件时创建单行 `@AGENTS.md`；已有干净文件缺少该导入时追加；已有导入时不改。Pi 与 Codex 继续使用各自原生的 AGENTS 加载行为。
8. 多上下文 leaf 可以是 `context` 目录或其子目录中的 Markdown 文件。Map 的 `Contexts` 使用 GitHub 风格 Markdown 表格，列名和顺序固定为 `Context`、`Leaf`、`Owns`。表格解析遵守 GitHub 风格 Markdown，转义竖线和行内代码中的竖线不分列。`Context` 是非空且唯一的上下文名。`Leaf` 是且仅是一个 Markdown 链接；链接目标相对 Map 文件解析，解析后必须位于 `mmw domain dirs` 返回的 `context` 目录内，并以 `.md` 结尾。`Owns` 是非空的自然语言所有权说明，doctor 不解析其内部语义。
9. `Relationships` 是非空的 Markdown 列表，由 agent 读取，不建立新的机器语法。doctor 只检查该节存在且含有列表项，不猜关系端点或所有权。
10. leaf 的权威引用格式固定为 `(authoritative: [显示文本](相对路径))`。路径相对当前 leaf 解析，目标必须位于 `context` 目录内，并且必须等于 `Contexts` 已登记的某个 leaf。
11. `mmw doctor` 检查对应领域形态的受管区块、Map 固定节、三列表格、leaf 范围和文件类型，以及 `authoritative` 引用。发现错误时返回非零。
12. `mmw domain path` 的 `map` 提示改为“读取 Map 列出的相关 leaf”，移除 `CONTEXT.md` 文件名假设。map、fallback、context 与 ADR 四个配置字段必须是仓库内的非空相对路径，并且不能包含 TAB 或换行。`mmw domain dirs` 按 `single`、`map`、`context`、`adr` 的固定顺序输出四个已验证绝对路径，使 `none` 形态的领域建模流程也能取得首份领域文档落点。领域格式和领域建模技能同步采用命名 leaf 合同。
13. 直接产生原型、ticket、plan、Wiki 或集成取舍记录的关键技能增加一句短提醒：遵守目标仓库 `AGENTS.md` 的领域上下文规则。完整消费逻辑不复制到技能中，subagent task 也不注入 leaf 路径。
14. 发现冲突后，主 agent 停止依赖该语义的工作并交给用户决定；subagent 把冲突报告给主 agent。未受冲突影响的只读调查可以继续。
15. AgentFlow 的根 Map 使用用户批准的标准结构。通用规则来自 MMW 受管区块；七个项目路由和五条关系留在项目区块。宿主加载细节不进入 Map。
16. 新同步器、doctor 检查和技能消费入口写入根 `mmw-skill-map.html`，保持架构可视化与发布行为一致。

### 受管 `AGENTS.md` 区块

```markdown
<!-- MMW-DOMAIN-CONTEXT-START -->
## 领域上下文

开始调查、讨论、设计、写文档、写代码或审查前，运行 `mmw domain path`：

- 返回 `map`：先读 Map，再读本次涉及的全部 leaf。
- 返回 `single`：读命令返回的领域文档。
- 返回 `none`：直接继续，不报告缺失，也不创建领域文档。

运行 `mmw domain dirs`，读取 `adr` 路径下与本次范围相关的 ADR。

任何面向用户或写入仓库的内容，都使用 leaf 定义的 canonical 术语。代码标识符和测试名也适用。不得使用 `_Avoid_` 中列出的说法。

用户说法、leaf、ADR 或代码现状互相冲突时，明确列出冲突，不得自行选择一个覆盖其他内容。

形成长期术语、关系或歧义结论时，使用 `/mmw-domain-modeling` 更新拥有该概念的 leaf。其他 leaf 只保留权威路径引用。

同一 agent 在任务范围不变时只需读取一次。任务进入新的 bounded context 后重新选路并读取。
<!-- MMW-DOMAIN-CONTEXT-END -->
```

### 受管 `CONTEXT-MAP.md` 区块

```markdown
<!-- MMW-CONTEXT-MAP-RULES-START -->
## 使用规则

1. 根据 `Contexts` 和 `Relationships` 选择本次涉及的全部 leaf。答复用户或写入文件前读完这些 leaf。
2. 术语归属不明确时，运行 `mmw domain dirs` 取得 `context` 路径并搜索该术语。仍无法判断时询问用户。
3. 使用 leaf 定义的 canonical 术语，避开 `_Avoid_`。共享术语以标有 `authoritative` 路径的主 leaf 为准。
4. 读取 `mmw domain dirs` 返回的 `adr` 路径下与本次范围相关的 ADR。
5. 用户说法、多个 leaf、ADR 或代码现状互相冲突时，明确列出冲突，不得静默覆盖。
6. 长期术语、关系和歧义只写入拥有它们的 leaf。只有上下文集合、所有权或跨上下文关系改变时才修改本 Map。
7. 操作步骤、实施计划、发布状态和一次性调查不进入领域文档。
<!-- MMW-CONTEXT-MAP-RULES-END -->
```

## Failure Paths

| 失败 | 什么触发 | 谁捕获 | 用户看到什么 | 系统做什么 | 对应哪条验收 |
| --- | --- | --- | --- | --- | --- |
| 受管标记损坏 | 标记缺失一端、重复或次序错误 | 领域规则同步器 | 点名文件和标记错误 | 非零退出，不改原文件 | 同步失败保持原文件字节不变 |
| 目标文件已有用户改动 | 既有目标未跟踪、已暂存或有工作区修改 | `mmw init` | 点名目标文件并要求先处理现有改动 | 不同步该文件，不提交 | 用户改动不进入初始化提交 |
| 受管目标不安全 | AGENTS、Map 或 CLAUDE 是符号链接，或多个目标解析到同一路径 | 领域规则同步器、`mmw doctor` | 点名目标或冲突配置 | 返回 `unsafe-target` 或 `conflicting-targets`，整轮不写 | 受管目标不跟随链接且不互相覆盖 |
| Map 结构不合格 | 缺少固定节或表格列 | `mmw doctor` | 点名缺少的节或列 | 返回非零 | doctor 能定位结构错误 |
| Map 候选不合格 | 已有 Map 在同步规则后仍有表格、关系、leaf 或权威引用错误 | 领域规则同步器 | 点名 Map、leaf 与错误 | 整轮不写，init 不登记领域路径 | 无效项目正文不因规则同步进入提交 |
| leaf 链接失效 | `Leaf` 指向不可读文件 | `mmw doctor` | 显示失效路径 | 返回非零 | 每条 Map leaf 均存在 |
| 权威引用失效 | `authoritative` 指向 Map 未登记的 leaf | `mmw doctor` | 显示来源 leaf 与失效目标 | 返回非零 | 权威引用可解析 |
| fallback 不合格 | fallback 已存在但不是普通、可读的 UTF-8 Markdown 文件 | `mmw doctor` | 点名 fallback | 返回 `unreadable-single` | 不把损坏 single 静默当成 none |
| 回滚不完整 | 正向替换失败后任一已替换目标恢复失败 | 领域规则同步器 | `io-error` 点名未恢复目标 | 清理回滚临时文件并返回非零 | 失败状态完整可见 |
| 同步无变化 | 目标区块已经等于种子 | 同步器 | 报告已是最新 | 不重写文件，不登记提交 | 连续同步第二次无 diff |

## Testing Decisions

| Seam | 验证什么行为 | 为什么是这一层 |
| --- | --- | --- |
| 临时 Git 仓库中的领域规则同步 CLI | 创建、插入、升级、幂等、损坏标记、符号链接、目标冲突、Map 候选和原子失败 | 这是用户实际调用的文件边界，能覆盖种子、解析、原子写和退出码 |
| 临时 Git 仓库中的领域路径 CLI | 自定义 map、fallback、context 和 ADR 路径的四行落点，以及越界或含控制字符的配置失败 | 这是领域建模流程取得首份文档落点的公开边界 |
| 临时 `none`、`single`、`map` fixture 上的领域检查 CLI | 三种合法形态、普通 UTF-8 fallback、GFM 三列表格、leaf 边界和 authoritative 引用 | 这是领域文档合同的最高稳定边界，不绑定内部函数 |
| `mmw init` 临时仓库流程 | 新仓库、已有干净仓库、已有脏目标、带空格路径、无效 Map、Claude bridge 和实际变化路径登记 | 这是配置流程的公开入口 |
| 技能与 Codex 物化检查 | 三套技能产物和 Codex 发布输入无漂移 | 这是宿主发布结果的现有检查 seam |
| AgentFlow 仓库 guard 与真实 Map | 标准 Map、现有七份 leaf、宿主规则加载均有效 | 这是首个消费仓库的真实验收边界 |

仓库不保留自动化测试套件。实现时使用临时 fixture 执行上述行为测试，并按根 `TESTING.md` 运行 ShellCheck、JSON 校验、`git diff --check` 和物化检查。

## Contract Boundaries

| 边界 | 归属方 | 提供方 | 消费方 | 合同 | 登记与验证 |
| --- | --- | --- | --- | --- | --- |
| 目标仓库领域路径 | 目标仓库 | `.mmw.json` | 领域同步器、`mmw domain path`、`mmw domain dirs` | `map`、`fallback`、`context_dir`、`adr_dir` | `mmw doctor` 读取真实文件验证 |
| `AGENTS.md` 受管区块 | MMW | AGENTS 种子 | 主 agent、subagent | 一对唯一标记及其间的固定正文；目标是普通文件且不与 Map、CLAUDE 重合 | 同步器精确比较，doctor 检查 |
| Claude Code 规则入口 | 目标仓库 | 根 `CLAUDE.md` | Claude Code 主 agent、subagent | 导入根 `AGENTS.md` | init 同步并检查导入 |
| Map 使用规则区块 | MMW | Map 规则种子 | 读取 Map 的 agent | 一对唯一标记及其间的固定正文 | 同步器精确比较，doctor 检查 |
| Map 项目路由 | 目标仓库 | `Contexts`、`Relationships` | 读取 Map 的 agent、doctor | GFM 三列表格、自然语言关系列表、真实 leaf 路径 | 同步前与 doctor 都验证结构和路径；agent 解释关系语义 |
| 技能发布产物 | MMW 技能源 | 技能物化器 | Pi、Claude Code、Codex | 三个宿主的物化 Markdown | 物化 `--check` 与 Codex runtime 检查 |

## Cross-Plan Contract Anchors

| Plan | 文件归属 | 提供 | 消费 |
| --- | --- | --- | --- |
| 01 | 当前已漂移的 Pi 与 Claude Code 物化文件；不得修改技能源 | `mmw skills materialize --host all --check` 返回成功的三宿主零漂移基线 | 03 在 01 集成后重新物化领域技能改动 |
| 02 | 两份领域规则种子、`context_docs.py`、init、domain、doctor CLI 接入和根 `AGENTS.md` 受管区块 | `mmw domain sync` 四列 TSV、`mmw domain check` 四列 TSV、`mmw domain path` 三列 TSV、`mmw domain dirs` 四行 TSV、doctor 领域状态行和两对固定 marker | 03 的领域建模技能、关键产出技能和架构图 |
| 03 | 领域技能源、01 基线完成后的三宿主物化产物、根 `TESTING.md`、架构可视化和发布版本字段 | `0.9.0` 正式发布内容 | AgentFlow 独立迁移任务 |

物化目录采用阶段性交接：01 只恢复既有源对应的基线并先集成；03 才能在领域技能源改变后重新生成最终产物。02 不修改物化目录。

Plan 02 固定使用以下公开命令：`mmw domain sync` 成功时逐目标输出 `sync<TAB><agents|map|claude><TAB><仓库相对路径><TAB><状态>`；`mmw domain check` 成功时输出 `check<TAB><none|single|map><TAB><仓库相对路径或 -><TAB>valid`；`mmw domain dirs` 成功时按 `single`、`map`、`context`、`adr` 顺序输出 `<类型><TAB><绝对路径>`。失败统一返回 `1`，并把可定位诊断写入 stderr。Plan 03 只消费这些合同，不复制检查逻辑。

## Release Risk

改动只更新 Markdown 合同、CLI 同步和检查行为，不迁移业务数据。受管区块更新可由版本控制回滚。同步器遇到歧义标记时停止，避免覆盖用户内容。

MMW 发版后，AgentFlow 在独立 worktree 使用新同步流程迁移。发布入口的版本字段按仓库合同同步更新。正式发布和推送仍需用户单独授权。

## Out of Scope

- 不移动或重命名 AgentFlow 的七份 leaf；路径迁移没有业务价值。
- 不在 subagent task 中逐份注入 leaf 路径；subagent 读取同一份 `AGENTS.md`。
- 不让 MMW 根据目录或内容猜 bounded context 所有权。
- 不把宿主 cascade、override 或桥接实现写入通用 Map。
- 不把操作步骤、计划、发布状态或一次性调查写入领域文档。
- 不在本次改动中修复 AgentFlow 的 `.worktrees` guard 漏排除或陈旧的 Pi 测试文档；两项分别独立提交。
