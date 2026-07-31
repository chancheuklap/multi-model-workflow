---
name: mmw-reviewer
description: 你被派去独立审一份产物时读这份。
user-invocable: false
---

开工读共享审查纪律，再读你这一路视角的审查角度。只读验证，每条发现引用具体位置。发现清单回什么、几样齐，你的角色说明里写了。

---

## 线下 · 不是技能内容

**谁读这份**：`roles/reviewer-claude.md` 与 `roles/reviewer-gpt.md` 两路共用。选派哪一路是 `mmw-review` 的判断，派的做法见 `mmw-dispatch`。

### 施工单

- **来源**：`plugin/skills/worktree-review/SKILL.md`、`references/method.md`、`design.md`、`plan.md`、`final.md`、`merge.md`
- **保留**：共享审查纪律（只读边界、看别的版本用 git 只读命令、代码差异用不可信标记包裹、一次审透、知道却没报就是审查失败）；四份审查角度；返回合同要求每条发现带位置、严重度、置信度，不夹带修复动作
- **删除**：视角名与引擎起审子命令的耦合；跨计划合同门单列（角度并进终审）

<!-- 方法论正文待填。填之前先读「来源」里的旧文件全文，按保留与删除两列取舍。 -->
