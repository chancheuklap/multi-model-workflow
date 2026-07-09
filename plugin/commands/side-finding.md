---
description: 手动指定计划外项处置:开 issue 记下,或当场修
argument-hint: "issue | fix"
disable-model-invocation: true
---

用户手动指定当前计划外项的处置。参数 `$ARGUMENTS`:`issue`(开 issue 记下)或 `fix`(当场修)。

## 指令

1. 读 `${CLAUDE_PLUGIN_ROOT}/skills/orchestrate/references/control/steering-commands.md`(计划外分流协议在里面)。
2. 确认当前计划外项的标签(bug/optimize/out-of-scope/needs-evaluation)与一句话摘要。
3. 落盘:
   - `issue` → `mmw side-finding record --tag <t> --disposition issue --finding "<摘要>"`
   - `fix` → `mmw side-finding record --tag <t> --disposition fix --finding "<摘要>"`
4. `fix` 第一刀**不扩大**现有合法修复边界;用户要扩大则单独立项。
5. 板已自动刷新;回报处置结果。
