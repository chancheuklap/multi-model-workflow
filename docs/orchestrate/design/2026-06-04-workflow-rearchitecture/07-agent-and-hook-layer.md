# 分册 07：Agent 层收口 + Hook 强制层重排

> **绑定关系**：本分册在 `00-overview.md` 契约下展开。锁定决策 D1–D5（§3）、北极星不变量（§6）、保留清单（§5）为不可动摇前提。与骨架冲突 = 本文错。
> 本分册依赖 `02-routes-as-data.md`（routes 清单数据结构）、`04-budget-as-instrument.md`（预算降仪表）、`06-external-skill-strategy.md`（skill embed 矩阵）。
> 所有源码事实均引 `file:line`，来自亲自 Read。

## 0. 一句话结论

Agent 层有两对 90% 重叠的 twin（executor / explorer），重叠段已部分收口到 build template（`worker-loop` 已单源，`voice-directive` 已单源），但**两个 twin 的 worker-loop 在 agent 文件里仍是 锚点内的整段拷贝**——这是健康的（build 单源注入），不需要再动；真正要做的是：把 explorer twin 也纳入同样的单源待遇，并删掉 voice-directive 模板里**永不注入的 codex-reviewer dead variant**。Hook 层 16 注册 / 13 脚本中，3 个 PreToolUse/PostToolUse Bash 钩子 fire-on-every-Bash（`guard-premature-push` / `gate-codex-review` / `track-review-budget`），其中两个可加 `if:` 降频，push 守卫保留为发布硬闸门；新增一个**轮次截断机器化**点把 `repair-truncation.md:113` 的散文上限变成机器强制；validate-* 三件套改读 routes 清单（引 02）替代 phase 字面量；state.sh 删 3 行死 transition、`mutations[]`/`self_verifications[]` 降级为 DEBUG 开关、merge-brief 290 行嵌套 JSON Schema 降为散文骨架但保字段名+枚举；build 7 resolver 塌缩为 3 类内联函数，voice 禁止词 footer 单源注入但**每条派发路径（含 codex-review/adhoc）必须仍走 build**，否则 Anti-Sycophancy 静默丢失。

---

## 1. Agent twin 收口

### 1.1 现状（源码锚点）

四个 agent 构成两对 twin，重叠度极高：

| Twin 对 | model（frontmatter 静态字段） | 重叠段（逐行对照已确认） |
| --- | --- | --- |
| `pack-executor` / `complex-pack-executor` | `pack-executor.md:10` = `sonnet` / `complex-pack-executor.md:10` = `claude-opus-4-8[1m]` | `worker-loop`（已单源）、三次失败协议表、Memory 策略、模式 2a/2b、Return Contract、交付前自检 |
| `code-explorer` / `complex-code-explorer` | `code-explorer.md:11` = `sonnet` / `complex-code-explorer.md:11` = `claude-opus-4-8[1m]` | 核心纪律（只读/不扩 scope）、项目感知、Memory 策略、Return Contract、必验声明 |

**已经单源的部分（不要重做）**：

- `worker-loop` 段已抽到 `build/templates/worker-loop.md.tmpl`，由 `worker-loop.sh` resolver 注入。两个 executor 文件中 `<!-- BEGIN: worker-loop -->` / `<!-- END: worker-loop -->`（`pack-executor.md:59-188`、`complex-pack-executor.md:57-186`）锚点内的内容逐字相同，来自同一模板（`worker-loop.md.tmpl:1-129`）。build check 当前 clean（`build.sh --check` exit 0）。
- `voice-directive` 段已单源：7 个 agent 文件各有 `<!-- BEGIN: voice-directive [variant=X] -->` 锚点（`pack-executor.md:283` / `complex-pack-executor.md:288` / `code-explorer.md:59` / `complex-code-explorer.md:68` / `plan-writer.md:64` / `docs-worker.md:71` / `root-cause-analyst.md:161`），全部从 `voice-directive.md.tmpl` 的对应 `[variant=...]` 块 sed 抽取。

**model 是 frontmatter 静态字段，无法 build 注入**：Claude Code 读 agent 文件的 YAML frontmatter（`model:` / `effort:` / `skills:`）决定派哪个模型；这些字段必须在文件落盘时就存在，不能靠 build 锚点动态生成。所以**保留两文件是正确的**——twin 收口的目标是"重叠正文移到单源模板，两文件只留 frontmatter + 高风险/复杂度差异段 + 锚点占位"，不是合并成一个文件。

### 1.2 问题

