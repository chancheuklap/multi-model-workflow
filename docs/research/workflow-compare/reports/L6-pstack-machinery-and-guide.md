# L6 pstack 的外壳、agent 定义、guide 与 benny automation pack

范围：`docs/research/code-landing-refs/pstack/` 下的 `README.md`（261 行）、`.cursor-plugin/plugin.json`（31 行）、`agents/poteto-agent.md`（9 行）、`agents/comment-sicko.md`（32 行）、`docs/guide/` 下除 `08-principles.md` 外的全部 10 个文件、`automations/benny/` 下全部 11 个文件。以上文件都已逐行读完。另外为核对连线，查看了范围外几处 frontmatter 和引语：`skills/*/SKILL.md` 第 2 到 8 行、`skills/no-comments/SKILL.md` 第 3、9、11、19 行、`skills/poteto-mode/SKILL.md` 第 1 到 8 行和第 91 行、`skills/poteto-mode/playbooks/multi-phase-plan.md` 第 7 行。凡是引到这些范围外位置的地方，都标了「范围外核对」。

写法约定：「原文」表示文件里写明；「推断」是我的推理；读不到或拿不准的都放进第 9 节「未确定」。

---

## 1. 组件清单

| 文件 | 组件类型 | 管什么 |
|---|---|---|
| `README.md` | 文档（插件门面） | 安装、入口 `/poteto-mode`、23 个 playbook 的索引表、技能表、principle 表、两个 subagent、未随插件发布的依赖、benny 入口 |
| `.cursor-plugin/plugin.json` | 配置（插件清单） | 声明插件元数据和两个交付面：`"skills": "./skills/"`、`"agents": "./agents/"` |
| `agents/poteto-agent.md` | agent 定义 | 一个 subagent 类型，唯一职责是「先完整读 `poteto-mode` 的 SKILL.md」 |
| `agents/comment-sicko.md` | agent 定义（带人设的只读审查者） | 只审注释：保留清单、`MUST KILL` 标记、只出报告不改代码 |
| `docs/guide/README.md` | 文档（教程索引） | 10 页教程的目录，以及「目标 + 检验方式」这一条核心习惯 |
| `docs/guide/01-setup.md` | 文档（教程） | 安装、`/setup-pstack`、模型规则文件、验证技能的提议、第一个任务 |
| `docs/guide/02-poteto-mode.md` | 文档（教程） | 提示词如何被路由到 playbook、sticky、`new task`、worktree |
| `docs/guide/03-understand.md` | 文档（教程） | `/how`、`/why`、`/teach`、`/recall`、Session pickup |
| `docs/guide/04-design.md` | 文档（教程） | `/architect`、`/arena`、`/swarm`、`/interrogate`，以及按需投入设计工作的阶梯 |
| `docs/guide/05-build-and-clean.md` | 文档（教程） | 各构建类 playbook 的提示写法、`/tdd`、typescript 规则、`/deslop`、`/unslop`、`/no-comments` |
| `docs/guide/06-verify-and-ship.md` | 文档（教程） | 完成条件、验证技能的生成与维护、开 PR、Babysit、Shipping |
| `docs/guide/07-overnight.md` | 文档（教程） | 过夜约定（overnight contract）、`/loop`、决策日志、Autopilot 和 Orchestrate |
| `docs/guide/09-make-it-yours.md` | 文档（教程） | `/automate-me`、`/reflect`、编写技能、`/technical-writing`、Eval |
| `docs/guide/10-recipes-and-pitfalls.md` | 文档（教程） | 可复制的提示词和常见错误 |
| `automations/benny/README.md` | 文档（人读的安装说明） | 6 步安装 benny |
| `automations/benny/FOR_AGENTS.md` | 意图文档，同时是 bootstrap 入口（给 agent 的指令） | 人写的两个 automation 的意图、共享规则、配置占位，以及「for the agent」7 步把 pack 拷进目标仓库 |
| `automations/benny/skills/setup-benny/SKILL.md` | 能力技能形态的「操作文件」（按路径读，不注册） | 8 节的安装与配置流程 |
| `automations/benny/skills/triage-issue-reports/SKILL.md` | 操作文件（automation 1 的全部指令） | 10 节：冻结坐标 → 读报告 → 追因 → 分类 → 路由 → tracker 适配器 → 去重 → 建单 → 发一次结论 → 跟进窗口 |
| `automations/benny/skills/reproduce-and-fix-issues/SKILL.md` | 操作文件（automation 2 的全部指令） | 15 节：从冻结坐标一直到开 draft PR 和清理 |
| `.../triage-issue-reports/references/routing.example.md` | reference（配置模板，按数据读取） | 路由表的 YAML 样例和规则 |
| `.../reproduce-and-fix-issues/references/control-adapter.md` | reference（接口契约） | 控制适配器必须提供的 7 项能力、行为要求、环境转换规则、9 步安装检查 |
| `.../reproduce-and-fix-issues/references/verify-existing-fix.md` | reference（分支流程） | 已有修复时进入的验证模式：基线、补丁、三种结果 |
| `.../reproduce-and-fix-issues/references/feature-map.example.md` | reference（配置模板） | 每个功能一节的模板、虚构示例、完整性检查清单 |
| `automations/benny/templates/configuration.example.yaml` | 配置模板 | `schema_version: 1`，分 slack / repository / tracker / routing / control / markers / emoji / budgets / models 九组 |
| `automations/benny/templates/triage-automation-prompt.md` | 提示词模板（给 `/automate` 的原料） | triage automation 的提示词骨架，带 `{{…}}` 占位 |
| `automations/benny/templates/reproduce-automation-prompt.md` | 提示词模板 | repro automation 的提示词骨架 |

我负责的文件里没有 mode、playbook、principle 或脚本。这几类组件只从 README 和 guide 对它们的描述里看得到，另外对 frontmatter 做了范围外核对。

---

## 2. 逐个组件解剖

### 2.1 `.cursor-plugin/plugin.json`（31 行，JSON）

- 键：`name`、`displayName`、`version: "0.15.4"`、`description`、`author.name: "Lauren Tan"`、`homepage`、`repository`、`license: "MIT"`、`logo: "assets/logo.png"`、`keywords`（7 个）、`category: "developer-tools"`、`tags`（4 个，其中有 `"planning"`）、`"skills": "./skills/"`、`"agents": "./agents/"`。
- 交付面（原文）：只声明了 `skills` 和 `agents` 两个目录。没有 rules、hooks、commands、MCP 之类的键。`automations/` 和 `docs/` 都不在清单里。
- 推断：README 说 `/setup-pstack` 写的是「a small always-applied rule」，所以 Cursor rule 这个交付面不走插件清单，而是由技能在运行时写到 `~/.cursor/rules/pstack-models.mdc`（`docs/guide/01-setup.md`「Pick your models」）。
- 快照缺口：`logo` 指向的 `assets/logo.png` 和 guide 引用的 `./images/*.jpg` 都不在快照里（用 `ls` 确认过，目录不存在）。

