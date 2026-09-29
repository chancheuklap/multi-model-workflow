# L5-pstack-principles：pstack 的 23 个 principle 技能怎么写、怎么连线

范围：`docs/research/code-landing-refs/pstack/skills/principle-*/SKILL.md`（23 个，全部逐行读完，合计 513 行）和 `docs/research/code-landing-refs/pstack/docs/guide/08-principles.md`（71 行，读完）。以下路径都相对 `docs/research/code-landing-refs/pstack/`。

为回答「谁引用原则」，还做了两件事：(a) 在全 pstack 所有 `.md` 里按 slug（如 `prove-it-works`）和标题（如 `Prove It Works`，不分大小写）grep 每条原则；(b) 完整读了 `skills/poteto-mode/SKILL.md`（143 行，原则索引所在处）、`agents/poteto-agent.md`、`.cursor-plugin/plugin.json`、`README.md` 第 185–225 行、`skills/poteto-mode/playbooks/authoring-a-skill.md`、`skills/architect/references/runner-prompt.md` 前 30 行、`skills/interrogate/references/rubric.md` 第 15–45 行、`skills/typescript-best-practices/SKILL.md` 前 30 行、`docs/guide/02-poteto-mode.md` 前 40 行。其余调用方文件只读了 grep 命中的那一行，涉及这些文件整体结构的结论标为推断。脚本没有运行。

标注约定：「原文」= 文件里写明，附路径和标识；「推断」= 我的归纳。

---

## 0. 结论摘要

1. **原则 = 一条「何时适用 + 规则 + 理由」的短技能，不被调用，只被按名字读取和引用。** 23 个文件的 frontmatter 完全相同：只有 `name`、`description`、`disable-model-invocation: true` 三个键，没有 `mode`、`reminder`、`icon`、`paths`。每个 `description` 都以 `Apply` 开头（`Apply when …` / `Apply to …` / `Apply after …` / `Apply before …` / `Apply during …`），第一句是触发条件，其后是祈使句写的规则摘要。正文 16–34 行。
2. **加载路径是两级的**（原文）：`skills/poteto-mode/SKILL.md`「## Principles」把 23 条的触发条件和一句规则内联成索引，agent 每次任务开始读这个索引；真正应用某条时才去读叶文件全文（"Read the leaf skill in full for any principle you apply."），并在回复里写出它改变了哪个决定（「## Non-negotiables」："name each principle that shaped a decision and the specific choice it changed. Cite only principles whose leaf SKILL.md you read this session."）。`docs/guide/08-principles.md` 对人说的是同一件事："You don't invoke principles. You use their names to steer."
3. **原则单独成文件的理由，原文只有一句**：`README.md`「## principles」："the standalone files are there so other skills can reference a principle by name, and so the index can point at the full rule for each." 另一个作用是给人当「转向词汇」（`08-principles.md`「Steering in practice」）。
4. **「被多处引用」不是成为原则的条件。** 除去 `poteto-mode` 索引、`README.md` 表格和 `docs/guide/` 以外，`attack-the-premise`、`experience-first`、`test-behavior-not-implementation` 三条的功能性引用是 0；`make-operations-idempotent`、`migrate-callers-then-delete-legacy-apis`、`outcome-oriented-execution` 各 1 次。引用最多的是 `prove-it-works`（12）、`encode-lessons-in-structure`（10）、`sequence-verifiable-units`（10）。推断：够格成为原则的实际条件是「作者希望每个任务开始时都能看到的、跨 playbook 的一条工程判断」，而不是「已经被复用」。
5. **格式并不统一。** 16/23 有 `**Why:**`；只有 1 条（`build-the-lever`）有 `**Balance:**`；16/23 有带标签的做法小节，标签有 `**Pattern:**`、`**The pattern:**`、`**The patterns:**`、`**Rule:**`、`**Core rule:**`、`**The rule.**`、`**Reach for structures like these:**` 七种写法，其余用无标签列表或粗体段首句；2 条（`experience-first`、`redesign-from-first-principles`）没有任何小节标签。原则之间的交叉引用有三种写法并存。
6. **分层并不干净。** 有 4 条原则内含有序步骤（`attack-the-premise`、`encode-lessons-in-structure`、`separate-before-serializing-shared-state`、`redesign-from-first-principles`），有几条含语言或工具细节（`test-behavior-not-implementation` 列 Jest 断言名，`type-system-discipline` 列各语言惯用法）。多条原则之间内容重叠，pstack 部分用「Distinct from …」句子区分，部分没有处理。同一条原则的一句话摘要在 4 处重复（`description`、`poteto-mode` 索引条目、`README.md` 表格、`08-principles.md` 列表），措辞不完全一致。
7. **没有任何脚本检查原则引用。** grep `*.mjs/*.ts/*.sh/*.js/*.py` 里 `principle` 无命中；「引用了就要改变一个决定」只靠 `poteto-mode` 正文和 `08-principles.md` 的文字约束。

---

## 1. 组件清单

| 文件 | 类型 | 管什么（一句话） |
|---|---|---|
| `skills/principle-laziness-protocol/SKILL.md` | 原则（core） | 偏向删除和最小改动，拒绝多余层级与信号穿透。 |
| `skills/principle-foundational-thinking/SKILL.md` | 原则（core） | 先定数据结构与脚手架，再写逻辑；结构决定保留选择余地。 |
| `skills/principle-redesign-from-first-principles/SKILL.md` | 原则（core） | 新需求按「从第一天就存在」重做设计，而不是外挂。 |
| `skills/principle-attack-the-premise/SKILL.md` | 原则（core） | 两次以上同前提的修复失败后，先做 census 再质疑前提。 |
| `skills/principle-subtract-before-you-add/SKILL.md` | 原则（core） | 先删死代码、冗余校验、空壳引用，再在更简单的基础上加。 |
| `skills/principle-minimize-reader-load/SKILL.md` | 原则（core） | 用「要追的层数」和「要记住的状态」两轴衡量可维护性。 |
| `skills/principle-outcome-oriented-execution/SKILL.md` | 原则（core） | 计划内重写时收敛到目标架构，不为中间态写兼容代码。 |
| `skills/principle-experience-first/SKILL.md` | 原则（core） | 实现便利与使用者体验冲突时选体验；少而精。 |
| `skills/principle-exhaust-the-design-space/SKILL.md` | 原则（core） | 无先例的设计先做 2–3 个竞争原型再定。 |
| `skills/principle-build-the-lever/SKILL.md` | 原则（core） | 非平凡工作先造能重跑的工具（codemod、脚本、生成器、委派技能）。 |
| `skills/principle-model-the-domain/SKILL.md` | 原则（architecture） | 用贴合领域的结构（状态机、类型模型、表）替代分散的条件分支。 |
| `skills/principle-boundary-discipline/SKILL.md` | 原则（architecture） | 校验集中在系统边界，内部信任类型，业务逻辑是纯函数。 |
| `skills/principle-type-system-discipline/SKILL.md` | 原则（architecture） | 让非法状态无法表示、给语义原始类型加品牌、穷举变体。 |
| `skills/principle-make-operations-idempotent/SKILL.md` | 原则（architecture） | 操作在崩溃、重启、重试后收敛到同一终态。 |
| `skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md` | 原则（architecture） | 新内部 API 上线时同一波迁移调用方并删旧 API。 |
| `skills/principle-separate-before-serializing-shared-state/SKILL.md` | 原则（architecture） | 并发写同一对象时先消除共享，真需要才结构化串行。 |
| `skills/principle-prove-it-works/SKILL.md` | 原则（verification） | 用真实产物验证，不用代理指标或自述。 |
| `skills/principle-fix-root-causes/SKILL.md` | 原则（verification） | 调试时先复现、追问 why 到根因，不加掩盖症状的守卫。 |
| `skills/principle-sequence-verifiable-units/SKILL.md` | 原则（verification） | 工作拆成每步可检查的小单元，并按能自证的顺序交付提交。 |
| `skills/principle-test-behavior-not-implementation/SKILL.md` | 原则（verification） | 测试以用户方式调用并断言字面期望值；删掉永不失败的测试。 |
| `skills/principle-guard-the-context-window/SKILL.md` | 原则（delegation） | 大块读取交给 subagent，主上下文只留摘要。 |
| `skills/principle-never-block-on-the-human/SKILL.md` | 原则（delegation） | 可逆工作不停下问人，做完再呈现；不可逆动作才确认。 |
| `skills/principle-encode-lessons-in-structure/SKILL.md` | 原则（meta） | 同一条指示第二次出现时改写成 lint、检查、脚本等机制。 |
| `docs/guide/08-principles.md` | 文档（给人看的用户指南） | 教使用者用原则名字转向 agent，并按五组列出 23 条。 |

