# GStack 优化计划过度设计审查报告

> **审查对象**: `2025-05-22-gstack-prompt-optimization-plan.md`（P1-P11，11 个优化项）
> **审查日期**: 2025-05-22
> **审查视角**: 是否过度设计、是否照搬、是否推倒重来、规模是否合适

---

## 审查方法论

判断标准不是"这个东西好不好"，而是"这个东西在我们的系统中是否合适、是否过重"。具体判别维度：

1. **是否实现已承诺的设计条目（maturity doc §）**：填补已规划承诺 = 合理适配；引入新概念 = 需要额外审视
2. **是否已有等效机制**：现有文件已覆盖相同语义 → 重复建设
3. **占比是否合理**：我们 6 个 SKILL.md 总共 1342 行（execution 433, plan-writing 242, workflow 218, final-review 203, multi-pr-merge 128, discovery 118）；voice-directive.md.tmpl 71 行（14 个 variant）；agent 定义从 39 行到 157 行不等。新增内容相对于宿主文件的占比是关键指标
4. **受众适配度**：GStack 面向单人技术创始人；我们面向非技术项目负责人。语气、颗粒度、术语密度要匹配

---

## 逐项审查

### P1: Decision Brief Protocol — ⚠️ 需要缩减

**映射状态**：实现 §3.7（BLOCKED 不是黑洞）+ §5b（Direction Check 信息化）— 合理适配。

**过度设计问题**：

1. **10 项自检清单过重**。GStack 的自检清单是为 3000 行 SKILL.md 设计的——单个 SKILL.md 内有数十处 AskUserQuestion 调用，自检清单帮助维持一致性。我们的 SKILL.md 平均 224 行，每个 phase 的 AskUserQuestion 调用通常 1-3 次。10 项清单对 AI 来说是噪音——到第 7 项 AI 已经不认真逐项检查了。

2. **"≥40 字符"的机械规则不适合我们**。GStack 这条规则是为了防止英文场景下的"点到为止"敷衍（"it's faster"这种 4 字回复）。中文表达天然更紧凑（40 个中文字 = 120 字符的信息密度），强加字符数限制会导致注水。

3. **计划作者自己标记了"格式过于刚性"的风险**，但给出的缓解（"快速问题逃逸"规则）是补丁而非精简——正确做法是从源头缩减。

**已有覆盖**：execution SKILL.md 第 232-243 行已有双层 BLOCKED 报告格式（业务影响层 + 技术详情层），这正是 §3.7 承诺的核心。Decision Brief 是对此格式的泛化，不是从零建设。

**建议**：
- Decision Brief 模板保留，但去掉 ELI10 标题改为"通俗说明"（已做到）
- 自检清单从 10 项精简到 4 项核心项：(1) D<N> 标题行 + 通俗说明段存在；(2) 有明确建议且有理由；(3) 每个选项有真实优劣势对比（不要求字符数下限）；(4) 是真正的业务决策不是技术细节
- 去掉"你在调用 AskUserQuestion 工具，不是在写散文"——这是对 AI 说教，不是结构化规则
- 去掉"非 ASCII 字符直接写不用 \u 转义"——这是 GStack 的英文环境问题，我们全中文环境不存在这个场景

---

### P2: Voice Directive 充实 — ⚠️ 需要缩减

**映射状态**：实现 §4d（Persona + Voice Directive）— 合理适配。

**过度设计问题**：

1. **禁止词从 7 个扩展到 19 个 + "no em dashes"过重**。当前 7 个禁止词（delve, robust, comprehensive, nuanced, multifaceted, furthermore, moreover）覆盖了最高频的 AI 腔词汇。新增的 12 个中，`crucial, additionally, pivotal` 是合理补充；但 `landscape, tapestry, underscore, foster, showcase, intricate, vibrant` 在中文 AI 输出中几乎不出现（这些是英文 AI 的特色词汇）。"No em dashes"规则更是纯英文问题——中文用的是中文破折号（——），和英文 em dash（—）是不同字符。

2. **调查员层（code-explorer, complex-code-explorer, root-cause-analyst, codex-reviewer）不需要 Good/Bad 示例对**。这些 agent 不和用户沟通，它们的输出只给 Coordinator 看。Coordinator 自己有 voice directive 控制最终用户看到的内容。给调查员加 Good/Bad 示例是多余的 token 消耗。

3. **三层分级策略本身是合理的**——Coordinator 层 12-15 行、Worker 层 8-10 行、调查员层 8-10 行，占比可接受。