### 2.2 `agents/poteto-agent.md`（9 行）

- frontmatter：
  - `name: poteto-agent`
  - `description:` 有四句：先说身份「Routing target for `/poteto-mode` and any request for poteto's style.」；再说复用规则「Resume an existing `poteto-agent` for the conversation rather than spawning a sibling.」；再说行为「Reads the `poteto-mode` skill's `SKILL.md` in full before any work, including its inline Principles index.」；最后是反例「Substituting `generalPurpose` skips that read and drifts.」
  - `is_background: true`
- 正文：一个 H1 `# Poteto subagent`，加一段两句话：「Read the `poteto-mode` skill's `SKILL.md` in full before doing any work, including its inline Principles index. Navigate to a leaf `principle-*` skill whenever you apply that principle.」
- 语气是第二人称祈使句。正文不带任何规则，只指路。
- 这意味着什么（推断）：
  1. agent 定义只是一层外壳，规则的唯一来源是 mode 技能。行为改动只改 `poteto-mode/SKILL.md`，agent 文件不用同步，所以不会出现两份规则漂移。README「the `poteto-agent` and Comment Sicko subagents」写道「`/poteto-mode` and `subagent_type: "poteto-agent"` route through the same wrapper.」
  2. 全部技能都是 `disable-model-invocation: true`（见 5.4），subagent 不会自己按描述加载 mode。所以需要一个 subagent 类型，在启动时把「先读 mode」变成硬性第一步。反例写进 description（`generalPurpose` 会 drift），就是为了让调用方选对 `subagent_type`。
  3. `is_background: true` 加上「Resume … rather than spawning a sibling」，说明它被设计成一次会话里常驻、可复用的工作者，而不是一次性工具。
- 范围外核对：`skills/poteto-mode/SKILL.md` 第 91 行「Use `subagent_type: "poteto-agent"` for any subagent you spawn inside a playbook step … Routed workflow skills (`how`, `why`, `interrogate`, `reflect`, `swarm`) set their own `subagent_type` for diverse-model review.」`skills/poteto-mode/playbooks/multi-phase-plan.md` 第 7 行也按 `subagent_type: "poteto-agent"` 派生。

### 2.3 `agents/comment-sicko.md`（32 行）

- frontmatter：`name: Comment Sicko`（带空格，大小写混用，也就是 `subagent_type: "Comment Sicko"`）；`description: A deranged comment-hater that savors deletion and condemns workaround code.`。没有 `is_background`。
- 正文结构：H1 → 固定开场白（「My first output when spawned is exactly this. / Yes... Ha ha ha... Yes!」）→ 输入范围（「Feed me the parent scoped files or diff. If none exists, feed me the current diff against `main`.」）→ 保留清单，共 5 条（license header、外部依赖强加的行为、`// prettier-ignore`、公开 API 的 doc comment、issue 或 RFC 链接）→ 判定规则（「When I am not sure a keep clause applies, the comment dies.」）→ 对各类 suppression 的处理 → 对 `IMPORTANT` / `do not remove` 这类措辞的取证：「I run `/how`, `/why`, or both from the **how** and **why** skills on the named symbol or call.」→ 越权边界（「I do not touch the code.」「I never write application code.」）→ 输出格式（「Report only. Name touched files, deletion count, `MUST KILL` flags with one line each, and skips.」）。
- 语气：第一人称人设，用夸张的比喻（「meat」「confession」「alibi」）。整份文件只有判断规则、边界和输出格式，没有步骤顺序。
- 为什么单独做成 agent（原文理由）：`docs/guide/05-build-and-clean.md`「Strip the comments with `/no-comments`」写道「Comments need their own pass, and not from the agent that wrote them. An author defends its comments the way you'd defend yours. So before review, hand them to fresh eyes」，以及「a read-only reviewer with a short keep list」。README 写「usually invoke it through `/no-comments`, not directly.」
- 推断：它是 agent 而不是技能，因为关键是「另一个上下文、不是作者本人」，这只有 subagent 能做到。技能会在作者自己的上下文里加载。另外，保留清单写在 agent 里，调用方 `/no-comments` 就不必复述。范围外核对：`skills/no-comments/SKILL.md` 第 19 行「Spawn `Task` with `subagent_type: "Comment Sicko"`. Pass the scope. Do not restate its rules.」
- 分工：Comment Sicko 只出 `MUST KILL` 标记，`/no-comments` 负责「fix accepted findings, and offer encodings for claimed constraints」（范围外核对，第 3 行 description）。这是「只读审查者 agent + 执行技能」的拆法。

### 2.4 `README.md`（261 行）

- 没有 frontmatter。章节顺序：开场宣言（第 1 到 13 行，第一人称小写口语）→ `## install` → `## get started`（两步）→ `## usage`（23 个 playbook 的表，以及 invoked 之后做的 3 件事，外加 sticky 说明）→ `## skills`（技能表 + 示例）→ `## the poteto-agent and Comment Sicko subagents` → `## principles`（23 条的表，分 core / architecture / verification / delegation / meta 五组）→ `## not shipped here` → `## why are there no planning skills?` → `## make it yours` → `## automations` → `## license`。
- 关于分层的原文陈述：
  - mode 的职责：「it reads your request, picks from a set of playbooks, and runs the other skills as the steps need them.」（第 34 行）
  - playbook 进 todo：「matches your task to a playbook and opens a todo list whose first items are its steps, copied in verbatim.」（第 85 行）
  - sticky：「once entered it stays on across turns, applying itself when a playbook matches or the task needs rigor and staying out of the way otherwise. opt out any time by saying so.」（第 91 行）
  - 为什么 principle 单独成技能：「twenty-three short skills, one principle each. `poteto-mode` indexes them inline and reads that index at task start. the standalone files are there so other skills can reference a principle by name, and so the index can point at the full rule for each.」（第 196 行）
  - 技能由 mode 代为调用：「`/poteto-mode` runs most of these for you when a step needs them (`how`, `why`, `architect`, …, and the principles). the table below is for when you want one directly」（第 97 行）
  - 没有 planning 技能：「the best spec is code.」（第 241 行）
  - 外部依赖：`deslop`、`control-cli`、`control-ui` 在 `cursor-team-kit`；`/create-skill` 是 Cursor 内置；babysit playbook「supersedes」Cursor 内置的 `/babysit`（第 231 到 237 行）。
  - 模型配置：「writes a small always-applied rule mapping each role … every skill reads it and falls back to sensible defaults when the rule is absent, so you override only what you want.」（第 249 行）
  - 扩展方式：`/automate-me`「drafts a `<your-name>-mode` skill … and routes through pstack underneath. you keep pstack as the base and end up with your own routing skill alongside `poteto-mode`.」（第 247 行）
  - benny：「pstack also ships a dormant benny automation pack … its files are not registered as slash skills.」（第 255 行）

