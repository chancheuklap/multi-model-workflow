---
description: 切回有人值守(退出强无人,恢复可向用户提问)
argument-hint: ""
---

用户要切回**有人值守**。

## 指令

先定位 mmw:

<!-- BEGIN: locate-mmw -->
会话开头的 mmw 分诊已经报告插件根绝对路径时，直接使用它。没有时读 Cursor 本地插件安装位；开发可用仓内路径或 `~/.cursor/plugins/local` 软链：

```sh
MMW_ROOT=""
if [ -n "${CURSOR_PLUGIN_ROOT:-}" ] && [ -f "$CURSOR_PLUGIN_ROOT/scripts/mmw.sh" ]; then
  MMW_ROOT="$CURSOR_PLUGIN_ROOT"
fi
if [ -z "$MMW_ROOT" ]; then
  for cand in \
    "$HOME/.cursor/plugins/local/multi-model-workflow-cursor" \
    "$(pwd | sed -n 's|\(.*multi-model-workflow\)/.*|\1/cursor-plugin|p')" \
    "$(pwd)/cursor-plugin"
  do
    [ -f "$cand/scripts/mmw.sh" ] || continue
    MMW_ROOT="$cand"
    break
  done
fi
MMW="$MMW_ROOT/scripts/mmw.sh"
[ -f "$MMW" ] && echo "MMW=$MMW" || echo "MMW 定位失败：先确认 cursor-plugin 已装到 ~/.cursor/plugins/local 或 CURSOR_PLUGIN_ROOT 已设"
```

`mmw X` 等价于 `bash "$MMW" X`。每个新 shell 都使用回显的绝对路径，不依赖 shell 变量跨调用留存，也不要从 `.pi` / `.claude` / `.factory` 宿主镜像目录取运行时代码。
<!-- END: locate-mmw -->

1. 跑 `mmw unattended exit`,按输出处置:
2. 若输出 `ATTENDANCE=attended`:告诉用户已回到有人值守,后续软停会正常使用 AskQuestion 问人。
3. 若报 `ERROR: 当前不是在管任务 worktree`:说明当前不在在管任务,无 run 可切换。
4. 切回后照 `mmw where` 续跑。
