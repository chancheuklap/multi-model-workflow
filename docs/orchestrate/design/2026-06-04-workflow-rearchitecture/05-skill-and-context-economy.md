# 05 · Skill 瘦身与上下文经济 + 漂移根治

> 本分册在 `00-overview.md` 骨架约束内展开。职责：**让主线程真正少烧 token，并根治文档↔源码漂移**。
> 与骨架冲突以骨架为准。所有源码主张均由本分册作者亲自 `Read`/`grep` 核验，附 `file:line`。
>
> - 上游契约：`00-overview.md` §4（控制平面 vs 内容平面切分）、§5 保留清单（第 7/11 项）、§6 北极星不变量。
> - 锁定决策约束：D4（明显降 token + 提速，地板=流程稳定）是本分册主目标函数；D1/D5 间接相关。
> - 下游消费：本分册结论将由 `orchestrate-plan-writing` 直接拆 task。

---

## 0. 结论先行（给 plan-writing 的可执行摘要）

本分册有四个产出，按"运行时真省 token"的价值排序：

1. **参数化切片（运行时真省，最高价值）**：phase 进入时只 Read 它需要的 gate/angle 段，而非全量 Read 整份 `_shared`。今天每个派发 review 的 phase 都把 `review-dispatch.md`（6576 字符）+ `repair-routing.md`（5753 字符）**整份**读进主线程上下文——而它当下只用其中一小段。切片机制把"读整份"变成"读它当前 step 需要的那一节"。**这是唯一真正减少运行时 token 注入的改造。**
2. **SKILL 瘦身（账面 + 部分运行时）**：把"流程怎么走"（phase 序列、合法跳转、step→step 路由）从散文移进 `02` 的 routes 清单数据，SKILL 只留"当前 phase 这一步做什么"的薄指令。execution SKILL.md 现 20214 字符，瘦身后可砍掉重复的 Hard Gate/Only-stop/signpost/流程位置散文。
3. **三套修复截断统一**：execution（2 worker + 1 RCA = 3 轮）、final-review（1 repair + 1 RCA）、plan-review（2 轮）三处各写一份散文截断策略，统一为单一参数化策略 `max_repair_rounds + escalate_to_rca`，各 phase 传值；且**轮次截断由 hook 读 `repair_round` 机器强制**——今天它纯散文，没有任何 hook 设上限。
4. **漂移根治**：重写 `architecture-draft.md` 校准到 v3.10.0（它是唯一总览图，**重写不删**）；清掉文档里描述"还活着的旧机制"的过时段落（范围 **2 项**，下文逐项指明）；区分"D1 已落地的单源（preamble/voice-directive/signpost 已走 build 单源）"与"待删 wrapper"。

**诚实标注（贯穿全文）**：要严格区分两种"省"——

| 省的类型 | 含义 | 例子 | 是否减少主线程烧的 token |
| --- | --- | --- | --- |
| **账面省（build-time）** | 单源化 consolidate：一份内容写一处，build 注入多处。维护时只改一处。 | preamble/voice-directive 单源到 `.tmpl` | **否**。运行时仍把全文注入每个 SKILL，token 一字不少。 |
| **运行时真省** | 减少注入主线程上下文的字节 | 参数化切片：只读需要的段；删 SKILL 散文 | **是**。 |

不能拿"已经单源化了"冒充"省了运行时 token"。这是本分册最重要的诚实边界。

---

## 1. 参数化切片（运行时真省的关键）

### 1.1 现状（源码锚点）

**每个派发 Codex review 的 phase，都被指令"整份 Read" `_shared/review-dispatch.md`（6576 字符）。** 验证：