1. **executor twin 的非-worker-loop 重叠段仍是双份手写**：三次失败协议表（`pack-executor.md:242-253` vs `complex-pack-executor.md:238-249`，逐字相同）、Memory 策略骨架、模式 2a/2b、交付前自检前 3 项——这些在两个文件里各写一遍，改一处忘另一处就漂移。
2. **explorer twin 完全没纳入 build 单源**：`code-explorer.md` 和 `complex-code-explorer.md` 除了 voice-directive 锚点外，核心纪律 / 项目感知 / Memory 策略 / Return Contract / 必验声明全是手写双份（`code-explorer.md:26-57` vs `complex-code-explorer.md:26-66`）。
3. **voice-directive 模板有 dead variant**：`voice-directive.md.tmpl:53-56` 的 `[variant=codex-reviewer]` 块**全仓零注入**——`grep "variant=codex-reviewer"` 只命中模板自身一行，没有任何文件携带该 anchor。codex-reviewer 没有 agent `.md` 文件（它是 Codex 外部模型，经 `codex-companion.mjs` 派发），它的"反幻觉四件套"由 `review-dispatch.content-only.md.tmpl` 注入（见 §4.3），不是 voice 禁止词 footer。这个 variant 是上一轮收口残留的死块。

### 1.3 目标设计

**收口原则（用户 #14：不过度设计）**：只把"逐字相同且会随业务规则一起改"的段落单源化。一次性的、agent 特有的、几乎不变的段落（如 description frontmatter、高风险自检）保持手写，单源化它们只增加 build 复杂度不产生收益。

具体动作：

| 段落 | 现状 | 目标 | 模板 |
| --- | --- | --- | --- |
| executor worker-loop | 已单源 | 不动 | `worker-loop.md.tmpl` |
| executor 三次失败协议表 | 双份手写 | 新增 `failure-protocol` anchor，单源注入两 executor | 新建 `failure-protocol.md.tmpl` |
| explorer 核心纪律+Memory+Return Contract | 双份手写 | 新增 `explorer-shared` anchor，单源注入两 explorer | 新建 `explorer-shared.md.tmpl` |
| 各 agent voice 行 | 已单源 | 不动（除删 dead variant） | `voice-directive.md.tmpl` |
| voice `[variant=codex-reviewer]` | 死块 | **删除**该 variant 块 | `voice-directive.md.tmpl:53-56` |

**两 executor 文件收口后只留**：frontmatter（含 `model`/`effort`/`skills`/`memory`/`color` 差异）+ Git 纪律 + 方法论（skill 调用差异，引 06）+ 高风险纪律段（`complex-pack-executor.md:40-47` 独有）+ 高风险自检段（`complex-pack-executor.md:188-196` 独有）+ 4 个单源 anchor（worker-loop / failure-protocol / 交付前自检 / voice-directive）。pack-executor 的交付前自检 4 项（`pack-executor.md:257-263`）与 complex 的 5 项（`complex-pack-executor.md:261-267`）差一条"合同闭合"——用 variant 处理（content-only 注入前 4 项，complex variant 追加第 5 项），或干脆保留手写（差异小，不强求）。

**skill 嵌入落地（引 06）**：twin 收口后，frontmatter 的 `skills:` 字段与正文"方法论"段的 `Skill({...})` 调用是 06 分册的 embed/invoke 矩阵落点。本分册只负责：收口正文时，**方法论段的 skill 调用差异（pack-executor 只调 `tdd`/`diagnose`/`prototype`；complex 多调 `improve-codebase-architecture`）保留在各自文件**，不强行单源化——因为这正是 twin 之间的有意义差异。explorers 当前 frontmatter 无 `skills:`，06 决定是否补 embed；本分册预留 frontmatter 位置，不替 06 拍板。

### 1.4 落地要点

1. 新建 `build/templates/failure-protocol.md.tmpl`（内容 = `pack-executor.md:242-253` 的表 + 关键规则行），在两 executor 文件中用 `<!-- BEGIN: failure-protocol -->` 锚点替换手写段。
2. 新建 `build/templates/explorer-shared.md.tmpl`（核心纪律 + Memory 骨架 + Return Contract），两 explorer 用 `<!-- BEGIN: explorer-shared -->` 锚点。注意 complex-code-explorer 的"调查方法"段（`complex-code-explorer.md:34-39`，root-cause 维度）是独有的，**不进**共享模板。
3. 删 `voice-directive.md.tmpl:53-56` 的 codex-reviewer variant。删后 `test_voice_injection.sh` 不受影响（它只测 7 个 agent variant + workflow/pack-executor 可抽取，`test_voice_injection.sh:12,18-22`，不测 codex-reviewer）。
4. 改任何 `.tmpl` 后**必须** `bash plugin/build/build.sh --apply --plugin-dir plugin` → `--check` 验证（CLAUDE.md 检查清单）。
5. 新 resolver 走 §4 塌缩后的统一内联（不为每个新 anchor 再写一个 4 行 cat 脚本）。

### 1.5 风险

