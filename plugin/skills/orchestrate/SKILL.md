---
name: orchestrate
description: "开发工作流主入口。用户给出想法/功能/改造、报 bug、要优化、或要合并多个并行 worktree 时主动使用。入口只做两件事:断点恢复 + 选路由(LLM 当场判),随后把你交给那条路自己的 reference。"
---

# Orchestrate · 入口

主线程入口。**只做两件事:断点恢复、路由。** 判出这是哪条路,就把你交给那条路自己的 reference——那一份从头到尾讲清这条路怎么走(建 worktree、阶段契约、回执跳转、收尾全在里面),本文不重复、你也不用回来。

`${SKILL_DIR}` = 本 skill 目录(= 插件根 `/skills/orchestrate`);`${SCRIPTS}` = 插件根 `/scripts`;`mmw` ≡ `bash "${SCRIPTS}/mmw.sh"`(`mmw help` 看全表)。这三个绝对路径由下面 Step 0 一次定位得出,**不依赖任何环境变量**,Claude / Droid 通用。

**双宿主**:开跑前读 `${SKILL_DIR}/references/control/host-contract.md`(路径/工具/派发后端)。`export MMW_HOST=droid|claude` 可显式锁定宿主。

## Step 0 · 先定位插件,再跑 `mmw where`(它自带指路)

先一次性定位当前宿主的插件(无需环境变量),**记住回显的三个绝对路径**,后文所有 `mmw` / `${SCRIPTS}` / `${SKILL_DIR}` 都用它们替换:

```bash
if [ -n "${DROID_PLUGIN_ROOT:-}" ] || printf %s "$PATH" | grep -q '/.factory/bin'; then P=~/.factory/plugins; else P=~/.claude/plugins; fi
MMW="$(find "$P" -type f -path '*multi-model-workflow*/scripts/mmw.sh' 2>/dev/null | head -1)"
printf 'mmw       = %s\nSCRIPTS   = %s\nSKILL_DIR = %s\n' \
  "$MMW" "$(dirname "$MMW")" "$(dirname "$(dirname "$MMW")")/skills/orchestrate"
```

`mmw X` ≡ `bash "$MMW" X`(每个新 shell 用回显的绝对路径,别指望 shell 变量跨调用留存)。然后无脑先跑一次(无论在哪):

```bash
bash "$MMW" where
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

## 控制面(任何阶段可用,跨路径)

用户可随时用 slash command 指挥在管 run;这些是控制面,不改施工面流程:

| 命令 | 作用 | 你要做 |
| --- | --- | --- |
| `/progress` | 看进度板 | 照命令跑 `mmw progress render --stdout`,原样转述板面 |
| `/unattended` `/attended` | 进/出强无人值守 | 读 `${SKILL_DIR}/references/control/attendance.md`(值守档合同 + no-question 双层),照它执行 |
| `/side-finding` | 计划外二选一登记 | 读 `${SKILL_DIR}/references/control/steering-commands.md` |
| `/reassess` `/skip-current` `/rescope` `/replan-remaining` `/force-validate` | 中途指挥 | 读 `${SKILL_DIR}/references/control/steering-commands.md` |

**值守档是横切合同**:任何阶段续跑前先看 `task.json.attendance`;`unattended` 时按 `control/attendance.md` 自我约束,不向用户提问。软停/计划外分流的问不问,按该合同判。

## 边界

- 入口只路由:**不讲流程、不建 worktree、不写设计 / 计划 / 代码、不派 worker、不做 review**——那些都在各路径 reference 和各阶段方法论里。
- 路由是 LLM 语义判断,不要脚本化、不读关键词表。
