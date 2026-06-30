---
name: orchestrate
description: "开发工作流主入口。用户给出想法/功能/改造、报 bug、要优化、或要合并多个并行 worktree 时主动使用。入口只做两件事:断点恢复 + 选路由(LLM 当场判),随后把你交给那条路自己的 reference。"
---

# Orchestrate · 入口

主线程入口。**只做两件事:断点恢复、路由。** 判出这是哪条路,就把你交给那条路自己的 reference——那一份从头到尾讲清这条路怎么走(建 worktree、阶段契约、回执跳转、收尾全在里面),本文不重复、你也不用回来。

`${SKILL_DIR}` = 本 skill 目录;`${SCRIPTS}` = `${CLAUDE_PLUGIN_ROOT}/scripts`;`mmw` ≡ `bash "${SCRIPTS}/mmw.sh"`(`mmw help` 看全表)。

## Step 0 · 先跑 `mmw where`(它自带指路)

无脑先跑一次(无论在哪):

```bash
mmw where
```

- **在管任务**(在 worktree 里)→ `where` 报 `scenario` + `phase` + `load`/`do`/`then`。一句话告诉用户"你在 `<phase>`",然后**读 `references/scenario/<scenario>.md`**,按它的契约从当前 phase 续(断点恢复靠 `where` + 接力单,不靠会话记忆)。**跳过 Step 1。**
- **`UNMANAGED` + 起始选项菜单**(在主仓库)→ 不是在管任务。菜单列全了所有开口 → 进 Step 1。

## Step 1 · 路由 → 进该路径的 reference

看对话判这是哪条路,选一个,**直接读那份 reference,本文到此为止**:

| 你怎么开口 | 路径 | 读这份(从头到尾就靠它) |
| --- | --- | --- |
| 明确的小改 | `small-change` | `${SKILL_DIR}/references/scenario/small-change.md` |
| 新想法 / 功能 或 要优化改造(要设计) | `develop` | `${SKILL_DIR}/references/scenario/develop.md` |
| bug / 报错 / regression,根因不明 | `bug` | `${SKILL_DIR}/references/scenario/bug.md` |
| 多个并行 worktree 要合并 | `merge` | `${SKILL_DIR}/references/scenario/merge.md` |

判不准就问一句收窄(一次只问一个)。概念 / 事实问题直接答,不进 orchestrate。

## 边界

- 入口只路由:**不讲流程、不建 worktree、不写设计 / 计划 / 代码、不派 worker、不做 review**——那些都在各路径 reference 和各阶段方法论里。
- 路由是 LLM 语义判断,不要脚本化、不读关键词表。
