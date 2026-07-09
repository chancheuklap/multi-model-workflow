> **Slug**：`2026-07-09-control-plane-steering-unattended`  
> **状态**：设计草案（待用户确认 → 待审查 → 再 plan-writing）  
> **适用对象**：以 Claude Code plugin 正本 `plugin/` 为落地权威；`codex-orchestrate-new/` 若后续对齐，只做宿主适配镜像，不得反客为主  
> **状态平面权威路径**：`.claude/multi-model-workflow/`（Claude Code）；禁止把 `.codex/multi-model-workflow/` 写成 Claude 正本路径  
> **性质**：控制面增强，不改施工面内核（阶段推进 / Document-as-Context / 审闸 / worker 边界）  
> **交互正本**：Claude Code slash Commands / Skills / Hooks / AskUserQuestion / `mmw` CLI

---

## 1. 背景和问题

### 1.1 用户视角

负责人在长跑编排中需要四件事：

1. **中途像项目经理一样指挥**：用固定命令改方向、跳过、重估，不必懂 phase 名与状态机术语。
2. **一眼看见进度**：跨会话、跨 compaction 后，不必翻长对话也能接手。
3. **计划外问题怎么处理要简单**：落地或验收时发现计划外 bug / 需改内容，由人选择「开 issue 记下来」或「当场修」。
4. **对设计和计划有信心后可以走开**：进入无人值守后，任何 agent 都不得再向人提问，按 workflow 跑到完成或硬停。

### 1.2 现状（源码已核）

| 能力 | 现成接缝 | 缺口 |
| --- | --- | --- |
| 用户触发入口 | `plugin/commands/gather-context.md` 已证明 slash command 是插件正式入口 | 控制面口令尚未做成 command 族 |
| 技能/命令模型 | Claude Code：commands 与 skills 合并为 `/name`；支持 `$ARGUMENTS`、`` !`cmd` `` 动态注入、`disable-model-invocation`、`disallowed-tools` | 设计稿若只写「认自然语言」会浪费这些能力 |
| 值守模式 | `loop-state.attendance = attended \| afk`；`mmw loop softstop` 在 attended 写 pause、afk 自决留痕 | 缺 `unattended` 强无人合同与进入前置 |
| 预算/打断 | 审闸预算 + loop 轮次 + `guard-loop` 熔断 | 与「完全不问人」需在正本重新定义 |
| 计划外项 | `mmw spinoff` / finding / open_items | 缺固定「开 issue 或当场修」二选一协议 |
| 进度 | `task.json` / `loop-state.json` 可支撑投影 | 无负责人可读进度板 |
| 中途指挥 | 主线程唯一对用户说话；HITL / Decision Brief / BLOCKED 已存在 | 无 command 化口令与动作映射 |
| 会话恢复 | SessionStart → `session-triage.sh` 注入 slug/phase/status | 未注入 mode / 预算 / 板入口 |
| 设计硬门 | 设计未确认不写代码 | 必须保留，无人值守不得绕过 |

### 1.3 问题归纳

1. **控制面口令缺失**：人有项目管理意图，系统只有流程内部术语。
2. **状态对机器可读、对人不可扫**：磁盘真相在，负责人视图缺失。
3. **计划外分流过「自动」**：该由人拍的「记下来还是现在修」被散文默认吃掉。
4. **`afk` 语义过弱**：不能满足「设计计划已过门后，整段执行到收尾不问人」。
5. **交互面偏 LLM 识别**：若只靠自然语言命中口令，稳定性低于 Claude Code 原生 command 入口。

### 1.4 设计原则

1. 磁盘状态是 compaction / 断点续传唯一可信源。
2. Coordinator 编排；worker 施工；hook 守机械门。
3. 设计未确认不写代码（Hard Gate，不可破）。
4. Worker 禁改 `docs/`；checkbox 由 Coordinator 翻。
5. 子代理返回必亲验。
6. 判断类决策不盲目 ossify 成 exit-2；机械账本进 `mmw` 与 `.claude/multi-model-workflow/`。
7. 共享纪律单源，阶段 skill 只引用，不各自发明。
8. **交互入口优先 Claude Code 原语**：slash command / skill / SessionStart hook / AskUserQuestion；自然语言只做次级兼容。
9. 编排流程是公司资产；**本仓库 Claude Code plugin 正本是 `plugin/`**，状态面是 `.claude/multi-model-workflow/`。