- **build 注入失败 = agent 缺指令静默上岗**：新增 anchor 后若 resolver 没注册到塌缩函数的 dispatch，`resolve_anchor` 返回 1，`process_skill_file` 的 `|| continue`（`build.sh:98`）会**静默跳过**——锚点之间留空，agent 拿到残缺指令。缓解：`verify-maturity.sh` 增加"每个 agent 的每个 BEGIN anchor 都被成功 resolve（resolved 非空）"的断言。
- **explorer 收口动到只读纪律**：explorer 的"只调查不写文件"是角色红线，收口时若误改语义，explorer 可能越权写盘。缓解：收口是机械搬运（逐字进模板），不改字；用 `diff` 验证收口前后渲染产物字节一致。

### 1.6 验收信号

- `grep -c "BEGIN:" plugin/agents/code-explorer.md` ≥ 2（explorer-shared + voice-directive 都已 anchor 化）。
- 两 executor 文件中"第 1 次/第 2 次/第 3 次"协议表字符串只出现在 `failure-protocol.md.tmpl`，agent 文件里在锚点内（build 注入）。
- `grep "variant=codex-reviewer" plugin/` 零命中。
- `build.sh --check` exit 0；`test_voice_injection.sh` 全 PASS。

---

## 2. Hook 强制层逐条裁决

### 2.1 现状（源码锚点）

`hooks.json` 注册 16 项，引用 13 个脚本（11 在 `hooks/`，2 在 `scripts/`：`guard-premature-push.sh` / `cleanup-before-push.sh`）。Claude Code 的 `if:` 字段可声明触发条件，但当前只有 3 个注册用了 `if:`（`hooks.json:26` git commit、`:40-55` Agent 类型、`:95` git commit、`:101` git push）。其余 PreToolUse/PostToolUse Bash 钩子**无 `if:`，每条 Bash 命令都触发，靠脚本内部 grep 自闸门**。

### 2.2 逐条裁决表

| 钩子 | 事件/matcher | 现状触发 | 裁决 | 理由 + 风险 |
| --- | --- | --- | --- | --- |
| `session-start.sh` | SessionStart | startup/clear/compact | **保留** | 硬前置检查（环境变量/jq/版本），承重。 |
| `guard-premature-push.sh` | PreToolUse Bash | **每条 Bash**（无 if） | **保留 + 加 if 但守住双责** | 双责：①禁 `git merge --squash`（`:17`）②未勾选任务阻断 push/PR（`:24`）。是**发布硬闸门**（北极星 §6 质量门最小集），D1 Light Lane 也保留。可加 `if: "Bash(git push *)\|Bash(gh pr create *)\|Bash(git merge *)"`——但 Claude Code `if:` 是单模式 glob，三 OR 需拆三注册或保留无 if。**裁决：保留无 if**（脚本头两行 grep 极廉价，`:13` jq + `:17/:24` grep 是 O(命令长度)，每 Bash 跑成本可忽略；拆三注册增加 hooks.json 复杂度，违 #14）。 |
| `enforce-plan-commit.sh` | PreToolUse Bash | `if: Bash(git commit *)` | **保留** | 已正确降频。Pack commit 格式校验（`:41`）。 |
| `gate-codex-review.sh` | PreToolUse Bash | **每条 Bash**（无 if） | **加 if 降频** | 脚本 `:12` 已自闸门 grep `codex-companion.*task`，但每条 Bash 都跑这个 grep。加 `if: "Bash(*codex-companion*)"` 让它只在 Codex 派发时触发。**风险**：`if:` glob 与脚本内 grep 必须语义一致，否则 if 漏掉某些 codex 调用形式（如 `CODEX_SCRIPT` 别名，`:12` 也匹配它）→ baseline review 的 pack-completion 闸门（`:45-49`）静默失效。**缓解**：if 用宽模式 `Bash(*codex*task*)`，脚本内 grep 仍做精确二次判定（双层保险）。 |
| `validate-plan-dispatch.sh` | PreToolUse Agent | `if: Agent(pack-executor*)` + `Agent(complex-pack-executor*)` | **保留 + 改读 routes（引 02）** | `:75` `if [[ "$PHASE" == "execution" ]]` 是 phase 字面量硬判，骨架 §2/§4 病根。改为读 routes 清单判定（见 §2.3）。 |
| `validate-pack-manifest.sh` | PreToolUse Agent | 同上两 Agent if | **保留** | A==B、C⊆A 三方对账（`:3-16`），承重审计链。 |
| `validate-multi-pr-dispatch.sh` | PreToolUse Agent | **每个 Agent**（无 if，脚本内判 phase） | **保留 + 改读 routes（引 02）** | `:45-49` `if [[ "$PHASE" != "multi-pr-merge" ]]; then exit 0` 是 phase 字面量。改读 routes 判定该 phase 是否需要 merge-brief gate。**风险**：multi-pr-merge 的 4 项 gate（merge-brief 存在 / META 一致 / conflict_id / prompt 引用）是承重——routes 化时这些 gate 参数必须从 routes 清单读，不能丢。 |
| `guard-doc-edit.sh` | PreToolUse Edit/Write | 每个 Edit/Write（无 if） | **保留** | Worker 禁改 docs/（北极星 §6 数据权威）。worker-active marker 判定（`:37-41`）。承重。 |
| `track-review-budget.sh` | PostToolUse Bash | **每条 Bash**（无 if） | **加 if 降频** | `:10` 已自闸门 grep `codex-companion`+`result`。加 `if: "Bash(*codex*result*)"` 降频。预算逻辑本身按 04 改（软继续+到顶停，删 80% 硬 DC 触发，`:50-55,64-67`）。**风险**：同 gate-codex-review，if 与脚本 grep 语义对齐。 |
| `track-execution-state.sh` | PostToolUse Bash | `if: Bash(git commit *)` | **保留** | 已降频。Pack 完成状态写 execution-state（承重，compaction recovery 唯一真相源）。 |
| `cleanup-before-push.sh` | PostToolUse Bash | `if: Bash(git push *)` | **保留** | 已降频。 |
| `agent-return-handler.sh` | PostToolUse Agent | 每个 Agent（无 if，脚本内判类型） | **保留 + 精简** | `:28-31` 只处理 executor twin，其他类型 `exit 0`。可加 `if: "Agent(*pack-executor*)"` 降频；7 路 verdict emit 已在 commit 743f447 塌缩，不再动文案。 |
| `track-effort-budget.sh` | PostToolUse Agent | 每个 Agent（无 if） | **保留 + 改（引 04）** | effort 权重计算（`:37-75`）。删 root-cause-analyst 的 `EFFORT_INCREMENT="2"`（`:73`，骨架 §4 "删 effort 2×"）按 04 处理；本分册只标记此处是 04 的落点。 |