### 2.5 `docs/guide/` 各页的共同写法

- 都没有 frontmatter。每页结构相同：H1 → 一段「In this page you …」或说明问题的引子 → 配图（`![…](./images/…jpg)`，快照里缺图）→ 若干 H2，每个 H2 是「一个 `text` 代码块的示例提示词 + 一段解释它为什么有效」→ 大多数页末尾有一条 `**Pitfall:**` → `Next: [...]`。
- 语气：第二人称，Google developer style（「You might be wondering…」出现在 01 和 04）。内容是用户怎么说、背后发生什么、理由，不写 agent 的执行步骤。
- 行数：README 30、01 49、02 98、03 53、04 81、05 75、06 87、07 81、09 67、10 94。
- 02 和 07 各有一张 mermaid 流程图（路由图、过夜循环图），04 有一张 arena 的流程图。

逐页装的内容：

| 页 | 装的内容 | 关于机制的原文要点 |
|---|---|---|
| README | 目录和核心习惯 | 「"repro first" and a checkable outcome are all the routing signal `/poteto-mode` needs. It matches the Bug fix playbook, copies the steps into a todo list, and calls the right skills as each step fires.」 |
| 01 | 安装、模型角色 | 模型规则文件 `~/.cursor/rules/pstack-models.mdc`；`inherit-parent`/`auto` 表示省略 `model` 字段；panel 角色是列表，「the list length sets the panel size」；跳过的步骤写成 `skip: <reason>`；「After setup, start a new chat. The model rule applies to new sessions.」 |
| 02 | 路由 | 「Short works because the mode is sticky and the playbook holds the structure. Your words carry the intent, and the skill carries the rigor.」；「"new task" tells `/poteto-mode` to re-match rather than continue the prior playbook.」；Pitfall：「don't enumerate skills in your prompt … a hand-written sequence usually reorders or drops steps the playbook would have kept.」 |
| 03 | 理解代码 | `/teach` 调 `/how` 和 `/why`；Session pickup「treats the prior trail as authoritative」 |
| 04 | 设计 | `/architect` 调 `/how`、`/why`、`/arena`；arena 和 swarm 的区别；阶梯最后一句「`/poteto-mode` already applies this ladder.」 |
| 05 | 构建与清理 | 「the playbook supplies the steps you didn't type」；typescript 规则「loads whenever the agent touches a `.ts` or `.tsx` file」；Opening a PR playbook 跑 `/deslop` 和 `/unslop` |
| 06 | 验证与发布 | `principle-prove-it-works` 引出「your job is to make "the real artifact" checkable」；验证技能生成到 `.cursor/skills/verify-<app>/`；Babysit「never merges」；Shipping「the agent that judges a change is never the one that wrote it」 |
| 07 | 过夜 | 过夜约定的 4 个要素，逐行说明每行的作用；`/loop` 是 Cursor 内置；决策 TSV；Autopilot-full、Autopilot-stack、Orchestrate |
| 09 | 定制 | 「The machinery underneath, playbooks, routing, model roles, works just as well wearing yours.」；编写技能走 playbook 而不要徒手写；Eval 针对 observer effect |
| 10 | 配方与坑 | 8 条 pitfall，其中 1、2、3、7 条是 02、05、07 里 pitfall 的复述 |

### 2.6 benny：`FOR_AGENTS.md`（89 行）

- 没有 frontmatter。结构：`# benny automation intent` → `## what i want to automate`（两个 automation，每个都用固定的 bullet 标签：`trigger` / `behavior` / `tracker` 或 `gates` / `fix` / `tools` / `outcome` / `boundary`）→ `### shared rules`（9 条）→ `### my configuration`（13 个占位）→ `## for the agent`（7 步 + settings.json 合并 + 验证 + 提交提醒 + 首次用 `/automate` 创建 + 已有 automation 的处理）。
- 语气：前半是第一人称用户意图（「i want …」「i never want …」），后半是对 agent 的祈使句。
- 作用（原文）：「the human enters setup by pointing cursor at this file. do not look for or invoke a discovered benny slash skill.」setup-benny §7 写道「Read `../../FOR_AGENTS.md` from the copied pack as the primary user-intent source」。
- 推断：它同时承担 README 式的意图说明和 bootstrap 脚本两种角色。以文字形式存在，是因为执行者是 agent，不是 shell。

### 2.7 benny：`setup-benny/SKILL.md`（266 行）

- frontmatter：`name: setup-benny`；`description: Configure Benny and prepare its triage and repro automations. Use when installing Benny or changing its Slack, tracker, repository, routing, control, model, or budget settings.`；`disable-model-invocation: true`。
- description 句式：一句功能 + 一句「Use when …」触发条件。
- 正文：开头 4 段说明定位（「The plugin manifest exposes only pstack's normal skill root; this file and the two operational files are not slash skills.」）和两条硬规则（不擅自创建 automation、不放 secret）。之后是编号的 H2：`## 1. Copy the pack and enable shared pstack skills` → `## 2. Adapt the configuration` → `## 3. Fill the required choices` → `## 4. Check integration capabilities` → `## 5. Prepare the routing map` → `## 6. Verify the control adapter` → `## 7. Prepare the live automations`（其下有 `### First-time creation` / `### Existing automations` / `### Creation boundary`）→ `## 8. Test thread safety`（7 项验证）。
- 内容：编号 H2 给出步骤顺序；H2 里面既有做法（怎么合并 JSONC），也有判据（「Do not count a skill loaded from the current session or a user-scoped plugin.」）和交给外部技能的边界（「Do not duplicate `automate`'s Slack, repository, integration, … or editor-handoff work.」）。

### 2.8 benny：`triage-issue-reports/SKILL.md`（240 行）

