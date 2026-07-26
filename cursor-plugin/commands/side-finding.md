---
description: 手动指定计划外项处置:开 issue 记下,或当场修
argument-hint: "issue | fix"
disable-model-invocation: true
---

用户手动指定当前计划外项的处置。参数 `$ARGUMENTS`:`issue`(开 issue 记下)或 `fix`(当场修)。

## 指令

先定位 mmw(无需环境变量;记住返回的绝对路径,下文 `mmw X` 即 `bash <该路径> X`;插件根 = 该路径上两级目录):

<!-- BEGIN: locate-mmw -->
会话开头的 mmw 分诊已经报告插件根绝对路径时，直接使用它。没有时按安装位查找（Marketplace / Team Marketplace 安装后通常落在 Cursor plugins 目录；本地试装在 `~/.cursor/plugins/local`）：

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
# Marketplace 缓存安装位：按 name 扫一层
if [ -z "$MMW_ROOT" ]; then
  for cand in "$HOME"/.cursor/plugins/*/*/multi-model-workflow-cursor \
              "$HOME"/.cursor/plugins/*/multi-model-workflow-cursor; do
    [ -f "$cand/scripts/mmw.sh" ] || continue
    MMW_ROOT="$cand"
    break
  done
fi
MMW="$MMW_ROOT/scripts/mmw.sh"
[ -f "$MMW" ] && echo "MMW=$MMW" || echo "MMW 定位失败：先从 Cursor Marketplace / Team Marketplace 安装 multi-model-workflow-cursor，或设 CURSOR_PLUGIN_ROOT"
```

`mmw X` 等价于 `bash "$MMW" X`。每个新 shell 都使用回显的绝对路径，不依赖 shell 变量跨调用留存，也不要从 `.pi` / `.claude` / `.factory` 宿主镜像目录取运行时代码。
<!-- END: locate-mmw -->

1. 读插件根下 `skills/orchestrate/references/control/steering-commands.md`(计划外分流协议在里面)。
2. 确认当前计划外项的标签(bug/optimize/out-of-scope/needs-evaluation)与一句话摘要。
3. 落盘:
   - `issue` → `mmw side-finding record --tag <t> --disposition issue --finding "<摘要>"`
   - `fix` → `mmw side-finding record --tag <t> --disposition fix --finding "<摘要>"`
4. `fix` 第一刀**不扩大**现有合法修复边界;用户要扩大则单独立项。
5. 板已自动刷新;回报处置结果。
