# Orchestrate Plan Writing 质量压测

## 输入

压测使用 AgentFlow 真实素材：

- `/Users/cheuklapchan/agentflow/docs/superpowers/specs/2026-05-16-ai-video-review-batch-completion-design-draft.md`
- `/Users/cheuklapchan/agentflow/docs/issues/2026-05-17-ai-review-batch-completion-progress.md`

为了测试 plan 质量，而不是只测试缺件路由，本压测模拟 `to-issues` 已把该大 issue 拆成 5 个 small issues：

1. 审核单个商品创建 1 商品 AI 视频审核批次。
2. 已选商品和当前采集批次入口创建统一批次。
3. 重复 active 审核保护和范围重叠去重。
4. 历史 stuck 批次完成收敛 repair。
5. AI 视频审核批次 summary projection 和多批次进度卡消费。

## 生成效果审查

按当前 skill 生成代表性 plan 时，结构可以成立：

- 大 issue 能成为 plan 一级章节。
- 5 个 small issues 能成为 5 个 Task Packs。
- Task Pack 能带出真实 AgentFlow 路径，例如 `src/local_agent/collection_task_api.py`、`src/local_agent/compass_batch_review_task_executor.py`、`src/local_agent/video_review_service.py`、`src/local_agent/local_collection_store.py`、`src/dashboard/templates/console/collection/compass/partials/board_main.html`。
- verification 能落到 `tests/test_local_console_host.py`、`tests/test_compass_capture_ui_contract.py`、`tests/test_local_video_review_parallel_tasks.py`、`tests/unit/local_agent/test_video_review_service_split.py`。

## 发现的问题

### 1. 细 task 深度过硬，容易过度设计

旧 `plan-document-contract.md` 要求每个代码或测试 step 放“完整 test shape”和“完整 contract / method / schema / state-machine shape”。真实应用到 AgentFlow 后会产生两个坏结果：

- plan 作者为了满足合同，会提前写大量生产代码和测试代码，容易虚构 fixture、函数、字段和 helper 位置。
- plan 变成半实现文档，Phase 0b review 很难判断哪些是设计合同，哪些只是 plan 作者临时想出来的实现。

修正：细 task 必须写清 behavior、关键断言、合同面、命令和 expected result；每个 step 只做一个动作，按 RED -> GREEN -> 验证 -> 整理推进；只有 source design、prototype、ADR 或 existing contract 固定了精确 shape 时，才写代码片段。

### 2. 缺少专门的过度设计 / 设计不足门禁

旧 self-review 主要检查 coverage、executability 和 pack quality，但没有显式问：

- 是否为当前 issue 没要求的未来能力预建了 registry、migration、消息中心、历史页或复杂抽象？
- 是否缺少 failure state、contract owner / consumer、UI states、billing / permission / runtime anchors？
- 是否把大而全测试矩阵当作 pack-local verification？

修正：新增 `references/plan-quality-gates.md`，并把它加入 `SKILL.md` 的按需加载规则；只有 plan 初稿形成后才读取，不在技能启动时预加载。

### 2b. 旧合同没有完整吸收“零上下文 worker”的计划质量

旧版本虽然写了 Task Pack 字段，但没有把计划文档必须服务“没有当前聊天上下文的 worker”这一点落实成检查项。结果是 plan 可能看起来信息很多，却缺少 RED / GREEN expected result、文件责任一致性、type / fixture 一致性和无 placeholder 扫描。

修正：`plan-document-contract.md` 新增无 placeholder 规则、保存前一致性检查和更明确的小步 task 节奏；`plan-self-review.md` 增加 Scope Check 拆分、File Map 回指、RED / GREEN expected result 和 placeholder 扫描。

### 3. Phase 0b 没有明确审 plan 的质量形态

旧 `plan-review.md` 会审 coverage、路径、合同和验证，但没有单独要求 reviewer 检查“过度设计”和“设计不足”。这会让一个结构完整但臃肿或欠设计的 plan 进入 Phase A。

修正：在 Plan Review 的 Coverage And Task Quality 检查中加入 overdesign / underdesign 检查。

## 修正后的信心判断

修正后我对这套技能的判断是：

- 核心架构成立：`to-issues` 负责 issue hierarchy，`orchestrate-plan-writing` 负责 issue-backed plan，`orchestrate-workflow` 负责 Phase 0b / Phase A / Phase B。
- 质量门禁补齐后，plan 不再只追求结构完整，也会检查是否过度设计或设计不足。
- 仍不能说“绝对完善”：真实项目里还需要用至少一份完整 AgentFlow plan 继续跑 Phase 0b 审查，观察 reviewer findings 是否还能反向暴露 skill 缺口。