---

## 2. 目标结果

完成后系统能稳定做到：

1. 用户用 slash command 中途指挥 run；command 内部调用同一套 `mmw` 动作，不新开平行编排。
2. 每个 active run 有一份可读进度板；SessionStart 给一行摘要，`/progress` 给全板。
3. 有人值守时，计划外项**必须**用 AskUserQuestion 问一次：开 issue 或当场修。
4. 用户在设计与计划过门后可显式 `/unattended`；进入后 Coordinator 与一切 agent **禁止向用户提问**，直到完成或命中硬停。
5. 既有 `attended` / `afk` 兼容；默认值不变。
6. routes / worker loop / review envelope / doc-guard / push-guard 不被削弱。

可观察验收见 §8。

---

## 3. 用户场景

### 3.1 用户故事

1. 作为负责人，我要敲 `/progress`，以便不翻对话就知道做到哪。
2. 作为负责人，我要敲 `/reassess`，以便系统停下来用磁盘状态重新判断真实情况。
3. 作为负责人，我要敲 `/skip-current`，以便卡住的 plan 先放下继续后面。
4. 作为负责人，我要敲 `/rescope` / `/replan-remaining`，以便需求变化时保留已完成、重做后续。
5. 作为负责人，我要在发现计划外 bug 时选「开 issue」，以便不打断主交付。
6. 作为负责人，我要在发现计划外 bug 时选「当场修」，以便当前交付不被该 bug 卡住。
7. 作为负责人，我要在设计与计划都过审后敲 `/unattended`，以便离开座位后流程继续。
8. 作为负责人，我要在无人值守硬停时看到进度板原因，以便回来后只处理一个决策。
9. 作为 Coordinator，我要在 unattended 下禁止提问，以便满足「任何 agent 都不得问人」。
10. 作为 Coordinator，我要在设计未确认时拒绝进入 unattended，以便不破坏 Hard Gate。

### 3.2 失败与边界

| 场景 | 期望行为 |
| --- | --- |
| 无 active run 时敲 command | 说明无可指挥 run，不伪造状态 |
| 设计未过门就 `/unattended` | 拒绝进入，说明缺哪道门 |
| plan 含未回答 HITL pack 且未预授权 | 拒绝 unattended，或要求先预授权 HITL 策略 |
| unattended 中出现设计方向打穿 | 硬停，写 progress board，等用户回来 |
| unattended 中预算到 100% | 硬停，不静默超支 |
| unattended 中需真机/生产环境 | BLOCKED + manual gate，不擅自连接 |
| 计划外项在 unattended | 按进入时预授权策略自动选，不问 |
| worker 试图问用户 | 不允许；worker 合同保持零用户交互 |
| compact 后恢复 | 从磁盘读 mode / policy / board，不靠对话记忆 |
| 用户只说自然语言「进度」 | 次级兼容：映射到与 `/progress` 同一 handler；主推仍是 slash |

---

## 4. 方案设计

### 4.1 Claude Code 原生能力映射（本设计的正本交互面）

| 需求 | Claude Code 能力 | 本设计落点 |
| --- | --- | --- |
| 用户中途指令 | `plugin/commands/*.md` slash command（`gather-context` 先例仅证明 slash 基础入口，见下注） | `/progress` `/reassess` `/skip-current` `/rescope` `/replan-remaining` `/force-validate` `/attended` `/unattended` `/side-finding` |
| 只许人手动触发的副作用命令 | frontmatter `disable-model-invocation: true` | `/unattended` `/skip-current` `/rescope` `/replan-remaining` `/side-finding` |
| 命令参数 | `$ARGUMENTS` / `$0` | 例如 `/side-finding issue`、`/unattended reject-enter` |
| 进度即时接地 | skill/command 内 `` !`mmw where` `` / `` !`mmw progress render --stdout` `` 动态注入 | `/progress` 先注入现状再汇报 |
| 有人值守二选一 | 内置 `AskUserQuestion` | 计划外项 A/B |
| 强无人禁提问 | skill `disallowed-tools: AskUserQuestion`（会话内生效到下一用户消息） | unattended 激活后禁止问人工具 |
| 会话开场分诊 | SessionStart hook `session-triage.sh` | 追加一行 mode/phase/budget + `/progress` 提示 |
| 机械读写 | `mmw` CLI + hooks | mode / policy / board / open_items 写盘 |
| 阶段纪律 | `plugin/skills/orchestrate/references/**` | steering / attendance 共享纪律，阶段只引用 |
| 子代理 | `plugin/agents/*` | 不新增对用户说话角色 |

