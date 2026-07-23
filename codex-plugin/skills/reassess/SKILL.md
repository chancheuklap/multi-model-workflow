---
name: reassess
description: 丢开会话记忆，依据 MMW 磁盘状态和 Git 现场重新判断当前位置与下一步。
---

# 重新判断

从本 skill 的绝对路径定位 plugin：

```bash
MMW_SKILL="<本轮 skill source locator 给出的 reassess/SKILL.md 绝对路径>"
MMW_ROOT="$(cd "$(dirname "$MMW_SKILL")/../.." && pwd)"
MMW="$MMW_ROOT/scripts/mmw.sh"
```

运行 `bash "$MMW" where` 和 `git status --short`。如果当前不是在管任务就停止；否则用业务语言说明现在到哪、卡在哪里、真实下一步是什么，并只给一个推荐动作。这个入口只重估，不自动续跑。
