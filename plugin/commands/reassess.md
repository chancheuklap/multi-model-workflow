---
description: 停下来用磁盘状态重新判断真实情况,给可执行结论
argument-hint: ""
---

## 指令

用户要你**基于磁盘真相**重新判断,不靠会话记忆。

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

1. 跑 `mmw where`。若是 `UNMANAGED` / 无在管任务:说明当前不在在管 run,停止。
2. 结合 `mmw where` + `git status`(自己跑一次),给业务级结论:现在到哪、卡在哪、真实下一步是什么。
3. 给一个推荐动作(接着跑 / 换阶段 / 补哪道门);模糊处只给一个最该先做的,不铺开多方向。
4. 不自动续跑,等用户确认方向。