分组来源（原文）：`skills/poteto-mode/SKILL.md`「## Principles」下的粗体小标题 `**Core**`、`**Architecture**`、`**Verification**`、`**Delegation**`、`**Meta**`；`README.md` 表格的 `group` 列；`08-principles.md`「The 23, briefly」。三处的分组和顺序一致。

`08-principles.md` 不是 agent 读取的组件（推断，依据：`.cursor-plugin/plugin.json` 只声明 `"skills": "./skills/"` 和 `"agents": "./agents/"`，`docs/` 不在插件清单里）。

---

## 2. 解剖

### 2.1 frontmatter（23 个完全同构）

原文逐个核对（每个文件第 1–5 行）：

```
---
name: principle-<slug>
description: "Apply <when/to/after/before/during> <trigger>. <imperative rule summary>."
disable-model-invocation: true
---
```

- `name`：等于目录名，统一 `principle-` 前缀。
- `description`：双引号字符串。23/23 以 `Apply` 开头。第一句是触发条件，写的是**情境**而非任务类型，例如 `principle-attack-the-premise`："Apply when two or more fixes that share one premise have failed the same gate."；`principle-never-block-on-the-human`："Apply when tempted to ask 'should I do X?' on reversible work."；`principle-build-the-lever`："Apply to any non-trivial work, not just bulk work"。后面一到两句是祈使句规则摘要，例如 `principle-boundary-discipline`："Concentrate guards at system boundaries (CLI, config, network, external APIs); trust internal types and keep business logic in pure functions."
- `disable-model-invocation: true`：23/23。但这不是原则专有的：pstack `skills/` 下 47 个技能（含 23 个原则）里只有 `skills/setup-pstack/SKILL.md` 没有这个键（grep 结果）。推断：这是 pstack 全局默认，含义是「不让模型按 description 自动触发」，原则的读取靠 `poteto-mode` 索引和调用方按名字指向。pstack 文件里没有解释这个键的语义（见「未确定」）。
- 没有 `mode`、`reminder`、`icon`、`color`、`paths`。对照：`skills/poteto-mode/SKILL.md` 有 `mode: true`、`icon: crown`、`color: yellow`、`reminder: New task? Playbook match or rigor needed -> apply /poteto-mode. …`；`skills/typescript-best-practices/SKILL.md` 有 `paths: ["**/*.ts", "**/*.tsx"]`。原则不承担路由和自动触发职责。

### 2.2 正文的通用骨架（归纳，推断）

`# <Title Case 名称>` → 一到三句规则陈述（祈使句或定义句）→ `**Why:**` 一到三句理由 → `**Pattern:**` 类小节，列 3–8 条做法（粗体引导语 + 一句） → 可选的判别小节（`**The test:**` / `**The tests:**` / `**Stop:**` / `**Boundaries:**` / `**Balance:**` / `**When it applies:**` / `**When it doesn't:**` / `**Guardrails:**` / `**Anti-patterns:**` / `**Keep**`） → 可选的一句「与某原则的区别/互补」。

小节用粗体段首标签，不用 `##` 标题；唯一例外是 `principle-prove-it-works` 的 `## Script the check when you can`。

语气（原文可见）：短陈述句、祈使句、第二人称省略（"Reproduce first"、"Do not add guards"）；判别问句用引号（`principle-boundary-discipline`「The tests」："Is this data crossing a system boundary right now?"）；多数不含命令、参数和输出格式。

### 2.3 逐个解剖表

「内容类型」列用：规则 = 陈述要做什么；做法 = 具体手法；理由 = Why；判别 = 触发/不触发/自检问句；步骤 = 有先后顺序的动作；细节 = 语言、工具或具体机制。

