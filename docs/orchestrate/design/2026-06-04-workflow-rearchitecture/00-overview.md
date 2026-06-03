# Workflow 架构精简与升级 · 总览（骨架 / 绑定契约）

> **本文件是整套升级改造方案的灵魂与绑定契约。** 它定义病根、锁定决策、目标架构、保留清单与不变量；`01`–`08` 各分册在本契约的约束内展开细节。任何分册与本文件冲突，以本文件为准。
>
> - 日期：2026-06-04
> - 状态：设计草案（待用户复核 → 待 Codex 对抗评审 → 转 plan-writing）
> - 适用对象：`plugin/`（MultiModel Worktree Plugin，当前 v3.10.0）
> - 方法论：本方案以 **plugin 源码为唯一 ground truth**，历史文档仅作见证。下方所有"证据"列均已由主线程亲自 `Read`/`grep` 核验。

---

## 1. 执行摘要（业务语言）

这套编排系统的设计意图是对的、要保留：**文档即上下文（Document-as-Context）+ Plan 级 Worker 自治 + 主线程只做思考与调度 + Codex 作外部对抗评审**。它现在的四个毛病——开发被拖慢（僵硬）、烧主线程上下文、太复杂、有冗余——**根子是同一个**：

> **"流程怎么走"被写死在散文文档里，靠主线程读完再"自觉"执行，真正能强制的机器（脚本/钩子）几乎不参与控制。**

后果：① 重型流程和轻量小改被同一台机器吞进去，而所谓"轻量旁路"是一张没人执行的便签；② 主线程每进一个阶段要重读上万字规则；③ 成本护栏被做成"到一半硬卡住等人"的阻断闸，让"无人值守自主跑"名存实亡；④ 上一轮"逐条删字"瘦身切了符号留了机制，删完又被改回，文档与代码系统性漂移。

**本方案不再"切 cut-list"，而是做一次真正改变结构的重排**：把"流程形态"（有哪些阶段、允许怎么跳、每阶段的门禁/预算参数）从写死在 bash 数组 + schema enum + hook 字面量三处，抽成**一份声明式清单数据**，让机器读这份清单做校验。于是"轻量任务跳过设计评审"变成清单里合法的一行、而不是靠绕；预算从硬闸门降为仪表。**这同时解决四个毛病，且不丢任何现有能力。**

---

## 2. 病根诊断（已源码验证）

一个病根，四个症状。每条都附已核验的源码证据。

| 症状 | 根因（非表面） | 已核验证据 |
| --- | --- | --- |
| **僵硬（最痛）** | 轻量旁路是假的：没有任何机器执行点。Hard Gate"每个项目都走 Discovery，无论看起来多简单"逐字注入 6 个 SKILL，而轻量变体依赖的 `phase_skip` 字段**零 hook 消费**。两条指令打架，跳不跳全靠主线程自觉。 | `grep phase_skip plugin/` → 只在 文档/schema/`state.sh:152`(写`[]`)/`SKILL.md:68,70`/2 个 test，**无任何 hook 读取**。Hard Gate 命中全部 6 个 orchestrate SKILL.md，单源 `build/templates/preamble.md.tmpl`。 |
| **僵硬（控制越权）** | 流程形态写死：`TRANSITION_MATRIX` 是硬编码 bash 白名单，校验 hook 用字面量判 `phase==execution`。预算更进一步把成本护栏做成硬阻断闸：Direction Check 触发即 `exit 2` 阻断所有非 reviewer 派发，AFK 场景卡死等人 ack。 | `state.sh:73-98` 硬编码数组，含 `Pack 2.14 / Plan 005` 死注释。`validate-plan-dispatch.sh:75` `if [[ "$PHASE" == "execution" ]]`；`:66-70` 读 `pending_direction_check.ack_status` → `exit 2`（route 仅在注释 :15）。 |
| **烧 token + 复杂** | 控制流写在散文里：主线程既要消化（token）又要自觉执行（无机器强制=僵硬）。同一条纪律在 N 个文件各写一份，主线程在 ~5959 行指令面之间来回对账。 | `plugin/skills` 总计 5959 行；单进一次 execution 阶段纯指令文本 ~48KB（SKILL+references，不含 `_shared` 的 ~12KB），≈16K token。session-start 常驻注入仅 ~450 token（2.8%）——**真正大头在阶段指令的重复 Read，不在常驻注入**。 |
| **冗余（治标不治本）** | 上一轮逐条 cut 有部分"标完成未落地"，文档/代码系统性漂移，主线程读到自相矛盾的指令。 | `architecture-draft.md:5` 自标 "3.8.0"，`plugin.json` 已 3.10.0。`state.sh:916` 现为 `3*plan_count+12`（曾提议 2P+6，被 commit `743f447` 改回）。Path A / Targeted Re-Review 仍活在 canonical 路径，文档却称已删。 |

