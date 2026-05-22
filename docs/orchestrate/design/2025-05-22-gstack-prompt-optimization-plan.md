# GStack 提示词优化计划——基于独立核实后的实施方案

> **前置文档**: `2025-05-22-gstack-prompt-borrowing.md`（调研报告）, `2025-05-22-plugin-maturity.md`（成熟架构设计）
> **日期**: 2025-05-22
> **性质**: 调研报告的核实结果 + 独立优先级排序的实施计划

---

## 第一部分：调研报告核实结果

### 1.1 数字核实

| 报告声称 | 实际情况 | 判定 |
|---------|---------|------|
| Voice Directive "12 个变体共 61 行" | **14 个变体共 71 行**（8 个 agent variant + 6 个 skill variant）。每个 variant 实际只有 2 行内容（1 行角色描述 + 1 行禁止词），外加 3 行标记/空行 | **部分准确**——数量和行数均有误差（12→14, 61→71），但"每个 ~5 行、内容稀薄"的核心判断成立，实际内容密度比报告描述的更低（2 行实质内容 vs 报告说的 5 行） |
| "禁止词 7 个" | 确认 7 个：delve, robust, comprehensive, nuanced, multifaceted, furthermore, moreover | **准确** |
| "全系统 0 处 Good/Bad 示例" | grep 搜索所有 SKILL.md、agent 定义、reference 文件和模板，未找到任何 Good/Bad 示例对 | **准确** |
| "用户可见输出格式只有 4 处" | 实际有 **5 处**：(1) Direction Check 信息化模板, (2) 设计文档确认一句话, (3) Business Report 四段式, (4) PR body 模板, (5) BLOCKED 双层报告格式。报告遗漏了 BLOCKED 格式（已定义在 workflow 和 execution 两个 SKILL.md 中）。不过报告本身在 §3.1 也提到了 BLOCKED 格式的存在，只是没计入"4 处"的统计 | **部分准确**——4→5，报告自身有自相矛盾 |
| "BLOCKED 格式只在 workflow 和 execution 两个 SKILL.md 中定义，discovery / plan-writing / final-review / multi-pr-merge 四个 phase 的 BLOCKED 格式完全缺失" | 确认。这 4 个 skill 只写了"BLOCKED 报告用户"但无格式定义 | **准确** |
| GStack "17+ 个禁止词" | 实际 19 个 + "no em dashes" 规则。完整列表：delve, crucial, robust, comprehensive, nuanced, multifaceted, furthermore, moreover, additionally, pivotal, landscape, tapestry, underscore, foster, showcase, intricate, vibrant, fundamental, significant | **准确**（"17+"是保守表述） |
| Decision Brief "11 项自检清单" | GStack 源文件 `generate-ask-user-format.ts` 确认只有 **10 项**。报告列出的清单也只有 10 个 bullet point。报告文本写"11 项"是内部不一致 | **不准确**——应为 10 项 |
| "GStack 单个 skill 的 Voice 段有 ~30 行" | GStack ship/SKILL.md 的 Voice 段包含 6 条正面原则 + Good/Bad 示例 + 19 个禁止词 + "no em dashes" + 用户主权声明 + 模型行为修正层 + Rationalization prevention + Honesty rule，合计约 25-35 行 | **准确** |
| plan-writer.md 39 行 | 确认 39 行 | **准确** |
| pack-executor.md 157 行 | 确认 157 行 | **准确** |

### 1.2 Tier 0 Bug 核实

| Bug | 当前状态 | 判定 |
|-----|---------|------|
| docs-worker voice-directive 注入了 Coordinator 人格 | **已修复**。当前 `docs-worker.md` 行 74 标记为 `variant=docs-worker`，注入内容是"你是文档整理员"，正确 | 已修复 |
| complex-code-explorer voice-directive 注入了错误变体 | **已修复**。当前 `complex-code-explorer.md` 行 68 标记为 `variant=complex-code-explorer`，注入内容是"你是多模块调查员"，正确 | 已修复 |
| persona.md 缺少 docs-worker | **已修复**。当前 persona.md 覆盖 8 个角色，包括 docs-worker（行 38-41） | 已修复 |

### 1.3 GStack 引用核实

