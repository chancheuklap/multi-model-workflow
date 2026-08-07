---
name: mmw-to-spec
description: 把已经谈定的内容综合、审查并发布成 spec。用于用户直接要求写 spec，或者 `/mmw-grilling` 已经形成共同理解、`/mmw-prototype` 已经形成用户走查结论、`/mmw-wayfinder` 已关闭且 destination 是 spec 后进入本技能。
---

本技能使用当前对话上下文和对代码库的理解来生成一份 spec。**不要**访谈用户；只综合已经掌握的内容。

开始前，遵守目标仓库 `AGENTS.md` 的领域上下文规则。

## 读取已经形成的产物

先确定当前情况，再按匹配行读取已经形成的产物。

| 当前情况 | 要读取的已有产物 | 产物位置 | 怎样找到属于这份 spec 的内容 |
| --- | --- | --- | --- |
| 用户直接调用 To Spec | 当前对话中已经谈定的内容 | 当前对话 | 从用户提出本次需求的位置开始，读取已经明确形成的决定。不要使用尚未得到确认的建议或问题 |
| `/mmw-grilling` 完成后进入 To Spec | 用户已经确认的共同理解 | 当前对话中 `/mmw-grilling` 最后一次总结的问题、约束、决定、取舍和范围 | 找到用户明确确认的最后一份完整总结。`/mmw-grilling` 调用过 `/mmw-research` 或 `/mmw-prototype` 时，同时读取这份总结引用的结论和精确产物路径 |
| `/mmw-prototype` 完成后直接进入 To Spec | prototype 资产索引，以及索引记录的用户走查结论、选中产物、否定约束、长期证据和可复用内容 | `/mmw-prototype` 交回的 prototype 资产索引精确路径。该文件是 `<mmw path prototype <产物目录> [issue-<编号>]>/README.md` | 读取交回的 `README.md`。确认其中的“当前问题”属于这份 spec，再读取索引点名的选中产物、长期证据和可复用内容。不要扫描其他 prototype 目录 |
| `/mmw-wayfinder` 关闭 map 后进入 To Spec | 已关闭的 map、相关 decision ticket 的解决结果，以及解决结果链接的 prototype、research 或 evidence | 使用 `/mmw-wayfinder` 交回的 map URL 或编号，运行 `gh issue view <map 编号> --comments` | 确认 map 的 `Destination` 是这份 spec。沿 `Decisions so far` 中的 `context pointer` 读取相关 decision ticket。对每张相关 ticket 运行 `gh issue view <ticket 编号> --comments`，读取 resolution comment 和其中链接的精确产物。不要读取与 destination 无关的 ticket |

匹配行要求的产物不存在，或者产物中仍缺少一项产品、设计或架构决定时，写清缺少的完整内容和已经检查的位置，然后停止。不要在本技能中重新访谈，也不要猜测缺失产物的位置。

## 流程

1. 如果还没有探索过仓库，就探索仓库，以理解代码库当前状态。整份 spec 都使用项目领域术语表中的词汇，并遵守本次涉及范围内的所有 ADR。

2. 勾勒将用于测试这项功能的 seam。已有 seam 应优先于新 seam。使用尽可能高层的 seam。确实需要新 seam 时，在能够达到的最高层提出。整个代码库中的 seam 越少越好；理想数量是一个。

每个 seam 写清公开 interface、将在这个 seam 上验证的外部行为，以及选择这一层的原因。

| Seam | 验证的外部行为 | 选择这一层的原因 |
| --- | --- | --- |

向用户确认这些 seam 是否符合预期。用户确认前不要写 spec。

3. 完整读取 [spec-template.md](spec-template.md)，使用该模板编写 spec，然后发布到项目 issue tracker。添加 `ready-for-agent` triage 标签，不需要再次 triage。

按照以下顺序完成第 3 步：

1. 运行 `mmw path spec <任务 slug>`，把 spec 写入命令返回的精确路径。只记录已经形成的决定。写作中发现缺少决定时，写清缺少的完整内容和已经检查的位置，然后停止。
2. 从 Wayfinder 进入时，把相关 decision ticket 中互相链接的决定综合成一份 spec。prototype 的完整可运行资产继续留在 prototype 目录；spec 只吸收用户确认的决定和选中产物中可以准确表达决定的内容。research 只使用主 agent 已经验证并综合的事实。
3. 按照 `/mmw-review` 发起一次 ① spec 审。传入 spec 的精确路径，以及 spec 实际引用的 prototype 资产索引、选中产物、research 索引和精确文件。没有对应材料时写「无」。等待 `/mmw-review` 完成 finding 处置和采信项修复验收。
4. 向用户展示完整 spec、① spec 审结果和已经确认的 seam 清单，询问是否批准定稿和发布。用户要求修改时，按照用户意见修改 spec，再次展示完整结果。用户明确批准前不提交或发布 spec。
5. 用户明确批准后，先提交 spec 文件，再创建一张 spec issue。issue 正文保存 spec 摘要、`mmw path spec <任务 slug>` 返回的精确路径，以及本 spec 实际使用的输入出处。从 Wayfinder 进入时，输入出处包含 map 名称及其 URL 或编号。

```bash
mmw issue create --title "<spec 名称>" --body-file <摘要文件> --label ready-for-agent
```

发布完成的判据是：spec 文件已经提交；对应 spec issue 指向该文件；spec issue 带 `ready-for-agent`。这个标签表示 spec 人工审批关卡已经通过，不表示直接实施整份 spec。发布后不再进入 `/mmw-triage`。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| spec 已经提交并发布，而且对应 issue 带 `ready-for-agent` | **移交**：`/mmw-to-tickets`，把 spec 拆成 tracer bullet ticket |
