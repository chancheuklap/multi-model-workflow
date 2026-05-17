# Plan Quality Gates

本文件用于判断生成的 issue-backed plan 是否真正适合作为 Orchestrate Workflow 执行合同，而不只是结构完整。

## 1. 质量目标

合格 plan 必须同时满足：

- 未来 worker 不需要当前聊天上下文，也能知道要交付什么用户可见行为或系统可验证行为。
- Phase 0b reviewer 能逐条核对 design intent、issue acceptance、路径真实性、合同边界和验证闭环。
- Task Pack 足够垂直，能独立验证；但不会把一个大 issue 临时拆成横向 schema / API / UI / test 任务。
- plan 不把未验证的实现猜想伪装成代码事实；它提供行为、合同、路径、测试、依赖和验收。
- plan 的细 task 足够小，能按 RED -> GREEN -> 验证 -> 整理的短反馈循环执行。
- plan 不为未来 hypothetical scope 预建抽象、长期状态层、registry、migration、消息系统或 UI surface。
- production-risk 不只是 Task Pack 的 risk flag；必须进入 plan 的“发布风险和人工门禁”，说明是否需要提前 review、Phase B final gate 输入和 manual owner。

## 2. 过度设计信号

出现以下情况，先删减 plan；删不掉时按 `orchestrate-plan-writing/SKILL.md` 返回 `NEEDS_DISCOVERY` 或 `NEEDS_ARCHITECTURE`：

- 为一个 small issue 新增多个长期对象、长期状态层、registry、migration 或 UI surface，但 source issue 只要求一个可验证行为。
- 把未来消息中心、历史页、全局 dashboard、跨设备恢复、长期留存、复杂权限或运营后台提前塞进当前 pack。
- 因为多个 pack 都会触碰同一文件，就抽象出 shared helper，但没有当前重复复杂度证据。
- 细 task 写出大量生产代码片段，超过 plan 所需的接口 shape、字段、断言和调用边界。
- plan 预设未验证的 fixture、函数名、class 名、schema 字段或 helper placement，并要求 worker 照做。
- verification 变成大而全测试矩阵，pack-local 行为反而没有 focused command。
- Scope Check 写了 “yes, split into multiple plans”，但仍把多个大 issue 塞进一份 plan。
- 每个 pack 都要求新增代码片段，但这些片段没有来自 source design、prototype、ADR 或 existing contract。

修正原则：

- 当前 source issue 没要求的能力移到 out of scope 或返回 `NEEDS_ISSUES` 重新拆 issue。
- 没有 path reality 的代码细节改成“先用 `rg` 验真，再落到实际符号”。
- 新抽象必须绑定当前至少两个真实 consumer，且能减少当前 pack 的复杂度。

## 3. 设计不足信号

出现以下情况，plan 不能进入 Phase A：

- Task Pack 只写“实现功能”，没有用户可见行为、系统可验证结果或 failure state。
- 只写路径和文件，不写 owner、provider、consumer、model / schema、read model、registry / migration / catalog。
- UI 工作没有 states、viewport、interaction、DOM / screenshot / manual visual gate。
- billing、permission、runtime、sync、DB、JSON、Pydantic、Local Agent、browser takeover 没有 Contract anchors。
- small issue acceptance criteria 没进入 Task Pack acceptance criteria。
- blocked-by 没进入 dependencies，或者把真实串行依赖写成可并行。
- pack 改 shared contract，却没有安排 consumer 同步和 compatibility / migration / release gate。
- production-risk / billing / permission / runtime / migration / manual gate 出现在 pack 中，但没有进入“发布风险和人工门禁”。
- 只列最终大套测试，没有 pack-local focused verification。
- worker 仍需要自行决定业务术语、文案、UI target state、计费含义、权限含义或 issue hierarchy。
- 只说“修改某文件”，没有说明该文件在本 pack 中承担什么 responsibility。
- 没有把测试 RED / GREEN 的 expected result 写清楚。
- 没有做 type / field / fixture / command 一致性检查，后文引用和前文定义对不上。

修正原则：

- 业务 / UX / 术语不清：返回 `NEEDS_DISCOVERY`。
- 状态行为、interface shape 或 UI 方向需要比较方案：返回 `NEEDS_DECISION`，交 Orchestrate 选择 user decision 或 upstream `prototype`。
- issue 太大或无法独立验证：返回 `NEEDS_ISSUES`。
- 架构边界反复卡住：返回 `NEEDS_ARCHITECTURE`。

## 4. 细 Task 深度

细 task 应该让 worker 知道下一步如何验证和实现，但不要替 worker 完成实现。

必须写清：

- 要新增或修改的测试文件；
- 测试要表达的 public behavior；
- 关键断言、输入、输出、状态变化和失败原因；
- 要修改的生产路径、合同面、owner / consumer；
- focused command 和 expected result；
- 何时更新 docs、`AGENTS.override.md` / `agents.overrides.md`、registry、migration、release gate。
- production-risk pack 对应哪一个发布风险面。

只有在这些情况才写代码片段：

- source design、prototype、ADR 或既有 contract 已经固定了精确 shape；
- 不写片段会让 worker 误解 schema、state transition 或 validation rule；
- 片段中引用的类型、函数、fixture 和字段已经验真，或明确标为新建。

禁止：

- 用省略号、伪变量或未定义 fixture 伪装成完整代码；
- 写大段生产实现；
- 把“可以自己选择实现方式”的地方包装成固定代码；
- 用代码片段掩盖未澄清的产品行为或架构边界。

## 5. 小步质量

每个 Task Pack 的 implementation tasks 必须呈现可执行节奏：

1. 先定义 public behavior test 或 contract test。
2. 再运行 focused command，确认失败原因和预期一致。
3. 再实现最小合同，不同时扩展未来能力。
4. 再运行 focused command，确认通过。
5. 只有 GREEN 保持 GREEN 时才 refactor。
6. 最后补齐 docs / rules / registry / migration / release gate。

不要把多个行为塞进一个 step；不要把多个不相关测试命令塞成唯一 verification。

## 6. 质量结论

保存 plan 前给出一个简短自审结论：

```text
Plan quality: pass / needs repair / route required
Overdesign checked:
Underdesign checked:
Largest remaining risk:
Route if not pass:
```
