---
description: 进入强无人值守(设计+计划已过门后放权,任何 agent 不再向用户提问)
argument-hint: ""
disable-model-invocation: true
---

用户要进入**强无人值守**。这是副作用命令,只有用户手动敲才触发。

## 指令

先定位 mmw(无需环境变量;记住返回的绝对路径,下文 `mmw X` 即 `bash <该路径> X`):

```sh
if [ -n "${DROID_PLUGIN_ROOT:-}" ] || printf %s "$PATH" | grep -q '/.factory/bin'; then P=~/.factory/plugins; else P=~/.claude/plugins; fi
find "$P" -type f -path '*multi-model-workflow*/scripts/mmw.sh' 2>/dev/null | head -1
```

跑 `mmw unattended enter`,按进入门禁的结果处置:

1. 若输出 `UNATTENDED-ENTERED`:
   - 告诉用户已进入强无人值守,并复述 policy。
   - **从现在起本会话激活 no-question 合同**:不调用 AskUserQuestion、不向用户提任何问题;软停自决留痕,遇预算顶/设计打穿/外部环境/无自动路径才硬停并写进度板等用户回来。
   - 继续按 workflow 跑,不停下问人。
2. 若输出以 `ERROR: 拒绝进入`:照实告诉用户缺哪道门(设计未过门 / 计划未过审 / 有未答 HITL),**不降级、不硬进**;引导用户补齐后再敲本命令。
3. 若输出 `NO-ACTIVE-RUN` 或无 task.json:说明当前不在在管任务,无 run 可进入。

> no-question 权威是磁盘 `task.json.attendance`,不是运行时工具限制:每次续跑(含 compaction 恢复)先读盘 mode=unattended 即自我约束。用户下一条消息会自动解除强无人假设(需再敲本命令重新进入)。
