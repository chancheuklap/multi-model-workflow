# `to-tickets` 1.2.2 翻译审查

## 固定术语

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| ticket、issue、issue tracker | `ticket`、`issue`、`issue tracker` | 不把不同 tracker 对象混成一个中文词 |
| tracer bullet | `tracer bullet` | 上游方法 leading word |
| blocking edge、blocker、blocked by | `blocking edge`、blocker、`Blocked by` | 方法词、角色词和模板标题分别保留 |
| vertical slice、horizontal slice | 垂直切片、横向切片 | 有稳定中文译名 |
| prefactor | `prefactor` | 上游方法词，不误写成通用重构 |
| wide refactor | `wide refactor` | 上游例外类型名称 |
| blast radius | `blast radius` | 上游 leading word |
| expand–contract | `expand–contract` | 上游迁移方法名称 |
| green、CI | `green`、`CI` | 测试状态词和行业缩写 |
| frontier | `frontier` | 上游 leading word和 MMW canonical 术语 |
| parent、sub-issue | parent、`sub-issue` | tracker 关系词，不与 blocker 混同 |
| `ready-for-agent` | 保留原文 | 标签和状态字面量 |
| acceptance criterion | 验收判据 | 有稳定中文译名 |

## 逐行完整性检查

空行只承担 Markdown 分隔，不包含待翻译文字。下表逐一登记其他每一行。

