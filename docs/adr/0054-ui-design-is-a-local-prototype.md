---
date: 2026-10-18
amends: [0029, 0030, 0044, 0048]
---

# 界面设计在产品代码里做本地原型，Claude Design 退役

界面设计在产品自己的代码里做完整、可交互的本地原型，主人和 session 一对一迭代，说「就是这个」时 design freeze。winner 是界面的 baseline，worker 照抄外观与交互、按生产标准重写代码，同时做真后端。白天照 winner 写同一份 e2e 测试，在 `design` 和 `product` 两个 target 上跑，夜里只读；Spec 轴逐对看同一状态的原型与产品截图。这份决定采用 #1094 正文「最终方案」和 spec #1124 第 6、8 节，取代 0029、0030 的 Claude Design 与设计包流程，改写 0048 的界面 baseline；0048 的验证文件位置、白天写和夜里只读仍成立。

## 为什么这样定

- Claude Design 当年是为了让 worker 照设计做。本地 mockup 作 baseline 同样有效，`efforts/code-landing/prototypes/ui-gate/EXP/README.md` 的 `### round-2 — 2026-08-28` 表记录 mockup vs impl 在两个 viewport 都为 0.000%，复现 issue-534。问题在 worker 不照做，见 `9ff2d5b44:docs/research/code-landing/10-previous-attempt-postmortem.md` 第 96 行主人的原话。现在由 Read first 加 baseline-is-the-contract、先红后绿的 e2e 和 reviewer 管住，本地原型还能当真页面试用。ERP 的 22 个静态单页不能这样试。
- `design` target 对已有产品只比产品启动命令多一个环境变量，Electron 也一样。同一份测试没有 target 分支，落地后原型入口自然停用、测试不改。入口挂在产品代码里，主人试用的不是空壳。
- UI 原型不写 README。结论进 feature file，流程没有读 UI 原型 README 的步骤。
- 「产品能做什么」提交在 effort 分支或 `fix-<n>`，不直接进 project branch。后者只写产品现在能做的事，否则 maintain-verification-skill 会把「写了没做」当作描述错误。
- 前后端分仓库时，后端先落地，前端晚一夜。前端测试不截还没做的接口，免去以后靠人记得清理。
- 多份 spec 的 mount point 可以随前一夜 PR 进 project branch，留到它对应的功能落地再按页面拆。它只在环境变量打开时渲染原型，是到期必拆的临时入口，不是测试后门。
- Doctor 只在测试失败排查时跑，夜里不为每次正常运行重复检查。上游的「一觉得不对就先跑」不适合这条固定步骤的验收路径。
- 截图对并入 Spec 轴，不另开第五个轴。Correctness 轴保留。#1094 §7 记录的 45 份 review 中，它有 106 条复核成立的问题，出现在 39 份报告里，87 条当票修掉，覆盖其他轴不查的错误吞掉、表面修补和重跑后状态乱。
- 环境工具属于产品仓库，供手动试用、调试、排查和验证共用。验证技能的 Launch 只调用它，不自带另一套环境脚本。

## Considered Options

- **保留 Claude Design，把本地原型转成静态签字页。** 否决。主人已在真页面试过原型，再转一份静态页面不能增加判断，反而多一份要保持一致的设计。
- **按 target 分准备步骤，落地后改测试。** 否决。同一份步骤和断言才能证明原型里的操作在产品里成立；两套步骤会分叉。
- **逐句请主人确认 feature file 的「产品能做什么」。** 否决。主人确认的是原型。句子只取自 winner、已关闭的决策和术语表，每句有出处。规则以决策为准，叫法以术语表为准，样子和交互以原型为准；原型落后就修原型。
- **逐元素或像素比对，另开界面审查轴。** 否决。测试证明用户能做成什么，Spec 轴看截图对补足外观，四个轴已经覆盖各自的问题。

## Consequences

- 0029 的唯一源头和 pull、0030 的独立设计系统与不加载产品代码的约定，由产品内本地原型取代；design-pages 技能退役，不产生 `design/<product>/`。
- 0044 第 6 条由「句子只取自 winner、已关闭的决策和术语表，不请主人确认」取代。design freeze 前逐张对决策，把每条界面上可见的规则补进原型；主人只确认原型。
- API fake 只替未有接口，示例数据来自环境工具的种子数据，已有接口和登录走本机真后端。`Proof` 与 e2e 只证明用户看到什么、能做什么；真实存储由票的后端测试证明。
- 原型、feature file 的「产品能做什么」部分、以及 effort 里生成的环境工具和验证技能随 effort 的 PR 合入。UI 原型只有一份，结论进 feature file；LOGIC、EXP、SKETCH 的 README 保留。
- 原型和测试夜里只读，错误经 `contract` 子票退回白天。改原型要新一轮原型和 design freeze，PR 给主人的页面按同一状态并排放原型与产品截图。