### 2.3 删假门 + 新增轮次截断机器化

**删假 phase_skip 连带（引 03 主导，本分册标 hook 侧清理）**：`phase_skip` 字段零 hook 消费（骨架 §2 已验，本分册复验：`grep phase_skip plugin/hooks/` 零命中——只在 `state.sh` / `workflow-state-v1.json` / `orchestrate-workflow/SKILL.md` / 2 个 scripts test）。**hook 层无删除动作**（本来就没消费它），但 03/02 删 schema 字段后，要确认没有 hook 引入对它的新依赖。本分册仅记录：hook 层对 phase_skip 的清理 = 零（已是干净的），无需动作。

**新增轮次截断 hook（核心新增）**：

- **现状病根**：repair round 上限"2 Worker round + 1 RCA round = 3"写在散文里（`execution-repair-truncation.md:113`），靠主线程自觉数轮次。这正是骨架 §1 病根"靠主线程自觉、机器不参与控制"的典型。
- **机器化难点（必须诚实交代）**：repair 走 **SendMessage 续派**，而 SendMessage **不触发 PreToolUse Agent 钩子**（`validate-plan-dispatch.sh:17` 明确"Repair Mode uses SendMessage, which does not fire this PreToolUse Agent hook"）。Targeted Re-Review 经 Bash `codex-companion` 派发。所以截断的机器执行点不能挂在 Agent 钩子上。
- **目标设计**：新增 `enforce-repair-round-cap.sh`，挂 **PreToolUse Bash**，`if: "Bash(*codex*task*)"`（与 gate-codex-review 同触发面，因为每轮 Targeted Re-Review 必经一次 Codex 派发）。逻辑：从 dispatch envelope 或 gate 名解析 `plan-impl-review-N-repair-<round>`（`execution-repair-truncation.md:108` 规定 gate 名带 round），读 `execution-state.plans[N].repair_round`，超过 routes 清单配置的上限（默认 2，引 02 routes 携带 `repair_round_cap` 参数）→ `exit 2`，强制主线程改派 root-cause-analyst 或 BLOCKED。
- **为什么放 Bash 钩子而非 SendMessage**：SendMessage 没有 PreToolUse 钩子可挂；但每个 repair round 的闭环必然包含一次 Targeted Re-Review（Codex 派发，走 Bash），在那个点拦截等价于拦截整轮——round N+1 的 re-review 派发被拦 = round N 已被认定超限。这是机器能抓到的唯一稳定点。
- **与 04 预算的关系**：轮次截断是"质量稳定地板"（D4，防无限 repair 循环），预算是"成本护栏"（D3）。两者正交：截断防"一个 plan 在 review 里反复打转"，预算防"整 session 烧 token"。

**routes 化 phase 字面量（引 02）**：`validate-plan-dispatch.sh:75` 和 `validate-multi-pr-dispatch.sh:45-49` 的 `PHASE == "X"` 字面量改为：读 routes 清单查"当前 phase 是否启用本 gate + gate 参数"。02 负责定义 routes schema 与读取库；本分册负责列出 hook 侧消费点改造清单：