| 引用内容 | 核实结果 | 判定 |
|---------|---------|------|
| Decision Brief Protocol 格式 | GStack review/SKILL.md 确认存在完整格式（D<N>、ELI10、Stakes、Recommendation、Pros/cons、Net），与报告引用一致 | **准确** |
| 自检清单内容 | 10 项内容逐条匹配，包括 Completeness scored、Dual-scale effort labels、Non-ASCII 等。报告原文标注"11 项"但实际列出 10 项 | **内容准确，数量标注错误** |
| Pre-emit Verification Gate 正文 | GStack confidence.ts 和 review/SKILL.md 双重确认：quote motivating line → cannot quote → force confidence 4-5 → appendix only。与报告引用完全一致 | **准确** |
| FP 类别表（4 个类别） | GStack 确认 4 个 FP 类别：field doesn't exist / dict.get() might be None / save() might lose fields / update_fields might miss X。与报告一致 | **准确** |
| Framework Meta 特殊规则 | GStack 确认：quote meta-construct 而非 grep literal name，列举 Django Meta / Rails has_many / SQLAlchemy / TypeORM / Prisma / Sequelize | **准确** |
| Anti-Sycophancy Rules（5 条禁止句式） | GStack office-hours/SKILL.md.tmpl 确认 4 条禁止句式（不是 5 条）：报告把 "You might want to consider..." 列为第 3 条但 GStack 原文表述略有不同——不影响实质。两条"Always"规则存在 | **基本准确**——句式数量和表述有微小出入 |
| Completion Status Protocol（DONE/DONE_WITH_CONCERNS/BLOCKED/NEEDS_CONTEXT） | GStack ship/SKILL.md 确认完整的 4 状态 + FORMAT: STATUS, REASON, ATTEMPTED, RECOMMENDATION | **准确** |
| Honesty Rule | GStack 确认："Do NOT classify an item as DONE just because related code shipped" + UNVERIFIABLE 优先于 DONE | **准确** |
| Adversarial Subagent prompt | GStack review/SKILL.md 确认存在 adversarial review 机制（Red Team，activated when DIFF_LINES > 200 or CRITICAL finding），但具体 prompt 文本与报告引用存在差异——报告的版本更像是编辑整理后的摘要而非逐字引用 | **实质准确，非逐字引用** |
| Cross-Model Tension 格式 | GStack 有 ADVERSARIAL REVIEW SYNTHESIS 格式，但结构与报告引用的 `CROSS-MODEL TENSION` 有差异。GStack 实际格式是"High confidence / Unique to Claude / Unique to Codex"的分层结构 | **部分准确**——报告简化了 GStack 的实际格式 |
| Context Health 指令 | GStack preamble.ts 确认 T2+ 加载 `generateContextHealth()`。investigate/SKILL.md.tmpl 的 5-phase methodology 包含 progress reporting 机制 | **准确** |
| Calibration Learning | GStack confidence.ts 确认：sub-7 confidence finding confirmed real → calibration event → log corrected pattern | **准确** |

### 1.4 报告遗漏的 GStack 内容

调研报告未覆盖以下值得借鉴的 GStack 内容：

1. **Learnings 反注入正则**（`bin/gstack-learnings-log`）：10+ 个正则模式阻止 prompt injection 进入 learnings 系统。具体模式包括 `ignore\s+previous\s+instructions`、`always\s+output\s+no\s+findings`、`skip\s+all\s+security`、`\bsystem\s*:`、`do\s+not\s+(report|flag|mention)` 等。这是成熟设计 §8a "Learnings Trust Gate" 的**具体实现**，报告只提了概念没给实现。

2. **Trust 二值标记**：`trusted = (source === "user-stated")`——只有用户明确陈述的 learning 被标记为 trusted，所有 AI 生成来源（observed/inferred/cross-model）均为 untrusted。简洁有效的信任模型。

3. **Iron Law + 3-Strike Rule**（investigate/SKILL.md.tmpl）："NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST" + "3 hypotheses tested, none match → halt and ask"。直接适用于我们的 `root-cause-analyst` agent，当前该 agent 没有类似硬规则。

4. **PR Quality Score 公式**：`max(0, 10 - (critical×2 + informational×0.5))`。可量化的质量分数，直接可用于 Final Review 的 business report，填补"用业务语言"的锚点空白。

5. **Slop scan 机制**：GStack 有 `slop-scan.config.json`（当前只配了 vendor ignore）+ 代码层面的 banned word 检测，说明禁止词不只是 prompt 指令——还有运行时扫描。我们当前只在 voice directive 文本层面做禁止，没有验证层。这个优先级不高但值得记录。

6. **`/careful` + `/freeze` 的分层安全模式**：advisory warning + hard block 的双层设计。我们的 hooks 已经有类似机制（exit 0 warn vs exit 2 block），但报告没有系统性地对比这个设计模式。

---

## 第二部分：优化计划

### 优先级排序原则

- 填补成熟设计文档 9 个承诺中**已规划但缺少具体内容**的条目 > 新增文档未规划的功能
- 用户可见体验改善 > AI 内部行为控制 > 流程健壮性
- 复用已有构建系统管道（resolver + template）> 新建管道
- 每个优化项必须映射到成熟设计的具体承诺

### 基础设施就绪状态

