---
date: 2026-10-30
amends: [0054]
---

# 普通代码改动共用 Develop a change 准备流程，专业方法作为 skill 按需组合

mmw-mode 按请求的结果和现有进度选择入口。Develop a change 只补已选定改动缺少的证据、决定和计划，产出独立 ticket 或 spec batch，再按既有授权交给 One ticket 或 Run a night。专业方法返回调用步骤，也可服务只读诊断、实现和验证。Authoring or modifying a skill 保留技能改动专有的取证、标准、文字作者例外和行为证明；大型改动把这些材料带入公共准备流程，不反向重启 Authoring。

## 为什么这样分

主人要求只描述人物和目标就能进入正确组件，并明确日常顺序包括讨论、设计、记录、规划、agent 实现、主人运行验收和 agent 收尾。目标明确的小任务应省去不需要的讨论和 spec；大型任务则可在同一准备中组合 bug、性能和重构方法。

按任务名字各写一份开票、准备和交接流程，会让这些共同规则漂移。把所有环节集中到 Develop 又会形成第二个 mode。因此入口选择留在 mmw-mode，未知位置由 Session pickup 重建，执行与恢复仍归现有执行器，PR 内反馈留在原交付流程。

to-spec 记录决定并返回 spec，to-tickets 写独立票或 batch，wayfinder 建图或解决一项决定，improve-codebase-architecture 返回候选报告。它们不因为被调用就扩大任务或取得执行授权。多个 spec 保留原有的一次一份和 fresh-session 边界。

独立票和 batch 共用写票判断标准，记录位置按实际材料区分。独立票的 review 约束进入 What to build 的非编号约束或 Read first 的 baseline，测试前提进入 Seam 和 Owns；batch 使用父 spec。完整写票格式由实际写票入口读取，开问题记录不加载它。

大型技能改动的 Prove it, once 在交付给主人验收前执行。合并后才证明会使“证明失败则挡住改动”的原要求无法成立。主人采纳 advisor 建议，移动已有证明，不增加证明次数；失败留在同一交付分支修正。测试把候选技能当隔离的被测材料，实际运行仍由冻结的 installed runtime 控制。

## Considered Options

- 保留五份代码任务 playbook，再在旁边增加只处理 spec 的 Develop。否决。共同开票和交接仍重复，大型组合任务仍被迫先选一种任务名字。
- 让 Develop 处理所有入口、运行恢复和验证。否决。它会重复 mmw-mode 和现有执行器的责任。
- 独立票也使用 batch 的父 spec、quiz 和记录位置。否决。小任务会被迫创建不需要的 spec，或由 agent 猜替代位置。
- 保留 finish 后的技能证明，再增加专用恢复分支。否决。PR 和 spec 已结束，补恢复步骤不能恢复待接受状态。

## Consequences

- 十一份旧 playbook 原样归档。八个方法 skills、一个公共准备 playbook 与它们的真实调用者同批迁移；模板与规则在使用者处保留一份。
- 当前 issue 的 Problem、effort 分支、已有证据与授权保持。历史 Playbook 题名提供上下文，不再使恢复者打开退役文件。
- worker、review、最终 criteria、events、watch 和调度协议保持。主人验收前的自动证明不能替代主人实际运行产品。
- 本改动落在开发分支，不安装或发布，也不让候选版本控制正在改变它的运行。
