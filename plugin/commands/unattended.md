---
description: 进入强无人值守(设计+计划已过门后放权,任何 agent 不再向用户提问)
argument-hint: ""
disable-model-invocation: true
disallowed-tools: AskUserQuestion
---

用户要进入**强无人值守**。这是副作用命令,只有用户手动敲才触发。

## 指令

先定位 mmw:

<!-- BEGIN: locate-mmw -->
会话开头 SessionStart hook 已报过 mmw 绝对路径的,直接用它(hook 从激活插件根跑,是权威)。没有才跑下面定位块——候选(缓存各版本 + 本地源安装)按版本取最高,不许 `head -1` 抓第一个:

```sh
P=~/.claude/plugins
MMW="$( { find "$P" -type f -path '*multi-model-workflow*/scripts/mmw.sh' 2>/dev/null
  jq -r '.["multi-model-workflow"].installLocation // empty' "$P/known_marketplaces.json" 2>/dev/null | sed 's|$|/plugin/scripts/mmw.sh|'
  } | while IFS= read -r f; do
    [ -f "$f" ] || continue
    r="${f%/scripts/mmw.sh}"
    v="$(jq -r '.version' "$r/.claude-plugin/plugin.json" 2>/dev/null || echo 0)"
    printf '%s %s\n' "$v" "$f"
  done | sort -V | tail -1 | cut -d' ' -f2- )"
echo "MMW=$MMW"
```

`mmw X` ≡ `bash "$MMW" X`;每个新 shell 用回显的绝对路径,别指望 shell 变量跨调用留存。
<!-- END: locate-mmw -->

跑 `mmw unattended enter`,按进入门禁的结果处置:

1. 若输出 `UNATTENDED-ENTERED`:
   - 告诉用户已进入强无人值守,并复述 policy。
   - **从现在起本会话激活 no-question 合同**:不调用 AskUserQuestion、不向用户提任何问题;软停自决留痕,遇预算顶/设计打穿/外部环境/无自动路径才硬停并写进度板等用户回来。
   - 继续按 workflow 跑,不停下问人。
2. 若输出以 `ERROR: 拒绝进入`:照实告诉用户缺哪道门(设计未过门 / 计划未过审 / 有未答 HITL),**不降级、不硬进**;引导用户补齐后再敲本命令。
3. 若报 `ERROR: 当前不是在管任务 worktree`:说明当前不在在管任务,无 run 可进入。

> no-question 权威是磁盘 `task.json.attendance`,不是运行时工具限制:每次续跑(含 compaction 恢复)先读盘 mode=unattended 即自我约束。用户下一条消息会自动解除强无人假设(需再敲本命令重新进入)。