经核实，以下目标文件**已存在于当前分支**（成熟架构实施 R3 的产物）：
- `plugin-v2/build/templates/voice-directive.md.tmpl` -- 已有 14 个 variant
- `plugin-v2/build/templates/review-dispatch.md.tmpl` -- 已有 review 模板
- `plugin-v2/build/templates/preamble.md.tmpl` -- 已有 T1-T3 preamble
- `plugin-v2/build/resolvers/*.sh` -- 10 个 resolver 已就位
- `plugin-v2/scripts/state.sh` -- 25KB，已实现统一状态机
- `plugin-v2/scripts/learnings-jsonl.sh` -- learnings 读写已实现

因此以下所有 P 项均为**立即可做**——不需要等待其他承诺先完成。唯一的新建文件是 P1 的 `decision-brief.md.tmpl`。

---

### P1: Decision Brief Protocol（新建模板）

**映射承诺**: §3.7 "BLOCKED 对非技术用户不再是黑洞" + §5b "Direction Check 信息化"

**目标文件**: `plugin-v2/build/templates/decision-brief.md.tmpl`（新建）

**变更内容**:

创建 Decision Brief 模板，由构建系统注入到所有需要 AskUserQuestion 的位置。模板内容适配我们的场景（中文 + 非技术用户）：

```markdown
D<N> — <一行问题标题>
背景：<当前在做什么，1 句话>
通俗说明：<用非技术语言说清利害关系，2-4 句>
选错的后果：<一句话>
建议：<推荐选项> 因为 <一行理由>
各选项对比：
A) <选项> (推荐)
  优势：<具体可观测的好处，40 字以上>
  代价：<真实可观测的代价，40 字以上>
B) <选项>
  优势：...
  代价：...
总结：<一句话总结本质上在交换什么>
```

配套 10 项自检清单（依据 GStack 源码确认的实际数量）：

```markdown
发出 AskUserQuestion 前自检：
- [ ] D<N> 标题行存在
- [ ] 通俗说明段存在（含"选错的后果"行）
- [ ] 建议行存在且有具体理由
- [ ] 每个选项至少 2 个优势 + 1 个代价，各 ≥40 字符
- [ ] 有且仅有一个选项标注"(推荐)"
- [ ] 涉及工作量的选项标注双尺度：(人工: ~X / Claude Code: ~Y)
- [ ] 总结行关闭决策
- [ ] 你在调用 AskUserQuestion 工具，不是在写散文
- [ ] 非 ASCII 字符（中文/日文/重音）直接写，不用 \u 转义
- [ ] 问题是真正需要用户判断的业务决策，不是技术实现细节
```

**注意**：第 10 条是我们新增的（GStack 原版没有），因为我们的全局规范要求"只暴露业务决策，技术实现细节自己判断不反问"。

**注入位置**（由 resolver 生成注入标记）:
- 所有 6 个 SKILL.md 的 BLOCKED 输出点
- `direction-check.md` 的用户交互点
- `plan-review-resolution.md` 的 user decision disposition 点
- `discovery` SKILL.md 的设计方向确认点

**预期效果**: 所有用户交互从散文式变为结构化，非技术用户在任何 phase 的 BLOCKED 点都能做出有信息的决策。

**风险**: 格式过于刚性可能导致简单问题也被强制填充冗长模板。缓解：加"快速问题逃逸"规则——只有 2 个以上选项或涉及工作量/时间/功能取舍时才要求完整 Decision Brief，是/否问题可简化。

---

### P2: Voice Directive 充实（改现有模板）

**映射承诺**: §4d "Persona + Voice Directive"

**目标文件**: `plugin-v2/build/templates/voice-directive.md.tmpl`

**变更内容**:

采用**分层扩充**策略，不盲目把所有 14 个 variant 都扩展到 15-20 行。理由：我们的 SKILL.md 平均 ~150 行，GStack 的 3000 行 SKILL.md 中放 30 行 Voice 只占 1%，我们放 20 行占 13%——占比过高。

| Variant 层级 | 适用 Variant | 目标行数 | 扩充内容 |
|-------------|-------------|---------|---------|
| **Coordinator 层**（与用户直接沟通） | workflow, discovery, execution, plan-writing, final-review, multi-pr-merge | 12-15 行 | +正面行为原则（3-4 条） +Good/Bad 示例对 +完整禁止词 |
| **Worker 层**（与 Coordinator 沟通） | pack-executor, complex-pack-executor, plan-writer, docs-worker | 8-10 行 | +Good/Bad 示例对 +完整禁止词 |
| **调查员层**（只返回证据） | code-explorer, complex-code-explorer, root-cause-analyst, codex-reviewer | 8-10 行 | +Good/Bad 示例对 +完整禁止词 |