- frontmatter：`name`、`description: Triage Slack issue reports with one thread-only verdict, evidence review, cause-aware routing, tracker dedupe, and fail-closed ticket creation. Use only from the configured Benny triage automation.`、`disable-model-invocation: true`。触发条件写成「Use only from …」，排他式。
- 正文：H1 → 两段定位（做什么和不做什么：「Do not reproduce or fix it here.」；缺配置就停）→ `## Hard safety rules`（14 条 bullet，最后两条点名 principle）→ `## 1.` 到 `## 10.` 编号步骤。§4 下用 H3 列出 5 个类别；§9 有一个 `text` 代码块给出 marker 契约。
- 内容：顺序靠编号 H2 表达；每步里是捕获清单、判据（例如 §7 的 4 档去重结果）、硬门槛（§8 的 7 个 AND 条件）。输出格式在 §9。

### 2.9 benny：`reproduce-and-fix-issues/SKILL.md`（310 行）

- frontmatter 的形态和 triage 相同，也是「Use only from the configured Benny repro automation.」加 `disable-model-invocation: true`。
- 正文：H1 → 两段定位 → `## Hard safety rules`（18 条，最后两条点名 4 个 principle）→ `## 1.` 到 `## 15.` 编号步骤。§3 分成三个 H3 门槛；§3 和 §10 转到 `references/verify-existing-fix.md`；§5 读 `references/control-adapter.md` 和用户的 feature map，并调用 `control.skill_name` 指定的技能；§6 调 `how`/`why`；§12 调 `tdd`；§14 调 `unslop`。
- 语气：祈使句、短句，大量「Never / Do not / Only」。

### 2.10 benny 的 references 与 templates

- `control-adapter.md`（169 行）：接口契约。H2 `Required capabilities` 下每项能力一个 H3，写明 Input / Return / 禁止事项；`Adapter behavior`；`Environment translation`；`Setup check`（9 步）。装的是契约和判据，不是调用方的流程。
- `verify-existing-fix.md`（93 行）：一个分支模式的完整小流程：Qualify → Protect the working tree → baseline → patched → 三种 Outcomes → Cleanup。
- `routing.example.md`（61 行）、`feature-map.example.md`（205 行）：配置模板。都写明要「Copy this file outside `.cursor/automations/benny/` … Pack refreshes must not overwrite it.」routing 的文件头说「The triage skill treats this as data.」
- `configuration.example.yaml`（84 行）：`schema_version: 1`；安全开关默认关闭（`allow_source_root_posts: false`、`allow_worker_slack_writes: false`、`draft_only: true`、`owner_pings_default: false`）。
- 两个 prompt 模板（39 行和 33 行）：开头是 blockquote 说明「Source material for the copied setup workflow. Paraphrase this intent into a built-in `automate` draft…」；然后是「Read and follow `<path>` for this run.」、`{{BENNY_CONFIG_PATH}}`、trigger JSON 占位，以及复述的硬规则。

---

## 3. 调用与连线

### 3.1 pstack 主体（从我负责的文件看得到的部分）

- 用户用斜杠命令 `/poteto-mode` 调 mode，也可以直接用斜杠命令调任何技能（README `## skills`：「the table below is for when you want one directly」）。
- mode 路由到 playbook，把 playbook 步骤抄进 todo，再在步骤触发时调能力技能和 principle（README 第 83 到 87 行；guide README）。
- 父 agent 用 `subagent_type: "poteto-agent"` 派生 poteto-agent；poteto-agent 读 mode，并在应用某条 principle 时去读对应的 leaf `principle-*` 技能。
- `/no-comments` 用 `subagent_type: "Comment Sicko"` 派生 Comment Sicko；Comment Sicko 取证时跑 `/how` 和 `/why`。
- 能力技能之间的调用（guide 原文）：`/teach` 调 how 和 why（03）；`/architect` 调 how、why、arena（04）；`/figure-it-out` 接上 `/show-me-your-work`（02、07）；`/automate-me` 调内置 `create-skill` 和 `/unslop`，然后走 PR（09）；`/setup-pstack` 在找不到验证手段时提议调 `/create-verification-skill`（01）；Opening a PR playbook 调 `/deslop`（外部插件）和 `/unslop`（05）；autonomous-run playbook 用内置 `/loop`（07）；authoring-a-skill playbook 走内置 `create-skill`，再交给 Opening a PR playbook（09）；`/show-me-your-work` 派一个其他模型家族的 reviewer（07）；`/reflect` 派三个并行 reviewer 和一个 synthesizer（09）。
- 配置：每个技能都读 `~/.cursor/rules/pstack-models.mdc`（README 第 249 行，01）。

### 3.2 benny

- 人把 Cursor 指到 `FOR_AGENTS.md`（相对路径入口，不用斜杠命令）。`FOR_AGENTS.md` 的 §「for the agent」第 7 步要求读目标仓库里的 `.cursor/automations/benny/skills/setup-benny/SKILL.md`。
- setup-benny 读 templates 和 references（`../../templates/configuration.example.yaml`、`../reproduce-and-fix-issues/references/feature-map.example.md`、`../triage-issue-reports/references/routing.example.md`、`../reproduce-and-fix-issues/references/control-adapter.md`），读 `../../FOR_AGENTS.md`，调用 Cursor 内置 `automate` 技能，调用 pstack 的 `unslop`。
- 运行时：Cursor automation 的提示词写着「Read and follow `.cursor/automations/benny/skills/<x>/SKILL.md`」，用稳定的仓库相对路径直接读取。原文禁止用 plugin cache 路径，也禁止拷贝文件内容（setup-benny §1 末段、FOR_AGENTS shared rules）。
- triage → repro 之间没有直接调用，而是通过 Slack 线程里的 marker（`[benny:bug]` 等）交接，repro 只信任配置里 triage identity 发的 marker（triage §9，repro §2）。
- 两个操作文件按技能名调 pstack 共享技能（`how`、`why`、`tdd`、`unslop`），按名字点名 principle。这些共享技能通过目标仓库 `.cursor/settings.json` 里的 `"plugins": {"pstack": {"enabled": true}}` 在项目范围内解析。

