---
name: mmw-to-spec
description: 把已经谈定的对话和证据综合、审查并发布成 spec。用于 Grilling 已经确认共同理解、prototype 已经形成用户结论、research 事实已经进入确定的方案、Wayfinder 已经建立 spec issue、其他调用方已经形成完整决定、实现阶段需要回补测试 seam，或用户直接要求把已经谈定的内容写成 spec。
---

本技能使用当前对话上下文、调用方交回的材料和对代码库的理解来生成一份 spec。**不要**访谈用户；只综合已经掌握的内容。spec 记录已经形成的决定，不在写作过程中产生新决定。

开始前，遵守目标仓库 `AGENTS.md` 的领域上下文规则。

## 1. 取得已经谈定的输入

先确定调用方，并取得当前分支需要的材料。只读取本次 spec 实际使用的内容。

| 调用方 | 取得的材料 |
| --- | --- |
| `/mmw-grilling` | 当前对话中已经确认的共同理解，以及本轮形成的领域术语和 ADR |
| `/mmw-prototype` | 当前问题、用户逐轮结论、prototype 资产索引、选中产物、当前验证事实、否定约束、UI 与后端的对应关系、可复用内容和精确证据路径 |
| `/mmw-research` | 已验证的事实、出处和未查清项；本次 spec 确实引用已保存 research 时，再读取 research 索引和精确文件 |
| `/mmw-wayfinder` | map 下不带 `wayfinder:` 标签的当前 spec issue；读取其中点名的决定、原样继承的 `产物目录`，以及确实需要的 prototype、research 或 evidence 精确路径 |
| `/mmw-improve-codebase-architecture`、`/mmw-triage` 或其他调用方 | 已经谈定的问题、方案、范围边界、测试 seam 初判和经过验证的现状事实；只把当前调用方实际提供的字段当作输入 |
| `/mmw-implement` | 当前 spec 和实现阶段发现缺少的测试 seam；本次只补 seam，不重写其他内容 |
| 用户直接调用 | 当前对话中已经谈定的内容；没有单独的上游产物 |

逐项检查输入是否仍有未决内容：

- 产品、设计或架构决定尚未形成时，移交 `/mmw-grilling`，并停止本步骤。
- 问题必须通过可运行资产才能判断时，移交 `/mmw-prototype`，并停止本步骤。
- 问题需要多个独立角度或多份一手来源才能取得事实时，移交 `/mmw-research`，并停止本步骤。
- Wayfinder 派生的 spec 仍缺少一项必须通过 decision ticket 才能形成的决定或事实时，把 map 编号、spec issue 编号、缺少的完整问题和已有出处交回 `/mmw-wayfinder`，并停止本步骤。`/mmw-wayfinder` 负责重新接管 map、decision ticket 和分支集成。

一个仓库文件、一个符号或一次直接查询能够补齐的代码库事实不属于未决设计。把它留给第 2 步直接读取。

只有问题、方案、范围边界和已有决定都能够完整复述，而且没有未解决的设计问题时，才进入第 2 步。

## 2. 理解代码库现状

如果还没有探索过仓库，就探索仓库，以理解代码库当前状态。当前对话、调用方材料和已经读取的代码足以说明现状时，直接使用这些内容。不要重复执行 research，也不要重新验证 `/mmw-research` 已经交回的已验证事实。

如果还不了解代码库现状，直接读取本次范围内的入口、公开 interface、调用方和测试先例。只有缺口确实需要多个独立角度系统取证时，才调用 `/mmw-research`。

整份 spec 使用项目领域术语，并遵守本次范围内的 ADR。当前代码状态、外部合同和其他会随时间变化的事实必须带出处。用户已经确认的决定必须能够追溯到当前对话、Wayfinder decision ticket、prototype 走查结论或 research 结论。

完成本步骤时，现状事实已经足以支撑已有决定，所有关键事实都有当前出处。

## 3. 勾勒并确认测试 seam

勾勒将用于测试这项功能的 seam。已有 seam 应优先于新 seam。使用尽可能高层的 seam。确实需要新 seam 时，在能够达到的最高层提出。整个代码库中的 seam 越少越好；理想数量是一个。

每个 seam 写清三个项目：公开 interface、将在这个 seam 上验证的外部行为，以及选择这一层的原因。

| Seam | 验证的外部行为 | 选择这一层的原因 |
| --- | --- | --- |

向用户展示完整 seam 清单，并确认这些 seam 是否符合预期。用户要求修改时，修改清单并再次确认。用户确认前不要写 spec。

从 `/mmw-implement` 回来补 seam 时，只执行本步骤。用户确认后，把更新后的 spec 提交到当前任务分支，再回到 `/mmw-implement`。不要重写 spec 的其他 section，也不要重新执行 ① spec 审。

## 4. 编写 spec