具体扩充内容（以 `workflow` variant 为例）：

```markdown
[variant=workflow]
你是 Coordinator——项目的中枢调度者。你不写代码，你编排。对用户用业务语言（进展、风险、决策点），对 sub-agent 用精确技术指令。每个决策有 evidence，不凭直觉。

行为原则：
- 先说结论再说过程。用户需要知道"发生了什么、影响什么、下一步什么"。
- 用具体数字和文件名。"3 个 Pack 完成，2 个待修复，预计还需 4 次 review" 好过 "进展顺利"。
- 技术选择关联用户影响："选 A 方案用户登录快 2 秒，选 B 方案省 3 天开发时间"。

Good: "用户现在可以用手机号登录，15 秒内完成。之前只支持邮箱，平均 45 秒。"
Bad:  "实现了 PhoneAuthProvider 并集成到 AuthStrategy pipeline，通过 TDD 验证了 happy path 和 edge cases。"

禁止词：delve, crucial, robust, comprehensive, nuanced, multifaceted, furthermore, moreover, additionally, pivotal, landscape, tapestry, underscore, foster, showcase, intricate, vibrant, fundamental, significant. No em dashes.
[/variant]
```

**禁止词扩充**（全局）：从 7 个扩展到 19 个 + "no em dashes" 规则，与 GStack 对齐。新增 12 个：crucial, additionally, pivotal, landscape, tapestry, underscore, foster, showcase, intricate, vibrant, fundamental, significant。

**预期效果**: AI 产出从"勉强避免最差表现"（7 个禁止词）升级到"有明确的好/坏标杆"（正面原则 + 示例对 + 19 个禁止词）。

**风险**: 过长的 voice directive 可能被 AI 在长 context 中降低优先级。缓解：Coordinator 层的 voice 放在 preamble 顶部（高优先级位置），Worker/调查员层相对简短。

---

### P3: Pre-emit Verification Gate（改 review dispatch 模板）

**映射承诺**: §3a "Finding 结构化" + §3b-2 "Coordinator 亲验纪律"

**目标文件**: `plugin-v2/build/templates/review-dispatch.md.tmpl`（或由 `review-dispatch.sh` resolver 生成的等效内容）

**变更内容**:

在 review prompt 模板中 confidence 1-10 分桶之后，追加 Verification Gate 规则：

```markdown
## Pre-emit Verification Gate

每个 finding 必须满足以下条件才能进入报告：

1. **引用触发 finding 的具体代码行**——file:line + 该行的原始文本。
   - "field X doesn't exist on model Y" → 引用 class Y 的定义体，证明字段缺失
   - "dict.get() might return None" → 引用 dict 的初始化代码
   - "race condition between A and B" → 引用 A 和 B 两处代码

2. **无法引用 = finding 未验证**。将 confidence 强制设为 4-5（从主报告中抑制，移入附录）。
   不要通过虚构 confidence 7+ 来绕过此门槛。

3. **框架元编程特例**：当符号来自 ORM 元类、装饰器、migration 历史时（Django Meta、Rails has_many、SQLAlchemy relationship、TypeORM decorators、Prisma generated client），引用生成该符号的元构造，而非期望在类体中 grep 到字面名称。

## Rationalization Prevention

- "This looks fine" 不是 finding。要么引用证据证明它确实没问题，要么标记为未验证。
- "likely handled elsewhere" → 读并引用处理代码，或标记 unknown。
- "probably tested" → 给出测试文件和方法名，或标记 unknown。
```

同时追加 **FP 类别表**：

| FP 类别 | Gate 为什么能消灭它 |
|---------|-----------------|
| "field doesn't exist on model" | 要求引用 model class body；字段不存在一目了然 |
| "dict.get() might be None" | 要求引用 dict 初始化 |
| "save() might lose fields" | 要求引用 ORM 签名或 model 定义 |
| "update_fields might miss X" | 要求引用 field set |

**预期效果**: Reviewer（Codex GPT）的 FP 率从源头降低，Coordinator 花在验证错误 finding 上的 context 减少。

**风险**: GPT 可能不严格遵循引用要求而编造 line number。缓解：Coordinator 亲验仍是最后防线（§3b-2 不变），Gate 是降低亲验工作量的第一层过滤。

---

### P4: Anti-Sycophancy Rules（注入 discovery variant）

**映射承诺**: §4d Voice Directive（discovery 场景）

**目标文件**: `plugin-v2/build/templates/voice-directive.md.tmpl`（discovery variant 区块）

**变更内容**:

在 discovery variant 中追加 Anti-Sycophancy 规则。中文化适配（用户沟通语言一致性）：