- `_shared/review-dispatch.md` 字节数 6576（`wc -c skills/_shared/review-dispatch.md`）；`_shared/repair-routing.md` 5753 字符；`disposition-table.md` 2760；`decision-brief.md` 988。
- `review-dispatch.md` 被以下 **10 处**指令"按其格式" Read（每处都是整份）：`orchestrate-execution/SKILL.md:264`、`execution-review-dispatch.md`、`execution-release-gate.md`、`final-review-angles.md`、`final-review-release-gate.md`、`plan-review-dispatch.md`、`merge-integration-review.md`、`bug-investigation-route.md`、`workflow-direct-repair.md`、`design-review-angles.md`（`grep -rln "_shared/review-dispatch.md" skills/`）。
- `repair-routing.md` 被 **9 处** Read（`execution-repair-truncation.md:11`、`final-review-repair.md:7` 等）。

**指令形态是"整份读"，不是"读某节"。** 验证 `orchestrate-execution/SKILL.md`：

- `:264` `**Read** plugin/skills/_shared/review-dispatch.md 并按其格式派发 Codex review。`
- `:272` `**Read** plugin/skills/_shared/disposition-table.md 并按其 disposition 选项处理 findings。`

没有任何"只读 §X 节"的语义。`build/build.sh` 的锚点机制（`<!-- BEGIN: xxx -->`）只支持**整块替换**，不支持节级切片（`grep -ni "section\|slice\|partial\|fragment" build/README.md` 无命中）。

**为什么这是真烧 token**：`review-dispatch.md` 的 6576 字符里，主体（`:32-69`，约 2400 字符）是**抑制外部模型幻觉四件套**——Confidence rubric + Pre-emit Verification Gate + 证据表 + Bias indicators。它属于 **review prompt 的内容**（要写进发给 Codex 的 prompt），不是主线程派发动作需要消化的指令。主线程读它只为"把这块原样拷进 review prompt"，但它每次都进了主线程的上下文窗口。disposition step 读 `disposition-table.md` 时，又只需要其中的 disposition 选项表（`:32-43`），不需要 Confidence 校准全表。

### 1.2 问题

- **同一份 `_shared` 文件服务多个不同 step，但每次全量注入。** review-dispatch 既含"派发动作脚本"（Coordinator 要执行）又含"review prompt 内容块"（要拷给 Codex）；disposition step 不需要派发脚本，派发 step 不需要 disposition 表。
- **`_shared` 是"为复用而合并"的产物，复用省的是维护（账面），代价是运行时每次全读。** 骨架 §4 已点明"真正大头在阶段指令的重复 Read，不在常驻注入"（`00-overview.md:32`：session-start 常驻注入仅 ~450 token / 2.8%）。

### 1.3 目标设计：节级切片（fragment-addressable shared content）

把 `_shared` 文件内部按**消费 step** 切成命名片段，phase 的 step 只 Read 它需要的片段。两种落地路径，推荐 **B**：

**路径 A（轻量，纯文档约定）**：在 `_shared` 文件内用二级锚点标注片段边界，phase step 的 Read 指令带"只读 `<fragment>` 节"语义。缺点：靠主线程"自觉只读一节"——和骨架病根（散文靠自觉）同病，**不采用为主方案**。

**路径 B（推荐，build resolver 产出切片文件）**：复用现有 build 锚点 + resolver 机制（`build/build.sh:48` resolver 接受 `anchor_name` + `variant` 两参），把 `_shared` 的逻辑片段在 **build 时**物化为独立小文件，phase step 直接 Read 那个小文件。即：

- 源：`_shared/review-dispatch.source.md`（单源，含全部片段 + 片段锚点）。
- build 产出（resolver 切片）：
  - `_shared/fragments/review-dispatch.dispatch-steps.md`（派发动作脚本，`:1-31` + `:71-73` compaction recovery）
  - `_shared/fragments/review-prompt-quartet.md`（幻觉抑制四件套 `:32-69`，**这块是 review prompt 内容，被写进 prompt，不需主线程消化逻辑**）
  - `_shared/fragments/disposition-options.md`（disposition 表 `:32-43`）
  - `_shared/fragments/disposition-discipline.md`（亲验纪律 + Confidence 校准 + 审计写入 `:3-30,44`）
- phase step 改 Read 指令指向对应 fragment 文件。

