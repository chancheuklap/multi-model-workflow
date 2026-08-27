# 落地中：worker 写码时如何不偏离设计与 prototype

本文回答一个问题：各家参考资料在 worker 动手写码期间，用什么机制让它跟着设计走、发现偏离时怎么处理、怎么控制过度构建。参考快照都在 `docs/research/code-landing-refs/`（目录索引见其 `README.md` 第 7–14 行）；下文的路径省略这个前缀。我们自己的技能在 `mmw-v2/upstream/skills/engineering/` 下，路径写全。

## 1. 一句话结论

各家都把"设计产物"升格为**契约**（pstack 的 sketch、visual-parity 的 baseline、unlazy 的 GATES 账本、grok 的 design doc 节选），再用三条互相独立的机制守住它：写码前把契约内容塞进 worker 的提示词而不是给路径、写码中把偏离当成要上报的信号而不是默默吸收、写完后用可运行的检查（图像 diff / `CHECK:`+`EXPECT:`）而不是靠眼睛验收；过度构建则只有 ponytail 有基准证据证明"哪种措辞真的改变行为"——写成带具体动作的操作性指令（"grep every caller"）有效，写成原则性散文（"trace the flow end to end"）无效。

## 2. 机制对照表

行是机制类型，列是来源。格内是该来源里最直接的出处；空格表示该来源没有这一机制。