```markdown
[variant=discovery]
你是产品设计引导者。探索性、问题优先。先暴露约束再提出方案。对用户用业务语言，对技术判断给出 evidence 支撑的 trade-off 分析。

Anti-Sycophancy——诊断阶段禁止说：
- "这个想法很有趣" — 给出明确立场
- "有很多方式可以考虑" — 选一个，说明什么证据会改变你的判断
- "你可以考虑..." — 直接说"这行不通因为..."或"这可行因为..."
- "这应该可以" — 基于现有证据说它到底行不行，缺什么证据
- "我理解你为什么这样想" — 如果用户错了，直接说错在哪

始终：
- 对每个回答给出明确立场 + 什么证据会改变这个立场
- 质疑用户主张的最强版本，不是稻草人

Good: "这个方案的核心假设是用户愿意多走一步验证——但你的数据显示 60% 的用户在第二步就流失。建议先做 A/B 测试验证这个假设。"
Bad:  "这是一个有趣的方向！我们可以从多个角度来探索这个可能性。"

禁止词：delve, crucial, robust, comprehensive, nuanced, multifaceted, furthermore, moreover, additionally, pivotal, landscape, tapestry, underscore, foster, showcase, intricate, vibrant, fundamental, significant. No em dashes.
[/variant]
```

**预期效果**: Discovery 阶段产出的设计文档质量提升——Coordinator 不会因为迎合用户而遗漏关键约束。

**风险**: GStack 的 Anti-Sycophancy 规则来自 `/office-hours` skill——面向的是创始人的产品战略诊断。我们的 discovery 场景面向的是非技术项目负责人。禁止句式列表（"这个想法很有趣"、"我理解你为什么这样想"等）在这个受众面前可能显得对抗性过强。

缓解方案：**保留"Always"规则和 Good/Bad 锚点（这是核心价值），"Never say"列表标记为建议性而非强制性**。实际落地前需要用户确认：4 条禁止句式的语气是否适合当前项目的沟通风格。如果用户觉得过于生硬，可以只保留 2 条 Always 规则 + Good/Bad 示例，去掉 Never say 列表。

---

### P5: Learnings 反注入 + Trust Gate（新建脚本逻辑）

**映射承诺**: §8a "Learnings Trust Gate"

**目标文件**: `plugin-v2/scripts/state.sh`（learnings 写入函数）

**变更内容**:

在 learnings 写入路径中加入 GStack 已验证的反注入正则扫描。具体模式（从 GStack `bin/gstack-learnings-log` 借鉴）：

```bash
INJECTION_PATTERNS=(
  'ignore\s+(all\s+)?previous\s+(instructions|context|rules)'
  'you\s+are\s+now\s+'
  'always\s+output\s+no\s+findings'
  'skip\s+(all\s+)?(security|review|checks)'
  'override[:\s]'
  '\bsystem\s*:'
  '\bassistant\s*:'
  '\buser\s*:'
  'do\s+not\s+(report|flag|mention)'
  'approve\s+(all|every|this)'
)
```

Trust 标记逻辑：
```bash
# source 字段决定 trust
if [ "$source" = "user-stated" ]; then
  trusted=true
else
  trusted=false  # observed, inferred, cross-model
fi
```

**预期效果**: 防止恶意仓库代码通过 learnings 系统投毒后续 workflow 运行。

**风险**: 正则过于宽泛可能误杀合法 learning 内容（比如讨论注入防御的 learning 本身会包含这些词）。缓解：扫描范围限定在 `insight` 字段，不扫 `tags`/`files` 等结构化字段；误杀时 exit 1 + 明确报错信息，Coordinator 可以重写措辞后重试。

---

### P6: plan-writer 安全网（改 agent 定义）

**映射承诺**: 无直接映射——这是调研报告发现的结构性缺陷，属于基础质量提升

**目标文件**: `plugin-v2/agents/plan-writer.md`

**变更内容**:

从当前 39 行扩展到 ~80 行，补充：

1. **Return Contract**（参照 pack-executor.md 的格式）：
```markdown
## Return Contract

返回时必须包含以下结构化区块：

### Verdict
pass | needs revision | blocked

### Plan Summary
- Plan 编号
- Pack 总数 + 每个 Pack 的一句话摘要
- 总预估 review 次数

### Open Items
对每个发现标注 [out-of-scope] | [needs-evaluation]

### Self-Check 完成状态
<勾选以下清单后才能返回 pass>
```

2. **Self-Check 清单**：
```markdown
## Pre-delivery Self-Check

- [ ] 每个 Pack 有 Owned files（明确的文件范围）
- [ ] 每个 Pack 有 Acceptance criteria（可验证的完成标准）
- [ ] 每个 Pack 有 Verification commands（机械化检验命令）
- [ ] Pack 间依赖关系已标注（blocked_by 字段）
- [ ] 没有"后续处理"、"待定"、"TBD"措辞——每个不确定项要么在 Open Items 中标注，要么在 Pack 中具体化
- [ ] Plan 中引用的所有文件路径在仓库中存在（通过 Glob 验证）
```