```edges
user -> poteto-mode : calls (slash /poteto-mode)
user -> how : calls (slash, direct)
user -> no-comments : calls (slash, direct)
poteto-mode -> playbooks/* : routes-to
poteto-mode -> principle-* : cites-principle (inline Principles index)
poteto-mode -> how : calls
poteto-mode -> why : calls
poteto-mode -> architect : calls
poteto-mode -> arena : calls
poteto-mode -> swarm : calls
poteto-mode -> interrogate : calls
poteto-mode -> unslop : calls
poteto-mode -> no-comments : calls
poteto-mode -> technical-writing : calls
poteto-mode -> tdd : calls
poteto-mode -> figure-it-out : routes-to (large work or no playbook match)
poteto-mode -> poteto-agent : spawns-subagent (subagent_type, from playbook steps)
poteto-agent -> poteto-mode : reads-reference (reads SKILL.md in full before any work)
poteto-agent -> principle-* : cites-principle (navigate to leaf when applying)
no-comments -> Comment Sicko : spawns-subagent (subagent_type: "Comment Sicko")
Comment Sicko -> how : calls
Comment Sicko -> why : calls
teach -> how : calls
teach -> why : calls
architect -> how : calls
architect -> why : calls
architect -> arena : calls
figure-it-out -> show-me-your-work : calls
automate-me -> create-skill(cursor built-in) : calls
automate-me -> unslop : calls
setup-pstack -> create-verification-skill : hands-off-to (offered once)
playbooks/opening-a-pr -> deslop(cursor-team-kit) : calls
playbooks/opening-a-pr -> unslop : calls
playbooks/authoring-a-skill -> create-skill(cursor built-in) : calls
playbooks/authoring-a-skill -> playbooks/opening-a-pr : hands-off-to
playbooks/autonomous-run -> /loop(cursor built-in) : calls
playbooks/* -> playbooks/opening-a-pr : hands-off-to (README: invoked at the end of every other playbook)
playbooks/babysit -> /babysit(cursor built-in) : supersedes (self-coined: replaces the built-in inside poteto-mode)
show-me-your-work -> reviewer(other model family) : spawns-subagent
reflect -> reviewers x3 + synthesizer : spawns-subagent
typescript-best-practices -> principle-type-system-discipline : cites-principle (README: grounds it in syntax)
all-skills -> ~/.cursor/rules/pstack-models.mdc : configured-by
setup-pstack -> ~/.cursor/rules/pstack-models.mdc : writes (self-coined)
plugin.json -> skills/ : declares (self-coined)
plugin.json -> agents/ : declares (self-coined)
user -> benny/FOR_AGENTS.md : calls (point Cursor at file path)
benny/FOR_AGENTS.md -> benny/skills/setup-benny/SKILL.md : hands-off-to (read by target-repo path)
setup-benny -> benny/templates/configuration.example.yaml : reads-reference
setup-benny -> reproduce-and-fix-issues/references/feature-map.example.md : reads-reference
setup-benny -> triage-issue-reports/references/routing.example.md : reads-reference
setup-benny -> reproduce-and-fix-issues/references/control-adapter.md : reads-reference
setup-benny -> benny/FOR_AGENTS.md : reads-reference (primary user-intent source)
setup-benny -> benny/templates/triage-automation-prompt.md : reads-reference
setup-benny -> benny/templates/reproduce-automation-prompt.md : reads-reference
setup-benny -> automate(cursor built-in) : calls
setup-benny -> unslop : calls
setup-benny -> target/.cursor/settings.json : configured-by (writes plugins.pstack.enabled)
cursor-automation(benny-triage) -> triage-issue-reports/SKILL.md : reads-reference (repo-relative path)
cursor-automation(benny-reproduce) -> reproduce-and-fix-issues/SKILL.md : reads-reference (repo-relative path)
triage-issue-reports -> user-config(.cursor/benny/*.yaml) : configured-by
triage-issue-reports -> routing map (routing.map_path) : reads-reference (as data)
triage-issue-reports -> how : calls
triage-issue-reports -> why : calls
triage-issue-reports -> unslop : calls
triage-issue-reports -> principle-separate-before-serializing-shared-state : cites-principle
triage-issue-reports -> principle-minimize-reader-load : cites-principle
triage-issue-reports -> issue-tracker adapter (tracker.adapter_skill_name) : calls
triage-issue-reports -> reproduce-and-fix-issues : hands-off-to (Slack marker in source thread)
reproduce-and-fix-issues -> user-config(.cursor/benny/*.yaml) : configured-by
reproduce-and-fix-issues -> references/verify-existing-fix.md : routes-to (fix artifact exists)
reproduce-and-fix-issues -> references/control-adapter.md : reads-reference
reproduce-and-fix-issues -> feature map (control.feature_map_path) : reads-reference
reproduce-and-fix-issues -> control adapter (control.skill_name) : calls
reproduce-and-fix-issues -> how : calls
reproduce-and-fix-issues -> why : calls
reproduce-and-fix-issues -> tdd : calls
reproduce-and-fix-issues -> unslop : calls
reproduce-and-fix-issues -> principle-guard-the-context-window : cites-principle
reproduce-and-fix-issues -> principle-sequence-verifiable-units : cites-principle
reproduce-and-fix-issues -> principle-fix-root-causes : cites-principle
reproduce-and-fix-issues -> principle-prove-it-works : cites-principle
reproduce-and-fix-issues -> read-only workers : spawns-subagent (Slack-write ban in every child prompt)
```

---

## 4. 边界判据（从原文和实际写法看）

### 4.1 mode 与其它组件

- 原文：mode 做三件事：匹配 playbook、按步骤路由到其它技能、按统一风格写回复（README 第 83 到 87 行）。它是唯一带 `mode: true` 和 `reminder:` 的技能（范围外核对：`skills/poteto-mode/SKILL.md` 第 5 行 `mode: true`，第 8 行 `reminder: New task? Playbook match or rigor needed -> apply /poteto-mode. Casual turn or user opts out -> don't.`）。
- 为什么常驻，原文理由：「Short works because the mode is sticky and the playbook holds the structure. Your words carry the intent, and the skill carries the rigor.」（02「Say the goal, not the ceremony」）。README 第 91 行说它「applying itself when a playbook matches or the task needs rigor and staying out of the way otherwise」。
- 推断：`reminder` 是 sticky 的实现手段。每轮用一句话让模型判断「新任务就重新应用 mode，闲聊或用户退出就不应用」，这样不用每轮重新加载全文。重新匹配由用户说 `new task` 显式触发（02「Switch tasks with "new task"」）。

### 4.2 playbook 与能力技能