| 机制类型 | pstack | unlazy | ponytail | grok-bundled | swarm-forge | 我们现状 |
| --- | --- | --- | --- | --- | --- | --- |
| **设计草图即契约** | `pstack/skills/architect/SKILL.md` 第 55 行 "The synthesized sketch is the contract"；`references/runner-prompt.md` 第 9 行 "The usage is the spec; the two must agree, so reconcile the sketch to the usage, not the reverse" | `unlazy/SKILL.md` 第 12 行：写码前先写 `GATES.md`，"State one observable outcome per gate"；`references/token-economy.md` 第 14 行 "Give a leaf the shared contract and its own ledger, not the driver's transcript" | — | `grok-bundled/execute-plan/SKILL.md` 第 502–504 行：implementer 提示词里直接放 "the full design doc content that pertains to this PR's scope"，不是路径 | — | `mmw-v2/upstream/skills/engineering/prototype/SKILL.md` 第 8 行 "the real implementation is written with it as reference"、第 107 行 "with the prototype as reference"——只是"参考"，没有"契约"一词 |
| **常驻规则注入** | `pstack/README.md` 第 84 行：poteto-mode 开工时 "the first item is reading the inline principles index"；21 条原则表在第 201–224 行；单条原则文件都是 `disable-model-invocation: true`（如 `pstack/skills/principle-laziness-protocol/SKILL.md` 第 4 行） | `unlazy/SKILL.md` 第 84–92 行：可选的 Claude Code Stop hook，账本有未满足的 gate 时返回 `decision: "block"` | `ponytail/.openclaw/skills/ponytail/SKILL.md` 第 14–18 行 "ACTIVE EVERY RESPONSE. No drift back to over-building"；`ponytail/docs/agent-portability.md` 第 13–15 行：OpenCode / pi 适配器 "injects the ruleset each turn"，Grok "lifecycle hooks are not used because passive hook output cannot inject instructions" | `grok-bundled/implement/SKILL.md` 第 48–60 行：每次 spawn 把 `shared/personas/implementer.md` 全文 **prepend** 到提示词；`execute-plan/SKILL.md` 第 102 行 `--instructions` 注入每个 implementer 与 reviewer 提示词 | `swarm-forge/swarmforge/constitution/articles/engineering.prompt`、`workflow.prompt` 是每个角色的宪法（文件名后缀 `.prompt`） | 技能软链是一次性读取（`AGENTS.md` 约定段："只有 frontmatter 的 `description` 是宿主启动时扫进去的"）；没有逐轮注入 |
| **偏离即信号并上报** | `pstack/skills/architect/SKILL.md` 第 57 行 "Deviations from the sketch are signal worth surfacing, not friction to absorb silently… Surface it; don't bolt it on"；第 59–79 行 Phase E：同形偏离重复出现 → 扔掉 sketch 重设计 | `unlazy/SKILL.md` 第 32 行：做不到的 gate 不能删，写 `ABANDON: <id> <reason>` 并作为 "required handoff" 暴露 | — | `grok-bundled/execute-plan/SKILL.md` 第 535–536 行：implementer 的 summary 必须写 "any deviations from the plan"；`grok-bundled/implement/SKILL.md` 第 539–571 行 Plan Alignment 专家审 "Whether the implementation deviates from the planned approach"、"Whether any scope creep has occurred" | `workflow.prompt` 第 30–31 行 Failure Conditions："stop and report instead of silently working in the wrong place" | `mmw-v2/upstream/skills/engineering/implement/SKILL.md` 第 8 行只在开工前 "stop and report"；写码中没有偏离上报条款 |
| **视觉基线** | `pstack/skills/poteto-mode/playbooks/visual-parity.md` 第 3 行 "The baseline is the spec; you do not touch it"；第 5 行 "No baseline, no parity claim"；第 6 行 "no harness modifications, no baseline tampering, no component restructuring to make a diff pass"；第 8 行 "A nonzero diff is a fail" | `unlazy/references/gates.md` 第 97 行 "Observe the outcome directly. Make the check read the artifact… named by the title"——可承载截图 diff，但没有现成的视觉 gate | — | — | — | `mmw-v2/upstream/skills/engineering/prototype/UI.md` 第 102 行只说 "Fold the winner into the real code, rewritten to production standard"；没有任何验收方式 |
| **四遍工作法** | `pstack/skills/poteto-mode/playbooks/refactoring.md` 第 13 行第 7 步 "If the diff does not lower reader load somewhere, revert it"（事后自审一遍） | `unlazy/SKILL.md` 第 53–58 行 "Work each leaf in four passes"：完整交付 → 以领域专家身份重读并替换廉价版本 → 猎正确性/集成/可移植/性能/证据缺陷 → 低成本打磨，直到一整遍找不到东西 | — | `grok-bundled/implement/SKILL.md` 第 758–760 行：外部 reviewer 循环 "until 0 issues"，不是自审 | — | — |
| **写路径所有权** | `pstack/skills/poteto-mode/playbooks/feature.md` 第 12 行：委派时给 "a specific scope (file paths, named data shape…)" | `unlazy/references/gates.md` 第 10 行 `OWNS: src/import/**, tests/import/**`、第 39 行格式、第 130–132 行 "Concurrent leaves must declare disjoint paths, claim them before dispatch"；`unlazy/SKILL.md` 第 38 行 "Treat scopes… as coordination, never as filesystem isolation" | — | `grok-bundled/execute-plan/SKILL.md` 第 482 行 `isolation: "worktree"`、第 499 行提示词列 "Files to modify" | `workflow.prompt` 第 3–8 行 Worktree Discipline："Work only in your assigned branch or worktree"、"Do not inspect, diff, merge, or base work on another branch unless… named in a handoff" | `AGENTS.md` 约定段：正式改动在独立 worktree；票没有写路径声明 |
| **其他：过度构建控制** | `pstack/skills/principle-laziness-protocol/SKILL.md` 第 9–18 行；`principle-subtract-before-you-add/SKILL.md` 第 9–22 行 | — | `ponytail/.openclaw/skills/ponytail/SKILL.md` 第 20–36 行梯子 | `grok-bundled/shared/personas/implementer.md` 第 15 行 "Make the smallest change that solves the problem"、第 18 行 "Don't add features that weren't asked for" | `engineering.prompt` 第 21 行 "Prefer the simplest design that supports the current behavior and leaves clear options for the next step" | `mmw-v2/upstream/skills/engineering/tdd/SKILL.md` 第 36 行 "Don't anticipate future tests or add speculative features"——只管 TDD 循环内 |
| **其他：不改测试/基线迁就实现** | `pstack/skills/tdd/SKILL.md` 第 31–32 行 "Do not change tests merely to match a wrong implementation"、"Do not weaken existing assertions" | `unlazy/SKILL.md` 第 28 行 "never treat a successful `EXPECT:` match as proof that the English gate is honest"；`references/gates.md` 第 100 行 "Do not make a number copied from the brief its own expectation" | — | — | `engineering.prompt` 第 52 行 "Do not edit mutation testing or Gherkin acceptance mutation manifests by hand" | — |

