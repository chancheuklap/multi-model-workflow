---
name: write-design-doc
description: "把模糊的功能想法 / bug / 反馈 / 截图 / PRD 讨论成一份完整、可评审、可拆分的设计文档。用户说『写个设计文档』『把这个想法理一理』『设计这个功能 / 改造』时使用。"
---

# write-design-doc

读 propose 钉的选定方向 + investigate 现状报告 → 选路（访谈 A / 综合 B）→ 与用户讨论细化选定方向 → 设计文档（+ 项目领域文档）→ 自检 → 拆 issue 立骨架 → handoff。

> **方向已定**：给 2-3 方案、HITL 指定哪个,是上游 propose 阶段做的(`prev_outputs` 带来 `docs/design/<slug>-direction.md`)。本 skill 不再提方案、不重选向——只把**已选定的方向**细化成设计文档。被事实击穿要换向 → handoff `needs-redirection` 回上游,别在这重摆备选。

**手动驱动**：你自己读报告、和用户讨论、写文档，无自动状态机、无自动 reviewer。

> **在 plugin2 编排里**：这是「想方案 / design」阶段，**主线程跑**（只有主线程能跟用户讨论）。系统探查已由 investigate 阶段做完、不在此重做；①设计审与换阶段归 flow 引擎，**本 skill 不自派审、不自己跳阶段**，做完 `mmw handoff` 交还。

**Hard Gate**：用户确认设计之前，不写代码、不创建骨架——真简单的设计可以几句话，但必须呈现并取得确认。

## 各步读哪份 reference（走到该步现读**全文**，别凭记忆默写）

| 步 | 干什么 | 读哪份（整份） |
|---|---|---|
| **讨论** | 选路 A/B、Step 0–4、挑战前提、定 scope、细化方向、领域对齐——设计阶段全部讨论方法论 + 角色声音 + Hard Gate 细则 | `references/discussion.md` |
| **架构严谨度** | 细化方向时的架构判断本能 | `references/design-rigor.md` |
| **写文档** | 信息足 + 方向确认后按模板一次成文（写作规则 / section 清单 / 每节细则 / UI 对照 / Cross-Plan Anchors 占位全在模板里，单一源） | `references/design-doc-template.md` |
| **自检** | 保存前逐条过，再告诉用户"设计文档已写入 `<path>`，请审阅" | `references/design-self-check.md` |

## 收尾：拆 issue → handoff

1. **拆 issue 立骨架**：用 `to-issues` skill 拆成可独立认领的 issue，**只立骨架、内容由 plan 阶段丰富**：大 issue 落 `docs/issues/<YYYY-MM-DD>-<slug>/`（slug 与设计对齐），标 AFK / HITL，填至少一条指向设计章节的 `## Design context refs`；`## Small issues` 留 `<!-- PENDING -->`，由 `write-plan-doc` 补全。（vertical-slice 方法论在 to-issues。）
2. **handoff 交还 flow**（不自己跳阶段，不自派审）：
   - 设计 OK → `mmw handoff --conclusion pass --produced docs/design/<slug>.md` → flow 触发 ①设计审（Codex 独立审），审过再进 plan。
   - 缺关键输入没法定稿 → `--conclusion needs-context`。
   - 方向本身存疑（解错问题 / 该换框架）→ `--conclusion needs-redirection`。
   - ①设计审打回 design gap → flow 回 design（`needs-repair`），停在本 skill 改设计、改完 handoff 重审，不绕过。**Critical 必须修掉才能进 plan。**

## 边界

没有设计文档前不进 plan。已批准设计下的纯实现偏离不重走本流程——直接修代码。
