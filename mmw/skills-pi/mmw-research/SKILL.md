---
name: mmw-research
description: 把 research 派出去，查当前仓库的现状或仓库之外的事实。要摸清代码实现、影响面、库或接口的一手说法时用它。
---

一个问题派一个 subagent。主 agent 继续处理不依赖该问题的工作。

## research 清单

先把本次全部问题列进一张表，再直接派发。一个问题只能走一个方向。

| 方向 | 适用范围 | 问题写法 | 出处 | 纪律文件 |
| --- | --- | --- | --- | --- |
| 内部 | 当前仓库的实现、seam、数据流、调用链、影响面、根因 | 一句话，能够判定真假 | `文件:行号` | [internal-brief.md](internal-brief.md) |
| 外部 | 第三方库、接口、规范和本地知识库 | 一句话，能够判定真假 | 一手链接，或命令原文与输出 | [external-brief.md](external-brief.md) |

一个函数、一个已知文件或一条命令能回答的问题，由主 agent 直接读取。需要真实运行才能回答的问题移交 `/mmw-prototype` 的 `EVIDENCE.md`。

## 派发

每个问题使用一份四栏 task：

| 栏 | 内容 |
| --- | --- |
| 目标 | 方向、角度和要回答的问题 |
| 读 | 对应纪律文件；内部 research 再加仓库根和 `mmw domain path` 返回的领域文档；已落盘背景，没有则写「无」 |
| 约束 | 只读；不改代码；不提方案；内部取证不得超出 task 点名的仓库根 |
| 验收 | 每条结论带出处；内部使用 `文件:行号`，外部使用一手链接或命令与输出 |

启动：调用原生 `subagent`，agent 设为 `mmw-investigator`，task 传四栏表全文。
互不依赖的问题在同一条消息中并行派发。

## 验证与综合

| 步骤 | 主 agent 的动作 |
| --- | --- |
| 过滤 | 丢弃没有出处的断言，并记录丢弃数量和内容 |
| 验证 | 按 `/mmw-verifying-agent-output` 打开出处；内部“没有找到”和外部二手来源必须重新查 |
| 综合 | 跨问题去重，把相关事实串起来，每条保留出处；综合不派发 |

subagent 原始报告不是 research。research 是主 agent 验证和综合后的最终内容。

## 保存人工审批关卡

每次 `/mmw-research` 只问一次。主 agent 完成综合后，先展示：

| research 主题 | 结论摘要 | 拟保存文件 | 拟保存路径 |
| --- | --- | --- | --- |
| `<research 主题>` | `<验证后的摘要>` | `README.md`、`report.md` 和确实需要的配套文件 | `<完整仓库相对路径>` |

然后询问用户是否保存本次 research。用户明确选择前，不创建 research 目录，不写 research 文件。

| 用户选择 | 处理 |
| --- | --- |
| 保存 | 按本节定义的 research 目录结构写入拟保存路径 |
| 不保存 | 不创建 research 目录；验证后的事实仍可写入当前 ticket、spec、ADR 或代码 |

先按下表确定 `产物目录`。当前 research 属于已有 effort 时，必须复用已有值，不得新建 slug。

| 场景 | `产物目录` 来源 |
| --- | --- |
| Wayfinder decision ticket | map 正文继承的 `产物目录` |
| 已绑定的普通任务 | 当前任务 slug |
| 其它技能调用 | 调用方已有的 `产物目录` |
| 用户直接调用，而且没有已有 effort | 主 agent 根据 research 所属主题提议一个稳定的单路径段；拟保存表展示该值和完整路径，用户可在同一次人工审批中确认或改正 |

普通任务运行 `mmw path research <产物目录>`。Wayfinder decision ticket 运行 `mmw path research <产物目录> issue-<编号>`。命令返回 research 的上级目录；在其下建立一个 `<research 主题 slug>/`：

```text
<research 路径>/<research 主题 slug>/
├── README.md
├── report.md
└── <research 配套文件>
```

| 文件 | 必须包含 |
| --- | --- |
| `README.md` | 问题、范围快照、结论摘要、文件索引、下游用途、未查清项；内部 research 记录 commit，外部 research 记录访问日期和版本 |
| `report.md` | 验证后的完整结论和逐条出处 |
| research 配套文件 | 用户批准保存的 HTML、字段表、脚本或其它文件；用途写进 `README.md` |

subagent 原始报告默认不落盘。确需跨进程转交时，使用 `mmw path scratch <产物目录> [issue-<编号>|task-<任务 slug>]`，与网页转储、抓取缓存和未采信内容一起写入 scratch，不进 Git。research 不进入 ADR 目录；只有满足 `/mmw-domain-modeling` 判据的决定才进入 ADR。

## 交回

| 调用方 | 交回内容 |
| --- | --- |
| `/mmw-wayfinder` | ticket 评论写验证后的结论；用户选择保存时，再加 research 索引路径 |
| 其它技能 | 验证后的事实与出处；用户选择保存且调用方确实需要时，再加 research 索引和精确文件路径 |
| 用户直接调用 | 当前会话中的结论、出处、未查清项和被过滤内容；用户选择保存时，再加 research 索引路径 |

保存不代表下游必须引用。下游只读取当前工作明确点名的 research 索引和精确文件，不递归读取 research 的上级目录。

下表准备移交下一技能时，先读 [`../mmw-start/phase-boundaries.md`](../mmw-start/phase-boundaries.md)，按顺序判断是否留在当前会话。自己继续和因 blocker 停下不触发阶段边界判断。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 调用方还在等待 | **移交**：带回验证后的事实；只有用户选择保存且调用方需要时，才带 research 路径 |
| 用户直接调用，research 已交回 | **停**：报告结论、出处、未查清项、过滤内容和用户选择的保存结果 |
| 出处不成立 | **自己继续**：重新派发原问题，明确纪律文件和仓库根 |
| 需要真实运行 | **移交**：`/mmw-prototype` 的 `EVIDENCE.md` |
| 问题无法写成可判真假的一句话 | **停**：说明它需要用户决定，或者必须先拆分 |