**建议**：
- 禁止词扩展到 ~10 个（保留当前 7 个 + 新增 crucial, additionally, pivotal），去掉中文场景中不出现的英文 AI 腔词汇
- 去掉 "no em dashes" 规则
- Coordinator 层：保留 Good/Bad 示例对 + 正面行为原则（这是真正有价值的新增）→ 12-15 行可以
- Worker 层：保留 Good/Bad 示例对 → 8-10 行可以
- 调查员层：只保留禁止词更新，不加 Good/Bad 示例对 → 维持当前 ~3 行实质内容

---

### P3: Pre-emit Verification Gate — ✅ 适度（需要小幅编辑）

**映射状态**：实现 §3a（Finding 结构化）+ §3b-2（Coordinator 亲验纪律）— 合理适配。

**评价**：当前 review-dispatch.md.tmpl 只有 26 行，确实过薄。核心机制（"引用代码行或强制降级到 confidence 4-5"）是 GStack 中最有实操价值的设计之一，且不依赖单人单模型假设——在我们的跨模型 review 场景中同样适用。Rationalization Prevention 三条规则精练有效。

**需要编辑的部分**：FP 类别表中的框架列举（Django Meta / Rails has_many / SQLAlchemy / TypeORM / Prisma / Sequelize）是 GStack 的 Web 后端偏见。我们的用户项目类型不确定——应该泛化为"当符号来自 ORM 元类、装饰器、代码生成器时，引用生成该符号的元构造"，不穷举具体框架。

---

### P4: Anti-Sycophancy Rules — ⚠️ 需要大幅缩减

**映射状态**：属于 §4d 的扩展，但原始设计文档并未规划 Anti-Sycophancy——这是 GStack 的新引入概念。

**过度设计问题**：

1. **来源不匹配**：GStack 的 Anti-Sycophancy Rules 来自 `/office-hours` skill——面向创始人的产品战略诊断（"你的 TAM 假设有问题"、"你的 GTM 策略错了"）。那个场景需要强对抗姿态。我们的 discovery 面向非技术项目负责人讨论功能设计——语境完全不同。

2. **4-5 条禁止句式过于刚性**。"不要说'这个想法很有趣'"、"不要说'我理解你为什么这样想'"——这些在技术创始人对话中是合理的（创始人需要直言不讳的反馈），但在非技术项目负责人面前会被感知为粗鲁。计划作者自己也标记了"对抗性过强"的风险。

3. **缓解方案不够**：作者建议"保留 Always 规则和 Good/Bad 锚点，Never say 列表标记为建议性"——但"建议性"的禁止词列表在实践中 AI 要么全遵守要么全忽略，没有"建议性遵守"的中间态。

**建议**：
- 保留 2 条 Always 规则（"对每个回答给出明确立场 + 什么证据会改变"、"质疑用户主张的最强版本"）——这是核心价值
- 保留 Good/Bad 示例对——这是锚定 AI 行为的有效手段
- **完全去掉 4-5 条禁止句式列表**——不适合我们的受众
- 最终 discovery variant 应该是 ~8-10 行（当前 2 行角色描述 + 2 行 Always + Good/Bad 对 + 禁止词 = 合理）

---

### P5: Learnings 反注入 + Trust Gate — ✅ 适度

**映射状态**：直接实现 §8a（Learnings Trust Gate）— 填充已规划的基础设施。

**评价**：`learnings-trust-gate.md` 已经存在并引用了 `learnings-poison-detector.sh`——当前是 stub，P5 是往 stub 里填充具体实现。10 个反注入正则模式来自 GStack 的生产验证，二值 trust 标记（`user-stated` = trusted，其他 = untrusted）简洁有效。

这不是 GStack 照搬——是用 GStack 已验证的具体实现填充我们自己规划的空壳。规模合理，直接实施。

---

### P6: plan-writer 安全网 — ✅ 适度

**映射状态**：无直接 § 映射，但是结构性缺陷修复——plan-writer 39 行 vs pack-executor 157 行是不合理的。

**评价**：这不是 GStack 借鉴，是内部一致性修复。plan-writer 是唯一没有 Return Contract、Self-Check、Three-Failure Protocol 的 agent。pack-executor 已有完整的安全网（Return Contract 行 139-153、三次失败协议行 114-126、交付前自检行 128-136）。给 plan-writer 补齐同等结构是必要的。

从 39 行扩展到 ~80 行，增幅 ~41 行。考虑到 pack-executor 157 行、root-cause-analyst 156 行，plan-writer 80 行仍然是较轻量的 agent。规模合理，直接实施。

