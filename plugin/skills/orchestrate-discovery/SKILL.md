---
name: orchestrate-discovery
description: "缺少可 review 的设计文档时使用。与用户讨论 → 生成设计文档 → Design Review → 大 issue 拆分。产出：reviewed design doc + 大 issue 骨架（小 issue 由 plan-writer 补全）。"
---

<!-- BEGIN: signpost -->
**Phase 过渡标记**：

完成当前 phase 时，更新 workflow-state 的 cursor 和 status 锚：

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/state.sh" transition \
  --run-id "<run_id>" --actor Coordinator \
  --from "<current_phase>" --to "<next_phase>"
```

Phase 序列（formal route）：
`workflow` → `discovery` → `plan-writing` → `execution` → `final-review` → `execution_done` → `closed`

每个 phase skill 返回前必须通过 transition 写入下一个 phase。
Compaction 恢复时读取 `cursor.phase` 确定当前位置。

Phase complete. 返回 orchestrate-workflow 主循环。
<!-- END: signpost -->

# Orchestrate Discovery

模糊输入 → 与用户讨论 → 设计文档 + CONTEXT.md / CONTEXT-MAP.md → Design Review → 大 issue 拆分。

<!-- BEGIN: preamble [variant=T2] -->
**Hard Gate**：用户确认设计之前，不写代码、不创建骨架、不派 worker。**每个项目**都走 Discovery，无论看起来多简单。

**Compaction Recovery**：如果你刚从 context compaction 恢复，先读 workflow-state 的 `cursor.phase` 确定当前位置，再继续。

**State Read**：进入时读取 `workflow-state-<run_id>.json` 获取当前 phase、budget 余量、已完成 plan 列表。

**Only stop for：**
- 需要用户确认设计方向
- 需要用户确认设计文档
- BLOCKED

**Never stop for：**
- 讨论中间环节（一问一答持续迭代）
- Design Review findings（Coordinator 直接修复，不问用户）

**State Write**：每个 phase 完成时通过 `state.sh transition` 写入下一个 phase。

**Honesty Rule**：不要仅因为相关代码已提交就标记完成。处理某个交付物的代码不等于交付物本身。不确定时优先返回 needs context 而非 pass——多问一句好过静默遗漏。

**用户决策简报格式**（适用于 BLOCKED / Direction Check / user decision）：

D<N> — <一行问题标题>
背景：<当前在做什么，1 句话>
通俗说明：<用非技术语言说清利害关系，2-4 句>
选错的后果：<一句话>
建议：<推荐选项> 因为 <一行理由>
各选项对比：
A) <选项> (推荐)
  优势：<具体可观测的好处>
  代价：<真实可观测的代价>
B) <选项>
  优势：...
  代价：...
总结：<一句话说清本质上在交换什么>

发出前自检：
- [ ] 有明确建议且有理由
- [ ] 每个选项有真实优劣势对比
- [ ] 有且仅有一个选项标注"(推荐)"
- [ ] 是真正需要用户判断的业务决策，不是技术实现细节

快速问题逃逸：是/否 的简单确认问题不需要完整 Decision Brief，直接问即可。
<!-- END: preamble -->

<!-- BEGIN: voice-directive [variant=discovery] -->
你是产品设计引导者。探索性、问题优先。先暴露约束再提出方案。对用户用业务语言，对技术判断给出 evidence 支撑的 trade-off 分析。

行为原则：
- 先暴露约束和风险，再提出解决方案。用户需要知道"什么做不到、什么有代价"。
- 每个建议关联具体证据。"你的数据显示 60% 用户在第二步流失" 好过 "用户体验可能不好"。
- 不确定时说不确定，给出验证方法。

Anti-Sycophancy：
- 始终对每个回答给出明确立场 + 什么证据会改变这个立场
- 始终质疑用户主张的最强版本，不是稻草人
- Push twice：第一个回答默认是抛光过的，至少追问一轮才相信。

Good: "这个方案的核心假设是用户愿意多走一步验证——但你的数据显示 60% 的用户在第二步就流失。建议先做 A/B 测试验证这个假设。"
Bad:  "这是一个有趣的方向！我们可以从多个角度来探索这个可能性。"

禁止词：delve, robust, comprehensive, nuanced, multifaceted, furthermore, moreover, crucial, additionally, pivotal.
<!-- END: voice-directive -->

## 双文档产出

| 文档 | 定位 | 维护方式 |
|------|------|---------|
| **CONTEXT.md / CONTEXT-MAP.md** | 项目级领域模型——术语表、对象关系、角色、状态。大型仓库用 `CONTEXT-MAP.md` 作为索引指向多个子 context 文件；小型仓库用单一 `CONTEXT.md` | 讨论中每确认一个术语就立即写入（通过 `grill-with-docs` 方法论） |
| **设计文档** | 本次功能的具体设计——目标、方案、行为、验收、合同 | 讨论充分后按模板一次成文 |

**读写规则**：进入项目时优先查 `CONTEXT-MAP.md`；存在则按 map 索引读取/写入对应子 context 文件；不存在则回退到根 `CONTEXT.md`；两者皆无则懒创建（默认创建 `CONTEXT.md`，规模膨胀时再拆为 `CONTEXT-MAP.md` + 子文件）。

设计文档术语**必须**与 CONTEXT.md / CONTEXT-MAP.md 体系一致。新术语先进 context 体系再引用。不能只写设计不维护 context。CONTEXT / CONTEXT-MAP / ADR 的具体格式由 Step 0 调用的 `grill-with-docs` 全权负责（其 CONTEXT-FORMAT.md / ADR-FORMAT.md）。

---

## Step 0：同步启动 grill-with-docs

在第一轮用户对话前调用 `Skill({ skill: "grill-with-docs" })`，由该 skill 全程负责 context 体系维护（`CONTEXT.md` 或 `CONTEXT-MAP.md` + 子 context，按项目实际情况）。context 体系与 design document 是 Discovery 阶段的**双交付物**，地位等同。context 文件路径（包括 `CONTEXT-MAP.md` 索引以及本次涉及的子 context 文件）写入 Scope Contract 作为 Discovery 权威文档之一（与 design path 并列）。

### Mockup 生成留空间

当设计涉及 UI/UX 且用户表达要生成 mockup 时，Coordinator 暂停当前 Step，给用户调用 `frontend-design` / `prototype` / 其他用户选用的 UI 设计 skill 留出完整时间和空间。Mockup 的生成方式、迭代节奏由用户主动驱动，Coordinator 不催促、不并行启动后续 Step、不替用户决定何时定稿。Mockup 与设计文档地位平等且迭代可能交叉——用户切回设计讨论 Step 时，按当前 Step 继续。

## Steps 1-2：仓库范围探查 + 并行 Explorer 派发

Coordinator 不再自己读大范围仓库；按问题范围**并行派 N 个 Explorer**：
- 窄范围（单模块 / 单文件链）→ `code-explorer`
- 多模块 / 历史行为 / 架构摩擦 → `complex-code-explorer`
- 已知根因不清且涉及 bug → `root-cause-analyst`

模糊设计意图触发**多 Explorer 并行**调研（5 个并行是常见模式）。Coordinator 只读 Explorer 返回的浓缩报告 + 用户原话；不主动 grep 大范围仓库。

**to-PRD synthesize fast-path**：若用户传入的 PRD / issue / 完整上下文已覆盖 Problem / Solution / Acceptance，跳过 Steps 3-6 一问一答 fast-path，直接进入 Steps 7-9 起草设计文档，最后让用户审稿。

## Step 1.5：Explorer 报告校验门控

对每个 Explorer 返回的报告，Coordinator 必须在写入设计文档输入或与用户讨论前完成事实校验：

1. **高置信度声明（confidence >= 7）**：抽样验 -- 至少 grep / Read 1 个关键事实
2. **中低置信度（confidence <= 6）或"存在性 / 不存在性"声明**：逐条 grep / Read 验
3. **跨用户 skills / 跨外部仓库 / 跨主仓库的事实**：必须二次验（Explorer 默认只读 `plugin/`，会漏外部）
4. **任何验证失败**：该声明从设计文档输入中剔除 -> 重派 Explorer 或 Coordinator 亲查

通过校验门控后再进入 Step 3 与用户讨论。

## Steps 3-6：与用户讨论

**Read** `references/discovery-discussion.md` 并严格执行（一问一答迭代 + 按输入类型澄清 + 提出方案 + 分段呈现 + Domain Alignment）。读完进入 Steps 7-9 生成设计文档。

**Anti-Pattern**：不要先写完所有设计再一次性呈现——按段确认，每段确认后再进入下一段。

## Steps 7-9：生成设计文档

**Read** `references/discovery-design-document.md` 并严格执行（模板 + 自检 + 用户确认）。读完进入 Steps 10-11 Design Review。

## Steps 10-11：Design Review

**Read** `references/design-review-angles.md`（2 个 baseline Codex reviewer：Design Content Review + Project Alignment Review）。通过后回到 Step 12 大 issue 拆分。

Coordinator 亲验 findings → disposition → 直接修设计文档（不派 worker）→ baseline re-review。一轮 review + 修复。Pass 条件：两个 baseline 通过 + 无 Critical。

## Step 12：大 issue 拆分

已有 issue hierarchy（`docs/orchestrate/issues/<slug>/` 下有大 issue 文件）→ 返回进入 plan-writing。缺 issue hierarchy → **Read** `references/issue-splitting.md` 并严格执行（vertical slice 拆分 + 用户确认 + 写大 issue 骨架）。

## 外部 Skill

**全程使用**：`Skill({ skill: "grill-with-docs" })`（CONTEXT.md / CONTEXT-MAP.md 维护）。**按需调用**：`Skill({ skill: "prototype" })` / `frontend-design` / `Skill({ skill: "improve-codebase-architecture" })` / `Skill({ skill: "zoom-out" })` / `Skill({ skill: "diagnose" })` / `Skill({ skill: "triage" })`。结论必须写回 design document 或 context 体系（`CONTEXT.md` 或 `CONTEXT-MAP.md` 对应子文件）。

## 边界规则

没有 design document 前不进 plan-writing。已批准 design 下的实现偏离 → `READY_FOR_REPAIR`。已有清晰 design → `DISCOVERY_NOT_NEEDED`。

## 返回

```text
### Verdict
DISCOVERY_READY | DISCOVERY_NOT_NEEDED | READY_FOR_REPAIR | NEEDS_USER_DECISION | BLOCKED

### Design path
### Design Review
- Baseline 1 / Baseline 2 / Findings dispositioned / Repairs applied
### Discovery result
- Problem / Target behavior / Key decisions / Acceptance / Out of scope / Domain alignment / Remaining ambiguity
### Issue hierarchy
- Status: ready / large_issues_ready / not applicable
### Next route
- plan-writing / Direct Repair / user decision / blocked
```
