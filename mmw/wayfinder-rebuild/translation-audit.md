# Wayfinder 1.2.2 翻译审查

## 固定术语

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
| canonical artifact | `canonical artifact` |
| domain-agnostic、tracker-specific | `domain-agnostic`、`tracker-specific` |
| chart、charting、redraw | `chart`、`charting`、`redraw` |
| map（名词或动词） | `map` |
| native dependency relationship、native blocking | 保留英文原词 |
| context pointer、resolution comment | 保留英文原词 |
| breadth-first、wire、zoom、create-then-wire、rule out of scope | 保留英文原词 |
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
| index | 索引 |
| body | 正文 |
| title、name | 标题、名称 |
| link、URL | 链接、URL |
| label | 标签 |
| scope、out-of-scope work | 范围、out-of-scope 工作 |

## 逐段完整性检查

| 上游行 | 结论 |
| --- | --- |
| 3 | description 的 effort 大小、共享 map、decision ticket、一次一张和 destination 完成条件均已保留 |
| 7、9 | 松散想法、单 session 容量、fog、destination、decision ticket 与构建切片的区别、destination 示例和 domain-agnostic 均已保留 |
| 11-17 | planning 默认、Notes 覆盖、handoff 边界，以及 name 不得由裸 id、number 或 slug 代替均已保留 |
| 19-25 | canonical artifact、index-not-store、单一答案位置、tracker-specific 和 local-markdown fallback 均已保留 |
| 27-53 | map 低分辨率正文、每 session 加载一次、open ticket 查询，以及五个原始正文区块均已保留 |
| 55-71 | child issue、100K token session、Question、四种 label、claim、native blocking、frontier 和资产链接均已保留 |
| 73-80 | HITL、AFK 和四种 ticket type 的用途、角色、例子与完成判据均已保留 |
| 82-93 | map 刻意不完整、fog 的形成和转化、协作者路标，以及 fog-or-ticket 判据均已保留 |
| 95-101 | destination 固定范围、Out of scope、永不转成 ticket、关闭误入范围 ticket 和 Decisions so far 排除规则均已保留 |
| 103-116 | 两种调用模式、一 session 一 ticket、destination、breadth-first、无 fog 出口、create-then-wire、research branch 和建图停止条件均已保留 |
| 118-128 | map 输入、可选 ticket、claim、zoom、resolution comment、context pointer、newly-surfaced ticket、rule out of scope 和并发编辑均已保留 |

## 本轮发现并修正的问题

1. description 中“各会话逐张解决”可能被理解成一个会话连续解决多张 ticket，已经改成“一次解决一张 ticket”。
2. 上游标题 `Tickets` 曾被误写成单数 `Ticket`，已经恢复复数。
3. `canonical artifact`、`domain-agnostic` 和 `tracker-specific` 曾被直接换成中文表达，已经恢复英文 leading word。
4. `claim`、`unclaimed`、`native dependency relationship`、`unblocked`、`resolution comment`、`zoom`、`create-then-wire` 和 `rule out of scope` 曾被翻成不同中文操作词，已经统一恢复英文原词。
5. research 的 context pointer 曾被写成“从 ticket 提供”，没有说明指向关系。现在明确为“在 ticket 中留下指向该分支的 context pointer”。
6. `first steps takeable now` 保持复数含义，翻译为“当前可以采取的起始步骤”。它没有被改成单一“第一步”。
7. 上游第 114 行虽未出现 `all`，其指令对象是当前能够精确表述的 ticket 集合，并与第 88-91 行的 fog-or-ticket 判据共同要求全部建立。翻译使用“当前能够精确表述的 ticket 全部创建出来”，没有把范围缩成“第一批 ticket”。
8. `chart/charting` 曾被分别翻成“画、绘制、建图”，已经统一恢复英文原词。
9. `map` 的动词用法、`wire` 和 `throwaway branch` 曾被换成中文操作词，已经统一恢复英文原词。

## 无新增语义检查

翻译文件没有加入 MMW 的自动路由、worktree、报告验证、research 保存审批、产物目录、`issue-<编号>` 子目录、ADR、领域 leaf、提前切 spec、收尾流程或宿主动作。100K token session、local-markdown fallback、throwaway research branch 和用户选择无 fog 后续方式均按上游保留，即使这些内容以后会被 MMW 有意调整。