---

### P7: root-cause-analyst Iron Law + 3-Strike — ⚠️ 需要缩减（已有等效机制）

**映射状态**：GStack investigate/SKILL.md.tmpl 的新引入概念。

**已有覆盖**：root-cause-analyst.md 当前已有等效规则：
- 行 60-66"通用停止条件"：`3 假设无确认证据 → 停止，报告已排除路径` — 这就是 3-Strike Rule
- 行 59-61"不重复规则"：`每个假设必须和前几个不同维度` — 这保证了假设多样性
- 行 55-58"不是你的活"：`问题原因已经明确 → 返回 needs context` — 这就是 Iron Law 的 spirit（不做已知问题的修复，做根因调查）

计划作者自己承认"与 RCA agent 的现有角色定义完全一致，是具体化而非方向改变"——但 proposal 是新增独立的 `## Iron Law` 和 `## 3-Strike Rule` 章节，实际效果是**重复现有内容并加上 GStack 的命名体系**。

**建议**：
- 不新增独立章节。在现有"通用停止条件"段落中追加 Iron Law 的一句话表述（"没有根因调查就没有修复——修症状制造打地鼠调试"）
- "Red flags"三条可以作为 bullet points 追加到现有"不是你的活"段落
- 不引入 GStack 的 "Iron Law" / "3-Strike" 命名——用我们自己的语言说同样的事

---

### P8: Business Report Good/Bad 锚点 + PR Quality Score — ⚠️ 需要拆分

**映射状态**：Good/Bad 锚点实现 §4c（失败报告双层化）+ §4d；Quality Score 是 GStack 新引入。

拆分审查：

#### Good/Bad 锚点 — ✅ 适度

`final-review-completion.md` Step 19 当前说"用业务语言，不用技术术语"但没有任何示例。AI 对"业务语言"的理解不稳定——Good/Bad 示例对是锚定这个理解的最有效手段。2-3 组示例对（~12 行）加入到 119 行的文件中，占比 ~10%，合理。

#### PR Quality Score — ❌ 不应该做

`max(0, 10 - (critical*2 + informational*0.5))` 是伪量化指标：
1. 它把多维信息（critical 数量、informational 数量）压缩成一个数字，丢失了对非技术用户最关键的上下文（"什么是 critical"、"informational 意味着什么"）
2. maturity §4b 已有结构化的 `review_effectiveness`（total/accepted/rejected/suppressed），这比单一分数更有信息量
3. 面向非技术用户的"业务报告"中放一个公式计算的分数，违反了"用业务语言"的核心原则——"7.0/10"对项目负责人来说没有任何可操作含义
4. GStack 的 Quality Score 面向技术创始人（懂 critical vs informational 的含义），我们的用户不懂

**建议**：保留 Good/Bad 锚点，删除 Quality Score。如果需要给用户一个直观的质量感知，在业务报告中用自然语言："审查发现 1 个需要修复的问题（已修复），3 个改进建议（已记录到后续计划）。整体代码质量符合发布标准。"

---

### P9: Completion Status Protocol — ✅ 适度（需要框架修正）

**映射状态**：属于 §4d 的扩展，统一退出格式。

**已有覆盖**：pack-executor.md 第 142-144 行已有显式映射："映射：DONE = pass，DONE_WITH_CONCERNS = needs repair，NEEDS_CONTEXT = needs context，BLOCKED = blocked。" root-cause-analyst 有同样的 verdict 结构。6 个 SKILL.md 的返回区都有结构化的 Verdict 列表。

**真正新增的内容是 Honesty Rule**（"不要仅因为相关代码已提交就标记 DONE"）——这确实是当前系统没有的，且有实际价值。

**建议**：
- 不新增"退出状态协议"作为独立的 preamble 段落——现有 Return Contract + Verdict 已覆盖
- **只追加 Honesty Rule**：在 preamble.md.tmpl 的 T2/T3 变体中追加 2-3 行 Honesty Rule 文本
- 将 `STATUS, REASON, ATTEMPTED, RECOMMENDATION` 格式声明去掉——我们的返回格式已经有更丰富的结构（Verdict / Evidence / Result / Verification / Open Items）

---

### P10: maxTurns 边界行为 — ✅ 适度

**映射状态**：调研报告 §6.3 发现的实际缺陷修复。

