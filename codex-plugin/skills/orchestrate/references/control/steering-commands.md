# 控制面指挥(command → 机械动作)

用户中途指挥在管 run 的完整动作表。command 是第一入口;自然语言只做次级兼容,命中后走同一动作。所有副作用走 `mmw`,不新开平行编排。有 active run 才接受副作用类命令;无 active run 说明无对象、不伪造状态。

## 命令表

| 命令 | 用户意图 | 机械动作 |
| --- | --- | --- |
| `/progress` | 看进度板 | `mmw progress render --stdout`,照板汇报 |
| `/reassess` | 重新判断真实状态 | 跑 `mmw where` + `git status` 摘要,读盘后给业务结论与建议下一步(不靠会话记忆) |
| `/approve-design` | 确认设计,过门放权 | `mmw approve [--report <承重文档>]...`(唯一人闸;引擎盖指纹、切 afk、推进) |
| `/skip-current` | 当前步先放下 | 登记后继续别的(落 open_items 留痕);说明放下了什么 |
| `/rescope <说明>` | 砍/加范围 | 更新范围;要回上游改就明确翻译成引擎动作:`mmw handoff --conclusion needs-redirection --to-phase <design|plan|...>`(回哪级向用户说清);改了已确认的设计 → 改完请用户重新 `/approve-design`;大改先确认基线 |
| `/replan-remaining` | 保留已完成,重做后续 | `mmw handoff --conclusion needs-redirection --to-phase plan` 回流 plan 修订;已完成的落地不动,把"哪些保留"先说给用户 |
| `/force-validate` | 立刻跑当前层审查 | 触发当前阶段合法 review(`mmw review start --stage <当前层>`) |
| `/attended` | 切回有人 | `mmw unattended exit`(回 attended) |
| `/unattended` | 进强无人 | `mmw unattended enter`(过门禁);合同见 `control/attendance.md` |
| `/side-finding issue\|fix` | 手动指定计划外处置 | `mmw side-finding record --tag <t> --disposition issue\|fix --finding <s>` |

**用户说「回设计 / 回上一步 / 重新讨论 X」而没敲命令**:这就是回退意图,直接翻译成 `mmw handoff --conclusion needs-redirection [--to-phase <阶段>]` 执行——讨论态掉头不计成本,不用劝用户"要不还是往前走"。

## 计划外分流:开 issue 或当场修

在**代码落地**或**验收**中发现计划外的 bug / 需改内容时,按值守档处置(worker 标签枚举不变,变的是 Coordinator 处置):

- **attended**:必须用 ask_user 问一次,二选一。
- **afk**:按默认策略自动选,`mmw side-finding record` 落 open_items + 板刷新。
- **unattended**:按进入时 policy(`side_finding_default`)自动选,**不提问**。

也可由用户主动 `/side-finding issue|fix` 覆盖当前项。

### attended 问法(ask_user,不用长 Decision Brief)

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

- 用户原话命中「进度 / 重估 / 确认设计 / 跳过当前 / 回上一步 / 无人值守 / 计划外 …」→ 映射到对应命令**同一动作**(唯一例外:确认设计必须用户亲敲 `/approve-design`,口头同意时请他敲,不代跑)。
- 模糊指令先归 `/reassess`,再给一个推荐命令,不连问多个。
- 无 active run:说明无对象,不创建幽灵状态。
- 教学默认教 slash(带插件前缀 `/multi-model-workflow:*`),不把自然语言当主入口。
