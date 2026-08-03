---
description: 进入强无人值守(设计+计划已过门后放权,任何 agent 不再向用户提问)
argument-hint: ""
disable-model-invocation: true
---

用户要进入**强无人值守**。这是副作用命令,只有用户手动敲才触发。

## 指令

先定位 mmw:

<!-- BEGIN: locate-mmw -->
会话开头 SessionStart hook 已报过 mmw 绝对路径的,直接用它(hook 从激活插件根跑,是权威)。没有才跑下面定位块——**读实际激活的安装位**(installed_plugins.json),不扫缓存挑版本号(缓存里躺着历史版本,版本号最高 ≠ 正在运行的那个):

```sh
P=~/.factory/plugins
MMW="$( jq -r '.plugins | to_entries[] | select(.key | startswith("multi-model-workflow-droid@")) | .value[0].installPath // empty' \
        "$P/installed_plugins.json" 2>/dev/null | head -1 | sed 's|$|/scripts/mmw.sh|' )"
[ -f "$MMW" ] || MMW="$( jq -r '.["multi-model-workflow"].installLocation // empty' "$P/known_marketplaces.json" 2>/dev/null | sed 's|$|/droid-plugin/scripts/mmw.sh|' )"
[ -f "$MMW" ] && echo "MMW=$MMW" || echo "MMW 定位失败:插件未装?(装了才有 installed_plugins.json 条目)"
```

`mmw X` ≡ `bash "$MMW" X`;每个新 shell 用回显的绝对路径,别指望 shell 变量跨调用留存。**别用仓库里的相对路径 `droid-plugin/scripts/mmw.sh` 当运行时**——在旧分支 worktree 里那是旧代码。
<!-- END: locate-mmw -->

跑 `mmw unattended enter`,按进入门禁的结果处置:

1. 若输出 `UNATTENDED-ENTERED`:
   - 告诉用户已进入强无人值守,并复述 policy。
   - **从现在起本会话激活 no-question 合同**:不调用 AskUser、不向用户提任何问题;软停自决留痕,遇预算顶/设计打穿/外部环境/无自动路径才硬停并写进度板等用户回来。
   - 继续按 workflow 跑,不停下问人。
2. 若输出以 `ERROR: 拒绝进入`:照实告诉用户缺哪道门(设计未过门 / 计划未过审 / 有未答 HITL),**不降级、不硬进**;引导用户补齐后再敲本命令。
3. 若报 `ERROR: 当前不是在管任务 worktree`:说明当前不在在管任务,无 run 可进入。

> no-question 权威是磁盘 `task.json.attendance`,不是运行时工具限制:每次续跑(含 compaction 恢复)先读盘 mode=unattended 即自我约束。用户回来发任意消息即恢复 attended(两宿主同语义,不存在用户回来了还闷头跑);要续无人值守须再敲本命令重新进入。