**结论：用户口令第一入口是 Commands，不是散文关键词表。**  
自然语言只做次级兼容：命中后走同一 handler。

> **落地前须验（能力先例注）**：本仓库现有 `gather-context.md` 只用了 `description` 一个字段，**仅证明 slash 基础入口成立**。本设计押注的 `disable-model-invocation`、`disallowed-tools`、`$ARGUMENTS`、`` !`cmd` `` 动态注入、`${CLAUDE_PLUGIN_ROOT}` 均为 Claude Code 原生能力（已核实存在），但在本仓库尚未被任何 command 实际行使。Slice A 第一个 command 落地时须逐字段跑通一次坐实，不得把「原生支持」直接当「本仓库已验证」。

### 4.2 架构与边界

```text
用户 slash command（主入口）
  或自然语言次级兼容
        │
        v
plugin/commands/*  →  注入 mmw 现状  →  主线程 Coordinator
        │
        +-- Read plugin 内 steering / attendance 共享纪律
        │
        v
mmw CLI + `.claude/multi-model-workflow/` 写盘
  - task.json / loop-state.json（扩展 attendance）
  - unattended_policy
  - open_items / side_findings（可选）
  - progress-board.md（投影）
        │
        v
阶段 skill / scenario 读状态
  - AskUserQuestion（仅 attended）
  - 自动分流 / 继续 / 硬停
        │
        v
帮手 / 审者 / 写码工人
  - 只干活与回传
  - 永不直接问用户
```

| 组件 | 职责 | 不负责 |
| --- | --- | --- |
| `plugin/commands/*` | 用户触发入口、参数、动态注入 | 不各自发明状态机 |
| steering 纪律文档 | command → 机械动作映射 | 不实现新 scenario/route |
| attendance 纪律文档 | 三模式行为合同 | 不改写码循环 |
| progress board | 状态投影，给人看 | 不是第二真相源 |
| `mmw` 脚本族 | mode / policy / board 机械读写 | 不做产品判断 |
| SessionStart | 一行摘要 + 续跑入口 | 不自动续跑压力 |
| AskUserQuestion | attended 下二选一 | unattended 禁用 |
| workers | 继续报 finding / open item | 不向用户提问 |

### 4.3 控制流总图

```text
[Entry / Infrastructure]
        |
        v
 attendance = attended | afk   (默认 afk，兼容现状)
        |
        v
[Discovery / Design / Plan] ---- 设计确认 Hard Gate 仍生效
        |
        |  用户敲 /unattended
        |  且设计+计划已过门
        v
 attendance = unattended
 写入 unattended_policy
 激活 no-question 合同（禁 AskUserQuestion）
        |
        v
[Build / Review / Final / Closing]
  - 不问用户
  - 计划外项按 policy
  - 进度板关键边界刷新
        |
        +--> 完成 → Closing
        |
        +--> 硬停（budget_100 / design_gap / external_env / 无自动路径 BLOCKED）
              写 progress board，等用户回来
```

### 4.4 已有什么（复用 vs 重建）

| 已有 | 处置 |
| --- | --- |
| `plugin/commands/gather-context.md` | **模板**；控制面 command 照此形状扩展 |
| `.claude/multi-model-workflow/` + `task.json` / `loop-state.json` | **真相源**；progress board 只做投影 |
| `mmw where / handoff / loop / review / spinoff` | **复用并扩展**动词 |
| `loop-state.attendance` + `softstop` / `surface` | **对齐扩展**为 attended / afk / unattended |
| `mmw spinoff` / finding / open_items | **复用**为计划外项入口 |
| Decision Brief / HITL | **保留**长问；短二选一改走 AskUserQuestion |
| SessionStart `session-triage.sh` | **增强一行** mode/phase/budget |
| hooks：`guard-redline` / `record-step` / `guard-loop` | **不动**；不把判断类决策塞进 hook |