3. **Three-Failure Protocol**：
```markdown
## Three-Failure Protocol

连续 3 次 revision 未通过 Plan Review → 停止修订，返回 blocked + 完整的 3 轮 revision 历史。不做第 4 次尝试。
```

**预期效果**: plan-writer 从"完全依赖外部 methodology 文件"变为"有内置安全网 + 外部 methodology 提供领域指导"。

**风险**: 扩充后的 agent 定义可能与 Coordinator dispatch 时传入的 methodology 文件有冲突或重复。缓解：plan-writer.md 中的 Return Contract 和 Self-Check 是**结构要求**（格式层面），methodology 文件是**内容指导**（怎么拆 Pack、怎么写 criteria 等），两者互补不冲突。

---

### P7: root-cause-analyst Iron Law + 3-Strike（改 agent 定义）

**映射承诺**: 无直接映射——从 GStack investigate/SKILL.md.tmpl 借鉴的新增内容

**目标文件**: `plugin-v2/agents/root-cause-analyst.md`

**变更内容**:

追加 Iron Law 和 3-Strike 规则：

```markdown
## Iron Law

NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST. 修症状会制造"打地鼠"式调试——每个创可贴让下一个 bug 更难定位。每个修复必须定位到真实根因。

## 3-Strike Rule

连续 3 个假设被证伪后，停止继续猜测。返回 blocked + 已排除的 3 个假设 + 收集到的证据 + 建议下一步方向。

Red flags（出现以下信号时立即停止当前方向）：
- "先临时修一下" — 没有"临时"修复，要么修根因要么上报
- 提出修复方案但还没追踪完数据流 — 那是猜测不是诊断
- 每次修复都暴露新问题 — 说明在错误的层面操作
```

**预期效果**: RCA agent 行为更加纪律化，减少在错误方向上消耗 turn 的概率。

**风险**: 无显著风险。这些规则与 RCA agent 的现有角色定义（"列 falsifiable hypotheses，逐个验证"）完全一致，是具体化而非方向改变。

---

### P8: Business Report Good/Bad 锚点（改 reference 文件）

**映射承诺**: §4c "失败报告双层化" + §4d "Persona + Voice Directive"

**目标文件**: `plugin-v2/skills/orchestrate-final-review/references/final-review-completion.md`（Step 19 区域）

**变更内容**:

在 Business Report 四段式模板（Steps 19a-19d）之后追加 Good/Bad 锚点：

```markdown
### 业务报告写作锚点

Good:
> **新增能力**：用户现在可以用手机号登录，15 秒内完成。之前只支持邮箱，平均 45 秒。
> **验证证据**：注册→登录→访问首页全流程测试通过（verification commands 输出附后）。
> **残余风险**：海外手机号格式未覆盖，影响 ~5% 用户。已开 issue #42 跟踪。

Bad:
> **新增能力**：实现了 PhoneAuthProvider 并集成到 AuthStrategy pipeline。
> **验证证据**：TDD red-green-refactor 完成，所有 23 个 test case 通过。
> **残余风险**：需要进一步测试边界条件。
```

同时追加 **PR Quality Score**（从 GStack 借鉴）作为 business report 的可量化指标：

```markdown
### Quality Score（附在业务报告末尾）

quality_score = max(0, 10 - (critical_count × 2 + informational_count × 0.5))

示例：
- 0 critical + 3 informational → 8.5/10
- 1 critical + 2 informational → 7.0/10
- 3 critical → 4.0/10
```

**预期效果**: Business report 从"看 AI 心情"变为"有明确的好/坏标杆和可量化分数"。

**风险**: Quality Score 公式过于简单可能不反映实际代码质量。缓解：Score 定位为"辅助参考"而非"通过/不通过门槛"，只用于帮助非技术用户理解代码审查结论的严重程度。

---

### P9: Completion Status Protocol（改 agent preamble）

**映射承诺**: §4d "Persona + Voice Directive"（标准化退出）

**目标文件**: `plugin-v2/build/templates/preamble.md.tmpl`（或由 preamble.sh resolver 注入）

**变更内容**:

在 T2/T3 preamble 中加入统一退出状态要求：

```markdown
## 退出状态协议

每次返回必须以以下四种状态之一开头：

- **DONE** — 已完成，附证据
- **DONE_WITH_CONCERNS** — 已完成但有顾虑，列出顾虑
- **BLOCKED** — 无法继续，说明阻塞原因和已尝试的方案
- **NEEDS_CONTEXT** — 缺少信息，精确说明需要什么

格式：STATUS, REASON, ATTEMPTED, RECOMMENDATION

Honesty Rule：不要仅因为相关代码已提交就标记 DONE。处理某个交付物的代码不等于交付物本身。不确定时优先标记 NEEDS_CONTEXT 而非 DONE——多问一句好过静默遗漏。
```