| 原则 | 行数 | 正文小节（按出现顺序） | Why | 内容类型 | 出链（引用谁） |
|---|---|---|---|---|---|
| attack-the-premise | 23 | 规则句 → `**Why:**` → `**Pattern:**`（4 条，有先后）→ `**Stop:**`（2 条闸门）→ 区别句 | 有 | 规则、步骤、判别 | build-the-lever、fix-root-causes、laziness-protocol、redesign-from-first-principles（相对链接） |
| boundary-discipline | 34 | 规则段 → `**Why:**` → `**The pattern:**`（3）→ `**Applications:**`（两组共 8 条）→ `**The tests:**`（2 问） | 有 | 规则、做法、判别 | 无 |
| build-the-lever | 23 | 规则句 → `**Why:**` → `**Pattern:**`（默认句 + 6 条）→ `**Balance:**` → 区别句 | 有 | 规则、做法、判别、少量编排做法 | laziness-protocol、encode-lessons-in-structure、prove-it-works（相对链接） |
| encode-lessons-in-structure | 31 | 规则段 → `**Why:**` → `**Pattern:**`（编号 1–3）→ `**Pick the strongest mechanism.**` → `**Corollary:**` → `**Feedback loop:**`（3）→ `**Anti-patterns:**`（3） | 有 | 规则、步骤、做法、判别 | 无链接；文中出现 "brain note"、"skill or lint rule"、"principle" 三个落点 |
| exhaust-the-design-space | 21 | 规则段 → `**The rule.**` → `**When it applies:**`（3）→ `**When it doesn't:**`（3） | 无独立 Why，理由在首段："Building the wrong thing costs more than exploring three options." | 规则、判别 | 无 |
| experience-first | 19 | 规则句 → 5 条无标签列表 → 「谁是用户」段 → 与 foundational-thinking 的分工句 | 无 | 规则、做法 | foundational-thinking（纯文本 "Foundational thinking governs the *sequence* of work."，无链接） |
| fix-root-causes | 23 | 规则句 → `**Why:**` → `**Pattern:**`（6）→ `**Restart bugs: suspect state before code**` 小节 | 有 | 规则、做法、具体场景细节 | 无 |
| foundational-thinking | 21 | `**Structural decisions**`/`**Code-level decisions**` 定义句 → `**Data structures first.**` 段 → code level 段 → `**Concurrency corollary.**` → `**Scaffold first.**` → 两句收尾 | 无独立 Why | 规则、做法、顺序要求 | 无 |
| guard-the-context-window | 16 | 规则句 → `**Why:**` → `**Pattern:**`（3） | 有 | 规则、做法 | 无 |
| laziness-protocol | 18 | 规则句 → 6 条粗体引导列表 → `**The test:**` | 无 | 规则、做法、判别 | 无 |
| make-operations-idempotent | 24 | 规则段（含两问）→ `**Why:**` → `**The pattern:**`（4）→ `**The test:**`（编号 3 问）→ 结论句 | 有 | 规则、做法、判别、机制细节（"PID-based stale lock detection"） | 无 |
| migrate-callers-then-delete-legacy-apis | 22 | 规则句 → `**Rule:**`（4）→ `**When this applies:**`（3）→ 理由句收尾 | 无独立 Why，末句是理由 | 规则、判别 | 无 |
| minimize-reader-load | 23 | 定义段（两轴，编号 1–2）→ `**Why:**` → `**The pattern:**`（6）→ `**The test:**` | 有 | 规则、做法、判别 | guard-the-context-window（相对链接） |
| model-the-domain | 26 | 规则句 → `**Why:**` → `**Reach for structures like these:**`（8）→ 「不要强加抽象」段 → 「跳过的信号」段 | 有 | 规则、做法、判别 | 无 |
| never-block-on-the-human | 20 | 规则段 → `**Why:**` → `**Pattern:**`（2）→ `**Boundaries:**`（3） | 有 | 规则、判别 | 无 |
| outcome-oriented-execution | 21 | 规则句 → `**Why:**` → `**Core rule:**`（2）→ `**Guardrails:**`（4） | 有 | 规则、判别 | 无 |
| prove-it-works | 22 | 规则句 → `**Why:**` → 3 条无标签列表 → `## Script the check when you can` 两段 | 有 | 规则、做法、交付物策略 | show-me-your-work（能力技能，粗体名："the **show-me-your-work** skill"） |
| redesign-from-first-principles | 16 | 规则句 → 4 条列表（有先后）→ 定位句 | 无 | 规则、步骤 | 无 |
| separate-before-serializing-shared-state | 16 | 规则段 → `**Why:**` → `**Pattern:**`（编号 1–3） | 有 | 规则、步骤、判别、例子（`state.json`） | 无 |
| sequence-verifiable-units | 17 | 规则句 → `**Why:**` → `**Execution.**` 段 → `**Delivery.**` 段 → 互补句 | 有 | 规则、做法 | prove-it-works、build-the-lever（粗体名："the **prove-it-works** principle skill"） |
| subtract-before-you-add | 21 | 规则句 → `**Why:**` → 「持续投入」段 → `**The pattern:**`（6） | 有 | 规则、做法 | 无 |
| test-behavior-not-implementation | 25 | 定义段 → 自检段 → `**Why:**` → `**Five shapes …:**`（5，含 Jest 断言名）→ `**The fix:**` → `**Keep**` | 有 | 规则、判别、工具细节、例子代码 | 无 |
| type-system-discipline | 31 | 规则段 → 适用语言段 → `**The patterns:**`（8，含多语言惯用法）→ `**The tests:**`（6 问） | 无独立 Why，理由写在首段 | 规则、做法、判别、语言细节 | typescript-best-practices（能力技能，反引号名）、boundary-discipline、encode-lessons-in-structure（粗体名） |

### 2.4 值得单独记下的写法

- **Why 的写法**：一到三句，陈述后果或成本，不讲故事。例：`principle-attack-the-premise`「Why」："Each failure under a shared premise is evidence about the premise."；`principle-never-block-on-the-human`「Why」："Every permission pause stalls the pipeline and makes the human the bottleneck."
- **判别小节是原则的主要「可执行」部分**：自检问句（`principle-minimize-reader-load`「The test」："Can a new reader answer "where does X come from?" and "what can change X?" in under 30 seconds?"）、否定性检验（`principle-test-behavior-not-implementation`："ask whether it would still pass if every function it imports returned `undefined`"）、应用证据（`principle-build-the-lever`「Pattern」："Applying this principle produces a file. If you cited it and there is no codemod, script, generator, or delegate skill in the diff, you didn't apply it."）。后一类把「引用即须改变决定」落实到可检查的产物上。
- **区别句**：3 条原则末尾显式与近邻划界。`principle-attack-the-premise`："This principle is distinct from [Redesign from First Principles] … It questions a fact the current design assumes."；`principle-build-the-lever`："Distinct from [Encode Lessons in Structure], which makes a recurring instruction a durable guardrail."；`principle-experience-first`："Foundational thinking governs the *sequence* of work. This principle governs the *target*." 另有 2 条写互补关系：`principle-sequence-verifiable-units`（"The sequencing complement to the **prove-it-works** principle skill …"）、`principle-minimize-reader-load`（"This is the human analog of [Guard the Context Window]"）。
- **`docs/guide/08-principles.md` 的解剖**：71 行。`# Steer with principle names` → 两段引言（说明 `/poteto-mode` 读索引、应用并在回复里点名）→ `## Steering in practice`（三个 ` ```text ` 例句，每句=「原则名 + 一句具体要求」，如 "apply prove it works. run the real import flow and show me the written records."）→ 一段强调「引用必须对应决定」（"A principle citation with no decision behind it is the tell that it name-dropped instead of applying."）→ `## The 23, briefly`（五组，每组一句组义 + 每条一句第三人称摘要，相对链接 `../../skills/principle-*/SKILL.md`）→ "Don't memorize the list." → `Next:` 链接。读者是人，语气是教程第二人称。

---

## 3. 调用与连线

### 3.1 原则怎么被读到（原文）

| 路径 | 机制 | 出处 |
|---|---|---|
| `/poteto-mode` 启动 | 读 `poteto-mode` 全文，其中「## Principles」是 23 条的内联索引；应用某条时读叶文件全文 | `skills/poteto-mode/SKILL.md`「## Non-negotiables」「## Principles」："Read the leaf skill in full for any principle you apply. Each entry names when it applies." |
| `subagent_type: "poteto-agent"` | agent 定义要求先读 `poteto-mode` 全文含索引，应用时导航到叶技能 | `agents/poteto-agent.md`："Navigate to a leaf `principle-*` skill whenever you apply that principle." |
| `figure-it-out` 技能 | todolist 第一项是读 `poteto-mode` 的 Principles 小节 | `skills/figure-it-out/SKILL.md` 第 13 行："Open a todolist whose first item is to read the Principles section of the **poteto-mode** skill." |
| playbook、能力技能、reference、其他原则 | 在步骤或规则句末尾用括号或 `per` 点名 | 见 3.3 |
| 人 | 在对话里说原则名 | `docs/guide/08-principles.md`「Steering in practice」 |
| 外部自动化 benny | 要求 pstack 的 6 个原则技能在目标仓库以项目作用域可解析 | `automations/benny/skills/setup-benny/SKILL.md` 第 54–59 行 |

