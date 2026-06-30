# Plan · 拆计划 / 出实施计划(阶段操作指南)

> plan 阶段:**主线程跑**。`prev_outputs` 带来两份(按 `reads:[design,to-issue]`)——design 钉的设计文档 + to-issue 钉的 issue 目录,照单读。主 Agent 编排:划边界、验收、回填、就绪门,**不亲自拆小 issue、不亲自写 Task Pack**(那是 `plan-writer` 的活)。
>
> 红线:**②计划审与换阶段归 flow 引擎,本阶段不自派审、不自己跳阶段、不选执行方式**(执行方式 build 阶段定)。就绪门过后 `mmw handoff` 交还,产出钉 plan 目录。

阶段目标:把已评审设计 + issue 拆成执行者零上下文也能照做的实施计划(Task Pack + TDD 步骤 + 验收命令),钉进接力单喂 build。一个大 issue 对应一份 plan。

## 前置

设计已评审通过 + issue 已就绪(design 阶段产出,从 `prev_outputs` 读)。缺设计 → `mmw handoff --conclusion needs-context` 回 design。

## 流程总览

读 `prev_outputs`(设计 + issue)→ 写跨 plan 合同骨架 → 逐 issue 并行派 `plan-writer` → 亲验 + 回填 + 就绪门 → `mmw handoff` 交还。

## 各步读哪份(走到该步现读**全文**,别凭记忆默写)

| 步 | 干什么 | 读哪份(整份) |
|---|---|---|
| **编排** | 判单/多计划模式、映射 plan 清单、写跨 plan 合同骨架、fan-out plan-writer、亲验、回填、就绪门,含角色声音 + Git 纪律——拆计划的全套编排方法论 | `plan-flow.md` |
| **写 plan(单计划主线程自己写,或派发时给 plan-writer)** | Task Pack 模板 + Plan Header + TDD 步骤格式 | `task-pack.md` |
| **写作严谨度** | 测试纪律、正反例、反模式 | `plan-rigor.md` |
| **就绪门自检** | 跨 plan 覆盖与 ownership 逐条过 | `plan-self-check.md` |

## 收尾:钉产出 → handoff(交还 flow,不自己选执行方式)

就绪门过后,**钉 plan 目录进接力单 + 一条 handoff**(落地由 build 阶段派 Codex,本阶段不交接执行方式;②计划审由 flow 触发,不自派):

- 计划就绪 → `mmw handoff --conclusion pass --produced docs/plans/<slug>/` → flow 触发 ②计划审(Codex 独立审),审过再进 build。
- 设计 / 验收不清没法拆 → 回 design 改:`--conclusion needs-redirection --to-phase design`(`needs-repair` 是原地返工、回不到 design);缺用户输入 → `needs-context`。
- 探代码撞破设计方向 → `--conclusion needs-redirection`。
- ②计划审打回 → flow 回 plan(`needs-repair`),停在本阶段改、改完 handoff 重审。**Critical 必须修掉才能进 build。**

## 边界

没有就绪的 plan 不进 build。plan-writer 返回的事实未经主 Agent 亲验不采信——它是劳动力不是 ground truth。
