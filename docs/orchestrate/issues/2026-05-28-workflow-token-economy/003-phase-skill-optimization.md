# Issue 003 — Phase Skill 优化与压缩

## What to build

在 Issue 001（基础设施）+ Issue 002（合同清理）完成后的干净基线上，对 6 个 phase skill 做最后一层压缩与精修：

- **Discovery 阶段集成**（决策 14-19）：
  - Explorer agent 并行派发（与 Plan-writing 对称）
  - `grill-with-docs` 提升为 Step 0 同步入口；CONTEXT.md 与 design 同等地位
  - 外部精华轻量引入 3 条（synthesize fast-path / prototype-snippet 例外 / Push twice）；**显式不引入** Forcing Questions 三问
  - Discovery 文档压缩（删 Self-Read Protocol 死内容 / Route Dispatch 错位行 / grill-with-docs 重复）；合并两个 issue template
  - **完全删除 GitHub Issue 发布**（不是 opt-in 而是 fully delete）；issue 本地文件保留
  - Mockup 生成留时间和空间（最小化，仅一行规则——用户主动调用 frontend-design/prototype 等 skill）
- **Sub-agent 事实校验机制（横切）**（决策 18 / Content Review C3 闭合）：
  - `plugin/agents/code-explorer.md` / `complex-code-explorer.md` / `root-cause-analyst.md` description 含 "Coordinator must verify" 表述
  - `orchestrate-discovery/SKILL.md` 新增 Step 1.5（Explorer 报告校验门控）
  - `orchestrate-plan-writing` / `orchestrate-execution` / `orchestrate-multi-pr-merge` SKILL.md 同步加 Step
  - `agent-return-handler.sh` 输出 "⚠️ 写入交付物前必须校验本次返回的事实声明"
  - `architecture-draft.md` 新增"Sub-agent 信任边界"章节
- **Plan Writing 压缩**（决策 20）：删 `plan-writer-dispatch.md` L5-15 + `plan-review-dispatch.md` L5-13 Self-Read Protocol 死内容；budget 公式同步落地（Issue 002 已确定公式，此处落地到 plan-gates.md L46 + orchestrate-plan-writing/SKILL.md L172）
- **Execution 微调**（决策 21 / Alignment Review C1 完整版）：**8 处** `execution-worker-handbook` 引用全部修正为 `execution-worker-dispatch.md`：
  1. `plugin/skills/orchestrate-execution/SKILL.md` L202
  2. `plugin/agents/pack-executor.md` L71
  3. `plugin/agents/complex-pack-executor.md` L69
  4. `plugin/build/templates/worker-loop.md.tmpl` L12（**critical runtime bug**）
  5-8. `plugin/architecture-draft.md` L53 / L286 / L299 / L338
  
  + 删 `execution-review-dispatch.md` L5-15 Self-Read 死内容
- **Final Review 微调**（决策 22）：
  - `final-review-angles.md` L5-15 Self-Read 死内容删除
  - `final-review-repair.md` Step 11 整段（122 行 targeted re-review）+ Step 12 三轮截断改为二段（repair-once + RCA escalation）
  - L353 Phase 软上限重算为 **3**（2 baseline + 0 targeted + 1 release gate）
  - `final-review-release-gate.md` Step 18 / `final-review-completion.md` Step 15 / `SKILL.md` L52 同步删除 targeted re-review 引用
- **Multi-PR 微调**（决策 23）：
  - "Coordinator 端最小职责" section 重复 5 处提取为 SKILL.md 顶部通用 4 step 模板
  - `merge-completion.md` "不存在非阻塞项" 改为单行引用 Final Review 清扫
  - `merge-integration-review.md` 末尾补 Phase 软上限 = **1**（1 integration review + 0 targeted）
  - 决策 13 在 Multi-PR 的 5 处级联清理（targeted re-review 模板 / gate 命名 / 2 轮修复 → 1 轮 + 自验 / Step 18 重写 / handbook L40-41）

完成本 issue 后：6 个 phase skill 全部达到 token economy 目标；Plugin 进入 v3.9.0（或对应版本）发布候选状态。

## Small issues

<!-- PENDING: plan-writer 将在 plan-writing 阶段补全小 issue 拆分 -->

## Blocked by

- **001 (Infrastructure)** — D14 Explorer 集成需要 D2 死模板清理后的 reference 基线；D18 Sub-agent 校验需要 agent frontmatter 瘦身（D11）已完成
- **002 (Contracts & State)** — D20 budget 公式落地需要 D13 公式已确定；D21 修 `worker-loop.md.tmpl` L12 必须在 D6 segment 5 重写（Issue 002 Pack）之后，避免 file ownership 冲突