## 3. 对"agent 无视 HTML mockup 自己乱写"：各家能挡住哪一层

症状拆成三层，从粗到细：**读没读**、**读了没照做**、**照做了但细节走样**。

### 3.1 读没读

- **grok-bundled** 最直接：`grok-bundled/execute-plan/SKILL.md` 第 502–504 行把设计文档**内容**放进提示词（"read and include the full design doc content that pertains to this PR's scope"），worker 不需要主动去读。同文件第 1245 行 "Include design context in initial prompts"、第 1253 行 "Include the design doc context in subagent prompts" 重复了两次。
- **unlazy**：`references/token-economy.md` 第 14 行，leaf 拿到的是 "the shared contract and its own ledger"，不是驱动者的完整 transcript——同样是内容而非路径，且只给这一片。
- **pstack**：`pstack/README.md` 第 188 行 "substituting `generalPurpose` skips that read and drifts"——承认"没读就漂"，解法是专用 subagent `poteto-agent` 开工必读 poteto-mode 全文。
- **我们现状**：`mmw-v2/upstream/skills/engineering/implement/SKILL.md` 第 10 行要求读 "the chosen artifact of a prototype"，靠 worker 自觉；spec 大时会被跳过或读丢。

### 3.2 读了没照做

- **pstack** 最直接：`pstack/skills/architect/SKILL.md` 第 55–57 行，sketch 是契约，偏离要**上报**而非默默加上（"Surface it; don't bolt it on"）。这给了 worker 一条不是"照做"就是"说出来"的二选一，堵住第三种"自己改了不说"。
- **grok-bundled**：`grok-bundled/implement/SKILL.md` 第 539–571 行 Plan Alignment 专家事后审 "deviates from the planned approach" 和 "scope creep"；`execute-plan/SKILL.md` 第 536 行 summary 必填 "any deviations from the plan"。这是**事后**挡，写码期间不介入。
- **ponytail**：`ponytail/.openclaw/skills/ponytail/SKILL.md` 第 80–83 行 "Never simplify away… anything explicitly requested. User insists on the full version → build it, no re-arguing"。只挡"因为懒而不照做"这一种动机。
- **grok implementer 人格**：`grok-bundled/shared/personas/implementer.md` 第 14 行 "Follow existing code patterns exactly"、第 18 行 "Don't add features that weren't asked for"。是泛化的服从条款，没提设计产物。

### 3.3 照做了但细节走样

- **pstack visual-parity** 最直接，也是**唯一**专门针对 UI 的：`pstack/skills/poteto-mode/playbooks/visual-parity.md` 第 5 行先建截图基线（"No baseline, no parity claim. A blocking prerequisite, not a follow-up"）、第 8 行 "Equivalence is verified by image diff, not by eye… A nonzero diff is a fail; investigate the pixel delta, don't wave it through"、第 6 行禁止改基线或改 harness 让 diff 过、"If the baseline looks wrong, stop and ask, don't edit it"。
- **unlazy**：`unlazy/references/gates.md` 第 97–102 行的 gate 写法（直接观察产物、只输出成功标记、负控制）能承载一个截图 diff 的 `CHECK:`，但快照里没有现成的视觉 gate 模板。
- 其余各家没有到这一层。

### 3.4 小结