- 原文里 playbook 的特征：由 mode 选出；步骤「copied in verbatim」进 todo（README 第 85 行）；「The playbook already sequences them」（02 Pitfall）；「the playbook supplies the steps you didn't type: reproduce before fixing, name the data shape before implementing, pin behavior before restructuring, profile before optimizing」（05）。这说明 playbook 装的是跨技能的步骤顺序，以及每类任务特有的先后门槛。
- 原文里能力技能的特征：用户也能直接用斜杠命令调用（README `## skills`），每个技能是一项可复用的能力（「`/arena` is the general tool underneath」，04）。
- 能力技能自带多步流程为什么没拆成 playbook：guide 没有直接陈述。可以观察到的写法有两点。第一，技能内部的步骤是这项能力自己的做法，例如 arena 的「candidates → cross-judge → pick a base → graft → verify」（04 的 mermaid 图），不在技能之间排顺序。第二，这些技能要能被多个 playbook 和用户直接复用，拆开就没法单独调用了。推断：判据是「步骤顺序是否跨越多个能力、是否由任务类型决定」。一项能力自己的固定流程留在技能里；按任务类型编排多项能力的顺序才是 playbook。
- 有一个反例值得注意：`figure-it-out` 是技能，但它的职责是「designs a rigorous, auditable playbook for the task」（README 技能表），也就是生成 playbook 的技能。它在没有匹配的 playbook 或任务很大时被 mode 路由到（02 的 mermaid 图：「Large work or no match → figure-it-out」）。

### 4.3 principle 与调用方正文里的规则

- 原文理由（README 第 196 行）：principle 单独成文件，是为了「other skills can reference a principle by name, and so the index can point at the full rule for each」。另一条理由在 guide README 第 8 项：「The 23 names that redirect an agent mid-task」，以及 10「Redirect a drifting run」：「You rarely need more words. You need the right name」。也就是说，principle 的名字本身是用户中途纠偏时用的词汇（例如「apply prove it works」）。
- 实际写法：benny 的两个操作文件用「Apply pstack's `principle-…`」一句话点名引用，不复述规则内容（triage 和 repro 的 `Hard safety rules` 最后几条）。poteto-agent 写的是「Navigate to a leaf `principle-*` skill whenever you apply that principle.」
- 仍然写在调用方正文里、没抽成 principle 的规则（全部出自 benny）：
  - repro `Hard safety rules`：「No confirmed repro means no authored fix.」「The exact discriminating symptom must appear twice through real UI interaction.」「State inspection may confirm an observation. It must not inject or force the symptom.」这几条和 `principle-prove-it-works`、`principle-fix-root-causes` 的方向一致，但更具体，只在 benny 里有效。
  - triage §8：「Prefer no ticket over a guessed or duplicate ticket.」
  - repro §13：「A compile, unit test, code review, or plausible diff is not after evidence.」这几乎是 `prove-it-works` 的 README 一句话摘要（「not a proxy, self-report, or 'it compiles.'」）的领域特化版本。
  - 推断：判据是适用面。跨任务通用的写成 principle；绑定到 Slack 坐标、marker、UI 复现两次这类具体领域参数的留在调用方。调用方在点名 principle 的同时，把它在本领域的具体化写在正文里。

### 4.4 reference 与正文

- benny 的做法（原文）：
  - 接口契约放 reference：`control-adapter.md` 定义适配器必须提供什么，正文 §5 只列 7 项能力的名字，然后「Read `references/control-adapter.md`」。
  - 条件分支的整段子流程放 reference：`verify-existing-fix.md` 只在「an open pull request or merged commit plausibly fixes this report」时读（repro §3、§10）。
  - 给人复制去改的配置模板放 reference 或 templates：routing 和 feature-map 的 example 都要求「Copy this file outside …」。
- 推断：判据有两条。一是只在某个分支才需要（按需加载）；二是被多方消费（setup-benny §6 和 repro §5 都读 control-adapter.md）。主流程每次都要执行的内容留在正文。

### 4.5 脚本与文字

- 我负责的文件里没有脚本。benny 没带任何脚本，所有「操作」都靠 agent 读文字执行：复制 pack、合并 JSONC、校验 7 项 thread-safety 等，即便是机械步骤也写成文字（FOR_AGENTS「for the agent」第 1 到 7 步、setup-benny §1）。
- 推断：这和 `principle-build-the-lever`、`principle-encode-lessons-in-structure`（README principle 表：「Encode the rule as a lint, metadata flag, runtime check, or script instead of more text.」）的方向有张力，见第 5 节。guide 里提到的脚本只有 babysit 的「bundled watcher」（06「Babysit watches the PR with a bundled watcher」），位于 playbook 目录之外的 `poteto-mode/scripts/`（范围外，只看到目录存在）。

### 4.6 agent 定义与技能

- 原文判据有两条。一是需要全新上下文、不是作者本人：Comment Sicko（05「not from the agent that wrote them」）。二是需要保证 subagent 在开工前加载某个 mode：poteto-agent（README：「substituting `generalPurpose` skips that read and drifts」）。
- agent 文件本身尽量薄。poteto-agent 只指路；Comment Sicko 只装判断规则、边界和输出格式，执行和修复留给调用它的技能（`/no-comments`）。

### 4.7 benny 为什么没有 mode 或 playbook 层

- 原文：benny 的入口是 Cursor automation 的触发器和提示词，提示词只说「Read and follow `<path>`」。
- 推断：automation 是单一任务类型，入口固定，不需要 mode 做路由，也不需要按任务类型选 playbook。所以 benny 的「操作文件」同时承担 playbook（编号步骤顺序）和技能（每步做法）两层。它们放在 `skills/<name>/SKILL.md`、带技能 frontmatter，但不经过技能注册，按路径读取。这说明 pstack 的分层是为「一个入口路由到多种任务」服务的；单一入口的自动化被压成了一层。

---

## 5. 重复与例外

### 5.1 重复