| 消费点 | 现状字面量 | routes 化后 |
| --- | --- | --- |
| `validate-plan-dispatch.sh:75` | `PHASE == "execution"` → plan-level 强制 | routes 查 `phase=execution` 的 `dispatch_granularity=plan` |
| `validate-multi-pr-dispatch.sh:47` | `PHASE != "multi-pr-merge"` → exit 0 | routes 查 `phase=multi-pr-merge` 的 `requires_merge_brief=true` |
| `gate-codex-review.sh:30` | `case "$REVIEW_INTENT" in baseline)` | routes 查 phase 的 `review_required` + intent 白名单 |

### 2.4 验收信号

- `enforce-repair-round-cap.sh` 存在并注册；test 覆盖：round=2 第 3 次 Codex re-review 派发被 exit 2 拦截。
- `gate-codex-review` / `track-review-budget` 带 `if:`，非 codex 的 Bash 命令不再触发它们（用 hook fire 计数或 strace 间接验，或单测：纯 `ls` Bash 不进脚本主体）。
- validate-* 三件套不再含 `== "execution"` / `== "multi-pr-merge"` 字面量分支（改为 routes 查询）。
- 16 注册 → 17（+轮次截断）；guard-premature-push 仍无 if 且双责完整。

---

## 3. state.sh 瘦身

### 3.1 删死 transition 行

`TRANSITION_MATRIX`（`state.sh:73-98`）含 26 条规则。结合实际 transition 调用（grep 确认调用方：`orchestrate-*/SKILL.md` 的 `state.sh transition`、`plan-review-resolution.md:36/47`、`final-review-repair.md:20/31`、`execution-repair-truncation.md:24/35`、`agent-return-handler.sh`、`track-execution-state.sh`），死行裁决：

| 行 | 规则 | 裁决 | 依据 |
| --- | --- | --- | --- |
| `:75` | `Coordinator:pending:in_progress` | **删** | 注释自标 `Pack 2.14 / plan-level Worker first dispatch`；plan-level 首派由 Worker 调 `agent-id set` 时隐式置 in_progress（`validate-plan-dispatch.sh:143-145` 明确"不 pre-mutate"），Coordinator 不走 pending→in_progress transition。test_state.sh:467 测了它但那是死代码的测试。 |
| `:78` | `Coordinator:returned:review_pending` | **核验后删/保**：test_state.sh:475 测了 `returned→review_pending`。若 plan-impl-review 流程实际不调此 transition（review 经 dispatch-review.sh，不经 state.sh transition），则为死行。**裁决：标记待 02 复验**——routes 化后 review 状态是否还经 transition 决定生死。保守：先保留，02 确认无消费再删。 |
| `:96` | `agent-return-handler:in_progress:returned` | **保留** | `agent-return-handler.sh` 确有 plan-level 自动返回，但它经 `plan-returns ingest`（`:87`）而非 `transition`。需核：handler 是否调 transition。grep 未见 handler 调 `state.sh transition`——**疑似死行**，但注释指向真实流程。**裁决：标记待复验**，不盲删。 |

**裁决纪律（保守，引 #14 反面——不盲目删）**：`:75` 证据充分（validate-plan-dispatch 明确不走此路径）→ 删；`:78`/`:96` 证据是"grep 未见调用"，属"不存在"声明，按子代理纪律需主线程亲验消费点后再删，本分册标 `[待 02 复验]` 不替 02 拍板。同时删 `state-transition-matrix.md` 与 `architecture-draft.md:720,801` 中对应的死规则描述（漂移根治，引 05/08）。

### 3.2 mutations[] / self_verifications[] 降级为 DEBUG 开关

- **现状**：`mutations[]` 由 `cmd_update`（`state.sh:234-237`）和 `cmd_transition`（`:318-321`）每次写状态都 append；`self_verifications[]` 由 `cmd_self_verify_append`（`:500-526`）append。
- **消费者审计（grep 确认）**：`mutations` 运行时**零消费**——只被 `test_state.sh:244-251`（断言数组存在/有记录）、`verify-maturity.sh:272-274`（断言 state.sh 含 "mutations" 字符串）、`test_effort_budget_weighting.sh:53`（fixture 占位）读。`self_verifications` 同样**零运行时消费**——只被 `test_state.sh:56-130` 读、SKILL references 写入（`execution-repair-truncation.md:37` 等的 `self-verify append` 命令）。
- **问题**：每次 update/transition 都多一次 jq 重写整个 state 文件（`:228` 写值 + `:237` 写 mutation = 两次 mv），是无消费者的纯审计开销。`self_verifications` 是"自验收记录"，但没有任何 hook/脚本读它做决策。
- **目标设计**：两者降级为 **DEBUG 开关**——`STATE_DEBUG=1` 时才 append，默认不写。`init` 模板（`state.sh:170,175`）仍初始化空数组（向后兼容，schema 不破），但 `cmd_update`/`cmd_transition`/`cmd_self_verify_append` 的 append 包在 `[[ "${STATE_DEBUG:-}" == "1" ]]` 内。
- **测试影响（必须同步，引 08）**：`test_state.sh:244-251`（mutations）、`:56,122-130`（self-verify）、`verify-maturity.sh:272-274` 这些断言要么改为"DEBUG 模式下才断言"，要么删。`self-verify append` 命令本身保留（SKILL references 仍调它，不报错——DEBUG off 时它是 no-op 但 exit 0）。
- **风险**：若未来引入"读 self_verifications 做 RCA 路由"的消费者，需重新评估。当前无此需求（#14：不为假想需求保留开销）。