**切片维度 = 消费 step，不是话题。** 切的依据是"哪个 step 在什么时候用到这段"，而非语义分类。例如 disposition step 读 `disposition-options.md` + `disposition-discipline.md`，但**不**读 `review-prompt-quartet.md`（那是 review 派发时拷进 prompt 的）。

**为什么用 build 而非运行时拼**：build 机制已存在且经测试（`build/tests/`），resolver 是纯 bash 字符串操作，不引入运行时新依赖（不过度设计，符合用户核心原则 #14）。fragment 文件是 build 产物，源单一（`.source.md`），改一处 build 一次，账面省同时保住。

**诚实标注**：路径 B 的 fragment 物化本身**也是单源化**（账面省）。运行时真省来自"step 只 Read 它需要的那个 fragment"这一行为改变——前提是切片粒度对，让每个 step 读到的字节显著小于原整份。若一个 step 真的需要整份内容，切片对它无运行时收益（不强切）。

### 1.4 量化（保守估算，待 `08` 实测复核）

以 execution phase 一次完整 plan review + disposition + repair 为例：

| step | 现状 Read（整份） | 切片后 Read | 节省 |
| --- | --- | --- | --- |
| Step 7 派 review | review-dispatch 6576 | dispatch-steps ≈ 3400 + quartet 2400（quartet 进 prompt 不是逻辑消化，仍需读取拷贝） | dispatch 逻辑面 ≈ 砍 3176 |
| Step 8 disposition | disposition-table 2760（整份） | disposition-options ≈ 900 | ≈ 1860 |
| Step 10 repair | repair-routing 5753（整份） | 当前 finding 形态对应的 owner 行 + 回归证据要求 ≈ 2800 | ≈ 2900 |

单次 execution review-repair 循环的 `_shared` 注入：现 ≈ 15089 字符 → 切片后逻辑面 ≈ 9100 字符（quartet 仍读但用途明确），**逻辑消化面省 ≈ 40%**。跨 6 个 phase × 多次循环，运行时累积可观。**精确数字以 `08` 实测为准**——这里给的是机制和量级，不是承诺值。

### 1.5 风险

- **切片粒度错会两头不讨好**：切太碎 → step 要读多个 fragment，反而增 Read 次数；切太粗 → 没省。缓解：以"现有 step Read 边界"为切割线（已经是 phase 在用的自然边界）。
- **quartet 是 §5 第 7 项保留项**：抑制幻觉四件套一字不能丢、不能弱化。切片只改"在哪个文件"，不改内容。切完必须 `grep` 确认四件套全文在 prompt 注入路径上仍存在。

### 1.6 验收信号

- 任一 phase 的某个 disposition step 不再 Read 含"派发脚本"的整份 review-dispatch。
- `08` 实测：execution 单循环 `_shared` 逻辑面注入字符数较现状下降 ≥ 30%。
- quartet 四件套在 review prompt 注入路径上 `grep` 全文仍在（保留项零丢失）。

---

## 2. SKILL 瘦身（流程形态移出散文）

### 2.1 现状（源码锚点）

`orchestrate-execution/SKILL.md` 377 行 / 20214 字符，加 references 28044 字符 = **48258 字符 ≈ 16K token**（与骨架 `00-overview.md:32` 一致）。其中"流程形态"散文占相当篇幅：

- **signpost 锚点（`:6-24`）**硬编码 formal phase 序列散文：`:18` `workflow → discovery → plan-writing → execution → final-review → execution_done → closed`。这段由 build 单源注入 **6 个 SKILL**（`grep -c "Phase 序列" skills/orchestrate-*/SKILL.md` → discovery/execution/final-review/multi-pr-merge/plan-writing 各 1，workflow 0），源 `build/templates/signpost.md.tmpl:11-12`。
- **流程位置散文**散落各处：`:119` `> **流程位置**：per-plan 循环 · 通过 → Step 13；needs repair → Step 10`；`:282` `修复通过后 → Step 13...→ Step 14`；`:286`、`:303`、`:321`。这些是 step→step 的跳转图，写成散文靠主线程读懂再跳。
- **重复的 Only stop / Never stop**：preamble 锚点 `:35-42` 一组，SKILL 正文 `:82-92` 又一组（两组语义重叠，各服务不同层）。

