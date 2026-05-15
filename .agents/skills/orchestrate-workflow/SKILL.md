---
name: orchestrate-workflow
description: Use when 已有 design / implementation plan，Superpowers writing-plans 刚生成项目文档，或用户要求执行、审核、继续、恢复、完成一段有文档依据的开发工作流。
---

# Orchestrate Workflow

目标：把已有 design / plan 变成可验证的代码、文档更新和业务结果。这个 skill 不负责从零构思需求；没有 design / plan 时先用 `superpowers:brainstorming` 或 `superpowers:writing-plans`。

## 运行算法

1. **建立现场账本**
   - 找到 design / plan / bug brief。
   - 读取当前项目规则：`AGENTS.md`，以及其要求的 `PROJECT.md`、`ENGINEERING-RULES.md`、相关 SPEC / ADR / GUIDE / `AGENTS.override.md`。
   - 写下当前任务的 intent、acceptance criteria、风险、验证命令、已完成和未完成项。可以放在工作笔记里；只有项目要求时才改正式 plan。

2. **Phase 0：先审文档是否能落地**
   - design 存在时，先审 design：术语是否对齐正式文档，业务对象和责任边界是否清楚，至少能走通一个正常场景和一个失败/权限/重复/回滚场景。
   - plan 存在时，审 plan：每个任务是否有交付物、文件范围、验证方式、依赖顺序和 `AGENTS.override.md` 同步要求。
   - 技术性缺口由主线程直接修。会改变产品承诺、业务规则、发布策略或架构 trade-off 时才问用户。

3. **把 plan 切成 Task Packs**
   - 每个 pack 必须是 vertical slice：完成后能 demo 或 independently verify。
   - 每个 pack 写清：目标行为、owned files、入口、验证命令、依赖、风险、AFK/HITL。
   - 按技术层横切的 pack 不合格，例如“先写全部 tests / schema / templates，再写 implementation”。
   - 碰同一批文件、migration、billing、auth、runtime、browser takeover、shared contract 的 packs 默认串行；只有 write set 和依赖都不相交才并行。

4. **派发或主线程执行**
   - 当前关键路径、很小的局部修改、或主线程没有非重叠工作可做时，主线程自己做。
   - 独立 sidecar work 才用 `spawn_agent`。
   - review findings 发回同一个 worker 时用 `send_input`；只有下一步真的被阻塞时才 `wait_agent`。

5. **每个 pack 都必须 review + repair**
   - 普通 pack 完成后用 `code_reviewer`。
   - 触及 deploy、database、billing、permissions、runtime、browser takeover、rollback、production dependency、cross-service contract 时用 `release_reviewer`。
   - finding 有效就修；同一问题三次失败必须换方法，必要时进入 root-cause route。

6. **Root-cause route**
   - 先建立可重复 feedback loop，再修复。
   - 不能复现同一个问题时，不写补丁；返回缺少的日志、样本、环境或人工步骤。
   - 不确定根因时派 `complex_code_explorer`；诊断和修复紧耦合时派 `complex_coding_worker`。

7. **Phase B：最终意图验证**
   - 用真实命令、测试、smoke、browser / VM / deploy check 验证 design intent。
   - 不用 worker 自报代替验证。
   - implementation gap 派回 worker；design gap 用业务语言交给用户。

8. **Phase C：业务汇报**
   - 汇报已完成的产品能力、修改范围、验证结果、剩余风险、需要人工判断的点。
   - 这个 skill 不自动 merge、push、开 PR。收分支时用 `superpowers:finishing-a-development-branch`。

## Agent 路由表

| 情况 | agent_type |
| --- | --- |
| 小范围查代码、调用链、测试位置 | `code_explorer` |
| 多模块调查、历史行为、未知 root cause | `complex_code_explorer` |
| 普通实现、测试修复、局部重构 | `coding_worker` |
| migration / billing / auth / permissions / runtime / Gateway / browser takeover / shared contract | `complex_coding_worker` |
| design / plan / pack review | `code_reviewer` |
| 发布前、生产风险、跨服务合同、回滚风险 | `release_reviewer` |
| 低风险文档整理 | `docs_worker` |

## Dispatch Prompt 模板

```text
Phase:
Purpose:
Read first:
Task Pack:
Owned files / read-only boundary:
Acceptance criteria:
Verification commands:
Risk flags:
Do not:
Return:
```

派发 prompt 只传当前任务事实。不要重复粘贴 reviewer / worker 的完整方法论；稳定方法已经写在对应 `~/.codex/agents/*.toml`。

## Pack 合格标准

一个 pack 合格必须同时满足：

- 有用户可见行为、公开接口行为或可检查的系统效果。
- 有明确 owned files / responsibilities。
- 有最小验证命令或复现检查。
- 完成后能独立证明价值。
- 风险类型明确：普通、高风险、生产风险、HITL。
- 依赖关系是真阻塞，不是“可能有关”。

不合格 pack 先重切，不要派发。

## 停止条件

- design / plan 技术上不成立。
- 需要产品、价格、权限、发布策略或架构取舍。
- 缺少环境、账号、样本、日志或人工验证，导致 feedback loop 不能建立。
- 同一 repair loop 三次失败。
- Phase B 发现 design intent 和实现结果不一致。

停止时只报告阻塞事实、已验证证据、可选决策，不输出空泛计划。

## 汇报格式

```text
Status:
完成的能力:
修改范围:
验证:
未完成 / 风险:
需要用户决策:
```

没有需要用户决策时写“无”。不要把普通技术后续伪装成用户决策。
