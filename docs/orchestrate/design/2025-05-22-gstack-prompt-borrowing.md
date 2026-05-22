# GStack 提示词框架调研报告——基于 Plugin 现状的深度对照

> **调研对象**: [GStack](https://github.com/garrytan/gstack) (garrytan/gstack)
> **调研日期**: 2025-05-22
> **调研目的**: 识别 GStack 中值得借鉴到 multi-model-workflow plugin-v2 的提示词框架和具体提示词内容
> **前置文档**: `2025-05-22-plugin-maturity.md`（成熟架构设计）

## 1. 核心发现：脚手架已搭好，内容是骨架

通读了 plugin-v2 全部 97 个文件（6 个 SKILL.md、8 个 agent 定义、45 个 reference 文档、11 个模板、10 个 resolver、全部 hooks 和 scripts）后，发现：

**架构层面**已经吸收了 GStack 的核心思想——构建系统（11 个模板 + 10 个 resolver）、信封协议、状态机、置信度分桶、Trust Boundary、Voice Directive 变体机制——这些全部到位。

**提示词内容层面**严重不足。用数字说：

| 维度 | 我们的现状 | GStack 对应内容 |
|------|----------|---------------|
| Voice Directive | 12 个变体共 61 行（每个 ~5 行） | 单个 skill 的 Voice 段就有 ~30 行 |
| 禁止词 | 7 个 | 17+ 个 |
| Good/Bad 示例 | 全系统 0 处 | 每个 Voice 段都有 |
| AskUserQuestion 格式规范 | 0（Direction Check 有模板但无格式框架） | 完整 Decision Brief Protocol + 11 项自检 |
| 用户可见输出格式 | 全系统只有 4 处定义 | 每个 skill exit 都有结构化格式 |
| Confidence 验证门槛 | 有 1-10 分桶，无验证机制 | Pre-emit Verification Gate（引用代码行或降级） |
| 结构化退出协议 | 无 | DONE/DONE\_WITH\_CONCERNS/BLOCKED/NEEDS\_CONTEXT |
| Anti-Sycophancy | 无 | 5 条禁止句式 + 正面替换 |
| Review 校准反例 | "只 flag 真实问题" 一句话 | Rationalization Prevention + FP 类别表 |

**问题不是"缺什么功能"，而是"已有框架里的内容密度不够"。** 构建系统、resolver、模板机制已经到位——现在需要的是用 GStack 已经验证过的高密度提示词内容去填充这些框架。

## 2. Tier 0：发现的 Bug（与 GStack 无关，需要先修）

通读过程中发现的正确性问题：

### 2.1 docs-worker voice-directive 注入了 Coordinator 人格

`agents/docs-worker.md` 行 74：voice-directive 标记为 `variant=workflow`，注入的是 Coordinator 人格（"你是 Coordinator——项目的中枢调度者"）。docs-worker 带着 Coordinator 的身份在运行。

### 2.2 complex-code-explorer voice-directive 注入了错误变体

`agents/complex-code-explorer.md` 行 68：voice-directive 标记为 `variant=code-explorer`，注入的是 code-explorer 而非 complex-code-explorer 人格。

### 2.3 persona.md 缺少 docs-worker

`agents/persona.md` 覆盖 7 个角色，缺少 docs-worker。persona.md 与各 agent 文件中的 voice-directive 块是同一份内容的两个独立来源——上面两个 bug 就是漂移的证据。

### 2.4 plan-writer agent 定义极度单薄

`agents/plan-writer.md`（39 行）是所有 agent 中最薄的。没有 Return Contract、没有 Self-Check、没有 Three-Failure Protocol。所有行为定义全部外挂到 Coordinator dispatch 中传入的 methodology 文件。如果 Coordinator 的 dispatch prompt 少了 methodology 路径，plan-writer 没有任何 fallback。对比 pack-executor（157 行）有完整的 Return Contract + Self-Check + Three-Failure Protocol + Pre-delivery Checklist。

### 2.5 结构性建议：persona.md 应成为 Voice 唯一权威来源

两个 voice-directive bug + persona.md 缺少 docs-worker = 双来源漂移的证据。建议 persona.md 成为 SSOT，构建系统从 persona.md 为每个 agent 生成 voice-directive 块。agent 文件中不再手写 voice。

## 3. Tier 1：用户可见体验——差距最大的区域

### 3.1 Decision Brief Protocol（新建 `decision-brief.md.tmpl`）

**现状**：整个 plugin 只有 4 处定义了用户可见的输出格式——direction-check 模板、设计文档确认一句话、business report 四段式、PR body 模板。除此之外，所有的 AskUserQuestion（BLOCKED、user decision disposition、Direction Check、模糊输入收窄）都没有格式规范。BLOCKED 格式只在 workflow 和 execution 两个 SKILL.md 中定义，**discovery、plan-writing、final-review、multi-pr-merge 四个 phase 的 BLOCKED 格式完全缺失**。

**GStack 做了什么**：一套完整的 Decision Brief 协议，确保每次向用户提问都是结构化的：

```
D<N> — <一行问题标题>
ELI10: <用16岁能看懂的话说清利害关系，2-4句>
Stakes if we pick wrong: <一句话：选错了什么会坏>
Recommendation: <推荐选项> because <一行理由>
Pros / cons:
A) <选项> (recommended)
  ✅ <优点——具体可观测, ≥40字符>
  ❌ <缺点——真实可观测, ≥40字符>
B) <选项>
  ✅ ...
  ❌ ...
Net: <一句话总结你在交换什么>
```

配套 11 项自检清单：

```
Before calling AskUserQuestion, verify:
- [ ] D<N> header present
- [ ] ELI10 paragraph present (stakes line too)
- [ ] Recommendation line present with concrete reason
- [ ] Completeness scored (coverage) OR kind-note present (kind)
- [ ] Every option has ≥2 ✅ and ≥1 ❌, each ≥40 chars (or hard-stop escape)
- [ ] (recommended) label on one option (even for neutral-posture)
- [ ] Dual-scale effort labels on effort-bearing options (human / CC)
- [ ] Net line closes the decision
- [ ] You are calling the tool, not writing prose
- [ ] Non-ASCII characters (CJK / accents) written directly, NOT \u-escaped
```

**为什么这是最高优先级**：设计文档 §3.7 承诺"BLOCKED 对非技术用户不再是黑洞"，§5b 承诺"Direction Check 信息化"。Decision Brief 是一个统一框架，可以同时填补 BLOCKED 报告、Direction Check、user decision disposition 三类用户交互场景。

**落地位置**：新建 `decision-brief.md.tmpl`，由构建系统注入到所有需要 AskUserQuestion 的位置。

### 3.2 Business Report 需要 Good/Bad 锚点

**现状**：`final-review-completion.md` Step 19 定义了业务报告的四段结构（新增能力 / 验证证据 / 残余风险 / 发布检查），说了"用业务语言，不用技术术语"，但没有示例。AI 看到"用业务语言"时，对什么算"业务语言"的理解不稳定。

**GStack 的 Voice 段提供了完美的锚点对比**：

```
Good: "用户现在可以用手机号登录，15 秒内完成。之前只支持邮箱，平均 45 秒。"
Bad:  "实现了 PhoneAuthProvider 并集成到 AuthStrategy pipeline，通过 TDD 验证了 
       happy path 和 edge cases。"
```

**落地位置**：在 `final-review-completion.md` Step 19 中加入 2-3 组 Good/Bad 示例对。同时在 `voice-directive.md.tmpl` 的 `workflow` variant 中也加入类似的示例。

## 4. Tier 2：AI 行为控制——Voice 和 Calibration

### 4.1 Voice Directive 充实（改 `voice-directive.md.tmpl`）

**现状**：每个 variant 约 5 行（1 句角色声明 + 1 句行为指令 + 7 个禁止词）。

**GStack 的 Voice 段是 ~30 行**，包含六层：

```
1. 正面行为原则（6条）
- Lead with the point. Say what it does, why it matters, and what changes for the builder.
- Be concrete. Name files, functions, line numbers, commands, outputs, evals, and real numbers.
- Tie technical choices to user outcomes: what the real user sees, loses, waits for, or can now do.
- Be direct about quality. Bugs matter. Edge cases matter. Fix the whole thing, not the demo path.
- Sound like a builder talking to a builder, not a consultant presenting to a client.
- Never corporate, academic, PR, or hype. Avoid filler, throat-clearing, generic optimism.

2. Good/Bad 对比示例
Good: "auth.ts:47 returns undefined when the session cookie expires. Users hit a white screen. 
       Fix: add a null check and redirect to /login. Two lines."
Bad:  "I've identified a potential issue in the authentication flow that may cause problems 
       under certain conditions."

3. 17 个禁止词 + "no em dashes"
delve, crucial, robust, comprehensive, nuanced, multifaceted, furthermore, moreover, 
additionally, pivotal, landscape, tapestry, underscore, foster, showcase, intricate, 
vibrant, fundamental, significant.

4. 用户主权声明
"The user has context you do not: domain knowledge, timing, relationships, taste. 
 Cross-model agreement is a recommendation, not a decision. The user decides."

5. 模型行为修正层（subordinate to skill workflow）
6. Rationalization prevention + Honesty rule
```

**需要充实的 variant（按优先级）**：

1. `workflow` — Coordinator 是与用户沟通最多的角色。需要"业务语言"的正面示例 + Good/Bad 对
2. `execution` — 需要"直接、具体"的正面示例 + Good/Bad 对
3. `discovery` — 需要 Anti-Sycophancy Rules（见 §4.2）
4. `codex-reviewer` — 需要 Rationalization Prevention（见 §4.3）
5. 所有 variant — 补充禁止词：`crucial, additionally, pivotal, landscape, tapestry, underscore, foster, showcase, intricate, vibrant, fundamental, significant`

### 4.2 Anti-Sycophancy Rules（注入 `discovery` variant）

**现状**：discovery variant 只写了"探索性、问题优先。先暴露约束再提出方案。" 没有任何机制阻止 Coordinator 对用户的想法过度迎合。

**GStack 的原文**（直接适用于我们的 discovery 场景）：

```
Never say these during the diagnostic:
- "That's an interesting approach" — take a position instead
- "There are many ways to think about this" — pick one and state what evidence 
  would change your mind
- "You might want to consider..." — say "This is wrong because..." or "This works because..."
- "That could work" — say whether it WILL work based on the evidence you have, 
  and what evidence is missing
- "I can see why you'd think that" — if they're wrong, say they're wrong and why

Always:
- Take a position on every answer. State your position AND what evidence would change it.
- Challenge the strongest version of the user's claim, not a strawman.
```

**为什么重要**：Discovery 产出的设计文档是后续所有工作的基础。如果 Coordinator 在这个阶段对用户过度迎合，设计会遗漏关键约束，后面 Plan/Execution/Final Review 全部受影响。

### 4.3 Pre-emit Verification Gate（注入 `review-dispatch.md.tmpl`）

**现状**：review dispatch 模板（26 行）有 confidence 1-10 分桶和"bias indicators"要求，但**没有验证门槛**——reviewer 可以报告一个 confidence 8 的 finding 而不引用任何代码行。

**GStack 的 Pre-emit Verification Gate**：

```
Before any finding is promoted to the report, the gate requires:

1. Quote the specific code line that motivates the finding — file:line plus the verbatim 
   text of the line(s) that triggered it. If the finding is "field X doesn't exist on 
   model Y", quote the lines of class Y where the field would live. If "dict.get() might 
   return None", quote the dict initialization. If "race condition between A and B", 
   quote both A and B.

2. If you cannot quote the motivating line(s), the finding is unverified. Force its 
   confidence to 4-5 (suppressed from main report). It still goes into the appendix so 
   reviewers can audit calibration, but the user does NOT see it in the critical-pass 
   output. Do not work around this by inventing speculative confidence 7+ — that defeats 
   the gate.
```

配合 **Rationalization Prevention**：

```
"This looks fine" is not a finding. Either cite evidence it IS fine, or flag it as unverified.
```

和 **FP 类别表**（已验证能消灭的 false positive 类型）：

| FP 类别 | Gate 为什么能消灭它 |
|---------|-----------------|
| "field doesn't exist on model" | 要求引用 model class body 或 Meta；字段不存在会一目了然 |
| "dict.get() might be None" | 要求引用 dict 初始化（如 Django form 的 `cleaned_data` 是 `{}`） |
| "save() might lose fields" | 要求引用 ORM 签名或 model 定义 |
| "update_fields might miss X" | 要求引用 field set；如果 X 不存在，FP 不言自明 |

还有 **Framework Meta 特殊规则**：

```
When the symbol is generated by a framework metaclass, descriptor, ORM Meta inner-class, 
or migration history (Django Meta, Rails has_many/scope, SQLAlchemy relationship/Column, 
TypeORM decorators, Sequelize init/belongsTo, Prisma generated client), quote the 
meta-construct instead of expecting the literal name in the class body. The verification 
is "I read the source that creates this symbol", not "I grep'd for the name and didn't 
find it."
```

**为什么重要**：当前 Coordinator 收到 reviewer findings 后逐条亲验——如果 reviewer 本身的 FP 率高，Coordinator 花大量 context 在验证错误的 findings 上。在 reviewer 端加 gate 是从源头降噪。

### 4.4 Completion Status Protocol（改 `preamble.md.tmpl` + 各 agent 定义）

**现状**：Worker 返回有 verdict 字段（pass / blocked / needs repair / needs context），但**没有结构化的退出格式要求**。execution SKILL.md 定义了 worker verdict table，但 plan-writer（39 行）完全没有 return contract。

**GStack 做了什么**：

```
Every skill must end with one of four statuses:
- DONE — completed with evidence.
- DONE_WITH_CONCERNS — completed, but list concerns.
- BLOCKED — cannot proceed; state blocker and what was tried.
- NEEDS_CONTEXT — missing info; state exactly what is needed.

Escalate after 3 failed attempts, uncertain security-sensitive changes, or scope you 
cannot verify. Format: STATUS, REASON, ATTEMPTED, RECOMMENDATION.
```

加上 **Honesty Rule**：

```
Do NOT classify an item as DONE just because related code shipped. Code that *handles* 
a deliverable is not the deliverable. Shipping a markdown-extraction library is not the 
same as shipping the markdown file. When in doubt between DONE and UNVERIFIABLE, prefer 
UNVERIFIABLE — better to surface a confirmation prompt than silently miss a deliverable.
```

**落地优先级**：先给 plan-writer 补上 Return Contract（当前是 0）和 Self-Check，然后把 Honesty Rule 注入所有 agent 的 pre-delivery self-check。

## 5. Tier 3：流程健壮性

### 5.1 Confusion Protocol（注入 T2/T3 preamble）

**现状**：有 Stop/Continue 列表定义了"什么情况停"，但缺少"停的时候以什么格式向用户汇报"的标准动作。

**GStack**：

```
For high-stakes ambiguity (architecture, data model, destructive scope, missing context), 
STOP. Name it in one sentence, present 2-3 options with tradeoffs, and ask. 
Do not use for routine coding or obvious changes.
```

**落地位置**：注入 `preamble.md.tmpl` 的 T2/T3 变体，和 Decision Brief Protocol 配合——停下来时用 Decision Brief 格式向用户提问。

### 5.2 Calibration Learning 精确触发条件

**现状**：设计文档 §4a 列了 6 种 learning 写入事件，`learnings-confidence-audit.md` 有 bash 命令，但触发条件是叙述性的，没有精确的 if-then 规则。

**GStack**：

```
Calibration learning: If you report a finding with confidence < 7 and the user confirms 
it IS a real issue, that is a calibration event. Your initial confidence was too low. Log 
the corrected pattern as a learning so future reviews catch it with higher confidence.
```

**建议**：在 disposition 步骤中加入显式触发规则：
- confidence < 7 但 Coordinator 亲验后 accept → 写 calibration learning（"reviewer under-confidence on this pattern"）
- 同一 category 连续 3 条 reject → 写 reviewer-drift learning（"reviewer consistently wrong on this category"）
- confidence ≥ 8 但 Coordinator reject → 写 over-confidence learning（"reviewer confident but wrong"）

### 5.3 Adversarial Review Prompt 文本

**现状**：Final Review 有 review angles（regression + intent coverage + cross-plan integration + code-level），但没有"对抗性审查"的具体 prompt。

**GStack 的 Adversarial Subagent prompt**：

```
Think like an attacker and a chaos engineer. Your job is to find ways this code will 
fail in production. Look for: edge cases, race conditions, security holes, resource leaks, 
failure modes, silent data corruption, logic errors that produce wrong results silently, 
error handling that swallows failures, and trust boundary violations.

Be adversarial. Be thorough. No compliments — just the problems.

For each finding, classify as FIXABLE (you know how to fix it) or INVESTIGATE 
(needs human judgment).

After listing findings, end with ONE line:
Recommendation: <action> because <one-line reason naming the most exploitable finding>
```

和 **Cross-Model Tension 输出格式**：

```
CROSS-MODEL TENSION:
  [Topic]: Review said X. Outside voice says Y. 
  [Present both perspectives neutrally. 
   State what context you might be missing that would change the answer.]
```

**落地位置**：注入 `final-review-angles.md` 作为 Baseline 2 的一个 review dimension，或作为独立的 adversarial review pass。FIXABLE/INVESTIGATE 分类对 Coordinator disposition 直接有用。Cross-Model Tension 格式适用于 Coordinator 在 Claude-写/GPT-审之间发现矛盾时的结构化输出。

## 6. Tier 4：结构性建议（从现状分析得出，非 GStack 借鉴）

### 6.1 persona.md 应成为 Voice 唯一权威来源

两个 voice-directive bug（docs-worker 用了 Coordinator 人格、complex-code-explorer 用了 code-explorer 人格）+ persona.md 缺少 docs-worker = 双来源漂移的证据。

**建议**：persona.md 成为 SSOT，构建系统从 persona.md 为每个 agent 生成 voice-directive 块。agent 文件中不再手写 voice。这正是构建系统存在的意义——消除需要人记住"还有哪些文件引用了这个"的维护负担。

### 6.2 plan-writer agent 需要最低安全网

当前 39 行，是唯一没有 Return Contract 和 Self-Check 的 agent。pack-executor（157 行）有 Return Contract + Self-Check + Three-Failure Protocol + Pre-delivery Checklist。plan-writer 应至少有同等水平的内置安全网，不能把一切都依赖外部 methodology 文件传入。

### 6.3 maxTurns 边界行为未定义

code-explorer(20)、complex-code-explorer(30)、docs-worker(20)、root-cause-analyst(40) 都有 turn 上限，但没有任何一个定义了"接近 turn 上限时应该怎么做"——应该返回部分结果还是硬 BLOCKED。

**GStack 的 Context Health 指令**：

```
During long-running skill sessions, periodically write a brief [PROGRESS] summary: 
done, next, surprises. If you are looping on the same diagnostic, same file, or failed 
fix variants, STOP and reassess.
```

建议：在所有 turn-limited agent 中加入"当 turn 消耗超过 80% 时，返回当前结果 + 'partial: turn limit approaching'"的指令。

## 7. 明确不建议借鉴的部分

| GStack 特性 | 不借鉴理由 |
|---|---|
| 全量内联 3000 行 SKILL.md | 设计文档 §6.1 已拒绝——我们有构建系统实现等效效果 |
| Review Army 多 specialist 独立 dispatch | §6.4 已拒绝——我们的 reviewer 是单个 Codex 按 angles 全面审查，拆分会失去跨 angle 关联发现 |
| 完整 Dual Voice（双方独立生成 finding） | §6.3 已推迟——budget 不允许，用单向验证 + 偏差检测补偿 |
| 静默降级 `|| true` | §6.5 已拒绝——非技术用户不能承受静默失败 |
| Per-skill hook frontmatter | 不适配多进程模型——我们的 hooks 是全局的 |
| 跨机器 GBrain 同步 | 不在范围——我们是单项目单机器 |
| Jargon 术语表自动注入 | 用户是非技术人员，不需要 gloss 技术术语 |
| Specialist adaptive gating | 我们没有多 specialist 架构，且 §6.4 已拒绝 Review Army |
| Plan Mode Exception | Claude Code 的 plan mode 不是我们的控制流机制 |

## 8. GStack 关键源文件索引

以下是本报告引用的 GStack 源文件，供后续实施时参考：

| 文件 | 内容 |
|------|------|
| `ship/SKILL.md` (~3100 行) | 最大的 skill：20 步 workflow，Stop/Continue、Voice、Confidence Calibration 的最完整实例 |
| `review/SKILL.md` (~1789 行) | Review Army、specialist dispatch、Pre-emit Verification Gate、PR Quality Score |
| `SKILL.md` (root, ~47KB) | 路由表（40+ 规则），proactive invocation directives |
| `investigate/SKILL.md.tmpl` | Iron Law + 3-strike rule + 5-phase methodology |
| `office-hours/SKILL.md.tmpl` | Anti-Sycophancy Rules、Forcing Questions、Builder Mode |
| `ETHOS.md` | Boil the Lake, User Sovereignty |
| `scripts/resolvers/preamble.ts` | 20+ sub-generators，tier 1-4 composition |
| `scripts/resolvers/confidence.ts` | Pre-emit Verification Gate, FP class table |
| `scripts/resolvers/review-army.ts` | Specialist dispatch template, finding dedup, confidence boost |
| `scripts/gen-skill-docs.ts` | Template → SKILL.md pipeline, placeholder resolution, dry-run check |
| `bin/gstack-learnings-log` | Learnings schema, anti-injection patterns, trust marking |
| `bin/gstack-learnings-search` | Dedup, time-based decay, cross-project trust gate |

## 9. 语言适配备注

GStack 全英文，plugin-v2 主体中文。借鉴时需要翻译适配，但以下内容建议保留英文（AI 对英文指令的遵从度更高）：

- 禁止词列表（delve, robust, comprehensive...）
- Good/Bad 示例中的 code reference 部分
- Finding 格式标签（Confidence, Severity, Evidence, Category）
- Trust boundary 标记（BEGIN UNTRUSTED / END UNTRUSTED）
- Status 关键词（DONE, BLOCKED, NEEDS_CONTEXT）

角色描述、行为原则、Anti-Sycophancy 禁止句式建议用中文（与用户沟通的内容应与 plugin 主体语言一致）。

## 10. 优先级总结

按影响力排序的实施建议：

1. **Decision Brief Protocol** — 填补用户交互的格式空白（影响全部 6 个 phase）
2. **Voice Directive 充实** — 从 5 行/variant 提升到 15-20 行（影响全部 12 个 variant）
3. **Pre-emit Verification Gate** — 从源头降低 review FP（影响所有 review dispatch）
4. **plan-writer 安全网** — 从 39 行补到至少有 Return Contract + Self-Check
5. **Anti-Sycophancy** — 保护 Discovery 阶段的设计质量
6. **Completion Status Protocol** — 统一所有 agent 的退出格式
7. **Adversarial Review prompt** — 增强 Final Review 的审查深度
8. **Confusion Protocol** — 标准化歧义处理
9. **Calibration Learning 触发条件** — 让 learning 写入从描述性变为规则驱动
10. **Bug 修复** — docs-worker voice、complex-code-explorer voice、persona.md 补全