### 3.3 merge-brief 290 行嵌套 JSON Schema 降为散文骨架

- **现状**：`state-schema/merge-brief-v1.json` 293 行深层嵌套 JSON Schema。运行时消费者是 `cmd_merge_brief_verify`（`state.sh:1582`），它**不读这个 .json schema**——而是用 python 正则消费 markdown 产物：`:1606` 解析 `MERGE_BRIEF_META` 注释块、`:1617` 校验 6 必填 META 字段、`:1623` 校验 `current_stage` 7 枚举、`:1637-1640` 校验 9 个 section heading、`:1661/1686` 正则抽 `conflict_id`、`:1689` 抽 `status`、`:1695-1702` 校验 `status=resolved`→§6 有条目 / `status=rca-in-progress`→§5 有条目。`validate-multi-pr-dispatch.sh:142-165` 同样正则消费 §4 的 `conflict_id`+`status`。
- **关键**：merge-brief 的**运行时权威是 markdown 产物 + 正则**，那 293 行 JSON Schema 是给"人/工具校验产物结构"的旁置文档，无运行时读取。
- **目标设计**：JSON Schema 降为**散文骨架**（保留为 reference 文档），但 **§4/§5/§6 的字段名 + 枚举值必须原样保留**，因为 `state.sh:1582` 和 `validate-multi-pr-dispatch.sh` 的正则按字面消费（骨架 §5 保留项 17）：
  - `conflict_id`（§4，正则 `conflict_id[^:]*:`，`state.sh:1661`）
  - `status` 枚举：`resolved` / `rca-in-progress`（`state.sh:1695,1699`）+ 非-resolved 任意值
  - section heading 字面量：`## 4. Conflict` / `## 5. Root Cause` / `## 6. Resolution`（`state.sh:1680-1682`、`:1637-1640`）
  - `current_stage` 7 枚举：`init`/`conflict_discovery`/`rca`/`repair`/`integration_review`/`merging`/`complete`（`state.sh:1623`，与 `MERGE_BRIEF_STAGES` 数组一致）
  - META 6 必填：`schema_version`/`run_id`/`slug`/`created_at`/`last_updated_at`/`current_stage`（`state.sh:1617`）
- **降级形态**：把 293 行 JSON Schema 替换为一个 ~40 行的散文 + 字段表 reference（列字段名、枚举、哪个 section、被哪行正则消费）。这既减少漂移面（293 行嵌套 schema 没人维护就过时），又把"承重字段是哪些、谁消费"显式化。
- **风险（承重）**：若降级时漏掉任一字段名/枚举的字面写法，`merge-brief verify` 或 multi-pr dispatch gate 会静默放行错误产物（§4 status 自洽性失效）。**缓解**：保留 `test_state_merge_brief.sh`、`test_validate_multi_pr_dispatch.sh` 作为回归闸门——降级后这两个 test 必须仍全绿。

### 3.4 验收信号

- `state.sh:73-98` 删 `:75`（确认死）；`:78`/`:96` 经 02 复验后处理。
- 默认环境跑 workflow，`workflow-state-*.json` 的 `mutations`/`self_verifications` 保持空数组（DEBUG off）；`STATE_DEBUG=1` 时有记录。
- `merge-brief-v1.json` 行数从 293 降至 ≤ ~50（散文骨架）；`test_state_merge_brief.sh` + `test_validate_multi_pr_dispatch.sh` 全绿。
- `grep "conflict_id\|rca-in-progress\|## 4. Conflict" plugin/state-schema/merge-brief-v1.json` 仍命中（承重字段名保留）。

---

## 4. build resolver 塌缩

### 4.1 现状（源码锚点）

7 个 resolver（`build/resolvers/*.sh`），`build.sh:46-67` 的 `resolve_anchor` 调用它们。关键事实：

