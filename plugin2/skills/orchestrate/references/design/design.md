# Design · 想方案 / 出设计文档(阶段操作指南)

> design 阶段:**主线程跑**(只有主线程能跟用户讨论)。`prev_outputs` 带来上游两份——propose 钉的选定方向(`docs/design/<slug>-direction.md`)+ investigate 现状报告(`docs/investigating/<slug>.md`),照单读、不重探查、不重提方案。
>
> 红线:**HITL 集中在这**,放开问透;但方向已由 propose 拍定,这里只**细化选定方向**,不重摆备选(被事实击穿 → `mmw handoff --conclusion needs-redirection` 回上游换向)。系统探查 investigate 做完、不重做;**①设计审与换阶段归 flow 引擎,本阶段不自派审、不自己跳阶段**,做完 `mmw handoff` 交还。

阶段目标:把选定方向细化成一份完整、可评审、可拆分的设计文档(+ 维护项目领域文档),钉进接力单喂 ①设计审。**本阶段只产设计文档;issue 切片骨架在 ①设计审过之后的 `to-issue` 阶段做(审后再切片),不在这。**

**Hard Gate**:用户确认设计之前,不写代码——真简单的设计可以几句话,但必须呈现并取得确认。

## 流程总览

读 `prev_outputs`(方向 + 现状)→ 与用户讨论细化选定方向(涉 UI/UX 则 prototype + mockup)→ 写设计文档(+ 领域文档)→ 自检 → `mmw handoff` 交还(进 ①设计审)。

## 各步读哪份(走到该步现读**全文**,别凭记忆默写)

| 步 | 干什么 | 读哪份(整份) |
|---|---|---|
| **讨论** | Step 0–4、挑战前提、定 scope、细化选定方向、领域对齐——设计阶段全部讨论方法论 + 角色声音 + Hard Gate 细则 | `discussion.md` |
| **架构严谨度** | 细化方向时的架构判断本能 | `design-rigor.md` |
| **prototype / mockup** | 设计涉 UI/UX 或非平凡状态模型时:prototype 验状态模型、html mockup 定 UI/UX,产物原子拆进 acceptance | `prototype-mockup.md` |
| **写文档** | 信息足 + 方向确认后按模板一次成文(写作规则 / section 清单 / 每节细则 / UI 对照 / Cross-Plan Anchors 占位全在模板里,单一源) | `design-doc-template.md` |
| **自检** | 保存前逐条过,再告诉用户"设计文档已写入 `<path>`,请审阅" | `design-self-check.md` |

## 收尾:handoff 交还 flow(不自己跳阶段,不自派审)

设计自检过后,`mmw handoff` 交还引擎。结论词照判断选;**`mmw where` 的 `then` 已给好钉产物(只设计文档)的命令模板,照抄即可**:

- 设计 OK → `mmw handoff --conclusion pass --produced docs/design/<slug>.md` → flow 触发 ①设计审(Codex 独立审,只审设计文档),审过进 `to-issue` 阶段切片。
- 缺关键输入没法定稿 → `--conclusion needs-context`。
- 方向本身存疑(解错问题 / 该换框架)→ `--conclusion needs-redirection`。
- ①设计审打回 design gap → flow 回 design(`needs-repair`),停在本阶段改设计、改完 handoff 重审,不绕过。**Critical 必须修掉才能进 to-issue / plan。**

## 边界

没有设计文档前不进 to-issue / plan。已批准设计下的纯实现偏离不重走本流程——直接修代码。
