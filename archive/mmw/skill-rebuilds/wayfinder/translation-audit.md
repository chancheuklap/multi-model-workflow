# Wayfinder 1.2.2 翻译审查

## 本技能术语应用

共享术语只由 [上游技能翻译共享术语](../translation-terms.md) 定义。下表记录本技能的术语应用和独有术语，不建立第二份定义。

下列词是 Wayfinder 的 leading word、tracker 术语、代码字面值或上游技能名。中文翻译中保留英文原词，不为同一个词另造多个中文名称。

| 上游原词 | 统一写法 |
| --- | --- |
| Wayfinding、Wayfinder | `Wayfinding`、`Wayfinder` |
| destination、effort | `destination`、`effort` |
| map、ticket、decision ticket | `map`、`ticket`、`decision ticket` |
| fog、fog of war、frontier | 按上游原文分别写 `fog`、`fog of war`、`frontier` |
| issue、child issue、issue tracker、tracker | `issue`、`子 issue`、`issue tracker`、`tracker` |
| session、agent、subagent、dev | `session`、`agent`、`subagent`、`开发者` |
| spec、prototype、research、grilling、task | 保留英文原词 |
| claim、claimed、unclaimed | `claim`、`claimed`、`unclaimed` |
| blocking、blocked、blocker、unblocked | 保留英文原词 |
| open、assignee | `open`、`assignee` |
| chart、charting、redraw | `chart`、`charting`、`redraw` |
| map（名词或动词） | `map` |
| context pointer、resolution comment | 保留英文原词 |
| wire、zoom、create-then-wire、rule out of scope | 保留英文原词 |
| branch、throwaway branch | `branch`、`throwaway branch` |
| `wayfinder:map`、`wayfinder:<type>` | 保留代码字面值 |
| `/setup-matt-pocock-skills`、`/research`、`/prototype`、`/grilling`、`/domain-modeling` | 保留技能名 |
| `Destination`、`Notes`、`Decisions so far`、`Not yet specified`、`Out of scope`、`Question` | 保留 map 和 ticket 的标题字面值 |

以下普通词有稳定中文含义，统一使用一个译名：

| 上游原词 | 统一译名 |
| --- | --- |
| planning | 规划 |
| decision | 决定 |
| deliverable | 交付物 |
| artifact、asset | 产物、资产 |
| canonical artifact | 权威产物 |
| domain-agnostic | 领域无关 |
| tracker-specific | 由具体 tracker 决定 |
| native dependency relationship、native blocking | 原生依赖关系、原生 blocking |
| breadth-first | 广度优先 |
| index | 索引 |
| body | 正文 |
| title、name | 标题、名称 |
| link、URL | 链接、URL |
| label | 标签 |
| scope、out-of-scope work | 范围、out-of-scope 工作 |

## 逐行完整性检查

空行只承担 Markdown 分隔，不包含待翻译文字。

