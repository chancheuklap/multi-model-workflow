# Wayfinder 与批量 Grilling 调查

## 结论

MMW 可以把 Grilling 改成按设计树的当前 frontier 批量提问。现有 Wayfinder 的 ticket、分支、结果集成和人工审批合同都位于 Grilling 外层，不依赖每轮只出现一个问题。

批量提问需要遵守一条范围边界：一场由 `wayfinder:grilling` ticket 发起的 Grilling 只解决这张 ticket 的决定。问答中新出现的独立决定需要写回 map，成为新的 ticket 或保留在 fog of war，留给新的会话处理。批量提问不表示在当前会话继续解决新 ticket。

上游当前已经使用这套组合。Wayfinder 调用 `/grilling`，而 `/grilling` 默认一次提出整个 frontier。上游没有为 Wayfinder 设置逐题例外，也没有保留独立的批量技能。[当前上游 Wayfinder](https://github.com/mattpocock/skills/blob/main/skills/engineering/wayfinder/SKILL.md)；[当前上游 Grilling](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md)

当前公开材料只能证明交互轮数下降的设计目标。上游声称约十三个问题可以从十三轮缩短到约三轮，但没有公布可复现的基准、运行日志、模型配置或 token 数据。[上游 PR #593](https://github.com/mattpocock/skills/pull/593)

## MMW Wayfinder 在哪里调用 Grilling

| 阶段 | 目的 | 完成边界 |
| --- | --- | --- |
| 建 map，确定 destination | 把 effort 的终点定成一两行话 | 用户认可 destination |
| 建 map，广度优先横扫 | 找出未决决定和当前第一步 | 有 fog of war 就建 map；没有就转 spec |
| 走链，解决 `wayfinder:grilling` ticket | 取得这张决定 ticket 的用户答案 | 记录答案、关闭 ticket、更新 map |

建 map 的两次 Grilling 都发生在 map 创建会话中。该会话明确只建 map，不解决任何 ticket（`mmw/skills/mmw-wayfinder/drawing.md:3-17`）。

走链时，一张 `wayfinder:grilling` ticket 是 HITL，由主 Agent 调用 `/mmw-grilling`。答案随后写成结案评论，ticket 关闭，map 的 `Decisions so far`、领域术语、ADR、fog of war 和受影响 ticket 再由 Wayfinder 更新（`mmw/skills/mmw-wayfinder/map-anatomy.md:39-76`；`mmw/skills/mmw-wayfinder/walking.md:25-49`）。

## 批量提问与 Wayfinder 外层合同

| 外层合同 | 是否依赖逐题提问 | 依据 |
| --- | --- | --- |
| 一张 ticket 只解一个决定 | 不依赖每轮问题数 | ticket 正文只保存要解决的一个决定（`mmw/skills/mmw-wayfinder/map-anatomy.md:39-49`） |
| HITL 决定必须由用户回答 | 不依赖每轮问题数 | Agent 不得代答（`mmw/skills/mmw-wayfinder/map-anatomy.md:55-70`） |
| 答案写入结案评论 | 不依赖每轮问题数 | Grilling 完成后统一记录（`mmw/skills/mmw-wayfinder/walking.md:40-49`） |
| 新决定进入 ticket 或 fog of war | 不依赖每轮问题数 | Wayfinder 在记录答案后更新 map（`mmw/skills/mmw-wayfinder/walking.md:48-49`） |
| 新解锁的 HITL ticket 使用新会话 | 不依赖每轮问题数 | 当前链不认领 HITL ticket，立即停止（`mmw/skills/mmw-wayfinder/walking.md:53-71`） |
| 分支验证和集成 | 不依赖每轮问题数 | 发生在链任务完成后（`mmw/skills/mmw-wayfinder/SKILL.md:33-43`） |
| 人工审批关卡 | 不依赖每轮问题数 | 唯一关卡在 `/mmw-to-spec` 第 7 步（`mmw/skills/mmw-wayfinder/map-anatomy.md:64`；`mmw/skills/mmw-to-spec/SKILL.md:95-117`） |

因此，批量提问改变的是 Grilling 与用户之间的交互次数。它不直接改变 ticket 数量、tracker 状态、worktree、分支集成或人工审批关卡。

## 真正的 Wayfinder 风险

上游 issue #628 报告了一种会话边界问题：用户在处理 map 的长会话中提出约七个新想法后，Agent 倾向于留在当前会话继续 Grilling。报告者希望新想法只进入 map，每张 Grilling ticket 再用独立会话处理。该 issue 仍为 open，没有维护者确认或关联修复。[上游 issue #628](https://github.com/mattpocock/skills/issues/628)

这个问题针对“在同一长会话继续解决新 ticket”，不是针对“一张 ticket 的一轮包含几个问题”。

MMW 当前已经提供两层防护：

1. 建 map 的会话只建 map，不解决 ticket（`mmw/skills/mmw-wayfinder/drawing.md:3`）。
2. 走链时，新解锁的 HITL ticket 不得在当前会话认领，链任务到此停止（`mmw/skills/mmw-wayfinder/walking.md:53-71`）。

批量 Grilling 必须保留这两层边界。当前 ticket 的问答中发现新的独立决定时，只把它写回 map，不在当前 Grilling 中继续解决。

## 上游性能证据

| 指标 | 当前证据 |
| --- | --- |
| 用户交互轮数 | 上游声称约十三个问题从十三轮缩短到约三轮 |
| 端到端耗时 | 没有可复现数据 |
| token 用量 | 没有数据 |
| 模型调用数 | 没有数据 |
| 后台调查并发收益 | 有方法说明，没有测量数据 |
| 问题遗漏率 | 没有数据 |
| 同轮依赖误判率 | 没有数据 |

上游文档明确承认 frontier 来自 Agent 判断，并非计算图。两个问题可能被错误地放在同一轮，后续答案才暴露它们存在依赖；处理方式是在下一轮重新打开受影响分支。[上游 Grilling 文档](https://github.com/mattpocock/skills/blob/main/docs/productivity/grilling.md)

社区对交互体验的反馈不一致。有人报告批量方式更快，也有人报告批量问题增加认知负担。现有反馈都不是受控测试。[上游 PR #593](https://github.com/mattpocock/skills/pull/593)；[上游 issue #663](https://github.com/mattpocock/skills/issues/663)

## MMW 改动影响面

MMW 的逐题合同目前重复在三个位置：

- `mmw-grilling` 的 description、完成说明和提问步骤（`mmw/skills/mmw-grilling/SKILL.md:3-33`）。
- `mmw-triage` 的 Grilling 调用步骤（`mmw/skills/mmw-triage/SKILL.md:81`）。
- Wayfinder 的 ticket 类型定义和解法（`mmw/skills/mmw-wayfinder/map-anatomy.md:72-81`；`mmw/skills/mmw-wayfinder/walking.md:31-38`）。

`present-ui-review` 是 Grilling 唯一的宿主动作。它发生在第一轮问题之前，物化后的各宿主行为没有规定每轮问题数，因此批量提问不需要改变宿主适配（`mmw/skills/mmw-grilling/SKILL.md:20-24`；`mmw/cli/lib/materialize_skills.py:155-169`）。

Prototype 的“一轮只回答一个问题”属于单个原型的证据合同。Domain Modeling 在首次建立 bounded context 时“一次只问一个问题”属于首次建模分支。两者都不应随 Grilling 改成批量提问（`mmw/skills/mmw-prototype/SKILL.md:12-16`；`mmw/skills/mmw-domain-modeling/SKILL.md:36`）。

## 证据边界

本调查没有找到 MMW 自身关于逐题和批量 Grilling 的运行基准、遥测或对照测试。上游“约十三个问题缩短到约三轮”只作为作者声明，不作为已验证的 MMW 性能结果。

调查报告中没有出处的断言过滤为零条。上游 issue 中的用户体验只作为问题报告和使用反馈，没有提升为已确认缺陷。