不重建：阶段运行契约、写码+验收主线、worktree 生命周期、红线 guard。

---

## 5. 功能设计分册

### 5.1 中途指挥：Commands 第一（原建议第 6 点）

#### 5.1.1 落点

| 层 | 路径 | 职责 |
| --- | --- | --- |
| 用户入口 | `plugin/commands/<name>.md` | slash 触发、参数、动态注入、执行步骤 |
| 共享纪律 | `plugin/skills/orchestrate/references/control/steering-commands.md` | command 与自然语言次级兼容共用的动作表 |
| 机械层 | `mmw ...` | 写盘 / 渲染 / 模式切换 |

阶段 skill 只引用纪律文档，不各自抄一份口令表。

#### 5.1.2 Command 表（第一版固定集合）

| Command | 用户意图 | frontmatter 要点 | 机械动作 |
| --- | --- | --- | --- |
| `/progress` | 看进度板 | 可动态注入 `mmw where` / progress render | 渲染并展示 board |
| `/reassess` | 重新判断真实状态 | 注入 where + git 摘要 | 读盘后给业务结论与建议下一步 |
| `/skip-current` | 当前步骤先放下 | `disable-model-invocation: true` | 记 blocked/skipped + 推进 |
| `/rescope` | 砍/加范围 | `disable-model-invocation: true` + `$ARGUMENTS` | 更新范围；必要时回流 design/plan |
| `/replan-remaining` | 保留已完成，重做后续 | `disable-model-invocation: true` | 回流 plan 修订 |
| `/force-validate` | 立刻跑当前层审查 | 可手动 | 触发当前阶段合法 review |
| `/attended` | 切回有人模式 | 可手动 | `mmw loop attendance --mode attended` 或外层写盘 |
| `/unattended` | 进入强无人 | `disable-model-invocation: true` | 走 §5.4 进入门禁 |
| `/side-finding` | 手动指定计划外处置 | `disable-model-invocation: true` + `$ARGUMENTS` | `issue` / `fix` |

命令文案形状对齐 `gather-context.md`：短、可执行、先点明意图再四步内做完。

#### 5.1.3 `/progress` 形状示例（设计级，非实现）

```markdown
---
description: 展示当前 multi-model-workflow 任务进度板
argument-hint: ""
---

## 现状（动态注入）

!`bash "${CLAUDE_PLUGIN_ROOT}/scripts/mmw.sh" where`

## 指令

1. 无在管任务：明确说无可展示 run，停止。
2. 有在管任务：跑 `mmw progress render`，向用户展示 progress board 全文。
3. 只汇报板面内容与一个「若需你拍板」问题（若有）；不自动续跑。
```

#### 5.1.4 次级兼容：自然语言

- 用户原话命中「进度 / 重估 / 跳过当前 / 无人值守 …」时，映射到与对应 command **同一 handler**。
- 模糊指令先归 `/reassess`，再给一个推荐 command，不连问多个。
- 无 active run：说明无对象，不创建幽灵状态。
- **文档与教学默认教 slash**，不把自然语言当主入口宣传。

### 5.2 进度板（原建议第 8 点）

#### 5.2.1 真相与投影

- **真相源**：`.claude/multi-model-workflow/task.json`、`loop-state.json`，以及同目录审闸/旁路账本
- **投影**：`.claude/multi-model-workflow/progress-board.md`
  - 与 `task.json` 同目录（`prepare.sh` 的 `STATE_SUBDIR=".claude/multi-model-workflow"`）
  - 一个 worktree 任务一份板；若需区分多 run 可用 `progress-board-<slug>.md`，仍落该目录
- **禁止**：写到 `.codex/multi-model-workflow/`

放在状态目录而非 `docs/`：

1. 属于运行态，不是设计/计划权威。
2. 随 worktree 清理消失。
3. 主仓库 `.claude/.gitignore` 已遮蔽 `multi-model-workflow/`。

#### 5.2.2 机器命令

```bash
mmw progress render
# 可选：mmw progress render --stdout   # 供 command 动态注入
```

从 `task.json` / `loop-state.json` / open_items / 审闸账本聚合生成/覆盖 board。  
主线程在关键边界调用；用户 `/progress` 时调用。

#### 5.2.3 板面结构（固定）