**外部 skill 接线乱象（新增维度，已核验）**：三种机制并存无统一策略——frontmatter 嵌入（`pack-executor`/`complex-pack-executor`=`tdd`；`root-cause-analyst`=`diagnose,tdd`）、运行时 `Skill()` 调用（`improve-codebase-architecture`/`grill-with-docs`/`frontend-design`/`prototype`/`triage`/`zoom-out`）、散文内化（`to-issues`→`issue-splitting.md`）。**`impeccable` 全仓零引用、`to-issues` 零引用、`zoom-out` 疑似悬空引用**（不在已安装 skill 列表）。4 个 agent（explorers/plan-writer/docs-worker）未嵌任何 skill。

---

## 3. 已锁定决策（locked priors）

以下为用户 2026-06-04 拍板，作为后续全部分册的不可动摇前提：

| # | 决策 | 选择 | 对设计的约束 |
| --- | --- | --- | --- |
| D1 | **快车道边界** | **激进线** | 默认走轻档（Light Lane）；只有用户明确说"大改造/新功能"，或改动触碰**计费/权限/数据权威/用户可见合同**时，才自动升级完整流程（Formal Lane）。 |
| D2 | **快车道外审** | **默认免、可手动加** | Light Lane 默认不派 Codex；保留用户对单次改动手动要求一次外审的入口。 |
| D3 | **无人值守超支** | **软继续 + 到顶停** | AFK 模式：过半只记提醒并继续，到 100% 才停（escape hatch）；在场模式：保留过半停顿。 |
| D4 | **重构幅度（目标函数）** | **明显降 token + 提速，地板=流程相对稳定** | "相对稳定"= 几乎不跳步、不忘调用该调的外部 skill。→ 采用结构性适中版（见 §4）。注意：机器强制比散文自觉**更稳定**，故结构化方向与"稳定地板"同向。 |
| D5 | **外部 skill = 战略杠杆** | 立为独立支柱 | 外部 skill 用于：① 减轻自研 workflow 维护负担；② 靠上游持续更新、汲取外部方法；③ 嵌进 sub-agent 提升专项能力。详见 `06`。 |

**D1 与 D4 的兼容性说明（重要）**：D1 选"激进默认轻档"，D4 要求"不跳步"。二者不矛盾——"激进"指的是**默认选择轻档这一有意动作**；机器仍强制每条档位内部该有的步骤与 skill 调用，不会"误跳"。今天的不稳定恰恰来自散文自觉执行，结构化后稳定性是提升的。

---

## 4. 目标架构总览：B+ 数据驱动流程清单 + 控制平面瘦身

**一句话**：把"流程形态"从代码三处硬编码抽成一份声明式 routes 清单数据；机器读清单做 transition 校验与 gate 豁免；轻档成为清单里的一等公民而非贴在重机器上的便签；预算从硬闸门降为仪表。**不碰** worker-loop / Document-as-Context 派发层（它们是健康的、要保留）；**不做**一次性大重写引擎（避开 compaction recovery 重测风险）。

### 控制平面 vs 内容平面（核心切分）

```
┌─ 控制平面（机器读取的数据 + 薄强制逻辑）──────────────────┐
│  routes 清单（声明式数据）：phase 序列 / 合法跳转 / gate 豁免 / budget 参数 │
│  state.sh（瘦身）：读 routes 做 transition；删死行；mutations 降级       │
│  hooks（重排）：读 routes 判 gate；轮次截断机器化；fire-on-every-Bash 瘦身 │
└──────────────────────────────────────────────────────────┘
┌─ 内容平面（人/模型读取的指令与文档）────────────────────┐
│  SKILL.md（瘦身为"当前 phase 做什么"的薄指令，流程形态移出散文）        │
│  references（参数化切片：phase 只 Read 需要的 gate+angle 段）          │
│  设计/计划/issue 文档（Document-as-Context，原样保留）                 │
└──────────────────────────────────────────────────────────┘
┌─ 能力平面（外部/内部 skill 杠杆，新支柱）──────────────────┐
│  embed（frontmatter 嵌 subagent） / invoke（运行时 Skill()） / 不再 internalize │
└──────────────────────────────────────────────────────────┘
```

### 分层改造摘要（现状 → 目标）

