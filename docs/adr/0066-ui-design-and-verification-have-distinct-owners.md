---
date: 2026-10-30
amends: [0055]
---

# Design a UI 推进界面设计，prototype 构建原型，四个 verification skills 按需提供检查方法

Design a UI 负责本次界面设计的范围、主人试用、反复迭代、design freeze 和交回结果。prototype 的 UI 方法构建或更新完整可操作的页面，LOGIC、EXP、SKETCH 继续作为可复用方法。开发准备仍归 Develop a change，写 spec、ticket 和执行仍归原组件。明确要求的小修复和行为保持任务使用真实产品基线，不为满足流程而虚构 winner；有新设计问题时仍先做完整原型并由主人确认。这是对 ADR 0055 适用条件的修改，其余本地原型、同一套双 target 测试和执行期 UI 验收只读的约定继续成立。

## 为什么这样分

主人要求沿用 ADR 0064 的经验，系统性重组前端流程。互动、暂停和多步骤本身不决定组件类型。Design a UI 有独立的设计结果，也会调用原型、研究和决定方法；构建一个候选又能被单独请求，因此两者分别归 Playbook 和 Skill。

create-verification-skill 保留产品级环境、运行方法和 feature map 的生成。Prepare environment 可单独进入，避免尚无原型时要求先完成原型验证。Generate and prove 在有实际产品或可运行原型后证明生成结果。maintain-verification-skill 保留 Find affected features 的只读查找和主人要求的全产品维护。

prepare-ui-acceptance 把已定的新设计、已复现的修复要求或现有行为变成本次固定步骤的验收。通用测试判断仍归 test-audit。独立票、batch 和专业准备入口共用 to-tickets 的 Prepare verification，先取得缺少的产品检查方法，再准备本次验收。

create-formal-verification-skill 和 maintain-formal-verification-skill 分别建立检查、修正未随代码更新的检查。普通相关改动按生成的项目内 skill 同步模型与真实代码。尚无代码时，准备步骤确定规则、工具、路径和固定 CHECK，由实现票写出代码后生成；不声称模型证明未来代码。formal 文件在 Owns 内可以修改，既定 UI 验收仍只读，不能仅按 verify-* 名称区分。

advisor 审查后补清直接设计请求复用现有准备记录与 effort branch 的入口，以及现有 Tests reviewer 对 formal 模型、真实代码对应、假设、范围和故意破坏证据的审查。没有增加 reviewer、运行阶段或调度协议。

## Considered Options

- 把 UI、LOGIC、EXP、SKETCH 全改成 Playbook。否决。后三种仍能交回明确问题的实验或结构结果，无须另设外层流程。
- 让 Develop a change 管理所有前端互动和验证维护。否决。它会重复 mmw-mode 的入口选择和专门方法的责任。
- 每个 UI ticket 都先生成新原型或重建 verify skill。否决。已定修复和行为保持有真实基线，已有产品方法可以直接复用。
- 采用上游 statechart runtime。未采用。本次读取原生 checker 结果并在真实代码上解释反例，不声称具有 statechart 的自动报告能力。

## Consequences

- 新增 Design a UI、prepare-ui-acceptance 和两个 formal skills，原 UI 方法及其调用者同批调整。tests-from-prototype 原文保存在 retired-skills。
- 六个 skills 的十八份分支 Markdown 移到各自 references/，保留原文件名。真实调用者、相对链接及路径消费者同批迁移，历史和只读上游引文保留原样。
- 产品检查和 formal 检查由同一准备步骤按需要取得，不成为每次前端任务的强制阶段。新项目仍先证明 design，再由 smoke ticket 完成 product 启动证明。
- 单票与 batch 的执行、criteria、review、主人验收和 PR 收尾继续使用原流程。此改动只提交到开发分支并开 PR，不合并、安装或发布。