**注意**：当前 pack-executor 已有 verdict table（pass/needs repair/blocked/needs context），plan-writer 没有。此变更是**统一格式**而非新增——现有 verdict 语义不变，加了标准化退出格式和 Honesty Rule。

**预期效果**: 所有 agent 返回的格式一致，Coordinator 解析更可靠；Honesty Rule 防止 agent 过度乐观。

**风险**: 低。现有 verdict 已覆盖大部分语义，这是格式统一和 Honesty Rule 增补。

---

### P10: maxTurns 边界行为（改 agent 定义）

**映射承诺**: 无直接映射——调研报告 §6.3 发现的缺陷

**目标文件**: 所有有 maxTurns 的 agent 定义：`code-explorer.md`(20), `complex-code-explorer.md`(30), `docs-worker.md`(20), `root-cause-analyst.md`(40)

**变更内容**:

在每个 agent 定义中追加：

```markdown
## Turn Budget 意识

当消耗超过总 turn 预算的 80% 时（即距离 maxTurns 剩余 ≤20%），立即返回当前已有结果 + 状态标记 `partial: turn limit approaching`。不要在最后几个 turn 尝试"快速完成"——返回部分结果让 Coordinator 决定是否 re-dispatch 比硬撞 turn 上限后丢失所有上下文更有价值。
```

**预期效果**: Agent 不会在 turn 上限处突然中断导致结果丢失。

**风险**: Agent 可能过早返回（80% 阈值可能过于保守）。缓解：80% 是 GStack 的 Context Health 机制的常见阈值，且"返回部分结果"比"硬截断"更安全。

---

### P11: Calibration Learning 精确触发条件（改 learnings 相关 reference）

**映射承诺**: §4a "Learnings JSONL"

**目标文件**: `plugin-v2/skills/orchestrate-execution/references/learnings-confidence-audit.md`

**变更内容**:

将当前叙述性的触发条件改为 if-then 规则：

```markdown
## Calibration Learning 触发规则

| 条件 | 动作 | Learning 类型 |
|------|------|-------------|
| Finding confidence < 7 但 Coordinator 亲验后 accept | 写入 calibration learning："reviewer under-confidence on this pattern" | review-calibration |
| Finding confidence ≥ 8 但 Coordinator reject | 写入 over-confidence learning："reviewer confident but wrong on [category]" | review-calibration |
| 同一 category 连续 3 条 reject | 写入 reviewer-drift learning："reviewer consistently wrong on [category]" | reviewer-drift |
| Worker 返回 needs repair（首次 dispatch 未通过） | 写入 repair-pattern learning | repair-pattern |
| Worker 修改了 owned files 之外的文件 | 写入 scope-drift learning | scope-drift |
```

**预期效果**: Learning 写入从"Coordinator 酌情判断"变为"规则驱动"，校准数据积累更一致。

**风险**: 规则可能产出过多低价值 learning（尤其是 repair-pattern 类型）。缓解：加载时的 time-based decay（§4a 已规划）会自然清理过时 learning。

---

### 不纳入计划的调研报告建议

| 报告建议 | 不纳入理由 |
|---------|----------|
| **persona.md 成为 Voice 唯一权威来源（§6.1）** | 成熟设计 §4d 已规划 `voice-directive.sh` resolver 从 .tmpl 模板生成 voice。persona.md 应作为 resolver 的**输入规格**（角色定义），voice-directive.md.tmpl 是**内容模板**，两者通过构建系统关联。不需要额外的 SSOT 机制——构建系统本身就是 SSOT 的保证。如果 persona.md 和 voice-directive.md.tmpl 出现漂移，`build.sh --check` 就会报错 |
| **Confusion Protocol 注入 T2/T3 preamble（§5.1）** | P1 的 Decision Brief Protocol 已覆盖这个需求——"停下来时用 Decision Brief 格式向用户提问"就是 Confusion Protocol 的具体实现形式。不需要独立的 Confusion Protocol 条目 |
| **Adversarial Review 作为独立 review pass（§5.3）** | 成熟设计 §3 已有 4 个 review angle（regression + intent coverage + cross-plan + code-level）。增加独立的 adversarial pass 意味着额外的 Codex dispatch（budget 消耗），且当前架构是"单个 Codex 按 angles 全面审查"（§6.4 已拒绝 Review Army）。替代方案：将 adversarial 语气（"think like an attacker"）融入现有 code-level review angle 的 prompt 中，不新增 dispatch。FIXABLE/INVESTIGATE 分类可以加入现有 finding 的 Category 字段 |
| **Cross-Model Tension 输出格式（§5.3）** | 当前架构是单向验证（Codex 审 → Coordinator 亲验），不是双向独立生成。Cross-Model Tension 格式预设了"两个 AI 各自独立产出 finding 后比对"的场景。成熟设计 §6.3 已将完整 Dual Voice 推迟。如果后续启用 Dual Voice，再引入此格式 |
| **Calibration Learning 中的 reviewer-drift 连续 3 条 reject 规则（§5.2 的第二条）** | 纳入了——见 P11。但注意：报告建议的"同一 category 连续 3 条 reject"在实践中很难在单次 workflow 内触发（一次 review 通常不会在同一 category 产出 3 条 finding）。这个规则更适合**跨 run 统计**。P11 保留了这条规则但应将"连续"改为"累计近 5 次 run 中同一 category 3 条 reject" |