| 层 | 现状（已验证） | 目标 | 分册 |
| --- | --- | --- | --- |
| **流程形态** | `TRANSITION_MATRIX` bash 硬编码 + schema enum + hook 字面量三处 | 单一声明式 routes 清单数据，机器读取 | `02` |
| **轻量旁路** | 假的 `phase_skip`（零消费） | Light Lane = routes 一条数据 + hook 真豁免 gate + 一键升级门 | `03` |
| **预算** | `3P+12` 硬编码 + 80% 硬 `exit 2` + 不随 reflux 重置 + effort=2× | 仪表化：软继续+到顶停 + 可配置上限 + reflux 重置 + 删 effort 2× | `04` |
| **Skill/Context** | 6 SKILL 各注入 preamble/voice；阶段全量 Read references | SKILL 瘦身 + 参数化切片（运行时真省）+ 漂移根治 | `05` |
| **外部 skill** | 三机制并存无策略；impeccable/to-issues 零接线；zoom-out 悬空 | 统一 embed/invoke 策略 + 补接线 + skill→subagent 矩阵 | `06` |
| **Agent/Hook** | twin 90% 重叠；13 脚本/16 注册；3 个 fire-on-every-Bash 门禁 | twin 收口 build 单源 + skill 嵌入 + hook 重排（删假门、截断机器化） | `07` |
| **迁移** | 上轮逐条 cut 漂移 | 低风险分期 + 差异对照 + 量化验收 + 回滚 | `08` |

---

## 5. 保留清单（承重 + 珍贵外部经验，一个不丢）

新架构**必须**让以下能力原样存活（详见 `01`）。这是"不丢能力"的硬约束：

