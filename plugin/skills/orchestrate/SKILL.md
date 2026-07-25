---
name: orchestrate
description: "MMW 正式编排入口。默认直接处理开发请求；仅在需要跨会话持久状态、设计审批、多任务协调、审闸保证、多结果合并，或用户明确要求 MMW 时使用。"
---

# Orchestrate · 入口

主线程入口。**只做三件事：有限只读定向、断点恢复、路由。** 判出正式编排场景后，就把任务交给对应 reference；建 worktree、阶段契约、回执跳转和收尾都由那份 reference 负责。

`${SKILL_DIR}` = 本 skill 目录(= 插件根 `/skills/orchestrate`);`${SCRIPTS}` = 插件根 `/scripts`;`mmw` ≡ `bash "${SCRIPTS}/mmw.sh"`(`mmw help` 看全表)。这三个绝对路径由下面 Step 0 一次定位得出,**不依赖任何环境变量**。

先在任何 `mmw` 命令、写操作和任务 worktree 之前做入口判断。入口只有三种结果：

- **续跑 `resume(task)`**：SessionStart 已报告当前在管任务且本轮请求属于它，或用户明确要求继续某个既有 MMW 任务。
- **直接处理 `direct`（默认）**：当前主线程能完整落地并验证。直接处理仍可读代码、TDD、跑测试、用 reviewer/advisor，必要时也可用普通 worktree；这些工程动作本身不需要 MMW。直接处理代码任务时，实施前先读 `${SKILL_DIR}/../worktree-build/references/tests.md` 的完整测试质量权威和目标仓库项目指令链；普通说明文档修改不要求测试。
- **正式编排 `orchestrate(scenario, capabilities, evidence)`**：用户明确要求 MMW，或只读定向已经证实任务需要至少一种 MMW 治理能力。

只读定向最多做三件事：定位代码 owner / seam、确认期望行为、做一次聚焦复现。定向期间不写文件、不建分支、不建状态、不建 worktree。以下治理能力才允许正式编排：跨会话持久状态（`durable-state`）、设计审批（`design-approval`）、多任务协调（`coordinated-delivery`）、审闸保证（`gated-assurance`）、多结果合并（`multi-result-integration`）；用户明确要求则记 `explicit-request`。新功能、根因不明、多文件、多步骤、读改测、需要测试或普通 worktree 都不是触发器。

无法给出具体治理能力和对应用户原话/只读证据时，选 `direct`。只有选了 `resume` 或 `orchestrate` 才继续 Step 0；新建任务时，场景 reference 必须把能力和证据传给 `mmw task new`。选择 MMW 后同时读 `${SKILL_DIR}/references/retrieval-doctrine.md`，并贯穿 investigate、plan、build 和 review。

## Step 0 · 已选 MMW 后定位插件，再跑 `mmw where`

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

现在才运行一次；不要为了“看看在哪”而在普通请求上运行：

```bash
bash "$MMW" where
```

- **在管任务**(在 worktree 里)→ `where` 报 `scenario` + `phase` + `load`/`do`/`then`。一句话告诉用户"你在 `<phase>`",然后**读 `references/scenario/<scenario>.md`**,按它的契约从当前 phase 续(断点恢复靠 `where` + 接力单,不靠会话记忆)。**跳过 Step 1。**
- **`UNMANAGED` + 起始选项菜单**(在主仓库)→ 已决定正式编排，但当前还没有任务 → 进 Step 1。

## Step 1 · 路由 → 进该路径的 reference

看对话判这是哪条路,选一个,**直接读那份 reference,本文到此为止**:

| 你怎么开口 | 路径 | 读这份(从头到尾就靠它) |
| --- | --- | --- |
| 行为、根因和改法已明确，无需设计，但需要持久状态/独立终审或用户明确要求 | `small-change` | `${SKILL_DIR}/references/scenario/small-change.md` |
| 只读定向确认需要用户设计审批，或多个独立交付切片需要协调 | `develop` | `${SKILL_DIR}/references/scenario/develop.md` |
| 只读定向后仍需跨会话调查，或修复风险要求审闸保证 | `bug` | `${SKILL_DIR}/references/scenario/bug.md` |
| 多个既有 worktree / PR 需要按业务意图合并 | `merge` | `${SKILL_DIR}/references/scenario/merge.md` |

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

- 入口只做有限只读定向、恢复和路由；未选正式编排时不建 MMW 状态或任务 worktree，不写设计 / 计划 / 代码，不派 worker，不做 review。
- 路由是基于治理能力和证据的 LLM 语义判断，不要退化成关键词或任务大小分类器。