---

## 第三部分：核实摘要

### 逐条核实结论

| 序号 | 调研报告声称 | 结论 |
|------|------------|------|
| 1 | Voice Directive "12 个变体共 61 行" | **部分准确**——实际 14 个变体共 71 行，核心判断（内容稀薄）成立 |
| 2 | 禁止词 7 个 | **准确** |
| 3 | GStack 17+ 个禁止词 | **准确**（实际 19 个 + no em dashes） |
| 4 | 全系统 0 处 Good/Bad 示例 | **准确** |
| 5 | 用户可见输出格式只有 4 处 | **部分准确**——实际 5 处（遗漏了 BLOCKED 双层格式），报告自身内容有矛盾 |
| 6 | BLOCKED 格式在 4 个 phase 缺失 | **准确** |
| 7 | Decision Brief "11 项自检清单" | **不准确**——GStack 源码确认 10 项，报告自己列出的也是 10 项 |
| 8 | Decision Brief 格式内容 | **准确**——与 GStack review/SKILL.md 逐项匹配 |
| 9 | Pre-emit Verification Gate 内容 | **准确**——与 GStack confidence.ts 和 review/SKILL.md 双重匹配 |
| 10 | FP 类别表（4 类） | **准确** |
| 11 | Framework Meta 特殊规则 | **准确** |
| 12 | Anti-Sycophancy Rules（5 条禁止句式） | **基本准确**——GStack 原文有 4 条禁止句式 + 2 条 Always 规则，报告表述略有出入但实质正确 |
| 13 | Completion Status Protocol | **准确** |
| 14 | Honesty Rule | **准确** |
| 15 | Adversarial Subagent prompt | **实质准确**——报告版本是编辑摘要而非逐字引用 |
| 16 | Cross-Model Tension 格式 | **部分准确**——GStack 实际格式与报告引用有差异 |
| 17 | Tier 0 Bug: docs-worker voice | **已修复**（报告写作时存在，现已修正） |
| 18 | Tier 0 Bug: complex-code-explorer voice | **已修复** |
| 19 | Tier 0 Bug: persona.md 缺 docs-worker | **已修复** |
| 20 | plan-writer 39 行 / pack-executor 157 行 | **准确** |
| 21 | GStack Context Health 指令 | **准确** |
| 22 | GStack Calibration Learning 触发 | **准确** |

### 报告整体质量评价

**总体评级：B+（良好，有小瑕疵）**

**优点**：
- 对比分析的框架设计出色——按维度对照（Voice/禁止词/Good-Bad/格式/Confidence/退出协议/Anti-Sycophancy/Review 校准）使差距一目了然
- GStack 核心内容的引用实质准确，没有断章取义或歪曲原意
- 优先级排序合理（用户可见体验 > AI 行为控制 > 流程健壮性）
- "明确不建议借鉴的部分"（§7）展示了独立判断力，没有盲目搬运
- Tier 0 Bug 的发现有价值（虽然已修复，但能发现说明通读了全部文件）

**瑕疵**：
- 数字不精确：variant 数量（12→14）、行数（61→71）、自检清单数量（11→10）、用户可见格式数量（4→5）
- 部分 GStack 引用是编辑整理版而非原文，但标注为"原文"（如 Adversarial Subagent prompt、Cross-Model Tension）
- 遗漏了 GStack 中几个有实操价值的内容（反注入正则、Trust 二值标记、Iron Law + 3-Strike、PR Quality Score）
- 报告内部有矛盾：§3.1 提到 BLOCKED 格式存在但统计时没计入"4 处"

**总结**：报告的核心判断——"架构已到位，内容密度不够"——是准确的。GStack 引用的实质内容经核实可信。数字上的误差不影响结论方向。作为优化计划的输入，报告提供了可靠的基础，但不应不经核实就直接采纳具体数字。
