---
name: skip-current
description: 当前步骤先放下,继续后面(记 blocked/skipped 留痕)
argument-hint: ""
disable-model-invocation: true
---

用户要放下当前卡住的步骤先继续后面。

## 指令

先定位 mmw:

<!-- BEGIN: locate-mmw -->
会话开头的 mmw 分诊已经报告引擎根绝对路径时，直接使用它。没有时按安装位查找：

```sh
MMW_ROOT=""
if [ -n "${MMW_ENGINE_ROOT:-}" ] && [ -f "$MMW_ENGINE_ROOT/scripts/mmw.sh" ]; then
  MMW_ROOT="$MMW_ENGINE_ROOT"
fi
if [ -z "$MMW_ROOT" ]; then
  for cand in \
    "$HOME/.cursor/multi-model-workflow-engine" \
    "$(pwd | sed -n 's|\(.*multi-model-workflow\)/.*|\1/cursor-plugin|p')" \
    "$(pwd)/cursor-plugin"
  do
    [ -f "$cand/scripts/mmw.sh" ] || continue
    MMW_ROOT="$cand"
    break
  done
fi
MMW="$MMW_ROOT/scripts/mmw.sh"
[ -f "$MMW" ] && echo "MMW=$MMW" || echo "MMW 定位失败：先跑 bash cursor-plugin/scripts/install-local-surface.sh，或设 MMW_ENGINE_ROOT"
```

`mmw X` 等价于 `bash "$MMW" X`。每个新 shell 都使用回显的绝对路径，不依赖 shell 变量跨调用留存，也不要从 `.pi` / `.claude` / `.factory` 宿主镜像目录取运行时代码。
<!-- END: locate-mmw -->

1. 先跑 `mmw where` 看现状。
2. 记下放下的是什么、为什么(一句话),落 `mmw side-finding record` 或 `mmw loop softstop` 留痕,别静默跳过。
3. 继续后面的活,说明放下了哪一步、后面从哪续(登记在 open_items,不静默丢)。
4. 刷新板:`mmw progress render`。