| 层 | 最直接的一家 | 出处 |
| --- | --- | --- |
| 读没读 | grok-bundled | `grok-bundled/execute-plan/SKILL.md` 第 502–504 行 |
| 读了没照做 | pstack | `pstack/skills/architect/SKILL.md` 第 55–57 行 |
| 照做了但细节走样 | pstack | `pstack/skills/poteto-mode/playbooks/visual-parity.md` 第 5–8 行 |

注意 pstack 的 sketch 契约是**类型和签名**（`pstack/skills/architect/SKILL.md` 第 9 行 "Sketch types, function signatures, class shapes, and module boundaries"），不是 UI mockup；把它用于 `prototypes/<task>/<issue>/UI/` 是我们自己的类比。visual-parity 原本用于"make X match Y exactly"、样式系统迁移、跨框架移植（该文件第 3 行），把"prototype 的获胜 variant"当 Y 同样是类比。

## 4. 过度构建控制

### 4.1 ponytail 梯子 与 pstack laziness-protocol / subtract-before-you-add 的异同

**相同的地方**

| 主张 | ponytail 出处（`ponytail/.openclaw/skills/ponytail/SKILL.md`） | pstack 出处 |
| --- | --- | --- |
| 删除优先于新增 | 第 48 行 "Deletion over addition" | `principle-laziness-protocol/SKILL.md` 第 11 行 "Prefer deletion"；`principle-subtract-before-you-add/SKILL.md` 第 11 行 "Default to subtraction" |
| 最小 diff | 第 50 行 "Shortest working diff wins" | `principle-laziness-protocol/SKILL.md` 第 14 行 "Minimize the diff" |
| 不做投机性的东西 | 第 24 行 rung 1 "Speculative need = skip it" | `principle-subtract-before-you-add/SKILL.md` 第 18–19 行 "Design for observed usage, not speculative edge cases / No speculative validators, parsers, or guards beyond what the spec demands" |
| 借人类维护者的疲劳感 | 第 10–12 行 "been paged at 3am for one" | `principle-laziness-protocol/SKILL.md` 第 9 行 "borrowing a human maintainer's fatigue" |

**不同的地方**

| 维度 | ponytail | pstack |
| --- | --- | --- |
| 形态 | **逐决策的有序梯子**：第 22 行 "Stop at the first rung that holds"，7 级从"要不要存在"到"最小代码"；每个"要不要写这段"的决定都跑一遍 | **两条原则**：laziness 是一组并列偏好（第 11–16 行），subtract 是**时序**原则（第 16 行 "Sequence removal before construction"）；作用在整个设计/diff 层面，不是逐决策 |
| 何时生效 | 第 14–18 行 "ACTIVE EVERY RESPONSE"，默认 `full`，只有说 "stop ponytail" 才关 | 原则文件全是 `disable-model-invocation: true`（如 `principle-laziness-protocol/SKILL.md` 第 4 行），由 poteto-mode 在开工时读索引（`pstack/README.md` 第 84 行）；`playbooks/feature.md` 第 12 行明说 "Laziness Protocol does not override it"（委派必做） |
| 例外清单 | 第 78–83 行 "When NOT to be lazy"：trust boundary 的输入校验、防数据丢失的错误处理、安全、无障碍、**明确要求的东西**；第 85–89 行 "Never lazy about understanding the problem" | 没有例外清单；`playbooks/refactoring.md` 第 10 行 "A speculative cleanup that 'might help' gets reverted"、第 13 行 "If the diff does not lower reader load somewhere, revert it"——用**回滚**而非例外来兜底 |
| 输出格式 | 第 63 行固定模式 `[code] → skipped: [X], add when [Y].`；第 52 行用 `ponytail:` 注释标记有已知天花板的简化 | 无输出格式；`pstack/docs/guide/05-build-and-clean.md` 第 49–51 行靠提交前 `/deslop` 清 "narrating comments, unsupported guards, dead compatibility paths" |
| 检查 | 第 95–100 行 "Lazy code without its check is unfinished"：非平凡逻辑留 ONE runnable check | `principle-subtract-before-you-add/SKILL.md` 不谈检查；prove-it-works 是另一条原则（`pstack/README.md` 第 218 行） |
| 覆盖 bug 修 | 第 38–42 行 "Bug fix = root cause, not symptom… grep every caller" | `pstack/README.md` 第 219 行 fix-root-causes 原则："reproduce first, ask why until you reach it" |