- `resolver_base="${anchor_name}"`（`build.sh:49`）——**resolver 文件名恒等于 anchor 名**，dispatch 是纯路径拼接（`build.sh:61` `RESOLVER_DIR/${resolver_base}.sh`）。
- 7 个 resolver 实际只有 **2 类逻辑**：
  - **纯 cat**：`worker-loop.sh:18`（cat 模板）。`control-envelope.sh:8-22` 和 `review-dispatch.sh:8-22` 是"按 `.VARIANT.md.tmpl` 文件名取 variant，找不到回退主模板，然后 cat"——文件级 variant + cat。
  - **同段 sed variant**：`preamble.sh:17`、`sendmessage-resume.sh:17`、`signpost.sh:16`、`voice-directive.sh:17`——全部是同一行 `sed -n "/\[variant=$VARIANT\]/,/\[\/variant\]/{ /\[variant=/d; /\[\/variant\]/d; p; }"`，从单模板内抽 `[variant=X]...[/variant]` 块。
- 骨架描述"4 纯 cat + 3 同段 sed"，实际核验是 **3 类**：① 纯 cat（worker-loop）② 文件级 variant + cat（control-envelope / review-dispatch）③ 同段 sed variant（preamble / sendmessage-resume / signpost / voice-directive）。三类逻辑各异但每类内部完全相同（同段 sed 那 4 个脚本 sed 行逐字一致）。

### 4.2 目标设计：塌缩为内联函数

7 个独立 4–22 行脚本塌缩为 `build.sh` 内的 3 个内联函数（或一个带 mode 参数的函数），按 anchor 名映射到逻辑类：

```text
resolve_anchor(anchor, variant):
  case anchor in
    worker-loop:                       cat <template>                      # 纯 cat
    control-envelope | review-dispatch: cat <template[.variant]>           # 文件级 variant + cat
    preamble | sendmessage-resume | signpost | voice-directive:
                                       sed_extract_variant <template> var  # 同段 sed
```

收益：删 7 个文件、消除"新增 anchor 要新建一个几乎复制的 resolver"的仪式（#14：减少阻碍迭代的样板）。`build.sh:53-59` 已有的 review-dispatch content-only 特判逻辑并入这个 case。

**保留 review-dispatch 的特殊约束**：`build.sh:53-59` 规定 review-dispatch 只有 `content-only` variant 被 template 解析（其余 anchor 内容已迁到 `_shared/`，return 1 跳过）。塌缩时这个守卫**必须保留**——否则非-content-only 的 review-dispatch anchor 会被错误注入。

### 4.3 voice 禁止词 footer 单源 + 承重守卫（最关键）

- **现状**：禁止词 footer（`禁止词：delve, robust, comprehensive, nuanced, multifaceted, furthermore, moreover, crucial, additionally, pivotal.`）在 `voice-directive.md.tmpl` 的**每个 variant 块末尾各写一遍**（13 个 variant，`:14,23,32,41,50,55,60,65,70,89,103,117,131,145`）——同一行禁止词重复 13 次。
- **目标**：禁止词 footer 作为**公共 footer 注入一次**——voice resolver 抽 variant 主体后，统一追加一行禁止词 footer（footer 在 build.sh 内联或模板单独一行，不在每个 variant 里重复）。
- **承重守卫（北极星 §5 保留项 11 + 骨架 §7 本分册职责"voice-directive 去重的承重守卫"）**：禁止词 footer + Anti-Sycophancy 是 voice 的物理载体。去重时**每条派发路径必须仍走 build 注入**，否则静默丢失。逐路径核验：

| 派发路径 | voice 注入点 | 去重后是否仍走 build |
| --- | --- | --- |
| 7 个 sub-agent（executor×2 / explorer×2 / plan-writer / docs-worker / root-cause-analyst） | agent `.md` 的 `voice-directive` anchor（已确认 7 处） | ✅ 必须保 anchor，build apply 后 footer 在 |
| 6 个 Coordinator phase（workflow + discovery/plan-writing/execution/final-review/multi-pr-merge） | SKILL.md 的 `voice-directive` anchor（已确认 6 处，`:16,53,49,64,64,64`） | ✅ 同上 |
| **codex-review / adhoc** | **不走 voice anchor**——codex-review/SKILL.md 只有 `review-dispatch [variant=content-only]` anchor（`:74-98`），注入的是反幻觉四件套（Confidence/Pre-emit Gate/证据表/Bias，`review-dispatch.content-only.md.tmpl:1-23`），**没有禁止词 footer** | ⚠️ **承重风险点见下** |

- **codex-review/adhoc 的真实承重项**：codex-reviewer 路径的 Anti-Sycophancy 等价物**不是禁止词 footer**，而是 `review-dispatch.content-only` 的反幻觉四件套（Confidence rubric / Pre-emit Verification Gate / 证据表 / Bias indicators）。这条路径**已经走 build 注入**（content-only anchor），且 `test_review_evidence_table.sh:28-29` 已守"ad-hoc codex-review 必须含证据表"。所以：
  - 删 voice 模板的 codex-reviewer dead variant（§1.3）**不影响** codex-review 路径——它本来就不从 voice 取 footer。
  - 禁止词 footer 单源化只影响 13 个 voice variant 的渲染，codex-review 路径无 footer 是**现状即如此**，不是去重引入的回归。