| 上游行 | 本行翻译检查 |
| --- | --- |
| `SKILL.md:1` | YAML 起始分隔符已保留 |
| `SKILL.md:2` | 技能名已保留 |
| `SKILL.md:3` | 超过一次 session、共享 map、decision ticket、逐张解决和路线清楚均已保留 |
| `SKILL.md:4` | 禁止模型隐式调用已保留 |
| `SKILL.md:5` | YAML 结束分隔符已保留 |
| `SKILL.md:7` | 松散想法、单 session 容量、fog、destination、chart、decision ticket 与构建切片区别均已保留 |
| `SKILL.md:9` | destination 因 effort 而异、先命名、三类终点例子和领域无关均已保留 |
| `SKILL.md:11` | Plan, don't do 标题已翻译 |
| `SKILL.md:13` | 默认 planning、完成判据、执行冲动代表交接边界和 Notes 覆盖均已保留 |
| `SKILL.md:15` | Refer by name 标题已翻译 |
| `SKILL.md:17` | 名称即标题、人读内容禁用裸 id、名称包裹链接及可读性理由均已保留 |
| `SKILL.md:19` | Map 标题已保留 |
| `SKILL.md:21` | 单一 tracker issue、wayfinder 标签、权威产物和子 issue 均已保留 |
| `SKILL.md:23` | map 是索引非存储库、决定只在 ticket 一处、只写概要和链接均已保留 |
| `SKILL.md:25` | 存放方式由 tracker 决定、setup fallback、Wayfinding operations 和 local Markdown 默认均已保留 |
| `SKILL.md:27` | map 正文标题已翻译 |
| `SKILL.md:29` | 低分辨率、每 session 一次、不列 open ticket 且通过查询取得均已保留 |
| `SKILL.md:31` | Markdown 代码块起始已保留 |
| `SKILL.md:32` | Destination 标题已保留 |
| `SKILL.md:34` | destination 内容、三类终点、一两行和选 ticket 前校准均已保留 |
| `SKILL.md:36` | Notes 标题已保留 |
| `SKILL.md:38` | 领域、每 session 技能和长期偏好占位均已翻译 |
| `SKILL.md:40` | Decisions so far 标题已保留 |
| `SKILL.md:42` | 索引、每个 closed ticket 一行、判断相关性和 zoom 链接已保留 |
| `SKILL.md:44` | 已关闭 ticket 名称链接和答案概要格式已保留 |
| `SKILL.md:46` | Not yet specified 标题已保留 |
| `SKILL.md:48` | 范围内 fog、暂不可建 ticket 和随 frontier 推进转化均已保留 |
| `SKILL.md:50` | Out of scope 标题已保留 |
| `SKILL.md:52` | 超过 destination 的工作已关闭且永不转化均已保留 |
| `SKILL.md:53` | Markdown 代码块结束已保留 |
| `SKILL.md:55` | Tickets 复数标题已保留 |
| `SKILL.md:57` | 子 issue 身份、tracker id、问题正文和一次 100K token session 粒度均已保留 |
| `SKILL.md:59` | Markdown 代码块起始已保留 |
| `SKILL.md:60` | Question 标题已保留 |
| `SKILL.md:62` | ticket 解决的决定或调查问题占位已翻译 |
| `SKILL.md:63` | Markdown 代码块结束已保留 |
| `SKILL.md:65` | wayfinder 类型标签、四种类型和链接均已保留 |
| `SKILL.md:67` | 工作前 claim、指派开发者、并发跳过和 assignee 等同 claim 均已保留 |
| `SKILL.md:69` | 原生依赖关系、UI 可视化、fallback、unblocked 和 frontier 定义均已保留 |
| `SKILL.md:71` | 答案不在正文、解决时记录及资产只链接不粘贴均已保留 |
| `SKILL.md:73` | Ticket Types 标题已保留 |
| `SKILL.md:75` | HITL、AFK、实时交流及 agent 不代答的人机合同均已保留 |
| `SKILL.md:77` | Research 的资源范围、事实目的、research subagent 和目录外知识条件均已保留 |
| `SKILL.md:78` | Prototype 提高讨论保真度、低成本且粗糙的具体产物、提纲、粗略版本、stub、UI 或 logic code、资产链接和使用问题均已保留 |
| `SKILL.md:79` | Grilling 是默认对话并总是调用两个技能已保留 |
| `SKILL.md:80` | Task 前置手工工作、三项排除、三类例子、唯一执行类型、HITL/AFK 和完成记录均已保留 |
| `SKILL.md:82` | Fog of war 标题已保留 |
| `SKILL.md:84` | 刻意不完整、fog 定义、依赖 open 问题、逐张转化至路线清楚且没有尚待解决的 ticket 均已保留 |
| `SKILL.md:86` | Not yet specified 内容、朝向 destination、范围内、松紧程度和协作者路标均已保留 |
| `SKILL.md:88` | fog 与 ticket 的判据是能否精确提问而非能否回答已保留 |
| `SKILL.md:90` | 问题清晰即建 ticket，即使被阻塞也一样已保留 |
| `SKILL.md:91` | 尚不清晰留作 fog、禁止预切和一块可转成多张或零张均已保留 |
| `SKILL.md:93` | Not yet specified 排除已决定、open ticket 和范围外内容已保留 |
| `SKILL.md:95` | Out of scope 标题已保留 |
| `SKILL.md:97` | destination 固定范围、范围外不是 fog、独立章节及按范围而非清晰度判定均已保留 |
| `SKILL.md:99` | 范围外永不转化、frontier 在终点停止、重画后是新 effort 均已保留 |
| `SKILL.md:101` | 排除范围是范围决定、关闭误入 ticket、记录一行和不进 Decisions so far 均已保留 |
| `SKILL.md:103` | 调用方式标题已翻译 |
| `SKILL.md:105` | 两种模式、每 session 不超过一张 ticket 和 research 例外均已保留 |
| `SKILL.md:107` | Chart the map 标题已保留 |
| `SKILL.md:109` | 用户以松散想法调用已翻译 |
| `SKILL.md:111` | 先命名 destination、运行两个技能、三类终点和先固定范围均已保留 |
| `SKILL.md:112` | 广度优先展开、open 决定、当前起始步骤和无 fog 时停止询问均已保留 |
| `SKILL.md:113` | 创建 map、标签、填写两节、清空决定和 fog 写入对应章节均已保留 |
| `SKILL.md:114` | 当前可精确表述的 ticket 全部创建、第二遍 wire、frontier/blocked 和其余 fog 均已保留 |
| `SKILL.md:115` | 每张 research ticket 并行派 subagent、throwaway branch 和 ticket 指针均已保留 |
| `SKILL.md:116` | charting 占一个 session 且本 session 不亲手解决 ticket 已保留 |
| `SKILL.md:118` | Work through the map 已准确翻译为“沿 map 推进”，没有写成一次走完整张 map |
| `SKILL.md:120` | map 可用 URL 或编号、ticket 可选且 agent 自选下一决定均已保留 |
| `SKILL.md:122` | 只加载低分辨率 map 而非全部 ticket 正文已保留 |
| `SKILL.md:123` | 用户点名优先、否则首张 frontier、工作前 claim 均已保留 |
| `SKILL.md:124` | 按需 zoom、读取相关或已关闭 ticket、Notes 技能和默认两个技能均已保留 |
| `SKILL.md:125` | resolution comment、关闭 issue 和 Decisions so far 指针均已保留 |
| `SKILL.md:126` | newly surfaced tickets、create-then-wire、fog 清理、rule out of scope 和失效 ticket 处理均已保留 |
| `SKILL.md:128` | 用户可并行运行 unblocked ticket 及并发编辑 tracker 预期已保留 |
| `agents/openai.yaml:1` | interface 配置键已保留 |
| `agents/openai.yaml:2` | 显示名已保留 |
| `agents/openai.yaml:3` | 大型 effort map 成 decision ticket 的短描述已翻译 |
| `agents/openai.yaml:4` | policy 配置键已保留 |
| `agents/openai.yaml:5` | 禁止隐式调用已保留 |