一句话：ponytail 是**写码时逐决策跑的操作性清单**，pstack 是**设计和提交前的偏好与回滚规则**。两者不冲突，但放在一个技能里会有两套"最小"的定义，所以本文第 6 节只取一家。

### 4.2 ponytail 基准里"哪种措辞真的有效"的证据

来源：`ponytail/benchmarks/results/2026-06-22-issue-245-217-comprehension.md`。

- 任务（第 29–36 行）：`bank.py` 里 `transfer()` 和 `withdraw()` 共用 `_debit()`；bug 报告只提 transfer；评分用报告里**没提**的 withdraw，只有修到共享的 `_debit()` 才算过。
- 结果（第 38–44 行）：Sonnet 4.6 与 Opus 4.8 上 baseline 1/6 → ponytail 6/6；Haiku 4.5 两臂都约 0。
- **关键控制实验**（第 50–52 行）："pre-fix ponytail and a plain-prose version ('trace the flow end to end') both scored 0/3 on Opus; only the grep-the-callers directive moved it to 6/6."——同一个意图，写成原则性散文无效，写成带具体动作的指令（第 21–24 行的 "Grep every caller of the function you touch and fix the shared function once"）有效。
- 措辞的第二个要点（第 26–27 行）："the root-cause fix is presented as the *lazier* (smaller) diff, so ponytail's own instinct pulls toward it rather than away."——把想要的行为说成符合 agent 已有偏好的那个选项。
- 模型天花板（第 54–61 行）：Haiku 不执行多步指令，措辞再强也没用；规则只对"有余量"的模型起作用。
- 反例（第 63–71 行）：rung 2 "Already in this codebase?" 在三个模型上 baseline 与 ponytail 都是 1.0，"the behavioural value is unproven here"——不是所有规则都能测出效果，测不出的不能拿来当证据。
- 回归检查（第 73–87 行）：改规则后 27 项安全/质量任务不变；顺带记了一个与本议题相关的小模型现象："Haiku sometimes *narrates* a complete solution in chat but leaves the file unwritten"（第 85–87 行）——`grok-bundled/implement/SKILL.md` 第 19–27 行的 Tool-Call Discipline 是针对同一现象的另一家解法。

对我们的含义：给 worker 的防偏离条款要写成"做什么动作、对什么对象"（例如"打开 `prototypes/<task>/<issue>/UI/README.md` 里记录的获胜 variant 文件，按其 DOM 结构逐段实现"），不要写成"以 prototype 为参考"。`mmw-v2/upstream/skills/engineering/prototype/SKILL.md` 第 107 行 "with the prototype as reference" 正是基准里证明无效的那类措辞。

## 5. 对照我们 implement 技能的缺口清单

对象：`mmw-v2/upstream/skills/engineering/implement/SKILL.md`（全文 24 行）与它引用的 `tdd/SKILL.md`、`prototype/SKILL.md`、`prototype/UI.md`。

**必须补的（5 条）**