### 2.2 问题

- **流程形态（有哪些 phase、怎么跳、step 间路由）写死在散文里，主线程每进一个 phase 重读一遍。** 这正是骨架 §1 病根："流程怎么走被写死在散文文档里，靠主线程读完再自觉执行"。
- signpost 的 phase 序列散文与 `02` 即将建的 routes 清单数据**重复**——同一信息两处，必然漂移（骨架 §2 已记 architecture-draft 版本漂移先例）。

### 2.3 目标设计

**原则：流程形态进 `02` routes 清单数据（机器读），SKILL 只留"当前 phase 这一步做什么"的薄指令。**

具体迁移：

1. **phase 序列散文 → routes 清单（引 `02`）**：signpost 的 `Phase 序列（formal route）：workflow → ...` 这行散文删除，phase 序列由 `02` 的 routes 数据声明。SKILL 的 signpost 锚点只保留"完成时调 `state.sh transition` 写下一 phase"的动作指令——下一个 phase 是什么由 routes 数据给，不在散文里写死。
2. **step→step 路由散文 → 薄跳转标注**：`:119`、`:282` 等"流程位置 / 通过→Step N"散文，保留**最小**跳转提示（主线程仍需知道"这一步通过去哪"），但删掉重复表述。判断线：同一跳转信息只写一次。
3. **Only stop / Never stop 去重**：preamble 锚点（build 单源 `:35-42`）是通用层，SKILL 正文 execution 专属层（`:82-92`）是 execution 特化层。保留两层但确认无逐字重复——通用条目（BLOCKED）不在专属层再写一遍。

**不动的部分（保留）**：
- preamble / voice-directive 的实质内容（Honesty Rule、Hard Gate、Anti-Sycophancy）是 §5 第 11 项保留项，不删，继续 build 单源注入。
- DISPATCH_ENVELOPE 块（`control-envelope` 锚点 `:146-176`）是计费/派发不变量载体（§6），原样保留。
- Worker 类型选型表（`:131-144`，Risk × Context 双维度）是执行决策核心，保留。

### 2.4 量化

execution SKILL.md 20214 字符中，可移出/去重的流程形态散文估 **2000-3500 字符**（signpost phase 序列行 + 重复 Only/Never stop + 重复流程位置标注）。这部分**移出后是账面 + 部分运行时省**：signpost 经 build 注入 6 个 SKILL，删一处源（`signpost.md.tmpl`）= 6 处 SKILL 各少 ~150 字符运行时注入。SKILL 主体瘦身的运行时收益小于参数化切片（§1）——**SKILL 是进 phase 必读的，砍散文省的是固定头部；切片省的是按需的大块 `_shared`**。

### 2.5 风险

- **删流程散文不能让主线程"不知道下一步"**：routes 数据给的是机器校验的合法跳转，主线程仍需一个"我现在该读哪个 reference"的薄索引。SKILL 必须保留这个薄索引（step → reference 文件映射），只删冗余的散文解释。
- **依赖 `02` 先落地**：phase 序列移出散文的前提是 routes 清单数据存在且机器在读。`02` 未落地前，本项只能做"去重"不能做"移出"。**强依赖 `02`**。

### 2.6 验收信号

- `signpost.md.tmpl` 不再硬编码 phase 序列散文；phase 序列单一来源是 `02` routes 数据。
- execution SKILL.md 字符数较现状下降（目标 `08` 量化）。
- 主线程进 phase 后，"下一步读哪个 reference" 仍有明确薄索引（不靠记忆）。

---

## 3. 三套修复截断统一为单一参数化策略

### 3.1 现状（源码锚点）——三套各写一份，且纯散文无机器强制

