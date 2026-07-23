---
name: attended
description: 把当前 MMW 任务切回有人值守，恢复需要时向用户提问。
---

# 切回有人值守

从本 skill 的绝对路径定位 plugin：

```bash
MMW_SKILL="<本轮 skill source locator 给出的 attended/SKILL.md 绝对路径>"
MMW_ROOT="$(cd "$(dirname "$MMW_SKILL")/../.." && pwd)"
MMW="$MMW_ROOT/scripts/mmw.sh"
```

运行：

```bash
bash "$MMW" unattended exit
bash "$MMW" where
```

输出 `ATTENDANCE=attended` 后告诉用户已经恢复有人值守，并照 `where` 续跑。没有在管任务时如实说明。