| # | 缺什么 | 哪家有 | 出处 |
| --- | --- | --- | --- |
| 1 | 没有把 prototype 的获胜 artifact 定性为契约；第 10 行只要求"读到结论"，`prototype/SKILL.md` 第 107 行只说 "as reference" | pstack | `pstack/skills/architect/SKILL.md` 第 55 行；`pstack/skills/poteto-mode/playbooks/visual-parity.md` 第 3 行 |
| 2 | 写码期间没有偏离上报条款；第 8 行的 "stop and report" 只在开工前 | pstack | `pstack/skills/architect/SKILL.md` 第 57 行 |
| 3 | UI 票没有验收方式；`prototype/UI.md` 第 102–109 行第 6 步的完成条件只是"叶子目录外无人 import" | pstack | `pstack/skills/poteto-mode/playbooks/visual-parity.md` 第 5–8 行 |
| 4 | 没有过度构建规则；`tdd/SKILL.md` 第 36 行只管 TDD 循环内不预写测试 | ponytail | `ponytail/.openclaw/skills/ponytail/SKILL.md` 第 20–36、45–52、78–100 行 |
| 5 | 票没有写路径声明，worker 可以改任何文件；`AGENTS.md` 只约束 worktree 层级 | unlazy | `unlazy/references/gates.md` 第 10、39、130–132 行 |

**之后再看的（3 条）**

| # | 缺什么 | 哪家有 | 出处 |
| --- | --- | --- | --- |
| 6 | worker 拿到的是整份 spec 的路径而不是本票相关节选的内容（"spec 很大，用不上"的直接原因） | grok-bundled | `grok-bundled/execute-plan/SKILL.md` 第 502–504 行 |
| 7 | 没有交付前自审遍数；第 18 行直接交给 `/code-review` | unlazy | `unlazy/SKILL.md` 第 53–58 行 |
| 8 | 规则不常驻：技能只在调用时读一次，长会话里会漂 | ponytail | `ponytail/.openclaw/skills/ponytail/SKILL.md` 第 14–18 行；`ponytail/docs/agent-portability.md` 第 13–15 行说明哪些宿主能逐轮注入、哪些不能 |

## 6. 候选改法（≤5 条，一个议题只取一家）

每条只取一家来源。互斥项指"同一议题另一家的做法"，取了本条就不取那家。

| # | 改法 | 来源（唯一） | 落点 | 互斥项 |
| --- | --- | --- | --- | --- |
| A | 在 implement 开工读取之后加一句：票 **Read first** 里 prototype 的获胜 artifact 是契约；实现时发现契约装不下的需求（需要 prototype 没有的状态、字段、交互），先在票上评论"契约缺什么、是 prototype 错了还是需求漏了还是实现越界了"，再继续；不默默加 | pstack `pstack/skills/architect/SKILL.md` 第 55–57 行 | `mmw-v2/upstream/skills/engineering/implement/SKILL.md` 第 10 行之后 | grok-bundled 的"summary 里写 deviations + Plan Alignment 事后审"（`grok-bundled/execute-plan/SKILL.md` 第 536 行、`implement/SKILL.md` 第 539–571 行）——那是事后通道，与 A 的即时通道二选一 |
| B | UI 票增加视觉基线：写码前对获胜 variant 截图存为 baseline；折入真实页面后对同一路由截图做图像 diff；diff 非零就不算完成，去查像素差；禁止改 baseline、改 harness、或为了让 diff 过而重排组件；baseline 看着不对就停下问 | pstack `pstack/skills/poteto-mode/playbooks/visual-parity.md` 第 5–8 行 | `mmw-v2/upstream/skills/engineering/prototype/UI.md` 第 6 步（第 100–109 行）的完成条件 | unlazy 用 `CHECK:`/`EXPECT:` gate 承载同一个 diff（`unlazy/references/gates.md` 第 97–102 行）——验收账本形式，与 B 的 playbook 形式二选一 |
| C | 过度构建：把 ponytail 的 7 级梯子、"When NOT to be lazy" 例外清单（含"明确要求的东西必须建"）、输出模式 `skipped: [X], add when [Y]`、以及"非平凡逻辑留 ONE runnable check"写进 implement 的写码段；措辞按第 4.2 节的证据写成操作性指令 | ponytail `ponytail/.openclaw/skills/ponytail/SKILL.md` 第 20–36、63、78–100 行 | `mmw-v2/upstream/skills/engineering/implement/SKILL.md` 第 14 行 "Use /tdd" 附近 | pstack laziness-protocol + subtract-before-you-add（`pstack/skills/principle-laziness-protocol/SKILL.md` 第 9–18 行、`principle-subtract-before-you-add/SKILL.md` 第 9–22 行）；grok `implementer.md` 第 15、18 行——三家对"最小"的定义不同，只取一家 |
| D | 写路径所有权：票声明 `OWNS:` 路径 glob；worker 只在这些路径内写；要改路径外的文件就是第 A 条的偏离，先上报 | unlazy `unlazy/references/gates.md` 第 10、39、130–132 行；`unlazy/SKILL.md` 第 38 行 | 票模板（`to-tickets`）加一节，implement 第 8 行的开工核对加一项 | swarm-forge Worktree Discipline（`workflow.prompt` 第 3–8 行）是分支粒度的同一议题；grok `execute-plan/SKILL.md` 第 499 行 "Files to modify" 是提示词粒度——只取一家作为"我能写哪里"的规则 |
| E | 派 worker 时把票指名的 spec 小节、prototype 叶子 `README.md` 的结论段**内容**放进提示词，不给路径；worker 完成时在 summary 里列 "any deviations from the plan"（若已取 A，则此处只保留内容注入，不再写 deviations） | grok-bundled `grok-bundled/execute-plan/SKILL.md` 第 502–504、535–536 行 | 派发 implement 的那一端（属于落地前一刻与落地中的交界，本文只记录，归属由第一阶段研究决定） | unlazy `references/token-economy.md` 第 14 行的 "contract + ledger" 是同一议题的另一种切法 |