| phase | 截断策略 | 源码锚点 |
| --- | --- | --- |
| execution | 2 worker repair + 1 RCA = **3 轮** | `execution-repair-truncation.md:113` "最多 2 Worker repair round + 1 root-cause-analyst round = 3 repair round"；`:119` Round 3 截断新建 RCA |
| final-review | 1 repair + 1 RCA escalation | `final-review-repair.md:124` "每个 gap 最多 1 个 repair round + 1 个 RCA escalation" |
| plan-review | **2 轮** | `plan-review-resolution.md:85` "Plan Review 最多 2 个 repair round"；`:90` Round 2 截断 |

每套是一段独立散文 + 独立 Round 表，结构高度相似但各写一份（漂移温床）。

**关键问题：轮次截断没有任何 hook 机器强制。** 验证：

- 唯一读 `repair_round` 做校验的 hook 是 `validate-plan-dispatch.sh:39,122`——但它只校验 "repair_round≥1 时 disposition_refs 必须 accepted + 有 evidence"（`:122-145`），**不设轮次上限**。
- `grep -rn "max.*round\|round.*>=\|exceed\|truncat" hooks/*.sh`（排除 test）→ 零命中轮次上限检查。`validate-multi-pr-dispatch.sh:104-117` 只校验 repair_round 与 merge-brief stage 的一致性，不设上限。
- 即"最多 3 轮 / 2 轮"完全靠主线程读散文后自觉停——和骨架 §1 病根同构。

### 3.2 问题

- **三份散文 = 改一处忘两处的漂移源。** 骨架 §2 已记录上轮 cut-list "标完成未落地"漂移。
- **轮次上限靠自觉 = D4 地板（流程稳定）的漏洞。** 主线程若读漏或 compaction 后忘了轮次，可能无限修或提前停。机器强制比散文自觉更稳（骨架 D4 说明：机器强制比散文自觉更稳定）。

### 3.3 目标设计：两参数 + hook 机器强制

**单一参数化截断策略**，每个 phase 在 routes 数据（`02`）里传两个值：

```
repair_policy:
  max_repair_rounds: <int>   # worker/coordinator 修复轮上限
  escalate_to_rca:   <bool>  # 到顶后是否升级 RCA（再给 1 轮）
```

各 phase 取值（与现状等价，不改行为，只改表达）：

| phase | max_repair_rounds | escalate_to_rca |
| --- | --- | --- |
| execution | 2 | true（RCA = 第 3 轮） |
| final-review | 1 | true |
| plan-review | 2 | false（到顶 BLOCKED/backflow，无 RCA） |

**截断改为 hook 机器强制**：在派发修复的 validate hook（execution 走 `validate-plan-dispatch.sh`）增加一步——读 envelope 的 `repair_round` 与该 phase 的 `max_repair_rounds`（+ escalate 余量）对照，**超限即 `exit 2` 阻断派发**，并提示"已达修复轮上限，应走 RCA escalation 或 BLOCKED"。截断不再停在散文层。

- `repair_round` 已在 envelope 里且被 hook 读取（`validate-plan-dispatch.sh:39`），只是没拿来比上限——**接线成本低，机制已就位**。
- 上限值从 routes 数据按 phase 取（不在 hook 里硬编码每 phase 的数字），保持单源。

**散文侧**：三份截断 reference 的 Round 表收敛为"引用本 phase 的 `repair_policy` 参数"，RCA dispatch 模板（`execution-repair-truncation.md:121-157`、`final-review-repair.md:132-169`）保留（它们是实际 prompt 内容），但"最多 N 轮"的数字从散文移除，由参数 + hook 持有。

### 3.4 风险

- **hook 强制截断不能误杀合法续修**：`repair_round` 语义在 re-entry / reflux 场景要清楚（execution re-entry 时 `repair_round` 不递增，见 `SKILL.md:321`）。hook 上限检查必须尊重这个语义，否则误阻 reflux。**与 `04` reflux 重置逻辑联动，需对齐。**
- **escalate_to_rca 的 RCA 轮要不要也计入 hook 上限**：RCA dispatch 走的是 `Agent({...})` 不一定经同一 validate hook（RCA 是 `root-cause-analyst`，不是 plan worker）。需确认 RCA 派发路径上有对应 gate，否则 RCA 轮逃逸机器强制。**落地时核 RCA 派发是否过 validate hook。**