1. **Document-as-Context 派发层**：envelope 只传 `plan_id+plan_path`，Worker 自读，不粘贴 Pack 内容（`execution-worker-dispatch.md:8` 起，待 `01` 复验）。
2. **Plan 级自治 Worker**：一个 Plan 一个 Worker，35–55 次 pack 派发收敛为 7–11 次 plan 派发（历史最大省点）。单一共享工作树（worktree-per-worker 已否决，勿再提）。
3. **磁盘状态抗断点续传**：workflow-state cursor + execution-state per-pack `committed` + `state-lock.sh` mkdir 原子锁。
4. **Source Stability 自动重审门**：`last_gate_timestamp`（`state.sh:314` 写）+ `git log --since` 检测 review 通过后 source 是否被改。与 cursor 职责正交，不可二选一。
5. **子代理返回必验纪律**：Coordinator 必 `Read`/`grep` 验证 worker/reviewer 返回的 hash/路径/计数后才采信。
6. **Codex 外部对抗评审 + 模型分层**：Design/Plan 用 GPT-5.5 xhigh，Execution 用 GPT-5.4 xhigh。用户珍视的核心价值。
7. **抑制外部模型幻觉四件套**：Confidence rubric + Pre-emit Verification Gate（finding 必引 file:line）+ 证据表 + Bias indicators。
8. **Discovery 双文档对等** + grill-with-docs 维护术语 + Explorer 报告校验门控。
9. **Mockup 与文字设计平级、原子拆解为视觉规格表**（不只传目录路径）。
10. **Worker 禁改 docs/**（`guard-doc-edit.sh` worker-active marker）+ checkbox toggle 是 Coordinator 专属。
11. **Anti-Sycophancy + Push twice + Honesty Rule + Decision Brief**（voice-directive 是其物理载体，去重时每条派发路径必须仍走 build 注入）。
12. **vertical-slice / tracer-bullet + AFK 优先于 HITL 的大 issue 拆分内核**。
13. **idempotency_key 防 compaction 后重复派 agent/重复计费**（计费不变量）。
14. **成本护栏的核心诉求**（机制可重做，诉求保留）：长 session 防无限烧 token。
15. **gstack §7"明确不借鉴"清单**（全量内联 3000 行 SKILL / Review Army / 完整 Dual Voice / 静默降级 / Jargon 术语表）——已论证的反向决策，勿再提。
16. **`git merge --squash` 禁令 + 未勾选任务阻断 push**。
17. **merge-brief §4/§5/§6 字段约定**（conflict_id/status 枚举）被 `state.sh:1582` 运行时正则消费，降级 schema 时字段名/枚举必须原样保留。

---

## 6. 北极星不变量（不可破）

无论怎么精简，以下不变量任何分册不得违反（违反 = 方案作废）：

- **计费/LINEAGE**：idempotency_key 防重复计费；任何派发去重逻辑不得绕过它。
- **状态权威**：磁盘状态是 compaction/断点续传的唯一可信源；不得把关键状态只留在主线程上下文里。
- **数据权威**：docs/ 下设计/计划是 source of truth；Worker 不得改 docs/；checkbox 由 Coordinator 按 plan-return 翻。
- **质量门最小集**（即使 Light Lane 也保留）：子代理返回必验、Worker 禁改 docs/、未勾选任务阻断 push。
- **核心红线自动升级**：改动触碰计费/权限/数据权威/用户可见合同 → 必须走 Formal Lane（有 reviewed design）。

---

## 7. 文档集导航与每分册职责契约

后续分册由本骨架绑定。每分册**必须**：以源码为 ground truth、引用 `file:line`、不与本骨架冲突、产出可被 plan-writing 阶段直接消费的结构。

| 分册 | 职责（边界） | 必须覆盖 |
| --- | --- | --- |
| `01-preserve-and-invariants.md` | 把 §5 保留清单 + §6 不变量展开为可验收的"承重契约"，逐条给源码锚点 + "若被破坏会丢什么" | 复验 worker-dispatch-minimal、last_gate、merge-brief 字段；给每条保留项的"机器化守卫现状 vs 目标" |
| `02-routes-as-data.md` 【核心】 | 声明式 routes 清单的数据结构设计 + state.sh/hook 如何读它做 transition 与 gate；列出所有现"读 phase 字面量"的消费点改造 | routes schema 字段；`TRANSITION_MATRIX` 死行清理；hook 从 `PHASE==execution` 改读清单；向后兼容 |
| `03-light-lane-and-escape-hatch.md` | Light Lane 完整设计（D1 激进默认）+ 机器执行点 + 一键升级 `cmd_budget_reinitialize`（unlimited→bounded 缺口）+ hotfix/spike 子模式 + D2 外审策略 | Entry 判定线；hook 豁免；升级门状态机；删假 phase_skip 的连带清理清单 |
| `04-budget-as-instrument.md` | 预算从硬闸门降仪表（D3 软继续+到顶停）+ 可配置上限 + reflux 重置 + 删 effort 2× + AFK/在场双模式 | `state.sh:916` 公式参数化；删 `exit 2` 硬阻断的安全替代；review_used reset 逻辑 |
| `05-skill-and-context-economy.md` | SKILL 瘦身（流程形态移出散文）+ 参数化切片（运行时真省 token，非仅 build-time）+ 漂移根治（architecture-draft 重写、假删正名、统一截断） | 量化每项省 token；区分"已建单源"与"待删 wrapper"；三套截断统一为参数 |
| `06-external-skill-strategy.md` 【新支柱】 | embed/invoke/internalize 三机制统一策略 + skill→subagent 嵌入矩阵 + 补 impeccable/mockup 接线 + 清 zoom-out 悬空 + 上游更新如何持续汲取 | 决策树（何时 embed vs invoke vs 不内化）；逐 agent 嵌入建议；Mockup 设计 skill 接线 |
| `07-agent-and-hook-layer.md` | agent twin 90% 重叠收口 build 单源 + skill 嵌入落地 + hook 强制层重排（删假门、轮次截断机器化、fire-on-every-Bash 瘦身、state.sh 死行、merge-brief schema 降级、build resolver 塌缩） | 逐 hook 保留/精简/删 + 风险；voice-directive 去重的承重守卫 |
| `08-migration-rollout-acceptance.md` | 低风险分期顺序 + 现状↔目标差异对照表 + 量化验收（降 token/提速）+ 回滚 + 测试套件影响 | 分期依赖图；每期验收信号；不变量回归测试 |

---

## 8. 验收信号（D4 目标函数的可观测化）

本方案落地后应可观测到：

1. **明显降 token**：进入 Light Lane 的小改动**完全跳过** Discovery（~9.5KB 指令 + 2 次 xhigh Codex job）；Formal Lane 单阶段指令文本经参数化切片后较现状 ~48KB 显著下降（目标量化见 `05`/`08`）。
2. **明显提速**：日常小改从"被拖完整流程"变为轻档直达；预算不再中途硬卡。
3. **流程相对稳定（地板）**：该走的步、该调的 skill 由机器（routes 清单 + hook）保证，不靠主线程自觉——稳定性较现状**提升**。
4. **逃逸旁路真实可用**：Light Lane 有机器执行点；一键升级门存在且经测试。
5. **漂移归零**：architecture-draft 与源码一致；不存在"文档说删了代码还活着"。
6. **能力零丢失**：§5 保留清单逐条仍可用（`08` 给回归测试）。

---

## 9. 后续流程

本草案 → 用户复核 → **Codex 对抗评审（Design tier, GPT-5.5 xhigh）批判修订** → 转 `orchestrate-plan-writing` 拆实施计划 → 串并行落地。
