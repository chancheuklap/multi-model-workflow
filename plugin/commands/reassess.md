---
description: 停下来用磁盘状态重新判断真实情况,给可执行结论
argument-hint: ""
---

## 指令

用户要你**基于磁盘真相**重新判断,不靠会话记忆。

先定位 mmw:

<!-- BEGIN: locate-mmw -->
会话开头 SessionStart hook 已报过 mmw 绝对路径的,直接用它(hook 从激活插件根跑,是权威)。没有才跑下面定位块——**读实际激活的安装位**(installed_plugins.json),不扫缓存挑版本号(缓存里躺着历史版本,版本号最高 ≠ 正在运行的那个):

```sh
P=~/.claude/plugins
MMW="$( jq -r '.plugins | to_entries[] | select(.key | startswith("multi-model-workflow@")) | .value[0].installPath // empty' \
        "$P/installed_plugins.json" 2>/dev/null | head -1 | sed 's|$|/scripts/mmw.sh|' )"
[ -f "$MMW" ] || MMW="$( jq -r '.["multi-model-workflow"].installLocation // empty' "$P/known_marketplaces.json" 2>/dev/null | sed 's|$|/plugin/scripts/mmw.sh|' )"
[ -f "$MMW" ] && echo "MMW=$MMW" || echo "MMW 定位失败:插件未装?(装了才有 installed_plugins.json 条目)"
```

`mmw X` ≡ `bash "$MMW" X`;每个新 shell 用回显的绝对路径,别指望 shell 变量跨调用留存。**别用仓库里的相对路径 `plugin/scripts/mmw.sh` 当运行时**——在旧分支 worktree 里那是旧代码。
<!-- END: locate-mmw -->

1. 跑 `mmw where`。若是 `UNMANAGED` / 无在管任务:说明当前不在在管 run,停止。
2. 结合 `mmw where` + `git status`(自己跑一次),给业务级结论:现在到哪、卡在哪、真实下一步是什么。
3. 给一个推荐动作(接着跑 / 换阶段 / 补哪道门);模糊处只给一个最该先做的,不铺开多方向。
4. 不自动续跑,等用户确认方向。