### 3.5 验收信号

- 三套截断 reference 不再各自硬编码"最多 N 轮"数字；统一引用 `repair_policy` 参数。
- 派发修复时 `repair_round` 超 `max_repair_rounds`（含 RCA 余量）被 hook `exit 2` 阻断（新增 hook test 覆盖）。
- 行为等价：execution 仍 3 轮、final-review 仍 1+1、plan-review 仍 2 轮（`08` 回归测试确认无行为漂移）。

---

## 4. 漂移根治

### 4.1 重写 architecture-draft 校准到 v3.10.0（唯一总览图，重写不删）

**现状**：`architecture-draft.md:5` 自标 `Plugin 版本：3.8.0`，`:3-4` 审计日期 2026-05-28；`plugin.json` 实际 `3.10.0`（`jq -r .version`）。文档 1303 行 / 82502 字符，`:6` 自称"理解 plugin 整体 workflow 的**唯一**入口文档"。

**它是唯一总览图，承重，不能删。** CLAUDE.md 也指它为"架构权威"。目标是**重写校准**，不是废弃。

重写范围（**只改与源码不符的段，不重做全文**）：

1. **版本头**：`:5` `3.8.0` → `3.10.0`；`:3-4` 审计日期更新到本次重排落地日。
2. **bug-seed 过时描述（漂移项 1/2）**：`architecture-draft.md:1226` 仍写 `Bug RCA 发现设计问题 → ... 先创建 bug seed file 再以 seed 进入 Route 1`。但实际路径已删此机制——`bug-investigation-route.md:63` 明写 `不创建中间 bug-seed 文件，RCA findings 报告路径直接加入 Scope Contract 的 Source artifacts`。**bug-seed 文件机制已真删（代码侧），architecture-draft 描述未跟上。** 修法：把 `:1226` 改为与 `bug-investigation-route.md:63` 一致的"RCA findings 直接作 Discovery source artifact，不创建中间 seed 文件"。
   > **严正提醒（骨架明确）**：bug-seed 已**真删**，这是文档描述落后于代码，不是"代码还有残留要删"。**不要去补做不存在的 seed 删除**，只改文档描述。
3. **routes / 截断 / 切片新事实回填**：`02` routes 清单、本分册的参数化切片与统一截断落地后，architecture-draft 对应段（如 `:145-149` Route 表、`:279` plan-writing step 列、`:857-867` Path A 段）需同步反映新结构。**这部分依赖 `02`/`03`/`04` 先落地，本分册标为"待回填"。**

**漂移项 2/2**：版本号自标漂移本身（`:5`），即第 1 条。**注意范围是 2 项不是 3 项**（骨架 `00-overview.md:33` 与本分册职责均明确）。Path A / Targeted Re-Review **不在删除/扶正之列**——见 4.2。

### 4.2 Path A / Targeted Re-Review：扶正为正式轻量自修，清"已删"假声明

**核验结果（重要纠偏）**：plugin 文档内部**没有**任何"Path A 已删 / Targeted Re-Review 已删"的假声明。`grep -rn "Path A.*删\|Targeted.*删\|Path A.*removed" skills/ architecture-draft.md` 零命中。Path A 在 canonical 路径**全程活着且描述一致**：`repair-routing.md:9,24`、`final-review-repair.md:11`、`execution-repair-truncation.md:15`、`architecture-draft.md:181,214,857,867` 均一致描述 Path A = Coordinator 直接修 ≤2 文件、失败升 Path B。

骨架 `00-overview.md:33` 那句"Path A / Targeted Re-Review 仍活在 canonical 路径，文档却称已删"指的是**上一轮 cut-list 的意图**（曾想删但没删，且没在 plugin 文档里留下"已删"声明）。落地动作：