没有自动触发、没有斜杠命令入口、没有 `subagent_type`。原则**不调用**任何脚本、playbook 或 subagent。

### 3.2 引用写法（四种并存，原文）

1. 粗体名 + "principle skill"：最常见，如 `playbooks/bug-fix.md` 第 12 行 "This is the canonical **sequence-verifiable-units** principle skill"。
2. 带前缀的粗体 slug：如 `playbooks/refactoring.md` 第 10 行 "(**principle-subtract-before-you-add**)"；`poteto-mode` 索引条目格式为 `**Title** (**principle-slug**). <trigger>. <rule>.`
3. 相对 Markdown 链接：只在原则之间和 `docs/guide/` 里用，如 `principle-attack-the-premise` 第 15 行 `[Build the Lever](../principle-build-the-lever/SKILL.md)`。
4. 纯文本名：如 `skills/arena/SKILL.md` 第 49 行 "per the Laziness Protocol"；`principle-experience-first` 第 19 行 "Foundational thinking"。

`playbooks/authoring-a-skill.md` 给出引用方针："Delegate to other skills by path. Don't restate."

### 3.3 每条原则的引用计数和位置（全 pstack grep）

「功能性引用」= 除 `poteto-mode` 索引（每条 1 次，第 43–77 行）、`README.md` 表格（每条 1 次，第 203–225 行）、`docs/guide/*` 之外的引用行。行号为文件内行号。

| 原则 | 功能性引用 | 位置 |
|---|---|---|
| prove-it-works | 12 | playbooks：multi-phase-plan:13、session-pickup:9、worktree-cleanup:6、autopilot-full:6、hillclimb:5、refactoring:12；技能：figure-it-out:19、arena:65；原则：build-the-lever:23、sequence-verifiable-units:17；benny：reproduce-and-fix-issues:32、setup-benny:59。另有文档 guide/06-verify-and-ship.md:3、guide/10-recipes-and-pitfalls.md:64、08 的例句:18 |
| encode-lessons-in-structure | 10 | playbooks：multi-phase-plan:10、authoring-a-skill:10、worktree-cleanup:5、orchestrate:25；技能：figure-it-out:51、reflect:47、show-me-your-work:51；reference：architect/references/runner-prompt.md:14；原则：build-the-lever:23、type-system-discipline:21 |
| sequence-verifiable-units | 10 | playbooks：bug-fix:12、multi-phase-plan:8、autonomous-run:8、hillclimb:16、feature:15、perf-issue:17、refactoring:14；技能：figure-it-out:39；benny：reproduce-and-fix-issues:32、setup-benny:57 |
| guard-the-context-window | 9 | playbooks：trace-forensics:7、multi-phase-plan:7、session-pickup:5、worktree-cleanup:7、hillclimb:12、runtime-forensics:6；原则：minimize-reader-load:13；benny：reproduce-and-fix-issues:31、setup-benny:56 |
| laziness-protocol | 9 | playbooks：prototype:5、hillclimb:17、feature:12、refactoring:10；技能：figure-it-out:30、arena:49；reference：runner-prompt.md:18；原则：build-the-lever:21、attack-the-premise:17 |
| separate-before-serializing-shared-state | 9 | playbooks：hillclimb:12、orchestrate:17、feature:10、visual-parity:7；技能：figure-it-out:31、arena:29；reference：runner-prompt.md:12；benny：setup-benny:54、triage-issue-reports:27。另有 08 例句:24 |
| boundary-discipline | 7 | 技能：typescript-best-practices:25；reference：typescript-best-practices/references/patterns.md:3、:261，architect/references/rationale-template.md:15，runner-prompt.md:15，interrogate/references/rubric.md:36（只复述规则，未点名为技能）；原则：type-system-discipline:18 |
| redesign-from-first-principles | 6 | playbooks：refactoring:9；技能：architect:61、architect:77、arena:57、no-comments:22；原则：attack-the-premise:23 |
| fix-root-causes | 5 | 技能：architect:61、no-comments:22；原则：attack-the-premise:16；benny：reproduce-and-fix-issues:32、setup-benny:58 |
| foundational-thinking | 4 | playbooks：refactoring:9；技能：figure-it-out:27、architect:49；原则：experience-first:19（纯文本） |
| build-the-lever | 4 | playbooks：hillclimb:8、worktree-cleanup:5；原则：attack-the-premise:15、sequence-verifiable-units:17 |
| minimize-reader-load | 4 | playbooks：refactoring:13；reference：runner-prompt.md:18；benny：setup-benny:55、triage-issue-reports:28 |
| model-the-domain | 3 | `poteto-mode`「Non-negotiables」第 21 行（索引之外的触发条目）；playbooks：feature:12、refactoring:8 |
| exhaust-the-design-space | 2 | playbooks：prototype:10；技能：architect:35 |
| never-block-on-the-human | 2 | playbooks：multi-phase-plan:6；技能：figure-it-out:23 |
| subtract-before-you-add | 2 | playbooks：refactoring:10；技能：architect:78。另有 08 例句:12 |
| type-system-discipline | 2 | 技能：typescript-best-practices:10；reference：patterns.md:3。另有 README.md:128 |
| make-operations-idempotent | 1 | reference：runner-prompt.md:17 |
| migrate-callers-then-delete-legacy-apis | 1 | playbooks：refactoring:11 |
| outcome-oriented-execution | 1 | 技能：architect:49 |
| attack-the-premise | 0 | 只有索引、README、guide |
| experience-first | 0 | 只有索引、README、guide |
| test-behavior-not-implementation | 0 | 只有索引、README、guide |

按引用方类别合计（推断归纳）：playbook 最多地引用 verification 和 delegation 两组（`sequence-verifiable-units` 7 个 playbook、`guard-the-context-window` 6 个、`prove-it-works` 6 个）；architecture 组主要被 `architect` 技能及其 reference 引用；`playbooks/refactoring.md` 一个文件引用了 9 条原则，是最密集的调用方。

---

## 4. 边界判据

### 4.1 原则 vs playbook

- 原文：`skills/poteto-mode/SKILL.md`「## Playbooks」："Open a todolist whose first items are the matched playbook's steps, copied in verbatim … A step you choose not to do stays in the list with a one-line `skip: <reason>`. Match the task to a playbook below"。playbook 按**整个任务**匹配，步骤被逐字抄进 todolist，可以跳步但要写理由。
- 原文：原则按**情境**触发（每个 `description` 的 "Apply when …"），`poteto-mode` 索引说 "Each entry names when it applies."；`08-principles.md`："applies the ones the task triggers"。原则从不进 todolist。
- 推断：因此判据是「管一个完整任务的执行顺序 → playbook；管任务中某类决定的取舍 → 原则」。原则里即使有步骤（见 5.2），也是围绕一个决定的 2–4 步，不构成一个任务的主线，所以没有被拆成 playbook。
- 反向：playbook 里不重写原则内容，只在步骤末尾括号点名，例如 `playbooks/refactoring.md` 第 10 行 "Subtract before you add. Delete dead code, … (**principle-subtract-before-you-add**)"。但 playbook 会**限定**原则：`playbooks/prototype.md` 第 5 行 "The one playbook where the Laziness Protocol's "smallest change" and the verification bar invert."；`playbooks/feature.md` 第 12 行 "Mandatory: no skip-with-reason escape, and Laziness Protocol does not override it"。能力技能也会：`skills/no-comments/SKILL.md` 第 22 行 "The **principle-fix-root-causes** and **principle-redesign-from-first-principles** skills guide intent only. Neither authorizes widening the fence"。即「原则给方向，调用方决定这次的适用范围」。