## 本轮发现并修正的问题

1. description 中“各会话逐张解决”可能被理解成一个会话连续解决多张 ticket，已经改成“一次解决一张 ticket”。
2. 上游标题 `Tickets` 曾被误写成单数 `Ticket`，已经恢复复数。
3. `canonical artifact`、`domain-agnostic` 和 `tracker-specific` 都是普通技术表达，不是 Wayfinder leading word；已经分别改为“权威产物”“领域无关”和“由具体 tracker 决定”。
4. `native dependency relationship` 和 `native blocking` 已改为正统中文“原生依赖关系”和“原生 blocking”；`claim`、`unclaimed`、`unblocked`、`resolution comment`、`zoom`、`create-then-wire` 和 `rule out of scope` 继续保留上游原词。
5. research 的 context pointer 曾被写成“从 ticket 提供”，没有说明指向关系。现在明确为“在 ticket 中留下指向该分支的 context pointer”。
6. `first steps takeable now` 保持复数含义，翻译为“当前可以采取的起始步骤”。它没有被改成单一“第一步”。
7. 上游第 114 行虽未出现 `all`，其指令对象是当前能够精确表述的 ticket 集合，并与第 88-91 行的 fog-or-ticket 判据共同要求全部建立。翻译使用“当前能够精确表述的 ticket 全部创建出来”，没有把范围缩成“第一批 ticket”。
8. `chart/charting` 曾被分别翻成“画、绘制、建图”，已经统一恢复英文原词。
9. `map` 的动词用法、`wire` 和 `throwaway branch` 曾被换成中文操作词，已经统一恢复英文原词。
10. `a spec to hand off and iterate on` 曾被加上上游没有使用的“下游”方位词，已经恢复为“要交出去并继续迭代的 spec”。
11. `until ... no tickets remain` 曾被写成“没有 ticket 留下”，容易被理解成已关闭的 ticket 也不再保留，已经明确为“没有尚待解决的 ticket”。
12. `Work through the map` 曾被写成“走完整张 map”，容易使 agent 在一个 session 内连续解决多张 ticket，已经改为“沿 map 推进”。

## 无新增语义检查

翻译文件没有加入 MMW 的自动路由、worktree、报告验证、research 保存审批、产物目录、`issue-<编号>` 子目录、ADR、领域 leaf、提前切 spec、收尾流程或宿主动作。100K token session、local-markdown fallback、throwaway research branch 和用户选择无 fog 后续方式均按上游保留，即使这些内容以后会被 MMW 有意调整。