| 上游行 | 本行翻译检查 |
| --- | --- |
| `SKILL.md:1` | YAML 起始分隔符已保留 |
| `SKILL.md:2` | `name: to-tickets` 字面量已保留 |
| `SKILL.md:3` | plan、spec、当前对话、整组 tracer bullet ticket、每张 ticket 的 blocking edge、配置 tracker、本地单文件文字 edge 和真实 tracker 原生 link 均已保留 |
| `SKILL.md:4` | `disable-model-invocation: true` 已保留 |
| `SKILL.md:5` | YAML 结束分隔符已保留 |
| `SKILL.md:7` | `To Tickets` 标题已保留 |
| `SKILL.md:9` | 三种输入、ticket 集合、tracer bullet 垂直切片和每张 ticket 声明 blocker 均已保留 |
| `SKILL.md:11` | issue tracker、triage 标签词汇和 `/setup-matt-pocock-skills` fallback 均已保留 |
| `SKILL.md:13` | `Process` 译为“流程” |
| `SKILL.md:15` | `Gather context` 译为“收集上下文”，步骤编号已保留 |
| `SKILL.md:17` | 使用既有对话上下文、三种引用类型、取得引用对象、读取完整正文和评论均已保留 |
| `SKILL.md:19` | `Explore the codebase (optional)` 的步骤编号和可选性质均已保留 |
| `SKILL.md:21` | 尚未探索时再探索、理解当前代码、ticket 标题和描述使用领域术语、遵守相关 ADR 均已保留 |
| `SKILL.md:23` | 寻找 prefactor 机会和原文引语的先后关系均已保留 |
| `SKILL.md:25` | `Draft vertical slices` 的步骤编号已保留 |
| `SKILL.md:27` | 工作必须拆成 tracer bullet ticket 已保留 |
| `SKILL.md:29` | `<vertical-slice-rules>` 起始标签已保留 |
| `SKILL.md:31` | 狭窄、完整、贯穿 schema、API、UI、测试、垂直而非单层横切均已保留 |
| `SKILL.md:32` | 每个完成切片可独立演示或验证已保留 |
| `SKILL.md:33` | 每个切片适合一个全新上下文窗口已保留 |
| `SKILL.md:34` | 所有 prefactor 先完成已保留 |
| `SKILL.md:36` | `</vertical-slice-rules>` 结束标签已保留 |
| `SKILL.md:38` | 每张 ticket 的 blocking edge、必须先完成的 ticket 和无 blocker 可立即开始均已保留 |
| `SKILL.md:40` | wide refactor 的机械改动定义、两个例子、blast radius、无法垂直保持 green、expand、分批迁移、每批 blocking、CI 持续 green、contract、无调用方、全部迁移批次 blocking、integration branch、最终 integrate-and-verify ticket 和只在最后承诺 green 均已逐项保留 |
| `SKILL.md:42` | `Quiz the user` 的步骤编号已保留，译为“询问用户”而非自动审查 |
| `SKILL.md:44` | 以编号清单展示拟议拆分，以及每张 ticket 都要展示信息均已保留 |
| `SKILL.md:46` | `Title` 和简短描述性名称已保留 |
| `SKILL.md:47` | `Blocked by`、其他 ticket 和“如果有”这一可空条件均已保留 |
| `SKILL.md:48` | `What it delivers` 和端到端行为已保留 |
| `SKILL.md:50` | “向用户询问”这一动作已保留 |
| `SKILL.md:52` | 粒度是否正确，以及太粗、太细两个方向均已保留 |
| `SKILL.md:53` | blocking edge 正确性和“只依赖真正 gate 它的 ticket”均已保留 |
| `SKILL.md:54` | 合并 ticket 和进一步拆分两个选项均已保留 |
| `SKILL.md:56` | 持续迭代直到用户批准拆分已保留 |
| `SKILL.md:58` | 发布到已配置 tracker 的步骤编号已保留 |
| `SKILL.md:60` | 只发布已批准 ticket、tracker 决定表达方式、ticket 内容相同、只有 edge 形态不同均已保留 |
| `SKILL.md:62` | 本地路径、每 ticket 一文件、从 `01` 编号、依赖顺序、blocker 在前、`Blocked by` 内容、单 ticket 模板和禁止合并文件均已保留 |
| `SKILL.md:63` | 真实 tracker、每 ticket 一 issue、依赖顺序、真实标识符、原生 blocking 或 sub-issue、无原生关系时的 fallback、默认 `ready-for-agent` 和 agent 可直接认领均已保留 |
| `SKILL.md:65` | frontier 定义和线性链从上到下均已保留 |
| `SKILL.md:67` | 不得关闭或修改 parent issue 已保留 |
| `SKILL.md:69` | `<local-ticket-template>` 起始标签已保留 |
| `SKILL.md:71` | 本地 ticket 的编号与标题格式已保留 |
| `SKILL.md:73` | `What to build`、用户角度、端到端行为和禁止逐层实施清单均已保留 |
| `SKILL.md:75` | `Blocked by`、阻塞 ticket 编号和标题，以及无阻塞字面值均已保留 |
| `SKILL.md:77` | `Status: ready-for-agent` 字面值已保留 |
| `SKILL.md:79` | 第一条验收判据复选框已保留 |
| `SKILL.md:80` | 第二条验收判据复选框已保留 |
| `SKILL.md:82` | `</local-ticket-template>` 结束标签已保留 |
| `SKILL.md:84` | `<issue-template>` 起始标签已保留 |
| `SKILL.md:86` | `Parent` 标题已保留 |
| `SKILL.md:88` | parent issue 引用和来源不是已有 issue 时省略章节均已保留 |
| `SKILL.md:90` | `What to build` 标题已保留 |
| `SKILL.md:92` | 用户角度、端到端行为和禁止逐层实施均已保留 |
| `SKILL.md:94` | `Acceptance criteria` 标题已保留 |
| `SKILL.md:96` | 第一条判据复选框已保留 |
| `SKILL.md:97` | 第二条判据复选框已保留 |
| `SKILL.md:99` | `Blocked by` 标题已保留 |
| `SKILL.md:101` | 每张 blocking ticket 的引用和无阻塞字面值均已保留 |
| `SKILL.md:103` | `</issue-template>` 结束标签已保留 |
| `SKILL.md:105` | 两种形态都禁止易过期路径和代码片段；prototype 片段例外、四类例子、内联、来源说明、只保留决定信息和排除可运行 demo 均已保留 |
| `agents/openai.yaml:1` | `interface` 字段已保留 |
| `agents/openai.yaml:2` | `display_name: "To Tickets"` 已保留 |
| `agents/openai.yaml:3` | 短描述中的 plan、拆分和 tracer bullet ticket 均已保留 |
| `agents/openai.yaml:4` | `policy` 字段已保留 |
| `agents/openai.yaml:5` | `allow_implicit_invocation: false` 已保留 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。两个上游文件的标题、正文、规则、长例外、问题和模板均有对应翻译 |
| 增写 | 无。没有加入 MMW spec issue、CLI、plan、`worker` 或人工审批关卡接线 |
| 曲解 | 无。先起草全部可见 ticket，再声明各自 blocking edge；没有误写成“只建第一批 ticket，再补阻塞关系” |
| 术语漂移 | 无。`tracer bullet`、`blocking edge`、`wide refactor`、`blast radius`、`expand–contract` 和 `frontier` 始终使用同一写法 |