**评价**：4 个有 maxTurns 的 agent（code-explorer 20, complex-code-explorer 30, docs-worker 20, root-cause-analyst 40）确实没有定义接近上限时的行为——当前是硬截断导致结果丢失。追加 2-3 行"80% turn 消耗时返回部分结果"的指令，在 62-156 行的 agent 定义中占比 ~2-5%。

这不是 GStack 特有的设计——是通用的 agent 工程最佳实践。规模合理，直接实施。

---

### P11: Calibration Learning 精确触发条件 — ✅ 适度

**映射状态**：具体化 §4a（Learnings JSONL）中叙述性的触发条件。

**评价**：`learnings-confidence-audit.md` 当前是叙述性的处理规则（48 行），缺少精确的"什么条件 → 写入什么类型的 learning"映射。P11 的 if-then 表格把 5 种触发条件结构化，替换叙述性描述。

计划作者已自修正"连续 3 条 reject"为"累计近 5 次 run 中同一 category 3 条 reject"——这表明对实际场景有思考。规模合理（替换现有内容，不是纯新增），直接实施。

---

## 整体评价

### 照搬倾向判定

**这份计划不是系统性照搬，但在 3 个点上存在 GStack 的引力过大的问题**：

| 倾向类型 | 涉及条目 | 表现 |
|---------|---------|------|
| **合理适配**（填充已规划承诺） | P3, P5, P6, P10, P11 | 5 项直接实施 |
| **作者自知但未收敛**（标记了风险但缓解不够） | P1, P2, P4 | 3 项需要按本审查缩减 |
| **重复现有机制**（已有等效内容，包装为新概念） | P7, P9 | 2 项需要降级为现有内容的微调 |
| **GStack 概念直接移植**（不适合我们的受众） | P8 Quality Score | 1 项应完全删除 |

### 核心问题

计划的核心问题不是"照搬 GStack"——作者对 GStack 的适配意识是存在的（三层 voice directive 分级、中文化适配、"不纳入计划"的 4 项拒绝都表明了独立判断）。

核心问题是**自我缩减不彻底**。计划在 P1、P2、P4 三处明确标记了"可能过度"的风险，但给出的缓解方案是"加一条逃逸规则"或"标记为建议性"——这是用补丁修补过度设计，而不是从源头精简。正确做法是识别出风险后直接缩减内容，而不是保留全部内容再加一条"但如果太重可以不完全遵守"的免责声明。

### 对现有体系的保护

**没有推倒重来的风险**。P1-P11 全部是增量操作（新建模板 1 个 + 改现有模板/reference/agent），没有任何条目建议删除或替换现有从 Superpowers/Planning with Files/Mattpocock 借鉴来的内容。现有的 preamble 结构、disposition table、forbidden shortcuts、signpost 系统、review dispatch 协议、TDD 方法论、三方分离架构全部不受影响。

### 规模总评

按计划实施后的预估新增行数（未缩减版本 vs 本审查建议版本）：

| 条目 | 计划预估新增行数 | 审查建议版本 | 差异 |
|------|----------------|-------------|------|
| P1 Decision Brief | ~40 行模板 + ~20 行清单 | ~30 行模板 + ~8 行清单 | -22 行 |
| P2 Voice Directive | ~120 行（14 variant 扩充） | ~70 行（Coordinator+Worker 扩充，调查员只更新禁止词） | -50 行 |
| P3 Pre-emit Gate | ~35 行 | ~30 行（泛化框架举例） | -5 行 |
| P4 Anti-Sycophancy | ~20 行 | ~10 行（去掉禁止句式列表） | -10 行 |
| P5 Learnings Gate | ~25 行 | ~25 行 | 0 |
| P6 plan-writer | ~40 行 | ~40 行 | 0 |
| P7 RCA Iron Law | ~20 行新章节 | ~5 行追加到现有段落 | -15 行 |
| P8 Good/Bad | ~25 行 | ~15 行（去掉 Quality Score） | -10 行 |
| P9 Completion Status | ~15 行新协议 | ~5 行 Honesty Rule | -10 行 |
| P10 maxTurns | ~12 行（4 个 agent） | ~12 行 | 0 |
| P11 Calibration | ~15 行 | ~15 行 | 0 |
| **总计** | **~367 行** | **~265 行** | **-102 行** |

缩减 ~28% 的新增量。更重要的是去掉了 GStack 特有的不适配内容（英文 AI 腔禁止词、字符数限制、创始人对抗风格、伪量化分数），保留了普适性价值（Good/Bad 锚点、引用验证门槛、结构化 Decision Brief、Honesty Rule、反注入正则）。