```markdown
# Progress Board · <slug>

## 现在
- 路线 / 阶段 / 值守模式
- 预算：effective_used / total（含 credit 说明）
- 一句话当前动作

## 计划进度
| Plan | 状态 | Packs | Review | 备注 |

## 阻塞与待决
- ...

## 计划外项
| ID | 标签 | 摘要 | 选择 | 去向 |

## 下一步
- 自动下一步
- 若需你拍板：只保留一个问题
- 指挥入口：/progress /reassess /attended /unattended /side-finding
```

#### 5.2.4 刷新时机

| 时机 | 是否必须 |
| --- | --- |
| phase transition 成功后 | 必须 |
| execution 每个 Plan 边界 | 必须 |
| Direction Check / surface 触发后 | 必须 |
| 计划外项完成分流后 | 必须 |
| 进入/退出 unattended 后 | 必须 |
| 用户 `/progress` | 必须 |
| compact 恢复后 | Coordinator 续跑时必须重渲染 |
| SessionStart | **只注入一行摘要**，不强制全板 |

#### 5.2.5 SessionStart 增强

`session-triage.sh` 在管任务时，现有 slug/phase/status 之外追加：

```text
mode=<attended|afk|unattended> budget=<used>/<total>
板：/progress   指挥：/reassess /attended /unattended
```

保持「不主动续跑压力」策略：只指路，不替用户开跑。

### 5.3 计划外分流：开 issue 或当场修（原建议第 7 点，简化）

#### 5.3.1 规则

在**代码落地**或**验收**中，发现计划以外的 bug 或需要修改的内容时：

- **attended**：必须用 **AskUserQuestion** 问一次——开 issue，或当场修。
- **afk**：按默认策略自动选，写入 progress board + open_items。
- **unattended**：按进入时预授权策略自动选，**禁止提问**。

也可由用户主动 `/side-finding issue|fix` 覆盖当前项。

#### 5.3.2 不改标签枚举

继续使用既有 worker 标签（如 `out-of-scope` / `needs-evaluation` / `bug`）。  
改变的是 **Coordinator 处置协议**，不是 worker 回报形状。

#### 5.3.3 默认策略

| 标签 / 情形 | afk / unattended 默认 |
| --- | --- |
| `bug` 且挡住当前交付 | 当场修 |
| `bug` 且不挡当前交付 | 开 issue |
| `out-of-scope` | 开 issue |
| `needs-evaluation` | 开 issue；仅当明确属于当前 scope 且改动局部时可当场修 |

unattended 进入时可覆盖该默认（见 §5.4.3）。

#### 5.3.4 attended 问法：AskUserQuestion 优先

不用长 Decision Brief 当默认。默认走 Claude Code 原生结构化问题：

```text
header: 计划外问题
question: <一句话是什么 + 挡/不挡当前交付>
options:
  - label: 开 issue
    description: 记入 open_items / 旁路 issue，主交付继续
  - label: 当场修
    description: 纳入当前合法修复范围立即处理
```

仅当需要解释复杂权衡时，才升格为 Decision Brief。

#### 5.3.5 动作落盘

| 选择 | 动作 |
| --- | --- |
| 开 issue | `mmw spinoff` 或等价旁路 + open_items 记 disposition=defer_issue；board 刷新 |
| 当场修 | 纳入当前合法修复范围；记 disposition=fix_now；board 刷新 |

「当场修」第一刀默认**不扩大**现有合法修复边界；若用户要求扩大，单独立项，不混进本切片。

### 5.4 真无人值守（原建议第 10 点）

#### 5.4.1 三模式合同

扩展现有 `loop-state.attendance`，**不另起平行 mode 系统**：

| 模式 | 软停（有合理默认） | 冒泡（缺输入/方向疑） | 计划外分流 | 可否向用户提问 |
| --- | --- | --- | --- | --- |
| `attended` | 停，AskUserQuestion / Decision Brief | 停 | 必问 A/B | 可以 |
| `afk` | 自决+留痕 | 停 | 按默认策略自动 | 仅在 surface/硬门时 |
| `unattended` | 自决+留痕 | **仍停（硬停）** | 按预授权 policy 自动 | **禁止** |

说明：

