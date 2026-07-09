# Host Contract · 双宿主合同(Claude Code / Droid)

> 主线程与阶段 reference 共用。判断当前宿主后只走对应列,不混用工具名。

## 0. 识别宿主

脚本侧自动检测(`plugin/scripts/lib/host.sh`):

| 条件 | 宿主 |
| --- | --- |
| `MMW_HOST=droid\|claude` | 显式 |
| `DROID_PLUGIN_ROOT` 已设 | droid |
| 否则 | claude |

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
| 插件根 env | `CLAUDE_PLUGIN_ROOT` | `DROID_PLUGIN_ROOT`(脚本亦提供 `CLAUDE_PLUGIN_ROOT` 别名) |

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

审者都读已装 `worktree-review` skill(方法单源);plugin 内不塞审查方法论正文。

## 5. 角色 × 模型(Droid Custom Droids)

| droid | 职责 | 建议 model | 工具 |
| --- | --- | --- | --- |
| `plan-writer` | 写单份 plan | 强推理(Opus 级 / inherit high) | 读写 + 检索 |
| `pack-executor` | 按 plan 落地 | 强写码(GPT-Codex / 等价) | 读写 + Execute |
| `reviewer-design` | 设计审 | 强推理 | read-only |
| `reviewer-plan` | 计划审 | 强推理 | read-only |
| `reviewer-final-a` | final 基线1 | 与写码不同模型 | read-only |
| `reviewer-final-b` | final 基线2 | 与 A 不同模型 | read-only |
| `review-coordinator` | 审 loop 协调 | inherit | 读写 + Execute |
| `investigate-topic` | 单 topic 取证 | 中高 | read-only + web |
| `code-explorer` | 只读探代码 | 快/中 | read-only |

装 plugin 后 droid 落在 `plugin/droids/`;Droid 会话可按 `subagent_type` 引用。

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
