# Host Contract · 双宿主合同(Claude Code / Droid)

> 主线程与阶段 reference 共用。判断当前宿主后只走对应列,不混用工具名。

## 0. 识别宿主

脚本侧自动检测(`plugin/scripts/lib/host.sh`):

| 优先级 | 条件 | 宿主 |
| --- | --- | --- |
| 1 | `MMW_HOST=droid\|claude` | 显式 |
| 2 | `DROID_PLUGIN_ROOT` 已设(仅 Droid hook 运行时有) | droid |
| 3 | 脚本自身路径含 `.factory/plugins/` → droid;`.claude/plugins/` → claude | 路径自检 |
| 4 | 否则 | claude |

路径自检让主线程 Execute 里直接跑 mmw(无 `DROID_PLUGIN_ROOT`)也判得对宿主。

主线程开跑可先:

```bash
export MMW_HOST=droid # 或 claude;一般不必,自动检测
mmw where
```

## 1. 路径

| 项 | Claude | Droid |
| --- | --- | --- |
| 状态平面 | `.claude/multi-model-workflow/` | `.factory/multi-model-workflow/` |
| worktree 根 | `.claude/worktrees/<slug>` | `.factory/worktrees/<slug>` |
| 插件根 env | `CLAUDE_PLUGIN_ROOT`(命令 `!` 注入 / hook 里可用) | `DROID_PLUGIN_ROOT`(仅 hook 运行时;主线程 Execute 里没有) |

`task.json` / `loop-state.json` / progress 投影 / review-brief 都在状态平面内。

## 2. 工具名

| 语义 | Claude | Droid |
| --- | --- | --- |
| 壳命令 | `Bash` | `Execute` |
| 写文件 | `Write` | `Create` / `Edit` |
| 问用户(结构化) | `AskUserQuestion` | `AskUser` |
| 子代理 | Agent / Task(`subagent_type`) | `Task`(`subagent_type` = droid name) |
| 进 worktree | `EnterWorktree({ path })` | 在该路径开会话或 `cd` 到路径后 `mmw where` |
| 长时间后台 | `Bash` + `run_in_background` + `TaskOutput` | `Task` 派 droid(流式进度) |
| 技能调用 | `Skill({ skill })` | 读 skill / `/skill-name` / 自动匹配 |
| Investigate fan-out | `Workflow({ scriptPath })` | `Task` 派 `investigate-topic`(可并行) |

## 3. 写码工人

| 宿主 | 派发 | 后端 |
| --- | --- | --- |
| Claude | `mmw worker dispatch ...`(兼容 `mmw codex dispatch`) | 外挂 `codex exec`(workspace-write 围在 worktree) |
| Droid | `mmw worker dispatch ...` | 机器准备 worktree + prompt 包;主线程 `Task` → `pack-executor` droid |

两宿主共同红线:

- Worker 禁改 `docs/`
- 主线程按 plan 验收(跑测试 / 读 diff),不信工人自述
- 每 Pack 提交带 `Pack N.M`

## 4. 审闸

| 宿主 | 派发 |
| --- | --- |
| Claude | brief 内 `codex exec` / `claude -p` 无头 CLI(后台) |
| Droid | brief 内 `Task` → `reviewer-*` droid,按 stage/视角/模型矩阵并行 |

审者读 `worktree-review` skill(审查方法论单源):**Claude 侧** Codex / Claude 无头 CLI 读它自己 hub 装的(`~/.agents/skills/worktree-review/`);**Droid 侧**读随插件发布的 `plugin/skills/worktree-review/`(派发消息传绝对路径,不赌子代理自动加载)。同一套方法,两宿主各取自己够得到的副本。

## 5. 角色 × 模型(Droid Custom Droids)

主线程编排会话默认用 `grok-4.5` high(用户偏好;会话级选择,不是 droid 文件)。

| droid | 职责 | model | 工具 |
| --- | --- | --- | --- |
| `plan-writer` | 写单份 plan | `claude-opus-4-8` high | 读写 + 检索 |
| `pack-executor` | 按 plan 落地 | `glm-5.2` max | 读写 + Execute |
| `reviewer-design-a` | 设计审轴A | `claude-opus-4-8` high | read-only |
| `reviewer-design-b` | 设计审轴B | `claude-opus-4-8` high | read-only |
| `reviewer-plan-a` | 计划审轴A | `gpt-5.5` high | read-only |
| `reviewer-plan-b` | 计划审轴B | `gpt-5.5` high | read-only |
| `reviewer-final-a` | final / merge 跨模型路A | `gpt-5.5` high(≠写码) | read-only |
| `reviewer-final-b` | final / merge 跨模型路B | `claude-opus-4-8` high(≠A) | read-only |
| `review-coordinator` | 审 loop 协调(可选隔离) | inherit / 同主线程 | 读写 + Execute + Task |
| `investigate-topic` | 单 topic 取证 | `grok-4.5` high | read-only + web |
| `code-explorer` | 只读探代码 | `claude-sonnet-5` high | read-only |
| `fable-advisor` | 稀疏关键顾问(非审闸) | `claude-fable-5` high | read-only |

①②设计/计划审两轴**同模型**(design 两轴 opus、plan 两轴 gpt-5.5),只分两路视角不分模型(与 Claude 宿主一致:①② 都由单一 Codex 审、两审者分走视角);跨模型只在 ④final / merge(a≠b)。写者≠验者靠"审者模型 ≠ 该阶段作者模型"保证。

装 plugin 后 droid 落在 `plugin/droids/`;Droid 会话可按 `subagent_type` 引用。Claude 宿主对应表面在 `plugin/agents/`(如 plan-writer),模型/工具名按 Claude 习惯,与 droids 表不必逐字同一 ID。

`fable-advisor` 不进 review 矩阵、不写产物;主线程仅在 phase-contract 允许的时机 `Task` 派出(propose 可选 / design 主战场 / build afk)。

Droid final 分档与 Claude 同判据(`review.sh` tier):small-change/bug → 1 路;develop 无 capable 且 diff 小 → 2 路;否则 / 判不出 → 4 路。merge-impl → final-a + final-b 双路。


## 6. Hooks

| 事件 | Claude matcher | Droid matcher | 脚本 |
| --- | --- | --- | --- |
| SessionStart | (无 matcher) | 同 | `session-triage.sh` |
| PreToolUse | `Bash` | `Execute`(hooks 用 `Bash\|Execute`) | `guard-redline.sh` |
| PostToolUse | `Bash` | `Execute` | `record-step.sh` |
| SubagentStop | (无 matcher) | 同 | `guard-loop.sh` |

Droid 若 hook 事件名/payload 字段有差异,以 `lib/host.sh` + hooks 内容错为准;逻辑(记 step / 看守 / 分诊)不变。

## 7. 安装

| 宿主 | 安装 |
| --- | --- |
| Claude | marketplace / 本地 plugin 路径,见 README |
| Droid | `droid plugin install multi-model-workflow@mmw-droid`(本仓库 `.factory-plugin/marketplace.json`)或项目 `.factory/` 链接 |

两宿主可共装同一 plugin 目录;状态平面按宿主隔离,互不踩盘。

**skill 依赖**:`worktree-build` / `worktree-review` 是 worker/reviewer 的方法论单源。Droid 侧随插件发布(`plugin/skills/`),装 plugin 即到位。Claude 侧的写码/审查是**外部** Codex / Claude 无头 CLI,读不到 plugin 内部,须另把这两个 skill 装进 Codex hub(`~/.agents/skills/`,源在本仓库 `codex-skills/`);没装则 Claude 侧派发 fail-closed(报找不到 skill)。