### 4.2 原则 vs 能力技能

- 推断：能力技能有输入、产出和工具（如 `typescript-best-practices` 的规则表、`show-me-your-work` 的 `decisions.tsv`），原则没有产出格式、没有命令。原则指向能力技能时是「向下落地」：`principle-type-system-discipline`："Applies to any typed language. Skills like `typescript-best-practices` ground it in specific syntax."；反过来 `skills/typescript-best-practices/SKILL.md` 第 10 行 "Apply the **type-system-discipline** principle skill first."。这对边界写明了「原则语言无关，技能绑定具体语法」。
- 但 `principle-type-system-discipline` 本身仍列了 Rust、Swift、Kotlin、Haskell、TypeScript 的惯用法，没有完全守住这条线（见 5.2）。

### 4.3 原则 vs 调用方里的一段规则

- 原文唯一的判据来自 `principle-encode-lessons-in-structure`「Feedback loop」："Route to the right layer. One-off -> brain note. Recurring fix -> skill or lint rule. Systemic issue -> principle."
- 原文的收益说明：`README.md` 第 196 行（按名字引用 + 索引指向全文）；`08-principles.md` 第 5 行（"one phrase redirects the work more precisely than a paragraph of instructions"）。
- 实际情况（推断）：「systemic」与「被 ≥2 处引用」不一致——6 条原则功能性引用 ≤1（3.3）。这 6 条的共同点是：都出现在 `poteto-mode` 索引里，因而每次任务开始都被看到。所以 pstack 的实际标准更接近「作者希望每个任务都考虑的跨任务判断」，复用次数不是前提。
- 仍写在调用方正文、没抽成原则的规则（原文可见的例子）：
  - `skills/poteto-mode/SKILL.md`「## Autonomy」："**Always pause** for irreversible writes: force-push to shared branches, deploys, data deletion, customer messages." 与 `principle-never-block-on-the-human`「Boundaries」重叠，但 Autonomy 带了具体动作清单和 "Session overrides"，没有引用该原则。
  - `skills/poteto-mode/SKILL.md`「## Writing the reply」："Every claim carries its evidence or its label in the same sentence. Measured, inferred, or guess." 与 `principle-prove-it-works` 相近，未引用。
  - `skills/architect/references/runner-prompt.md` 第 10、11、13、16 行："Caller's usage first."、"Data structures first."、"Interface depth."、"Single source of truth per invariant. Derive instead of sync."——前两条与 `principle-foundational-thinking` 重叠但未点名，后两条与 `principle-minimize-reader-load`「Demand interface compression」「Derive instead of sync」重叠但未点名。
  - `skills/interrogate/references/rubric.md`「## Root Causes vs. Symptoms」「## Structural Integrity」：复述了 fix-root-causes、encode-lessons-in-structure（"Instructions where structure would be better"）、boundary-discipline、redesign-from-first-principles（"Bolted-on vs. integrated"）、migrate-callers-then-delete-legacy-apis（"Legacy dual-paths"）、separate-before-serializing-shared-state（第 15 行 Concurrency），全部没有点名原则。推断：rubric 是给审查模型的评分表，作者选择自包含而不是指向原则。
  - `skills/tdd/SKILL.md` 第 17 行："The test should encode intended behavior, not mirror the current implementation." 与 `principle-test-behavior-not-implementation` 同义，未引用（只读了该行）。

### 4.4 reference vs 正文、脚本 vs 文字（原则里写明的判据）

- 内联还是拆 reference：`principle-guard-the-context-window`「Pattern」："Keep frequently used content inline. Templates and references used on every invocation belong in the skill file, not in separate files that cost a read each time." 以及 `principle-subtract-before-you-add`："When a reference has no novel content, delete it rather than leaving a stub"。原则本身都是单文件、无 reference，符合前一条（推断：原则短到每次读都整读）。
- 脚本还是文字：`principle-encode-lessons-in-structure`「Pattern」第 1–3 步："Ask: can this be a lint rule, a metadata flag, a runtime check, or a script? … If yes, encode it. Delete the instruction … If no (requires judgment), make the instruction more prominent and add an example of the failure mode"；「Pick the strongest mechanism」给出强弱次序："an unrepresentable state that cannot compile, then a lint or banned API that fails CI, then a canonical helper, then a runtime check"。`principle-build-the-lever`「Balance」："The bar is triviality, not repetition."；`principle-prove-it-works`「Script the check when you can」："The strongest proof is a deterministic script that re-runs the same comparison, not a one-time eyeball."
- 推断：pstack 自己没有把「引用原则须改变决定」编码成脚本（没有任何脚本提到 principle），这条仍停在文字层，与 encode-lessons-in-structure 的要求不一致；`playbooks/eval.md` 第 9 行则主张从代码形状而非自述判断是否遵循（"grade chain-following from code shape, not self-report"）。

---

## 5. 重复与例外

### 5.1 摘要的四处重复

同一条原则的一句话在 `description`、`poteto-mode` 索引条目、`README.md` 表格 `rule` 列、`08-principles.md` 列表里各写一次，措辞各不相同。`README.md` 表格还不一致：有的条目去掉了触发句（如 laziness-protocol 只剩 "Bias toward deletion …"），有的保留完整 description（foundational-thinking、attack-the-premise、outcome-oriented-execution、build-the-lever、prove-it-works、sequence-verifiable-units、test-behavior-not-implementation 七条以 "Apply …" 开头）。标题大小写也不一致：H1 `# Redesign From First Principles` vs 索引和指南 "Redesign from First Principles"；H1 `# Sequence work into verifiable units` vs "Sequence Work into Verifiable Units"。

### 5.2 原则内部的分层例外（原则里写了步骤、流程或细节）

| 原则 | 例外 | 原文 |
|---|---|---|
| attack-the-premise | 有序步骤 + 前置闸门 | 「Stop」："Do not start the next fix before the premise is written down and the census exists." |
| redesign-from-first-principles | 4 步顺序 | "Read all affected files … Ask … Propagate … Think about the whole redesign, then deliver it incrementally" |
| encode-lessons-in-structure | 编号步骤 + 反馈回路流程 | 「Pattern」1–3；「Feedback loop」Capture → Route → Close |
| separate-before-serializing-shared-state | 编号步骤 | 「Pattern」1. Identify → 2. Default: eliminate → 3. Only when … serialize |
| fix-root-causes | 顺序 + 特定场景 | "Reproduce first"；「Restart bugs: suspect state before code」 |
| build-the-lever | 编排做法（委派技能的内容与写权限） | "write the lever as a skill they all read: the recipe, the verification contract, and the do-not-touch fences in one artifact. Keep it outside the delegates' write scope" |
| prove-it-works | 交付物策略 + 指向能力技能 | "Commit it only for large or complex work where the trail has to be auditable later … (the **show-me-your-work** skill)." |
| test-behavior-not-implementation | 工具细节（Jest 断言名、`*.test-d.ts`） | "Only `toHaveBeenCalled`, `not.toHaveBeenCalled`, `toBeUndefined` …" |
| type-system-discipline | 多语言惯用法 | "`never`-typed binding in TypeScript, unannotated `match` in Rust, `-Wincomplete-patterns` in Haskell …" |
| make-operations-idempotent | 具体机制 | "Self-healing locks: use PID-based stale lock detection" |
| guard-the-context-window | 预算做法 | "Limit files per phase, set turn budgets" |