1. **扶正为正式轻量自修**：Path A（Coordinator 直接修 ≤2 文件 + 自验，失败升 Path B）就是 D1 激进默认轻档精神在修复层的体现——轻量、不必每次外审。把它从"看起来像临时旁路"正式确认为 canonical 的一等轻量自修路径。`repair-routing.md:9,24` 已是这个语义，**确认保留，不做删除**。
2. **Targeted Re-Review 现状已是受控的**：`execution-repair-truncation.md:13` 明写"默认自验收，仅满足 exception 条件（3+ 文件控制流 / 用户要求 / RCA 根因 / Path A 自修）才派 targeted Codex re-review"，`gate-codex-review.sh` 强制（`:26` 读 `exception_code`）。final-review 更进一步**不再派 targeted re-review**（`final-review-repair.md:9`）。这与 D2（默认免外审）同向，**确认保留**。
3. **清假声明**：因 plugin 文档内无"Path A 已删"假声明，本项的实际动作是**确认无需扶正删除**——避免后续 plan 阶段误读骨架那句话去"补删 Path A"。**Path A 不删。**

### 4.3 区分"已建单源（D1 已落地）"与"待删 wrapper"

**已落地的单源（D1 精神已在 build 层落地，不要重做）**：

| 内容 | 单源 | 注入处（build 锚点） | 状态 |
| --- | --- | --- | --- |
| preamble（Hard Gate / Only-stop / Honesty Rule） | `build/templates/preamble.md.tmpl`（T1/T2/T3 三 variant） | 6 SKILL（`grep -o "preamble \[variant=...\]"`：T1=workflow, T2=discovery/multi-pr-merge, T3=execution/final-review/plan-writing） | **已单源**，build `--apply` 注入 |
| voice-directive（Anti-Sycophancy / 禁止词） | `voice-directive.md.tmpl`（14 variant） | 6 SKILL + agent | **已单源** |
| signpost（transition 动作） | `signpost.md.tmpl` | 6 SKILL | **已单源**（但含待移出的 phase 序列散文，见 §2.3.1） |
| review-dispatch content-only | `review-dispatch.content-only.md.tmpl` | codex-review/SKILL.md | **已单源**（`build.sh:52` 注释确认仅此 variant 仍 template-resolved） |

**这些是账面省（build-time 维护单源），不是运行时省。** 它们仍把全文注入每个 SKILL（§0 表已强调）。本分册的运行时省来自 §1 切片，不是重做这些单源。

**待删 wrapper（本分册不主导，属 `07`，此处只标边界）**：
- `agent twin 90% 重叠`、`detect-worker-scope-drift.sh`（已真删，`architecture-draft.md:471` 已记，filesystem 确认 `hooks/detect-worker-scope-drift.sh` 不存在）等属 `07` agent/hook 层。本分册**不重复处理**，只在漂移根治时确认 architecture-draft 对它们的描述与 filesystem 一致（detect-worker-scope-drift 删除描述 `:471` 已正确，无需改）。

### 4.4 风险

- **architecture-draft 重写 vs 删**：它是承重总览，重写时若大改结构会引入新漂移。**纪律：只改与源码不符的段，逐段 `grep` 核对源码后再改，不动正确的段。**
- **新事实回填依赖下游**：routes/切片/截断的 architecture-draft 回填依赖 `02`/`03`/`04` 落地。本分册标"待回填"，由 `08` migration 收口时统一回填，避免提前写入未落地结构造成新漂移。

### 4.5 验收信号

- `architecture-draft.md:5` 版本与 `plugin.json` 一致（`diff` 验证：`jq .version plugin.json` == architecture-draft 版本头）。
- `architecture-draft.md:1226` bug-seed 描述与 `bug-investigation-route.md:63` 一致（不再说"创建 seed file"）。
- Path A 在所有 canonical 路径仍存在（`grep` 确认未被误删）。
- 不存在"文档说删了、代码还活着"或"代码删了、文档还描述"的项（漂移归零，骨架 §8 第 5 条）。