- `afk` 保持现状：放软停，不放真缺输入 / 方向疑。
- `unattended` = 更强 no-question 合同：软决策全自动，但预算顶 / 设计打穿 / 外部环境 / 无自动路径仍硬停。
- 外层 task 也需可读 mode（实现阶段可镜像到 `task.json` 或由 loop 投影），避免只有内层 loop 知道。

#### 5.4.2 进入条件（全部满足）

1. 用户显式触发：`/unattended`（或次级自然语言明确要求）。
2. 设计已确认（Hard Gate 已过）。
3. 计划已过审 / 已确认可执行。
4. 无未关闭的「必须人答」HITL；或已写入预授权策略。
5. 写盘成功：`attendance=unattended` + `unattended_policy` + board 刷新。

任一不满足 → 拒绝进入，说明缺什么。不静默降级成 afk。

#### 5.4.3 进入时预授权策略（写入磁盘）

```json
{
  "side_finding_default": "auto",
  "hitl_unanswered": "reject_enter",
  "budget_at_100": "hard_stop",
  "design_gap": "hard_stop",
  "external_env": "hard_stop",
  "blocked_no_auto_path": "hard_stop",
  "review_fail": "rework_then_hard_stop"
}
```

| 字段 | 含义 | 第一刀默认 |
| --- | --- | --- |
| `side_finding_default` | 计划外自动策略 | `auto`（用 §5.3.3 表） |
| `hitl_unanswered` | 仍有未答 HITL 时 | `reject_enter` |
| `budget_at_100` | 预算到顶 | `hard_stop` |
| `design_gap` | 设计方向打穿 | `hard_stop` |
| `external_env` | 真机/生产/外部凭证 | `hard_stop` |
| `blocked_no_auto_path` | BLOCKED 且无自动路径 | `hard_stop` |
| `review_fail` | 审闸失败 | `rework_then_hard_stop`（走既有返工/熔断路径，不问人；到 `guard-loop` 熔断则硬停写 board） |

#### 5.4.4 运行中 no-question 合同（双层：磁盘 mode 为权威，disallowed-tools 为活会话兜底）

no-question 有两层，**权威是磁盘 `mode`，不是 `disallowed-tools`**：

- **第一层（跨 compaction 的真权威）**：Coordinator **每次续跑前先读盘上 `attendance`**；读到 `unattended` 就自我约束——不调用 AskUserQuestion / 任何提问交互。这一层不依赖会话运行时态，compaction / 会话重启后照样成立。
- **第二层（活会话硬兜底）**：进入 unattended 时声明 `disallowed-tools: AskUserQuestion`，把该工具从可用池摘掉直到用户下一条消息。它是活会话内的硬封印，但它是**运行时会话态、不落盘**——compaction 后不自动重扣（见下条），所以只当兜底，不当唯一防线。

进入 unattended 后：

1. Coordinator **不得**调用 AskUserQuestion / 任何向用户提问的交互；依据是盘上 `mode`，`disallowed-tools` 只是同一约束的活会话强制。
2. **compaction / 会话重启后必须重新武装**：SessionStart 无法触发 slash command，`/unattended` 又是 `disable-model-invocation:true`，无法靠命令自动重扣 `disallowed-tools`。因此续跑第一步 Coordinator 读盘 `mode=unattended` 后，自我约束（第一层）立即生效即为合同保证；`disallowed-tools` 的重扣发生在 Coordinator 重新进入 orchestrate 流程、再次经过 unattended 激活路径时（best-effort，不是合同前提）。
3. worker 无需处理：Claude Code 具名 subagent 天生就调不了 AskUserQuestion（与 EnterPlanMode 等并列，属依赖主会话 UI 的工具），worker 那条链路免费成立，**不靠传播 `disallowed-tools`**。
4. 唯一对用户输出：进度板刷新、硬停回执、完成回执。
5. 需要人的情况只许硬停，不许「先问一句再继续」。

#### 5.4.5 退出

| 触发 | 结果 |
| --- | --- |
| 用户 `/attended` 或明确要求值守 | 回 `attended` |
| 任务完成 Closing | mode 随 run 结束 |
| 硬停（用户仍不在场） | 盘上**保持 `unattended`** + board 写明原因；`disallowed-tools` 无所谓（无人发消息） |
| 用户回来发**任意消息**（含 `/reassess`） | `disallowed-tools` 此刻必然清除；Coordinator **同步把盘上 `mode` 改回 `attended`**，恢复可提问。要继续无人值守须再显式 `/unattended` |

