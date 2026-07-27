---
description: 进入强无人值守(设计+计划已过门后放权,任何 agent 不再向用户提问)
argument-hint: ""
disable-model-invocation: true
---

用户要进入**强无人值守**。这是副作用命令,只有用户手动敲才触发。

## 指令

先定位 mmw:

<!-- BEGIN: locate-mmw -->
会话开头的 mmw 分诊已经报告插件根绝对路径时，直接使用它。没有时读 pi 的实际安装配置；本地路径安装不会复制，`packages` 中的路径就是插件根：

```sh
MMW_ROOT="$(jq -r '
  .packages[]?
  | if type=="string" then . elif type=="object" then (.source // "") else "" end
  | select(test("(^|/)pi-plugin/?$"))
' ~/.pi/agent/settings.json 2>/dev/null | head -1)"
[ -d "$MMW_ROOT" ] || MMW_ROOT="$(pwd | sed -n 's|\(.*multi-model-workflow/pi-plugin\).*|\1|p')"
MMW="$MMW_ROOT/scripts/mmw.sh"
[ -f "$MMW" ] && echo "MMW=$MMW" || echo "MMW 定位失败：先确认 pi install <multi-model-workflow/pi-plugin 绝对路径> 已完成"
```

`mmw X` 等价于 `bash "$MMW" X`。每个新 shell 都使用回显的绝对路径，不依赖 shell 变量跨调用留存，也不要从其他宿主镜像目录取运行时代码。
<!-- END: locate-mmw -->

跑 `mmw unattended enter`,按进入门禁的结果处置:

1. 若输出 `UNATTENDED-ENTERED`:
   - 告诉用户已进入强无人值守,并复述 policy。
   - **从现在起本会话激活 no-question 合同**:不调用 ask_user_question、不向用户提任何问题;软停自决留痕,遇预算顶/设计打穿/外部环境/无自动路径才硬停并写进度板等用户回来。
   - 继续按 workflow 跑,不停下问人。
2. 若输出以 `ERROR: 拒绝进入`:照实告诉用户缺哪道门(设计未过门 / 计划未过审 / 有未答 HITL),**不降级、不硬进**;引导用户补齐后再敲本命令。
3. 若报 `ERROR: 当前不是在管任务 worktree`:说明当前不在在管任务,无 run 可进入。

> no-question 权威是磁盘 `task.json.attendance`,不是运行时工具限制:每次续跑(含 compaction 恢复)先读盘 mode=unattended 即自我约束。用户回来发任意消息即恢复 attended(两宿主同语义,不存在用户回来了还闷头跑);要续无人值守须再敲本命令重新进入。
