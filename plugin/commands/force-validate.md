---
description: 立刻跑当前层的合法审查
argument-hint: ""
---

用户要立刻对当前阶段产物跑审查。

## 指令

先定位 mmw(无需环境变量;记住返回的绝对路径,下文 `mmw X` 即 `bash <该路径> X`):

```sh
if [ -n "${DROID_PLUGIN_ROOT:-}" ] || printf %s "$PATH" | grep -q '/.factory/bin'; then P=~/.factory/plugins; else P=~/.claude/plugins; fi
find "$P" -type f -path '*multi-model-workflow*/scripts/mmw.sh' 2>/dev/null | head -1
```

1. 先跑 `mmw where` 看当前阶段与可用的 `review_start`。
2. 触发当前层合法 review:`mmw review start --stage <当前层>`(design/plan/final 等,按 where 报的 stage)。
3. 只跑当前层该跑的审,不越层;审完照 review 回执处理 findings。
