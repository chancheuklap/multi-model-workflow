# 值守档合同(attendance)

Coordinator 在任何阶段都按当前值守档决定"软停问不问人"。值守档权威在磁盘 `task.json.attendance`,跨阶段留存;`loop-state.attendance` 只是执行账本的派生缓存,loop init 时从 task.json 读入。

## 档位怎么来(两态一门的值守曲线)

| 时点 | 档 | 谁定的 |
| --- | --- | --- |
| develop 建档(讨论态:investigate/propose/design) | `attended` | prepare 写死——讨论期天生可问、必须对齐 |
| 用户 `/approve-design` 过门 | 自动切 `afk` | approve 引擎——过门即放权 |
| bug / small-change 建档 | `afk` | prepare 写死;但**动手前有一次轻确认**(scenario reference 定:根因/改动方案给用户一句话,等回复再动),之后自主 |
| 用户 `/unattended`(过门禁) | `unattended` | 用户显式 |
| 用户回来发任意消息 | 回 `attended`(unattended 时) | 合同(见「退出」) |
| 随时 | `mmw attend --mode attended|afk` 自由切 | 用户或用户授意 |

## 三模式合同

| 模式 | 软停(有合理默认) | 冒泡(缺输入/方向疑) | 计划外分流 | 可否向用户提问 |
| --- | --- | --- | --- | --- |
| `attended` | 停,AskQuestion（无则聊天固定选项）/ Decision Brief | 停 | 必问 A/B | 可以 |
| `afk` | 自决 + 留痕(`mmw loop softstop` 写 decisions) | 停(硬停) | 按默认策略自动 | 仅冒泡/硬门时 |
| `unattended` | 自决 + 留痕 | 停(硬停) | 按预授权 policy 自动 | **禁止** |

- `afk` 与 `unattended` 软停都自决;差别 = `unattended` 有进入门禁 + 禁问合同 + 预授权 policy,冒泡时也不问、只硬停写板。

## no-question:磁盘 mode 为权威

- **跨 compaction 真权威**:每次续跑(含会话重启 / compaction 恢复)**先读 `task.json.attendance`**;读到 `unattended` 就自我约束——不调用 AskQuestion、不向用户提任何问题（含聊天里的选择题）。
- Cursor Task 子代理(worker/reviewer)通常调不了 AskQuestion;主线程仍必须按盘上 mode 自我约束。有 AskQuestion 用工具;会话未挂载时用聊天固定选项——二者都算「提问」。

## 进入 unattended(全部满足才进)

跑 `mmw unattended enter`(即 `/unattended`)。脚本机械校验:

1. 设计已过门(develop 的 `design` 阶段已越过,即用户已 `/approve-design`;无 design 阶段的预设不适用)。
2. 计划已过审(`plan` 阶段已越过;无则不适用)。
3. 无未答的必须人答 HITL(`status≠waiting-user` 且当前执行账本无 pause)。

任一不满足 → 脚本 `ERROR: 拒绝进入` 并列出缺口。**不降级成 afk、不硬进**,补齐后重敲。进入成功写 `attendance=unattended` + `unattended_policy` + 刷新板。

## 预授权 policy(进入时写盘)

| 字段 | 含义 | 默认 |
| --- | --- | --- |
| `side_finding_default` | 计划外自动策略 | `auto`(用计划外分流默认表) |
| `hitl_unanswered` | 仍有未答 HITL | `reject_enter` |
| `design_gap` | 设计方向打穿 | `hard_stop` |
| `external_env` | 真机/生产/外部凭证 | `hard_stop` |
| `blocked_no_auto_path` | BLOCKED 且无自动路径 | `hard_stop` |
| `review_fail` | 审闸失败 | `rework_then_hard_stop`(走返工,反复不收敛硬停写板,不问人) |

覆盖:`mmw unattended enter --policy '<json>'`。

## unattended 运行中

1. 软停 → `mmw loop softstop`(自决留痕,不偷跳)。
2. 冒泡 / 硬停清单命中 → `mmw loop surface`(写 pause)+ `mmw progress render`(板写明原因),**不提问绕过**。
3. 唯一对用户输出:进度板刷新、硬停回执、完成回执。
4. 审闸失败按 `review_fail` 走返工;返工反复不收敛硬停写板,不问"要不要继续"。

## 退出

| 触发 | 结果 |
| --- | --- |
| `/attended`(`mmw unattended exit`) | 回 `attended`,恢复可提问 |
| 任务完成 Closing | mode 随 run 结束 |
| 硬停(用户不在场) | 盘上留 `unattended` + 板写原因,等用户回来 |
| **用户回来发任意消息** | Coordinator 把盘 `mode` 落回 `attended`(不留"盘写 unattended、实际闷头跑"的分叉);要续无人值守须再 `/unattended`。**两宿主同语义——不存在用户回来了还按无人档闷头跑。** |