### 5.3 原则之间的内容重叠

| 重叠 | 位置 | pstack 是否处理 |
|---|---|---|
| 并发共享状态 | foundational-thinking「Concurrency corollary」 vs separate-before-serializing-shared-state 全文 | 未处理 |
| 先删再建 | foundational-thinking 末句 "Subtraction comes before scaffolding." vs subtract-before-you-add | 未处理 |
| 小提交、先测后修的顺序 | foundational-thinking「Scaffold first」"tests before fixes. Keep commits small and single-purpose." vs sequence-verifiable-units「Delivery」 | 未处理 |
| 测行为 | foundational-thinking "Test behavior and edge cases, not line counts." vs test-behavior-not-implementation；migrate-callers「Rule」"delete tests that only protect pre-refactor implementation details" | 未处理 |
| 调用层数 | laziness-protocol「Maintain a flat call hierarchy」（>3 files）vs minimize-reader-load「Layers to trace」 | 未处理 |
| 单一真源 | laziness-protocol「Consolidate decisions」 vs minimize-reader-load "Derive instead of sync" | 未处理 |
| 非法状态不可表示 | model-the-domain「Why」 vs type-system-discipline 第一条 pattern；encode-lessons「Pick the strongest mechanism」 | type-system 指向 encode-lessons（"See the **encode-lessons-in-structure** principle skill"），model-the-domain 未处理 |
| 边界解析 | boundary-discipline vs type-system-discipline "External data is untyped until parsed." | 已处理："See the **boundary-discipline** principle skill for where to put validation." |
| 不留兼容层 | migrate-callers-then-delete-legacy-apis vs outcome-oriented-execution | 未处理 |
| 原型 | experience-first "Prototype before committing" vs exhaust-the-design-space | 未处理 |
| 脚本化验证 | prove-it-works「Script the check」 vs build-the-lever | 已处理："For scripting the verification itself, see [Prove It Works]" |
| 泛化修复 | fix-root-causes "Check for the pattern, not just the instance" vs encode-lessons「Anti-patterns」"Fixing without generalizing" | 未处理 |
| 整体设计、增量交付 | redesign-from-first-principles 末条 vs sequence-verifiable-units | 未处理 |

推断：`foundational-thinking` 是重叠最多的一条，像是更早的总纲，后来拆出的专门原则没有回头删掉它里面对应的句子，这与 `principle-subtract-before-you-add` 自己的 "When a reference has no novel content, delete it" 相悖。

### 5.4 调用方复述原则（违反 `authoring-a-skill.md` 的 "Don't restate"）

- `skills/architect/references/runner-prompt.md` 第 12–18 行：先复述规则再写 "per the **X** principle skill"（如第 17 行 "Idempotent state transitions where applicable, per the **make-operations-idempotent** principle skill. Ask what happens if the operation runs twice or crashes halfway."）。推断：这是有意为之，因为这个文件是传给其他模型的 runner 的提示，runner 可能不去读叶文件。
- `skills/interrogate/references/rubric.md`：复述不点名（见 4.3）。
- `skills/poteto-mode/SKILL.md`「## Principles」：每条都复述触发和规则，这是索引的设计本意（README 第 196 行）。

### 5.5 未定义的术语

`principle-encode-lessons-in-structure` 第 25、30 行的 "brain note" 在全 pstack 没有其他出现，也没有定义。

---

## 6. 状态与重入

- 原则文件本身无状态、无待办、无持久化（原文：23 个文件里没有任何状态文件、todolist 或断点说明）。
- 读取状态以会话为界：`poteto-mode`「Non-negotiables」"Cite only principles whose leaf SKILL.md you read this session."；`agents/poteto-agent.md` 要求每次工作前重读 `poteto-mode` 全文。推断：会话中断或上下文压缩后，已读原则不算数，需重读叶文件。
- 可恢复的挂点只有一个：`figure-it-out` 把「读 Principles 小节」写成 todolist 的第一项（原文见 3.1），因此它随 todolist 一起被中断和恢复。
- 内容上，重入问题由原则 `principle-make-operations-idempotent` 自身处理（"What happens if this runs twice? What happens if the previous run crashed halfway?"），它是给被设计的系统用的，不是给原则的加载机制用的。

---

## 7. 额外问题的回答

**统一格式。** 没有强制模板。高频形态（推断归纳）：`# Title` + 规则句 + `**Why:**`（16/23）+ 带标签的 Pattern 类小节（16/23，七种标签写法；其余 7 条用无标签列表或粗体段首句承载做法）+ 判别小节（`The test(s)` 5 条、`Stop`/`Boundaries`/`Guardrails`/`When it applies` 等）。`**Balance:**` 只有 `principle-build-the-lever` 一条有。没有 Why 标签的 7 条：exhaust-the-design-space、foundational-thinking、experience-first、migrate-callers-then-delete-legacy-apis、type-system-discipline、laziness-protocol、redesign-from-first-principles；其中 exhaust、migrate、type-system 的理由写在首段或末句，experience-first、laziness-protocol、redesign、foundational-thinking 基本没有写理由（foundational-thinking 首句 "Structural decisions protect option value." 可算半句理由）。所以「都有 Why」不成立。

**description 怎么写「何时适用」。** 一律 "Apply <介词> <情境>."，情境写成可观察的信号或正在做的动作：失败次数（attack-the-premise "two or more fixes that share one premise have failed the same gate"）、心理冲动（never-block "tempted to ask"；laziness "tempted to add abstractions"）、重复（encode-lessons "writing the same instruction a second time"）、工作阶段（prove-it-works "after completing a task, before declaring done"；foundational-thinking "before writing logic"）、工作类型（fix-root-causes "when debugging"；test-behavior "when you write, change, or keep a test"）。`poteto-mode` 索引条目把 description 压成「情境片段 + 规则」两句，去掉 "Apply when"。

**原则之间怎么互相引用。** 6 条原则有指向其他原则的出链（attack-the-premise、build-the-lever、experience-first、minimize-reader-load、sequence-verifiable-units、type-system-discipline），共 13 条边；另有 2 条指向能力技能（prove-it-works → show-me-your-work，type-system-discipline → typescript-best-practices）（见 edges）。三种写法：相对链接 `[Title](../principle-x/SKILL.md)`（attack-the-premise、build-the-lever、minimize-reader-load）；粗体名 "the **x** principle skill"（sequence-verifiable-units、type-system-discipline）；纯文本（experience-first）。引用用途只有三种：「按 X 的方式做这一步」（attack-the-premise 的 "per [Build the Lever]"）、「与 X 的区别」、「X 的互补/类比」。被其他原则引用最多的是 laziness-protocol、build-the-lever、encode-lessons-in-structure、prove-it-works（各 2 次）。

