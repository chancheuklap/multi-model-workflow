---
description: 切回有人值守(退出强无人,恢复可向用户提问)
argument-hint: ""
---

用户要切回**有人值守**。

## 指令

先定位 mmw:

<!-- BEGIN: locate-mmw -->
会话开头 SessionStart hook 已报过 mmw 绝对路径的,直接用它(hook 从激活插件根跑,是权威)。没有才跑下面定位块——候选(缓存各版本 + 本地源安装)按版本取最高,不许 `head -1` 抓第一个:

```sh
P=~/.factory/plugins
MMW="$( { find "$P" -type f \( -path '*multi-model-workflow-droid*/scripts/mmw.sh' -o -path '*/droid-plugin/scripts/mmw.sh' \) 2>/dev/null
  jq -r '.["multi-model-workflow-droid"].installLocation // empty' "$P/known_marketplaces.json" 2>/dev/null | sed 's|$|/droid-plugin/scripts/mmw.sh|'
  } | while IFS= read -r f; do
    [ -f "$f" ] || continue
    r="${f%/scripts/mmw.sh}"
    v="$(jq -r '.version' "$r/.factory-plugin/plugin.json" 2>/dev/null || echo 0)"
    printf '%s %s\n' "$v" "$f"
  done | sort -V | tail -1 | cut -d' ' -f2- )"
echo "MMW=$MMW"
```

`mmw X` ≡ `bash "$MMW" X`;每个新 shell 用回显的绝对路径,别指望 shell 变量跨调用留存。
<!-- END: locate-mmw -->

1. 跑 `mmw unattended exit`,按输出处置:
2. 若输出 `ATTENDANCE=attended`:告诉用户已回到有人值守,后续软停会正常使用 AskUser 问人。
3. 若报 `ERROR: 当前不是在管任务 worktree`:说明当前不在在管任务,无 run 可切换。
4. 切回后照 `mmw where` 续跑。