**盘态与 enforcement 对齐规则**：unattended 期间盘上恒为 `unattended`；用户一旦发消息，运行时封印清除，Coordinator 立即将盘上 `mode` 落回 `attended`——不留「盘写 unattended、实际已可提问」的分叉窗口。

### 5.5 状态落点（Claude Code 正本）

| 数据 | 位置 | 说明 |
| --- | --- | --- |
| 值守模式 | `loop-state.json` 的 `attendance` 扩展为 `attended\|afk\|unattended`；外层可读投影 | 单一 mode 系统 |
| 无人策略 | `task.json` 扩展字段或同目录 `unattended-policy.json` | 进入时写入 |
| 计划外处置记录 | 优先复用 `open_items`；若不够再加轻量 `side_findings` | 避免平行账本 |
| 进度板 | `.claude/multi-model-workflow/progress-board.md` | 投影，可重建 |

机器读写经 `mmw`；agent 不手写 JSON。

### 5.6 文档与阶段 skill 改动边界

| 文档/模块 | 改动 |
| --- | --- |
| `plugin/commands/*` | **新增** command 族（主入口） |
| `plugin/skills/orchestrate/references/control/*` | **新增** steering + attendance 纪律 |
| `plugin/hooks/session-triage.sh` | **增强**一行 mode/budget |
| `plugin/scripts/loop.sh` + schema | **扩展** attendance 枚举与 softstop 行为 |
| `plugin/scripts/mmw.sh` + progress 脚本 | **新增** progress 动词 |
| build / review 阶段 reference | **补**计划外分流协议 + unattended 禁问 |
| scenario `develop` / `bug` / `small-change` | **引用**共享纪律，不复制全文 |
| routes / worker loop / review envelope | **不改内核** |

---

## 6. 关键接口与合同

### 6.1 CLI（挂现有 `mmw`）

```text
mmw progress render [--stdout]
mmw loop attendance --mode attended|afk|unattended
mmw unattended enter [--policy <json-or-flags>]
mmw unattended status
mmw side-finding record --id <id> --disposition issue|fix [--note ...]
```

命名可在实现时按现有 `mmw` 子命令风格微调，但语义不变：progress / attendance / unattended / side-finding。

### 6.2 用户入口（Commands）

```text
/progress
/reassess
/skip-current
/rescope <说明>
/replan-remaining
/force-validate
/attended
/unattended
/side-finding issue|fix
```

### 6.3 主线程行为合同（摘要）

1. 用户 slash command 优先于自然语言猜测。
2. 有 active run 才接受指挥类副作用 command。
3. unattended 下禁止 AskUserQuestion 与任何提问。
4. progress board 不是真相源；冲突以 `task.json` / `loop-state.json` 为准并重渲染。
5. 计划外「当场修」不得偷偷扩大合法修复范围。

### 6.4 与现有 softstop / surface 对齐

| 现有机制 | unattended 下 |
| --- | --- |
| `mmw loop softstop` | 一律走自决+留痕（同 afk） |
| `mmw loop surface`（needs-context / needs-redirection） | 仍硬停；写 board；禁止提问绕过 |
| `guard-loop` 熔断 | 仍硬停 |
| 审闸失败 | 按 policy `review_fail`（默认 `rework_then_hard_stop`）：走既有返工/熔断，不得问人「要不要继续」；到 `guard-loop` 熔断则硬停写 board |

---

## 7. 风险与权衡

| 风险 | 缓解 |
| --- | --- |
| command 太多用户记不住 | 第一版只上表 9 个；SessionStart 与 board 底部列入口 |
| 自然语言与 slash 双入口漂移 | 共享同一 handler / 纪律文档 |
| unattended 误伤该停的场景 | 硬停清单固定且默认拒绝进入未关门任务 |
| progress board 过期 | 关键边界强制 render；`/progress` 先 render 再展示 |
| 计划外当场修范围膨胀 | 第一刀禁止扩大修复边界 |
| `disallowed-tools` 只管到下一条用户消息、且不落盘 | 真权威是盘上 `mode`（§5.4.4 第一层）：续跑先读盘自我约束，`disallowed-tools` 只作活会话兜底。用户回来发消息 → 封印清除 + 盘 `mode` 落回 `attended`（§5.4.5）；需显式再 `/unattended` |
| compaction 后 `disallowed-tools` 丢失但盘上仍 `unattended` | Coordinator 续跑第一步读盘 `mode` 自我约束即保证 no-question，不依赖运行时封印存活；封印重扣为 best-effort |
| 把 Codex 适配路径写进正本 | 本设计明确禁止；状态面只认 `.claude/...` |