---

## 5. 与不变量/保留清单的对账（北极星不变量自检）

| 骨架约束 | 本分册是否触碰 | 守护 |
| --- | --- | --- |
| §5 第 7 项 抑制幻觉四件套 | §1 切片把 quartet 移到独立 fragment 文件 | 内容一字不改；切完 `grep` 确认全文在 prompt 注入路径上 |
| §5 第 11 项 voice-directive build 注入 | §2/§4.3 确认 voice-directive 仍 build 单源注入每条派发路径 | 不删、不改实质内容 |
| §6 计费/LINEAGE | §3 hook 读 `repair_round` 做截断；不碰 idempotency_key | DISPATCH_ENVELOPE 块原样保留 |
| §6 状态权威 | §3 截断从散文移到 hook（读 envelope/state） | 截断决策依据进机器，比散文更可信 |
| §6 质量门最小集（子代理返回必验） | 不动 disposition 亲验纪律 | `disposition-table.md:3-8` 亲验纪律切片后仍整段保留 |
| D4 目标函数（降 token + 稳定地板） | §1 降 token；§3 hook 强制升稳定 | 同向，不冲突 |
| 用户核心原则 #14 不过度设计 | 切片复用现有 build resolver，不引入运行时新依赖；截断复用已有 `repair_round` 字段 | 无新增基础设施 |

---

## 6. 落地要点清单（给 plan-writing 直接拆 task）

1. **【强依赖 `02`】** phase 序列散文从 `signpost.md.tmpl` 移出 → routes 数据；SKILL 保留薄 step→reference 索引。
2. **【可独立】** `_shared/review-dispatch.md` / `repair-routing.md` / `disposition-table.md` 改造为 `.source.md` + build resolver 切片为 fragment 文件；改各 phase step 的 Read 指向。
3. **【可独立】** execution/plan-writing/final-review SKILL 去重 Only/Never stop、流程位置散文。
4. **【依赖 `02` 提供 repair_policy 数据位】** 三套截断 reference 数字收敛为引用 `repair_policy`；新增 hook 轮次上限校验（扩 `validate-plan-dispatch.sh`，与 `04` reflux 语义对齐）；加 hook test。
5. **【可独立】** architecture-draft 版本头 3.8.0→3.10.0 + bug-seed 描述 `:1226` 校准。
6. **【依赖 `02`/`03`/`04`，由 `08` 收口】** architecture-draft routes/切片/截断新事实回填。
7. **【纪律】** Path A / Targeted Re-Review **不删**，确认保留即可。

---

## 附：本分册引用的源码事实索引（均亲验）

- 文件尺寸：`skills/_shared/review-dispatch.md`=6576B、`repair-routing.md`=5753B、`disposition-table.md`=2760B、`decision-brief.md`=988B；`orchestrate-execution/SKILL.md`=20214B/377 行、refs 合计 28044B（`wc -c`）。
- `_shared` Read 计数：review-dispatch 被 10 处 Read、repair-routing 被 9 处（`grep -rln`）。
- 截断散文：`execution-repair-truncation.md:113`、`final-review-repair.md:124`、`plan-review-resolution.md:85`。
- hook 无轮次上限：`grep -rn "max.*round\|round.*>=\|truncat" hooks/*.sh` 零命中；`validate-plan-dispatch.sh:39,122` 只校验 disposition_refs。
- architecture-draft：`:5`=3.8.0（vs plugin.json 3.10.0）、`:6`=唯一入口、`:1226` bug-seed 过时描述、`:471` detect-worker-scope-drift 已删描述（filesystem 确认文件不存在）。
- bug-seed 真删证据：`bug-investigation-route.md:63`。
- build 机制：`build.sh:48`（resolver 接 anchor_name+variant）、`:52` review-dispatch content-only 仍 template-resolved；`build/README.md` 无 section/slice 支持。
- signpost phase 序列散文：`signpost.md.tmpl:11-12`，注入 5 个 SKILL（workflow 除外）。
