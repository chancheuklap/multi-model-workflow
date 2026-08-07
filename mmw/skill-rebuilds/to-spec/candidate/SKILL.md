---
name: mmw-to-spec
description: 把已经谈定的内容综合、审查并发布成 spec。用于用户直接要求写 spec，或者其他技能在共同理解已经确认、prototype 走查已经形成结论、Wayfinder 已关闭且 destination 是 spec，或其他决定已经完整形成后明确移交到本技能。
---

本技能使用当前对话上下文和对代码库的理解来生成一份 spec。**不要**访谈用户；只综合已经掌握的内容。

MMW 调用方可以交回本次已经形成的决定和精确 context pointer。spec 记录已经形成的决定，不在写作过程中产生新决定。

开始前，遵守目标仓库 `AGENTS.md` 的领域上下文规则。

## 1. 收集这份 spec 使用的输入

使用当前对话，以及调用方或用户已经提供的精确 context pointer。输入来源只决定读取哪些材料，不改变第 2—7 步。

| 已有输入 | 读取方式 |
| --- | --- |
| 用户已经确认的共同理解 | 直接使用共同理解。领域术语和 ADR 按目标仓库的领域上下文规则读取，不要求调用方重复传递 |
| prototype 走查结论 | 先读取 prototype 资产索引，再读取索引点名的选中产物和这份 spec 实际使用的精确证据 |
| 已关闭的 Wayfinder map | 读取 map 的 `Destination`、`Decisions so far` 和 `Out of scope`；沿 `Decisions so far` 中的 context pointer 读取相关 decision ticket，不要求 Wayfinder 复制 ticket 内容或资产路径 |
| issue、agent brief 或用户选中的架构候选 | 读取对应 issue、agent brief 或候选，以及围绕它已经确认的共同理解 |
| 已保存的 research | 先读取 research 索引，再读取这份 spec 实际使用的精确文件 |
| 未保存的 research | 使用当前上下文中的已验证事实、出处和未查清项 |
| 用户点名的文档或其他材料 | 只读取用户点名的材料 |

如果输入仍缺少一项产品、设计或架构决定，写清缺少的完整问题和现有出处，然后停止。不要在本技能中重新访谈，也不要自行建立跨技能回退流程。

完成本步骤时，已经能够完整复述问题、方案、范围和已有决定；没有尚未解决的设计问题。

## 2. 理解代码库当前状态

如果还没有探索过仓库，就探索仓库，以理解代码库当前状态。整份 spec 都使用项目领域术语表中的词汇，并遵守本次涉及范围内的所有 ADR。

当前对话、已有材料和已经读取的代码足以说明现状时，不重复调查。只读取本次范围内的入口、公开 interface 和测试先例。会随代码或外部系统变化的关键事实使用当前出处。

## 3. 勾勒并确认测试 seam

勾勒将用于测试这项功能的 seam。已有 seam 应优先于新 seam。使用尽可能高层的 seam。确实需要新 seam 时，在能够达到的最高层提出。整个代码库中的 seam 越少越好；理想数量是一个。

每个 seam 写清公开 interface、将在这个 seam 上验证的外部行为，以及选择这一层的原因。

| Seam | 验证的外部行为 | 选择这一层的原因 |
| --- | --- | --- |

向用户展示完整 seam 清单，并确认这些 seam 是否符合预期。用户确认前不要写 spec。

## 4. 编写 spec

完整读取 [spec-template.md](spec-template.md)，再按模板编写 spec。运行 `mmw path spec <slug>`，把 spec 写入命令返回的精确路径。

只记录已经形成的决定。不要加入 TODO、待定项或由本技能推荐的新取向。写作中发现输入仍然缺少决定时，回到第 1 步，报告准确缺口并停止。

从 Wayfinder 进入时，把 map 中互相链接的决定综合成一份 spec。prototype 的完整可运行资产继续留在 prototype 目录；spec 只吸收用户确认的决定和选中产物中可以准确表达决定的内容。research 只使用主 agent 已经验证并综合的事实。

## 5. 发起 ① spec 审

按照 `/mmw-review` 发起一次 ① spec 审。传入 spec 的精确路径，以及 spec 实际引用的 prototype 资产索引、选中产物、research 索引和精确文件。没有对应材料时写「无」。

等待 `/mmw-review` 完成审查、finding 处置和采信项修复验收。只有当前 spec 已经完成 ① spec 审，才进入第 6 步。

## 6. 完成 spec 人工审批关卡

向用户展示完整 spec、① spec 审结果和已经确认的 seam 清单，并询问是否批准定稿和发布。

用户要求修改时，按照用户意见修改 spec，再次展示完整结果。用户明确批准前不提交或发布 spec。

## 7. 提交并发布

先提交 spec 文件，再更新 issue tracker。tracker 更新必须指向已经提交的 spec。

创建一张 spec issue。issue 正文保存 spec 摘要、`mmw path spec <slug>` 返回的精确路径，以及本 spec 实际使用的输入出处。从 Wayfinder 进入时，输入出处包含 map 名称及其 URL 或编号。

```bash
mmw issue create --title "<spec 名称>" --body-file <摘要文件> --label ready-for-agent
```

发布完成的判据是：spec 文件已经提交；对应 spec issue 指向该文件；spec issue 带 `ready-for-agent`。这个标签表示第 6 步的 spec 人工审批关卡已经通过，不表示直接实施整份 spec。发布后不再进入 `/mmw-triage`。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| spec 已经提交并发布，而且对应 issue 带 `ready-for-agent` | **移交**：`/mmw-to-tickets`，把 spec 拆成 tracer bullet ticket |