1. 冻结 source 坐标：triage §1（7 步）和 repro §1（6 步 + 每次发帖前 4 步）几乎逐字相同；两个 prompt 模板和 FOR_AGENTS shared rules 各再写一遍「immutable」。
2. Slack 写禁令：triage `Hard safety rules`、repro `Hard safety rules`、`triage-automation-prompt.md`、`reproduce-automation-prompt.md`、FOR_AGENTS shared rules、setup-benny §8 第 6 项，共六处。禁止的动作名单 `SendSlackMessage`、`PostToSlack`、`chat.postMessage` 在前四处都逐字出现。
3. marker 契约：triage §9 的代码块、repro §2 的代码块、triage 模板、FOR_AGENTS、setup-benny §7、`configuration.example.yaml` 的 `verdict_markers`。
4. 「never post a root message」出现在以上每一个 benny 文件里。
5. pack 复制步骤：FOR_AGENTS「for the agent」第 1 到 6 步和 setup-benny §1 第 1 到 6 步内容重叠。setup-benny 用「If this file is already being read from the target destination, treat the copy as complete」处理重复执行。
6. 共享技能清单：FOR_AGENTS 写「`how`, `why`, `tdd`, `unslop`, and the principle skills used by benny」，setup-benny §1 列出具体 10 项。两处核对过是一致的：triage 和 repro 点名的 6 个 principle 正好就是 setup 列出的 6 个。
7. 控制适配器能力：repro §5 列 7 项、setup-benny §6 列 7 项、control-adapter.md 按 H3 分项写、control-adapter.md `Setup check` 9 步，共四处。
8. 「真实 UI 两次」：repro `Hard safety rules`、§7、§13，verify-existing-fix.md 的 baseline 和 patched 两节，control-adapter.md。
9. guide 重复 playbook 的行为细节：06 写了 Babysit 的阻塞处理顺序「conflicts, then review threads, then CI」、「Every known fix batches into one push」；Shipping 的「contiguous verified run from the bottom」；07 写了 Autopilot-full 的轮次规则。README 的 playbook 表也有一句话摘要。推断：guide 被当作面向人的解释，重复是有意为之，但行为一旦改动就要多处同步。
10. guide 内部：10 的 pitfalls 复述了 02（不要列举技能）、07（模糊的完成条件、duration）、02 和 07（worktree 隔离）、05 和 06（green build 不算证据）。
11. 模型规则的说明：README 第 249 到 251 行和 01「Pick your models」内容重叠（包括「0.15.3 之前的规则」这条迁移说明）。

### 5.2 pstack 自己违反分层的地方

1. benny 的操作文件把流程顺序和做法写在同一个技能文件里（15 个编号步骤、10 个编号步骤），没有 playbook 层。见 4.7：推断这是单入口自动化有意压扁的结果，原文没有说明理由。
2. `reproduce-and-fix-issues/references/verify-existing-fix.md` 是一个 reference，但装的是完整子流程（Qualify → baseline → patched → outcomes → cleanup）。按 pstack 主体的说法，这属于 playbook 性质的内容。
3. `control-adapter.md` 的 `Setup check` 是 9 步流程，放在契约文档里；setup-benny §6 又只写了能力清单，没有指向那 9 步（§6 原文是「Read `../reproduce-and-fix-issues/references/control-adapter.md` … Confirm that the named skill can: …」）。所以这 9 步是否会被执行，取决于 agent 读到那一节时是否自觉去做（推断）。
4. benny 用文字描述本可以脚本化的机械步骤，例如合并 JSONC、复制 pack、7 项 thread-safety 检查，和 `principle-encode-lessons-in-structure` 的主张不一致（推断）。
5. Comment Sicko 是 agent 定义，却调用技能（「I run `/how`, `/why`」）。它不只是规则的承载体，也是会发起调用的执行体。这并不违反分层，但说明 agent 定义可以作为调用源。
6. `typescript-best-practices`：guide 05 说「It loads whenever the agent touches a `.ts` or `.tsx` file」。范围外核对它的 frontmatter，同时有 `paths: ["**/*.ts", "**/*.tsx"]` 和 `disable-model-invocation: true`。`paths` 触发和 `disable-model-invocation` 在 Cursor 里怎么共存，这些文件里没有写（列入第 9 节）。
7. guide 04 的「设计投入阶梯」写在文档里，并声称「`/poteto-mode` already applies this ladder」。阶梯是否真的编码在 mode 或 playbook 里，我负责的文件里无法验证。
8. `setup-pstack` 是 pstack 里唯一没有 `disable-model-invocation: true` 的技能（范围外核对：第 2 到 4 行只有 `name` 和 `description`）。推断：它希望通过 description 里的「configure pstack models」「pstack budget」被模型自动触发。

---

## 6. 状态与重入

pstack 主体（从 guide 和 README 看）：

- todo 清单是运行时状态：playbook 步骤被逐字抄进 todo；跳过的步骤保留为 `skip: <reason>`（01「Run your first task」、02）。原文给的理由只有「so you can see what it chose not to do」。推断：还有防止漏步的作用，因为 02 的 pitfall 说手写的序列「reorders or drops steps」。
- 会话切换：sticky 靠 `reminder`（范围外核对），重新匹配靠用户说 `new task`（02）。
- 中断和接手：由 Session pickup 和 Pause safely 两个 playbook 处理（README 表格；03 写 Session pickup「treats the prior trail as authoritative … names the resume point, and verifies inherited claims against the original goal」）。`/recall` 是跨会话重建上下文的轻量版本（03）。
- 持久状态：`/show-me-your-work` 的 `decisions.tsv` 或 `.audit/<task-slug>.tsv`，每行记录 time、phase、decision、reason、evidence pointer、result，默认留在本地（07）。
- 长跑：`/loop` 按事件或 heartbeat 重查完成条件（07）；循环规则是「One change, one check, one log row, every iteration」，并且「the finish condition never quietly relaxes」。
- 模型配置：规则文件在新会话生效（01）；重跑 `/setup-pstack` 会保留和默认值不同的角色（01，README）。

benny：

- 坐标冻结：用不可变值防止重入时发错线程（triage §1、repro §1）。
- 幂等：triage §7「Always check whether this source permalink is already linked to a tracker issue or a prior triage reply. If so, do not post or create a duplicate.」
- 补偿：建了单但结论没发出去，就用适配器的 compensation action 撤销（triage §9，`require_compensation_action: true`）。
- 有界窗口：跟进窗口只看一次，「Do not extend the window more than once. A new report should start a new run.」（triage §10）；repro §9 的 rejection window 过后才进入修复。
- 预算：`budgets` 组写明各环节的分钟数（yaml），超时就停。
- 安装重入：setup-benny §1「If this file is already being read from the target destination, treat the copy as complete」；合并时保留目标端独有的文件，冲突时 review diff，归属不明就停下来问；§7 分首次创建和已有 automation 两条路径，「Do not create replacements or duplicates.」
- 失败即关闭：配置、适配器、feature map 缺失时一律停止（FOR_AGENTS shared rules，各操作文件开头）。

---

## 7. 额外问题

### 7.1 plugin.json 声明的交付面