A、B、C、D 之间不互斥，可以同时取。E 与 A 在"偏离走哪条通道"上重叠，取 A 就删掉 E 的 deviations 部分。

## 7. 未读或未确定的事项

**未读**

- `pstack/skills/poteto-mode/SKILL.md` 全文与 `playbooks/prototype.md`、`playbooks/opening-a-pr.md`：README 第 63 行说 prototype playbook 是 "a throwaway sketch"，与我们"长期保存"的原型定位相反，可能有需要排除的条款。
- `pstack/skills/principle-prove-it-works/`、`principle-encode-lessons-in-structure/` 的正文：只读了 README 第 218、223 行的一句摘要。
- `unlazy/references/parallel.md`、`method.md`、`orchestration.md`、`dispatch.md`、`templates/`：OWNS 的 claim/release 协议细节在 `parallel.md`。
- `ponytail/benchmarks/README.md`、`benchmarks/agentic/`、`hooks/`：基准的评分方式和"逐轮注入"在 Claude Code 上的具体实现没看，第 4.2 节的结论只基于结果文件本身。
- `grok-bundled/shared/personas/reviewer.md`、`grok-bundled/design/`：reviewer 人格里可能有与 Plan Alignment 重叠的条款。
- `swarm-forge/swarmforge/handoff-protocol.md` 与 `constitution/articles/` 下其他文件。
- `mattpocock-implement-spec/`：不在本阶段分配范围内。

**未确定**

- `to-tickets` 生成的票，其 **Read first** 是否真的会列出 prototype 叶子目录；implement 第 10 行的 "the chosen artifact of a prototype" 依赖这一点，我没读 `to-tickets` 技能。
- 我们的宿主里有没有可用的截图 diff 工具链；`playwright-cli` 与 `ui-qa` 技能存在，但没核对它们能否做基线比对。B 条依赖这个。
- 第 8 条缺口（规则常驻）在我们"技能正文对所有宿主同一份、不按宿主名分支"的约定下能否实现；`ponytail/docs/agent-portability.md` 第 13 行明确 Grok 的 hook 不能注入指令。
- 第 4.2 节的证据来自 bug 修任务，是否能外推到"照 mockup 写 UI"这类任务，快照里没有对应基准。