**分组依据。** 原文只有 `08-principles.md` 的组义句："The core principles decide how much to build and when to rethink the design"；"The architecture principles decide where state, validation, and compatibility live"；"The verification principles define what counts as proof"；"The delegation principles keep parallel work sane"；"And one meta principle"。推断：分组按「这条原则约束哪类决定」划分，不按任务类型，也不按被哪个 playbook 使用。分组只影响索引排版，没有任何机制按组加载。

**什么样的规则够格成为原则（从 23 条归纳）。**

| 候选标准 | 是否成立 | 依据 |
|---|---|---|
| 跨任务通用 | 大体成立，但有领域限定：experience-first（产品/UX）、type-system-discipline（静态类型语言）、test-behavior-not-implementation（写测试时）、exhaust-the-design-space（无先例设计） | 各自 description |
| 都有 Why | 不成立，16/23 | 2.3 表 |
| 被 ≥2 处引用 | 不成立，6 条 ≤1 | 3.3 表 |
| 可用一个名词短语点名 | 成立，23/23 都是祈使短语或名词短语，可直接说出口转向 | `08-principles.md`「Steering in practice」 |
| 有可观察的触发情境 | 成立，23/23 description 以 Apply + 情境开头 | 2.1 |
| 能指出它改变了哪个决定 | 原文要求，但无机制检查 | `poteto-mode`「Non-negotiables」；`08-principles.md` 第 27 行 |
| 在 `poteto-mode` 索引里 | 成立，23/23 | `poteto-mode` 第 43–77 行 |

推断的实际门槛：**一个可以用短名字说出口、能在多种 playbook 中触发、能改变一个具体决定的工程判断，并且作者要求 agent 每次任务都在索引里看到它。** 被复用是结果，不是前提。

---

## 8. 给下一轮归置 MMW 的准绳（推断，基于上文）

1. 原则层的最小形态是：一个短文件（约 15–35 行），frontmatter 只有 `name`、`description`（"Apply when <情境>. <规则>."）和关闭自动触发；正文 = 规则句 + 理由 + 做法 + 判别问句。加载靠一个总是被读的索引（pstack 是 mode 技能里的内联列表）加「应用时读全文」。
2. 一条 MMW 现有规则是否值得抽成原则，按上表检查「能点名、有触发情境、能改变决定、跨 playbook」四项；不要求它已经被多处复用，但也不应为凑数把只属于一个流程的规则抽出来——pstack 的反例是 rubric、runner-prompt、Autonomy 里那些留在调用方的规则，它们带着具体清单或只服务一个读者，所以留在原处。
3. 原则只写方向，调用方有权限定范围（`prototype.md`、`feature.md`、`no-comments` 的写法），这使原则不需要为每个例外改写。
4. pstack 自己的例外（5.2、5.3）说明：原则里出现步骤、工具细节和相互重叠是可以容忍的，但会让索引摘要与正文漂移。若 MMW 采用这一层，应把 `description` 当作唯一摘要源，索引从它生成，避免 5.1 的四处不一致。

---

## 未确定

- `disable-model-invocation: true` 在 Cursor 中的确切语义（是否仍把 `description` 放进上下文、是否仍可被斜杠命令调用）：pstack 文件没有解释，本报告按键名推断为「不按 description 自动触发」。
- `poteto-mode` 索引是否是唯一的运行时发现路径：没有找到其他加载机制，但 Cursor 宿主是否另有技能列表注入，未查。
- "brain note" 指什么：pstack 内无定义。
- 只读了命中行的调用方文件（`skills/architect/SKILL.md`、`skills/arena/SKILL.md`、`skills/figure-it-out/SKILL.md`、各 playbook、`skills/reflect/SKILL.md`、`skills/show-me-your-work/SKILL.md`、`skills/tdd/SKILL.md`、`skills/no-comments/SKILL.md`、benny 三个技能）：这些文件里是否还有不含原则名的复述，未全部核对；4.3 的「未点名复述」清单因此不完整。
- grep 只覆盖 `.md` 的 slug 和标题两种写法；用意译（如 "design it twice" 对应 exhaust-the-design-space）引用原则的位置可能漏计。

---