---

## 8. 验收标准

### 8.1 功能验收

1. 在 active run 中 `/progress` 能展示与磁盘一致的板。
2. `/reassess` 基于磁盘状态给出可执行结论，不靠聊天记忆。
3. attended 下计划外项必出 AskUserQuestion 二选一；选择可在 board / open_items 追溯。
4. 设计未过门时 `/unattended` 被拒绝。
5. 合法进入 unattended 后，Coordinator 不再提问；遇预算顶/设计打穿/外部依赖硬停并写 board。
6. afk 行为与现状兼容（软停自决，冒泡仍停）。
7. SessionStart 在管任务时能看到 mode 一行与 `/progress` 入口。

### 8.2 非功能验收

1. 无 active run 时副作用 command 不写幽灵状态。
2. board 丢失可用 `mmw progress render` 从真相源重建。
3. 不削弱设计 Hard Gate、worker 零用户交互、审闸预算。
4. 新增 command 有 `disable-model-invocation` 的副作用项不会被模型擅自触发。

### 8.3 明确不做（本切片）

1. 不重做施工面 / routes / worker 内核。
2. 不把 Mission 产品绑进 MMW。
3. 不做复杂计划外标签体系，只做 issue / fix 二选一。
4. 不把自然语言词典当主 UX。
5. 不在第一刀扩大「当场修」合法范围。
6. 不把进度板权威放到 `.codex/` 或 `docs/`。

---

## 9. 落地切片建议（仅设计顺序，不实施）

### Slice A · Commands + Progress 最小闭环

1. `plugin/commands/progress.md` + `mmw progress render`
2. board 路径与刷新边界
3. SessionStart 一行 mode/budget（mode 暂映射现有 attended/afk）
4. steering 纪律文档（command 表）

### Slice B · 计划外二选一

1. attended → AskUserQuestion A/B
2. afk 默认策略 + board/open_items 留痕
3. `/side-finding issue|fix`
4. build/review reference 引用协议

### Slice C · Unattended

1. `attendance` 枚举扩展 + schema/tests
2. `/unattended` 进入门禁与 policy 写盘
3. no-question 合同 + `disallowed-tools` 策略
4. 硬停清单与 board 原因
5. `/attended` 退出

### Slice D · 其余指挥 command

1. `/reassess` `/skip-current` `/rescope` `/replan-remaining` `/force-validate`
2. 自然语言次级兼容
3. 测试与文档同步

---

## 10. 待你确认的开放决策

1. **`side_findings` 是否进 `task.json`**：优先复用 `open_items`；不够再加字段。默认建议复用。
2. **默认模式是否保持 `afk`**：建议保持，避免行为突变。
3. **unattended 遇到未答 HITL 的默认**：建议 `reject_enter`（拒绝进入，不静默 defer）。
4. **当场修是否允许扩大修复范围**：建议第一刀否。
5. **command 命名空间**：**已定 = 插件前缀（零撞车优先）**。插件名 `multi-model-workflow`，故实际调用形如 `/multi-model-workflow:progress`、`/multi-model-workflow:unattended`。本文其余处（§5.1.2 / §6.2）为可读性写短名 `/progress` 等，**均代表带前缀的完整命令**；command 文件仍按短名放 `plugin/commands/<name>.md`，前缀由插件机制自动加。

---

## 11. 结论

本设计把四项能力落成 Claude Code plugin 控制面增强：

1. **中途指挥** → `plugin/commands/*` 第一，自然语言次级兼容，动作统一进 `mmw`。
2. **进度板** → `.claude/multi-model-workflow/progress-board.md`，`mmw progress render`，SessionStart 一行摘要。
3. **计划外分流** → attended 用 AskUserQuestion；afk/unattended 按策略自动。
4. **真无人值守** → 扩展现有 `attendance`，强 no-question + 硬停清单，不另起 mode 系统。

施工面不动。确认 §10 后进入 plan-writing。