- **塌缩后的回归闸门**：`test_voice_injection.sh`（7 agent anchor + 可抽取）+ `test_review_evidence_table.sh`（ad-hoc 反幻觉四件套）+ 新增"每个 voice variant 渲染产物末尾含禁止词 footer 行"断言（防 footer 单源化时漏注入某个 variant）。

### 4.4 落地要点

1. 塌缩 `build.sh:46-67` 的 `resolve_anchor`：把 7 个 resolver 的逻辑内联为 case 分支；删 `build/resolvers/` 7 个 `.sh`。
2. 禁止词 footer 从 13 个 variant 块移除，改为 voice case 分支统一追加。
3. `--apply` 重新生成所有 13+ 注入点；`--check` 必须 exit 0（渲染产物字节不变——footer 文本与位置保持，只是来源从"每块写"变"统一追加"）。**这里要小心**：若 footer 追加位置与原 variant 末尾不完全一致（多/少一个换行），`--check` 会全红。需逐字节对齐。
4. `test_resolvers.sh`（现测 7 个 resolver 文件可执行）改为测内联 case 的各分支输出。

### 4.5 风险

- **塌缩改 build 核心 = 全 13 注入点同时回归风险**：`resolve_anchor` 是所有 anchor 的唯一入口，改它若有 bug，13 个注入点同时坏。**缓解**：塌缩前先 `--apply` 出基线产物，塌缩后 `--check` 必须零 diff（证明渲染等价），再跑全套 `build/tests/`。
- **footer 单源化漏 variant = 该 agent/phase 静默失去禁止词约束**：缓解见 §4.3 新增断言。

### 4.6 验收信号

- `ls plugin/build/resolvers/` 为空或仅留 README；`build.sh` 内含 3 类 resolve 逻辑。
- 禁止词字符串在 `voice-directive.md.tmpl` 只出现 1 次（footer 源），不再 13 次。
- `build.sh --check` exit 0（零 diff）；`build/tests/` 全套 PASS（尤其 `test_voice_injection` + `test_review_evidence_table`）。
- codex-review/SKILL.md 仍含 `review-dispatch [variant=content-only]` anchor，ad-hoc 派发仍带反幻觉四件套。

---

## 5. 跨分册依赖与交接

| 本分册动作 | 依赖/交接分册 | 交接内容 |
| --- | --- | --- |
| validate-* 改读 routes 字面量消费点（§2.3） | `02-routes-as-data.md` | routes schema 须含 `dispatch_granularity` / `requires_merge_brief` / `review_required` / `repair_round_cap` 字段；02 提供读取库 |
| 删假 phase_skip hook 侧确认（§2.3） | `03-light-lane-and-escape-hatch.md` | 03 删 schema/SKILL 字段后，本分册确认 hook 层零新依赖 |
| `track-effort-budget.sh` 删 effort 2×、`track-review-budget.sh` 删 80% 硬 DC（§2.2） | `04-budget-as-instrument.md` | 04 主导预算降仪表；本分册标 hook 落点（`:73`、`:50-67`） |
| agent frontmatter `skills:` embed 矩阵（§1.3） | `06-external-skill-strategy.md` | 06 决定 explorer 是否补 embed；本分册预留 frontmatter 位置 |
| state.sh 死行 `:78`/`:96` 复验、merge-brief 降级、mutations 降级测试同步（§3） | `08-migration-rollout-acceptance.md` | 08 给分期顺序 + 回归测试清单 + 漂移根治（architecture-draft 同步） |
| 漂移根治（删 state-transition-matrix 死规则、architecture-draft 描述） | `05-skill-and-context-economy.md` / `08` | 05 主导 architecture-draft 重写 |

---

## 6. 落地分期建议（供 08 消费）

低风险优先、承重守卫先行：

1. **P1（零风险机械）**：删 voice 模板 codex-reviewer dead variant + build resolver 塌缩（先 `--apply` 基线 → 塌缩 → `--check` 零 diff）。纯重构，产物不变。
2. **P2（agent 收口）**：executor `failure-protocol` + explorer `explorer-shared` 单源化。机械搬运 + diff 验证。
3. **P3（hook 降频）**：gate-codex-review / track-review-budget 加 `if:`（双层保险：if 宽 + 脚本 grep 精确）。
4. **P4（state.sh 瘦身）**：删确认死行 `:75`、mutations/self_verifications 降 DEBUG、merge-brief schema 降散文（保字段名+枚举，回归 test 守）。
5. **P5（依赖 02）**：validate-* 改读 routes + 新增 `enforce-repair-round-cap.sh`。须等 02 routes 库就绪。

每期独立 commit，每期跑对应 test 子集 + `verify-maturity.sh`。
