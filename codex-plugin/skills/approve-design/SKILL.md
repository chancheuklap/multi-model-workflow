---
name: approve-design
description: 用户明确确认当前设计时使用；盖承重文档指纹并放行后续无人值守流水线。
---

# 确认设计

本入口只响应用户显式调用。用户口头说“可以”不等于触发本入口，不能代跑。

从本 skill 的绝对路径定位 plugin：

```bash
MMW_SKILL="<本轮 skill source locator 给出的 approve-design/SKILL.md 绝对路径>"
MMW_ROOT="$(cd "$(dirname "$MMW_SKILL")/../.." && pwd)"
MMW="$MMW_ROOT/scripts/mmw.sh"
```

用户随调用给了一个或多个承重文档路径时，每个路径追加一个 `--report`；没有给路径时让引擎使用 design 已钉产出：

```bash
bash "$MMW" approve [--report <路径>]...
```

`APPROVED` 或 `RE-APPROVED` 后立即运行 `bash "$MMW" where` 并继续。承重文档缺失、prototype 未 accepted 或确认已过期时，按错误原文修正，不绕门。
