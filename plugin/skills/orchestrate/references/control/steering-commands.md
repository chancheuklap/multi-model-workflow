# 控制面指挥(command → 机械动作)

用户中途指挥在管 run 的完整动作表。command 是第一入口;自然语言只做次级兼容,命中后走同一动作。所有副作用走 `mmw`,不新开平行编排。有 active run 才接受副作用类命令;无 active run 说明无对象、不伪造状态。

## 命令表

| 命令 | 用户意图 | 机械动作 |
| --- | --- | --- |
| `/progress` | 看进度板 | `mmw progress render --stdout`,照板汇报 |
| `/reassess` | 重新判断真实状态 | 跑 `mmw where` + `git status` 摘要,读盘后给业务结论与建议下一步(不靠会话记忆) |
| `/skip-current` | 当前步先放下 | 记 blocked/skipped 后推进:落地步用 `mmw loop softstop`(留痕)或推进游标;说明放下了什么 |
| `/rescope <说明>` | 砍/加范围 | 更新范围;必要时回流 design/plan(`mmw` 阶段推进/掉头);大改先确认基线 |
| `/replan-remaining` | 保留已完成,重做后续 | 回流 plan 修订,已完成不动 |
| `/force-validate` | 立刻跑当前层审查 | 触发当前阶段合法 review(`mmw review start --stage <当前层>`) |
| `/attended` | 切回有人 | `mmw unattended exit`(回 attended) |
| `/unattended` | 进强无人 | `mmw unattended enter`(过门禁);合同见 `control/attendance.md` |
| `/side-finding issue\|fix` | 手动指定计划外处置 | `mmw side-finding record --tag <t> --disposition issue\|fix --finding <s>` |

## 计划外分流:开 issue 或当场修

在**代码落地**或**验收**中发现计划外的 bug / 需改内容时,按值守档处置(worker 标签枚举不变,变的是 Coordinator 处置):

- **attended**:必须用 AskUserQuestion 问一次(见下),二选一。
- **afk**:按默认策略自动选,`mmw side-finding record` 落 open_items + 板刷新。
- **unattended**:按进入时 policy(`side_finding_default`)自动选,**不提问**。

也可由用户主动 `/side-finding issue|fix` 覆盖当前项。

### attended 问法(AskUserQuestion,不用长 Decision Brief)

```
header: 计划外问题
question: <一句话是什么 + 挡/不挡当前交付>
options:
  - label: 开 issue
    description: 记入 open_items,主交付继续
  - label: 当场修
    description: 纳入当前合法修复范围立即处理
```

仅当需解释复杂权衡才升格 Decision Brief。

### afk / unattended 默认策略

| 标签 / 情形 | 默认 |
| --- | --- |
| `bug` 且挡住当前交付 | 当场修(fix) |
| `bug` 且不挡当前交付 | 开 issue |
| `out-of-scope` | 开 issue |
| `needs-evaluation` | 开 issue;仅当明确属当前 scope 且改动局部才当场修 |

**当场修第一刀不扩大现有合法修复边界**;用户要扩大则单独立项,不混进本切片。

## 次级兼容:自然语言

- 用户原话命中「进度 / 重估 / 跳过当前 / 无人值守 / 计划外 …」→ 映射到对应命令**同一动作**。
- 模糊指令先归 `/reassess`,再给一个推荐命令,不连问多个。
- 无 active run:说明无对象,不创建幽灵状态。
- 教学默认教 slash(带插件前缀 `/multi-model-workflow:*`),不把自然语言当主入口。