```edges
poteto-mode -> principle-laziness-protocol : routes-to
poteto-mode -> principle-foundational-thinking : routes-to
poteto-mode -> principle-redesign-from-first-principles : routes-to
poteto-mode -> principle-attack-the-premise : routes-to
poteto-mode -> principle-subtract-before-you-add : routes-to
poteto-mode -> principle-minimize-reader-load : routes-to
poteto-mode -> principle-outcome-oriented-execution : routes-to
poteto-mode -> principle-experience-first : routes-to
poteto-mode -> principle-exhaust-the-design-space : routes-to
poteto-mode -> principle-build-the-lever : routes-to
poteto-mode -> principle-model-the-domain : routes-to
poteto-mode -> principle-boundary-discipline : routes-to
poteto-mode -> principle-type-system-discipline : routes-to
poteto-mode -> principle-make-operations-idempotent : routes-to
poteto-mode -> principle-migrate-callers-then-delete-legacy-apis : routes-to
poteto-mode -> principle-separate-before-serializing-shared-state : routes-to
poteto-mode -> principle-prove-it-works : routes-to
poteto-mode -> principle-fix-root-causes : routes-to
poteto-mode -> principle-sequence-verifiable-units : routes-to
poteto-mode -> principle-test-behavior-not-implementation : routes-to
poteto-mode -> principle-guard-the-context-window : routes-to
poteto-mode -> principle-never-block-on-the-human : routes-to
poteto-mode -> principle-encode-lessons-in-structure : routes-to
poteto-mode -> principle-model-the-domain : cites-principle
agents/poteto-agent.md -> poteto-mode : calls
agents/poteto-agent.md -> principle-* : routes-to
figure-it-out -> poteto-mode : reads-reference
figure-it-out -> principle-prove-it-works : cites-principle
figure-it-out -> principle-never-block-on-the-human : cites-principle
figure-it-out -> principle-foundational-thinking : cites-principle
figure-it-out -> principle-laziness-protocol : cites-principle
figure-it-out -> principle-separate-before-serializing-shared-state : cites-principle
figure-it-out -> principle-sequence-verifiable-units : cites-principle
figure-it-out -> principle-encode-lessons-in-structure : cites-principle
playbook:authoring-a-skill -> principle-encode-lessons-in-structure : cites-principle
playbook:autonomous-run -> principle-sequence-verifiable-units : cites-principle
playbook:autopilot-full -> principle-prove-it-works : cites-principle
playbook:bug-fix -> principle-sequence-verifiable-units : cites-principle
playbook:feature -> principle-separate-before-serializing-shared-state : cites-principle
playbook:feature -> principle-laziness-protocol : scopes-principle
playbook:feature -> principle-model-the-domain : cites-principle
playbook:feature -> principle-sequence-verifiable-units : cites-principle
playbook:hillclimb -> principle-prove-it-works : cites-principle
playbook:hillclimb -> principle-build-the-lever : cites-principle
playbook:hillclimb -> principle-guard-the-context-window : cites-principle
playbook:hillclimb -> principle-separate-before-serializing-shared-state : cites-principle
playbook:hillclimb -> principle-sequence-verifiable-units : cites-principle
playbook:hillclimb -> principle-laziness-protocol : cites-principle
playbook:multi-phase-plan -> principle-never-block-on-the-human : cites-principle
playbook:multi-phase-plan -> principle-guard-the-context-window : cites-principle
playbook:multi-phase-plan -> principle-sequence-verifiable-units : cites-principle
playbook:multi-phase-plan -> principle-encode-lessons-in-structure : cites-principle
playbook:multi-phase-plan -> principle-prove-it-works : cites-principle
playbook:orchestrate -> principle-separate-before-serializing-shared-state : cites-principle
playbook:orchestrate -> principle-encode-lessons-in-structure : cites-principle
playbook:perf-issue -> principle-sequence-verifiable-units : cites-principle
playbook:prototype -> principle-laziness-protocol : scopes-principle
playbook:prototype -> principle-exhaust-the-design-space : cites-principle
playbook:refactoring -> principle-model-the-domain : cites-principle
playbook:refactoring -> principle-foundational-thinking : cites-principle
playbook:refactoring -> principle-redesign-from-first-principles : cites-principle
playbook:refactoring -> principle-laziness-protocol : cites-principle
playbook:refactoring -> principle-subtract-before-you-add : cites-principle
playbook:refactoring -> principle-migrate-callers-then-delete-legacy-apis : cites-principle
playbook:refactoring -> principle-prove-it-works : cites-principle
playbook:refactoring -> principle-minimize-reader-load : cites-principle
playbook:refactoring -> principle-sequence-verifiable-units : cites-principle
playbook:runtime-forensics -> principle-guard-the-context-window : cites-principle
playbook:session-pickup -> principle-guard-the-context-window : cites-principle
playbook:session-pickup -> principle-prove-it-works : cites-principle
playbook:trace-forensics -> principle-guard-the-context-window : cites-principle
playbook:visual-parity -> principle-separate-before-serializing-shared-state : cites-principle
playbook:worktree-cleanup -> principle-build-the-lever : cites-principle
playbook:worktree-cleanup -> principle-encode-lessons-in-structure : cites-principle
playbook:worktree-cleanup -> principle-prove-it-works : cites-principle
playbook:worktree-cleanup -> principle-guard-the-context-window : cites-principle
architect -> principle-exhaust-the-design-space : cites-principle
architect -> principle-foundational-thinking : cites-principle
architect -> principle-outcome-oriented-execution : cites-principle
architect -> principle-fix-root-causes : cites-principle
architect -> principle-redesign-from-first-principles : cites-principle
architect -> principle-subtract-before-you-add : cites-principle
architect/references/rationale-template.md -> principle-boundary-discipline : cites-principle
architect/references/runner-prompt.md -> principle-separate-before-serializing-shared-state : cites-principle
architect/references/runner-prompt.md -> principle-encode-lessons-in-structure : cites-principle
architect/references/runner-prompt.md -> principle-boundary-discipline : cites-principle
architect/references/runner-prompt.md -> principle-make-operations-idempotent : cites-principle
architect/references/runner-prompt.md -> principle-laziness-protocol : cites-principle
architect/references/runner-prompt.md -> principle-minimize-reader-load : cites-principle
arena -> principle-separate-before-serializing-shared-state : cites-principle
arena -> principle-laziness-protocol : cites-principle
arena -> principle-redesign-from-first-principles : cites-principle
arena -> principle-prove-it-works : cites-principle
interrogate/references/rubric.md -> principle-boundary-discipline : restates-principle
no-comments -> principle-fix-root-causes : scopes-principle
no-comments -> principle-redesign-from-first-principles : scopes-principle
reflect -> principle-encode-lessons-in-structure : cites-principle
show-me-your-work -> principle-encode-lessons-in-structure : cites-principle
typescript-best-practices -> principle-type-system-discipline : cites-principle
typescript-best-practices -> principle-boundary-discipline : cites-principle
typescript-best-practices/references/patterns.md -> principle-boundary-discipline : cites-principle
typescript-best-practices/references/patterns.md -> principle-type-system-discipline : cites-principle
principle-attack-the-premise -> principle-build-the-lever : cites-principle
principle-attack-the-premise -> principle-fix-root-causes : cites-principle
principle-attack-the-premise -> principle-laziness-protocol : cites-principle
principle-attack-the-premise -> principle-redesign-from-first-principles : cites-principle
principle-build-the-lever -> principle-laziness-protocol : cites-principle
principle-build-the-lever -> principle-encode-lessons-in-structure : cites-principle
principle-build-the-lever -> principle-prove-it-works : cites-principle
principle-experience-first -> principle-foundational-thinking : cites-principle
principle-minimize-reader-load -> principle-guard-the-context-window : cites-principle
principle-sequence-verifiable-units -> principle-build-the-lever : cites-principle
principle-sequence-verifiable-units -> principle-prove-it-works : cites-principle
principle-type-system-discipline -> principle-boundary-discipline : cites-principle
principle-type-system-discipline -> principle-encode-lessons-in-structure : cites-principle
principle-type-system-discipline -> typescript-best-practices : cites-skill
principle-prove-it-works -> show-me-your-work : cites-skill
benny:reproduce-and-fix-issues -> principle-guard-the-context-window : cites-principle
benny:reproduce-and-fix-issues -> principle-fix-root-causes : cites-principle
benny:reproduce-and-fix-issues -> principle-prove-it-works : cites-principle
benny:reproduce-and-fix-issues -> principle-sequence-verifiable-units : cites-principle
benny:triage-issue-reports -> principle-separate-before-serializing-shared-state : cites-principle
benny:triage-issue-reports -> principle-minimize-reader-load : cites-principle
benny:setup-benny -> principle-separate-before-serializing-shared-state : requires-installed
benny:setup-benny -> principle-minimize-reader-load : requires-installed
benny:setup-benny -> principle-guard-the-context-window : requires-installed
benny:setup-benny -> principle-sequence-verifiable-units : requires-installed
benny:setup-benny -> principle-fix-root-causes : requires-installed
benny:setup-benny -> principle-prove-it-works : requires-installed
principle-* -> .cursor-plugin/plugin.json : configured-by
docs/guide/08-principles.md -> principle-* : documents
README.md -> principle-* : documents
README.md -> principle-type-system-discipline : documents
docs/guide/06-verify-and-ship.md -> principle-prove-it-works : documents
docs/guide/10-recipes-and-pitfalls.md -> principle-prove-it-works : documents
```

自拟关系说明：`scopes-principle` = 调用方点名原则的同时限定或反转它在本处的适用范围；`restates-principle` = 复述原则内容但未点名为技能；`cites-skill` = 原则指向能力技能；`requires-installed` = 调用方要求该原则技能在目标环境中可解析；`documents` = 面向人的文档列出或链接该原则（`08-principles.md` 和 `README.md` 各对 23 条都有一条链接，这里用 `principle-*` 合并）。
