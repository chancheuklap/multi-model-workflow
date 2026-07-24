---
name: orchestrate
description: "需要正式编排的开发工作流主入口。用于新功能、系统改造、根因不明的 bug、需要独立任务边界的小改，或合并多个并行 worktree；不用于问答、解释、只读查看，以及主线程可直接完成并验证的琐碎单步动作。"
---

# Orchestrate · 入口

主线程入口。**只做两件事:断点恢复、路由。** 判出这是哪条路,就把你交给那条路自己的 reference——那一份从头到尾讲清这条路怎么走(建 worktree、阶段契约、回执跳转、收尾全在里面),本文不重复、你也不用回来。

`${SKILL_DIR}` = 本 skill 目录(= 插件根 `/skills/orchestrate`);`${SCRIPTS}` = 插件根 `/scripts`;`mmw` ≡ `bash "${SCRIPTS}/mmw.sh"`(`mmw help` 看全表)。这三个绝对路径由下面 Step 0 一次定位得出,**不依赖任何环境变量**。

先判是否需要正式编排。问答、解释、只读查看，以及主线程可直接完成并验证的琐碎单步动作，直接处理，不跑 `mmw`、不建 worktree。直接处理代码任务时，实施前先读 `${SKILL_DIR}/../worktree-build/references/tests.md` 的完整测试质量权威和目标仓库项目指令链；普通说明文档修改不要求测试。只有需要正式编排的开发任务才继续 Step 0。

## Step 0 · 先定位插件,再跑 `mmw where`(它自带指路)

先一次性定位当前宿主的插件(无需环境变量),**记住回显的三个绝对路径**,后文所有 `mmw` / `${SCRIPTS}` / `${SKILL_DIR}` 都用它们替换:

<!-- BEGIN: locate-mmw -->
会话开头 SessionStart hook 已报过 mmw 绝对路径的,直接用它(hook 从激活插件根跑,是权威)。没有才跑下面定位块——**读实际激活的安装位**(installed_plugins.json),不扫缓存挑版本号(缓存里躺着历史版本,版本号最高 ≠ 正在运行的那个):

```sh
P=~/.claude/plugins
MMW="$( jq -r '.plugins | to_entries[] | select(.key | startswith("multi-model-workflow@")) | .value[0].installPath // empty' \
        "$P/installed_plugins.json" 2>/dev/null | head -1 | sed 's|$|/scripts/mmw.sh|' )"
[ -f "$MMW" ] || MMW="$( jq -r '.["multi-model-workflow"].installLocation // empty' "$P/known_marketplaces.json" 2>/dev/null | sed 's|$|/plugin/scripts/mmw.sh|' )"
[ -f "$MMW" ] && echo "MMW=$MMW" || echo "MMW 定位失败:插件未装?(装了才有 installed_plugins.json 条目)"
```

`mmw X` ≡ `bash "$MMW" X`;每个新 shell 用回显的绝对路径,别指望 shell 变量跨调用留存。**别用仓库里的相对路径 `plugin/scripts/mmw.sh` 当运行时**——在旧分支 worktree 里那是旧代码。
<!-- END: locate-mmw -->

```bash
printf 'SCRIPTS   = %s\nSKILL_DIR = %s\n' "$(dirname "$MMW")" "${MMW%/scripts/mmw.sh}/skills/orchestrate"
```

然后无脑先跑一次(无论在哪):

```bash
bash "$MMW" where
```

- **在管任务**(在 worktree 里)→ `where` 报 `scenario` + `phase` + `load`/`do`/`then`。一句话告诉用户"你在 `<phase>`",然后**读 `references/scenario/<scenario>.md`**,按它的契约从当前 phase 续(断点恢复靠 `where` + 接力单,不靠会话记忆)。**跳过 Step 1。**
- **`UNMANAGED` + 起始选项菜单**(在主仓库)→ 不是在管任务。菜单列全了所有开口 → 进 Step 1。

## Step 1 · 路由 → 进该路径的 reference

看对话判这是哪条路,选一个,**直接读那份 reference,本文到此为止**:

| 你怎么开口 | 路径 | 读这份(从头到尾就靠它) |
| --- | --- | --- |
| 范围明确,但仍需独立任务边界与验收的代码改动 | `small-change` | `${SKILL_DIR}/references/scenario/small-change.md` |
| 新想法 / 功能 或 要优化改造(要设计) | `develop` | `${SKILL_DIR}/references/scenario/develop.md` |
| bug / 报错 / regression,根因不明 | `bug` | `${SKILL_DIR}/references/scenario/bug.md` |
| 多个并行 worktree 要合并 | `merge` | `${SKILL_DIR}/references/scenario/merge.md` |

判不准就问一句收窄(一次只问一个)。

## 控制面(任何阶段可用,跨路径)

用户可随时用 slash command 指挥在管 run;这些是控制面,不改施工面流程:

| 命令 | 作用 | 你要做 |
| --- | --- | --- |
| `/progress` | 看进度板 | 照该命令文件执行(动作在命令文件里,不在本表) |
| `/approve-design` | 确认设计(唯一人闸,只有用户能敲) | 照该命令文件执行;用户口头同意不算过门,请他敲命令 |
| `/unattended` `/attended` | 进/出强无人值守 | 读 `${SKILL_DIR}/references/control/attendance.md`(值守档合同 + no-question 双层),照它执行 |
| `/side-finding` `/reassess` `/skip-current` `/rescope` `/replan-remaining` `/force-validate` | 计划外分流 + 中途指挥(含用户口头「回上一步」的翻译) | 读 `${SKILL_DIR}/references/control/steering-commands.md` |

**值守档是横切合同**:任何阶段续跑前先看 `task.json.attendance`(develop 讨论态生来 `attended`,`/approve-design` 过门自动切 `afk`);`unattended` 时按 `control/attendance.md` 自我约束,不向用户提问,但用户回来发任意消息即恢复 `attended`。软停/计划外分流的问不问,按该合同判。

## 边界

- 入口只路由:**不讲流程、不建 worktree、不写设计 / 计划 / 代码、不派 worker、不做 review**——那些都在各路径 reference 和各阶段方法论里。
- 路由是 LLM 语义判断,不要脚本化、不读关键词表。
