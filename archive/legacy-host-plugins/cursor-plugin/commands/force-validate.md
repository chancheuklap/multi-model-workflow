---
name: force-validate
description: 立刻跑当前层的合法审查
argument-hint: ""
---

用户要立刻对当前阶段产物跑审查。

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

1. 先跑 `mmw where` 看当前阶段与可用的 `review_start`(在审闸内 where 会吐出带 `--stage` 和 `--source` 的完整命令)。
2. 触发当前层合法 review:照抄 where 吐的 `review_start` 整条跑(`--source` 必填,不可省)。不在审闸内则无合法审可起,如实告知用户。
3. 只跑当前层该跑的审,不越层;审完照 review 回执处理 findings。