完整读取 [spec-template.md](spec-template.md)，再按模板编写 spec。读取目标仓库 `.mmw.json` 中的 `paths.specs`；spec 路径是 `<paths.specs>/<slug>/<slug>.md`。

只记录已经形成的决定。不要加入 TODO、待定项或由本技能推荐的新取向。写作中发现输入仍然缺少决定时，停止写作并回到第 1 步处理。

从 Wayfinder 进入时，按以下关系综合，不重新讨论：

| Wayfinder 内容 | spec 内容 |
| --- | --- |
| Destination | `Problem Statement` 和 `Solution` |
| 已关闭 decision ticket 中与当前 spec 有关的决定 | `Implementation Decisions` 及其他对应 section |
| Out of scope | `Out of Scope` |
| spec issue 点名的 prototype、research 或 evidence | spec 抬头的输入出处，以及对应的决定、现状事实或视觉合同 |

prototype 的完整可运行资产继续留在 prototype 目录。spec 只吸收用户确认的结论、选中产物、否定约束和可移植决定。subagent 原始报告、网页转储和未采信内容不进入 spec；只使用主 agent 已经验证并综合的 research 事实，并在需要时引用 research 索引和精确文件。

## 5. 检查 spec

逐项检查，发现问题就修改 spec，再从本节第一项重新检查：

- `Problem Statement` 和 `Solution` 从用户角度准确记录已经谈定的问题和方案。
- `User Stories` 极其详尽地覆盖本次真实存在的角色、行为、失败和边界，没有为了增加长度编造场景。
- 每项 `Implementation Decisions` 都来自已经形成的决定，并且写清决定内容和相关取舍。
- `Implementation Decisions` 不包含具体文件路径或代码片段。prototype 中比文字更精确地编码决定的片段只保留决定信息密集的部分，并注明 prototype 出处。
- `Testing Decisions` 说明好测试只验证外部行为，不验证实现细节；列出测试 module、测试先例和用户已经确认的 seam。
- `Out of Scope` 完整记录已经明确排除的内容。
- 当前状态事实都有当前出处，领域术语和 ADR 没有冲突。
- 来自 prototype 或 research 的内容只引用当前 spec 使用的索引、精确文件和精确证据，没有递归引用整个目录。
- 条件式 section 只在当前 spec 确实涉及对应内容时出现。没有真实内容的 `Further Notes` 和其他条件式 section 已经删除。
- spec 没有 TODO 或未决决定，也没有本技能自行补出的决定。

全部项目通过后，进入第 6 步。

## 6. 发起 ① spec 审

按照 `/mmw-review` 发起一次 ① spec 审。设计内容审检查 spec 能否完整表达问题、行为、失败、界面和数据合同；项目一致性审检查领域术语、ADR、不变量、登记机制和现有基础设施。

审查不是人工审批关卡。主 agent 验证 findings，只修改已经采信的问题。修改完成后重新执行第 5 步，不重复发起 ① spec 审。

审查者交回 `needs-redirection` 时，停止本步骤。把方向为什么可疑、现有 spec 路径和审查者建议的重新框定完整交给用户，不自行改换产品方向。

## 7. 完成 spec 人工审批关卡

向用户展示以下内容：

1. 完整 spec，并说明它解决的问题和交付结果。
2. ① spec 审的 findings，以及每项 findings 的处理结果。
3. 用户已经确认的完整 seam 清单。

用户明确批准前不发布 spec。用户要求修改时，按意见修改 spec，重新执行第 5 步，然后再次展示完整结果；不要重复发起 ① spec 审。

用户明确批准后，人工审批关卡完成，进入第 8 步。

## 8. 提交并发布

先提交 spec 文件，再更新 issue tracker。tracker 更新必须指向已经提交的 spec。

普通任务使用一张新的 spec issue。issue 正文只保存完整 spec 的摘要和精确文件路径：

```bash
mmw issue create --title "<spec 名称>" --body-file <摘要文件> --label ready-for-agent
```

Wayfinder 已经建立 spec issue 时，更新原 issue 的正文并添加 `ready-for-agent`，不要创建第二张 issue：

```bash
gh issue edit <spec issue 编号> --body-file <摘要文件> --add-label ready-for-agent
```

发布完成的判据是：spec 文件已经提交；对应 spec issue 指向该文件；spec issue 带 `ready-for-agent`。这个标签记录第 7 步人工审批关卡已经通过，不表示直接实施整份 spec。

发布后不再进入 `/mmw-triage`。

准备进入下一技能时，完整读取 [`../mmw-start/phase-boundaries.md`](../mmw-start/phase-boundaries.md)，按其中的顺序判断是否继续当前会话。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| spec 已经提交并发布，而且对应 issue 带 `ready-for-agent` | **移交**：`/mmw-to-tickets`，把 spec 拆成 tracer bullet ticket |
| 从 `/mmw-implement` 回补的 seam 已经取得用户确认并提交 | **移交**：回到 `/mmw-implement`，继续原来的实现流程 |
