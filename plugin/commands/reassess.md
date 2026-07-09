---
description: 停下来用磁盘状态重新判断真实情况,给可执行结论
argument-hint: ""
---

## 指令

用户要你**基于磁盘真相**重新判断,不靠会话记忆。

先定位 mmw(无需环境变量;记住返回的绝对路径,下文 `mmw X` 即 `bash <该路径> X`):

```sh
if [ -n "${DROID_PLUGIN_ROOT:-}" ] || printf %s "$PATH" | grep -q '/.factory/bin'; then P=~/.factory/plugins; else P=~/.claude/plugins; fi
find "$P" -type f -path '*multi-model-workflow*/scripts/mmw.sh' 2>/dev/null | head -1
```

1. 跑 `mmw where`。若是 `UNMANAGED` / 无在管任务:说明当前不在在管 run,停止。
2. 结合 `mmw where` + `git status`(自己跑一次),给业务级结论:现在到哪、卡在哪、真实下一步是什么。
3. 给一个推荐动作(接着跑 / 换阶段 / 补哪道门);模糊处只给一个最该先做的,不铺开多方向。
4. 不自动续跑,等用户确认方向。
