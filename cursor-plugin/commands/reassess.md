---
description: 停下来用磁盘状态重新判断真实情况,给可执行结论
argument-hint: ""
---

## 指令

用户要你**基于磁盘真相**重新判断,不靠会话记忆。

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

1. 跑 `mmw where`。若是 `UNMANAGED` / 无在管任务:说明当前不在在管 run,停止。
2. 结合 `mmw where` + `git status`(自己跑一次),给业务级结论:现在到哪、卡在哪、真实下一步是什么。
3. 给一个推荐动作(接着跑 / 换阶段 / 补哪道门);模糊处只给一个最该先做的,不铺开多方向。
4. 不自动续跑,等用户确认方向。