只有 `skills`（`./skills/`）和 `agents`（`./agents/`）。`automations/benny/` 不在清单里，因此「not registered as slash skills」（README 第 255 行；setup-benny 开头「The plugin manifest exposes only pstack's normal skill root」）。Cursor rule 由 `/setup-pstack` 在运行时写到用户目录，不是清单声明的交付面。`docs/` 只是仓库文档。

### 7.2 agent 定义的格式与作用

格式：Markdown 加 YAML frontmatter（`name`、`description`，可选 `is_background`），正文是系统提示词。调用方式是 `subagent_type: "<name>"`。见 2.2、2.3、4.6。

### 7.3 guide 对分层设计理由的原文陈述

| 问题 | 原文 | 出处 |
|---|---|---|
| 为什么 mode 常驻 | 「Short works because the mode is sticky and the playbook holds the structure. Your words carry the intent, and the skill carries the rigor.」 | `02-poteto-mode.md`「Say the goal, not the ceremony」 |
| 为什么 playbook 抄进 todo | 「If `/poteto-mode` skips a step, the step stays in the list with `skip: <reason>`, so you can see what it chose not to do.」；「The playbook already sequences them, and a hand-written sequence usually reorders or drops steps the playbook would have kept.」 | `01-setup.md`「Run your first task」；`02-poteto-mode.md` Pitfall |
| 为什么 principle 单独成技能 | 「the standalone files are there so other skills can reference a principle by name, and so the index can point at the full rule for each.」；「You need the right name, and the principles page is the vocabulary.」 | `README.md`「principles」；`10-recipes-and-pitfalls.md`「Redirect a drifting run」 |
| 为什么技能都 `disable-model-invocation` | 我负责的文件里没有任何一句理由。README 第 30 行「the other skills are situational; the mode skill uses them for you as needed」，第 97 行「`/poteto-mode` runs most of these for you when a step needs them」。推断：调用权集中在 mode 和 playbook 手里，避免模型按 description 自行触发而打乱 playbook 的顺序；代价是 subagent 需要 poteto-agent 这个外壳来确保读到 mode | 见第 9 节 |
| 为什么没有 planning 技能 | 「i don't believe in planning. the best spec is code.」 | `README.md` |
| 为什么技能改动不能混在任务里 | 「A skill edit that ships tangled into feature work is invisible to review and impossible to evaluate.」 | `09-make-it-yours.md` Pitfall |
| 为什么技能要走 playbook 编写 | 「an unhelpful sentence becomes an instruction some future agent follows. Let the playbook hold that bar」 | `09-make-it-yours.md`「Author a focused skill」 |

### 7.4 benny 如何复用 pstack 又保持自己的技能

它是「另一个技能合集建在 pstack 之上」的实例，做法如下：

1. **共享技能靠项目级插件启用，不拷贝**：目标仓库的 `.cursor/settings.json` 写入 `"plugins": {"pstack": {"enabled": true}}`，而且只用于「shared dependencies such as `how`, `why`, `tdd`, `unslop`, and the required principle skills」（FOR_AGENTS shared rules）。验证时要求「a fresh agent rooted in the target repository」，并且「do not count skills loaded from the current session or a user-scoped install」（FOR_AGENTS，setup-benny §1）。
2. **自己的技能不注册、按路径读**：pack 整体复制到 `<target>/.cursor/automations/benny/`，automation 提示词写「read and follow `.cursor/automations/benny/skills/<x>/SKILL.md`」，而且「do not want plugin cache paths, copied excerpts, or slash-skill discovery」（FOR_AGENTS）。还明确禁止「add `.cursor/automations/benny/skills/` to a plugin manifest」。三个文件都带 `disable-model-invocation: true`，description 写「Use only from the configured Benny … automation」。
3. **引用 pstack 的方式**：用技能名调能力技能（「Use pstack's `how` skill」），用名字点名 principle（「Apply pstack's `principle-…`」）。不复述它们的内容。
4. **配置放在 pack 之外，避免被覆盖**：用户配置、feature map、routing map 放到 `.cursor/benny/` 或 `~/.config/benny/`（setup-benny §2）；「Do not edit the copied examples. Pack refreshes may update source-managed files after conflict review, but they must never touch the user-owned copies.」secret 放在 secret manager 或环境变量里（`optional_bot_token_env: "BENNY_SLACK_BOT_TOKEN"`）。刷新 pack 时保留目标端独有的文件，对 source-managed 的文件做 diff 合并（setup-benny §1 第 3 到 5 步）。
5. **可替换的外部依赖用契约表达**：tracker 是「an adapter, not a required vendor」（triage §6，列出 6 项必需操作）；控制适配器由 `control-adapter.md` 定义契约，由用户在 `control.skill_name` 里指定具体技能。benny 不绑定具体实现。
6. **和平台内置技能划清边界**：创建 automation 只走内置 `automate`，「Do not duplicate `automate`'s … work」「Never call a direct automation backend service」（setup-benny §7「Creation boundary」）。

---

## 8. 对下一轮归置 MMW 的直接启示（推断，供参考）

- pstack 的分层只在「一个入口路由到多种任务」时成立。benny 这种单入口自动化被压成了一层操作文件，只按名字引用共享技能和 principle。MMW 的夜间流水线里有固定入口的部分（例如 dispatch 的 night 流程），可能更接近 benny 的形态，不必为了套用 mode/playbook 而拆开。
- agent 定义只在两种情况下出现：需要独立上下文（Comment Sicko），或需要确保 subagent 先加载某个 mode（poteto-agent）。
- principle 被引用时只点名，领域特化的规则留在调用方正文里。

## 9. 未确定

- 为什么所有能力技能和 principle 都设 `disable-model-invocation: true`：我负责的文件里没有原文理由，上面是推断。`08-principles.md` 和 `poteto-mode/SKILL.md` 可能有说明，但不在本次范围内。
- `typescript-best-practices` 同时有 `paths` 和 `disable-model-invocation: true`，Cursor 实际会不会按 `paths` 自动加载：未确定。
- `reminder` 键的运行时语义（每轮注入还是其他机制）：只看到 frontmatter 值，Cursor 的实现没有看到。
- `is_background: true` 的确切含义（后台运行还是可以复用）：没有原文解释。
- guide 04 的「设计投入阶梯」、06 的 Babysit 顺序等细节是否和 playbook 原文一致：没有读 playbook，未核对。
- guide 引用的 `./images/*.jpg` 和 `assets/logo.png` 不在快照里，图片内容无法查看。
- `poteto-mode/scripts/` 里有什么脚本，以及它们怎么被 playbook 调用：不在本次范围，未读。
